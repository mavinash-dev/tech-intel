import json
import os
import ollama
from datetime import datetime
from db.connection import get_connection
from config import OLLAMA_MODEL, OLLAMA_HOST, BRIEFING_STYLE
from briefing.html_formatter import generate_html

TOP_SIGNALS_LIMIT = 8
SINCE_HOURS = 1.5
BRIEFING_DIR = "briefings"


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
        """SELECT id, briefing_date, prediction_text, domain
           FROM predictions WHERE status = 'watching'
           ORDER BY made_at DESC LIMIT 10"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _resolve_predictions(watching: list, signals: list) -> list:
    if not watching or not signals:
        return []
    signals_summary = "\n".join(
        f"- [{s['domain']}] {s['title']}: {s['plain_explanation'][:200]}" for s in signals
    )
    predictions_block = "\n".join(
        f"[ID:{p['id']} | {p['briefing_date']}] {p['prediction_text']}" for p in watching
    )
    raw = _ollama(
        f"Today's signals:\n{signals_summary}\n\nWatching predictions:\n{predictions_block}\n\n"
        'For each prediction: confirmed / wrong / still_watching. '
        'JSON only: [{"id": <int>, "status": "...", "note": "<one sentence>"}]',
        system="Return only valid JSON array. No preamble.",
    )
    try:
        return [
            {**r,
             "emoji": {"confirmed": "✅", "wrong": "❌"}.get(r.get("status", ""), "⏳"),
             "prediction_text": next((p["prediction_text"] for p in watching if p["id"] == r["id"]), "")}
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
                "UPDATE predictions SET status=?, resolved_at=datetime('now'), resolution_note=? WHERE id=?",
                (r["status"], r["note"], r["id"]),
            )
    conn.commit()
    conn.close()


def _why_it_matters(title: str, explanation: str, domain: str) -> str:
    raw = _ollama(
        f"Signal: {title}\nDomain: {domain}\nExplanation: {explanation}\n\n"
        "2 sentences explaining why this matters to someone new to the tech ecosystem. "
        "Start directly with 'Why it matters:' — no preamble.",
        system="Output only the explanation starting with 'Why it matters:'. No preamble.",
    )
    for line in raw.splitlines():
        if line.strip().lower().startswith("why it matters"):
            return line.strip()
    return raw.strip()


def _generate_question(signals: list) -> str:
    summary = "\n".join(f"- [{s['domain']}] {s['title']}" for s in signals)
    return _ollama(
        f"Signals:\n{summary}\n\n"
        "One sharp strategic question across these signals. "
        "About how power, money, or technology is shifting. One sentence. No preamble.",
    )


def generate_briefing() -> str:
    """Generate HTML briefing, save to file, return file path."""
    os.makedirs(BRIEFING_DIR, exist_ok=True)

    signals = _load_top_signals()
    if not signals:
        # Return a minimal HTML file
        now_str = datetime.now().strftime("%d %b %Y %H:%M")
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{{background:#0a0a0f;color:#6b7280;font-family:sans-serif;
        padding:40px;text-align:center;}}</style></head>
        <body><h2 style="color:#e2e8f0">Tech Intel · {now_str}</h2>
        <p>No new signals in the last 90 minutes.<br>
        Run <code>python daemon.py</code> to start ingestion.</p></body></html>"""
        path = os.path.join(BRIEFING_DIR, f"briefing_{datetime.now().strftime('%Y%m%d_%H%M')}.html")
        with open(path, "w") as f:
            f.write(html)
        return path

    watching = _load_watching_predictions()
    resolutions = _resolve_predictions(watching, signals)
    _apply_resolutions(resolutions)

    # Generate "why it matters" for each signal
    why_map = {}
    if BRIEFING_STYLE != "professional":
        for s in signals:
            why_map[s["id"]] = _why_it_matters(s["title"], s["plain_explanation"], s["domain"])

    question = _generate_question(signals)

    conn = get_connection()
    total_ingested = conn.execute(
        "SELECT COUNT(*) FROM signals_raw WHERE ingested_at >= datetime('now', '-24 hours')"
    ).fetchone()[0]
    conn.close()

    html = generate_html(
        signals=signals,
        why_map=why_map,
        question=question,
        callbacks=resolutions,
        total_ingested=total_ingested,
    )

    filename = f"briefing_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    path = os.path.join(BRIEFING_DIR, filename)
    with open(path, "w") as f:
        f.write(html)

    print(f"[briefing] saved to {path}")
    return path
