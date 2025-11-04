import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies
from tests.utils.db_client import get_study_progress
from tests.utils.quiz_flows import open_quiz_page_with_level_reset

QUIZ = (By.CSS_SELECTOR, "[data-testid='question-box']")
ANS_BTN_1 = (By.CSS_SELECTOR, "[data-testid='answer-1']")

@pytest.mark.tcid("TC-QZ-004")
@pytest.mark.quiz
def test_correct_answer_marks_quiz_as_completed(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "furigana-to-kanji"
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    last_char = question.text.strip()[-1]

    answer_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            f"[data-testid^='answer-'][data-answer-text$='{last_char}']"
        ))
    )
    answer_btn.click()
    
    # Assert DB state
    word_id = question.get_attribute("data-word-id")
    cookies = get_auth_cookies(driver)  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=True, level=level, type=type)
    assert progress and progress.get("completed") is True, (
        f"Word {word_id} not marked as completed within 5s"
    )
    
@pytest.mark.tcid("TC-QZ-005")
@pytest.mark.quiz
def test_incorrect_answer_marks_quiz_as_incomplete(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "furigana-to-kanji"
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    last_char = question.text.strip()[-1]

    buttons = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='answer-']")
    incorrect_btn = next(
        btn for btn in buttons
        if not btn.text.strip().endswith(last_char)
    )
    incorrect_btn.click()
    
    # Assert DB state
    word_id = question.get_attribute("data-word-id")
    cookies = get_auth_cookies(driver)  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level, type=type)
    assert progress and progress.get("completed") is False, (
        f"Word {word_id} is marked as complete"
    )
    
@pytest.mark.tcid("TC-FC-006")
@pytest.mark.quiz
def test_answer_buttons_disabled_until_next_quiz(driver, base_url, admin_email, admin_password):
    """Verify that answer buttons become disabled immediately after click,
    remain disabled until the next quiz loads, and then re-enable properly.
    """

    level = "TEST"
    type = "furigana-to-kanji"
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)

    # Button test
    question = WebDriverWait(driver, 5).until(EC.presence_of_element_located(QUIZ))
    word_id = question.get_attribute("data-word-id")

    answer_btn1 = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(ANS_BTN_1))
    answer_btn1.click()

    # Disabled promptly
    WebDriverWait(driver, 2).until(
        lambda d: d.find_element(*ANS_BTN_1).get_attribute("disabled") is not None,
        "Answer button did not disable promptly after click"
    )

    # Stay disabled until advance
    wait_stays_disabled_until_advance(driver, word_id, ANS_BTN_1)

    # Re-enable after next flashcard
    WebDriverWait(driver, 2).until_not(
        lambda d: d.find_element(*ANS_BTN_1).get_attribute("disabled") is not None,
        "Answer button still disabled after next flashcard loaded"
    )
    
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
                raise AssertionError("Button re-enabled before next flashcard appeared")
        time.sleep(0.05)
    raise TimeoutException("Quiz did not advance")


