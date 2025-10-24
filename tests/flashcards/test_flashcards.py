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