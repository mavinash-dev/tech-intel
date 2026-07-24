import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_CHARS = 4000
SPLIT_MARKER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SPLIT_MARKER_PRO = "---"


def _split_message(text: str) -> list:
    """Split briefing at section separators so Telegram's 4096 char limit is never hit mid-signal."""
    if len(text) <= MAX_CHARS:
        return [text]

    marker = SPLIT_MARKER if SPLIT_MARKER in text else SPLIT_MARKER_PRO
    sections = text.split(marker)
    chunks = []
    current = ""

    for section in sections:
        candidate = current + marker + section if current else section
        if len(candidate) <= MAX_CHARS:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = section
    if current:
        chunks.append(current.strip())

    return chunks or [text[:MAX_CHARS]]


def send_briefing(text: str) -> bool:
    """Send briefing to Telegram. Returns True if all chunks sent successfully."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env — skipping send")
        return False

    chunks = _split_message(text)
    url = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)
    success = True

    for i, chunk in enumerate(chunks):
        try:
            resp = requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "disable_web_page_preview": "true",
            }, timeout=15)
            resp.raise_for_status()
            print(f"[telegram] chunk {i+1}/{len(chunks)} sent ({len(chunk)} chars)")
        except Exception as e:
            print(f"[telegram] send error chunk {i+1}: {e}")
            success = False

    return success
