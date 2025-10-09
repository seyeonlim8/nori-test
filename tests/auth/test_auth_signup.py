import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.auth_flows import fill_and_submit_signup, make_unique_username

@pytest.mark.tcid("TC-AUTH-001")
@pytest.mark.auth
def test_signup_success(driver, base_url, test1_email, test1_password):
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)

    WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    text = alert.text or ""
    assert "Please check your email" in text, "Sign up success alert not visible"
    alert.accept()

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/login")), "Timeout waiting for redirect to login page"
    assert driver.current_url == f"{base_url}/login", "User not redirected to login page"

@pytest.mark.tcid("TC-AUTH-002")
@pytest.mark.auth


@pytest.mark.tcid("TC-AUTH-003")
@pytest.mark.auth
def test_duplicate_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    # Username test1 already exists in DB
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("Test1")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='username-feedback']"))
        )
    except Exception:
        pytest.fail("Username feedback error message not found for duplicate username")
    assert "Username is already in use" in error_msg.text
    
@pytest.mark.tcid("TC-AUTH-004")
@pytest.mark.auth
def test_short_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("ab")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='username-feedback']"))
        )
    except Exception:
        pytest.fail("Username feedback error message not found")
    assert "Username must be 4-19 characters" in error_msg.text
    
@pytest.mark.tcid("TC-AUTH-005")
@pytest.mark.auth
def test_long_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("abcdefghiklmnopqrstuvwxyz")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='username-feedback']"))
        )
    except Exception:
        pytest.fail("Username feedback error message not found")
    assert "Username must be 4-19 characters" in error_msg.text
    
@pytest.mark.tcid("TC-AUTH-006")
@pytest.mark.auth
def test_special_char_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("Test#$%")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='username-feedback']"))
        )
    except Exception:
        pytest.fail("Username feedback error message not found")
    assert "characters, letters and numbers only" in error_msg.text

@pytest.mark.tcid("TC-AUTH-011")
@pytest.mark.auth
def test_signup_button_disabled(driver, base_url, test1_email, test1_password):
    driver.get(f"{base_url}/signup")
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]')

    # All fields empty - btn disabled
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when all fields are empty"

    # Username only - btn disabled
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]')
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys(make_unique_username())
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when only username is filled"

    # Username, email only - btn disabled
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]')    
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(test1_email)
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when only username and email are filled"

    # Username, email, password only - btn disabled
    signup_btn = driver.find_element(By.XPATH, '//button[text()="Sign Up"]') 
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(test1_password)
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when confirm password is empty"
    
    # All fields filled - btn enabled
    driver.find_element(By.XPATH, "//input[@placeholder='Confirm Password']").send_keys(test1_password)
    assert signup_btn.is_enabled() is True, "Sign up button should be enabled when all fields are properly filled"