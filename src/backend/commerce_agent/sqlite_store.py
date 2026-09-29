"""SQLite-backed operational state for the local, synthetic MVP."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any

from .store import InMemoryStore


class SQLiteStore(InMemoryStore):
    """Persists sessions, simulated tickets, and metrics without external services."""

    def __init__(self, database_path: str = ":memory:") -> None:
        super().__init__()
        self.database_path = database_path
        self._db_lock = RLock()
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._migrate()
        self._load_metrics()

    def _migrate(self) -> None:
        migration = Path(__file__).parents[1] / "migrations" / "001_initial.sql"
        with self._db_lock:
            self._connection.executescript(migration.read_text(encoding="utf-8"))
            self._connection.commit()

    def _load_metrics(self) -> None:
        with self._db_lock:
            rows = self._connection.execute("SELECT name, value FROM metrics").fetchall()
        for row in rows:
            self._metrics[row["name"]] = int(row["value"])

    def session(self, thread_id: str) -> dict[str, Any]:
        with self._db_lock:
            row = self._connection.execute("SELECT payload FROM sessions WHERE thread_id = ?", (thread_id,)).fetchone()
        if row is None:
            return {"thread_id": thread_id, "messages": [], "slots": {}, "step_count": 0}
        return json.loads(row["payload"])

    def save_session(self, thread_id: str, state: dict[str, Any]) -> None:
        with self._db_lock:
            self._connection.execute(
                "INSERT INTO sessions(thread_id, payload) VALUES(?, ?) ON CONFLICT(thread_id) DO UPDATE SET payload = excluded.payload",
                (thread_id, json.dumps(state, ensure_ascii=False, separators=(",", ":"))),
            )
            self._connection.commit()

    def create_ticket(self, idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._db_lock:
            existing = self._connection.execute("SELECT payload FROM tickets WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
            if existing is not None:
                return {**json.loads(existing["payload"]), "deduplicated": True}
            count = self._connection.execute("SELECT COUNT(*) AS count FROM tickets").fetchone()["count"]
            ticket = {"ticket_id": f"SIM-TKT-{count + 1:04d}", "status": "simulated_open", "created_from": "commerce_agent_mvp", **deepcopy(payload)}
            self._connection.execute(
                "INSERT INTO tickets(idempotency_key, payload) VALUES(?, ?)",
                (idempotency_key, json.dumps(ticket, ensure_ascii=False, separators=(",", ":"))),
            )
            self._connection.commit()
        return {**ticket, "deduplicated": False}

    def increment(self, metric: str) -> None:
        super().increment(metric)
        if metric in self._metrics:
            with self._db_lock:
                self._connection.execute("INSERT INTO metrics(name, value) VALUES(?, 1) ON CONFLICT(name) DO UPDATE SET value = value + 1", (metric,))
                self._connection.commit()

    def snapshot_metrics(self) -> None:
        bucket = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat()
        with self._db_lock:
            self._connection.executemany(
                "INSERT INTO metric_snapshots(bucket, name, value) VALUES(?, ?, ?) ON CONFLICT(bucket, name) DO UPDATE SET value = excluded.value",
                [(bucket, name, value) for name, value in self.metrics().items()],
            )
            self._connection.commit()

    def metric_snapshots(self, limit: int = 24) -> list[dict[str, Any]]:
        with self._db_lock:
            rows = self._connection.execute(
                "SELECT bucket, name, value FROM metric_snapshots WHERE bucket IN (SELECT DISTINCT bucket FROM metric_snapshots ORDER BY bucket DESC LIMIT ?) ORDER BY bucket",
                (limit,),
            ).fetchall()
        snapshots: dict[str, dict[str, Any]] = {}
        for row in rows:
            snapshots.setdefault(row["bucket"], {"bucket": row["bucket"]})[row["name"]] = int(row["value"])
        return list(snapshots.values())

    def ready(self) -> bool:
        with self._db_lock:
            self._connection.execute("SELECT 1").fetchone()
        return True

    def close(self) -> None:
        with self._db_lock:
            self._connection.close()
