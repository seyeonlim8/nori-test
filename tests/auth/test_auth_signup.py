import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.auth_flows import fill_signup_form, fill_and_submit_signup, make_unique_username

SIGNUP_BTN = (By.XPATH, '//button[text()="Sign Up"]')
USERNAME = (By.XPATH, "//input[@placeholder='Username']")
USERNAME_FB = (By.CSS_SELECTOR, "[data-testid='username-feedback']")
EMAIL = (By.XPATH, "//input[@placeholder='Email']")
PASSWORD = (By.XPATH, "//input[@placeholder='Password']")
CONFIRM_PW = (By.XPATH, "//input[@placeholder='Confirm Password']")
CONFIRM_PW_ERR = (By.CSS_SELECTOR, "[data-testid='confirm-pw-error']")
EMAIL_ERR = (By.CSS_SELECTOR, "[data-testid='email-error']")

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
def test_signup_positive_feedback(driver, base_url, test1_email, test1_password):
    uname = make_unique_username()
    fill_signup_form(driver, base_url, uname, test1_email, test1_password)

    # Username: wait for positive text (allow up to 5s for network debounce)
    username_feedback = (USERNAME_FB)
    WebDriverWait(driver, 5).until(EC.visibility_of_element_located(username_feedback))
    WebDriverWait(driver, 5).until(
        EC.text_to_be_present_in_element(username_feedback, "Username available"),
        message="Username feedback did not show 'Username available'"
    )

    # Email: error disappears (≤500ms)
    email_err = (EMAIL_ERR)
    WebDriverWait(driver, 0.5).until(
        EC.invisibility_of_element_located(email_err),
        message="Email error stayed visible"
    )

    # Password checklist: all green
    bad = driver.find_elements(
        By.CSS_SELECTOR, "[data-testid='password-checklist'] li:not(.text-green-600)"
    )
    assert len(bad) == 0, f"These rules are not green: {[el.text for el in bad]}"

    # Confirm password: error disappears (≤500ms)
    confirm_pw_err = (CONFIRM_PW_ERR)
    WebDriverWait(driver, 0.5).until(
        EC.invisibility_of_element_located(confirm_pw_err),
        message="Confirm password error stayed visible"
    )
    
@pytest.mark.tcid("TC-AUTH-003")
@pytest.mark.auth
def test_duplicate_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    # Username test1 already exists in DB
    driver.find_element(*USERNAME).send_keys("Test1")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((USERNAME_FB))
        )
    except Exception:
        pytest.fail("Username feedback error message not found for duplicate username")
    assert "Username is already in use" in error_msg.text
    
@pytest.mark.tcid("TC-AUTH-004")
@pytest.mark.auth
def test_short_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    driver.find_element(*USERNAME).send_keys("ab")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((USERNAME_FB))
        )
    except Exception:
        pytest.fail("Username feedback error message not found")
    assert "Username must be 4-19 characters" in error_msg.text
    
@pytest.mark.tcid("TC-AUTH-005")
@pytest.mark.auth
def test_long_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    driver.find_element(*USERNAME).send_keys("abcdefghiklmnopqrstuvwxyz")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((USERNAME_FB))
        )
    except Exception:
        pytest.fail("Username feedback error message not found")
    assert "Username must be 4-19 characters" in error_msg.text
    
@pytest.mark.tcid("TC-AUTH-006")
@pytest.mark.auth
def test_special_char_username_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    driver.find_element(*USERNAME).send_keys("Test#$%")
    try:
        error_msg = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((USERNAME_FB))
        )
    except Exception:
        pytest.fail("Username feedback error message not found")
    assert "characters, letters and numbers only" in error_msg.text

@pytest.mark.tcid("TC-AUTH-007")
@pytest.mark.auth
@pytest.mark.parametrize("value,valid", [
    ("plain", False),
    ("a@", False),
    ("a@b", False),
    ("a@b.", False),
    ("a@b.c", False),
    ("user.name+tag@ex.co", True),
])
def test_invalid_email_format_feedback(driver, base_url, value, valid):
    driver.get(f"{base_url}/signup")
    driver.find_element(*EMAIL).send_keys(value)

    if valid:
        WebDriverWait(driver, 0.5).until(
            EC.invisibility_of_element_located(EMAIL_ERR),
            message=f"Email error should be hidden for valid value: {value!r}"
        )
    else:
        WebDriverWait(driver, 0.5).until(
            EC.visibility_of_element_located(EMAIL_ERR),
            message=f"Email error was not shown for invalid value: {value!r}"
        )
        msg = driver.find_element(*EMAIL_ERR).text
        assert "Invalid email format" in msg, "Email format error message not visible"
        
@pytest.mark.tcid("TC-AUTH-008")
@pytest.mark.auth
def test_live_password_checklist_update(driver, base_url):
    driver.get(f"{base_url}/signup")
    password = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(PASSWORD)
    )
    
    def rule_green(testid):
        el = driver.find_element(By.CSS_SELECTOR, f"[data-testid='{testid}']")
        cls = el.get_attribute("class") or ""
        return "text-green-600" in cls
        
    def wait_green(testid, timeout=0.5):
        WebDriverWait(driver, timeout).until(lambda d: rule_green(testid), f"{testid} did not turn green")
        
    # All rules red when field is empty
    for tid in ["pw-rule-lowercase","pw-rule-uppercase","pw-rule-number","pw-rule-special-char","pw-rule-length"]:
        assert not rule_green(tid), f"{tid} unexpectedly green at start"
        
    # Type lowercase - only lowercase rule turns green
    password.send_keys("a")
    wait_green("pw-rule-lowercase")
    assert not rule_green("pw-rule-uppercase")
    assert not rule_green("pw-rule-number")
    assert not rule_green("pw-rule-special-char")
    assert not rule_green("pw-rule-length")
    
    # Add uppercase
    password.send_keys("A")
    wait_green("pw-rule-uppercase")
    assert not rule_green("pw-rule-number")
    assert not rule_green("pw-rule-special-char")
    assert not rule_green("pw-rule-length")
    
    # Add number
    password.send_keys("1")
    wait_green("pw-rule-number")
    assert not rule_green("pw-rule-special-char")
    assert not rule_green("pw-rule-length")
    
    # Add special character
    password.send_keys("!")
    wait_green("pw-rule-special-char")
    assert not rule_green("pw-rule-length")
    
    # Reach length >= 6
    password.send_keys("bc")
    wait_green("pw-rule-length")
    
    # Final sanity check
    bad = driver.find_elements(
        By.CSS_SELECTOR, "[data-testid='password-checklist'] li:not(.text-green-600)"
    )
    assert len(bad) == 0, f"These rules are not green: {[el.text for el in bad]}"
    
@pytest.mark.tcid("TC-AUTH-009")
@pytest.mark.auth
def test_confirm_password_feedback(driver, base_url):
    driver.get(f"{base_url}/signup")
    pw = driver.find_element(*PASSWORD)
    confirm_pw = driver.find_element(*CONFIRM_PW)
    
    pw.send_keys("Password!123")
    confirm_pw.send_keys("WrongPassword!123")
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(CONFIRM_PW_ERR),
        message="Confirm password error was not shown"
    )
    err = driver.find_element(*CONFIRM_PW_ERR).text
    assert "Passwords do not match" in err

@pytest.mark.tcid("TC-AUTH-010")
@pytest.mark.auth
def test_signup_button_disabled(driver, base_url, test1_email, test1_password):
    driver.get(f"{base_url}/signup")
    signup_btn = driver.find_element(*SIGNUP_BTN)

    # All fields empty - btn disabled
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when all fields are empty"

    # Username only - btn disabled
    signup_btn = driver.find_element(*SIGNUP_BTN)
    driver.find_element(*USERNAME).send_keys(make_unique_username())
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when only username is filled"

    # Username, email only - btn disabled
    signup_btn = driver.find_element(*SIGNUP_BTN)    
    driver.find_element(*EMAIL).send_keys(test1_email)
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when only username and email are filled"

    # Username, email, password only - btn disabled
    signup_btn = driver.find_element(*SIGNUP_BTN) 
    driver.find_element(*PASSWORD).send_keys(test1_password)
    assert signup_btn.is_enabled() is False, "Sign up button should be disabled when confirm password is empty"
    
    # All fields filled - btn enabled
    driver.find_element(*CONFIRM_PW).send_keys(test1_password)
    assert signup_btn.is_enabled() is True, "Sign up button should be enabled when all fields are properly filled"