"""Firehose page — all classified signals from the last 24h, newest first."""
import json
from datetime import datetime
from db.connection import get_connection
from briefing.html_formatter import COMPANY_BRAND, DOMAIN_COLOR, _visible_color


_SOURCE_LABEL = {
    "hackernews":     "HN",
    "rss":            "RSS",
    "github_trending": "GitHub",
    "devto":          "Dev.to",
    "reddit":         "Reddit",
}


def _tags_html(title: str, entities_json: str) -> str:
    sig_text = (title + " " + (entities_json or "")).lower()

    # Company tags — match against COMPANY_BRAND watchlist
    company_tags = ""
    seen = set()
    for company, meta in COMPANY_BRAND.items():
        if company.lower() in sig_text and company not in seen:
            color = _visible_color(meta["color"])
            company_tags += (
                f'<span class="ftag" style="'
                f'background:{color}18;color:{color};border-color:{color}40;">'
                f'{company}</span>'
            )
            seen.add(company)
            if len(seen) >= 4:
                break

    # Fallback: entity tags from entities_json when no company matched
    entity_tags = ""
    if not company_tags and entities_json:
        try:
            entities = json.loads(entities_json)
            for e in entities[:3]:
                name = e.get("name", "")
                if name:
                    entity_tags += f'<span class="ftag ftag-entity">{name}</span>'
        except Exception:
            pass

    return company_tags + entity_tags


def _domain_tag_html(domain: str) -> str:
    color = DOMAIN_COLOR.get(domain, "#94a3b8")
    return (
        f'<span class="ftag ftag-domain" style="color:{color};border-color:{color}30;">'
        f'{domain}</span>'
    )


def _source_tag_html(source: str) -> str:
    label = _SOURCE_LABEL.get(source, source)
    return f'<span class="ftag ftag-source">{label}</span>'


def _load_signals() -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.id, r.title, r.url, r.source,
                  e.domain, e.relevance_score, e.plain_explanation, e.entities_json
           FROM signals_raw r
           JOIN signals_enriched e ON e.raw_id = r.id
           WHERE r.ingested_at >= datetime('now', '-24 hours')
           ORDER BY e.relevance_score DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_firehose() -> str:
    signals = _load_signals()
    count = len(signals)
    now_str = datetime.now().strftime("%d %b %Y %H:%M")

    cards_html = ""
    for s in signals:
        extra_tags = _tags_html(s["title"], s.get("entities_json") or "")
        domain_tag = _domain_tag_html(s["domain"])
        source_tag = _source_tag_html(s["source"])
        tags_row = f'<div class="ftags">{domain_tag}{source_tag}{extra_tags}</div>'

        explanation = s.get("plain_explanation") or ""
        score = s.get("relevance_score") or 0

        cards_html += f"""
<div class="fcard">
  <div class="fcard-meta">
    <span class="fcard-score">{score:.2f}</span>
  </div>
  <a class="fcard-title" href="{s['url']}" target="_blank" rel="noopener">{s['title']}</a>
  {f'<p class="fcard-body">{explanation}</p>' if explanation else ''}
  {tags_row}
</div>"""

    count_label = str(count) + (" signals" if count != 1 else " signal") + " in the last 24h"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Tech Intel · Firehose</title>
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
.page-header{{padding:40px 0 28px;margin-bottom:32px;border-bottom:1px solid var(--border-subtle);}}
.brand{{font-size:clamp(26px,4vw,34px);font-weight:700;color:var(--fg);letter-spacing:-0.02em;margin:10px 0 6px;}}
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
.fcard{{
  background:var(--surface);border:1px solid var(--border-subtle);
  border-radius:14px;padding:22px 24px;margin-bottom:14px;
  transition:border-color 0.15s,background 0.15s;
}}
.fcard:hover{{border-color:var(--border-default);background:var(--elevated);}}
.fcard-meta{{display:flex;align-items:center;gap:10px;margin-bottom:8px;}}
.fcard-score{{
  font-family:monospace;font-size:10px;letter-spacing:0.06em;
  color:var(--fg-muted);background:var(--elevated);
  border:1px solid var(--border-subtle);border-radius:4px;padding:1px 6px;
}}
.fcard-title{{
  display:block;font-size:15px;font-weight:600;color:var(--fg);
  text-decoration:none;margin-bottom:8px;line-height:1.45;
}}
.fcard-title:hover{{color:var(--green);opacity:1;}}
.fcard-body{{font-size:13px;color:var(--fg-muted);margin-bottom:12px;line-height:1.6;}}
.ftags{{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px;}}
.ftag{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.06em;
  padding:2px 8px;border-radius:4px;border:1px solid;
}}
.ftag-domain{{color:inherit;background:transparent;}}
.ftag-source{{
  background:var(--elevated);color:var(--fg-muted);
  border-color:var(--border-subtle);
}}
.ftag-entity{{
  background:transparent;color:var(--fg-muted);
  border-color:var(--border-default);
}}
.empty{{
  text-align:center;padding:80px 20px;
  font-family:monospace;font-size:13px;color:var(--fg-muted);letter-spacing:0.08em;
}}
.theme-toggle{{
  position:fixed;bottom:24px;right:20px;width:44px;height:44px;border-radius:50%;
  background:var(--surface);border:1px solid var(--border-default);cursor:pointer;
  font-size:18px;display:flex;align-items:center;justify-content:center;
  box-shadow:0 2px 8px rgba(0,0,0,0.12);z-index:100;
}}
.theme-toggle:hover{{background:var(--elevated);}}
.footer{{
  margin-top:48px;padding:18px;background:var(--fg);border-radius:14px;
  font-family:monospace;font-size:12px;color:var(--canvas);
  text-align:center;letter-spacing:0.1em;text-transform:uppercase;opacity:0.85;
}}
</style>
</head>
<body>
<header class="page-header">
  <p class="eyebrow">Signal Intelligence</p>
  <h1 class="brand">Tech <em>Intel</em> · Firehose</h1>
  <p class="sub">Every classified signal from the last 24h, newest first.</p>
</header>
<nav class="page-nav">
  <a href="index.html" class="nav-link">Briefing</a>
  <a href="firehose.html" class="nav-link active">Firehose</a>
  <a href="archive.html" class="nav-link">Archive</a>
</nav>
<p class="count">{count_label}</p>
{cards_html if signals else '<div class="empty">NO SIGNALS YET — INGEST PIPELINE RUNNING</div>'}
<footer class="footer">tech-intel · generated {now_str}</footer>
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

    with open("docs/firehose.html", "w") as f:
        f.write(html)
    print(f"[firehose] {count} signals written to docs/firehose.html", flush=True)
    return "docs/firehose.html"
