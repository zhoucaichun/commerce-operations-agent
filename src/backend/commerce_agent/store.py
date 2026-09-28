"""In-memory, synthetic data store used by the first runnable MVP slice."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any


class InMemoryStore:
    """Thread-safe store; no production merchant system is contacted."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._tickets: dict[str, dict[str, Any]] = {}
        self._ticket_counter = 0
        self._metrics = {"chat_requests": 0, "tool_calls": 0, "handoffs": 0}

        self.products = [
            {
                "sku": "AC-65W",
                "name": "65W USB-C PD Charger",
                "category": "charger",
                "power_w": 65,
                "ports": ["USB-C"],
                "regions": ["CN", "US", "EU"],
                "stock": "simulated_available",
            },
            {
                "sku": "AC-100W",
                "name": "100W USB-C PD Charger",
                "category": "charger",
                "power_w": 100,
                "ports": ["USB-C"],
                "regions": ["CN", "US", "EU"],
                "stock": "simulated_available",
            },
            {
                "sku": "CB-C2C-2M",
                "name": "2m USB-C to USB-C Cable",
                "category": "cable",
                "power_w": 100,
                "ports": ["USB-C", "USB-C"],
                "regions": ["CN", "US", "EU"],
                "stock": "simulated_low",
            },
        ]
        self.policies = [
            {
                "policy_id": "return-cn-2026-01",
                "topic": "return",
                "region": "CN",
                "effective_from": "2026-01-01",
                "summary": "Synthetic policy: unopened accessories may be requested for return within 7 days.",
                "source": "simulated_policy_seed",
            },
            {
                "policy_id": "warranty-cn-2026-01",
                "topic": "warranty",
                "region": "CN",
                "effective_from": "2026-01-01",
                "summary": "Synthetic policy: eligible chargers and cables have a 12-month limited warranty.",
                "source": "simulated_policy_seed",
            },
        ]
        self.orders = {
            "ORD-10023": {
                "order_id": "ORD-10023",
                "identity_suffix": "4821",
                "status": "shipped",
                "sku": "AC-65W",
                "quantity": 1,
                "purchased_on": "2026-09-10",
                "shipment": {
                    "carrier": "Simulated Express",
                    "tracking_number": "SIM-TRK-10023",
                    "last_event": "Handed to local carrier",
                    "estimated_delivery": "2026-09-29",
                },
            }
        }

    def session(self, thread_id: str) -> dict[str, Any]:
        with self._lock:
            state = self._sessions.setdefault(
                thread_id,
                {"thread_id": thread_id, "messages": [], "slots": {}, "step_count": 0},
            )
            return deepcopy(state)

    def save_session(self, thread_id: str, state: dict[str, Any]) -> None:
        with self._lock:
            self._sessions[thread_id] = deepcopy(state)

    def create_ticket(self, idempotency_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            existing = self._tickets.get(idempotency_key)
            if existing is not None:
                return {**deepcopy(existing), "deduplicated": True}
            self._ticket_counter += 1
            ticket = {
                "ticket_id": f"SIM-TKT-{self._ticket_counter:04d}",
                "status": "simulated_open",
                "created_from": "commerce_agent_mvp",
                **deepcopy(payload),
            }
            self._tickets[idempotency_key] = ticket
            return {**deepcopy(ticket), "deduplicated": False}

    def increment(self, metric: str) -> None:
        with self._lock:
            if metric in self._metrics:
                self._metrics[metric] += 1

    def metrics(self) -> dict[str, int]:
        with self._lock:
            return dict(self._metrics)
