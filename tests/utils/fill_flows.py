import time
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from tests.utils.auth_flows import get_auth_cookies, login
from tests.utils.db_client import get_study_progress, get_word_from_word_id

STUDY_BTN = (By.CSS_SELECTOR, "[data-testid='study-btn']")
FILL_BTN = (By.CSS_SELECTOR, "[data-testid='fill-btn']")
FILL_BOX = (By.CSS_SELECTOR, "[data-testid='fill-box']")
ENG_MEANING = (By.CSS_SELECTOR, "[data-testid='english-meaning']")
INPUT_BOX = (By.CSS_SELECTOR, "[data-testid='input-box']")
SUBMIT_BTN = (By.CSS_SELECTOR, "[data-testid='submit-btn']")

def login_and_open_fill_page(driver, base_url, email, password, level):
    
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )
    
    study_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(STUDY_BTN),
        "Study button is not found"
    )
    ActionChains(driver).move_to_element(study_btn).perform()
    fill_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(FILL_BTN),
        "Fill button is not clickable"
    )
    fill_btn.click()
    level_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='level-btn-{level.lower()}']")),
        f"{level.upper()} button is not clickable"
    )
    level_btn.click()
    
def login_and_open_fill_page_with_level_reset(driver, base_url, email, password, level):
    
    login(driver, base_url, email, password)
    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{base_url}/"),
        "Did not navigate to main page"
    )
    
    # Reset progress
    cookies = get_auth_cookies(driver)
    reset_url = f"{base_url}/api/study-progress/reset"
    r = requests.post(
        reset_url,
        params={"type": "fill", "level": level},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()

    study_btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(STUDY_BTN),
        "Study button is not found"
    )
    ActionChains(driver).move_to_element(study_btn).perform()
    fill_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(FILL_BTN),
        "Fill button is not clickable"
    )
    fill_btn.click()
    level_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-testid='level-btn-{level.lower()}']")),
        f"{level.upper()} button is not clickable"
    )
    level_btn.click()
    
def input_fill_answer(driver, answer):
    input_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(INPUT_BOX)
    )
    input_box.clear()
    input_box.send_keys(answer)
    
    submit_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(SUBMIT_BTN)
    )
    submit_btn.click()
    
def input_correct_fill_answer(driver):
    meaning_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(ENG_MEANING)
    )
    
    last_char = meaning_element.text.strip()[-1]
    answer = 'テスト' + last_char
    
    input_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(INPUT_BOX)
    )
    input_box.clear()
    input_box.send_keys(answer)
    
    submit_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(SUBMIT_BTN)
    )
    submit_btn.click()
    
def input_incorrect_fill_answer(driver):

    input_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(INPUT_BOX)
    )
    input_box.clear()
    input_box.send_keys("INCORRECT ANSWER")
    
    submit_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(SUBMIT_BTN)
    )
    submit_btn.click()
    
def get_correct_fill_answer(driver, base_url):
    
    fill_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(FILL_BOX)
    )
    
    word_id = fill_box.get_attribute("data-word-id")
    answer = get_word_from_word_id(base_url, word_id)['answer_in_example']
    
    return answer
    
    
def input_correct_fill_answer_from_db(driver, base_url):
    
    answer = get_correct_fill_answer(driver, base_url)
    
    input_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(INPUT_BOX)
    )
    input_box.clear()
    input_box.send_keys(answer)
    
    return answer
    

def input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url):
    
    answer = input_correct_fill_answer_from_db(driver, base_url)
    
    submit_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable(SUBMIT_BTN)
    )
    submit_btn.click()
    
    return answer

def input_correct_fill_answer_from_db_and_submit_with_keyboard(driver, base_url):
    
    answer = input_correct_fill_answer_from_db(driver, base_url)
    
    input_box = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(INPUT_BOX)
    )
    input_box.send_keys(Keys.ENTER)
    
    return answer
    
def wait_for_completion_state(base_url, word_id, cookies, expected, level, timeout=5):
    """Poll the study progress API until the word's completion state matches the expected value."""
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        progress = get_study_progress(base_url, cookies, "fill", level, word_id)
        if progress.get("completed") == expected:
            return progress
        time.sleep(0.5)
    return None
    
def wait_stays_disabled_until_advance(driver, old_word_id, timeout=3):
    """Wait until question advances, asserting submit button stays disabled until that point."""
    
    start = time.time()
    while time.time() - start < timeout:
        current_id = driver.find_element(*FILL_BOX).get_attribute("data-word-id")
        is_disabled = driver.find_element(*SUBMIT_BTN).get_attribute("disabled") is not None
        if current_id != old_word_id:
            return  
        # tolerate short flickers (<100ms)
        if not is_disabled:
            time.sleep(0.1)
            # re-check after brief delay in case it's transient
            if driver.find_element(*SUBMIT_BTN).get_attribute("disabled") is None:
                raise AssertionError("Submit button re-enabled before next quiz appeared")
        time.sleep(0.05)
    raise TimeoutException("Question did not advance")

def wait_for_fill_advance(driver, old_word_id, timeout=5):
    """Wait for the sentence to advance by checking that the word ID has changed."""
    
    def word_id_changed(driver):
        quiz = driver.find_element(*FILL_BOX)
        return quiz.get_attribute("data-word-id") != old_word_id
    WebDriverWait(driver, timeout).until(
        word_id_changed,
        "Quiz did not advance"
    )

def enter_review_mode(driver, num_of_completed, num_of_incomplete):
    """Complete the requested mix of questions so the session enters review mode. (Available in TEST set only)"""
    
    alert_poll_seconds = 1.5
    for _ in range(num_of_completed):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_correct_fill_answer(driver)
        wait_for_fill_advance(driver, current_word_id)
    for _ in range(num_of_incomplete):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_incorrect_fill_answer(driver)
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
        except TimeoutException:
            wait_for_fill_advance(driver, current_word_id)
        else:
            alert.accept()
            return
    raise AssertionError("Failed to trigger fill-in review mode with the requested incorrect answers.")

def dismiss_review_mode_modal(driver, num_of_completed, num_of_incomplete):
    
    alert_poll_seconds = 1.5
    for _ in range(num_of_completed):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_correct_fill_answer(driver)
        wait_for_fill_advance(driver, current_word_id)
    for _ in range(num_of_incomplete):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_incorrect_fill_answer(driver)
        try:
            alert = WebDriverWait(driver, alert_poll_seconds).until(EC.alert_is_present())
        except TimeoutException:
            wait_for_fill_advance(driver, current_word_id)
        else:
            alert.dismiss()
            return
    raise AssertionError("Failed to trigger fill-in review mode modal with the requested incorrect answers.")

def answer_all_problems_correctly_and_accept_alert(driver, base_url):
    
    modal_msg = None
    while True:
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url)
        
        try:
            alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
            modal_msg = alert.text
            alert.accept()
            break
        except TimeoutException:
            wait_for_fill_advance(driver, current_word_id)
    
    return modal_msg

def answer_problems(driver, base_url, num_of_correct, num_of_incorrect):
    
    for _ in range(num_of_correct):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_correct_fill_answer_from_db_and_submit_with_btn_click(driver, base_url)
        wait_for_fill_advance(driver, current_word_id)
    for _ in range(num_of_incorrect):
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(FILL_BOX)
        )
        current_word_id = question.get_attribute("data-word-id")
        input_incorrect_fill_answer(driver)
        wait_for_fill_advance(driver, current_word_id)
        
def reset_fill_level_progress(driver, base_url, level):
    
    cookies = get_auth_cookies(driver)
    r = requests.post(
        f"{base_url}/api/study-progress/reset",
        params={"type": "fill", "level": level},
        cookies=cookies,
        timeout=5,
    )
    r.raise_for_status()