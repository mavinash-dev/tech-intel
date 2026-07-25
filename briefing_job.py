#!/usr/bin/env python3
"""Single-run briefing generation + Telegram send job. Called by GitHub Actions every hour."""
import sys
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing


def main():
    print("[briefing] generating...")
    path, signals = generate_briefing()
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
