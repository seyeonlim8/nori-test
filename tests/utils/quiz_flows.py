import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies, login
from tests.utils.db_client import get_study_progress

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
QZ_BTN = (By.CSS_SELECTOR, "[data-testid='quiz-btn']")
QUIZ = (By.CSS_SELECTOR, "[data-testid='question-box']")

def open_quiz_page_with_level_reset(driver, base_url, email, password, level, type):
    """Log in, reset quiz progress for the given level/type, and open the quiz page."""
    
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )
    
    # Reset progress
    cookies = get_auth_cookies(driver)
    reset_url = f"{base_url}/api/study-progress/reset"
    r = requests.post(
        reset_url,
        params={"type": f"quiz-{type}", "level": level},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()

    study_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(STUDY_BTN),
        "Study button is not found"
    )
    ActionChains(driver).move_to_element(study_btn).perform()
    quiz_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(QZ_BTN),
        "Quiz button is not clickable"
    )
    quiz_btn.click()
    level_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='level-btn-{level.lower()}']")),
        f"{level.upper()} button is not clickable"
    )
    level_btn.click()
    
    type_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='{type.lower()}-btn']")),
        f"{level.upper()} button is not clickable"
    )
    type_btn.click()
    
def click_correct_quiz_answer(driver):
    """Click the correct quiz answer inferred from the current question text."""
    
    question_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    
    last_char = question_element.text.strip()[-1]
    answer_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            f"[data-testid^='answer-'][data-answer-text$='{last_char}']"
        ))
    )
    answer_btn.click()
    
def click_incorrect_quiz_answer(driver):
    """Click an incorrect quiz answer (one that does not match the expected value)."""
    
    question_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    
    last_char = question_element.text.strip()[-1]

    buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='answer-']")
    incorrect_btn = next(
        btn for btn in buttons
        if not btn.text.strip().endswith(last_char)
    )
    incorrect_btn.click()
    
def wait_for_completion_state(base_url, word_id, cookies, expected, level, type, timeout=5):
    """Poll the study progress API until the word's completion state matches the expected value."""
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        progress = get_study_progress(base_url, cookies, "quiz-{type}", level, word_id)
        if progress.get("completed") == expected:
            return progress
        time.sleep(0.5)
    return None

def wait_stays_disabled_until_advance(driver, old_word_id, btn_locator, timeout=3):
    """Wait until quiz advances, asserting button stays disabled until that point."""
    
    start = time.time()
    while time.time() - start < timeout:
        current_id = driver.find_element(*QUIZ).get_attribute("data-word-id")
        is_disabled = driver.find_element(*btn_locator).get_attribute("disabled") is not None
        if current_id != old_word_id:
            return  # advanced successfully
        # tolerate short flickers (<100ms)
        if not is_disabled:
            time.sleep(0.1)
            # re-check after brief delay in case it's transient
            if driver.find_element(*btn_locator).get_attribute("disabled") is None:
                raise AssertionError("Button re-enabled before next quiz appeared")
        time.sleep(0.05)
    raise TimeoutException("Quiz did not advance")

def wait_for_quiz_advance(driver, old_word_id, timeout=5):
    """Wait for the quiz to advance by checking that the word ID has changed."""
    
    def word_id_changed(driver):
        quiz = driver.find_element(*QUIZ)
        return quiz.get_attribute("data-word-id") != old_word_id
    WebDriverWait(driver, timeout).until(
        word_id_changed,
        "Quiz did not advance"
    )

def enter_review_mode(driver, num_of_completed, num_of_incomplete):
    """Complete the requested mix of quizzes so the session enters review mode."""
    
    alert_poll_seconds = 1.5
    for _ in range(num_of_completed):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_correct_quiz_answer(driver)
        wait_for_quiz_advance(driver, current_word_id)
    for _ in range(num_of_incomplete):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_incorrect_quiz_answer(driver)
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
        except TimeoutException:
            wait_for_quiz_advance(driver, current_word_id)
        else:
            alert.accept()
            return
    raise AssertionError("Failed to trigger quiz review mode with the requested incorrect answers.")
