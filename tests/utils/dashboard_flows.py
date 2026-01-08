import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LEVELS = ["N1", "N2", "N3", "N4", "N5"]
NAV_HELLO = (By.CSS_SELECTOR, "[data-testid='nav-hello']")
ACCOUNT_LINK = (By.XPATH, "//a[@href='/account']")
ACCOUNT_SETTINGS_TAB = (By.CSS_SELECTOR, "[data-testid='account-settings-tab']")
CURRENT_USERNAME_TEXT = (By.XPATH, "//*[contains(normalize-space(.), 'Current username:')]")

def open_account_page_from_header(driver, base_url):
    """Open My Account via header dropdown."""
    
    nav_hello = WebDriverWait(driver, 5).until(EC.presence_of_element_located(NAV_HELLO))
    ActionChains(driver).move_to_element(nav_hello).perform()
    account_link = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(ACCOUNT_LINK))
    account_link.click()
    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/account"))

def open_account_settings_tab(driver):
    """Open the Account Settings tab on the account page."""
    
    tab = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(ACCOUNT_SETTINGS_TAB))
    tab.click()

def get_current_username(driver):
    """Return the current username text from Account Settings."""
    
    text = WebDriverWait(driver, 5).until(EC.presence_of_element_located(CURRENT_USERNAME_TEXT))
    label = text.text.strip()
    if ":" in label:
        return label.split(":", 1)[1].strip()
    raise AssertionError(f"Unexpected username label: {label!r}")

def get_percentage_from_element(element):
    texts = element.find_elements(By.CSS_SELECTOR, "text")
    for t in texts:
        val = t.text.strip()
        if val.endswith("%"):
            return int(val.rstrip("%"))
    raise AssertionError("Percentage label not found in progress chart")

def fetch_words_summary(base_url, cookies):
    r = requests.get(
        f"{base_url}/api/words",
        params={"summary": "true"},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()
    return r.json()

def fetch_progress_data(base_url, cookies, progress_type):
    r = requests.get(
        f"{base_url}/api/study-progress",
        params={"type": progress_type},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()
    return r.json()

def compute_expected_progress(progress, words_summary):
    totals_by_level = {}
    for item in words_summary.get("summary", []):
        totals_by_level[item["level"]] = {"total": item["count"], "completed": 0}

    for item in progress:
        lvl = item.get("level", "").upper()
        if lvl not in totals_by_level:
            totals_by_level[lvl] = {"total": 0, "completed": 0}
        if item.get("completed"):
            totals_by_level[lvl]["completed"] += 1

    total_words = words_summary.get("total", 0) or 0
    completed_words = sum(v["completed"] for v in totals_by_level.values())
    overall = round((completed_words / total_words) * 100) if total_words > 0 else 0

    levels = []
    for lvl in LEVELS:
        stats = totals_by_level.get(lvl, {"total": 0, "completed": 0})
        if stats["total"]:
            levels.append(round((stats["completed"] / stats["total"]) * 100))
        else:
            levels.append(0)
    return overall, levels
