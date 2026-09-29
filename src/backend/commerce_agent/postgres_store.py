"""PostgreSQL-backed operational store for synthetic Commerce Agent state."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .store import InMemoryStore


class PostgresStore(InMemoryStore):
    def __init__(self, dsn: str) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required when COMMERCE_POSTGRES_DSN is set") from exc
        super().__init__()
        self.connection = psycopg.connect(dsn, autocommit=True)
        migration = Path(__file__).parents[1] / "migrations" / "002_postgres_state.sql"
        self.connection.execute(migration.read_text(encoding="utf-8"))
        self.products = [row[0] for row in self.connection.execute("SELECT payload FROM commerce_products ORDER BY sku")]
        self.policies = [row[0] for row in self.connection.execute("SELECT payload FROM commerce_policies ORDER BY policy_id")]
        self.orders = {row[0]: row[1] for row in self.connection.execute("SELECT order_id,payload FROM commerce_orders")}

    def session(self, thread_id: str) -> dict[str, Any]:
        row = self.connection.execute("SELECT payload FROM commerce_sessions WHERE thread_id = %s", (thread_id,)).fetchone()
        return row[0] if row else {"thread_id": thread_id, "messages": [], "slots": {}, "step_count": 0}

    def save_session(self, thread_id: str, state: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO commerce_sessions(thread_id,payload) VALUES(%s,%s) ON CONFLICT(thread_id) DO UPDATE SET payload=EXCLUDED.payload",
            (thread_id, json.dumps(state)),
        )

    def create_ticket(self, idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.connection.execute("SELECT payload FROM commerce_tickets WHERE idempotency_key=%s", (idempotency_key,)).fetchone()
        if row:
            return {**row[0], "deduplicated": True}
        count = self.connection.execute("SELECT COUNT(*) FROM commerce_tickets").fetchone()[0]
        ticket = {"ticket_id": f"SIM-TKT-{count + 1:04d}", "status": "simulated_open", "created_from": "commerce_agent_mvp", **deepcopy(payload)}
        self.connection.execute("INSERT INTO commerce_tickets(idempotency_key,payload) VALUES(%s,%s)", (idempotency_key, json.dumps(ticket)))
        return {**ticket, "deduplicated": False}

    def increment(self, metric: str) -> None:
        super().increment(metric)
        if metric in self._metrics:
            self.connection.execute("INSERT INTO commerce_metrics(name,value) VALUES(%s,1) ON CONFLICT(name) DO UPDATE SET value=commerce_metrics.value+1", (metric,))

    def snapshot_metrics(self) -> None:
        bucket = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for name, value in self.metrics().items():
            self.connection.execute(
                "INSERT INTO commerce_metric_snapshots(bucket,name,value) VALUES(%s,%s,%s) ON CONFLICT(bucket,name) DO UPDATE SET value=EXCLUDED.value",
                (bucket, name, value),
            )

    def metric_snapshots(self, limit: int = 24) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT bucket, name, value FROM commerce_metric_snapshots WHERE bucket IN (SELECT DISTINCT bucket FROM commerce_metric_snapshots ORDER BY bucket DESC LIMIT %s) ORDER BY bucket",
            (limit,),
        ).fetchall()
        snapshots: dict[str, dict[str, Any]] = {}
        for bucket, name, value in rows:
            key = bucket.isoformat()
            snapshots.setdefault(key, {"bucket": key})[name] = int(value)
        return list(snapshots.values())

    def ready(self) -> bool:
        self.connection.execute("SELECT 1").fetchone()
        return True

    def close(self) -> None:
        self.connection.close()
