import json
from groq import Groq
from config import GROK_API_KEY, GROQ_MODEL
from db.connection import get_connection

BATCH_SIZE = 5

SYSTEM_PROMPT = """You are a signal intelligence analyst classifying tech signals for someone new to the ecosystem.

Return ONLY a valid JSON array with one object per signal, in the same order as the input.

Each object must have exactly these keys:
  "domain": one of Capital | Talent | Technology | Power | Infrastructure | Narrative | Security
  "relevance_score": float 0.0-1.0 (IT sector relevance)
  "plain_explanation": 2-4 sentences in plain language — what happened, who the players are, why it matters. Define jargon.
  "entities": array of {"name": "<canonical name>", "type": "<Company|Person|Technology|Country|Organization>"}
  "prediction": one specific falsifiable forward-looking prediction with timeframe, or null

Domain definitions:
  Capital: investments, acquisitions, funding rounds, valuations, IPOs, bankruptcies
  Talent: hiring, layoffs, executive moves, team formations
  Technology: product launches, model releases, open source, research breakthroughs
  Power: regulation, government policy, antitrust, geopolitics, sanctions
  Infrastructure: data centres, chips, semiconductors, energy, cloud capacity
  Narrative: media framing, PR moves, industry discourse, analyst reports
  Security: breaches, vulnerabilities, CVEs, exploits, national security

Relevance score guide:
  0.9+: Major shift affecting multiple companies/countries
  0.7-0.9: Significant — one major company or policy with clear consequence
  0.5-0.7: Moderate — noteworthy but contained
  0.3-0.5: Low — minor update or niche interest
  <0.3: Noise"""


def _classify_batch(batch, batch_num):
    print(f"[groq] batch {batch_num}: sending {len(batch)} signals to {GROQ_MODEL}...", flush=True)
    client = Groq(api_key=GROK_API_KEY)
    lines = []
    for i, s in enumerate(batch, 1):
        body = (s.get("body") or "")[:400]
        lines.append(f"Signal {i}: {s['title']} — {body}")

    prompt = "\n".join(lines) + "\n\nReturn JSON array only. No preamble."

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        print(f"[groq] batch {batch_num}: got {len(result)} results.", flush=True)
        return result
    except Exception as e:
        print(f"[groq] batch {batch_num} error: {e}", flush=True)
        return None


def run_classification_batch(batch_size=30):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, title, source, body, url FROM signals_raw
           WHERE processed = FALSE
           ORDER BY ingested_at DESC
           LIMIT ?""",
        (batch_size,),
    ).fetchall()

    if not rows:
        print("[groq] no unprocessed signals.", flush=True)
        conn.close()
        return

    signals = [dict(r) for r in rows]
    print(f"[groq] classifying {len(signals)} signals in batches of {BATCH_SIZE}...", flush=True)
    classified = 0

    for i in range(0, len(signals), BATCH_SIZE):
        batch = signals[i: i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        results = _classify_batch(batch, batch_num)

        if results is None or len(results) != len(batch):
            print(f"[groq] batch {batch_num}: bad response, skipping {len(batch)} signals", flush=True)
            continue

        for signal, result in zip(batch, results):
            raw_id = signal["id"]
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
                        result.get("prediction") or "",
                    ),
                )
                conn.execute("UPDATE signals_raw SET processed = TRUE WHERE id = ?", (raw_id,))

                prediction_text = (result.get("prediction") or "").strip()
                if prediction_text:
                    enriched_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    entities = [e.get("name", "") for e in result.get("entities", [])]
                    conn.execute(
                        """INSERT INTO predictions
                           (briefing_date, prediction_text, related_entities, domain, signal_id)
                           VALUES (date('now'), ?, ?, ?, ?)""",
                        (prediction_text, json.dumps(entities), result.get("domain", "Narrative"), enriched_id),
                    )
                classified += 1
            except Exception as e:
                print(f"[groq] db write error for raw_id={raw_id}: {e}", flush=True)

    conn.commit()
    conn.close()
    print(f"[groq] done — {classified}/{len(signals)} classified.", flush=True)
