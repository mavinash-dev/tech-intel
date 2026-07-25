import sqlite3
import json
import requests as _requests
from config import DB_PATH, TURSO_DATABASE_URL, TURSO_AUTH_TOKEN


# ---------------------------------------------------------------------------
# Turso HTTP wrapper — mimics sqlite3.Connection interface
# ---------------------------------------------------------------------------

class _TursoRow(dict):
    """Dict subclass that also supports positional integer indexing."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _TursoCursor:
    def __init__(self, rows, lastrowid=None):
        self._rows = rows
        self.lastrowid = lastrowid

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


class TursoConnection:
    """Thin wrapper around Turso's /v2/pipeline HTTP API."""

    def __init__(self, url: str, token: str):
        self._url = url.rstrip("/") + "/v2/pipeline"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._pending = []  # buffered write statements for commit()

    def _execute_now(self, sql: str, params=()):
        """Execute a single statement immediately and return cursor."""
        args = [{"type": "text", "value": str(v)} if v is not None else {"type": "null"} for v in params]
        payload = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "positional_args": args}},
                {"type": "close"},
            ]
        }
        resp = _requests.post(self._url, headers=self._headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = data["results"][0]
        if result["type"] == "error":
            raise Exception(f"Turso error: {result['error']['message']}")

        exec_result = result["response"]["result"]
        cols = [c["name"] for c in exec_result["cols"]]
        rows = []
        for raw_row in exec_result["rows"]:
            values = [cell.get("value") if cell["type"] != "null" else None for cell in raw_row]
            rows.append(_TursoRow(zip(cols, values)))

        lastrowid = None
        if exec_result.get("last_insert_rowid"):
            lastrowid = int(exec_result["last_insert_rowid"])

        return _TursoCursor(rows, lastrowid=lastrowid)

    def execute(self, sql: str, params=()):
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT") or sql_upper.startswith("PRAGMA"):
            return self._execute_now(sql, params)
        # Buffer writes — they're flushed on commit()
        self._pending.append((sql, params))
        # Return a fake cursor with lastrowid support — we execute immediately too
        # so that last_insert_rowid() calls work
        return self._execute_now(sql, params)

    def commit(self):
        self._pending.clear()

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Public factory — returns sqlite3.Connection or TursoConnection
# ---------------------------------------------------------------------------

def get_connection():
    if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
        return TursoConnection(TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
