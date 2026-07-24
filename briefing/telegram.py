import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_CHARS = 4000
SPLIT_MARKER = "\n\n——————————————————\n\n"


def _split_message(text: str) -> list:
    """Split at section dividers so Telegram's 4096 char limit is never hit mid-signal."""
    if len(text) <= MAX_CHARS:
        return [text]

    sections = text.split(SPLIT_MARKER)
    chunks = []
    current = ""

    for section in sections:
        candidate = current + SPLIT_MARKER + section if current else section
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
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return False

    chunks = _split_message(text)
    url = TELEGRAM_API.format(token=TELEGRAM_BOT_TOKEN)
    success = True

    for i, chunk in enumerate(chunks):
        try:
            resp = requests.post(url, data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            }, timeout=15)
            resp.raise_for_status()
            print(f"[telegram] chunk {i+1}/{len(chunks)} sent ({len(chunk)} chars)")
        except Exception as e:
            print(f"[telegram] chunk {i+1} error: {e}")
            success = False

    return success
