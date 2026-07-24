import os
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

SEND_DOC_URL = "https://api.telegram.org/bot{token}/sendDocument"
SEND_MSG_URL = "https://api.telegram.org/bot{token}/sendMessage"

DOMAIN_EMOJI = {
    "Capital": "💰", "Talent": "👤", "Technology": "🔵",
    "Power": "⚡", "Infrastructure": "🏗", "Narrative": "📊", "Security": "🔒",
}


def _send_text(text: str) -> bool:
    try:
        resp = requests.post(
            SEND_MSG_URL.format(token=TELEGRAM_BOT_TOKEN),
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[telegram] summary send error: {e}")
        return False


def _build_summary(signals: list) -> str:
    now_str = datetime.now().strftime("%d %b, %H:%M")
    top3 = signals[:3]
    lines = [f"📡 Tech Intel · {now_str}", ""]

    for i, s in enumerate(top3, 1):
        emoji = DOMAIN_EMOJI.get(s["domain"], "📌")
        title = s["title"][:70] + ("..." if len(s["title"]) > 70 else "")
        # One-sentence summary: first sentence of plain_explanation
        summary = s["plain_explanation"].split(".")[0].strip() + "."
        if len(summary) > 120:
            summary = summary[:120] + "..."
        lines.append(f"{emoji} {title}")
        lines.append(f"   {summary}")
        lines.append("")

    lines.append("Full briefing with highlights below ↓")
    return "\n".join(lines)


def send_briefing(html_path: str, signals: list = None) -> bool:
    """Send a short summary text, then the HTML file as a document."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in .env")
        return False

    if not os.path.exists(html_path):
        print(f"[telegram] file not found: {html_path}")
        return False

    # 1. Send short summary text first
    if signals:
        summary = _build_summary(signals)
        _send_text(summary)

    # 2. Send HTML file
    try:
        with open(html_path, "rb") as f:
            resp = requests.post(
                SEND_DOC_URL.format(token=TELEGRAM_BOT_TOKEN),
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": "Tap to open full briefing"},
                files={"document": (os.path.basename(html_path), f, "text/html")},
                timeout=30,
            )
        resp.raise_for_status()
        print(f"[telegram] sent: {os.path.basename(html_path)}")
        return True
    except Exception as e:
        print(f"[telegram] file send error: {e}")
        return False
