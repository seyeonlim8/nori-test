import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies, logout
from tests.utils.db_client import get_study_progress, get_word_from_word_id
from tests.utils.fill_flows import answer_all_problems_correctly_and_accept_alert, answer_problems, dismiss_review_mode_modal, enter_review_mode, get_correct_fill_answer, input_correct_fill_answer_from_db_and_submit_with_btn_click, input_correct_fill_answer_from_db_and_submit_with_keyboard, input_fill_answer, input_incorrect_fill_answer, login_and_open_fill_page, login_and_open_fill_page_with_level_reset, reset_fill_level_progress, wait_for_completion_state, wait_for_fill_advance, wait_stays_disabled_until_advance

FILL_BOX = (By.CSS_SELECTOR, "[data-testid='fill-box']")
FILL_ANS = (By.CSS_SELECTOR, "[data-testid='fill-answer']")
SUBMIT_BTN = (By.CSS_SELECTOR, "[data-testid='submit-btn']")
ENG_MEANING = (By.CSS_SELECTOR, "[data-testid='english-meaning']")
BLK_SENTENCE = (By.CSS_SELECTOR, "[data-testid='blank-sentence']")
PROG_CNT = (By.CSS_SELECTOR, "[data-testid='progress-counter']")
PROG_BAR = (By.CSS_SELECTOR, "[data-testid='progress-bar-inner']")

@pytest.mark.tcid("TC-FILL-001")
@pytest.mark.fill
def test_fill_page_loads_correctly(driver, base_url, admin_email, admin_password):
    
    level = "N2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    blank_sentence = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(BLK_SENTENCE))
    assert blank_sentence is not None, "Sentence with blank is not visible"
    assert "____" in blank_sentence.text, "Sentence does not have a blank"
    
    eng_meaning = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(ENG_MEANING))
    assert eng_meaning is not None, "English meaning is not visible"

@pytest.mark.tcid("TC-FILL-002")
@pytest.mark.fill
def test_correct_answer_marks_fill_as_completed(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(FILL_BOX)
    )
    input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url)
    
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
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
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
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    question = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id = question.get_attribute("data-word-id")
    input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url)

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
def test_correct_fill_answer_feedback_with_btn_click(driver, base_url, admin_email, admin_password):
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    answer = input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url)
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
    
@pytest.mark.tcid("TC-FILL-006")
@pytest.mark.fill
def test_correct_fill_answer_feedback_submission_with_keyboard(driver, base_url, admin_email, admin_password):
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    answer = input_correct_fill_answer_from_db_and_submit_with_keyboard(driver, base_url)
    answer_span = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_ANS))    
    assert answer in WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX)).text, "Blank not replaced with answer"
    assert answer_span.text == answer, "Answer in sentence does not match the correct answer"
    assert "text-green-500" in answer_span.get_attribute("class"), "Answer in sentence is not green"
    
    submit_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(SUBMIT_BTN))
    assert "Correct!" in submit_btn.text, f"Submit button text is incorrect. Current text: {submit_btn.text}"
    
    wait_for_fill_advance(driver, word_id_before)
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    assert word_id_before != word_id_after, "Question did not advance"
    
@pytest.mark.tcid("TC-FILL-007")
@pytest.mark.fill
def test_incorrect_fill_answer_feedback_with_btn_click(driver, base_url, admin_email, admin_password):
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    input_incorrect_fill_answer(driver)
    answer = get_correct_fill_answer(driver, base_url)
    answer_span = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_ANS))    
    assert answer in WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX)).text, "Blank not replaced with answer"
    assert answer_span.text == answer, "Answer in sentence does not match the correct answer"
    assert "text-red-500" in answer_span.get_attribute("class"), "Answer in sentence is not red"
    
    submit_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(SUBMIT_BTN))
    assert "Incorrect" in submit_btn.text, f"Submit button text is incorrect. Current text: {submit_btn.text}"
    
    wait_for_fill_advance(driver, word_id_before)
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    assert word_id_before != word_id_after, "Question did not advance"
    
@pytest.mark.tcid("TC-FILL-008")
@pytest.mark.fill
def test_hiragana_answer_rejected(driver, base_url, admin_email, admin_password):
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    fill_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id = fill_box.get_attribute("data-word-id")
    hiragana_answer = get_word_from_word_id(base_url, word_id)['furigana']
    
    input_fill_answer(driver, hiragana_answer)
    submit_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(SUBMIT_BTN))
    assert "Incorrect" in submit_btn.text, f"Submit button text is incorrect. Current text: {submit_btn.text}"

@pytest.mark.tcid("TC-FILL-012")
@pytest.mark.fill
def test_half_width_katakana_answer_accepted(driver, base_url, admin_email, admin_password):

    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

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

@pytest.mark.tcid("TC-FILL-016")
@pytest.mark.fill
def test_fill_review_mode_modal_appears(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    modal_seen = False
    alert_poll_seconds = 3
    for _ in range(5):
        fill_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
        old_word_id = fill_box.get_attribute("data-word-id")
        input_incorrect_fill_answer(driver)
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
            alert_msg = alert.text
            assert "words need review" in alert_msg
            modal_seen = True
            alert.accept()
            break
        except TimeoutException:
            wait_for_fill_advance(driver, old_word_id)
    
    assert modal_seen, "Review modal did not appear after answering all questions."
    
@pytest.mark.tcid("TC-FILL-017")
@pytest.mark.fill
def test_accepting_review_modal_starts_fill_review_mode(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    enter_review_mode(driver, 2, 3)
    progress_counter = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(PROG_CNT),
        "Progress counter not visible"
    )
    assert "(Review Mode)" in progress_counter.text, f"Progress counter not indicating review mode. Current text: {progress_counter.text}"
    
@pytest.mark.tcid("TC-FILL-018")
@pytest.mark.fill
def test_cancel_review_modal_redirects_and_resets_fill_progress(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    dismiss_review_mode_modal(driver, 2, 3)
            
    # Assert redirection to level selection page
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/study/fill-in-the-blank"),
    )
    assert driver.current_url == f"{base_url}/study/fill-in-the-blank", "Did not redirect to level selection page"
    
    # Assert progress is reset
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, "fill", level)
    assert progress == [], f"Expected empty list, got {progress}"
    
@pytest.mark.tcid("TC-FILL-019")
@pytest.mark.fill
def test_review_mode_excludes_completed_sentence(driver, base_url, admin_email, admin_password):
    """Ensure review mode only surfaces sentences that still need review."""
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 2, 3) 
    progress_counter = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(PROG_CNT),
        "Progress counter not visible"
    )
    assert "(Review Mode)" in progress_counter.text
    
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
            input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url)

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
    
@pytest.mark.tcid("TC-FILL-020")
@pytest.mark.fill
def test_fill_review_mode_label_displayed_in_progress_counter(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    enter_review_mode(driver, 2, 3) 
    progress_counter = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(PROG_CNT),
        "Progress counter not visible"
    )
    assert "(Review Mode)" in progress_counter.text, "(Review Mode) not indicated in progress counter"
    
@pytest.mark.tcid("TC-FILL-021")
@pytest.mark.fill
def test_fill_review_mode_progress_counter(driver, base_url, admin_email, admin_password):
    """Verify that the progress counter displays correct counts when entering review mode."""
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    enter_review_mode(driver, 2, 3) 
    progress_counter = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(PROG_CNT))
    text = progress_counter.text.strip()
    fraction, mode = text.split("(", 1)
    current_str, total_str = [part.strip() for part in fraction.split("/", 1)]
    mode = mode.rstrip(") ").strip()

    assert int(current_str) == 0, f"Expected 0 problems completed, saw {current_str} (text: {text})"
    assert int(total_str) == 3, f"Expected 3 total problems, saw {total_str} (text: {text})"
    assert mode == "Review Mode", f"Expected Review Mode label, saw {mode!r} (text: {text})"
  
@pytest.mark.tcid("TC-FILL-023")
@pytest.mark.fill  
def test_fill_progress_reset_modal_message(driver, base_url, admin_email, admin_password):
    """Complete all problems; accept completion alert and confirm modal message contains reset confirmation text."""
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    modal_msg = answer_all_problems_correctly_and_accept_alert(driver, base_url)
    assert "You completed all Fill-in-the-Blank quizzes! Progress reset." in modal_msg
    
@pytest.mark.tcid("TC-FILL-02４")
@pytest.mark.fill  
def test_fill_progress_counter_after_reset(driver, base_url, admin_email, admin_password):
    """Verify that the progress counter resets to 0 after completing all problems and resetting."""
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    answer_all_problems_correctly_and_accept_alert(driver, base_url)
        
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    current, total = [int(part.strip()) for part in progress_counter.text.split("/")[:2]]
    assert current == 0 and total == 5, f"Progress counter is not reset to 0. Current: {progress_counter.text}"
    
    progress_bar = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_BAR))
    style = progress_bar.get_attribute("style")
    assert "width: 0%" in style, f"Unexpected style: {style!r}"
  
@pytest.mark.tcid("TC-FILL-025")
@pytest.mark.fill    
def test_fill_study_progress_deleted_from_db_after_reset(driver, base_url, admin_email, admin_password):
    """Verify that study progress is completely removed from the database after reset."""
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    answer_all_problems_correctly_and_accept_alert(driver, base_url)
    
    # Assert progress is reset
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, "fill", level)
    assert progress == [], f"Expected empty list, got {progress}"
   
@pytest.mark.tcid("TC-FILL-026")
@pytest.mark.fill  
def test_fill_reset_scope_limited_to_current_level(driver, base_url, admin_email, admin_password):
    """Verify that resetting progress for one level does not affect progress in other levels."""
    
    correct_num = 5
    level = "n3"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    answer_problems(driver, base_url, correct_num, 2)
    
    reset_fill_level_progress(driver, base_url, "TEST")
    driver.get(f"{base_url}/study/fill-in-the-blank/TEST")
    modal_msg = answer_all_problems_correctly_and_accept_alert(driver, base_url)
    assert modal_msg is not None, "Review modal never appeared"
    assert "You completed all Fill-in-the-Blank quizzes! Progress reset." in modal_msg, "Incorrect modal message"
    
    progress_counter_TEST = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    current_TEST, _ = [int(part.strip()) for part in progress_counter_TEST.text.split("/")[:2]]
    assert current_TEST == 0, f"TEST progress is not reset to 0: {progress_counter_TEST.text}"
    
    driver.get(f"{base_url}/study/fill-in-the-blank/{level}")
    progress_counter_other = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    current_other, _ = [int(part.strip()) for part in progress_counter_other.text.split("/")[:2]]
    assert current_other == correct_num, f"{level} progress changed: {progress_counter_other.text}"

@pytest.mark.tcid("TC-FILL-028")
@pytest.mark.fill
def test_fill_position_persists_after_page_refresh(driver, base_url, admin_email, admin_password):
    """Verify the same sentence loads after a browser refresh."""
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    answer_problems(driver, base_url, 0, 3)
    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    
    driver.refresh()
    
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    assert word_id_before == word_id_after, (
        f"Sentence did not persist after refresh: before={word_id_before}, after={word_id_after}"
    )
    
    answer_problems(driver, base_url, 3, 0)
    question_before2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before2 = question_before2.get_attribute("data-word-id")
    
    driver.refresh()
    
    question_after2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after2 = question_after2.get_attribute("data-word-id")
    assert word_id_before2 == word_id_after2, (
        f"Sentence did not persist after refresh: before={word_id_before2}, after={word_id_after2}"
    )
    
@pytest.mark.tcid("TC-FILL-029")
@pytest.mark.fill
def test_fill_position_persists_after_logout_login(driver, base_url, admin_email, admin_password):
    """Verify the same sentence loads after logout and re-login."""
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    answer_problems(driver, base_url, 0, 3)
    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    
    logout(driver)
    login_and_open_fill_page(driver, base_url, admin_email, admin_password, level)
    
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    assert word_id_before == word_id_after, (
        f"Sentence did not persist after refresh: before={word_id_before}, after={word_id_after}"
    )
    
    answer_problems(driver, base_url, 3, 0)
    question_before2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before2 = question_before2.get_attribute("data-word-id")
    
    logout(driver)
    login_and_open_fill_page(driver, base_url, admin_email, admin_password, level)
    
    question_after2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after2 = question_after2.get_attribute("data-word-id")
    assert word_id_before2 == word_id_after2, (
        f"Sentence did not persist after refresh: before={word_id_before2}, after={word_id_after2}"
    )
 
@pytest.mark.tcid("TC-FILL-030")
@pytest.mark.fill   
def test_fill_position_persists_after_reopening_browser_or_across_devices(driver_factory, base_url, admin_email, admin_password):
    """Verify the same sentence loads after closing and reopening the browser."""
    
    level = "n2"
    
    # First browser session
    driver1 = driver_factory()
    login_and_open_fill_page_with_level_reset(driver1, base_url, admin_email, admin_password, level)
    answer_problems(driver1, base_url, 3, 3)
    question_before = WebDriverWait(driver1, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    driver1.quit()
    
    # Second browser session
    driver2 = driver_factory()
    login_and_open_fill_page(driver2, base_url, admin_email, admin_password, level)
    question_after = WebDriverWait(driver2, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    
    assert word_id_before == word_id_after, (
        f"Sentence did not persist after closing and reopening browser: "
        f"before={word_id_before}, after={word_id_after}"
    )
    driver2.quit()
    
@pytest.mark.tcid("TC-FILL-031")
@pytest.mark.fill  
def test_fill_progress_persists_on_reenter_normal_mode(driver, base_url, admin_email, admin_password):
    """Verify completed sentences remain persisted after leaving and re-entering Fill in the Blank page in Normal mode."""
    
    level = "n2"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" not in progress_counter.text, "Should be in Normal mode, not Review mode"
    
    answer_problems(driver, base_url, 3, 3)   
         
    cookies = get_auth_cookies(driver)
    progress_before = get_study_progress(base_url, cookies, "fill", level)
    completed_before = {p["wordId"] for p in progress_before if p["completed"]}
    
    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    
    driver.get(f"{base_url}")
    driver.get(f"{base_url}/study/fill-in-the-blank/{level}")
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" not in progress_counter.text, "Should be in Normal Mode, not Review Mode"
    
    progress_after = get_study_progress(base_url, cookies, "fill", level)
    completed_after = {p["wordId"] for p in progress_after if p["completed"]}
    
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
        
    # Assert persistence
    assert completed_after == completed_before, (
        "Progress did not persist after re-entering quiz: "
        f"before exit={len(completed_before)}, after re-enter={len(completed_after)}"
    )
    assert word_id_before == word_id_after, (
        "Normal mode did not resume on the same quiz: "
        f"before exit={word_id_before}, after re-enter={word_id_after}"
    )    
    
@pytest.mark.tcid("TC-FILL-032")
@pytest.mark.fill 
def test_fill_progress_persists_on_reenter_review_mode(driver, base_url, admin_email, admin_password):
    """Verify completed sentences remain persisted after leaving and re-entering Fill in the Blank page in Review mode."""
    
    level = "TEST"
    login_and_open_fill_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 1, 4) 

    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" in progress_counter.text, "Should be in Review mode, not Normal mode"
    
    answer_problems(driver, base_url, 2, 1)   
        
    cookies = get_auth_cookies(driver)
    progress_before = get_study_progress(base_url, cookies, "fill", level)
    completed_before = {p["wordId"] for p in progress_before if p["completed"]}
    
    question_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_before = question_before.get_attribute("data-word-id")
    
    driver.get(f"{base_url}")
    driver.get(f"{base_url}/study/fill-in-the-blank/{level}")
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" in progress_counter.text, "Should be in Review Mode, not Normal Mode"
    
    progress_after = get_study_progress(base_url, cookies, "fill", level)
    completed_after = {p["wordId"] for p in progress_after if p["completed"]}
    
    question_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(FILL_BOX))
    word_id_after = question_after.get_attribute("data-word-id")
    
    # Assert persistence
    assert completed_after == completed_before, (
        "Progress did not persist after re-entering quiz: "
        f"before exit={len(completed_before)}, after re-enter={len(completed_after)}"
    )
    assert word_id_before == word_id_after, (
        "Normal mode did not resume on the same quiz: "
        f"before exit={word_id_before}, after re-enter={word_id_after}"
    )    