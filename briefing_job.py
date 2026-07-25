#!/usr/bin/env python3
"""Single-run briefing generation + Telegram send job. Called by GitHub Actions every hour."""
import sys
import os
import shutil
import glob
from datetime import datetime
from briefing.generator import generate_briefing
from briefing.telegram import send_briefing


def _parse_briefing_dt(filename: str):
    """Parse datetime from briefing_YYYYMMDD_HHMM.html"""
    base = os.path.basename(filename).replace("briefing_", "").replace(".html", "")
    try:
        return datetime.strptime(base, "%Y%m%d_%H%M")
    except Exception:
        return None


def _generate_archive():
    """Scan docs/briefings/, build docs/archive.html with human-readable index."""
    briefing_files = sorted(
        glob.glob("docs/briefings/briefing_*.html"),
        reverse=True
    )

    rows = []
    current_date = None
    for f in briefing_files:
        dt = _parse_briefing_dt(f)
        if not dt:
            continue
        date_str = dt.strftime("%A, %d %B %Y")
        time_str = dt.strftime("%H:%M")
        rel_path = os.path.basename(f)

        if date_str != current_date:
            if current_date is not None:
                rows.append("</div>")
            rows.append(f'<div class="day-group"><div class="day-label">{date_str}</div>')
            current_date = date_str

        rows.append(f'''
<a class="briefing-link" href="briefings/{rel_path}">
  <span class="btime">{time_str}</span>
  <span class="btitle">Tech Intel Briefing</span>
  <span class="barrow">→</span>
</a>''')

    if current_date is not None:
        rows.append("</div>")

    count = len(briefing_files)
    now_str = datetime.now().strftime("%d %b %Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Tech Intel · Archive</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:#111318;color:#d1d5db;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  font-size:16px;line-height:1.7;
  padding:24px 20px 64px;max-width:760px;margin:0 auto;
}}
a{{color:#818cf8;text-decoration:none;}}
.header{{padding:28px 0 20px;border-bottom:1px solid #2a2d36;margin-bottom:28px;}}
.eyebrow{{font-size:11px;letter-spacing:3px;color:#6b7280;text-transform:uppercase;margin-bottom:8px;}}
.brand{{font-size:32px;font-weight:800;color:#f9fafb;}}
.brand em{{color:#818cf8;font-style:normal;}}
.sub{{font-size:13px;color:#9ca3af;margin-top:6px;}}
.back{{font-size:13px;color:#818cf8;margin-bottom:24px;display:inline-block;}}
.back:hover{{color:#c7d2fe;}}
.count{{font-size:13px;color:#6b7280;margin-bottom:24px;}}
.day-group{{margin-bottom:28px;}}
.day-label{{
  font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;
  color:#9ca3af;padding-bottom:10px;border-bottom:1px solid #2a2d36;margin-bottom:8px;
}}
.briefing-link{{
  display:flex;align-items:center;gap:12px;
  padding:12px 16px;margin-bottom:6px;
  background:#1a1d24;border:1px solid #2a2d36;border-radius:8px;
  transition:border-color 0.15s;
}}
.briefing-link:hover{{border-color:#818cf8;}}
.btime{{font-size:15px;font-weight:700;color:#f9fafb;min-width:52px;}}
.btitle{{font-size:15px;color:#d1d5db;flex:1;}}
.barrow{{font-size:16px;color:#6b7280;}}
.footer{{margin-top:40px;padding-top:20px;border-top:1px solid #2a2d36;
  font-size:12px;color:#4b5563;text-align:center;}}
</style>
</head>
<body>
<div class="header">
  <div class="eyebrow">Signal Intelligence</div>
  <div class="brand">Tech <em>Intel</em> · Archive</div>
  <div class="sub">Every briefing, ever. Updated hourly.</div>
</div>
<a class="back" href="index.html">← Latest briefing</a>
<div class="count">{count} briefing{"s" if count != 1 else ""} stored</div>
{"".join(rows)}
<div class="footer">tech-intel · generated {now_str}</div>
</body>
</html>"""

    with open("docs/archive.html", "w") as f:
        f.write(html)
    print(f"[briefing] archive updated — {count} briefings indexed.", flush=True)


def main():
    print("[briefing] generating...")
    path, signals = generate_briefing()

    # Publish latest to docs/index.html
    os.makedirs("docs", exist_ok=True)
    shutil.copy(path, "docs/index.html")
    print("[briefing] published to docs/index.html")

    # Copy to docs/briefings/ for public archive
    os.makedirs("docs/briefings", exist_ok=True)
    dest = os.path.join("docs/briefings", os.path.basename(path))
    shutil.copy(path, dest)
    print(f"[briefing] archived to {dest}")

    # Regenerate archive index
    _generate_archive()

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
