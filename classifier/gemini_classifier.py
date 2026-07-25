import json
import time
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from db.connection import get_connection

_client = genai.Client(api_key=GEMINI_API_KEY)

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


def _classify_batch(batch: list[dict]) -> list[dict] | None:
    """Send up to BATCH_SIZE signals to Gemini, return list of classification dicts."""
    lines = []
    for i, s in enumerate(batch, 1):
        body = (s.get("body") or "")[:400]
        lines.append(f"Signal {i}: {s['title']} — {body}")

    prompt = SYSTEM_PROMPT + "\n\n" + "\n".join(lines) + "\n\nReturn JSON array only. No preamble."

    for attempt in range(3):
        try:
            resp = _client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            text = resp.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                wait = 15 * (attempt + 1)  # 15s, 30s, 45s
                print(f"[gemini] rate limited, waiting {wait}s (attempt {attempt+1}/3)...")
                time.sleep(wait)
            else:
                print(f"[gemini] batch classify error: {e}")
                return None
    print("[gemini] batch failed after 3 retries (rate limit)")
    return None


def run_classification_batch(batch_size: int = 30):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, title, source, body, url FROM signals_raw
           WHERE processed = FALSE
           ORDER BY ingested_at DESC
           LIMIT ?""",
        (batch_size,),
    ).fetchall()

    if not rows:
        print("[gemini] no unprocessed signals.")
        conn.close()
        return

    signals = [dict(r) for r in rows]
    print(f"[gemini] classifying {len(signals)} signals in batches of {BATCH_SIZE}...")
    classified = 0

    for i in range(0, len(signals), BATCH_SIZE):
        batch = signals[i : i + BATCH_SIZE]
        results = _classify_batch(batch)

        if results is None or len(results) != len(batch):
            print(f"[gemini] batch {i//BATCH_SIZE + 1}: bad response, skipping {len(batch)} signals")
            time.sleep(5)
            continue

        for signal, result in zip(batch, results):
            raw_id = signal["id"]
            try:
                cursor = conn.execute(
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
                print(f"[gemini] db write error for raw_id={raw_id}: {e}")

        time.sleep(4)  # ~15 req/min free tier limit — 4s gap keeps us safely under

    conn.commit()
    conn.close()
    print(f"[gemini] done — {classified}/{len(signals)} classified.")
