from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.mailhog_client import wait_for_email, extract_plain_html

def test_email_verification_template(driver, base_url, test1_email, test1_password):
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys("Test1")
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(test1_email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(test1_password)
    driver.find_element(By.XPATH, '//button[text()="Sign Up"]').click()

    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        driver.switch_to.alert.accept()
    except Exception:
        pass

    subject = "NORI Email Verification"
    msg = wait_for_email(test1_email, subject, timeout_s=30)
    assert msg is not None, "Expected verification email was not received within 30s."

    hdr = msg["Content"]["Headers"]
    from_val = hdr.get("From", [""])[0]
    subj_val = hdr.get("Subject", [""])[0]
    assert "NORI" in from_val
    assert subj_val == subject

    plain, html = extract_plain_html(msg)
    body = html or plain
    assert "Verify your email to join NORI" in body
    assert "just ignore this email" in body
    assert "Verify" in body
