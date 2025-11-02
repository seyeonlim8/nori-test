import datetime
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.utils.auth_flows import make_unique_username, fill_and_submit_signup, login, logout, assert_logged_in, assert_no_verify_error, new_chrome_like_fixture
from tests.utils.email_verification import fetch_verify_url_from_mailhog
from tests.utils.mailhog_client import wait_for_email, extract_plain_html

SUBJECT = "NORI Email Verification"
RESEND_BTN = (By.CSS_SELECTOR, "[data-testid='resend-verification-btn']")

@pytest.mark.tcid("TC-AUTH-011")
@pytest.mark.auth
def test_email_verification_sent(driver, base_url, test1_email, test1_password):
    """Verify that a verification email is sent on signup and contains correct headers/body."""

    # Sign up
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)

    # Get the email
    msg = wait_for_email(test1_email, SUBJECT, timeout_s=30)
    assert msg is not None, "Expected verification email was not received within 30s."

    # Verify email content
    hdr = msg["Content"]["Headers"]
    from_val = hdr.get("From", [""])[0]
    subj_val = hdr.get("Subject", [""])[0]
    assert "NORI" in from_val, "Email is not from NORI"
    assert subj_val == SUBJECT, "Incorrect email subject"
    
    plain, html = extract_plain_html(msg)
    body = html or plain
    assert "Verify your email to join NORI" in body and "just ignore this email" in body and "Verify" in body, "Incorrect email body"

@pytest.mark.tcid("TC-AUTH-013")
@pytest.mark.auth
def test_token_uniqueness_with_resend(driver, base_url, test1_email, test1_password):
    """Verify that resending verification issues a new token/URL different from the original."""

    uname = make_unique_username()
    since = datetime.datetime.now(datetime.timezone.utc)
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)
    
    # Get first token
    first_verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10, since=since)
    
    # Resend verification email
    login(driver, base_url, test1_email, test1_password)
    resend_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(RESEND_BTN),
        message="Resend button not found/clickable"
    )
    since = datetime.datetime.now(datetime.timezone.utc)
    resend_btn.click()
    
    # Get second token
    second_verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10, since=since)
    assert first_verify_url != second_verify_url
    
@pytest.mark.tcid("TC-AUTH-014")
@pytest.mark.auth
def test_old_token_is_invalid(driver, base_url, test1_email, test1_password):
    """Verify that the first (old) token becomes invalid after requesting a resend."""

    uname = make_unique_username()
    since = datetime.datetime.now(datetime.timezone.utc)
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)
    
    # Get first token
    first_verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10, since=since)
    
    # Resend verification email
    login(driver, base_url, test1_email, test1_password)
    resend_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(RESEND_BTN),
        message="Resend button not found/clickable"
    )
    since = datetime.datetime.now(datetime.timezone.utc)
    resend_btn.click()
    
    # Get second token
    second_verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10, since=since)
    
    # Assert failure UI - old token
    driver.get(first_verify_url)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Invalid or expired')]")),
        message="Expected an 'invalid' verification message but none appeared."
    )
    
    # Assert success UI - new token
    driver.get(second_verify_url)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'successfully verified')]")),
        message="Expected a verification success message but none appeared."
    )    

@pytest.mark.tcid("TC-AUTH-016")
@pytest.mark.auth
def test_account_activation_via_email_link(driver, base_url, test1_email, test1_password):
    """Verify that visiting the email verification link marks the account verified (UI + DB)."""

    # Sign up
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)

    # Get the email 
    verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10)
    driver.get(verify_url)
    
    # Assert success UI
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'successfully verified')]")),
        message="Expected a verification success message but none appeared."
    )
    
    # Assert DB state
    r = requests.get(f"{base_url}/api/auth/verify", params={"email": test1_email}, timeout=5)
    r.raise_for_status()
    assert r.json().get("isVerified") is True, "Account is not verified in DB"

@pytest.mark.tcid("TC-AUTH-017")
@pytest.mark.auth
def test_verification_link_is_one_time_use(driver, base_url, test1_email, test1_password):
    """Verify that the verification link works once and then shows an invalid/expired message."""

    # Sign up
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)
    
    # Get the email
    verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10)
    
    # Assert success UI - first click
    driver.get(verify_url)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'successfully verified')]")),
        message="Expected a verification success message but none appeared."
    )
    
    # Assert failure UI - second click
    driver.get(verify_url)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Invalid or expired')]")),
        message="Expected an 'invalid' verification message but none appeared."
    )

@pytest.mark.tcid("TC-AUTH-018")
@pytest.mark.auth
def test_account_activation_status_persists(driver, base_url, admin_email, admin_password):
    """Verify that verified status persists across logout/login and a fresh browser session."""

    # Login (session A)
    login(driver, base_url, admin_email, admin_password)
    assert_logged_in(driver, base_url)
    assert_no_verify_error(driver)
    
    # Logout and login again - activation status should persist
    logout(driver)
    login(driver, base_url, admin_email, admin_password)
    assert_logged_in(driver, base_url)
    assert_no_verify_error(driver)
    
    # Open a fresh browser - activation status should persist
    fresh_browser = new_chrome_like_fixture()
    try:
        login(fresh_browser, base_url, admin_email, admin_password)
        assert_logged_in(driver, base_url)
        assert_no_verify_error(driver)
    finally:
        fresh_browser.quit()

@pytest.mark.tcid("TC-AUTH-019")
@pytest.mark.auth
def test_invalid_token_rejected(driver, base_url):
    """Verify that an invalid/garbage token shows an invalid or expired verification message."""

    driver.get(f"{base_url}/verify?token=abc")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Invalid or expired')]")),
        message="Expected an 'invalid' verification message but none appeared."
    )

def _dismiss_alert_if_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except Exception:
        pass