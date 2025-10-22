from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.safari.webdriver import WebDriver as SafariDriver
from dotenv import load_dotenv
import pytest
import os
import time

load_dotenv()

def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Browser to run tests on (chrome or safari)"
    )
    
@pytest.fixture
def driver(request):
    browser = request.config.getoption("--browser")

    if browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1366,900")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    elif browser == "safari":
        driver = SafariDriver()

    else:
        raise ValueError(f"Unsupported browser: {browser}")

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