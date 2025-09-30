from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_login(driver, base_url, admin_email, admin_password):
    driver.get(f"{base_url}/login")
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(admin_email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(admin_password)
    driver.find_element(By.XPATH, '//button[text()="Log In"]').click()

    WebDriverWait(driver, 5).until(EC.url_to_be(f"{base_url}/"))
    assert driver.current_url == f"{base_url}/"

    nav_hello = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='nav-hello']")))
    assert nav_hello.text.startswith("Hello")

def test_invalid_credentials(driver, base_url, test1_email, test1_password):
    driver.get(f"{base_url}/login")
    email_field = driver.find_element(By.XPATH, "//input[@placeholder='Email']")
    password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
    login_btn = driver.find_element(By.XPATH, '//button[text()="Log In"]')

    # Invalid email, valid password
    email_field.send_keys("randomemail@random.com")
    password_field.send_keys(test1_password)
    login_btn.click()
    error_msg = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='credentials-error']"))
    )
    assert "Invalid email or password" in error_msg.text

    email_field.clear()
    password_field.clear()
    email_field = driver.find_element(By.XPATH, "//input[@placeholder='Email']")
    password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")

    # Valid email, invalid password
    email_field.send_keys(test1_email)
    password_field.send_keys("IncorrectPassword!123")
    login_btn.click()
    error_msg = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='credentials-error']"))
    )
    assert "Invalid email or password" in error_msg.text
