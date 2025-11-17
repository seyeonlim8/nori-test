import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies
from tests.utils.db_client import get_study_progress
from tests.utils.fill_flows import enter_review_mode, input_correct_fill_answer_from_db_and_submit, input_fill_answer, input_incorrect_fill_answer, open_fill_page_with_level_reset, wait_for_completion_state, wait_for_fill_advance, wait_stays_disabled_until_advance

FILL_BOX = (By.CSS_SELECTOR, "[data-testid='fill-box']")
FILL_ANS = (By.CSS_SELECTOR, "[data-testid='fill-answer']")
SUBMIT_BTN = (By.CSS_SELECTOR, "[data-testid='submit-btn']")
ENG_MEANING = (By.CSS_SELECTOR, "[data-testid='english-meaning']")

@pytest.mark.tcid("TC-FILL-002")
@pytest.mark.fill
def test_correct_answer_marks_fill_as_completed(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(FILL_BOX)
    )
    input_correct_fill_answer_from_db_and_submit(driver, base_url)
    
    # Assert DB state
    word_id = question.get_attribute("data-word-id")
    cookies = get_auth_cookies(driver)  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=True, level=level)
    assert progress and progress.get("completed") is True, (
        f"Question {word_id} not marked as completed within 5s"
    )
    
@pytest.mark.tcid("TC-FILL-003")
@pytest.mark.fill
def test_incorrect_answer_marks_fill_as_incomplete(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(FILL_BOX)
    )
    input_incorrect_fill_answer(driver)
    
    # Assert DB state
    word_id = question.get_attribute("data-word-id")
    cookies = get_auth_cookies(driver)  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level)
    assert progress and progress.get("completed") is False, (
        f"Question {word_id} is marked as completed"
    )
    
@pytest.mark.tcid("TC-FILL-004")
@pytest.mark.fill
def test_submit_button_disabled_until_next_sentence(driver, base_url, admin_email, admin_password):
    """Verify that submit button becomes disabled immediately after click,
    remains disabled until the next sentence loads, and then re-enables properly.
    """

    level = "n2"
    open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    question = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id = question.get_attribute("data-word-id")
    input_correct_fill_answer_from_db_and_submit(driver, base_url)

    # Disabled promptly
    WebDriverWait(driver, 2).until(
        lambda d: d.find_element(*SUBMIT_BTN).get_attribute("disabled") is not None,
        "Submit button did not disable promptly after click"
    )

    # Stay disabled until advance
    wait_stays_disabled_until_advance(driver, word_id)

    # Re-enable after next flashcard
    WebDriverWait(driver, 2).until_not(
        lambda d: d.find_element(*SUBMIT_BTN).get_attribute("disabled") is not None,
        "Submit button still disabled after next flashcard loaded"
    )
    
@pytest.mark.tcid("TC-FILL-005")
@pytest.mark.fill
def test_correct_fill_answer_feedback(driver, base_url, admin_email, admin_password):
    
    level = "n2"
    open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    answer = input_correct_fill_answer_from_db_and_submit(driver, base_url)
    answer_span = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_ANS))    
    assert answer in WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX)).text, "Blank not replaced with answer"
    assert answer_span.text == answer, "Answer in sentence does not match the correct answer"
    assert "text-green-500" in answer_span.get_attribute("class"), "Answer in sentence is not green"
    
    submit_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(SUBMIT_BTN))
    assert "Correct!" in submit_btn.text, f"Submit button text did not change. Current text: {submit_btn.text}"
    
    wait_for_fill_advance(driver, word_id_before)
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    assert word_id_before != word_id_after, "Question did not advance"

@pytest.mark.tcid("TC-FILL-012")
@pytest.mark.fill
def test_half_width_katakana_answer_accepted(driver, base_url, admin_email, admin_password):

    level = "TEST"
    open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    meaning_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(ENG_MEANING)
    )
    
    last_char = meaning_element.text.strip()[-1]
    half_width_answer = 'ﾃｽﾄ' + last_char
    input_fill_answer(driver, half_width_answer)
    
    submit_btn = WebDriverWait(driver, 2).until(
        EC.presence_of_element_located(SUBMIT_BTN)
    )
    assert "Correct" in submit_btn.text
    
@pytest.mark.tcid("TC-FILL-019")
@pytest.mark.fill
def test_review_mode_excludes_completed_sentence(driver, base_url, admin_email, admin_password):
    """Ensure review mode only surfaces sentences that still need review."""
    
    level = "TEST"
    open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 2, 3) 
    assert "Review Mode" in driver.page_source
    
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, "fill", level)
    completed = {p["wordId"] for p in progress if p["completed"]}
    print("Completed set:", completed)
    assert completed, "No completed words found — test precondition failed."
    
    displayed_set = set()
    while True:
        try:
            quiz = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
            word_id = int(quiz.get_attribute("data-word-id"))
            displayed_set.add(word_id)
            input_correct_fill_answer_from_db_and_submit(driver, base_url)

            try:
                WebDriverWait(driver, 1.5).until(EC.alert_is_present())
                break
            except TimeoutException:
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_element(*FILL_BOX).get_attribute("data-word-id") != str(word_id)
                )
        except TimeoutException:
            break
            
    assert not (displayed_set & completed), "Completed sentence appeared in Review Mode"
    
    
    