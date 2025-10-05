import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.auth_flows import login

@pytest.mark.tcid("TC-AUTH-018")
@pytest.mark.auth
def test_login_success(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/"))
    assert driver.current_url == f"{base_url}/"

    nav_hello = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='nav-hello']")))
    assert nav_hello.text.startswith("Hello")

@pytest.mark.tcid("TC-AUTH-019")
@pytest.mark.auth
def test_login_invalid_credentials(driver, base_url, test1_email, test1_password):
    # Invalid email, valid password
    login(driver, base_url, "randomemail@random.com", test1_password)
    error_msg = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='credentials-error']"))
    )
    assert "Invalid email or password" in error_msg.text

    # Valid email, invalid password
    login(driver, base_url, test1_email, "IncorrectPassword!123")
    error_msg = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='credentials-error']"))
    )
    assert "Invalid email or password" in error_msg.text
