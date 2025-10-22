from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import login

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
FC_BTN = (By.CSS_SELECTOR, "[data-testid='flashcards-btn']")

def open_flashcards_page(driver, base_url, email, password, level):
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )

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
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='level-btn-{level.lower()}']")),
        f"{level.upper()} button is not clickable"
    )
    level_btn.click()