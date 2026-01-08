import time
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from tests.auth.test_auth_email_verification import _dismiss_alert_if_present
from tests.utils.email_verification import fetch_verify_url_from_mailhog
from tests.utils.flashcards_flows import enter_review_mode, login_and_open_flashcards_page, login_and_open_flashcards_page_with_level_reset, mark_all_flashcards_O_and_accept_alert, reset_flashcards_level_progress, study_flashcards, wait_for_completion_state, wait_for_flashcard_advance, wait_stays_disabled_until_advance
from tests.utils.auth_flows import fill_and_submit_signup, get_auth_cookies, logout, make_unique_username
from tests.utils.db_client import get_study_progress

VOCAB = (By.CSS_SELECTOR, "[data-testid='vocabulary']")
FURIGANA = (By.CSS_SELECTOR, "[data-testid='furigana']")
O_BTN = (By.CSS_SELECTOR, "[data-testid='o-btn']")
X_BTN = (By.CSS_SELECTOR, "[data-testid='x-btn']")
EX_BTN = (By.CSS_SELECTOR, "[data-testid='example-btn']")
EX_SENTENCE = (By.CSS_SELECTOR, "[data-testid='ex-sentence']")
MEANING_BTN = (By.CSS_SELECTOR, "[data-testid='meaning-btn']")
MEANING = (By.CSS_SELECTOR, "[data-testid='meaning']")
PROG_CNT = (By.CSS_SELECTOR, "[data-testid='progress-counter']")
SUBJECT = "NORI Email Verification"
EX_TRANSLATION = (By.CSS_SELECTOR, "[data-testid='ex-translation']")
FAVORITE_BTN = (By.CSS_SELECTOR, "[data-testid='favorite-btn']")
STAR_BTN = (By.CSS_SELECTOR, "[data-testid='star-btn']")
FAVORITES_BTN = (By.CSS_SELECTOR, "[data-testid='level-btn-favorites']")
STAR_FILLED = "★"
STAR_EMPTY = "☆"

def get_progress_counts(driver):
    text = driver.find_element(*PROG_CNT).text.strip()
    fraction = text.split("(", 1)[0]
    current_str, total_str = [part.strip() for part in fraction.split("/", 1)]
    return int(current_str), int(total_str), text

def get_favorite_word_ids(base_url, cookies):
    response = requests.get(
        f"{base_url}/api/favorites",
        cookies=cookies,
        timeout=5,
    )
    response.raise_for_status()
    return [int(word["id"]) for word in response.json()]

def clear_favorites(base_url, cookies):
    favorite_ids = get_favorite_word_ids(base_url, cookies)
    for word_id in favorite_ids:
        response = requests.post(
            f"{base_url}/api/favorites",
            json={"wordId": word_id},
            cookies=cookies,
            timeout=5,
        )
        response.raise_for_status()

def wait_for_favorite_state(base_url, cookies, word_id, expected, timeout=10):
    end_time = time.time() + timeout
    while time.time() < end_time:
        ids = get_favorite_word_ids(base_url, cookies)
        if (word_id in ids) == expected:
            return ids
        time.sleep(0.5)
    return get_favorite_word_ids(base_url, cookies)

@pytest.mark.tcid("TC-FC-001")
@pytest.mark.flashcards
def test_flashcard_vocabulary_visible(driver, base_url, admin_email, admin_password):
    """Verify that the vocabulary element is visible and furigana is hidden on initial flashcard load."""
    
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, "n2")

    # Assert vocabulary is visible
    vocab_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB),
        "Vocabulary element not found on flashcard page"
    )
    assert vocab_element.is_displayed(), "Vocabulary element is present but not visible"
    
    # Assert furigana is invisible
    furigana_visible = EC.visibility_of_element_located(FURIGANA)
    WebDriverWait(driver, 5).until_not(
        furigana_visible, 
        "Furigana should be hidden at start"
    )
    
@pytest.mark.tcid("TC-FC-002")
@pytest.mark.flashcards
def test_japanese_characters_render(driver, base_url, admin_email, admin_password):
    """Verify that the vocabulary text is non-empty, contains no broken glyphs, and uses the correct font."""
    
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, "n2")

    vocab = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    text = vocab.text
    assert text.strip(), "Vocabulary text is empty"
    assert not any(ch in text for ch in "□?"), "Broken glyphs detected"

    font = driver.execute_script(
        "return window.getComputedStyle(document.querySelector('[data-testid=\"vocabulary\"]')).fontFamily"
    )
    assert any(f in font for f in ["Noto Sans JP", "sans-serif"]), f"Unexpected font: {font}"

@pytest.mark.tcid("TC-FC-003")
@pytest.mark.flashcards
def test_o_button_marks_word_as_completed(driver, base_url, admin_email, admin_password):
    """Verify that clicking the O button marks the current word as completed in the database."""
    
    level = "n2"
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, level)
    
    vocab = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id = vocab.get_attribute("data-word-id")
    
    o_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(O_BTN),
        "O button is not clickable"
    )
    o_btn.click()
    
    cookies = get_auth_cookies(driver)
    
    # Assert DB state  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=True, level=level)
    assert progress and progress.get("completed") is True, (
        f"Word {word_id} not marked as completed within 5s"
    )
        
@pytest.mark.tcid("TC-FC-004")
@pytest.mark.flashcards
def test_x_button_does_not_mark_word_completed(driver, base_url, admin_email, admin_password):
    """Verify that clicking the X button does not mark the word as completed in the database."""
    
    level = "n2"
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, level)
        
    vocab = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id = vocab.get_attribute("data-word-id")
    
    x_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(X_BTN),
        "X button is not clickable"
    )
    x_btn.click()
    
    cookies = get_auth_cookies(driver)

    # Assert DB state  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level)
    assert progress is not None and progress.get("completed") is False, (
        f"Expected completed=False, got {progress}"
    )

@pytest.mark.tcid("TC-FC-005")
@pytest.mark.flashcards
def test_advance_to_next_flashcard(driver, base_url, admin_email, admin_password):
    """Verify that clicking either O or X advances to the next flashcard."""

    level = "n2"
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, level)
        
    vocab_1 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_1 = vocab_1.get_attribute("data-word-id")
    o_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(O_BTN),
        "O button is not clickable"
    )
    o_btn.click()
    wait_for_flashcard_advance(driver, word_id_1)
    vocab_2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_2 = vocab_2.get_attribute("data-word-id")
    assert word_id_1 != word_id_2, f"Flashcard did not advance after O click (still {word_id_1})"
    
    x_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(X_BTN),
        "X button is not clickable"
    )
    x_btn.click()
    wait_for_flashcard_advance(driver, word_id_2)
    vocab_3 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_3 = vocab_3.get_attribute("data-word-id")
    assert word_id_2 != word_id_3, f"Flashcard did not advance after X click (still {word_id_2})"

@pytest.mark.tcid("TC-FC-006")
@pytest.mark.flashcards
def test_OX_buttons_disabled_until_next_flashcard(driver, base_url, admin_email, admin_password):
    """Verify that both 'O' and 'X' buttons become disabled immediately after click,
    remain disabled until the next flashcard loads, and then re-enable properly.
    """

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    # ===== O button test =====
    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = vocab.get_attribute("data-word-id")

    o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
    o_btn.click()

    # Disabled promptly
    WebDriverWait(driver, 2).until(
        lambda d: d.find_element(*O_BTN).get_attribute("disabled") is not None,
        "O button did not disable promptly after click"
    )

    # Stay disabled until advance
    wait_stays_disabled_until_advance(driver, word_id, O_BTN)

    # Re-enable after next flashcard
    WebDriverWait(driver, 2).until_not(
        lambda d: d.find_element(*O_BTN).get_attribute("disabled") is not None,
        "O button still disabled after next flashcard loaded"
    )

    # ===== X button test =====
    vocab_new = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_new = vocab_new.get_attribute("data-word-id")

    x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
    x_btn.click()

    WebDriverWait(driver, 2).until(
        lambda d: d.find_element(*X_BTN).get_attribute("disabled") is not None,
        "X button did not disable promptly after click"
    )

    wait_stays_disabled_until_advance(driver, word_id_new, X_BTN)

    WebDriverWait(driver, 2).until_not(
        lambda d: d.find_element(*X_BTN).get_attribute("disabled") is not None,
        "X button still disabled after next flashcard loaded"
    )

@pytest.mark.tcid("TC-FC-007")
@pytest.mark.flashcards
def test_OX_button_hover_animation_triggers(driver, base_url, admin_email, admin_password):
    """Verify that hovering O and X buttons triggers scale-up transform effect."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    o_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(O_BTN))
    x_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(X_BTN))

    def get_width(elem):
        return driver.execute_script("return arguments[0].getBoundingClientRect().width;", elem)

    # --- O button ---
    w_before = get_width(o_btn)
    ActionChains(driver).move_to_element(o_btn).perform()
    WebDriverWait(driver, 2).until(lambda d: get_width(o_btn) > w_before * 1.05)
    w_after = get_width(o_btn)
    assert w_after > w_before * 1.05, "O button did not scale up on hover"

    # --- X button ---
    w_before = get_width(x_btn)
    ActionChains(driver).move_to_element(x_btn).perform()
    WebDriverWait(driver, 2).until(lambda d: get_width(x_btn) > w_before * 1.05)
    w_after = get_width(x_btn)
    assert w_after > w_before * 1.05, "X button did not scale up on hover"

@pytest.mark.tcid("TC-FC-008")
@pytest.mark.flashcards
def test_example_sentence_toggle_button(driver, base_url, admin_email, admin_password):
    """Verify the 'Show example sentence' button toggles the example sentence on/off and button text changes."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    example_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(EX_BTN))

    WebDriverWait(driver, 2).until(
        EC.invisibility_of_element_located(EX_SENTENCE),
        "Example sentence should be hidden by default"
    )
    example_btn.click()
    assert example_btn.text == "Hide example sentence", "Button text did not change"
    
    WebDriverWait(driver, 2).until(
        EC.visibility_of_element_located(EX_SENTENCE),
        "Example sentence did not toggle after first click"
    )

    example_btn.click()
    assert example_btn.text == "See example sentence", "Button text did not change"
    
    WebDriverWait(driver, 2).until(
        EC.invisibility_of_element_located(EX_SENTENCE),
        "Example sentence did not toggle after second click"
    )

@pytest.mark.tcid("TC-FC-009")
@pytest.mark.flashcards
def test_meaning_toggle_button(driver, base_url, admin_email, admin_password):
    """Verify 'Show meaning' button toggles furigana, meaning, and example translation on and off."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    meaning_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(MEANING_BTN))
    example_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(EX_BTN))
    example_btn.click()
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located(EX_SENTENCE))

    meaning_btn.click()
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(FURIGANA),
        "Furigana did not become visible after clicking Show meaning"
    )
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(MEANING),
        "Meaning did not become visible after clicking Show meaning"
    )
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(EX_TRANSLATION),
        "Example translation did not become visible after clicking Show meaning"
    )

    meaning_btn.click()
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located(FURIGANA),
        "Furigana did not become hidden after second click"
    )
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located(MEANING),
        "Meaning did not become hidden after second click"
    )
    WebDriverWait(driver, 5).until(
        EC.invisibility_of_element_located(EX_TRANSLATION),
        "Example translation did not become hidden after second click"
    )

@pytest.mark.tcid("TC-FC-010")
@pytest.mark.flashcards
def test_toggle_state_persists_after_refresh(driver, base_url, admin_email, admin_password):
    """Verify meaning and example sentence toggle states persist after refresh within the session."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    meaning_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(MEANING_BTN))
    example_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(EX_BTN))
    o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))

    example_btn.click()
    meaning_btn.click()
    WebDriverWait(driver, 2).until(EC.visibility_of_element_located(FURIGANA))
    WebDriverWait(driver, 2).until(EC.visibility_of_element_located(MEANING))
    WebDriverWait(driver, 2).until(EC.visibility_of_element_located(EX_TRANSLATION))
    WebDriverWait(driver, 2).until(EC.visibility_of_element_located(EX_SENTENCE))

    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = vocab.get_attribute("data-word-id")
    o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
    o_btn.click()
    wait_for_flashcard_advance(driver, word_id)

    WebDriverWait(driver, 2).until(
        EC.visibility_of_element_located(FURIGANA),
        "Furigana toggle did not persist after refresh"
    )
    WebDriverWait(driver, 2).until(
        EC.visibility_of_element_located(MEANING),
        "Meaning toggle did not persist after refresh"
    )
    WebDriverWait(driver, 2).until(
        EC.visibility_of_element_located(EX_TRANSLATION),
        "Translation toggle did not persist after refresh"
    )
    WebDriverWait(driver, 2).until(
        EC.visibility_of_element_located(EX_SENTENCE),
        "Example sentence toggle did not persist after refresh"
    )

@pytest.mark.tcid("TC-FC-011")
@pytest.mark.flashcards
def test_flashcards_progress_counter_format(driver, base_url, admin_email, admin_password):
    """Verify the progress counter displays in the expected numeric format."""

    level = "n2"
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, level)

    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    text = progress_counter.text.strip()
    fraction = text.split("(", 1)[0]
    parts = [part.strip() for part in fraction.split("/", 1)]
    assert len(parts) == 2, f"Progress counter missing separator: {text}"
    assert parts[0].isdigit() and parts[1].isdigit(), f"Progress counter not numeric: {text}"

@pytest.mark.tcid("TC-FC-012")
@pytest.mark.flashcards
def test_flashcards_progress_counter_updates_on_button_clicks(driver, base_url, admin_email, admin_password):
    """Verify progress counter increments correctly after clicking O and X buttons."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))

    current, total, _ = get_progress_counts(driver)
    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = vocab.get_attribute("data-word-id")
    o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
    o_btn.click()
    wait_for_flashcard_advance(driver, word_id)
    WebDriverWait(driver, 5).until(
        lambda d: get_progress_counts(d)[0] == current + 1,
        "Progress counter did not increment after O click"
    )
    current_after_o, total_after_o, _ = get_progress_counts(driver)
    assert total_after_o == total, "Total count changed after O click"

    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = vocab.get_attribute("data-word-id")
    x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
    x_btn.click()
    wait_for_flashcard_advance(driver, word_id)
    WebDriverWait(driver, 5).until(
        lambda d: get_progress_counts(d)[0] == current_after_o,
        "Progress counter incremented after X click"
    )
    current_after_x, total_after_x, _ = get_progress_counts(driver)
    assert total_after_x == total_after_o, "Total count changed after X click"

@pytest.mark.tcid("TC-FC-013")
@pytest.mark.flashcards
def test_rapid_o_clicks_do_not_duplicate_progress(driver, base_url, admin_email, admin_password):
    """Verify rapid clicking O does not increment the progress counter multiple times."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))

    current, total, _ = get_progress_counts(driver)
    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = vocab.get_attribute("data-word-id")
    o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))

    for _ in range(5):
        try:
            driver.execute_script("arguments[0].click();", o_btn)
        except Exception:
            break

    wait_for_flashcard_advance(driver, word_id)
    WebDriverWait(driver, 2).until(lambda d: get_progress_counts(d)[0] >= current + 1)
    final_current, final_total, _ = get_progress_counts(driver)
    assert final_total == total, "Total count changed after rapid clicks"
    assert final_current == current + 1, (
        f"Progress counter incremented more than once: start={current}, end={final_current}"
    )

@pytest.mark.tcid("TC-FC-014")
@pytest.mark.flashcards
def test_star_button_toggle_updates_favorites_db(driver, base_url, admin_email, admin_password):
    """Verify star button adds/removes the word in favorites table."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    cookies = get_auth_cookies(driver)
    clear_favorites(base_url, cookies)
    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = int(vocab.get_attribute("data-word-id"))

    fav_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(FAVORITE_BTN))
    fav_btn.click()
    ids_after_add = wait_for_favorite_state(base_url, cookies, word_id, expected=True)
    assert word_id in ids_after_add, "Word was not added to favorites after first click"

    fav_btn.click()
    ids_after_remove = wait_for_favorite_state(base_url, cookies, word_id, expected=False)
    assert word_id not in ids_after_remove, "Word was not removed from favorites after second click"

@pytest.mark.tcid("TC-FC-015")
@pytest.mark.flashcards
def test_star_button_ui_changes_on_click(driver, base_url, admin_email, admin_password):
    """Verify star icon toggles between filled and empty states on click."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    cookies = get_auth_cookies(driver)
    clear_favorites(base_url, cookies)
    fav_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(FAVORITE_BTN))

    fav_btn.click()
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*STAR_BTN).text.strip() == STAR_FILLED,
        "Star icon did not change to filled after first click"
    )

    fav_btn.click()
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*STAR_BTN).text.strip() == STAR_EMPTY,
        "Star icon did not change to empty after second click"
    )

@pytest.mark.tcid("TC-FC-016")
@pytest.mark.flashcards
def test_star_icon_matches_favorite_state_after_reopen(driver, base_url, admin_email, admin_password):
    """Verify star icon reflects DB state after leaving and returning to flashcards, with no duplicates."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    cookies = get_auth_cookies(driver)
    clear_favorites(base_url, cookies)
    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = int(vocab.get_attribute("data-word-id"))

    fav_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(FAVORITE_BTN))
    fav_btn.click()
    ids = wait_for_favorite_state(base_url, cookies, word_id, expected=True)
    assert len(ids) == len(set(ids)), f"Duplicate favorite entries detected: {ids}"

    driver.get(f"{base_url}")
    driver.get(f"{base_url}/study/flashcards/{level}")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    ids_after_nav = get_favorite_word_ids(base_url, cookies)
    displayed_id = int(driver.find_element(*VOCAB).get_attribute("data-word-id"))
    expected_state = STAR_FILLED if displayed_id in ids_after_nav else STAR_EMPTY
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*STAR_BTN).text.strip() == expected_state,
        "Star icon does not match favorite state after returning to flashcards"
    )

@pytest.mark.tcid("TC-FC-017")
@pytest.mark.flashcards
def test_favorite_persists_across_sessions(driver, base_url, admin_email, admin_password):
    """Verify favorite status persists after logout and login."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    cookies = get_auth_cookies(driver)
    clear_favorites(base_url, cookies)
    vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id = int(vocab.get_attribute("data-word-id"))

    fav_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(FAVORITE_BTN))
    fav_btn.click()
    wait_for_favorite_state(base_url, cookies, word_id, expected=True)

    logout(driver)
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, level)
    vocab_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_after = int(vocab_after.get_attribute("data-word-id"))
    assert word_id_after == word_id, "Flashcard did not persist after re-login"

    cookies = get_auth_cookies(driver)
    ids = get_favorite_word_ids(base_url, cookies)
    assert word_id in ids, "Favorited word missing from DB after re-login"
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*STAR_BTN).text.strip() == STAR_FILLED,
        "Star icon did not persist as filled after re-login"
    )

@pytest.mark.tcid("TC-FC-018")
@pytest.mark.flashcards
def test_favorites_flashcards_page_shows_only_favorited_words(driver, base_url, admin_email, admin_password):
    """Verify Favorites flashcards set contains only favorited words."""

    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    cookies = get_auth_cookies(driver)
    clear_favorites(base_url, cookies)

    favorite_ids = set()
    for _ in range(2):
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        word_id = int(vocab.get_attribute("data-word-id"))
        fav_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(FAVORITE_BTN))
        fav_btn.click()
        favorite_ids.add(word_id)

        x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
        x_btn.click()
        wait_for_flashcard_advance(driver, str(word_id), timeout=10)

    driver.get(f"{base_url}/study/flashcards")
    favorites_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(FAVORITES_BTN))
    favorites_btn.click()

    cookies = get_auth_cookies(driver)
    favorites_from_db = set(get_favorite_word_ids(base_url, cookies))
    assert favorite_ids.issubset(favorites_from_db), "Favorites not saved to DB before opening favorites page"

    displayed_ids = set()
    for _ in range(len(favorites_from_db)):
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_id = int(vocab.get_attribute("data-word-id"))
        displayed_ids.add(current_id)
        assert current_id in favorites_from_db, f"Non-favorited word appeared in Favorites: {current_id}"

        o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
        o_btn.click()
        try:
            alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert.accept()
            break
        except TimeoutException:
            try:
                wait_for_flashcard_advance(driver, str(current_id), timeout=10)
            except TimeoutException:
                o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
                o_btn.click()
                wait_for_flashcard_advance(driver, str(current_id), timeout=10)

    assert displayed_ids == favorites_from_db, (
        f"Favorites set mismatch. Expected={favorites_from_db}, displayed={displayed_ids}"
    )
@pytest.mark.tcid("TC-FC-019")
@pytest.mark.flashcards
def test_flashcard_review_mode_modal_appears(driver, base_url, admin_email, admin_password):
    """Verify that the review mode modal appears after marking multiple flashcards incorrect."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    modal_seen = False
    alert_poll_seconds = 1
    for _ in range(5):
        x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        x_btn.click()
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
            alert_msg = alert.text
            assert "5 words still need review" in alert_msg
        except TimeoutException:
            wait_for_flashcard_advance(driver, current_word_id)
        else:
            modal_seen = True
            alert.accept()
            break
    
    assert modal_seen, "Review modal did not appear after completing five cards."

@pytest.mark.tcid("TC-FC-020")
@pytest.mark.flashcards
def test_accepting_review_modal_starts_flashcards_review_mode(driver, base_url, admin_email, admin_password):
    """Verify that accepting the review mode modal transitions the session into Review Mode."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    enter_review_mode(driver, 2, 3)
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" in progress_counter.text, "Should be in Review Mode, not Normal Mode"
    
@pytest.mark.tcid("TC-FC-021")
@pytest.mark.flashcards
def test_cancel_review_modal_redirects_and_resets_flashcards_progress(driver, base_url, admin_email, admin_password):
    """Verify that dismissing the review mode modal redirects to level selection and resets progress."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    alert_poll_seconds = 1
    for _ in range(5):
        x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        x_btn.click()
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
            alert_msg = alert.text
            # Assert modal warning message
            assert "progress will be reset" in alert_msg
        except TimeoutException:
            wait_for_flashcard_advance(driver, current_word_id)
        else:
            alert.dismiss()
            break
        
    # Assert redirection to level selection page
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/study/flashcards"),
    )
    assert driver.current_url == f"{base_url}/study/flashcards", "Did not redirect to level selection page"
    
    # Assert progress is reset
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, "flashcards", level)
    assert progress == [], f"Expected empty list, got {progress}"
    
@pytest.mark.tcid("TC-FC-022")
@pytest.mark.flashcards
def test_review_mode_excludes_completed_flashcards(driver, base_url, admin_email, admin_password):
    """Ensure review mode only surfaces words that still need review."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 2, 3) 
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" in progress_counter.text
    
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, "flashcards", level)
    completed = {p["wordId"] for p in progress if p["completed"]}
    assert completed, "No completed words found — test precondition failed."
    
    displayed_set = set()
    while True:
        try:
            vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
            word_id = int(vocab.get_attribute("data-word-id"))
            displayed_set.add(word_id)
            o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
            o_btn.click()

            # If alert shows up, review set is done
            try:
                WebDriverWait(driver, 1.5).until(EC.alert_is_present())
                break
            except TimeoutException:
                # no alert -> wait for next card to load
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_element(*VOCAB).get_attribute("data-word-id") != str(word_id)
                )
        except TimeoutException:
            break
            
    assert not (displayed_set & completed), "Memorized words appeared in Review Mode"
    
@pytest.mark.tcid("TC-FC-023")
@pytest.mark.flashcards
def test_review_mode_text_is_displayed_next_to_progress_counter(driver, base_url, admin_email, admin_password):
    """Verify that 'Review Mode' label is displayed next to the progress counter when in review mode."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 0, 5) 
    
    text = progress_counter.text.strip()
    fraction, mode = text.split("(", 1)
    current_str, total_str = [part.strip() for part in fraction.split("/", 1)]
    mode = mode.rstrip(") ").strip() # Because we split the string with '('.

    assert int(current_str) == 0, f"Expected 1 card reviewed, saw {current_str} (text: {text})"
    assert int(total_str) == 5, f"Expected 4 total cards, saw {total_str} (text: {text})"
    assert mode == "Review Mode", f"Expected Review Mode label, saw {mode!r} (text: {text})"
    
@pytest.mark.tcid("TC-FC-024")
@pytest.mark.flashcards
def test_flashcards_review_mode_progress_counter(driver, base_url, admin_email, admin_password):
    """Verify that the progress counter displays correct counts when entering review mode."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    enter_review_mode(driver, 1, 4) 
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    
    text = progress_counter.text.strip()
    fraction, mode = text.split("(", 1)
    current_str, total_str = [part.strip() for part in fraction.split("/", 1)]
    mode = mode.rstrip(") ").strip() # Because we split the string with '('.

    assert int(current_str) == 0, f"Expected 0 card completed, saw {current_str} (text: {text})"
    assert int(total_str) == 4, f"Expected 4 total cards, saw {total_str} (text: {text})"
    assert mode == "Review Mode", f"Expected Review Mode label, saw {mode!r} (text: {text})"
    
@pytest.mark.tcid("TC-FC-026")
@pytest.mark.flashcards
def test_flashcards_progress_reset_modal_message(driver, base_url, admin_email, admin_password):
    """Verify that the progress reset modal displays the correct message upon completion."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    modal_msg = mark_all_flashcards_O_and_accept_alert(driver)
    
    assert modal_msg is not None, "Review modal never appeared"
    assert "Progress has been reset" in modal_msg, "Incorrect modal message"
    
@pytest.mark.tcid("TC-FC-027")
@pytest.mark.flashcards
def test_flashcards_progress_counter_after_reset(driver, base_url, admin_email, admin_password):
    """Verify that the progress counter resets to 0 after completing all flashcards and resetting."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    mark_all_flashcards_O_and_accept_alert(driver)
    
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    current, total = [int(part.strip()) for part in progress_counter.text.split("/")[:2]]
    assert current == 0 and total == 5, f"Progress counter is not reset to 0. Current: {progress_counter.text}"

@pytest.mark.tcid("TC-FC-028")
@pytest.mark.flashcards
def test_flashcards_study_progress_deleted_from_db_after_reset(driver, base_url, admin_email, admin_password):
    """Verify that study progress is completely removed from the database after reset."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    mark_all_flashcards_O_and_accept_alert(driver)
    
    # Assert progress is reset
    cookies = get_auth_cookies(driver)
    progress = get_study_progress(base_url, cookies, "flashcards", level)
    assert progress == [], f"Expected empty list, got {progress}"
    
@pytest.mark.tcid("TC-FC-029")
@pytest.mark.flashcards
def test_flashcards_reset_scope_limited_to_current_level(driver, base_url, admin_email, admin_password):
    """Verify that resetting progress for one level does not affect progress in other levels."""
    
    completed_num = 5
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, "N5")
    study_flashcards(driver, completed_num, 0)
    
    reset_flashcards_level_progress(driver, base_url, "TEST")
    driver.get(f"{base_url}/study/flashcards/TEST")
    modal_msg = mark_all_flashcards_O_and_accept_alert(driver)
    assert modal_msg is not None, "Review modal never appeared"
    assert "Progress has been reset" in modal_msg, "Incorrect modal message"
    
    progress_counter_TEST = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    current_TEST, _ = [int(part.strip()) for part in progress_counter_TEST.text.split("/")[:2]]
    assert current_TEST == 0, f"TEST progress is not reset to 0: {progress_counter_TEST.text}"
    
    driver.get(f"{base_url}/study/flashcards/n5")
    progress_counter_N5 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    current_N5, _ = [int(part.strip()) for part in progress_counter_N5.text.split("/")[:2]]
    assert current_N5 == completed_num, f"N5 progress changed: {progress_counter_N5.text}"
    
@pytest.mark.tcid("TC-FC-030")
@pytest.mark.flashcards
def test_flashcard_order_randomized_after_cycle_reset(driver, base_url, admin_email, admin_password):
    """Verify flashcard order changes after completing and resetting a cycle."""
    
    level = "TEST"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)

    def complete_cycle_and_collect_order():
        order = []
        while True:
            vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
            word_id = vocab.get_attribute("data-word-id")
            order.append(word_id)
            o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
            o_btn.click()
            try:
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert.accept()
                break
            except TimeoutException:
                wait_for_flashcard_advance(driver, word_id)
        return order

    order_1 = complete_cycle_and_collect_order()
    order_2 = complete_cycle_and_collect_order()

    # order 3 is for flakiness guard (may get identical order for small sets)
    if order_2 == order_1:
        order_3 = complete_cycle_and_collect_order()
        assert order_3 != order_1, f"Flashcard order did not change across cycles: {order_1}"
    else:
        assert order_2 != order_1, f"Flashcard order did not change across cycles: {order_1}"

@pytest.mark.tcid("TC-FC-031")
@pytest.mark.flashcards
def test_flashcard_position_persists_after_page_refresh(driver, base_url, admin_email, admin_password):
    """Verify the same flashcard remains selected after a browser refresh."""
    
    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    study_flashcards(driver, 0, 3)
    vocab_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_before = vocab_before.get_attribute("data-word-id")
    
    driver.refresh()
    
    vocab_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_after = vocab_after.get_attribute("data-word-id")
    assert word_id_before == word_id_after, (
        f"Flashcard did not persist after refresh: before={word_id_before}, after={word_id_after}"
    )
    
    study_flashcards(driver, 3, 0)
    vocab_before2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_before2 = vocab_before2.get_attribute("data-word-id")
    
    driver.refresh()
    
    vocab_after2 = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_after2 = vocab_after2.get_attribute("data-word-id")
    assert word_id_before2 == word_id_after2, (
        f"Flashcard did not persist after refresh: before={word_id_before2}, after={word_id_after2}"
    )
    
@pytest.mark.tcid("TC-FC-032")
@pytest.mark.flashcards
def test_flashcard_position_persists_after_logout_login(driver, base_url, admin_email, admin_password):
    """Verify the same flashcard remains selected after logout then login."""
    
    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    study_flashcards(driver, 5, 0)
    vocab_before = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_before = vocab_before.get_attribute("data-word-id")
    
    logout(driver)
    login_and_open_flashcards_page(driver, base_url, admin_email, admin_password, level)
    
    vocab_after = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_after = vocab_after.get_attribute("data-word-id")
    assert word_id_before == word_id_after, (
        f"Flashcard did not persist after re-login: before={word_id_before}, after={word_id_after}"
    )
    
@pytest.mark.tcid("TC-FC-033")
@pytest.mark.flashcards
def test_flashcard_position_persists_after_reopening_browser_or_across_devices(driver_factory, base_url, admin_email, admin_password):
    """Verify the same flashcard remains selected after closing and reopening the browser."""
    
    level = "n2"
    
    # First browser session
    driver1 = driver_factory()
    login_and_open_flashcards_page_with_level_reset(driver1, base_url, admin_email, admin_password, level)
    vocab_before = WebDriverWait(driver1, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_before = vocab_before.get_attribute("data-word-id")
    driver1.quit()
    
    # Second browser session
    driver2 = driver_factory()
    login_and_open_flashcards_page(driver2, base_url, admin_email, admin_password, level)
    vocab_after = WebDriverWait(driver2, 5).until(EC.presence_of_element_located(VOCAB))
    word_id_after = vocab_after.get_attribute("data-word-id")
    
    assert word_id_before == word_id_after, (
        f"Flashcard did not persist after closing and reopening browser: "
        f"before={word_id_before}, after={word_id_after}"
    )
    driver2.quit()
    
@pytest.mark.tcid("TC-FC-034")
@pytest.mark.flashcards
def test_flashcard_progress_persists_on_reenter_normal_mode(driver, base_url, admin_email, admin_password):
    """Verify completed words remain persisted after leaving and re-entering flashcards in Normal mode."""
    
    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" not in progress_counter.text, "Should be in Normal mode, not Review mode"
    
    # Study a few cards
    for _ in range(3):
        o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        o_btn.click()
        
        WebDriverWait(driver, 5).until(
            lambda d: d.find_element(*VOCAB).get_attribute("data-word-id") != current_word_id
        )
        
    cookies = get_auth_cookies(driver)
    progress_before = get_study_progress(base_url, cookies, "flashcards", level)
    completed_before = {p["wordId"] for p in progress_before if p["completed"]}
    word_id_before_exit = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB)).get_attribute("data-word-id")
    
    # Exit and reenter flashcards page
    driver.get(f"{base_url}")
    driver.get(f"{base_url}/study/flashcards/{level}")
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" not in progress_counter.text, "Should be in Normal Mode, not Review Mode"
    
    progress_after = get_study_progress(base_url, cookies, "flashcards", level)
    completed_after = {p["wordId"] for p in progress_after if p["completed"]}
    word_id_after_reentry = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB)).get_attribute("data-word-id")
    
    # Assert persistence
    assert completed_after == completed_before, (
        "Progress did not persist after re-entering flashcards: "
        f"before exit={len(completed_before)}, after re-enter={len(completed_after)}"
    )
    assert word_id_before_exit == word_id_after_reentry, (
        "Normal mode did not resume on the same card: "
        f"before exit={word_id_before_exit}, after re-enter={word_id_after_reentry}"
    )    
    
@pytest.mark.tcid("TC-FC-035")
@pytest.mark.flashcards
def test_flashcard_progress_persists_on_reenter_review_mode(driver, base_url, admin_email, admin_password):
    """Verify completed words remain persisted after leaving and re-entering flashcards in Review mode."""
    
    level = "TEST"
    # Clear any previous progress for TEST set
    login_and_open_flashcards_page_with_level_reset(driver, base_url, admin_email, admin_password, level)
    
    # Complete a cycle to enter Review mode - test set length is 5.
    enter_review_mode(driver, 1, 4) 

    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" in progress_counter.text, "Should be in Review mode, not Normal mode"
    
    # Study a few cards
    for _ in range(2):
        o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        o_btn.click()
        wait_for_flashcard_advance(driver, current_word_id)
        
    cookies = get_auth_cookies(driver)
    progress_before = get_study_progress(base_url, cookies, "flashcards", level)
    completed_before = {p["wordId"] for p in progress_before if p["completed"]}
    word_id_before_exit = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB)).get_attribute("data-word-id")
    
    # Exit and reenter flashcards page
    driver.get(f"{base_url}")
    driver.get(f"{base_url}/study/flashcards/{level}")
    # Wait for the page to load and client-side state to rehydrate before asserting
    progress_counter = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PROG_CNT))
    assert "Review Mode" in progress_counter.text, "Should be in Review Mode, not Normal Mode"
    
    progress_after = get_study_progress(base_url, cookies, "flashcards", level)
    completed_after = {p["wordId"] for p in progress_after if p["completed"]}
    word_id_after_reentry = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB)).get_attribute("data-word-id")
    
    # Assert persistence
    assert completed_after == completed_before, (
        "Progress did not persist after re-entering flashcards: "
        f"before exit={len(completed_before)}, after re-enter={len(completed_after)}"
    )
    assert word_id_before_exit == word_id_after_reentry, (
        "Review mode did not resume on the same card: "
        f"before exit={word_id_before_exit}, after re-enter={word_id_after_reentry}"
    )

@pytest.mark.tcid("TC-FC-036")
@pytest.mark.flashcards
def test_study_progress_deletion_after_account_deletion(driver, base_url, test1_email, test1_password):
    """Verify that flashcard progress is wiped and APIs deny access after deleting the account."""
    
    # Sign up and verify account
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)
    verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10)
    driver.get(verify_url)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'successfully verified')]")))
    
    # Study a few cards
    level = "n2"
    login_and_open_flashcards_page_with_level_reset(driver, base_url, test1_email, test1_password, level)
    for _ in range(5):
        o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        o_btn.click()
        wait_for_flashcard_advance(driver, current_word_id)
        
    # Confirm progress is saved
    cookies = get_auth_cookies(driver)
    progress_before = get_study_progress(base_url, cookies, "flashcards", level)
    assert progress_before, "Progress is not saved in DB"
    
    # Delete account
    r = requests.delete(
        f"{base_url}/api/user",
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()
    
    # Wait until study-progress API returns 401
    elapsed = 0
    while elapsed < 5:
        resp = requests.get(
            f"{base_url}/api/study-progress",
            params={"type": "flashcards", "level": level},
            cookies=cookies,
            timeout=5,
        )
        if resp.status_code == 401:
            break
        elif resp.status_code >= 400:
            resp.raise_for_status()
        time.sleep(0.5)
        elapsed += 0.5
    else:
        pytest.fail(f"Progress API still accessible after account deletion (last status={resp.status_code})")

    assert resp.status_code == 401, f"Expected 401 after account deletion, got {resp.status_code}"
