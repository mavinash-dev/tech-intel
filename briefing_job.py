#!/usr/bin/env python3
"""Single-run briefing generation job. Called by GitHub Actions at scheduled times."""
import os
import json
import shutil
import glob
from datetime import datetime, timedelta

IST = timedelta(hours=5, minutes=30)
from briefing.generator import generate_briefing
from briefing.html_formatter import COMPANY_BRAND
from briefing.firehose import generate_firehose


def _parse_briefing_dt(filename: str):
    """Parse datetime from briefing_YYYYMMDD_HHMM.html"""
    base = os.path.basename(filename).replace("briefing_", "").replace(".html", "")
    try:
        dt = datetime.strptime(base, "%Y%m%d_%H%M")
        # Files before 20260726 were saved in UTC — apply IST offset
        if dt.date() < datetime(2026, 7, 26).date():
            dt = dt + IST
        return dt
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

        # Load sidecar metadata if available
        sidecar_path = f.replace(".html", ".json")
        meta = {}
        if os.path.exists(sidecar_path):
            try:
                with open(sidecar_path) as fj:
                    meta = json.load(fj)
            except Exception:
                pass

        companies = meta.get("companies", [])
        domains = meta.get("domains", [])

        # Build company tags (up to 4, colored)
        company_tags = ""
        for c in companies[:4]:
            color = COMPANY_BRAND.get(c, {}).get("color", "#6a7173")
            company_tags += f'<span class="atag" style="background:{color}18;color:{color};border-color:{color}40;">{c}</span>'

        # Build domain tags (up to 3)
        domain_colors = {
            "Capital": "#22c55e", "Power": "#ef4444", "Infrastructure": "#f97316",
            "Talent": "#3b82f6", "Security": "#eab308", "Technology": "#a855f7",
            "Narrative": "#94a3b8",
        }
        domain_tags = ""
        for d in domains[:3]:
            dc = domain_colors.get(d, "#94a3b8")
            domain_tags += f'<span class="atag atag-domain" style="color:{dc};border-color:{dc}30;">{d}</span>'

        tags_html = f'<div class="atags">{company_tags}{domain_tags}</div>' if (company_tags or domain_tags) else ""

        if date_str != current_date:
            if current_date is not None:
                rows.append("</div>")
            rows.append(f'<div class="day-group"><div class="day-label">{date_str}</div>')
            current_date = date_str

        rows.append(f'''
<a class="briefing-link" href="briefings/{rel_path}">
  <div class="blink-left">
    <span class="btime">{time_str}</span>
    {tags_html}
  </div>
  <span class="barrow">→</span>
</a>''')

    if current_date is not None:
        rows.append("</div>")

    count = len(briefing_files)
    now_str = datetime.now().strftime("%d %b %Y %H:%M")
    count_label = str(count) + (" briefings" if count != 1 else " briefing") + " stored"
    rows_html = "".join(rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Tech Intel · Archive</title>
<script>
  try{{var _t=localStorage.getItem('ti-theme');if(_t)document.documentElement.setAttribute('data-theme',_t);}}catch(_e){{}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{
  --canvas:#fdfcf0;--surface:#f1f0e4;--elevated:#fffefa;
  --border-subtle:#e5e4d8;--border-default:#cdc9b8;
  --fg:#080f11;--fg-body:#1a242a;--fg-muted:#6a7173;
  --pill-text:#080f11;--green:#3d9dff;
}}
[data-theme="dark"]{{
  --canvas:#080f11;--surface:#0e1518;--elevated:#141c20;
  --border-subtle:#1f272b;--border-default:#2a343a;
  --fg:#fdfcf0;--fg-body:#f1f0e4;--fg-muted:#888c8d;
  --pill-text:#fdfcf0;
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
.page-nav{{display:flex;gap:6px;margin-bottom:36px;flex-wrap:wrap;}}
.nav-link{{
  font-family:monospace;font-size:11px;letter-spacing:0.12em;text-transform:uppercase;
  padding:5px 12px;border-radius:6px;border:1px solid var(--border-subtle);
  color:var(--fg-muted);text-decoration:none;
  transition:border-color 0.15s,color 0.15s;
}}
.nav-link:hover{{color:var(--fg);border-color:var(--border-default);opacity:1;}}
.nav-link.active{{color:var(--green);border-color:var(--green);}}
.count{{font-family:monospace;font-size:12px;color:var(--fg-muted);
  margin-bottom:28px;letter-spacing:0.06em;text-transform:uppercase;}}
.day-group{{margin-bottom:32px;}}
.day-label{{
  font-family:monospace;font-size:10px;font-weight:400;letter-spacing:0.16em;
  text-transform:uppercase;color:var(--fg-muted);
  padding-bottom:10px;border-bottom:1px solid var(--border-subtle);margin-bottom:8px;
}}
.briefing-link{{
  display:flex;align-items:center;justify-content:space-between;gap:12px;
  padding:14px 18px;margin-bottom:6px;
  background:var(--surface);border:1px solid var(--border-subtle);
  border-radius:10px;transition:border-color 0.15s,background 0.15s;
  text-decoration:none;
}}
.briefing-link:hover{{border-color:var(--border-default);background:var(--elevated);opacity:1;}}
.blink-left{{display:flex;flex-direction:column;gap:7px;flex:1;min-width:0;}}
.btime{{font-family:monospace;font-size:13px;font-weight:600;color:var(--fg);letter-spacing:0.06em;}}
.atags{{display:flex;flex-wrap:wrap;gap:5px;}}
.atag{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.06em;
  padding:2px 8px;border-radius:4px;border:1px solid;color:var(--pill-text);
}}
.atag-domain{{background:transparent;}}
.barrow{{font-size:16px;color:var(--green);flex-shrink:0;}}
.theme-toggle{{
  position:fixed;bottom:24px;right:20px;width:44px;height:44px;border-radius:50%;
  background:var(--surface);border:1px solid var(--border-default);cursor:pointer;
  font-size:18px;display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 8px rgba(0,0,0,0.12);z-index:100;
}}
.theme-toggle:hover{{background:var(--elevated);}}
.footer{{
  margin-top:48px;padding:18px;
  background:var(--fg);border-radius:14px;
  font-family:monospace;font-size:12px;color:var(--canvas);
  text-align:center;letter-spacing:0.1em;text-transform:uppercase;opacity:0.85;
}}
</style>
</head>
<body>
<header class="page-header">
  <p class="eyebrow">Signal Intelligence</p>
  <h1 class="brand">Tech <em>Intel</em> · Archive</h1>
  <p class="sub">Every briefing, ever. Updated hourly.</p>
</header>
<nav class="page-nav">
  <a href="index.html" class="nav-link">Briefing</a>
  <a href="firehose.html" class="nav-link">Firehose</a>
  <a href="archive.html" class="nav-link active">Archive</a>
</nav>
<p class="count">{count_label}</p>
{rows_html}
<footer class="footer">tech-intel</footer>

<button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">&#127769;</button>
<script>
!function(){{
  var b=document.getElementById('themeToggle'),h=document.documentElement;
  function u(){{b.textContent=h.getAttribute('data-theme')==='dark'?'☀️':'\U0001f319';}}
  u();
  b.onclick=function(){{
    var n=h.getAttribute('data-theme')==='dark'?'light':'dark';
    h.setAttribute('data-theme',n);
    try{{localStorage.setItem('ti-theme',n);}}catch(e){{}}
    u();
  }};
}}();
</script>
</body>
</html>"""


    with open("docs/archive.html", "w") as f:
        f.write(html)
    print(f"[briefing] archive updated — {count} briefings indexed.", flush=True)


def main():
    print("[briefing] generating...")
    path, signals = generate_briefing()

    # Publish latest to docs/index.html — fix relative links (briefings/ uses ../ prefix)
    os.makedirs("docs", exist_ok=True)
    with open(path) as f:
        index_html = f.read()
    index_html = index_html.replace('href="../', 'href="')
    with open("docs/index.html", "w") as f:
        f.write(index_html)
    print("[briefing] published to docs/index.html")

    # Copy to docs/briefings/ for public archive
    os.makedirs("docs/briefings", exist_ok=True)
    dest = os.path.join("docs/briefings", os.path.basename(path))
    shutil.copy(path, dest)
    print(f"[briefing] archived to {dest}")

    # Save sidecar metadata for archive tags
    top_companies = []
    seen = set()
    for s in signals:
        sig_text = (s["title"] + " " + (s.get("entities_json") or "")).lower()
        for company in COMPANY_BRAND:
            if company not in seen and company.lower() in sig_text:
                top_companies.append(company)
                seen.add(company)
    top_domains = list(dict.fromkeys(s["domain"] for s in signals))
    sidecar = {"companies": top_companies[:6], "domains": top_domains[:4]}
    sidecar_path = dest.replace(".html", ".json")
    with open(sidecar_path, "w") as f:
        json.dump(sidecar, f)

    # Regenerate archive index
    _generate_archive()

    # Regenerate firehose
    generate_firehose()

    print("[briefing] done.")


if __name__ == "__main__":
    main()
