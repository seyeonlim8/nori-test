import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import login, logout, assert_no_sensitive_data_in_storage

LOGIN_BTN = (By.CSS_SELECTOR, "[data-testid='login-btn']")

@pytest.mark.tcid("TC-AUTH-029")
@pytest.mark.auth
def test_logout_success(driver, base_url, admin_email, admin_password):
    """Verify logout succeeds and login button reappears; storage has no sensitive data."""

    login(driver, base_url, admin_email, admin_password)

    logout(driver)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(LOGIN_BTN),
        "Login button not found"
    )
    
    assert_no_sensitive_data_in_storage(driver)
    
@pytest.mark.tcid("TC-AUTH-030")
@pytest.mark.auth
def test_redirection_to_login_page_after_logout(driver, base_url, admin_email, admin_password):
    """Verify the app redirects to the login page after logging out."""

    login(driver, base_url, admin_email, admin_password)
    
    logout(driver)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/login"), 
        "Did not redirect to login page after logout"
    )
    assert driver.current_url == f"{base_url}/login", "Not redirected to login page after logout"
