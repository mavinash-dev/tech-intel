"""
Manually trigger a briefing right now — useful for testing before 8am.
Run with: python send_now.py
Add --print to print to terminal without sending to Telegram.
"""
import sys
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing

briefing = generate_briefing()

if "--print" in sys.argv:
    print(briefing)
else:
    print(briefing)
    print("\n" + "─" * 50)
    confirm = input("Send to Telegram? [y/N] ").strip().lower()
    if confirm == "y":
        ok = send_briefing(briefing)
        print("Sent!" if ok else "Send failed — check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
    else:
        print("Not sent.")
