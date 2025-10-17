import datetime
import re, quopri
from utils.mailhog_client import wait_for_email, extract_plain_html

VERIFY_LINK_PATTERN = re.compile(r'https?://[^"\s<>]+/verify\?token=[^"\s<>]+')

def fetch_verify_url_from_mailhog(to_email: str, subject: str, timeout_s: int = 10, since: datetime.datetime | None = None,) -> str:
    """
    Waits for the email, normalizes the body, and returns the verify URL.
    """
    msg = wait_for_email(to_email, subject, timeout_s=timeout_s, since=since)
    assert msg, f"Expected email with subject {subject!r} to {to_email} not received within {timeout_s}s."

    plain, html = extract_plain_html(msg)
    raw = html or plain or ""
    assert raw, "Email content body is empty."

    # Clean up any quoted-printable encoding
    decoded = quopri.decodestring(raw.encode('utf-8')).decode('utf-8')

    # Verify that verification link exists in email
    m = VERIFY_LINK_PATTERN.search(decoded)
    assert m, "Verification link not found in email body."
    
    return m.group(0)