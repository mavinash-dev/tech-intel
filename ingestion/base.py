from abc import ABC, abstractmethod
from datetime import datetime
from db.connection import get_connection


class BaseIngester(ABC):
    source_name: str = ""

    @abstractmethod
    def fetch(self) -> list:
        """Return list of signal dicts matching signals_raw schema."""
        ...

    def save(self, signals: list[dict]) -> int:
        """Insert signals, skip duplicates. Returns count of new rows inserted."""
        if not signals:
            return 0

        conn = get_connection()
        inserted = 0
        for s in signals:
            try:
                conn.execute(
                    """INSERT INTO signals_raw
                       (source, source_id, title, url, body, published_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(source, source_id) DO NOTHING""",
                    (
                        s["source"],
                        s["source_id"],
                        s["title"],
                        s.get("url"),
                        s.get("body"),
                        s.get("published_at"),
                    ),
                )
                # Turso returns affected_row_count as int; sqlite3 returns changes() as int
                row = conn.execute("SELECT changes()").fetchone()
                if row and int(row[0]) > 0:
                    inserted += 1
            except Exception as e:
                print(f"[{self.source_name}] save error: {e}")
        conn.commit()
        conn.close()
        return inserted

    def run(self) -> int:
        print(f"[{self.source_name}] ingesting...")
        try:
            signals = self.fetch()
            count = self.save(signals)
            print(f"[{self.source_name}] {count} new signals saved ({len(signals)} fetched)")
            return count
        except Exception as e:
            print(f"[{self.source_name}] ingestion failed: {e}")
            return 0
