import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection

TABLES = [
    """CREATE TABLE IF NOT EXISTS signals_raw (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        source       TEXT NOT NULL,
        source_id    TEXT NOT NULL,
        title        TEXT NOT NULL,
        url          TEXT,
        body         TEXT,
        published_at DATETIME,
        ingested_at  DATETIME DEFAULT (datetime('now')),
        processed    BOOLEAN DEFAULT FALSE,
        UNIQUE(source, source_id)
    )""",
    """CREATE TABLE IF NOT EXISTS signals_enriched (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_id            INTEGER NOT NULL REFERENCES signals_raw(id),
        domain            TEXT NOT NULL,
        relevance_score   REAL NOT NULL,
        plain_explanation TEXT NOT NULL,
        entities_json     TEXT NOT NULL,
        prediction        TEXT,
        enriched_at       DATETIME DEFAULT (datetime('now')),
        last_shown_at     DATETIME
    )""",
    """CREATE TABLE IF NOT EXISTS predictions (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        made_at          DATETIME DEFAULT (datetime('now')),
        briefing_date    DATE NOT NULL,
        prediction_text  TEXT NOT NULL,
        related_entities TEXT,
        domain           TEXT,
        status           TEXT DEFAULT 'watching',
        resolved_at      DATETIME,
        resolution_note  TEXT,
        signal_id        INTEGER REFERENCES signals_enriched(id)
    )""",
    """CREATE TABLE IF NOT EXISTS company_facts (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        company   TEXT NOT NULL,
        fact_type TEXT NOT NULL,
        value     TEXT NOT NULL,
        source    TEXT,
        as_of     DATE,
        seeded_at DATETIME DEFAULT (datetime('now'))
    )""",
    "CREATE INDEX IF NOT EXISTS idx_raw_processed ON signals_raw(processed)",
    "CREATE INDEX IF NOT EXISTS idx_raw_source ON signals_raw(source, source_id)",
    "CREATE INDEX IF NOT EXISTS idx_enriched_domain ON signals_enriched(domain)",
    "CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status)",
    "CREATE INDEX IF NOT EXISTS idx_facts_company ON company_facts(company)",
]


def init_db():
    conn = get_connection()
    for stmt in TABLES:
        try:
            conn.execute(stmt)
        except Exception as e:
            print(f"[db] skipped (already exists?): {e}")
    conn.commit()
    conn.close()
    print("[db] Schema initialised.")


if __name__ == "__main__":
    init_db()
