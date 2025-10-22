import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.flashcards_flows import open_flashcards_page

VOCAB = (By.CSS_SELECTOR, "[data-testid='vocabulary']")
FURIGANA = (By.CSS_SELECTOR, "[data-testid='furigana']")

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
