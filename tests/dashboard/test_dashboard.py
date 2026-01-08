import time
import requests
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.auth.test_auth_email_verification import _dismiss_alert_if_present
from tests.utils.auth_flows import fill_and_submit_signup, get_auth_cookies, login, make_unique_username
from tests.utils.email_verification import fetch_verify_url_from_mailhog
from tests.utils.dashboard_flows import compute_expected_progress, fetch_progress_data, fetch_words_summary, get_current_username, get_percentage_from_element, open_account_page_from_header, open_account_settings_tab, LEVELS

STUDY_PROGRESS_TAB = (By.CSS_SELECTOR, "[data-testid='study-progress-tab']")
PROGRESS_TOTAL_LABEL = (By.CSS_SELECTOR, "[data-testid='progress-total']")
USERNAME_FIELD = (By.CSS_SELECTOR, "[data-testid='username-field']")
USERNAME_CHECK = (By.CSS_SELECTOR, "[data-testid='username-check']")
PW_FIELD = (By.CSS_SELECTOR, "[data-testid='pw-field']")
PW_CHECK = (By.CSS_SELECTOR, "[data-testid='pw-check']")
SAVE_BTN = (By.CSS_SELECTOR, "[data-testid='save-btn']")
SUCCESS_MSG = (By.CSS_SELECTOR, "[data-testid='success-msg']")
DELETE_BTN = (By.CSS_SELECTOR, "[data-testid='delete-btn']")
LOGIN_BTN = (By.CSS_SELECTOR, "[data-testid='login-btn']")
SUBJECT = "NORI Email Verification"
PROGRESS_KEYS = [
    "flashcards",
    "quiz-kanji-to-furigana",
    "quiz-furigana-to-kanji",
    "fill",
]

@pytest.mark.tcid("TC-DB-004")
@pytest.mark.dashboard
def test_dashboard_progress_calculations_accurate(driver, base_url, admin_email, admin_password):
    """Verify dashboard progress percentages match API data for all study types."""

    login(driver, base_url, admin_email, admin_password)
    open_account_page_from_header(driver, base_url)

    cookies = get_auth_cookies(driver)
    words_summary = fetch_words_summary(base_url, cookies)

    for key in PROGRESS_KEYS:
        container_locator = (By.CSS_SELECTOR, f"[data-testid='progress-chart-container-{key}']")
        container = WebDriverWait(driver, 10).until(EC.presence_of_element_located(container_locator))

        progress = fetch_progress_data(base_url, cookies, key)
        expected_overall, expected_levels = compute_expected_progress(progress, words_summary)

        total_label = container.find_element(*PROGRESS_TOTAL_LABEL)
        total_wrapper = total_label.find_element(By.XPATH, "..")
        overall_ui = get_percentage_from_element(total_wrapper)
        assert overall_ui == expected_overall, (
            f"{key} overall mismatch: expected {expected_overall}%, got {overall_ui}%"
        )

        for idx, expected in enumerate(expected_levels, start=1):
            level_wrapper = container.find_element(
                By.CSS_SELECTOR, f"[data-testid='progress-pie-n{idx}']"
            )
            level_ui = get_percentage_from_element(level_wrapper)
            assert level_ui == expected, (
                f"{key} level N{idx} mismatch: expected {expected}%, got {level_ui}%"
            )

@pytest.mark.tcid("TC-DB-006")
@pytest.mark.dashboard
def test_dashboard_username_validation_feedback(driver, base_url, admin_email, admin_password):
    """Verify real-time username validation for invalid, valid, and duplicate input."""

    login(driver, base_url, admin_email, admin_password)
    open_account_page_from_header(driver, base_url)
    open_account_settings_tab(driver)

    username_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located(USERNAME_FIELD))
    username_field.clear()
    username_field.send_keys("a!")

    msg = WebDriverWait(driver, 5).until(EC.presence_of_element_located(USERNAME_CHECK))
    assert "Username must be 4-19" in msg.text, f"Unexpected validation text: {msg.text}"
    WebDriverWait(driver, 5).until(
        lambda d: "text-red-500" in d.find_element(*USERNAME_CHECK)
        .find_element(By.TAG_NAME, "span")
        .get_attribute("class"),
        "Invalid username not marked red"
    )

    unique_name = f"User{int(time.time() * 1000)}"
    username_field.clear()
    username_field.send_keys(unique_name)

    WebDriverWait(driver, 10).until(
        lambda d: "Username available!" in d.find_element(*USERNAME_CHECK).text,
        "Valid username not marked as available"
    )
    WebDriverWait(driver, 5).until(
        lambda d: "text-green-600" in d.find_element(*USERNAME_CHECK)
        .find_element(By.TAG_NAME, "span")
        .get_attribute("class"),
        "Valid username not marked green"
    )

    username_field.clear()
    username_field.send_keys("Test1")

    WebDriverWait(driver, 10).until(
        lambda d: "already" in d.find_element(*USERNAME_CHECK).text.lower(),
        "Duplicate username not rejected"
    )
    WebDriverWait(driver, 5).until(
        lambda d: "text-red-500" in d.find_element(*USERNAME_CHECK)
        .find_element(By.TAG_NAME, "span")
        .get_attribute("class"),
        "Duplicate username not marked red"
    )

@pytest.mark.tcid("TC-DB-007")
@pytest.mark.dashboard
def test_dashboard_password_validation_feedback(driver, base_url, admin_email, admin_password):
    """Verify real-time password validation feedback for unmet and met requirements."""

    login(driver, base_url, admin_email, admin_password)
    open_account_page_from_header(driver, base_url)
    open_account_settings_tab(driver)

    pw_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PW_FIELD))
    pw_field.clear()
    pw_field.send_keys("abc")

    pw_check = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PW_CHECK))
    items = pw_check.find_elements(By.TAG_NAME, "li")
    assert items, "Password requirements not displayed"
    assert any("text-red-500" in item.get_attribute("class") for item in items), (
        "Unmet password requirements not marked red"
    )

    pw_field.clear()
    pw_field.send_keys(admin_password)
    WebDriverWait(driver, 5).until(
        lambda d: all(
            "text-green-600" in item.get_attribute("class")
            for item in d.find_elements(By.CSS_SELECTOR, "[data-testid='pw-check'] li")
        ),
        "Password requirements not marked green for valid password"
    )

@pytest.mark.tcid("TC-DB-008")
@pytest.mark.dashboard
def test_dashboard_save_changes_processes_correctly(driver, base_url, admin_email, admin_password):
    """Verify Save Changes behavior for empty/invalid input and successful updates."""

    login(driver, base_url, admin_email, admin_password)
    open_account_page_from_header(driver, base_url)
    open_account_settings_tab(driver)

    save_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located(SAVE_BTN))
    assert save_btn.get_attribute("disabled") is not None, "Save button should be disabled with empty fields"

    username_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located(USERNAME_FIELD))
    username_field.clear()
    username_field.send_keys("a!")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located(USERNAME_CHECK))
    assert save_btn.get_attribute("disabled") is not None, "Save button enabled with invalid username"

    unique_name = f"User{int(time.time() * 1000)}"
    username_field.clear()
    username_field.send_keys(unique_name)
    WebDriverWait(driver, 10).until(
        lambda d: "Username available!" in d.find_element(*USERNAME_CHECK).text
    )

    pw_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located(PW_FIELD))
    pw_field.clear()
    pw_field.send_keys("abc")
    WebDriverWait(driver, 5).until(
        lambda d: any(
            "text-red-500" in item.get_attribute("class")
            for item in d.find_elements(By.CSS_SELECTOR, "[data-testid='pw-check'] li")
        )
    )
    assert save_btn.get_attribute("disabled") is not None, "Save button enabled with invalid password"

    pw_field.clear()
    pw_field.send_keys(admin_password)
    WebDriverWait(driver, 5).until(
        lambda d: all(
            "text-green-600" in item.get_attribute("class")
            for item in d.find_elements(By.CSS_SELECTOR, "[data-testid='pw-check'] li")
        )
    )
    WebDriverWait(driver, 5).until(
        lambda d: d.find_element(*SAVE_BTN).get_attribute("disabled") is None,
        "Save button did not enable with valid inputs"
    )

    save_btn = driver.find_element(*SAVE_BTN)
    save_btn.click()

    success_msg = WebDriverWait(driver, 5).until(EC.presence_of_element_located(SUCCESS_MSG))
    assert "Account updated successfully." in success_msg.text
    assert "/account" in driver.current_url, "User was redirected away from account settings"

@pytest.mark.tcid("TC-DB-010")
@pytest.mark.dashboard
def test_dashboard_delete_account_warning_modal(driver, base_url, admin_email, admin_password):
    """Verify warning modal appears and requires explicit dismissal on delete account."""

    login(driver, base_url, admin_email, admin_password)
    open_account_page_from_header(driver, base_url)
    open_account_settings_tab(driver)

    delete_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(DELETE_BTN))
    delete_btn.click()

    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert_text = alert.text
    assert "delete your account" in alert_text.lower(), f"Unexpected alert text: {alert_text}"
    alert.dismiss()

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/account"))
    assert driver.current_url == f"{base_url}/account"

@pytest.mark.tcid("TC-DB-011")
@pytest.mark.dashboard
def test_dashboard_account_deletion_completes(driver, base_url, test1_email, test1_password):
    """Verify account deletion completes, ends session, and redirects to landing page."""

    # Sign up and verify account
    uname = make_unique_username()
    fill_and_submit_signup(driver, base_url, uname, test1_email, test1_password)
    _dismiss_alert_if_present(driver)
    verify_url = fetch_verify_url_from_mailhog(test1_email, SUBJECT, timeout_s=10)
    driver.get(verify_url)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'successfully verified')]"))
    )

    login(driver, base_url, test1_email, test1_password)
    open_account_page_from_header(driver, base_url)
    open_account_settings_tab(driver)

    cookies = get_auth_cookies(driver)
    delete_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(DELETE_BTN))
    delete_btn.click()

    confirm = WebDriverWait(driver, 5).until(EC.alert_is_present())
    confirm.accept()

    deleted = WebDriverWait(driver, 5).until(EC.alert_is_present())
    assert "Account deleted" in deleted.text
    deleted.accept()

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/"))
    WebDriverWait(driver, 5).until(EC.presence_of_element_located(LOGIN_BTN))

    # Wait until user API returns 401
    elapsed = 0
    while elapsed < 5:
        resp = requests.get(
            f"{base_url}/api/user",
            cookies=cookies,
            timeout=5,
        )
        if resp.status_code == 401:
            break
        elif resp.status_code >= 400:
            resp.raise_for_status()
        time.sleep(0.5)
        elapsed += 0.5
    else:
        pytest.fail(f"User API still accessible after account deletion (last status={resp.status_code})")

    assert resp.status_code == 401, f"Expected 401 after account deletion, got {resp.status_code}"
