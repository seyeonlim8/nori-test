import datetime
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.auth_flows import login, fill_and_submit_signup, make_unique_username
from utils.mailhog_client import wait_for_email, clear_inbox

LOGIN_BTN = (By.XPATH, '//button[text()="Log In"]')
LOGIN_ERR = (By.CSS_SELECTOR, "[data-testid='credentials-error']")
NAV_HELLO = (By.CSS_SELECTOR, "[data-testid='nav-hello']")
RESEND_BTN = (By.CSS_SELECTOR, "[data-testid='resend-verification-btn']")
SUBJECT = "NORI Email Verification"

def _dismiss_alert_if_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except Exception:
        pass
    
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
        EC.visibility_of_element_located(LOGIN_ERR),
        message="Login error not found"
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
    driver.get(f"{base_url}/login") # DO NOT REMOVE THIS LINE  
    # Start clean
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    driver.delete_all_cookies()
    
    login(driver, base_url, "invalidEmail@gmail.com", "InvalidPassword!123")
    
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(LOGIN_ERR),
        message="Login error not found"
    )
    assert "Invalid email or password" in error_msg.text, "Expected error message for invalid credentials not found."
    assert "4 attempts remaining" in error_msg.text, f"Expected 4 attempts remaining message not found - got {error_msg.text}"
    
    # Second bad attempt - 3 remaining
    login(driver, base_url, "invalidEmail@gmail.com", "InvalidPassword!123")
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(LOGIN_ERR),
        message="Login error not found"
    )
    assert "3 attempts remaining" in error_msg.text, "Expected 3 attempts remaining message not found."

@pytest.mark.tcid("TC-AUTH-024")
@pytest.mark.auth
def test_lockout_msg(driver, base_url):
    driver.get(f"{base_url}/login") # DO NOT REMOVE THIS LINE
    # Start clean
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    driver.delete_all_cookies()
    
    for attempt in range(1, 6):
        login(driver, base_url, "invalidEmail@gmail.com", "InvalidPassword!123")
        error_msg = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located(LOGIN_ERR),
            message="Login error not found"
        )
        if attempt < 5:
            # Before the 5th attempt - no lockout
            assert "Account locked for" not in error_msg.text and "Please try again later" not in error_msg.text, \
                f"Lockout text appeared too early on attempt {attempt}"

        else:
            # 5th failed attempt - lockout & login button disabled
            login_btn = driver.find_element(*LOGIN_BTN)
            assert login_btn.is_enabled() is False, "Login button should be disabled after 5 failed attempts"
            assert "Please try again later" in error_msg.text, "Missing 'Please try again later' on 5th failure."
            assert "Remaining lockout time" in error_msg.text, "Missing 'Remaining lockout time' on 5th failure."
            
@pytest.mark.tcid("TC-AUTH-026")
@pytest.mark.auth
def test_resend_verification_button(driver, base_url, admin_email, test1_email, test1_password):
    # Create new account without verification
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)
    
    msg = wait_for_email(test1_email, SUBJECT, timeout_s=15, poll_s=1)
    assert msg is not None, "Signup didn’t complete (no email yet)."
    
    # Attempt login with unverified account
    login(driver, base_url, test1_email, test1_password)
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located(LOGIN_ERR),
        message="Login error not found"
    )
    assert "Please verify your email first" in error_msg.text
    
    resend_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(RESEND_BTN),
        message="Resend button not found/clickable"
    )
    since = datetime.datetime.now(datetime.timezone.utc)
    resend_btn.click()
     
    # Get the email & verify email content
    new_msg = wait_for_email(test1_email, SUBJECT, timeout_s=30, poll_s=1, since=since)
    assert new_msg is not None, "Expected verification email was not received within 30s"

    hdr = new_msg["Content"]["Headers"]
    from_val = hdr.get("From", [""])[0]
    subj_val = hdr.get("Subject", [""])[0]
    assert "NORI" in from_val, "Email is not from NORI"
    assert subj_val == SUBJECT, "Incorrect subject"
    
@pytest.mark.tcid("TC-AUTH-027")
@pytest.mark.auth
def test_session_persists_across_tabs(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(NAV_HELLO),
        "User failed to login"
    )
    
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1]) # open newest tab
    driver.get(f"{base_url}")
    
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(NAV_HELLO),
        "User was unexpectedly logged out after opening a new tab"
    )
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
@pytest.mark.tcid("TC-AUTH-028")
@pytest.mark.auth
def test_session_persists_after_refresh(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(NAV_HELLO),
        "User failed to login"
    )
    
    driver.refresh()
    
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(NAV_HELLO),
        "User failed to login"
    )

@pytest.mark.tcid("TC-AUTH-027")
@pytest.mark.auth
def test_no_session_data_in_storage(driver, base_url, admin_email, admin_password):
    login(driver, base_url, admin_email, admin_password)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(NAV_HELLO),
        "User failed to login"
    )
    
    local_data = driver.execute_script("return window.localStorage;")
    session_data = driver.execute_script("return window.sessionStorage;")
    
    all_keys = list(local_data.keys()) + list(session_data.keys())
    all_values = list(local_data.values()) + list(session_data.values())
    
    forbidden_keywords = ["token", "auth", "session", "jwt", "password"]
    for key, value in zip(all_keys, all_values):
        key_lower = str(key).lower()
        value_lower = str(value).lower()
        for word in forbidden_keywords:
            assert word not in key_lower and word not in value_lower, (
                f"Sensitive data found in storage: {key} -> {value}"
            )