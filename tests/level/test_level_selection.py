import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import login

@pytest.mark.tcid("TC-LEVEL-001")
@pytest.mark.auth
def test_all_jlpt_levels_visible(driver, base_url, admin_email, admin_password):
    """Verify all JLPT level buttons (N5–N1) are visible across study pages."""

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
    
@pytest.mark.tcid("TC-LEVEL-002")
@pytest.mark.auth
def test_level_card_hover_animation_triggers(driver, base_url, admin_email, admin_password):
    """Verify level card hover triggers a CSS transform animation on the button."""

    login(driver, base_url, admin_email, admin_password)
    driver.get(f"{base_url}/study/flashcards")
    
    level_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='level-btn-n5']")),
        "Level N5 button not found on page"
    )
    
    before = level_btn.value_of_css_property("transform")
    ActionChains(driver).move_to_element(level_btn).perform()
    wait_for_transform_change(driver, level_btn, before, timeout=1.5)
    after = level_btn.value_of_css_property("transform")
    assert before != after, f"Hover animation did not trigger; transform unchanged"
    
def wait_for_transform_change(driver, element, old_val, timeout=1.0, poll_interval=0.05):
    WebDriverWait(driver, timeout, poll_interval).until(
        lambda d: element.value_of_css_property("transform") != old_val,
        "Hover transform animation did not trigger"
    )
