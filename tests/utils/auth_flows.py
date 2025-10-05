from time import time

def make_unique_username(prefix="Test", max_len=20):
    return f"{prefix}{int(time()*1000)}"[:max_len]

def fill_and_submit_signup(driver, base_url, username, email, password):
    from selenium.webdriver.common.by import By
    driver.get(f"{base_url}/signup")
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Username']").send_keys(username)
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Email']").send_keys(email)
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").clear()
    driver.find_element(By.XPATH, "//input[@placeholder='Password']").send_keys(password)
    driver.find_element(By.XPATH, '//button[normalize-space()="Sign Up"]').click()
