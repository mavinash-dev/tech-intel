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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{
  --canvas:#fdfcf0;--surface:#f1f0e4;--elevated:#fffefa;
  --border-subtle:#e5e4d8;--border-default:#cdc9b8;
  --fg:#080f11;--fg-body:#1a242a;--fg-muted:#6a7173;
  --green:#1ce783;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:var(--canvas);color:var(--fg-body);
  font-family:'Inter',system-ui,sans-serif;
  font-size:16px;line-height:1.7;
  padding:32px 20px 80px;max-width:760px;margin:0 auto;
}}
a{{color:var(--fg);text-decoration:underline;text-underline-offset:3px;}}
a:hover{{opacity:0.7;}}
.eyebrow{{
  font-family:'SF Mono','Fira Code',monospace;
  font-size:11px;letter-spacing:0.16em;color:var(--fg-muted);
  text-transform:uppercase;font-weight:400;
}}
.page-header{{padding:40px 0 28px;margin-bottom:32px;
  border-bottom:1px solid var(--border-subtle);}}
.brand{{font-size:clamp(26px,4vw,34px);font-weight:700;color:var(--fg);
  letter-spacing:-0.02em;margin:10px 0 6px;}}
.brand em{{color:var(--green);font-style:normal;}}
.sub{{font-size:14px;color:var(--fg-muted);}}
.back{{
  font-family:monospace;font-size:12px;letter-spacing:0.08em;
  color:var(--green);text-decoration:none;display:inline-block;
  margin-bottom:28px;text-transform:uppercase;
}}
.back:hover{{opacity:0.8;}}
.count{{font-family:monospace;font-size:12px;color:var(--fg-muted);
  margin-bottom:28px;letter-spacing:0.06em;text-transform:uppercase;}}
.day-group{{margin-bottom:32px;}}
.day-label{{
  font-family:monospace;font-size:10px;font-weight:400;letter-spacing:0.16em;
  text-transform:uppercase;color:var(--fg-muted);
  padding-bottom:10px;border-bottom:1px solid var(--border-subtle);margin-bottom:8px;
}}
.briefing-link{{
  display:flex;align-items:center;gap:14px;
  padding:13px 18px;margin-bottom:6px;
  background:var(--surface);border:1px solid var(--border-subtle);
  border-radius:10px;transition:border-color 0.15s,background 0.15s;
  text-decoration:none;
}}
.briefing-link:hover{{border-color:var(--border-default);background:var(--elevated);opacity:1;}}
.btime{{font-family:monospace;font-size:14px;font-weight:600;color:var(--fg);min-width:52px;}}
.btitle{{font-size:15px;color:var(--fg-body);flex:1;}}
.barrow{{font-size:16px;color:var(--green);}}
.footer{{
  margin-top:48px;padding:18px;
  background:var(--fg);border-radius:14px;
  font-family:monospace;font-size:12px;color:rgba(253,252,240,0.45);
  text-align:center;letter-spacing:0.1em;text-transform:uppercase;
}}
</style>
</head>
<body>
<header class="page-header">
  <p class="eyebrow">Signal Intelligence</p>
  <h1 class="brand">Tech <em>Intel</em> · Archive</h1>
  <p class="sub">Every briefing, ever. Updated hourly.</p>
</header>
<a class="back" href="index.html">← Latest briefing</a>
<p class="count">{count} briefing{"s" if count != 1 else ""} stored</p>
{"".join(rows)}
<footer class="footer">tech-intel · generated {now_str}</footer>
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
