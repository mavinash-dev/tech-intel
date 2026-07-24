import os
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

SEND_DOC_URL = "https://api.telegram.org/bot{token}/sendDocument"
SEND_MSG_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_briefing(html_path: str) -> bool:
    """Send the HTML briefing as a file attachment to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return False

    if not os.path.exists(html_path):
        print(f"[telegram] file not found: {html_path}")
        return False

    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    caption = f"📡 Tech Intel · {now_str}\nTap the file to open your briefing."

    try:
        with open(html_path, "rb") as f:
            resp = requests.post(
                SEND_DOC_URL.format(token=TELEGRAM_BOT_TOKEN),
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                files={"document": (os.path.basename(html_path), f, "text/html")},
                timeout=30,
            )
        resp.raise_for_status()
        print(f"[telegram] briefing sent: {os.path.basename(html_path)}")
        return True
    except Exception as e:
        print(f"[telegram] send error: {e}")
        return False
