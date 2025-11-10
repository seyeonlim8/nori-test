import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies
from tests.utils.db_client import get_study_progress
from tests.utils.quiz_flows import click_correct_quiz_answer, click_incorrect_quiz_answer, enter_review_mode, open_quiz_page_with_level_reset, wait_for_completion_state, wait_stays_disabled_until_advance

QUIZ = (By.CSS_SELECTOR, "[data-testid='question-box']")
ANS_BTN_1 = (By.CSS_SELECTOR, "[data-testid='answer-1']")

@pytest.mark.tcid("TC-QZ-004")
@pytest.mark.quiz
def test_correct_answer_marks_quiz_as_completed(driver, base_url, admin_email, admin_password):
    """Verify that selecting the correct answer marks the quiz item as completed in the database."""
    
    level = "TEST"
    type = "furigana-to-kanji"
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    click_correct_quiz_answer(driver)
    
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
    """Verify that selecting an incorrect answer keeps the quiz item marked as incomplete in the database."""
    
    level = "TEST"
    type = "furigana-to-kanji"
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    click_incorrect_quiz_answer(driver)
    
    # Assert DB state
    word_id = question.get_attribute("data-word-id")
    cookies = get_auth_cookies(driver)  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level, type=type)
    assert progress and progress.get("completed") is False, (
        f"Word {word_id} is marked as complete"
    )
    
@pytest.mark.tcid("TC-QZ-006")
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

    # Re-enable after next quiz
    WebDriverWait(driver, 2).until_not(
        lambda d: d.find_element(*ANS_BTN_1).get_attribute("disabled") is not None,
        "Answer button still disabled after next quiz loaded"
    )
    
@pytest.mark.tcid("TC-QZ-021")
@pytest.mark.quiz
def test_review_mode_excludes_completed_quiz(driver, base_url, admin_email, admin_password):
    """Ensure review mode only surfaces words that still need review."""
    
    level = "TEST"
    type = "kanji-to-furigana"
    # Clear any previous progress for TEST set
    open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 2, 3) 
    assert "Review Mode" in driver.page_source
    
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, f"quiz-{type}", level)
    completed = {p["wordId"] for p in progress if p["completed"]}
    print("Completed set:", completed)
    assert completed, "No completed words found — test precondition failed."
    
    displayed_set = set()
    while True:
        try:
            quiz = WebDriverWait(driver, 5).until(EC.presence_of_element_located(QUIZ))
            word_id = int(quiz.get_attribute("data-word-id"))
            displayed_set.add(word_id)
            click_correct_quiz_answer(driver)

            # If alert shows up, review set is done
            try:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                break
            except TimeoutException:
                # no alert -> wait for next quiz to load
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_element(*QUIZ).get_attribute("data-word-id") != str(word_id)
                )
        except TimeoutException:
            break
            
    assert not (displayed_set & completed), "Completed quiz appeared in Review Mode"
    



