import json
import re
from datetime import datetime

DOMAIN_COLOR = {
    "Capital":        "#22c55e",
    "Talent":         "#3b82f6",
    "Technology":     "#a855f7",
    "Power":          "#ef4444",
    "Infrastructure": "#f97316",
    "Narrative":      "#6b7280",
    "Security":       "#eab308",
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
    text = re.sub(
        r'\b\d+(?:\.\d+)?%',
        lambda m: f'<span class="number">{m.group()}</span>', text
    )
    text = re.sub(
        r'\b(\d+(?:,\d+)*)\s+(billion|million|trillion)',
        lambda m: f'<span class="number">{m.group(1)} {m.group(2)}</span>', text
    )
    return text


def _enrich(raw: str, entities: list) -> str:
    text = _h(raw)
    text = _highlight_entities(text, entities)
    text = _highlight_numbers(text)
    return text


def _signal_card(i: int, s: dict, why: str) -> str:
    domain = s["domain"]
    color = DOMAIN_COLOR.get(domain, "#6b7280")
    emoji = DOMAIN_EMOJI.get(domain, "📌")
    entities = [e.get("name", "") for e in json.loads(s.get("entities_json") or "[]")]
    explanation = _enrich(s["plain_explanation"], entities)
    why_html = _enrich(why, entities) if why else ""
    pred = _h((s.get("prediction") or "").strip())
    url = s.get("url", "")
    title = _h(s["title"])

    entity_chips = "".join(
        f'<span class="chip">{_h(e)}</span>' for e in entities if e
    )

    return f"""
    <div class="card">
        <div class="card-header">
            <span class="domain-tag" style="background:{color}20; color:{color}; border:1px solid {color}40">
                {emoji} {domain.upper()}
            </span>
            <span class="signal-num">#{i}</span>
        </div>

        <h2 class="signal-title">
            {"<a href='" + url + "' target='_blank'>" + title + "</a>" if url else title}
        </h2>

        <p class="explanation">{explanation}</p>

        {"<div class='why-box'><span class='why-label'>Why it matters</span><p>" + why_html + "</p></div>" if why_html else ""}

        {"<div class='prediction'>🔮 <em>" + pred + "</em></div>" if pred else ""}

        {"<div class='entities'>" + entity_chips + "</div>" if entity_chips else ""}
    </div>
    """


def _company_watch_html(signals: list) -> str:
    rows = []
    for company in ["Apple", "Meta", "Microsoft", "Google", "Amazon",
                    "Nvidia", "OpenAI", "Anthropic", "Tesla", "Baidu", "TSMC", "Samsung"]:
        found = next(
            (s for s in signals
             if company.lower() in s["title"].lower()
             or company.lower() in (s.get("entities_json") or "").lower()),
            None,
        )
        if found:
            idx = signals.index(found) + 1
            rows.append(
                f'<div class="watch-row active">'
                f'<span class="watch-name">{company}</span>'
                f'<span class="watch-ref">→ Signal #{idx}</span>'
                f'</div>'
            )
        else:
            rows.append(
                f'<div class="watch-row quiet">'
                f'<span class="watch-name">{company}</span>'
                f'<span class="watch-quiet">quiet today</span>'
                f'</div>'
            )
    return "\n".join(rows)


def generate_html(signals: list, why_map: dict, question: str,
                  callbacks: list, total_ingested: int) -> str:
    now_str = datetime.now().strftime("%A, %d %B %Y · %H:%M")
    signal_cards = "\n".join(
        _signal_card(i, s, why_map.get(s["id"], ""))
        for i, s in enumerate(signals, 1)
    )
    watch_html = _company_watch_html(signals)
    question_html = _h(question)

    callbacks_html = ""
    if callbacks:
        items = []
        for cb in callbacks:
            status_color = {"confirmed": "#22c55e", "wrong": "#ef4444"}.get(cb["status"], "#f97316")
            items.append(f"""
            <div class="callback-row" style="border-left:3px solid {status_color}">
                <div class="callback-status" style="color:{status_color}">{cb['emoji']} {cb['status'].upper().replace('_',' ')}</div>
                <div class="callback-said">We said: <em>{_h(cb['prediction_text'])}</em></div>
                <div class="callback-result">{_h(cb['note'])}</div>
            </div>
            """)
        callbacks_html = f"""
        <section class="section">
            <h3 class="section-title">🔁 What We Called</h3>
            {"".join(items)}
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tech Intel · {now_str}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #0a0a0f;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 15px;
    line-height: 1.7;
    padding: 16px;
    max-width: 720px;
    margin: 0 auto;
  }}

  a {{ color: #a78bfa; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* Header */
  .header {{
    padding: 24px 0 16px;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 24px;
  }}
  .header-label {{
    font-size: 11px;
    letter-spacing: 2px;
    color: #6b7280;
    text-transform: uppercase;
    margin-bottom: 6px;
  }}
  .header-title {{
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
  }}
  .header-meta {{
    font-size: 12px;
    color: #6b7280;
    margin-top: 6px;
  }}

  /* Section */
  .section {{ margin-bottom: 32px; }}
  .section-title {{
    font-size: 11px;
    letter-spacing: 2px;
    color: #6b7280;
    text-transform: uppercase;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e1e2e;
  }}

  /* Signal cards */
  .card {{
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 16px;
  }}
  .card-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }}
  .domain-tag {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 3px 8px;
    border-radius: 4px;
  }}
  .signal-num {{
    font-size: 12px;
    color: #4b5563;
    margin-left: auto;
  }}
  .signal-title {{
    font-size: 16px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 10px;
    line-height: 1.4;
  }}
  .signal-title a {{ color: #f1f5f9; }}
  .signal-title a:hover {{ color: #a78bfa; }}
  .explanation {{
    color: #94a3b8;
    margin-bottom: 12px;
    font-size: 14px;
  }}

  /* Entity & number highlights */
  .entity {{
    color: #c4b5fd;
    font-weight: 600;
  }}
  .number {{
    color: #34d399;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }}

  /* Why it matters box */
  .why-box {{
    background: #0f172a;
    border-left: 3px solid #7c3aed;
    border-radius: 0 6px 6px 0;
    padding: 12px 14px;
    margin: 12px 0;
  }}
  .why-label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #7c3aed;
    display: block;
    margin-bottom: 6px;
  }}
  .why-box p {{
    font-size: 13px;
    color: #94a3b8;
  }}

  /* Prediction */
  .prediction {{
    font-size: 13px;
    color: #6b7280;
    font-style: italic;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #1e1e2e;
  }}

  /* Entity chips */
  .entities {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
  }}
  .chip {{
    font-size: 11px;
    font-weight: 600;
    color: #a78bfa;
    background: #1e1b4b;
    border: 1px solid #312e81;
    padding: 2px 8px;
    border-radius: 20px;
  }}

  /* Callbacks */
  .callback-row {{
    padding: 12px 14px;
    margin-bottom: 10px;
    background: #111118;
    border-radius: 0 6px 6px 0;
  }}
  .callback-status {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .callback-said, .callback-result {{
    font-size: 13px;
    color: #6b7280;
    margin-top: 3px;
  }}
  .callback-result {{ color: #94a3b8; }}

  /* Company watch */
  .watch-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px;
  }}
  .watch-row {{
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .watch-row.active {{ border-color: #7c3aed40; background: #1e1b4b20; }}
  .watch-name {{
    font-size: 13px;
    font-weight: 600;
    color: #e2e8f0;
    display: block;
  }}
  .watch-ref {{ font-size: 11px; color: #a78bfa; }}
  .watch-quiet {{ font-size: 11px; color: #374151; }}

  /* Question */
  .question-box {{
    background: #111118;
    border: 1px solid #7c3aed40;
    border-radius: 10px;
    padding: 20px;
    font-size: 16px;
    color: #c4b5fd;
    font-style: italic;
    line-height: 1.6;
  }}

  /* Footer */
  .footer {{
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid #1e1e2e;
    font-size: 12px;
    color: #374151;
    text-align: center;
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-label">Signal Intelligence</div>
  <div class="header-title">Tech Intel</div>
  <div class="header-meta">{now_str} &nbsp;·&nbsp; {len(signals)} signals surfaced</div>
</div>

{callbacks_html}

<section class="section">
  <h3 class="section-title">Top Signals</h3>
  {signal_cards}
</section>

<section class="section">
  <h3 class="section-title">Company Watch</h3>
  <div class="watch-grid">
    {watch_html}
  </div>
</section>

<section class="section">
  <h3 class="section-title">Question to sit with</h3>
  <div class="question-box">{question_html}</div>
</section>

<div class="footer">
  {total_ingested} signals ingested (24h) · tech-intel · running locally on your Mac
</div>

</body>
</html>"""
