import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.auth_flows import login

LOGIN_ERR = (By.CSS_SELECTOR, "[data-testid='credentials-error']")
NAV_HELLO = (By.CSS_SELECTOR, "[data-testid='nav-hello']")

@pytest.mark.tcid("TC-AUTH-021")
@pytest.mark.auth
def test_login_success(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/"))
    assert driver.current_url == f"{base_url}/", f"Expected URL to be '{base_url}/' but got '{driver.current_url}'"

    nav_hello = WebDriverWait(driver, 5).until(EC.presence_of_element_located(NAV_HELLO))
    assert nav_hello.text.startswith("Hello"), "Expected greeting to start with 'Hello'"

@pytest.mark.tcid("TC-AUTH-022")
@pytest.mark.auth
def test_login_invalid_credentials(driver, base_url, test1_email, test1_password):
    # Invalid email, valid password
    login(driver, base_url, "randomemail@random.com", test1_password)
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(LOGIN_ERR)
    )
    assert "Invalid email or password" in error_msg.text, "Expected error message for invalid credentials not found."
    
    # Valid email, invalid password
    login(driver, base_url, test1_email, "IncorrectPassword!123")
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(LOGIN_ERR)
    )
    assert "Invalid email or password" in error_msg.text, "Expected error message for invalid credentials not found."

@pytest.mark.tcid("TC-AUTH-023")
@pytest.mark.auth
def test_login_attempts_remaining_msg(driver, base_url):
    driver.get(f"{base_url}/login")
    
    # Start clean
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    driver.delete_all_cookies()
    
    login(driver, base_url, "invalidEmail@gmail.com", "InvalidPassword!123")
    
    error_msg = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(LOGIN_ERR))
    assert "Invalid email or password" in error_msg.text, "Expected error message for invalid credentials not found."
    assert "4 attempts remaining" in error_msg.text, f"Expected 4 attempts remaining message not found - got {error_msg.text}"
    
    # Second bad attempt - 3 remaining
    login(driver, base_url, "invalidEmail@gmail.com", "InvalidPassword!123")
    error_msg = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(LOGIN_ERR))
    assert "3 attempts remaining" in error_msg.text, "Expected 3 attempts remaining message not found."
