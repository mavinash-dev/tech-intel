#!/usr/bin/env python3
"""Single-run briefing generation + Telegram send job. Called by GitHub Actions every hour."""
import sys
import os
import shutil
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing


def main():
    print("[briefing] generating...")
    path, signals = generate_briefing()

    # Always publish to docs/index.html so GitHub Pages shows the latest briefing
    os.makedirs("docs", exist_ok=True)
    shutil.copy(path, "docs/index.html")
    print(f"[briefing] published to docs/index.html")

    if not signals:
        print("[briefing] no signals — skipping Telegram send.")
        return

    print(f"[briefing] saved to {path}, sending to Telegram...")
    ok = send_briefing(path)
    if ok:
        print("[briefing] sent successfully.")
    else:
        print("[briefing] Telegram send failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
