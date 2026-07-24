import json
import ollama
from config import OLLAMA_MODEL, OLLAMA_HOST
from db.connection import get_connection

SYSTEM_PROMPT = """You are a signal intelligence analyst. You classify tech signals for someone new to the ecosystem who needs plain-language explanations.

Return ONLY valid JSON matching this exact schema:
{
  "domain": "<one of: Capital | Talent | Technology | Power | Infrastructure | Narrative>",
  "relevance_score": <float 0.0-1.0>,
  "plain_explanation": "<2-4 sentences. Explain what happened, who the key players are, and why it matters. Define any jargon. No assumed knowledge.>",
  "entities": [
    {"name": "<canonical entity name>", "type": "<Company | Person | Technology | Country | Organization>"}
  ],
  "prediction": "<one specific, falsifiable forward-looking prediction with a timeframe. Or empty string if nothing meaningful to predict.>"
}

Domain definitions:
- Capital: investments, acquisitions, funding rounds, valuations, IPOs, bankruptcies
- Talent: hiring, layoffs, executive moves, team formations, departures
- Technology: product launches, model releases, open source, research breakthroughs, APIs
- Power: regulation, government policy, antitrust, geopolitics, legislation, sanctions
- Infrastructure: data centres, chips, semiconductors, energy, physical layer, cloud capacity
- Narrative: media framing, public opinion, PR moves, industry discourse, analyst reports

Relevance score guide:
- 0.9+: Major shift — affects multiple companies/countries, long-term consequences
- 0.7-0.9: Significant signal — one major company or policy, clear consequence
- 0.5-0.7: Moderate — noteworthy but contained
- 0.3-0.5: Low — minor update, niche interest
- <0.3: Noise — skip-worthy"""

USER_PROMPT_TEMPLATE = """Classify this signal:

Title: {title}
Source: {source}
Body: {body}
URL: {url}"""


def classify_signal(raw_id: int, title: str, source: str, body: str, url: str) -> dict | None:
    prompt = USER_PROMPT_TEMPLATE.format(
        title=title,
        source=source,
        body=body or "(no body)",
        url=url or "(no url)",
    )
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            format="json",
        )
        result = json.loads(response["message"]["content"])
        return result
    except Exception as e:
        print(f"[classifier] Ollama error for raw_id={raw_id}: {e}")
        return None


def run_classification_batch(batch_size: int = 20):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, title, source, body, url FROM signals_raw
           WHERE processed = FALSE
           ORDER BY ingested_at DESC
           LIMIT ?""",
        (batch_size,),
    ).fetchall()

    if not rows:
        print("[classifier] no unprocessed signals.")
        conn.close()
        return

    print(f"[classifier] classifying {len(rows)} signals...")
    classified = 0

    for row in rows:
        raw_id = row["id"]
        result = classify_signal(raw_id, row["title"], row["source"], row["body"] or "", row["url"] or "")

        if result is None:
            continue

        try:
            conn.execute(
                """INSERT INTO signals_enriched
                   (raw_id, domain, relevance_score, plain_explanation, entities_json, prediction)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    raw_id,
                    result.get("domain", "Narrative"),
                    float(result.get("relevance_score", 0.5)),
                    result.get("plain_explanation", ""),
                    json.dumps(result.get("entities", [])),
                    result.get("prediction", ""),
                ),
            )
            conn.execute(
                "UPDATE signals_raw SET processed = TRUE WHERE id = ?",
                (raw_id,),
            )

            prediction_text = result.get("prediction", "").strip()
            if prediction_text:
                enriched_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                entities = [e.get("name", "") for e in result.get("entities", [])]
                conn.execute(
                    """INSERT INTO predictions
                       (briefing_date, prediction_text, related_entities, domain, signal_id)
                       VALUES (date('now'), ?, ?, ?, ?)""",
                    (
                        prediction_text,
                        json.dumps(entities),
                        result.get("domain", "Narrative"),
                        enriched_id,
                    ),
                )
            classified += 1
        except Exception as e:
            print(f"[classifier] db write error for raw_id={raw_id}: {e}")

    conn.commit()
    conn.close()
    print(f"[classifier] done — {classified}/{len(rows)} classified.")
