import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import login

@pytest.mark.tcid("TC-LEVEL-001")
@pytest.mark.auth
def test_all_jlpt_levels_visible(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)
    
    pages = ["flashcards", "quiz", "fill-in-the-blank"]
    expected_levels = ["n5", "n4", "n3", "n2", "n1"]
    
    for page in pages:
        driver.get(f"{base_url}/study/{page}")
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid^='level-btn']")),
            f"Level buttons not visible on {page.capitalize()} page"
        )
        
        found_levels = []
        elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid^='level-btn-']")
        for el in elements:
            lv = el.get_attribute("data-testid").replace("level-btn-", "")
            found_levels.append(lv)
            
        for level in expected_levels:
            assert level in found_levels, f"Level {level.upper} missing on {page.capitalize()} page"