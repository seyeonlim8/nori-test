from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import pytest
import os
import time

load_dotenv()

@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,900")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    yield driver
    driver.quit()

@pytest.fixture(scope="session")
def base_url():
    return os.getenv("NORI_BASE_URL")

@pytest.fixture(scope="session")
def admin_email():
    return os.getenv("ADMIN_EMAIL")

@pytest.fixture(scope="session")
def admin_password():
    return os.getenv("ADMIN_PASSWORD")

@pytest.fixture(scope="function")
def test1_email():
    base = os.getenv("TEST1_EMAIL")
    return f"{base}+{int(time.time())}@gmail.com"

@pytest.fixture(scope="session")
def test1_password():
    return os.getenv("TEST1_PASSWORD")