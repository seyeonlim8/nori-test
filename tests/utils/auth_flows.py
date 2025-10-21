def make_unique_username(prefix="Test", max_len=20):
    from time import time
    
    return f"{prefix}{int(time()*1000)}"[:max_len]

def fill_signup_form(driver, base_url, username, email, password):
    from selenium.webdriver.common.by import By
    
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys(username)
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(password)
    driver.find_element(By.XPATH, "//input[@placeholder='Confirm Password']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Confirm Password']").send_keys(password)
    
def fill_and_submit_signup(driver, base_url, username, email, password):
    from selenium.webdriver.common.by import By
    
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys(username)
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(password)
    driver.find_element(By.XPATH, "//input[@placeholder='Confirm Password']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Confirm Password']").send_keys(password)
    driver.find_element(By.XPATH, '//button[normalize-space()="Sign Up"]').click()

def login(driver, base_url, email, password):
    from selenium.webdriver.common.by import By
    
    driver.get(f"{base_url}/login")
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(password)
    driver.find_element(By.XPATH, '//button[text()="Log In"]').click()

def logout(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support import expected_conditions as EC

    nav_hello = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='nav-hello']")))
    ActionChains(driver).move_to_element(nav_hello).perform() # hover
    logout_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='logout-btn']"))
    )
    logout_btn.click()
     
def assert_logged_in(driver, base_url):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/"))
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='nav-hello']"))
    )

def assert_no_verify_error(driver):
    import contextlib
    import pytest
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    error_text = "Please verify your email before logging in."
    with contextlib.suppress(Exception):
        WebDriverWait(driver, 1.5).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[contains(normalize-space(.), '{error_text}')]")
            )
        )
        pytest.fail("Unexpected verification error banner/text was shown")

def new_chrome_like_fixture():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,900")
    d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    return d

def assert_no_sensitive_data_in_storage(driver):
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