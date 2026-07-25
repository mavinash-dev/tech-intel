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
        f'<span class="giant-badge" style="color:{COMPANY_BRAND[c]["color"]};border-color:{COMPANY_BRAND[c]["color"]}40;">{c}</span>'
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
        pred_links_html = f'<div class="pred-links-block"><span class="pred-links-label">Watching prediction</span>{items}</div>'

    return f"""
<div class="card" style="border-left:4px solid {color}; background:linear-gradient(135deg,{color}08 0%,#0f0f18 60%);">

  {"<div class='giant-badges'>" + giant_badges + "</div>" if giant_badges else ""}

  <h2 class="sig-title">
    {"<a href='" + url + "' target='_blank'>" + title + " <span class='ext'>↗</span></a>" if url else title}
  </h2>

  <p class="explanation">{explanation}</p>

  {'''<div class="why-block">
    <span class="why-heading">Why it matters</span>
    <p class="why-text">''' + why_html + '''</p>
  </div>''' if why_html else ""}

  {pred_links_html}

  {"<p class='prediction'>🔮 " + pred + "</p>" if pred else ""}

</div>"""


def _watch_row(company: str, top_signal=None, signal_idx: int = 0) -> str:
    brand = COMPANY_BRAND.get(company, {"color": "#6b7280"})
    c = brand["color"]

    recent = _company_recent_signals(company, limit=5)

    if top_signal:
        status_dot = f'<span class="wdot active-dot" style="background:{c};box-shadow:0 0 6px {c};"></span>'
        name_style = f'color:{c};font-weight:700;'
        meta = f'<span class="wref">→ in today\'s signal #{signal_idx}</span>'
    else:
        status_dot = f'<span class="wdot" style="border:1.5px solid {c};"></span>'
        name_style = 'color:#94a3b8;font-weight:600;'
        meta = ""

    links_html = ""
    if recent:
        items = "".join(
            f'<li><a href="{_h(r["url"] or "#")}" target="_blank" class="wlink">{_h(r["title"][:90])}{"…" if len(r["title"]) > 90 else ""}</a></li>'
            for r in recent if r.get("title")
        )
        links_html = f'<ul class="wlinks">{items}</ul>'
    else:
        links_html = '<p class="wno-data">No signals ingested yet for this company.</p>'

    cat = _h(brand.get("cat", ""))

    return f"""
<details class="wrow">
  <summary class="wrow-summary">
    {status_dot}
    <span class="wname" style="{name_style}">{_h(company)}</span>
    <span class="wcat">{cat}</span>
    {meta}
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
    return f"""<section class="section">
  <h3 class="sec-title">Predictions</h3>
  {"".join(rows)}
</section>"""


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
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:#07070d;color:#c8d3e0;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  font-size:clamp(14px,2.2vw,16px);line-height:1.65;
  padding:16px 14px 48px;max-width:860px;margin:0 auto;
}}
a{{color:#a78bfa;text-decoration:underline;text-underline-offset:3px;}}
a:hover{{color:#fff;}}

/* ── Header ── */
.header{{padding:20px 0 16px;border-bottom:1px solid #1a1a2a;margin-bottom:20px;}}
.eyebrow{{font-size:9px;letter-spacing:3px;color:#2e2e46;text-transform:uppercase;margin-bottom:6px;}}
.brand{{font-size:clamp(22px,4vw,28px);font-weight:800;color:#f8fafc;letter-spacing:-0.5px;}}
.brand em{{color:#7c3aed;font-style:normal;}}
.dateline{{font-size:11px;color:#2e2e46;margin-top:4px;}}
.stats{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;}}
.stat{{background:#0d0d17;border:1px solid #1a1a2a;border-radius:6px;padding:6px 12px;min-width:80px;}}
.stat strong{{font-size:clamp(16px,3vw,20px);font-weight:800;color:#e2e8f0;display:block;line-height:1.2;}}
.stat span{{font-size:10px;color:#2e2e46;}}

/* ── Section ── */
.section{{margin-bottom:28px;}}
.sec-title{{font-size:9px;letter-spacing:3px;color:#2e2e46;text-transform:uppercase;
  margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #1a1a2a;}}

/* ── Signal card ── */
.card{{border-radius:10px;padding:14px 16px;margin-bottom:10px;border:1px solid #1a1a2a;}}
.giant-badges{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px;}}
.giant-badge{{font-size:9px;font-weight:700;letter-spacing:0.5px;padding:1px 7px;border-radius:3px;border:1px solid;background:transparent;}}
.pred-links-block{{margin:10px 0;padding:8px 10px;background:#0d0d17;border-radius:5px;border-left:2px solid #7c3aed;}}
.pred-links-label{{font-size:8px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#7c3aed;display:block;margin-bottom:4px;}}
.pred-link{{font-size:11px;color:#4b5563;margin-top:3px;}}
.sig-title{{font-size:clamp(14px,2.5vw,16px);font-weight:700;color:#f1f5f9;margin-bottom:8px;line-height:1.3;}}
.sig-title a{{color:#f1f5f9;text-decoration:underline;text-decoration-color:#ffffff18;text-underline-offset:3px;}}
.sig-title a:hover{{color:#a78bfa;text-decoration-color:#a78bfa;}}
.ext{{font-size:11px;color:#2e2e46;}}
.explanation{{color:#7a8799;font-size:clamp(12px,2vw,13px);margin-bottom:10px;line-height:1.6;}}
.entity{{color:#a78bfa;font-weight:600;}}
.num{{color:#34d399;font-weight:700;}}
.why-block{{margin:10px 0;}}
.why-heading{{font-size:8px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
  color:{WHY_COLOR};display:block;margin-bottom:4px;}}
.why-text{{font-size:12px;color:#4b5563;line-height:1.55;}}
.prediction{{font-size:12px;color:#374151;font-style:italic;
  margin-top:10px;padding-top:10px;border-top:1px solid #1a1a2a;}}

/* ── Predictions accordion ── */
.pred-row{{border-bottom:1px solid #12121e;}}
.pred-summary{{
  display:flex;align-items:center;gap:8px;
  padding:8px 4px;cursor:pointer;list-style:none;user-select:none;
}}
.pred-summary::-webkit-details-marker{{display:none;}}
.pred-status{{font-size:9px;font-weight:800;letter-spacing:1px;flex-shrink:0;width:90px;}}
.pred-text{{font-size:12px;color:#4b5563;flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}}
.pred-body{{padding:6px 0 10px 24px;}}
.pred-full{{font-size:13px;color:#8892a4;line-height:1.5;}}
.pred-note{{font-size:12px;color:#4b5563;margin-top:4px;}}
.pred-meta{{font-size:10px;color:#2e2e46;margin-top:4px;}}

/* ── Company watch accordion ── */
.wcat-header{{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#2e2e46;
  padding:12px 0 5px;border-bottom:1px solid #1a1a2a;margin-bottom:1px;font-weight:700;}}
.wrow{{border-bottom:1px solid #0f0f18;}}
.wrow-summary{{
  display:flex;align-items:center;gap:7px;
  padding:7px 4px;cursor:pointer;list-style:none;user-select:none;
}}
.wrow-summary::-webkit-details-marker{{display:none;}}
.wrow-summary:hover .wname{{color:#e2e8f0 !important;}}
.wdot{{width:6px;height:6px;border-radius:50%;flex-shrink:0;background:transparent;}}
.wname{{font-size:12px;flex-shrink:0;min-width:110px;}}
.wcat{{font-size:10px;color:#1e1e2e;flex:1;}}
.wref{{font-size:9px;color:#7c3aed;margin-left:auto;flex-shrink:0;}}
.wchev{{font-size:12px;color:#2e2e46;flex-shrink:0;transition:transform 0.12s;}}
details[open] .wchev{{transform:rotate(90deg);}}
.wrow-body{{padding:4px 0 10px 20px;}}
.wlinks{{list-style:none;}}
.wlinks li{{padding:2px 0;border-bottom:1px solid #0a0a12;}}
.wlinks li:last-child{{border-bottom:none;}}
.wlink{{font-size:11px;color:#475569;text-decoration:none;display:block;line-height:1.4;}}
.wlink:hover{{color:#a78bfa;}}
.wno-data{{font-size:10px;color:#1e1e2e;}}

/* ── Question ── */
.q-box{{
  background:#0d0d17;border:1px solid #2d1b69;
  border-left:3px solid #7c3aed;border-radius:0 8px 8px 0;
  padding:14px 18px;font-size:clamp(13px,2.2vw,15px);font-style:italic;
  color:#a78bfa;line-height:1.6;
}}

/* ── Footer ── */
.footer{{margin-top:32px;padding-top:16px;border-top:1px solid #1a1a2a;
  font-size:10px;color:#1a1a2a;text-align:center;letter-spacing:0.5px;}}

/* ── Mobile ── */
@media(max-width:480px){{
  body{{padding:12px 10px 40px;}}
  .stats{{gap:6px;}}
  .stat{{padding:5px 10px;min-width:70px;}}
  .card{{padding:12px;}}
  .wname{{min-width:90px;}}
  .pred-status{{width:75px;font-size:8px;}}
}}
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
    <div class="stat"><strong>{len(GIANT_WATCH)}</strong><span>Tracked</span></div>
    <div class="stat"><strong>{len(callbacks)}</strong><span>Resolved</span></div>
  </div>
</div>

<section class="section">
  <h3 class="sec-title">Top Signals</h3>
  {cards_html}
</section>

{preds_html}

<section class="section">
  <h3 class="sec-title">Company Watch · {len(GIANT_WATCH)} companies</h3>
  {watch_html}
</section>

<section class="section">
  <h3 class="sec-title">Question to sit with</h3>
  <div class="q-box">{_h(question)}</div>
</section>

<div class="footer">tech-intel · {now_str}</div>
</body>
</html>"""
