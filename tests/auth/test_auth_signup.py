import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.tcid("TC-AUTH-001")
@pytest.mark.auth
def test_signup_success(driver, base_url, test1_email, test1_password):
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("Test1")
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(test1_email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(test1_password)
    driver.find_element(By.XPATH, '//button[text()="Sign Up"]').click()

    WebDriverWait(driver, 5).until(EC.alert_is_present())

    alert = driver.switch_to.alert
    assert "Please check your email to verify your account." in alert.text

    alert.accept()

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/login"))
    assert driver.current_url == f"{base_url}/login"

@pytest.mark.tcid("TC-AUTH-007")
@pytest.mark.auth
def test_signup_button_disabled(driver, base_url, test1_email, test1_password):
    driver.get(f"{base_url}/signup")
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]')

    # All fields empty - btn disabled
    assert signup_btn.is_enabled() is False

    # Username only - btn disabled
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]')
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("Test1")
    assert signup_btn.is_enabled() is False

    # Username, email only - btn disabled
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]')    
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(test1_email)
    assert signup_btn.is_enabled() is False

    # All fields filled - btn enabled
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]') 
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(test1_password)
    assert signup_btn.is_enabled() is True
