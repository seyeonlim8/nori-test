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

    