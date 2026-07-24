import json
import ollama
from datetime import date, datetime
from db.connection import get_connection
from config import OLLAMA_MODEL, OLLAMA_HOST, BRIEFING_STYLE

DOMAIN_EMOJI = {
    "Capital":        "💰",
    "Talent":         "👥",
    "Technology":     "🔬",
    "Power":          "⚡",
    "Infrastructure": "🏗️",
    "Narrative":      "📰",
}

GIANT_WATCH = [
    ("🍎", "Apple"),
    ("🔵", "Meta"),
    ("Ⓜ️", "Microsoft"),
    ("🔴", "Google"),
    ("🟠", "Amazon"),
    ("🟢", "Nvidia"),
    ("🔵", "OpenAI"),
    ("🤖", "Anthropic"),
    ("🚗", "Tesla"),
    ("🇨🇳", "Baidu"),
    ("💾", "TSMC"),
    ("📱", "Samsung"),
]

TOP_SIGNALS_LIMIT = 8
PREDICTION_BATCH_LIMIT = 10


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


def _load_top_signals(today: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT e.id, e.domain, e.relevance_score, e.plain_explanation,
                  e.entities_json, e.prediction, e.enriched_at,
                  r.title, r.url, r.source
           FROM signals_enriched e
           JOIN signals_raw r ON r.id = e.raw_id
           WHERE e.enriched_at >= datetime('now', '-24 hours')
           ORDER BY e.relevance_score DESC
           LIMIT ?""",
        (TOP_SIGNALS_LIMIT,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _load_watching_predictions() -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, briefing_date, prediction_text, related_entities, domain
           FROM predictions
           WHERE status = 'watching'
           ORDER BY made_at DESC
           LIMIT ?""",
        (PREDICTION_BATCH_LIMIT,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _resolve_predictions(watching: list, signals: list) -> list:
    """Ask Ollama whether today's signals confirm/contradict any watching predictions.
    Returns list of dicts with keys: id, status, note, emoji."""
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

    prompt = f"""Today's signals:
{signals_summary}

Watching predictions:
{predictions_block}

For each prediction, decide: confirmed / wrong / still_watching.
Return JSON array:
[{{"id": <int>, "status": "confirmed|wrong|still_watching", "note": "<one sentence on what happened or why still watching>"}}]
Only include predictions you can make a clear call on. Omit if truly uncertain."""

    raw = _ollama(prompt, system="You are a prediction resolution analyst. Return only valid JSON.")
    try:
        results = json.loads(raw)
        resolutions = []
        for r in results:
            emoji = {"confirmed": "✅", "wrong": "❌", "still_watching": "⏳"}.get(r.get("status", ""), "⏳")
            resolutions.append({
                "id": r["id"],
                "status": r.get("status", "still_watching"),
                "note": r.get("note", ""),
                "emoji": emoji,
            })
        return resolutions
    except Exception:
        return []


def _apply_prediction_resolutions(resolutions: list):
    if not resolutions:
        return
    conn = get_connection()
    for r in resolutions:
        if r["status"] in ("confirmed", "wrong"):
            conn.execute(
                """UPDATE predictions
                   SET status = ?, resolved_at = datetime('now'), resolution_note = ?
                   WHERE id = ?""",
                (r["status"], r["note"], r["id"]),
            )
    conn.commit()
    conn.close()


def _generate_question(signals: list) -> str:
    summary = "\n".join(f"- [{s['domain']}] {s['title']}" for s in signals)
    prompt = f"""Today's top signals:
{summary}

Write ONE sharp question that cuts across these signals — structural, strategic, worth sitting with.
Not a news question. A question about how power, money, or technology is shifting.
One sentence. No preamble."""
    return _ollama(prompt)


def _why_it_matters(title: str, explanation: str, domain: str) -> str:
    prompt = f"""Signal: {title}
Domain: {domain}
Explanation: {explanation}

Write 2-3 sentences starting with "Why it matters to you:" explaining why this signal is personally relevant
to someone new to the tech ecosystem who is building their understanding. Use "you" language. Be direct."""
    return _ollama(prompt)


def _giant_watch_line(emoji: str, company: str, signals: list, professional: bool) -> str:
    matching = [
        s for s in signals
        if company.lower() in s["title"].lower()
        or company.lower() in s.get("entities_json", "").lower()
    ]
    if matching:
        s = matching[0]
        ref = f"Signal #{signals.index(s) + 1} above" if not professional else s["title"][:60]
        return f"{emoji} {company} — {ref}."
    return f"{emoji} {company} — No major news today."


def generate_briefing() -> str:
    today = date.today().isoformat()
    day_str = datetime.now().strftime("%A, %d %b %Y")
    professional = (BRIEFING_STYLE == "professional")

    signals = _load_top_signals(today)
    if not signals:
        return f"Tech Intel — {day_str}\n\nNo signals ingested yet. Run the daemon first: python daemon.py"

    watching = _load_watching_predictions()
    resolutions = _resolve_predictions(watching, signals)
    _apply_prediction_resolutions(resolutions)

    question = _generate_question(signals)

    lines = []

    # Header
    if professional:
        lines.append(f"Tech Intel — {day_str}\n")
    else:
        lines.append(f"🧠 Tech Intel Briefing — {day_str}\n")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        confirmed = sum(1 for r in resolutions if r["status"] == "confirmed")
        new_preds = sum(1 for s in signals if s.get("prediction", "").strip())
        lines.append(
            f"TODAY'S PICTURE\n{len(signals)} signals · {len(resolutions)} history callbacks"
            f" · {confirmed} confirmed · {new_preds} new predictions\n"
        )

    # Prediction callbacks
    if resolutions or watching:
        sep = "---" if professional else "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        lines.append(sep)
        header = "CALLBACKS" if professional else "BEFORE YOU READ — WHAT WE CALLED"
        lines.append(f"\n{header}")

        resolved_ids = {r["id"] for r in resolutions}
        watching_map = {p["id"]: p for p in watching}

        for r in resolutions:
            p = watching_map.get(r["id"])
            if not p:
                continue
            lines.append(
                f"\n{r['emoji']} {r['status'].upper().replace('_',' ')} ({p['briefing_date']})\n"
                f"We said: {p['prediction_text']}\n"
                f"Today: {r['note']}"
            )

        still_watching = [p for p in watching if p["id"] not in resolved_ids]
        for p in still_watching[:3]:
            lines.append(
                f"\n⏳ WATCHING ({p['briefing_date']}) — {p['prediction_text'][:120]}"
            )

        if not professional:
            total = len(watching)
            lines.append(f"\nRunning prediction accuracy: tracking {total} predictions")

    # Signals
    sep = "---" if professional else "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for i, s in enumerate(signals, 1):
        lines.append(f"\n{sep}\n")
        emoji = DOMAIN_EMOJI.get(s["domain"], "📌")
        entities = [e.get("name", "") for e in json.loads(s.get("entities_json") or "[]")]

        if professional:
            lines.append(f"{emoji} {s['domain'].upper()} · #{i}")
            lines.append(s["title"])
            if s.get("url"):
                lines.append(s["url"])
            lines.append(f"\n{s['plain_explanation']}")
            if s.get("prediction", "").strip():
                lines.append(f"Prediction: {s['prediction']}")
            if entities:
                lines.append(f"Entities: {' · '.join(entities)}")
        else:
            lines.append(f"{emoji} {s['domain'].upper()} · Signal #{i}")
            lines.append(s["title"])
            if s.get("url"):
                lines.append(s["url"])
            lines.append(f"\nWhat this means:\n{s['plain_explanation']}")
            why = _why_it_matters(s["title"], s["plain_explanation"], s["domain"])
            if why:
                lines.append(f"\n{why}")
            if s.get("prediction", "").strip():
                lines.append(f"\nWhat we predict next:\n{s['prediction']}")
            if entities:
                lines.append(f"\nEntities: {' · '.join(entities)}")

    # Giant Watch
    lines.append(f"\n{sep}\n")
    watch_header = "GIANT WATCH" if professional else "GIANT WATCH\nCompanies we always track, regardless of whether they made the top signals today."
    lines.append(watch_header + "\n")
    for emoji, company in GIANT_WATCH:
        lines.append(_giant_watch_line(emoji, company, signals, professional))

    # One Question
    lines.append(f"\n{sep}\n")
    if professional:
        lines.append(question)
    else:
        lines.append(f"ONE QUESTION WORTH SITTING WITH\n{question}")

    # Footer
    conn = get_connection()
    total_today = conn.execute(
        "SELECT COUNT(*) FROM signals_raw WHERE ingested_at >= datetime('now', '-24 hours')"
    ).fetchone()[0]
    conn.close()

    lines.append(f"\n{sep}")
    lines.append(f"{total_today} ingested · {len(signals)} surfaced · Ollama ✓")

    return "\n".join(lines)
