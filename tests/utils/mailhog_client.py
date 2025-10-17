import datetime
import time, re, requests, base64

# Prefer dateutil for robust ISO8601 parsing; fallback to stdlib if unavailable
try:
    from dateutil.parser import isoparse as _isoparse  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _isoparse = None

MAILHOG_API = "http://localhost:8025/api/v2"

def wait_for_email(
    to_addr: str,
    subject: str,
    timeout_s: int = 30,
    poll_s: float = 1,
    since: datetime.datetime | None = None,
) -> dict | None:
    """
    Poll MailHog for the most recent message TO `to_addr` containing `subject`.
    If `since` is provided (UTC datetime), only return messages created after that.
    """
    deadline = time.time() + timeout_s

    while time.time() < deadline:
        # Query by recipient
        try:
            resp = requests.get(
                f"{MAILHOG_API}/search",
                params={"kind": "to", "query": to_addr},
                timeout=5,
            )
        except requests.RequestException:
            time.sleep(poll_s)
            continue

        if resp.status_code != 200:
            time.sleep(poll_s)
            continue

        data = resp.json()
        messages = data.get("items") or data.get("messages") or []

        for msg in messages:
            created_str = msg.get("Created") or msg.get("created")
            created_dt = (
                _parse_iso_to_utc(created_str)
                if created_str
                else datetime.datetime.now(datetime.timezone.utc)
            )

            if since and created_dt < since:
                continue

            hdrs = msg.get("Content", {}).get("Headers", {})
            subj_val = hdrs.get("Subject", [""])[0]
            if subject in subj_val:
                return msg

        time.sleep(poll_s)

    return None

def _parse_iso_to_utc(s: str) -> datetime.datetime:
    if _isoparse:
        dt = _isoparse(s)
    else:
        norm = s.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(norm)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)
    
def extract_plain_html(msg_json):
    mime = msg_json.get("MIME")
    if mime and "Parts" in mime:
        plain, html = None, None
        for part in mime["Parts"]:
            ctype = part["Headers"].get("Content-Type", [""])[0]
            enc = part["Headers"].get("Content-Transfer-Encoding", [""])[0].lower()
            body = _decode_mime_body(part.get("Body", ""), enc)
            if "text/plain" in ctype:
                plain = body
            elif "text/html" in ctype:
                html = body
        return plain, html
    else:
        # No MIME parts → fallback to top-level body
        body = msg_json["Content"].get("Body", "")
        return None, body

def _decode_mime_body(body: str, encoding: str) -> str:
    """Decode MIME body when base64 encoded; otherwise return as-is."""
    if not body:
        return ""
    if encoding == "base64":
        try:
            return base64.b64decode(body).decode("utf-8", errors="replace")
        except Exception:
            return body  # Fallback: return raw
    return body

def find_verify_link(body: str) -> str | None:
    match = re.search(r'href="(https?://[^"]+/verify\?token=[^"]+)"', body)
    return match.group(1) if match else None

def clear_inbox():
    requests.delete(f"{MAILHOG_API}/messages")