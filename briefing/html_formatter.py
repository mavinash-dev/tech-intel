import json
import re
from datetime import datetime
from db.connection import get_connection

# Domain as hashtag color — subtle, not a heading
DOMAIN_COLOR = {
    "Capital":        "#22c55e",
    "Talent":         "#3b82f6",
    "Technology":     "#a855f7",
    "Power":          "#ef4444",
    "Infrastructure": "#f97316",
    "Narrative":      "#94a3b8",
    "Security":       "#eab308",
}

# Real brand colors, tuned for dark mode visibility
COMPANY_BRAND = {
    "Apple":     {"color": "#a2aaad", "bg": "#a2aaad12"},
    "Meta":      {"color": "#0082fb", "bg": "#0082fb12"},
    "Microsoft": {"color": "#0078d4", "bg": "#0078d412"},
    "Google":    {"color": "#4285f4", "bg": "#4285f412"},
    "Amazon":    {"color": "#ff9900", "bg": "#ff990012"},
    "Nvidia":    {"color": "#76b900", "bg": "#76b90012"},
    "OpenAI":    {"color": "#10a37f", "bg": "#10a37f12"},
    "Anthropic": {"color": "#d97757", "bg": "#d9775712"},
    "Tesla":     {"color": "#e82127", "bg": "#e8212712"},
    "Baidu":     {"color": "#2f6de1", "bg": "#2f6de112"},
    "TSMC":      {"color": "#5b9bd5", "bg": "#5b9bd512"},
    "Samsung":   {"color": "#4a6cf7", "bg": "#4a6cf712"},
}

GIANT_WATCH = list(COMPANY_BRAND.keys())

# Consistent "Why it matters" accent — same across every card
WHY_COLOR = "#f97316"


def _h(t: str) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _highlight_entities(text: str, entities: list) -> str:
    for e in sorted(entities, key=len, reverse=True):
        if not e or len(e) < 3:
            continue
        text = re.sub(
            r'(?<!\w)' + re.escape(_h(e)) + r'(?!\w)',
            f'<span class="entity">{_h(e)}</span>', text
        )
    return text


def _highlight_numbers(text: str) -> str:
    text = re.sub(r'\$[\d,\.]+\s*(?:[BMKTbmkt](?:illion|rillion)?)?',
        lambda m: f'<span class="num">{m.group()}</span>', text)
    text = re.sub(r'\b\d+(?:\.\d+)?%',
        lambda m: f'<span class="num">{m.group()}</span>', text)
    text = re.sub(r'\b(\d+(?:,\d+)*)\s+(billion|million|trillion)',
        lambda m: f'<span class="num">{m.group(1)} {m.group(2)}</span>', text)
    return text


def _enrich(raw: str, entities: list) -> str:
    text = _h(raw)
    text = _highlight_entities(text, entities)
    text = _highlight_numbers(text)
    return text


def _last_seen(company: str) -> str:
    """Return how many days ago we last saw this company in signals."""
    try:
        conn = get_connection()
        row = conn.execute(
            """SELECT MAX(r.ingested_at) as last
               FROM signals_raw r
               JOIN signals_enriched e ON e.raw_id = r.id
               WHERE lower(r.title) LIKE ? OR lower(e.entities_json) LIKE ?""",
            (f"%{company.lower()}%", f"%{company.lower()}%"),
        ).fetchone()
        conn.close()
        if row and row["last"]:
            last_dt = datetime.fromisoformat(row["last"])
            days = (datetime.utcnow() - last_dt).days
            if days == 0:
                return "seen today"
            elif days == 1:
                return "seen yesterday"
            else:
                return f"last seen {days}d ago"
    except Exception:
        pass
    return "monitoring"


def _signal_card(i: int, s: dict, why: str) -> str:
    domain = s["domain"]
    color = DOMAIN_COLOR.get(domain, "#94a3b8")
    score_pct = int(s.get("relevance_score", 0) * 100)
    entities = [e.get("name", "") for e in json.loads(s.get("entities_json") or "[]")]
    url = s.get("url", "")
    title = _h(s["title"])
    explanation = _enrich(s["plain_explanation"], entities)
    why_html = _enrich(why, entities) if why else ""
    pred = _h((s.get("prediction") or "").strip())

    # Hashtag-style domain tag + sub-tags from entities (top 2)
    tags = f'<span class="tag" style="color:{color};">#{domain.lower()}</span>'
    for e in entities[:2]:
        slug = e.lower().replace(" ", "")
        tags += f' <span class="tag tag-entity">#{slug}</span>'

    entity_chips = "".join(
        f'<a class="chip" href="https://en.wikipedia.org/wiki/{_h(e)}" target="_blank">{_h(e)}</a>'
        for e in entities if e
    )

    return f"""
<div class="card" style="border-left:4px solid {color}; background:linear-gradient(135deg,{color}09 0%,#0f0f18 55%);">
  <div class="card-top">
    <div class="tags">{tags}</div>
    <div class="score-wrap" title="Relevance {score_pct}%">
      <div class="score-fill" style="width:{score_pct}%;background:{color};"></div>
    </div>
  </div>

  <h2 class="sig-title">
    {"<a href='" + url + "' target='_blank'>" + title + " <span class='ext'>↗</span></a>" if url else title}
  </h2>

  <p class="explanation">{explanation}</p>

  {'''<div class="why-block">
    <span class="why-heading">Why it matters</span>
    <p class="why-text">''' + why_html + '''</p>
  </div>''' if why_html else ""}

  {"<p class='prediction'>🔮 " + pred + "</p>" if pred else ""}

  {"<div class='chips'>" + entity_chips + "</div>" if entity_chips else ""}
</div>"""


def _watch_card(company: str, signal=None, signal_idx: int = 0) -> str:
    brand = COMPANY_BRAND.get(company, {"color": "#6b7280", "bg": "#6b728012"})
    c = brand["color"]
    bg = brand["bg"]

    if signal:
        domain = signal["domain"]
        domain_color = DOMAIN_COLOR.get(domain, "#94a3b8")
        title_short = signal["title"][:55] + ("…" if len(signal["title"]) > 55 else "")
        return f"""
<div class="wcard active" style="border:1px solid {c}; background:{bg};">
  <div class="wcard-top">
    <span class="wdot" style="background:{c}; box-shadow:0 0 8px {c};"></span>
    <span class="wname" style="color:{c};">{company}</span>
  </div>
  <div class="wcard-signal">
    <span class="wtag" style="color:{domain_color};">#{domain.lower()}</span>
    <span class="wtitle">{_h(title_short)}</span>
  </div>
  <div class="wref">→ Signal #{signal_idx}</div>
</div>"""
    else:
        last = _last_seen(company)
        return f"""
<div class="wcard quiet" style="border:1px solid #2a2a3a;">
  <div class="wcard-top">
    <span class="wdot" style="background:#2a2a3a; border:1px solid {c};"></span>
    <span class="wname" style="color:#6b7280;">{company}</span>
  </div>
  <div class="wcard-signal">
    <span class="wlast" style="color:#4b5563;">{last}</span>
  </div>
</div>"""


def _company_watch_html(signals: list) -> str:
    cards = []
    for company in GIANT_WATCH:
        found = next(
            (s for s in signals
             if company.lower() in s["title"].lower()
             or company.lower() in (s.get("entities_json") or "").lower()),
            None,
        )
        idx = signals.index(found) + 1 if found else 0
        cards.append(_watch_card(company, found, idx))
    return "\n".join(cards)


def _callbacks_html(callbacks: list) -> str:
    if not callbacks:
        return ""
    items = []
    for cb in callbacks:
        c = {"confirmed": "#22c55e", "wrong": "#ef4444"}.get(cb["status"], "#f97316")
        items.append(f"""
<div class="cb-row" style="border-left:4px solid {c};background:{c}08;">
  <span class="cb-status" style="color:{c};">{cb['emoji']} {cb['status'].upper().replace('_',' ')}</span>
  <p class="cb-said">We said: <em>{_h(cb.get('prediction_text',''))}</em></p>
  <p class="cb-result">{_h(cb.get('note',''))}</p>
</div>""")
    return f"""<section class="section">
  <h3 class="sec-title">🔁 What We Called</h3>
  {"".join(items)}
</section>"""


def generate_html(signals: list, why_map: dict, question: str,
                  callbacks: list, total_ingested: int) -> str:
    now_str = datetime.now().strftime("%A, %d %B %Y · %H:%M")
    cards_html = "\n".join(_signal_card(i, s, why_map.get(s["id"], "")) for i, s in enumerate(signals, 1))
    watch_html = _company_watch_html(signals)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Tech Intel · {now_str}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:#07070d;color:#cbd5e1;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  font-size:15px;line-height:1.75;
  padding:20px 16px 60px;max-width:740px;margin:0 auto;
}}
a{{color:#c4b5fd;text-decoration:underline;text-underline-offset:3px;}}
a:hover{{color:#fff;}}

/* Header */
.header{{padding:28px 0 20px;border-bottom:1px solid #1a1a2a;margin-bottom:28px;}}
.eyebrow{{font-size:10px;letter-spacing:3px;color:#3d3d55;text-transform:uppercase;margin-bottom:8px;}}
.brand{{font-size:28px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;}}
.brand em{{color:#7c3aed;font-style:normal;}}
.dateline{{font-size:12px;color:#3d3d55;margin-top:6px;}}
.stats{{display:flex;gap:12px;margin-top:16px;flex-wrap:wrap;}}
.stat{{background:#0f0f18;border:1px solid #1a1a2a;border-radius:8px;padding:8px 14px;}}
.stat strong{{font-size:20px;font-weight:800;color:#e2e8f0;display:block;line-height:1.2;}}
.stat span{{font-size:11px;color:#3d3d55;}}

/* Section */
.section{{margin-bottom:36px;}}
.sec-title{{font-size:10px;letter-spacing:3px;color:#3d3d55;text-transform:uppercase;
  margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #1a1a2a;}}

/* Signal card */
.card{{border-radius:12px;padding:20px;margin-bottom:14px;border:1px solid #1a1a2a;}}
.card-top{{display:flex;align-items:center;gap:10px;margin-bottom:12px;}}
.tags{{display:flex;gap:6px;flex-wrap:wrap;flex:1;}}
.tag{{font-size:10px;font-weight:700;letter-spacing:0.5px;}}
.tag-entity{{color:#3d3d55;}}
.score-wrap{{width:60px;height:3px;background:#1a1a2a;border-radius:2px;overflow:hidden;flex-shrink:0;}}
.score-fill{{height:100%;border-radius:2px;}}
.sig-title{{font-size:17px;font-weight:700;color:#f1f5f9;margin-bottom:10px;line-height:1.35;}}
.sig-title a{{color:#f1f5f9;text-decoration:underline;text-decoration-color:#ffffff20;text-underline-offset:4px;}}
.sig-title a:hover{{color:#c4b5fd;text-decoration-color:#c4b5fd;}}
.ext{{font-size:13px;color:#3d3d55;}}
.explanation{{color:#8892a4;font-size:14px;margin-bottom:14px;}}

/* Highlights */
.entity{{color:#c4b5fd;font-weight:600;}}
.num{{color:#34d399;font-weight:700;}}

/* Why it matters — no border, consistent orange heading */
.why-block{{margin:14px 0;}}
.why-heading{{
  font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
  color:{WHY_COLOR};display:block;margin-bottom:6px;
}}
.why-text{{font-size:13px;color:#6b7280;}}

.prediction{{font-size:13px;color:#4b5563;font-style:italic;
  margin-top:12px;padding-top:12px;border-top:1px solid #1a1a2a;}}

/* Entity chips → Wikipedia */
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px;}}
.chip{{font-size:11px;font-weight:600;color:#a78bfa;background:#1e1b4b;
  border:1px solid #312e81;padding:3px 10px;border-radius:20px;
  text-decoration:none!important;}}
.chip:hover{{background:#312e81;color:#fff;}}

/* Callbacks */
.cb-row{{border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:10px;}}
.cb-status{{font-size:11px;font-weight:800;letter-spacing:1px;display:block;margin-bottom:4px;}}
.cb-said,.cb-result{{font-size:13px;color:#4b5563;margin-top:3px;}}
.cb-result{{color:#8892a4;}}

/* Company watch grid */
.watch-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;}}
.wcard{{border-radius:10px;padding:12px 14px;}}
.wcard-top{{display:flex;align-items:center;gap:8px;margin-bottom:6px;}}
.wdot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;}}
.quiet-dot{{}}
.wname{{font-size:13px;font-weight:700;}}
.wcard-signal{{font-size:12px;}}
.wtag{{font-weight:700;margin-right:4px;}}
.wtitle{{color:#6b7280;}}
.wref{{font-size:11px;color:#3d3d55;margin-top:4px;}}
.wlast{{color:#3d3d55;font-size:11px;}}

/* Question */
.q-box{{
  background:#0f0f18;border:1px solid #7c3aed30;
  border-left:4px solid #7c3aed;border-radius:0 10px 10px 0;
  padding:20px 22px;font-size:16px;font-style:italic;
  color:#c4b5fd;line-height:1.65;
}}

/* Footer */
.footer{{margin-top:40px;padding-top:20px;border-top:1px solid #1a1a2a;
  font-size:11px;color:#1e1e2e;text-align:center;letter-spacing:0.5px;}}
</style>
</head>
<body>

<div class="header">
  <div class="eyebrow">Signal Intelligence</div>
  <div class="brand">Tech <em>Intel</em></div>
  <div class="dateline">{now_str}</div>
  <div class="stats">
    <div class="stat"><strong>{len(signals)}</strong><span>Surfaced</span></div>
    <div class="stat"><strong>{total_ingested}</strong><span>Ingested (24h)</span></div>
    <div class="stat"><strong>{len(callbacks)}</strong><span>Predictions hit</span></div>
  </div>
</div>

{_callbacks_html(callbacks)}

<section class="section">
  <h3 class="sec-title">Top Signals</h3>
  {cards_html}
</section>

<section class="section">
  <h3 class="sec-title">Company Watch</h3>
  <div class="watch-grid">{watch_html}</div>
</section>

<section class="section">
  <h3 class="sec-title">Question to sit with</h3>
  <div class="q-box">{_h(question)}</div>
</section>

<div class="footer">tech-intel · {now_str}</div>
</body>
</html>"""
