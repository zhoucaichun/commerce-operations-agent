"""PostgreSQL-backed operational store for synthetic Commerce Agent state."""

from __future__ import annotations

from copy import deepcopy
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

    def ready(self) -> bool:
        self.connection.execute("SELECT 1").fetchone()
        return True

    def close(self) -> None:
        self.connection.close()
