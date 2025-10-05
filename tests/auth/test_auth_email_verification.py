import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.auth_flows import make_unique_username, fill_and_submit_signup
from utils.email_verification import fetch_verify_url_from_mailhog
from utils.mailhog_client import wait_for_email, extract_plain_html

SUBJECT = "NORI Email Verification"

def _dismiss_alert_if_present(driver, timeout=3):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except Exception:
        pass
    
def test_email_verification_sent(driver, base_url, test1_email, test1_password):
    # Sign up
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)

    # Get the email
    msg = wait_for_email(test1_email, SUBJECT, timeout_s=10)
    assert msg is not None, "Expected verification email was not received within 10s."

    # Verify email content
    hdr = msg["Content"]["Headers"]
    from_val = hdr.get("From", [""])[0]
    subj_val = hdr.get("Subject", [""])[0]
    assert "NORI" in from_val
    assert subj_val == SUBJECT
    
    plain, html = extract_plain_html(msg)
    body = html or plain
    assert "Verify your email to join NORI" in body
    assert "just ignore this email" in body
    assert "Verify" in body

def test_account_activation_via_email_link(driver, base_url, test1_email, test1_password):
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
    assert r.json().get("isVerified") is True
    
def test_verification_link_is_one_time_use(driver, base_url, test1_email, test1_password):
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

def test_invalid_token_rejected(driver, base_url):
    driver.get(f"{base_url}/verify?token=abc")
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Invalid or expired')]")),
        message="Expected an 'invalid' verification message but none appeared."
    )
    
    

    