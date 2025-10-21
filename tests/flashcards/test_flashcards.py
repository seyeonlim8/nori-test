import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import login

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
FC_BTN = (By.CSS_SELECTOR, "[data-testid='flashcards-btn']")
N2_BTN = (By.CSS_SELECTOR, "[data-testid='level-btn-n2']")
VOCAB = (By.CSS_SELECTOR, "[data-testid='vocabulary']")
FURIGANA = (By.CSS_SELECTOR, "[data-testid='furigana']")

@pytest.mark.tcid("TC-FC-001")
@pytest.mark.auth
def test_flashcard_vocabulary_visible(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )

    # Navigate to flashcards page (N2)
    study_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(STUDY_BTN),
        "Study button is not found"
    )
    ActionChains(driver).move_to_element(study_btn).perform()
    flashcards_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(FC_BTN),
        "Flashcards button is not clickable"
    )
    flashcards_btn.click()
    level_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(N2_BTN),
        "N2 button is not clickable"
    )
    level_btn.click()

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
    
    