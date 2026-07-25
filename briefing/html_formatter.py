import json
import re
from datetime import datetime
from db.connection import get_connection

DOMAIN_COLOR = {
    "Capital":        "#22c55e",
    "Talent":         "#3b82f6",
    "Technology":     "#a855f7",
    "Power":          "#ef4444",
    "Infrastructure": "#f97316",
    "Narrative":      "#94a3b8",
    "Security":       "#eab308",
}

# Brand colors tuned for dark mode. Categories ordered for watch section grouping.
COMPANY_BRAND = {
    # ── US Big Tech ──────────────────────────────────────
    "Apple":          {"color": "#a2aaad", "cat": "US Big Tech"},
    "Meta":           {"color": "#0082fb", "cat": "US Big Tech"},
    "Microsoft":      {"color": "#0078d4", "cat": "US Big Tech"},
    "Google":         {"color": "#4285f4", "cat": "US Big Tech"},
    "Amazon":         {"color": "#ff9900", "cat": "US Big Tech"},
    "Nvidia":         {"color": "#76b900", "cat": "US Big Tech"},
    "Intel":          {"color": "#0071c5", "cat": "US Big Tech"},
    "AMD":            {"color": "#ed1c24", "cat": "US Big Tech"},
    "Qualcomm":       {"color": "#3253dc", "cat": "US Big Tech"},
    "Broadcom":       {"color": "#cc0000", "cat": "US Big Tech"},
    "IBM":            {"color": "#0530ad", "cat": "US Big Tech"},
    # ── AI / LLM ─────────────────────────────────────────
    "OpenAI":         {"color": "#10a37f", "cat": "AI / LLM"},
    "Anthropic":      {"color": "#d97757", "cat": "AI / LLM"},
    "xAI":            {"color": "#e2e8f0", "cat": "AI / LLM"},
    "Mistral":        {"color": "#f97316", "cat": "AI / LLM"},
    "Cohere":         {"color": "#39b2d5", "cat": "AI / LLM"},
    "Stability AI":   {"color": "#7c3aed", "cat": "AI / LLM"},
    "Hugging Face":   {"color": "#ffd21e", "cat": "AI / LLM"},
    "Perplexity":     {"color": "#20b2aa", "cat": "AI / LLM"},
    "Together AI":    {"color": "#6366f1", "cat": "AI / LLM"},
    "Scale AI":       {"color": "#ea5504", "cat": "AI / LLM"},
    "Runway":         {"color": "#00d8ff", "cat": "AI / LLM"},
    "ElevenLabs":     {"color": "#f59e0b", "cat": "AI / LLM"},
    "Cursor":         {"color": "#8b5cf6", "cat": "AI / LLM"},
    "DeepSeek":       {"color": "#4f8ef7", "cat": "AI / LLM"},
    "Midjourney":     {"color": "#ffffff", "cat": "AI / LLM"},
    "Replicate":      {"color": "#6366f1", "cat": "AI / LLM"},
    # ── Cloud / Infra ────────────────────────────────────
    "Cloudflare":     {"color": "#f38020", "cat": "Cloud / Infra"},
    "Vercel":         {"color": "#e2e8f0", "cat": "Cloud / Infra"},
    "Netlify":        {"color": "#00c7b7", "cat": "Cloud / Infra"},
    "DigitalOcean":   {"color": "#0080ff", "cat": "Cloud / Infra"},
    "Hetzner":        {"color": "#d50c2d", "cat": "Cloud / Infra"},
    "Fastly":         {"color": "#ff282d", "cat": "Cloud / Infra"},
    "Akamai":         {"color": "#009bde", "cat": "Cloud / Infra"},
    "Equinix":        {"color": "#ed2224", "cat": "Cloud / Infra"},
    # ── DevOps / Platform ────────────────────────────────
    "GitHub":         {"color": "#e2e8f0", "cat": "DevOps / Platform"},
    "GitLab":         {"color": "#e24329", "cat": "DevOps / Platform"},
    "HashiCorp":      {"color": "#844fba", "cat": "DevOps / Platform"},
    "Docker":         {"color": "#2496ed", "cat": "DevOps / Platform"},
    "Kubernetes":     {"color": "#326ce5", "cat": "DevOps / Platform"},
    "Pulumi":         {"color": "#8a3391", "cat": "DevOps / Platform"},
    "Atlassian":      {"color": "#0052cc", "cat": "DevOps / Platform"},
    "Linear":         {"color": "#5e6ad2", "cat": "DevOps / Platform"},
    "Notion":         {"color": "#e2e8f0", "cat": "DevOps / Platform"},
    # ── Observability ────────────────────────────────────
    "Datadog":        {"color": "#632ca6", "cat": "Observability"},
    "Grafana":        {"color": "#f46800", "cat": "Observability"},
    "New Relic":      {"color": "#1ce783", "cat": "Observability"},
    "Dynatrace":      {"color": "#1496ff", "cat": "Observability"},
    "Elastic":        {"color": "#00bfb3", "cat": "Observability"},
    "Splunk":         {"color": "#65a637", "cat": "Observability"},
    "PagerDuty":      {"color": "#06ac38", "cat": "Observability"},
    "Honeycomb":      {"color": "#f5a623", "cat": "Observability"},
    # ── Security ─────────────────────────────────────────
    "CrowdStrike":    {"color": "#e8052a", "cat": "Security"},
    "Palo Alto":      {"color": "#fa582d", "cat": "Security"},
    "Okta":           {"color": "#007dc1", "cat": "Security"},
    "Wiz":            {"color": "#00d1ff", "cat": "Security"},
    "Snyk":           {"color": "#4c4a73", "cat": "Security"},
    "SentinelOne":    {"color": "#6f2d8b", "cat": "Security"},
    "Zscaler":        {"color": "#006fce", "cat": "Security"},
    "Fortinet":       {"color": "#ee3124", "cat": "Security"},
    "Cloudflare WAF": {"color": "#f38020", "cat": "Security"},
    "Check Point":    {"color": "#e2000f", "cat": "Security"},
    "CyberArk":       {"color": "#005282", "cat": "Security"},
    # ── Data / Analytics ─────────────────────────────────
    "Snowflake":      {"color": "#29b5e8", "cat": "Data / Analytics"},
    "Databricks":     {"color": "#e8551b", "cat": "Data / Analytics"},
    "dbt Labs":       {"color": "#ff694a", "cat": "Data / Analytics"},
    "Fivetran":       {"color": "#0073e6", "cat": "Data / Analytics"},
    "Confluent":      {"color": "#cc232a", "cat": "Data / Analytics"},
    "Airbyte":        {"color": "#615eff", "cat": "Data / Analytics"},
    "Starburst":      {"color": "#dd00a1", "cat": "Data / Analytics"},
    # ── SaaS / Enterprise ────────────────────────────────
    "Salesforce":     {"color": "#00a1e0", "cat": "SaaS / Enterprise"},
    "ServiceNow":     {"color": "#81b5a1", "cat": "SaaS / Enterprise"},
    "Workday":        {"color": "#f5862e", "cat": "SaaS / Enterprise"},
    "SAP":            {"color": "#008fd3", "cat": "SaaS / Enterprise"},
    "Oracle":         {"color": "#f80000", "cat": "SaaS / Enterprise"},
    "HubSpot":        {"color": "#ff7a59", "cat": "SaaS / Enterprise"},
    "Zendesk":        {"color": "#03363d", "cat": "SaaS / Enterprise"},
    "Twilio":         {"color": "#e11f28", "cat": "SaaS / Enterprise"},
    "Stripe":         {"color": "#635bff", "cat": "SaaS / Enterprise"},
    "Shopify":        {"color": "#96bf48", "cat": "SaaS / Enterprise"},
    "Figma":          {"color": "#1abcfe", "cat": "SaaS / Enterprise"},
    # ── Fintech / Crypto ─────────────────────────────────
    "Coinbase":       {"color": "#0052ff", "cat": "Fintech / Crypto"},
    "Block":          {"color": "#e2e8f0", "cat": "Fintech / Crypto"},
    "Robinhood":      {"color": "#00c805", "cat": "Fintech / Crypto"},
    "Plaid":          {"color": "#111111", "cat": "Fintech / Crypto"},
    "Brex":           {"color": "#ff6b35", "cat": "Fintech / Crypto"},
    "Ripple":         {"color": "#346aa9", "cat": "Fintech / Crypto"},
    "Binance":        {"color": "#f3ba2f", "cat": "Fintech / Crypto"},
    "Klarna":         {"color": "#ffb3c7", "cat": "Fintech / Crypto"},
    # ── US Hardware / Transport ───────────────────────────
    "Tesla":          {"color": "#e82127", "cat": "Hardware / Transport"},
    "SpaceX":         {"color": "#4a90d9", "cat": "Hardware / Transport"},
    "Uber":           {"color": "#276ef1", "cat": "Hardware / Transport"},
    "Waymo":          {"color": "#4285f4", "cat": "Hardware / Transport"},
    "Rivian":         {"color": "#00b1d2", "cat": "Hardware / Transport"},
    "Arm":            {"color": "#0091bd", "cat": "Hardware / Transport"},
    "Applied Materials": {"color": "#009bde", "cat": "Hardware / Transport"},
    # ── China ────────────────────────────────────────────
    "Baidu":          {"color": "#2f6de1", "cat": "China"},
    "Alibaba":        {"color": "#ff6a00", "cat": "China"},
    "Tencent":        {"color": "#07c160", "cat": "China"},
    "ByteDance":      {"color": "#fe2c55", "cat": "China"},
    "Huawei":         {"color": "#cf0a2c", "cat": "China"},
    "Xiaomi":         {"color": "#ff6900", "cat": "China"},
    "DJI":            {"color": "#1a1a2e", "cat": "China"},
    "Meituan":        {"color": "#ffcc00", "cat": "China"},
    "JD.com":         {"color": "#e1251b", "cat": "China"},
    "CATL":           {"color": "#005bac", "cat": "China"},
    "BYD":            {"color": "#1058a7", "cat": "China"},
    "SenseTime":      {"color": "#0084ff", "cat": "China"},
    # ── Korea / Taiwan / Japan ────────────────────────────
    "Samsung":        {"color": "#4a6cf7", "cat": "Korea / Taiwan / Japan"},
    "SK Hynix":       {"color": "#ea5504", "cat": "Korea / Taiwan / Japan"},
    "LG":             {"color": "#a50034", "cat": "Korea / Taiwan / Japan"},
    "Kakao":          {"color": "#fee500", "cat": "Korea / Taiwan / Japan"},
    "Naver":          {"color": "#03c75a", "cat": "Korea / Taiwan / Japan"},
    "TSMC":           {"color": "#5b9bd5", "cat": "Korea / Taiwan / Japan"},
    "MediaTek":       {"color": "#e3000f", "cat": "Korea / Taiwan / Japan"},
    "ASUSTeK":        {"color": "#00539b", "cat": "Korea / Taiwan / Japan"},
    "Foxconn":        {"color": "#e2000a", "cat": "Korea / Taiwan / Japan"},
    "Sony":           {"color": "#00439c", "cat": "Korea / Taiwan / Japan"},
    "SoftBank":       {"color": "#cc0000", "cat": "Korea / Taiwan / Japan"},
    "Rakuten":        {"color": "#bf0000", "cat": "Korea / Taiwan / Japan"},
    "Toyota":         {"color": "#eb0a1e", "cat": "Korea / Taiwan / Japan"},
    # ── Europe ───────────────────────────────────────────
    "ASML":           {"color": "#009fdf", "cat": "Europe"},
    "Spotify":        {"color": "#1db954", "cat": "Europe"},
    "DeepMind":       {"color": "#4285f4", "cat": "Europe"},
    "Wise":           {"color": "#00b9ff", "cat": "Europe"},
    "Revolut":        {"color": "#0075eb", "cat": "Europe"},
    "N26":            {"color": "#39d98a", "cat": "Europe"},
    "Klarna EU":      {"color": "#ffb3c7", "cat": "Europe"},
    "UiPath":         {"color": "#fa4616", "cat": "Europe"},
    "Siemens":        {"color": "#009999", "cat": "Europe"},
    "Nokia":          {"color": "#005aff", "cat": "Europe"},
    "Ericsson":       {"color": "#007bc2", "cat": "Europe"},
    "LVMH Tech":      {"color": "#c9aa71", "cat": "Europe"},
    # ── India ────────────────────────────────────────────
    "Infosys":        {"color": "#007cc3", "cat": "India"},
    "TCS":            {"color": "#0033a0", "cat": "India"},
    "Wipro":          {"color": "#341c6b", "cat": "India"},
    "HCL":            {"color": "#0076c0", "cat": "India"},
    "Reliance Jio":   {"color": "#0b2f6e", "cat": "India"},
    "Flipkart":       {"color": "#2874f0", "cat": "India"},
    "Zepto":          {"color": "#8b1bff", "cat": "India"},
    "PhonePe":        {"color": "#5f259f", "cat": "India"},
    "Razorpay":       {"color": "#3395ff", "cat": "India"},
    "Freshworks":     {"color": "#25c16f", "cat": "India"},
    "Zoho":           {"color": "#e42527", "cat": "India"},
    "Meesho":         {"color": "#9b2882", "cat": "India"},
    "Zomato":         {"color": "#e23744", "cat": "India"},
    "CRED":           {"color": "#1c1c1c", "cat": "India"},
    # ── Semiconductor / EDA ──────────────────────────────
    "Marvell":        {"color": "#005695", "cat": "Semiconductor"},
    "Micron":         {"color": "#e2231a", "cat": "Semiconductor"},
    "Texas Instruments": {"color": "#c1272d", "cat": "Semiconductor"},
    "ASIC Cloud":     {"color": "#667eea", "cat": "Semiconductor"},
    "Cadence":        {"color": "#e2620e", "cat": "Semiconductor"},
    "Synopsys":       {"color": "#00aeef", "cat": "Semiconductor"},
    "KLA":            {"color": "#0070c0", "cat": "Semiconductor"},
    "Lam Research":   {"color": "#c1272d", "cat": "Semiconductor"},
}

GIANT_WATCH = list(COMPANY_BRAND.keys())

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


def _company_recent_signals(company: str, limit: int = 5) -> list:
    """Fetch recent signals from DB that mention this company."""
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT r.title, r.url, r.ingested_at
               FROM signals_raw r
               LEFT JOIN signals_enriched e ON e.raw_id = r.id
               WHERE lower(r.title) LIKE ? OR lower(COALESCE(e.entities_json,'')) LIKE ?
               ORDER BY r.ingested_at DESC
               LIMIT ?""",
            (f"%{company.lower()}%", f"%{company.lower()}%", limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _signal_card(i: int, s: dict, why: str, watching_predictions: list = None) -> str:
    domain = s["domain"]
    color = DOMAIN_COLOR.get(domain, "#94a3b8")
    entities = [e.get("name", "") for e in json.loads(s.get("entities_json") or "[]")]
    url = s.get("url", "")
    title = _h(s["title"])
    explanation = _enrich(s["plain_explanation"], entities)
    why_html = _enrich(why, entities) if why else ""
    pred = _h((s.get("prediction") or "").strip())

    mentioned_giants = [
        c for c in GIANT_WATCH
        if c.lower() in s["title"].lower() or c.lower() in (s.get("entities_json") or "").lower()
    ]
    giant_badges = "".join(
        f'<span class="giant-badge" style="background:{COMPANY_BRAND[c]["color"]}18;color:{COMPANY_BRAND[c]["color"]};border-color:{COMPANY_BRAND[c]["color"]}50;">{c}</span>'
        for c in mentioned_giants
    )

    related_preds = []
    if watching_predictions:
        sig_text = (s["title"] + " " + (s.get("entities_json") or "")).lower()
        for p in watching_predictions:
            p_entities = (p.get("related_entities") or "").lower()
            p_domain = (p.get("domain") or "").lower()
            if p_domain == domain.lower() or any(
                word.strip() in sig_text for word in p_entities.split(",") if len(word.strip()) > 2
            ):
                related_preds.append(p)

    pred_links_html = ""
    if related_preds:
        items = "".join(
            f'<div class="pred-link">⏳ <em>{_h(p["prediction_text"][:120])}{"…" if len(p["prediction_text"]) > 120 else ""}</em></div>'
            for p in related_preds[:2]
        )
        pred_links_html = f'<div class="pred-links-block"><span class="pred-links-label">Watching</span>{items}</div>'

    domain_label = f'<span class="domain-pill" style="background:{color}18;color:{color};border-color:{color}40;">{domain}</span>'

    return f"""
<article class="card" style="border-top:3px solid {color};">
  <div class="card-meta-row">
    {domain_label}
    {"<div class='giant-badges'>" + giant_badges + "</div>" if giant_badges else ""}
  </div>

  <h2 class="sig-title">
    {"<a href='" + url + "' target='_blank'>" + title + " <span class='ext'>↗</span></a>" if url else title}
  </h2>

  <p class="explanation">{explanation}</p>

  {'''<div class="why-block">
    <p class="why-label">Why it matters</p>
    <p class="why-text">''' + why_html + '''</p>
  </div>''' if why_html else ""}

  {pred_links_html}

  {"<p class='prediction'>🔮 " + pred + "</p>" if pred else ""}

</article>"""


def _watch_row(company: str, top_signal=None, signal_idx: int = 0) -> str:
    brand = COMPANY_BRAND.get(company, {"color": "#6b7280"})
    c = brand["color"]

    recent = _company_recent_signals(company, limit=5)
    has_signals = bool(recent)

    if top_signal:
        status_dot = f'<span class="wdot" style="background:{c};box-shadow:0 0 5px {c}80;"></span>'
        name_style = f'color:var(--fg);font-weight:600;'
        signal_tag = f'<span class="wtag wtag-today">in today\'s briefing #{signal_idx}</span>'
    elif has_signals:
        status_dot = f'<span class="wdot" style="background:{c}60;border:1.5px solid {c};"></span>'
        name_style = 'color:var(--fg-body);font-weight:500;'
        signal_tag = f'<span class="wtag wtag-has">{len(recent)} signal{"s" if len(recent) != 1 else ""}</span>'
    else:
        status_dot = f'<span class="wdot" style="background:var(--border-subtle);border:1.5px solid var(--border-default);"></span>'
        name_style = 'color:var(--fg-muted);font-weight:400;'
        signal_tag = '<span class="wtag wtag-none">no data</span>'

    links_html = ""
    if recent:
        items = "".join(
            f'<li><a href="{_h(r["url"] or "#")}" target="_blank" class="wlink">{_h(r["title"][:90])}{"…" if len(r["title"]) > 90 else ""}</a></li>'
            for r in recent if r.get("title")
        )
        links_html = f'<ul class="wlinks">{items}</ul>'
    else:
        links_html = '<p class="wno-data">No signals ingested yet — will populate as the pipeline runs.</p>'

    cat = _h(brand.get("cat", ""))

    return f"""
<details class="wrow">
  <summary class="wrow-summary">
    {status_dot}
    <span class="wname" style="{name_style}">{_h(company)}</span>
    <span class="wcat">{cat}</span>
    {signal_tag}
    <span class="wchev">›</span>
  </summary>
  <div class="wrow-body">
    {links_html}
  </div>
</details>"""


def _company_watch_html(signals: list) -> str:
    # Group companies by category
    from collections import OrderedDict
    cats = OrderedDict()
    for company in GIANT_WATCH:
        cat = COMPANY_BRAND[company].get("cat", "Other")
        cats.setdefault(cat, []).append(company)

    rows_html = []
    for cat, companies in cats.items():
        rows_html.append(f'<div class="wcat-header">{_h(cat)}</div>')
        for company in companies:
            found = next(
                (s for s in signals
                 if company.lower() in s["title"].lower()
                 or company.lower() in (s.get("entities_json") or "").lower()),
                None,
            )
            idx = signals.index(found) + 1 if found else 0
            rows_html.append(_watch_row(company, found, idx))

    return "\n".join(rows_html)


def _predictions_accordion_html(callbacks: list, watching: list) -> str:
    """Render all predictions — resolved ones and still-watching — as an accordion."""
    rows = []

    for cb in callbacks:
        c = {"confirmed": "#22c55e", "wrong": "#ef4444"}.get(cb.get("status", ""), "#f97316")
        status_label = cb.get("emoji", "⏳") + " " + cb.get("status", "").upper().replace("_", " ")
        note = _h(cb.get("note", ""))
        rows.append(f"""
<details class="pred-row">
  <summary class="pred-summary">
    <span class="pred-status" style="color:{c};">{status_label}</span>
    <span class="pred-text">{_h((cb.get('prediction_text') or '')[:80])}…</span>
    <span class="wchev">›</span>
  </summary>
  <div class="pred-body">
    <p class="pred-full">{_h(cb.get('prediction_text',''))}</p>
    {('<p class="pred-note">' + note + '</p>') if note else ''}
  </div>
</details>""")

    for p in watching:
        rows.append(f"""
<details class="pred-row">
  <summary class="pred-summary">
    <span class="pred-status" style="color:#f97316;">⏳ WATCHING</span>
    <span class="pred-text">{_h((p.get('prediction_text') or '')[:80])}…</span>
    <span class="wchev">›</span>
  </summary>
  <div class="pred-body">
    <p class="pred-full">{_h(p.get('prediction_text',''))}</p>
    <p class="pred-meta">Domain: {_h(p.get('domain',''))} · Made: {_h(str(p.get('briefing_date',''))[:10])}</p>
  </div>
</details>""")

    if not rows:
        return ""
    total = len(callbacks) + len(watching)
    return f"""<div class="section-accordion">
  <details>
    <summary>
      <p class="eyebrow">Predictions</p>
      <div class="sum-right">
        <span class="sum-count">{total} total</span>
        <span class="sum-chev">›</span>
      </div>
    </summary>
    <div class="section-accordion-body">
      {"".join(rows)}
    </div>
  </details>
</div>"""


def generate_html(signals: list, why_map: dict, question: str,
                  callbacks: list, total_ingested: int,
                  watching_predictions: list = None) -> str:
    now_str = datetime.now().strftime("%A, %d %B %Y · %H:%M")
    cards_html = "\n".join(
        _signal_card(i, s, why_map.get(s["id"], ""), watching_predictions or [])
        for i, s in enumerate(signals, 1)
    )
    watch_html = _company_watch_html(signals)
    preds_html = _predictions_accordion_html(callbacks, watching_predictions or [])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Tech Intel · {now_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ── Design tokens ── */
:root{{
  --canvas:   #fdfcf0;
  --surface:  #f1f0e4;
  --elevated: #fffefa;
  --border-subtle: #e5e4d8;
  --border-default: #cdc9b8;
  --fg:       #080f11;
  --fg-body:  #1a242a;
  --fg-muted: #6a7173;
  --green:    #1ce783;
  --green-tint:#aaf2ce;
  --blue:     #3d9dff;
  --ember:    #ff7f4d;
  --yellow:   #f7d354;
}}

*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:var(--canvas);color:var(--fg-body);
  font-family:'Inter',system-ui,sans-serif;
  font-size:16px;line-height:1.7;
  padding:32px 20px 80px;max-width:900px;margin:0 auto;
}}
a{{color:var(--fg);text-decoration:underline;text-underline-offset:3px;}}
a:hover{{color:#1a242a;}}
hr{{border:none;border-top:1px solid var(--border-subtle);margin:0;}}

/* ── Eyebrow (mono uppercase label) ── */
.eyebrow{{
  font-family:'SF Mono','Fira Code','Fira Mono',monospace;
  font-size:11px;letter-spacing:0.16em;color:var(--fg-muted);
  text-transform:uppercase;font-weight:400;
}}

/* ── Page header ── */
.page-header{{padding:40px 0 32px;margin-bottom:40px;}}
.brand{{font-size:clamp(28px,4vw,38px);font-weight:700;color:var(--fg);
  letter-spacing:-0.02em;line-height:1.15;margin:10px 0 6px;}}
.brand em{{color:var(--green);font-style:normal;}}
.dateline{{font-size:14px;color:var(--fg-muted);}}
.stats{{display:flex;gap:8px;margin-top:20px;flex-wrap:wrap;}}
.stat{{
  background:var(--surface);border:1px solid var(--border-subtle);
  border-radius:10px;padding:12px 18px;min-width:88px;
}}
.stat strong{{font-size:clamp(22px,3vw,26px);font-weight:700;color:var(--fg);
  display:block;line-height:1.1;letter-spacing:-0.02em;}}
.stat span{{font-size:11px;color:var(--fg-muted);font-family:monospace;text-transform:uppercase;letter-spacing:0.1em;}}

/* ── Section wrapper ── */
.section{{margin-bottom:44px;}}
.section-head{{display:flex;align-items:center;gap:10px;margin-bottom:18px;}}
.section-head hr{{flex:1;}}

/* ── Signal cards — gradient slab pattern ── */
.cards-slab{{
  border-radius:20px;padding:4px;gap:3px;
  background:linear-gradient(135deg, var(--green-tint) 0%, var(--green) 100%);
  display:flex;flex-direction:column;
}}
.card{{
  background:var(--elevated);border-radius:16px;
  padding:24px 26px;color:var(--fg);
}}
.card-meta-row{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;}}
.domain-pill{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.12em;
  text-transform:uppercase;padding:3px 9px;border-radius:4px;border:1px solid;
}}
.giant-badges{{display:flex;flex-wrap:wrap;gap:5px;}}
.giant-badge{{font-size:10px;font-weight:600;padding:2px 8px;border-radius:4px;border:1px solid;}}
.sig-title{{font-size:clamp(16px,2.5vw,19px);font-weight:600;color:var(--fg);
  margin-bottom:10px;line-height:1.4;letter-spacing:-0.01em;}}
.sig-title a{{color:var(--fg);text-decoration:underline;text-decoration-color:rgba(8,15,17,0.2);text-underline-offset:3px;}}
.sig-title a:hover{{text-decoration-color:var(--fg);}}
.ext{{font-size:12px;color:var(--fg-muted);}}
.explanation{{color:var(--fg-body);font-size:15px;margin-bottom:12px;line-height:1.75;}}
.entity{{color:var(--fg);font-weight:600;border-bottom:1.5px solid var(--green);}}
.num{{color:#059669;font-weight:700;}}
.why-block{{
  margin:14px 0;padding:13px 16px;
  background:rgba(255,127,77,0.07);
  border-radius:8px;border-left:3px solid var(--ember);
}}
.why-label{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.14em;
  text-transform:uppercase;color:var(--ember);margin-bottom:5px;
}}
.why-text{{font-size:14px;color:var(--fg-body);line-height:1.65;}}
.pred-links-block{{
  margin:12px 0;padding:11px 14px;
  background:rgba(28,231,131,0.07);border-radius:8px;border-left:3px solid var(--green);
}}
.pred-links-label{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.14em;
  text-transform:uppercase;color:var(--green);display:block;margin-bottom:5px;
}}
.pred-link{{font-size:13px;color:var(--fg-muted);margin-top:4px;}}
.prediction{{font-size:14px;color:var(--fg-muted);font-style:italic;
  margin-top:14px;padding-top:14px;border-top:1px solid var(--border-subtle);}}

/* ── Collapsible section accordion ── */
.section-accordion{{margin-bottom:44px;}}
.section-accordion > details{{
  border:1px solid var(--border-subtle);border-radius:14px;
  background:var(--surface);
}}
.section-accordion > details > summary{{
  display:flex;align-items:center;justify-content:space-between;
  padding:15px 20px;cursor:pointer;list-style:none;user-select:none;
}}
.section-accordion > details > summary::-webkit-details-marker{{display:none;}}
.section-accordion > details > summary:hover{{background:var(--elevated);border-radius:14px;}}
.section-accordion > details[open] > summary{{
  border-bottom:1px solid var(--border-subtle);border-radius:14px 14px 0 0;
}}
.section-accordion-body{{padding:18px 20px;}}
.sum-right{{display:flex;align-items:center;gap:10px;}}
.sum-count{{
  font-family:monospace;font-size:11px;color:var(--fg-muted);
  font-weight:400;letter-spacing:0;text-transform:none;
}}
.sum-chev{{font-size:15px;color:var(--fg-muted);transition:transform 0.15s;}}
details[open] .sum-chev{{transform:rotate(90deg);}}

/* ── Predictions rows ── */
.pred-row{{border-bottom:1px solid var(--border-subtle);}}
.pred-row:last-child{{border-bottom:none;}}
.pred-summary{{
  display:flex;align-items:center;gap:10px;
  padding:12px 4px;cursor:pointer;list-style:none;user-select:none;
}}
.pred-summary::-webkit-details-marker{{display:none;}}
.pred-summary:hover{{opacity:0.8;}}
.pred-status{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.1em;
  flex-shrink:0;width:100px;text-transform:uppercase;
}}
.pred-text{{font-size:14px;color:var(--fg-muted);flex:1;
  overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}}
.pred-body{{padding:6px 0 14px 28px;}}
.pred-full{{font-size:15px;color:var(--fg-body);line-height:1.6;}}
.pred-note{{font-size:13px;color:var(--fg-muted);margin-top:6px;}}
.pred-meta{{font-family:monospace;font-size:11px;color:var(--fg-muted);margin-top:6px;letter-spacing:0.06em;}}

/* ── Company watch ── */
.wcat-header{{
  font-family:monospace;font-size:10px;letter-spacing:0.16em;text-transform:uppercase;
  color:var(--fg-muted);padding:16px 0 8px;
  border-bottom:1px solid var(--border-subtle);margin-bottom:2px;font-weight:400;
}}
.wrow{{border-bottom:1px solid var(--border-subtle);}}
.wrow:last-child{{border-bottom:none;}}
.wrow-summary{{
  display:flex;align-items:center;gap:8px;
  padding:10px 4px;cursor:pointer;list-style:none;user-select:none;
}}
.wrow-summary::-webkit-details-marker{{display:none;}}
.wrow-summary:hover{{opacity:0.8;}}
.wdot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;background:transparent;}}
.active-dot{{box-shadow:none;}}
.wname{{font-size:14px;font-weight:500;flex-shrink:0;min-width:130px;color:var(--fg-body);}}
.wcat{{font-size:11px;color:var(--fg-muted);flex:1;font-family:monospace;letter-spacing:0.05em;}}
.wtag{{
  font-family:monospace;font-size:10px;font-weight:500;letter-spacing:0.08em;
  padding:2px 8px;border-radius:4px;flex-shrink:0;text-transform:uppercase;
}}
.wtag-today{{background:rgba(28,231,131,0.15);color:#059669;border:1px solid rgba(28,231,131,0.4);}}
.wtag-has{{background:rgba(61,157,255,0.1);color:#2563eb;border:1px solid rgba(61,157,255,0.3);}}
.wtag-none{{background:var(--surface);color:var(--fg-muted);border:1px solid var(--border-subtle);}}
.wchev{{font-size:14px;color:var(--fg-muted);flex-shrink:0;transition:transform 0.15s;}}
details[open] .wchev{{transform:rotate(90deg);}}
.wrow-body{{padding:6px 0 12px 24px;}}
.wlinks{{list-style:none;}}
.wlinks li{{padding:3px 0;border-bottom:1px solid var(--border-subtle);}}
.wlinks li:last-child{{border-bottom:none;}}
.wlink{{font-size:13px;color:var(--fg-muted);text-decoration:none;display:block;line-height:1.5;}}
.wlink:hover{{color:var(--fg);}}
.wno-data{{font-size:12px;color:var(--border-default);font-family:monospace;}}

/* ── Question box ── */
.q-box{{
  background:var(--surface);border:1px solid var(--border-subtle);
  border-left:3px solid var(--green);border-radius:0 12px 12px 0;
  padding:20px 24px;font-size:clamp(15px,2.2vw,17px);font-style:italic;
  color:var(--fg);line-height:1.75;font-weight:500;
}}

/* ── Archive card ── */
.archive-card{{
  display:flex;align-items:center;justify-content:space-between;
  padding:18px 22px;background:var(--surface);
  border:1px solid var(--border-subtle);border-radius:12px;
  text-decoration:none;transition:border-color 0.15s,background 0.15s;
}}
.archive-card:hover{{border-color:var(--border-default);background:var(--elevated);}}
.archive-card-title{{font-size:16px;font-weight:600;color:var(--fg);}}
.archive-card-sub{{font-size:13px;color:var(--fg-muted);margin-top:3px;}}
.archive-card-arrow{{font-size:18px;color:var(--green);}}

/* ── Footer ── */
.footer{{
  margin-top:48px;padding:20px;
  background:var(--fg);border-radius:14px;
  font-family:monospace;font-size:12px;color:rgba(253,252,240,0.5);
  text-align:center;letter-spacing:0.1em;text-transform:uppercase;
}}
.footer a{{color:rgba(28,231,131,0.8);text-decoration:none;}}
.footer a:hover{{color:#1ce783;}}

/* ── Mobile ── */
@media(max-width:480px){{
  body{{padding:20px 14px 56px;font-size:15px;}}
  .stats{{gap:7px;}}
  .stat{{padding:10px 14px;min-width:80px;}}
  .card{{padding:16px 18px;}}
  .wname{{min-width:100px;}}
  .pred-status{{width:84px;}}
  .explanation{{font-size:14px;}}
  .cards-slab{{border-radius:16px;}}
}}
</style>
</head>
<body>

<header class="page-header">
  <p class="eyebrow">Signal Intelligence</p>
  <h1 class="brand">Tech <em>Intel</em></h1>
  <p class="dateline">{now_str}</p>
  <div class="stats">
    <div class="stat"><strong>{len(signals)}</strong><span>Top signals</span></div>
    <div class="stat"><strong>{total_ingested}</strong><span>Articles scanned</span></div>
    <div class="stat"><strong>{len(callbacks)}</strong><span>Predictions resolved</span></div>
  </div>
</header>

<section class="section">
  <div class="section-head">
    <p class="eyebrow">Top Signals</p>
    <hr>
  </div>
  <div class="cards-slab">
    {cards_html}
  </div>
</section>

{preds_html}

<div class="section-accordion">
  <details>
    <summary>
      <p class="eyebrow">Company Watch</p>
      <div class="sum-right">
        <span class="sum-count">{len(GIANT_WATCH)} companies</span>
        <span class="sum-chev">›</span>
      </div>
    </summary>
    <div class="section-accordion-body">
      {watch_html}
    </div>
  </details>
</div>

<section class="section">
  <div class="section-head">
    <p class="eyebrow">Question to sit with</p>
    <hr>
  </div>
  <div class="q-box">{_h(question)}</div>
</section>

<section class="section">
  <div class="section-head">
    <p class="eyebrow">Past Briefings</p>
    <hr>
  </div>
  <a href="archive.html" class="archive-card">
    <div>
      <div class="archive-card-title">Briefing Archive</div>
      <div class="archive-card-sub">Every briefing, grouped by date</div>
    </div>
    <span class="archive-card-arrow">→</span>
  </a>
</section>

<footer class="footer">
  tech-intel · {now_str} · <a href="archive.html">archive</a>
</footer>
</body>
</html>"""
