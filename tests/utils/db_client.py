import requests

def get_study_progress(base_url, cookies, type, level, word_id=None):
    url = f"{base_url}/api/study-progress?type={type}&level={level}"
    if word_id is not None:
        url += f"&wordId={word_id}"
    r = requests.get(
        url,
        cookies=cookies,
        timeout=5
    )
    r.raise_for_status()
    progress = r.json()
    return progress

def get_word_from_word_id(base_url, word_id):
    """Fetch word data from the API by word ID."""
    
    url = f"{base_url}/api/words/{word_id}"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    word = r.json()
    return word