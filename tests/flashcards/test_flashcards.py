import time
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.flashcards_flows import open_flashcards_page

VOCAB = (By.CSS_SELECTOR, "[data-testid='vocabulary']")
FURIGANA = (By.CSS_SELECTOR, "[data-testid='furigana']")
O_BTN = (By.CSS_SELECTOR, "[data-testid='o-btn']")

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
    open_flashcards_page(driver, base_url, admin_email, admin_password, "n2")
    
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
    token = None
    for cookie in driver.get_cookies():
        if cookie['name'] == 'token':
            token = cookie['value']
            break

    assert token, "No auth token found in browser cookies after login"

    # Assert DB state  
    cookies = {'token': token}
    max_wait = 5
    deadline = time.time() + max_wait
    progress = None

    # Handle backend lag
    while time.time() < deadline:
        r = requests.get(
            f"{base_url}/api/study-progress?type=flashcard&level=n2&wordId={word_id}",
            cookies=cookies,
            timeout=5
        )
        r.raise_for_status()
        progress = r.json()
        if progress.get("completed") is True:
            break
        time.sleep(0.5)

    assert progress and progress.get("completed") is True, \
        f"Word {word_id} not marked completed within {max_wait}s (last response: {progress})"
