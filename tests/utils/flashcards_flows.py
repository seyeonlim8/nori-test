import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies, login
from tests.utils.db_client import get_study_progress

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
FC_BTN = (By.CSS_SELECTOR, "[data-testid='flashcards-btn']")
O_BTN = (By.CSS_SELECTOR, "[data-testid='o-btn']")
X_BTN = (By.CSS_SELECTOR, "[data-testid='x-btn']")
SUBJECT = "NORI Email Verification"
VOCAB = (By.CSS_SELECTOR, "[data-testid='vocabulary']")

def _open_flashcards_level(driver, level):
    """Hover the Study menu and open the requested flashcards level with retries."""
    
    study_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(STUDY_BTN),
        "Study button is not found"
    )
    
    flashcards_btn = None
    for attempt in range(3):
        ActionChains(driver).move_to_element(study_btn).pause(0.2).perform()
        try:
            flashcards_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(FC_BTN),
                "Flashcards button is not clickable"
            )
            flashcards_btn.click()
            break
        except TimeoutException as exc:
            if attempt == 2:
                raise TimeoutException("Flashcards button is not clickable after retries") from exc
    
    if flashcards_btn is None:
        raise TimeoutException("Flashcards button was never located")
    
    level_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='level-btn-{level.lower()}']")),
        f"{level.upper()} button is not clickable"
    )
    level_btn.click()

def login_and_open_flashcards_page(driver, base_url, email, password, level):
    """Log in and navigate to the flashcards page for the given level."""
    
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )

    _open_flashcards_level(driver, level)
    
def login_and_open_flashcards_page_with_level_reset(driver, base_url, email, password, level):
    """Log in, reset flashcard progress for the level, and open the flashcards page."""
    
    login(driver, base_url, email, password)
    
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )
    
    reset_flashcards_level_progress(driver, base_url, level)
    
    _open_flashcards_level(driver, level)
    
def reset_flashcards_level_progress(driver, base_url, level):
    
    cookies = get_auth_cookies(driver)
    r = requests.post(
        f"{base_url}/api/study-progress/reset",
        params={"type": "flashcards", "level": level},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()
    
def wait_for_transform_change(driver, element, old_val, timeout=1.0, poll_interval=0.05):
    """Wait for element's CSS transform property to change from its initial value."""
    
    WebDriverWait(driver, timeout, poll_interval).until(
        lambda d: element.value_of_css_property("transform") != old_val,
        "Hover transform animation did not trigger"
    )

def wait_stays_disabled_until_advance(driver, old_word_id, btn_locator, timeout=3):
    """Wait until flashcard advances, asserting button stays disabled until that point."""
    
    start = time.time()
    while time.time() - start < timeout:
        current_id = driver.find_element(*VOCAB).get_attribute("data-word-id")
        is_disabled = driver.find_element(*btn_locator).get_attribute("disabled") is not None
        if current_id != old_word_id:
            return  # advanced successfully
        if not is_disabled:
            try:
                WebDriverWait(driver, 0.3).until(
                    lambda d: d.find_element(*btn_locator).get_attribute("disabled") is not None
                )
                continue
            except TimeoutException:
                raise AssertionError("Button re-enabled before next flashcard appeared")
        time.sleep(0.05)
    raise TimeoutException("Flashcard did not advance")

def wait_for_completion_state(base_url, word_id, cookies, expected: bool, level: str, timeout=5):
    """Poll study progress until the word's completed flag matches expected; return record or None."""
    
    end_time = time.time() + timeout
    while time.time() < end_time:
        progress = get_study_progress(base_url, cookies, "flashcards", level, word_id)
        if progress.get("completed") == expected:
            return progress
        time.sleep(0.5)
    return None


def wait_for_flashcard_advance(driver, old_word_id, timeout=5):
    """Wait for the flashcard to advance by checking that the word ID has changed."""
    
    def word_id_changed(driver):
        vocab = driver.find_element(*VOCAB)
        return vocab.get_attribute("data-word-id") != old_word_id
    WebDriverWait(driver, timeout).until(
        word_id_changed,
        "Flashcard did not advance"
    )

def enter_review_mode(driver, num_of_completed, num_of_incomplete):
    """Complete the requested mix of cards so the session enters review mode. (Available in TEST set only)"""
    
    for _ in range(num_of_completed):
        o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        o_btn.click()
        wait_for_flashcard_advance(driver, current_word_id)
    for _ in range(num_of_incomplete):
        x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        x_btn.click()
        try:
            alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
            alert.accept()
            return
        except TimeoutException:
            wait_for_flashcard_advance(driver, current_word_id)
    raise AssertionError("Failed to enter review mode before exhausting requested incorrect answers.")

def mark_all_flashcards_O_and_accept_alert(driver):
    """Mark all flashcards as correct (O) until completion alert appears, then accept it."""
    
    modal_msg = None
    while True:
        try:
            vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
            word_id = int(vocab.get_attribute("data-word-id"))
            o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
            o_btn.click()
            
            try:
                alert = WebDriverWait(driver, 1).until(EC.alert_is_present())
                modal_msg = alert.text
                alert.accept()
                break
            except TimeoutException:
                WebDriverWait(driver, 5).until(
                    lambda d: d.find_element(*VOCAB).get_attribute("data-word-id") != str(word_id)
                )
        except TimeoutException:
            break
        
    return modal_msg

def study_flashcards(driver, num_of_completed, num_of_incomplete):
    """Study flashcards by marking the specified number as completed (O) and incomplete (X)."""
    
    for _ in range(num_of_completed):
        o_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(O_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        o_btn.click()
        wait_for_flashcard_advance(driver, current_word_id)
    for _ in range(num_of_incomplete):
        x_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(X_BTN))
        vocab = WebDriverWait(driver, 5).until(EC.presence_of_element_located(VOCAB))
        current_word_id = vocab.get_attribute("data-word-id")
        x_btn.click()
        wait_for_flashcard_advance(driver, current_word_id)
