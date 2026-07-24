import json
import ollama
from datetime import datetime
from db.connection import get_connection
from config import OLLAMA_MODEL, OLLAMA_HOST, BRIEFING_STYLE

DOMAIN_LABEL = {
    "Capital":        "CAPITAL",
    "Talent":         "TALENT",
    "Technology":     "TECHNOLOGY",
    "Power":          "POWER",
    "Infrastructure": "INFRASTRUCTURE",
    "Narrative":      "NARRATIVE",
    "Security":       "SECURITY",
}

GIANT_WATCH = [
    "Apple", "Meta", "Microsoft", "Google", "Amazon",
    "Nvidia", "OpenAI", "Anthropic", "Tesla", "Baidu", "TSMC", "Samsung",
]

TOP_SIGNALS_LIMIT = 8
PREDICTION_BATCH_LIMIT = 10
SINCE_HOURS = 1.5


def _h(text: str) -> str:
    """Escape special HTML chars in user-generated text."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _ollama(prompt: str, system: str = "") -> str:
    client = ollama.Client(host=OLLAMA_HOST)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = client.chat(model=OLLAMA_MODEL, messages=messages)
        return resp["message"]["content"].strip()
    except Exception as e:
        print(f"[briefing] Ollama error: {e}")
        return ""


def _load_top_signals() -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT e.id, e.domain, e.relevance_score, e.plain_explanation,
                  e.entities_json, e.prediction, e.enriched_at,
                  r.title, r.url, r.source
           FROM signals_enriched e
           JOIN signals_raw r ON r.id = e.raw_id
           WHERE e.enriched_at >= datetime('now', ?)
           ORDER BY e.relevance_score DESC
           LIMIT ?""",
        (f"-{SINCE_HOURS} hours", TOP_SIGNALS_LIMIT),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _load_watching_predictions() -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, briefing_date, prediction_text, related_entities, domain
           FROM predictions WHERE status = 'watching'
           ORDER BY made_at DESC LIMIT ?""",
        (PREDICTION_BATCH_LIMIT,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _resolve_predictions(watching: list, signals: list) -> list:
    if not watching or not signals:
        return []
    signals_summary = "\n".join(
        f"- [{s['domain']}] {s['title']}: {s['plain_explanation'][:200]}"
        for s in signals
    )
    predictions_block = "\n".join(
        f"[ID:{p['id']} | {p['briefing_date']}] {p['prediction_text']}"
        for p in watching
    )
    prompt = f"""Today's signals:\n{signals_summary}\n\nWatching predictions:\n{predictions_block}

For each prediction decide: confirmed / wrong / still_watching.
Return JSON array: [{{"id": <int>, "status": "confirmed|wrong|still_watching", "note": "<one sentence>"}}]
Only include predictions you can make a clear call on."""
    raw = _ollama(prompt, system="You are a prediction resolution analyst. Return only valid JSON.")
    try:
        return [
            {**r, "emoji": {"confirmed": "✅", "wrong": "❌"}.get(r.get("status", ""), "⏳")}
            for r in json.loads(raw)
        ]
    except Exception:
        return []


def _apply_resolutions(resolutions: list):
    if not resolutions:
        return
    conn = get_connection()
    for r in resolutions:
        if r["status"] in ("confirmed", "wrong"):
            conn.execute(
                """UPDATE predictions SET status=?, resolved_at=datetime('now'), resolution_note=?
                   WHERE id=?""",
                (r["status"], r["note"], r["id"]),
            )
    conn.commit()
    conn.close()


def _generate_question(signals: list) -> str:
    summary = "\n".join(f"- [{s['domain']}] {s['title']}" for s in signals)
    return _ollama(
        f"Today's signals:\n{summary}\n\nOne sharp strategic question across these signals. "
        "Not a news question. About how power, money, or technology is shifting. One sentence, no preamble."
    )


def _why_it_matters(title: str, explanation: str, domain: str) -> str:
    raw = _ollama(
        f"Signal: {title}\nDomain: {domain}\nExplanation: {explanation}\n\n"
        "In exactly 2 sentences, explain why this matters to someone new to the tech ecosystem. "
        "Start your response directly with 'Why it matters:' — no preamble, no meta-commentary.",
        system="You are a plain-language explainer. Output only the explanation. Start with 'Why it matters:'",
    )
    # Strip any preamble lines Llama adds before the actual content
    for line in raw.splitlines():
        if line.strip().lower().startswith("why it matters"):
            return line.strip()
    return raw.strip()


def _format_signal_html(i: int, s: dict, beginner: bool) -> str:
    domain = DOMAIN_LABEL.get(s["domain"], s["domain"].upper())
    entities = [e.get("name", "") for e in json.loads(s.get("entities_json") or "[]")]
    title = _h(s["title"])
    explanation = _h(s["plain_explanation"])
    url = s.get("url", "")

    lines = []
    lines.append(f'<b>#{i} — {domain}</b>')
    if url:
        lines.append(f'<a href="{url}">{title}</a>')
    else:
        lines.append(f'<b>{title}</b>')

    lines.append("")
    lines.append(explanation)

    if beginner:
        why = _why_it_matters(s["title"], s["plain_explanation"], s["domain"])
        if why:
            lines.append("")
            lines.append(f"<i>{_h(why)}</i>")

    pred = (s.get("prediction") or "").strip()
    if pred:
        lines.append("")
        lines.append(f"<b>Prediction:</b> {_h(pred)}")

    if entities:
        lines.append("")
        lines.append(f"<i>Entities: {' · '.join(_h(e) for e in entities if e)}</i>")

    return "\n".join(lines)


def _format_giant_watch(signals: list) -> str:
    mentioned = []
    not_mentioned = []
    for company in GIANT_WATCH:
        found = next(
            (s for s in signals
             if company.lower() in s["title"].lower()
             or company.lower() in (s.get("entities_json") or "").lower()),
            None,
        )
        if found:
            idx = signals.index(found) + 1
            mentioned.append(f"<b>{company}</b> — see signal #{idx}")
        else:
            not_mentioned.append(company)

    lines = ["<b>COMPANY WATCH</b>"]
    lines.extend(mentioned)
    if not_mentioned:
        lines.append(f"No signals today: {', '.join(not_mentioned)}")
    return "\n".join(lines)


def generate_briefing() -> str:
    now_str = datetime.now().strftime("%d %b %Y, %H:%M")
    beginner = (BRIEFING_STYLE != "professional")

    signals = _load_top_signals()
    if not signals:
        return (
            f"<b>Tech Intel · {now_str}</b>\n\n"
            "No new signals in the last 90 minutes.\n"
            "Run <code>python daemon.py</code> to start ingestion."
        )

    watching = _load_watching_predictions()
    resolutions = _resolve_predictions(watching, signals)
    _apply_resolutions(resolutions)
    question = _generate_question(signals)

    parts = []

    # ── Header ────────────────────────────────────────────────────────
    parts.append(
        f"<b>Tech Intel · {now_str}</b>\n"
        f"{len(signals)} signals · Ollama ✓"
    )

    # ── Prediction callbacks ──────────────────────────────────────────
    if resolutions:
        resolved_ids = {r["id"] for r in resolutions}
        watch_map = {p["id"]: p for p in watching}
        callback_lines = ["<b>WHAT WE CALLED</b>"]
        for r in resolutions:
            p = watch_map.get(r["id"])
            if not p:
                continue
            callback_lines.append(
                f"{r['emoji']} <b>{r['status'].upper().replace('_',' ')}</b> ({p['briefing_date']})\n"
                f"We said: {_h(p['prediction_text'])}\n"
                f"Today: {_h(r['note'])}"
            )
        still = [p for p in watching if p["id"] not in resolved_ids]
        for p in still[:2]:
            callback_lines.append(f"⏳ Still watching ({p['briefing_date']}): {_h(p['prediction_text'][:100])}")
        parts.append("\n".join(callback_lines))

    # ── Signals ───────────────────────────────────────────────────────
    for i, s in enumerate(signals, 1):
        parts.append(_format_signal_html(i, s, beginner))

    # ── Company watch ─────────────────────────────────────────────────
    parts.append(_format_giant_watch(signals))

    # ── One question ──────────────────────────────────────────────────
    parts.append(f"<b>QUESTION TO SIT WITH</b>\n{_h(question)}")

    # ── Footer ────────────────────────────────────────────────────────
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) FROM signals_raw WHERE ingested_at >= datetime('now', '-24 hours')"
    ).fetchone()[0]
    conn.close()
    parts.append(f"<i>{total} signals ingested in last 24h · {len(signals)} surfaced</i>")

    return "\n\n——————————————————\n\n".join(parts)
