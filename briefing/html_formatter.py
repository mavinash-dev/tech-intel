import json
import re
from datetime import datetime

DOMAIN_COLOR = {
    "Capital":        "#22c55e",   # green
    "Talent":         "#3b82f6",   # blue
    "Technology":     "#a855f7",   # purple
    "Power":          "#ef4444",   # red
    "Infrastructure": "#f97316",   # orange
    "Narrative":      "#94a3b8",   # slate
    "Security":       "#eab308",   # yellow
}

DOMAIN_EMOJI = {
    "Capital":        "💰",
    "Talent":         "👤",
    "Technology":     "🔵",
    "Power":          "⚡",
    "Infrastructure": "🏗",
    "Narrative":      "📊",
    "Security":       "🔒",
}

GIANT_WATCH = [
    "Apple", "Meta", "Microsoft", "Google", "Amazon",
    "Nvidia", "OpenAI", "Anthropic", "Tesla", "Baidu", "TSMC", "Samsung",
]


def _h(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _highlight_entities(text: str, entities: list) -> str:
    for entity in sorted(entities, key=len, reverse=True):
        if not entity or len(entity) < 3:
            continue
        pattern = r'(?<!\w)' + re.escape(_h(entity)) + r'(?!\w)'
        text = re.sub(pattern, f'<span class="entity">{_h(entity)}</span>', text)
    return text


def _highlight_numbers(text: str) -> str:
    text = re.sub(
        r'\$[\d,\.]+\s*(?:[BMKTbmkt](?:illion|rillion)?)?',
        lambda m: f'<span class="number">{m.group()}</span>', text
    )
    text = re.sub(r'\b\d+(?:\.\d+)?%',
        lambda m: f'<span class="number">{m.group()}</span>', text)
    text = re.sub(r'\b(\d+(?:,\d+)*)\s+(billion|million|trillion)',
        lambda m: f'<span class="number">{m.group(1)} {m.group(2)}</span>', text)
    return text


def _enrich(raw: str, entities: list) -> str:
    text = _h(raw)
    text = _highlight_entities(text, entities)
    text = _highlight_numbers(text)
    return text


def _signal_card(i: int, s: dict, why: str) -> str:
    domain = s["domain"]
    color = DOMAIN_COLOR.get(domain, "#94a3b8")
    emoji = DOMAIN_EMOJI.get(domain, "📌")
    entities = [e.get("name", "") for e in json.loads(s.get("entities_json") or "[]")]
    explanation = _enrich(s["plain_explanation"], entities)
    why_html = _enrich(why, entities) if why else ""
    pred = _h((s.get("prediction") or "").strip())
    url = s.get("url", "")
    title = _h(s["title"])
    score = s.get("relevance_score", 0)
    score_pct = int(score * 100)

    entity_chips = "".join(
        f'<a class="chip" href="https://en.wikipedia.org/wiki/{_h(e)}" target="_blank">{_h(e)}</a>'
        for e in entities if e
    )

    return f"""
<div class="card" style="border-left: 4px solid {color}; background: linear-gradient(135deg, {color}08 0%, #111118 60%);">
  <div class="card-header">
    <span class="domain-tag" style="background:{color}20; color:{color}; border:1px solid {color}50;">
      {emoji}&nbsp;{domain.upper()}
    </span>
    <div class="score-bar-wrap" title="Relevance {score_pct}%">
      <div class="score-bar" style="width:{score_pct}%; background:{color};"></div>
    </div>
    <span class="signal-num" style="color:{color}40;">#{i}</span>
  </div>

  <h2 class="signal-title">
    {"<a href='" + url + "' target='_blank'>" + title + " ↗</a>" if url else title}
  </h2>

  <p class="explanation">{explanation}</p>

  {"<div class='why-box' style='border-left:3px solid " + color + ";'><span class='why-label' style='color:" + color + ";'>Why it matters</span><p>" + why_html + "</p></div>" if why_html else ""}

  {"<div class='prediction'>🔮 <em>" + pred + "</em></div>" if pred else ""}

  {"<div class='entities'>" + entity_chips + "</div>" if entity_chips else ""}
</div>"""


def _company_watch_html(signals: list) -> str:
    items = []
    for company in GIANT_WATCH:
        found = next(
            (s for s in signals
             if company.lower() in s["title"].lower()
             or company.lower() in (s.get("entities_json") or "").lower()),
            None,
        )
        if found:
            color = DOMAIN_COLOR.get(found["domain"], "#94a3b8")
            idx = signals.index(found) + 1
            emoji = DOMAIN_EMOJI.get(found["domain"], "📌")
            items.append(f"""
<div class="watch-card active" style="border:1px solid {color}40; background:{color}08;">
  <span class="watch-dot" style="background:{color};"></span>
  <span class="watch-name">{company}</span>
  <span class="watch-signal" style="color:{color};">{emoji} Signal #{idx}</span>
</div>""")
        else:
            items.append(f"""
<div class="watch-card quiet">
  <span class="watch-dot quiet-dot"></span>
  <span class="watch-name quiet-name">{company}</span>
  <span class="watch-signal quiet-signal">no signal</span>
</div>""")
    return "\n".join(items)


def _callbacks_html(callbacks: list) -> str:
    if not callbacks:
        return ""
    items = []
    for cb in callbacks:
        color = {"confirmed": "#22c55e", "wrong": "#ef4444"}.get(cb["status"], "#f97316")
        items.append(f"""
<div class="callback-row" style="border-left:4px solid {color}; background:{color}08;">
  <div class="callback-status" style="color:{color};">{cb['emoji']} {cb['status'].upper().replace('_',' ')}</div>
  <div class="callback-said">We said: <em>{_h(cb.get('prediction_text',''))}</em></div>
  <div class="callback-result">{_h(cb.get('note',''))}</div>
</div>""")
    return f"""
<section class="section">
  <h3 class="section-title">🔁 What We Called</h3>
  {"".join(items)}
</section>"""


def generate_html(signals: list, why_map: dict, question: str,
                  callbacks: list, total_ingested: int) -> str:
    now_str = datetime.now().strftime("%A, %d %B %Y · %H:%M")
    signal_cards = "\n".join(_signal_card(i, s, why_map.get(s["id"], "")) for i, s in enumerate(signals, 1))
    watch_html = _company_watch_html(signals)
    cb_html = _callbacks_html(callbacks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tech Intel · {now_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #07070d;
    color: #cbd5e1;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 15px;
    line-height: 1.75;
    padding: 20px 16px 60px;
    max-width: 740px;
    margin: 0 auto;
  }}

  /* Links — clearly visible, always underlined */
  a {{ color: #c4b5fd; text-decoration: underline; text-underline-offset: 3px; }}
  a:hover {{ color: #fff; }}

  /* ── Header ─────────────────────────────── */
  .header {{
    padding: 28px 0 20px;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 28px;
  }}
  .header-eyebrow {{
    font-size: 10px; letter-spacing: 3px; color: #4b5563;
    text-transform: uppercase; margin-bottom: 8px;
  }}
  .header-title {{
    font-size: 26px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;
  }}
  .header-title span {{ color: #7c3aed; }}
  .header-meta {{
    font-size: 12px; color: #4b5563; margin-top: 8px;
  }}
  .header-stats {{
    display: flex; gap: 20px; margin-top: 14px; flex-wrap: wrap;
  }}
  .stat {{
    background: #111118; border: 1px solid #1e1e2e; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; color: #6b7280;
  }}
  .stat strong {{ color: #e2e8f0; font-size: 18px; display: block; }}

  /* ── Section ─────────────────────────────── */
  .section {{ margin-bottom: 36px; }}
  .section-title {{
    font-size: 10px; letter-spacing: 3px; color: #4b5563;
    text-transform: uppercase; margin-bottom: 16px;
    padding-bottom: 10px; border-bottom: 1px solid #1a1a2e;
  }}

  /* ── Signal cards ────────────────────────── */
  .card {{
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid #1e1e2e;
  }}
  .card-header {{
    display: flex; align-items: center; gap: 10px; margin-bottom: 12px;
  }}
  .domain-tag {{
    font-size: 10px; font-weight: 800; letter-spacing: 1.5px;
    padding: 4px 10px; border-radius: 5px; text-transform: uppercase;
    flex-shrink: 0;
  }}
  .score-bar-wrap {{
    flex: 1; height: 3px; background: #1e1e2e; border-radius: 2px; overflow: hidden;
  }}
  .score-bar {{ height: 100%; border-radius: 2px; }}
  .signal-num {{
    font-size: 11px; font-weight: 700; flex-shrink: 0;
  }}

  .signal-title {{
    font-size: 17px; font-weight: 700; color: #f1f5f9;
    margin-bottom: 10px; line-height: 1.35;
  }}
  .signal-title a {{
    color: #f1f5f9; text-decoration: underline;
    text-decoration-color: #ffffff30; text-underline-offset: 4px;
  }}
  .signal-title a:hover {{ color: #c4b5fd; text-decoration-color: #c4b5fd; }}

  .explanation {{ color: #94a3b8; font-size: 14px; margin-bottom: 14px; }}

  /* Inline highlights */
  .entity  {{ color: #c4b5fd; font-weight: 600; }}
  .number  {{ color: #34d399; font-weight: 700; font-variant-numeric: tabular-nums; }}

  /* Why it matters */
  .why-box {{
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin: 14px 0;
  }}
  .why-label {{
    font-size: 10px; font-weight: 800; letter-spacing: 2px;
    text-transform: uppercase; display: block; margin-bottom: 6px;
  }}
  .why-box p {{ font-size: 13px; color: #94a3b8; }}

  /* Prediction */
  .prediction {{
    font-size: 13px; color: #6b7280; font-style: italic;
    margin-top: 12px; padding-top: 12px; border-top: 1px solid #1e1e2e;
  }}

  /* Entity chips — link to Wikipedia */
  .entities {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }}
  .chip {{
    font-size: 11px; font-weight: 600; color: #a78bfa;
    background: #1e1b4b; border: 1px solid #312e81;
    padding: 3px 10px; border-radius: 20px;
    text-decoration: none !important;
  }}
  .chip:hover {{ background: #312e81; color: #fff; }}

  /* ── Callbacks ───────────────────────────── */
  .callback-row {{
    border-radius: 0 8px 8px 0;
    padding: 12px 16px; margin-bottom: 10px;
  }}
  .callback-status {{ font-size: 11px; font-weight: 800; letter-spacing: 1px; margin-bottom: 4px; }}
  .callback-said, .callback-result {{ font-size: 13px; color: #6b7280; margin-top: 3px; }}
  .callback-result {{ color: #94a3b8; }}

  /* ── Company Watch ───────────────────────── */
  .watch-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 8px;
  }}
  .watch-card {{
    border-radius: 8px; padding: 10px 12px;
    display: flex; flex-direction: column; gap: 4px;
  }}
  .watch-card.quiet {{
    background: #0f0f18; border: 1px solid #1a1a2e;
  }}
  .watch-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    display: inline-block; margin-bottom: 4px;
  }}
  .quiet-dot {{ background: #2d2d3d; }}
  .watch-name {{ font-size: 13px; font-weight: 700; color: #e2e8f0; }}
  .quiet-name {{ color: #4b5563; }}
  .watch-signal {{ font-size: 11px; font-weight: 600; }}
  .quiet-signal {{ color: #2d2d3d; }}

  /* ── Question ────────────────────────────── */
  .question-box {{
    background: #0f0f18;
    border: 1px solid #7c3aed40;
    border-left: 4px solid #7c3aed;
    border-radius: 0 10px 10px 0;
    padding: 20px 22px;
    font-size: 16px; font-style: italic;
    color: #c4b5fd; line-height: 1.65;
  }}

  /* ── Footer ──────────────────────────────── */
  .footer {{
    margin-top: 40px; padding-top: 20px;
    border-top: 1px solid #1a1a2e;
    font-size: 11px; color: #2d2d3d;
    text-align: center; letter-spacing: 0.5px;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-eyebrow">Signal Intelligence</div>
  <div class="header-title">Tech <span>Intel</span></div>
  <div class="header-meta">{now_str}</div>
  <div class="header-stats">
    <div class="stat"><strong>{len(signals)}</strong>Surfaced</div>
    <div class="stat"><strong>{total_ingested}</strong>Ingested (24h)</div>
    <div class="stat"><strong>{len(callbacks)}</strong>Predictions resolved</div>
  </div>
</div>

{cb_html}

<section class="section">
  <h3 class="section-title">Top Signals</h3>
  {signal_cards}
</section>

<section class="section">
  <h3 class="section-title">Company Watch</h3>
  <div class="watch-grid">{watch_html}</div>
</section>

<section class="section">
  <h3 class="section-title">Question to sit with</h3>
  <div class="question-box">{_h(question)}</div>
</section>

<div class="footer">
  tech-intel · running locally on your Mac · {now_str}
</div>

</body>
</html>"""
