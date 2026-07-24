"""
Manually trigger a briefing right now.
  python send_now.py           — generate + send to Telegram
  python send_now.py --open    — generate + open in browser only
"""
import sys
import subprocess
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing

path, signals = generate_briefing()
print(f"Briefing saved: {path}")

if "--open" in sys.argv:
    subprocess.run(["open", path])
else:
    subprocess.run(["open", path])   # also open locally for preview
    ok = send_briefing(path, signals)
    print("Sent to Telegram ✓" if ok else "Send failed — check .env")
