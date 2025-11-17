import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies, login
from tests.utils.db_client import get_study_progress, get_word_from_word_id

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
QZ_BTN = (By.CSS_SELECTOR, "[data-testid='quiz-btn']")
QUIZ = (By.CSS_SELECTOR, "[data-testid='question-box']")
PROG_CNT = (By.CSS_SELECTOR, "[data-testid='progress-counter']")

def login_and_open_quiz_page(driver, base_url, email, password, level, type):
    """Log in and open the quiz page."""
    
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )

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
    
def login_and_open_quiz_page_with_level_reset(driver, base_url, email, password, level, type):
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
    
def login_and_open_quiz_type_selection_page(driver, base_url, email, password, level):
    
    
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/"))
    
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
    
def get_correct_quiz_answer_element(driver, base_url, type):
    """Get the correct quiz answer element."""
    
    question_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    word_id = question_element.get_attribute("data-word-id")
    word = get_word_from_word_id(base_url, word_id)
    correct_ans = word['furigana'] if type == "kanji-to-furigana" else word['kanji']    
    
    buttons = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid^='answer-']"))
    )
    for b in buttons:
        if b.text[3:] == correct_ans:
            return b
    raise AssertionError(f"Correct answer '{correct_ans}' not found among quiz options. B text: {b.text} != {correct_ans}")
    
def click_correct_quiz_answer(driver, base_url, type):
    """Click the correct quiz answer."""
    
    correct_ans_btn = get_correct_quiz_answer_element(driver, base_url, type)
    correct_ans_btn.click()
    return correct_ans_btn
    
def click_incorrect_quiz_answer(driver, base_url, type):
    """Click an incorrect quiz answer (one that does not match the expected value)."""
    
    question_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    word_id = question_element.get_attribute("data-word-id")
    word = get_word_from_word_id(base_url, word_id)
    correct_ans = word['furigana'] if type == "kanji-to-furigana" else word['kanji']    
    
    buttons = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid^='answer-']"))
    )
    for b in buttons:
        if b.text[3:] != correct_ans:
            b.click()
            return b
    raise AssertionError("Incorrect answer not found among quiz options")
    
def wait_for_completion_state(base_url, word_id, cookies, expected, level, type, timeout=5):
    """Poll the study progress API until the word's completion state matches the expected value."""
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        progress = get_study_progress(base_url, cookies, f"quiz-{type}", level, word_id)
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

def enter_review_mode(driver, base_url, type, num_of_correct, num_of_incorrect):
    """Complete the requested mix of quizzes so the session enters review mode."""
    
    alert_poll_seconds = 1
    for _ in range(num_of_correct):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_correct_quiz_answer(driver, base_url, type)
        wait_for_quiz_advance(driver, current_word_id)
    for _ in range(num_of_incorrect):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_incorrect_quiz_answer(driver, base_url, type)
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
        except TimeoutException:
            wait_for_quiz_advance(driver, current_word_id)
        else:
            alert.accept()
            return
    raise AssertionError("Failed to trigger quiz review mode with the requested incorrect answers.")

def dismiss_review_mode_modal(driver, base_url, type, num_of_correct, num_of_incorrect):
    
    alert_poll_seconds = 1
    for _ in range(num_of_correct):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_correct_quiz_answer(driver, base_url, type)
        wait_for_quiz_advance(driver, current_word_id)
    for _ in range(num_of_incorrect):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_incorrect_quiz_answer(driver, base_url, type)
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
        except TimeoutException:
            wait_for_quiz_advance(driver, current_word_id)
        else:
            alert.dismiss()
            return
    raise AssertionError("Failed to trigger review mode modal with the requested incorrect answers.")

def answer_all_quizzes_correctly_and_accept_alert(driver, base_url, type):
    
    modal_msg = None
    while True:
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_correct_quiz_answer(driver, base_url, type)
        
        try:
            alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
            modal_msg = alert.text
            alert.accept()
            break
        except TimeoutException:
            wait_for_quiz_advance(driver, current_word_id)
    
    return modal_msg

def solve_quizzes(driver, base_url, num_of_correct, num_of_incorrect):
    
    for _ in range(num_of_correct):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_correct_quiz_answer(driver, base_url, type)
        wait_for_quiz_advance(driver, current_word_id)
    for _ in range(num_of_incorrect):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(QUIZ)
        )
        current_word_id = question.get_attribute("data-word-id")
        click_incorrect_quiz_answer(driver, base_url, type)
        wait_for_quiz_advance(driver, current_word_id)

def reset_quiz_level_progress(driver, base_url, level, type):
    
    cookies = get_auth_cookies(driver)
    r = requests.post(
        f"{base_url}/api/study-progress/reset",
        params={"type": f"quiz-{type}", "level": level},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()