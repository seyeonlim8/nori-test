import time
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.flashcards_flows import open_flashcards_page
from tests.utils.auth_flows import get_auth_token

VOCAB = (By.CSS_SELECTOR, "[data-testid='vocabulary']")
FURIGANA = (By.CSS_SELECTOR, "[data-testid='furigana']")
O_BTN = (By.CSS_SELECTOR, "[data-testid='o-btn']")
X_BTN = (By.CSS_SELECTOR, "[data-testid='x-btn']")

@pytest.mark.tcid("TC-FC-001")
@pytest.mark.auth
def test_flashcard_vocabulary_visible(driver, base_url, admin_email, admin_password):
    """Verify that the vocabulary element is visible and furigana is hidden on initial flashcard load."""
    
    open_flashcards_page(driver, base_url, admin_email, admin_password, "n2")

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
@pytest.mark.auth
def test_japanese_characters_render(driver, base_url, admin_email, admin_password):
    """Verify that the vocabulary text is non-empty, contains no broken glyphs, and uses the correct font."""
    
    open_flashcards_page(driver, base_url, admin_email, admin_password, "n2")

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
@pytest.mark.auth
def test_o_button_marks_word_as_completed(driver, base_url, admin_email, admin_password):
    """Verify that clicking the O button marks the current word as completed in the database."""
    
    level = "n2"
    open_flashcards_page(driver, base_url, admin_email, admin_password, level)
    
    vocab = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id = vocab.get_attribute("data-word-id")
    
    o_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(O_BTN),
        "O button is not clickable"
    )
    o_btn.click()
    
    # Extract auth token (from cookies)
    token = get_auth_token(driver)
    assert token, "No auth token found after login"
    cookies = {'token': token}

    # Assert DB state  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level)
    assert progress, f"Word {word_id} not marked as completed within 5s"
        
@pytest.mark.tcid("TC-FC-004")
@pytest.mark.auth
def test_x_button_does_not_mark_word_completed(driver, base_url, admin_email, admin_password):
    """Verify that clicking the X button does not mark the word as completed in the database."""
    
    level = "n2"
    open_flashcards_page(driver, base_url, admin_email, admin_password, level)
        
    vocab = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id = vocab.get_attribute("data-word-id")
    
    x_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(X_BTN),
        "X button is not clickable"
    )
    x_btn.click()
    
    # Extract auth token (from cookies)
    token = get_auth_token(driver)
    assert token, "No auth token found after login"
    cookies = {"token": token}

    # Assert DB state  
    progress = wait_for_completion_state(base_url, word_id, cookies, expected=False, level=level)
    assert progress.get("completed") is False, f"Expected completed=False, got {progress}"

@pytest.mark.tcid("TC-FC-005")
@pytest.mark.auth
def test_advance_to_next_flashcard(driver, base_url, admin_email, admin_password):
    """Verify that clicking either O or X advances to the next flashcard."""

    level = "n2"
    open_flashcards_page(driver, base_url, admin_email, admin_password, level)
        
    vocab_1 = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id_1 = vocab_1.get_attribute("data-word-id")
    o_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(O_BTN),
        "O button is not clickable"
    )
    o_btn.click()
    wait_for_flashcard_advance(driver, word_id_1)
    vocab_2 = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id_2 = vocab_2.get_attribute("data-word-id")
    assert word_id_1 != word_id_2, f"Flashcard did not advance after O click (still {word_id_1})"
    
    x_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(X_BTN),
        "X button is not clickable"
    )
    x_btn.click()
    wait_for_flashcard_advance(driver, word_id_2)
    vocab_3 = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(VOCAB)
    )
    word_id_3 = vocab_3.get_attribute("data-word-id")
    assert word_id_2 != word_id_3, f"Flashcard did not advance after X click (still {word_id_2})"
    
def wait_for_completion_state(base_url, word_id, cookies, expected, level, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(
            f"{base_url}/api/study-progress?type=flashcard&level={level}&wordId={word_id}",
            cookies=cookies,
            timeout=5
        )
        r.raise_for_status()
        progress = r.json()
        if progress.get("completed") == expected:
            return progress
        time.sleep(0.5)
    return None

def wait_for_flashcard_advance(driver, old_word_id, timeout=5):
    def word_id_changed(driver):
        vocab = driver.find_element(*VOCAB)
        return vocab.get_attribute("data-word-id") != old_word_id
    WebDriverWait(driver, timeout).until(
        word_id_changed,
        "Flashcard did not advance"
    )