import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies
from tests.utils.db_client import get_study_progress, get_word_from_word_id
from tests.utils.quiz_flows import click_correct_quiz_answer, click_incorrect_quiz_answer, enter_review_mode, get_correct_quiz_answer_element, login_and_open_quiz_page_with_level_reset, login_and_open_quiz_type_selection_page, wait_for_completion_state, wait_for_quiz_advance, wait_stays_disabled_until_advance

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
QUIZ = (By.CSS_SELECTOR, "[data-testid='question-box']")
ANS_BTN_1 = (By.CSS_SELECTOR, "[data-testid='answer-1']")
ANS_BTN_2 = (By.CSS_SELECTOR, "[data-testid='answer-2']")
ANS_BTN_3 = (By.CSS_SELECTOR, "[data-testid='answer-3']")
ANS_BTN_4 = (By.CSS_SELECTOR, "[data-testid='answer-4']")
QZ_BTN = (By.CSS_SELECTOR, "[data-testid='quiz-btn']")
K_TO_F_BTN = (By.CSS_SELECTOR, "[data-testid='kanji-to-furigana-btn']")
F_TO_K_BTN = (By.CSS_SELECTOR, "[data-testid='furigana-to-kanji-btn']")
PROG_CNT = (By.CSS_SELECTOR, "[data-testid='progress-counter']")

@pytest.mark.tcid("TC-QZ-001")
@pytest.mark.quiz
def test_quiz_type_selection_page_loads(driver, base_url, admin_email, admin_password):
    
    level = "n2"
    login_and_open_quiz_type_selection_page(driver, base_url, admin_email, admin_password, level)
    
    k_to_f_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(K_TO_F_BTN),
        "Kanji-to-furigana button not found"
    )
    f_to_k_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(F_TO_K_BTN),
        "Furigana-to-kanji button not found"
    )
    assert "漢字 → ふりがな" in k_to_f_btn.text, f"Incorrect text in button. Text: {k_to_f_btn.text}"
    assert "ふりがな → 漢字" in f_to_k_btn.text, f"Incorrect text in button. Text: {f_to_k_btn.text}"

@pytest.mark.tcid("TC-QZ-002")
@pytest.mark.quiz
def test_quiz_type_button_hover_changes_scale(driver, base_url, admin_email, admin_password):
    """Verify that hovering quiz type buttons trigger scale-up transform effect."""

    level = "n2"
    login_and_open_quiz_type_selection_page(driver, base_url, admin_email, admin_password, level)
    
    k_to_f_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(K_TO_F_BTN),
        "Kanji-to-furigana button not found"
    )
    f_to_k_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(F_TO_K_BTN),
        "Furigana-to-kanji button not found"
    )
    
    before_ktof = k_to_f_btn.value_of_css_property("transform")
    ActionChains(driver).move_to_element(k_to_f_btn).perform()
    wait_for_transform_change(driver, k_to_f_btn, before_ktof, timeout=1.5)
    after_ktof = k_to_f_btn.value_of_css_property("transform")
    assert before_ktof != after_ktof, f"Hover animation did not trigger (k-to-f); transform unchanged"
    
    before_ftok = f_to_k_btn.value_of_css_property("transform")
    ActionChains(driver).move_to_element(f_to_k_btn).perform()
    wait_for_transform_change(driver, f_to_k_btn, before_ftok, timeout=1.5)
    after_ftok = f_to_k_btn.value_of_css_property("transform")
    assert before_ftok != after_ftok, f"Hover animation did not trigger (f-to-k); transform unchanged"
   
def wait_for_transform_change(driver, element, old_val, timeout=1.0, poll_interval=0.05):
    WebDriverWait(driver, timeout, poll_interval).until(
        lambda d: element.value_of_css_property("transform") != old_val,
        "Hover transform animation did not trigger"
    )
    
@pytest.mark.tcid("TC-QZ-003")
@pytest.mark.quiz
def test_quiz_type_button_hover_changes_color(driver, base_url, admin_email, admin_password):
    """Verify that hovering quiz type buttons trigger color transform effect."""

    level = "n2"
    login_and_open_quiz_type_selection_page(driver, base_url, admin_email, admin_password, level)
    
    k_to_f_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(K_TO_F_BTN),
        "Kanji-to-furigana button not found"
    )
    f_to_k_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(F_TO_K_BTN),
        "Furigana-to-kanji button not found"
    )
    
    before_color_ktof = k_to_f_btn.value_of_css_property("background-color")
    ActionChains(driver).move_to_element(k_to_f_btn).perform()
    after_color_ktof = k_to_f_btn.value_of_css_property("background-color")
    assert before_color_ktof != after_color_ktof, "Button color did not change on hover (k-to-f)"
    
    before_color_ftok = f_to_k_btn.value_of_css_property("background-color")
    ActionChains(driver).move_to_element(f_to_k_btn).perform()
    after_color_ftok = f_to_k_btn.value_of_css_property("background-color")
    assert before_color_ftok != after_color_ftok, "Button color did not change on hover (f-to-k)"

@pytest.mark.tcid("TC-QZ-004")
@pytest.mark.quiz
def test_correct_answer_marks_quiz_as_completed(driver, base_url, admin_email, admin_password):
    """Verify that selecting the correct answer marks the quiz item as completed in the database."""
    
    level = "TEST"
    type = "furigana-to-kanji"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    click_correct_quiz_answer(driver, base_url, type)
    
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
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ)
    )
    click_incorrect_quiz_answer(driver, base_url, type)
    
    # Assert DB state
    word_id = question.get_attribute("data-word-id")
    cookies = get_auth_cookies(driver)  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level, type=type)
    assert progress and progress.get("completed") is False, (
        f"Word {word_id} is marked as complete"
    )

@pytest.mark.tcid("TC-QZ-006")
@pytest.mark.quiz
def test_kanji_to_furigana_quiz_displays_correct_format(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "kanji-to-furigana"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    q_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ),
        "Question box not found"
    )
    assert "テスト" in q_box.text, f"Quiz is not displaying Kanji. Displaying: {q_box.text}"
    
    word_id = q_box.get_attribute("data-word-id")
    answer = get_word_from_word_id(base_url, word_id)['furigana']
    option_texts = []
    for i in range(1, 5):
        ans_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='answer-{i}']")),
            "Answer button not found"
        )
        txt = ans_btn.text.strip()
        assert "てすと" in txt, f"Answer button {i} is not displaying Furigana. Displaying: {txt}"  # format validation
        option_texts.append(txt)
    # Assert correct number of options
    assert len(option_texts) == 4, f"Expected 4 answer options, got {len(option_texts)}: {option_texts}"
    # Assert uniqueness
    assert len(set(option_texts)) == 4, f"Duplicate answer options found: {option_texts}"
    # Assert correct answer present
    assert any(answer in t for t in option_texts), f"Correct answer '{answer}' not among options: {option_texts}"
    
@pytest.mark.tcid("TC-QZ-007")
@pytest.mark.quiz
def test_furigana_to_kanji_quiz_displays_correct_format(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "furigana-to-kanji"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    q_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(QUIZ),
        "Question box not found"
    )
    assert "てすと" in q_box.text, f"Quiz is not displaying Kanji. Displaying: {q_box.text}"
    
    word_id = q_box.get_attribute("data-word-id")
    answer = get_word_from_word_id(base_url, word_id)['kanji']
    option_texts = []
    for i in range(1, 5):
        ans_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"[data-testid='answer-{i}']")),
            "Answer button not found"
        )
        txt = ans_btn.text.strip()
        assert "テスト" in txt, f"Answer button {i} is not displaying Kanji. Displaying: {txt}"  # format validation
        option_texts.append(txt)
    # Assert correct number of options
    assert len(option_texts) == 4, f"Expected 4 answer options, got {len(option_texts)}: {option_texts}"
    # Assert uniqueness
    assert len(set(option_texts)) == 4, f"Duplicate answer options found: {option_texts}"
    # Assert correct answer present
    assert any(answer in t for t in option_texts), f"Correct answer '{answer}' not among options: {option_texts}"

@pytest.mark.tcid("TC-QZ-008")
@pytest.mark.quiz
def test_answer_quiz_with_mouse_click(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "kanji-to-furigana"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    quiz = WebDriverWait(driver, 5).until(EC.presence_of_element_located(QUIZ))
    old_word_id = quiz.get_attribute("data-word-id")
    ans_btn_1 = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(ANS_BTN_1),
        "Answer button is not clickable"
    )
    ans_btn_1.click()
    
    wait_for_quiz_advance(driver, old_word_id)
    new_word_id = quiz.get_attribute("data-word-id")
    assert old_word_id != new_word_id, "Quiz did not advance after mouse click"
    
@pytest.mark.tcid("TC-QZ-009")
@pytest.mark.quiz
def test_answer_quiz_with_keyboard_input(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "furigana-to-kanji"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    for i in range(1, 5):
        quiz = WebDriverWait(driver, 5).until(EC.presence_of_element_located(QUIZ))
        quiz.click()         
        old_word_id = quiz.get_attribute("data-word-id")
        ActionChains(driver).send_keys(i).perform()
        
        wait_for_quiz_advance(driver, old_word_id)
        new_word_id = quiz.get_attribute("data-word-id")
        assert old_word_id != new_word_id, "Quiz did not advance after keyboard input"

@pytest.mark.tcid("TC-QZ-010")
@pytest.mark.quiz
def test_correct_quiz_answer_color_feedback(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "kanji-to-furigana"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    correct_ans_btn = click_correct_quiz_answer(driver, base_url, type)
    correct_selector = correct_ans_btn.get_attribute("data-testid")

    WebDriverWait(driver, 2).until(
        lambda d: "bg-green-400" in d.find_element(By.CSS_SELECTOR, 
                                                   f"[data-testid='{correct_selector}']").get_attribute("class"),
        "Correct answer never turned green"
    )
    
    other_selectors = {f"answer-{i}" for i in range(1, 5)} - {correct_selector}
    for sel in other_selectors:
        WebDriverWait(driver, 2).until(
            lambda d, selector=sel: "bg-orange-100" in d.find_element(By.CSS_SELECTOR, 
                                                                      f"[data-testid='{selector}']").get_attribute("class"),
            f"Answer {sel} did not dim to orange"
        )   
        
@pytest.mark.tcid("TC-QZ-011")
@pytest.mark.quiz
def test_incorrect_quiz_answer_color_feedback(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "furigana-to-kanji"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    incorrect_ans_btn = click_incorrect_quiz_answer(driver, base_url, type)
    incorrect_selector = incorrect_ans_btn.get_attribute("data-testid")
    WebDriverWait(driver, 2).until(
        lambda d: "bg-red-400" in d.find_element(By.CSS_SELECTOR, 
                                                   f"[data-testid='{incorrect_selector}']").get_attribute("class"),
        "Incorrect answer never turned red"
    )
    
    correct_ans_btn = get_correct_quiz_answer_element(driver,base_url, type)
    correct_selector = correct_ans_btn.get_attribute("data-testid")
    WebDriverWait(driver, 2).until(
        lambda d: "bg-green-400" in d.find_element(By.CSS_SELECTOR, 
                                                   f"[data-testid='{correct_selector}']").get_attribute("class"),
        "Correct answer never turned green"
    )
    
    other_selectors = {f"answer-{i}" for i in range(1, 5)} - {incorrect_selector, correct_selector}
    for sel in other_selectors:
        WebDriverWait(driver, 2).until(
            lambda d, selector=sel: "bg-orange-100" in d.find_element(By.CSS_SELECTOR, 
                                                                      f"[data-testid='{selector}']").get_attribute("class"),
            f"Answer {sel} did not dim to orange"
        )
        
@pytest.mark.tcid("TC-QZ-012")
@pytest.mark.quiz
def test_answer_buttons_disabled_until_next_quiz(driver, base_url, admin_email, admin_password):
    """Verify that answer buttons become disabled immediately after click,
    remain disabled until the next quiz loads, and then re-enable properly.
    """

    level = "TEST"
    type = "furigana-to-kanji"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)

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
    
@pytest.mark.tcid("TC-QZ-020")
@pytest.mark.quiz
def test_review_mode_excludes_completed_quiz(driver, base_url, admin_email, admin_password):
    """Ensure review mode only surfaces words that still need review."""
    
    level = "TEST"
    type = "kanji-to-furigana"
    # Clear any previous progress for TEST set
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
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
            click_correct_quiz_answer(driver, base_url, type)

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
    
@pytest.mark.tcid("TC-QZ-021")
@pytest.mark.quiz
def test_review_mode_label_displayed_in_progress_counter(driver, base_url, admin_email, admin_password):
    
    level = "TEST"
    type = "kanji-to-furigana"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    enter_review_mode(driver, 2, 3)
    
    progress_counter = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(PROG_CNT),
        "Progress counter not found"
    )
    assert "(Review Mode)" in progress_counter.text, "(Review Mode) not indicated in progress counter"
    
@pytest.mark.tcid("TC-QZ-022")
@pytest.mark.quiz
def test_quiz_review_mode_progress_counter(driver, base_url, admin_email, admin_password):
    """Verify that the progress counter displays correct counts when entering review mode."""
    
    level = "TEST"
    type = "kanji-to-furigana"
    login_and_open_quiz_page_with_level_reset(driver, base_url, admin_email, admin_password, level, type)
    
    enter_review_mode(driver, 1, 4) 
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    
    text = progress_counter.text.strip()
    fraction, mode = text.split("(", 1)
    current_str, total_str = [part.strip() for part in fraction.split("/", 1)]
    mode = mode.rstrip(") ").strip()

    assert int(current_str) == 0, f"Expected 0 quiz completed, saw {current_str} (text: {text})"
    assert int(total_str) == 4, f"Expected 4 total quizzes, saw {total_str} (text: {text})"
    assert mode == "Review Mode", f"Expected Review Mode label, saw {mode!r} (text: {text})"