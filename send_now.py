"""
Manually trigger a briefing right now.
  python send_now.py           — generate + send to Telegram
  python send_now.py --open    — generate + open in browser (no Telegram send)
"""
import sys
import os
import subprocess
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing

path = generate_briefing()
print(f"Briefing saved: {path}")

if "--open" in sys.argv:
    subprocess.run(["open", path])
else:
    ok = send_briefing(path)
    print("Sent to Telegram ✓" if ok else "Send failed — check .env")
