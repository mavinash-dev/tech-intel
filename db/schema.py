from db.connection import get_connection


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals_raw (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT NOT NULL,
            source_id   TEXT NOT NULL,
            title       TEXT NOT NULL,
            url         TEXT,
            body        TEXT,
            published_at DATETIME,
            ingested_at  DATETIME DEFAULT (datetime('now')),
            processed    BOOLEAN DEFAULT FALSE,
            UNIQUE(source, source_id)
        );

        CREATE TABLE IF NOT EXISTS signals_enriched (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_id            INTEGER NOT NULL REFERENCES signals_raw(id),
            domain            TEXT NOT NULL,
            relevance_score   REAL NOT NULL,
            plain_explanation TEXT NOT NULL,
            entities_json     TEXT NOT NULL,
            prediction        TEXT,
            enriched_at       DATETIME DEFAULT (datetime('now')),
            last_shown_at     DATETIME
        );

        CREATE TABLE IF NOT EXISTS predictions (
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
        );

        CREATE INDEX IF NOT EXISTS idx_raw_processed ON signals_raw(processed);
        CREATE INDEX IF NOT EXISTS idx_raw_source ON signals_raw(source, source_id);
        CREATE INDEX IF NOT EXISTS idx_enriched_domain ON signals_enriched(domain);
        CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status);
    """)
    conn.commit()
    # Migrate: add last_shown_at if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE signals_enriched ADD COLUMN last_shown_at DATETIME")
        conn.commit()
    except Exception:
        pass
    conn.close()
    print("[db] Schema initialised.")


if __name__ == "__main__":
    init_db()
