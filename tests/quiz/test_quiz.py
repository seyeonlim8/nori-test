import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import get_auth_cookies
from tests.utils.db_client import get_study_progress
from tests.utils.quiz_flows import open_quiz_page_with_level_reset

@pytest.mark.tcid("TC-QZ-004")
@pytest.mark.quiz
def test_correct_answer_marks_quiz_as_completed(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "furigana-to-kanji"
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='question-box']"))
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
    
def wait_for_completion_state(base_url, word_id, cookies, expected, level, type, timeout=5):
    """Poll the study progress API until the word's completion state matches the expected value."""
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        progress = get_study_progress(base_url, cookies, f"quiz-{type}", level, word_id)
        if progress.get("completed") == expected:
            return progress
        time.sleep(0.5)
    return None
