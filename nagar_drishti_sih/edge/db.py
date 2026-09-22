from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Iterable
from .schemas import Event


class EdgeQueue:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init(self):
        with self._conn() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    retries INTEGER NOT NULL DEFAULT 0,
                    next_retry_at REAL,
                    created_at REAL NOT NULL DEFAULT (strftime('%s','now')),
                    last_error TEXT
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")

    def put(self, event: Event) -> None:
        payload = event.model_dump_json()
        with self._conn() as con:
            con.execute(
                "INSERT OR IGNORE INTO events(event_id,payload,status) VALUES(?,?, 'pending')",
                (event.event_id, payload),
            )

    def pending(self, limit: int = 25) -> list[Event]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM events WHERE status='pending' ORDER BY created_at LIMIT ?",
                (limit,),
            ).fetchall()
        return [Event.model_validate_json(r[0]) for r in rows]

    def ack(self, event_id: str) -> None:
        with self._conn() as con:
            con.execute("DELETE FROM events WHERE event_id=?", (event_id,))

    def fail(self, event_id: str, error: str, retry_at: float) -> None:
        with self._conn() as con:
            con.execute(
                "UPDATE events SET retries=retries+1,last_error=?,next_retry_at=? WHERE event_id=?",
                (error[:1000], retry_at, event_id),
            )

    def stats(self) -> dict:
        with self._conn() as con:
            row = con.execute(
                "SELECT COUNT(*), COALESCE(SUM(retries),0) FROM events WHERE status='pending'"
            ).fetchone()
        return {"pending": row[0], "total_retries": row[1]}
