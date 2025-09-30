import time, re, requests

MAILHOG_API = "http://localhost:8025/api/v2"

def wait_for_email(to_addr: str, subject: str, timeout_s: int = 30, poll_s: float = 1.0):
    end = time.time() + timeout_s
    while time.time() < end:
        resp = requests.get(f"{MAILHOG_API}/messages")
        resp.raise_for_status()
        data = resp.json()

        for msg in data.get("items", []):
            hdr = msg.get("Content", {}).get("Headers", {})
            subj = (hdr.get("Subject", [""])[0] or "").strip()
            from_ = (hdr.get("From", [""])[0] or "").strip()
            to_list = [rcpt.get("Mailbox", "") + "@" + rcpt.get("Domain", "") for rcpt in msg.get("To", [])]

            if subject == subj and to_addr in to_list:
                return msg
            time.sleep(poll_s)
        
        return None
    
def extract_plain_html(msg_json):
    mime = msg_json.get("MIME")
    if mime and "Parts" in mime:
        plain, html = None, None
        for part in mime["Parts"]:
            ctype = part["Headers"].get("Content-Type", [""])[0]
            if "text/plain" in ctype:
                plain = part["Body"]
            elif "text/html" in ctype:
                html = part["Body"]
        return plain, html
    else:
        # No MIME parts → fallback to top-level body
        body = msg_json["Content"].get("Body", "")
        return None, body

def find_verify_link(body: str) -> str | None:
    match = re.search(r'href="(https?://[^"]+/verify\?token=[^"]+)"', body)
    return match.group(1) if match else None