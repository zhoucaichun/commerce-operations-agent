"""Synthetic B2B tenant registry used only by the product demonstration."""

from __future__ import annotations

from typing import Any, Callable

from .agent import CommerceAgent
from .sqlite_store import SQLiteStore


DEMO_MERCHANTS: dict[str, dict[str, Any]] = {
    "demo-3c-store": {
        "merchant_id": "demo-3c-store",
        "name": "NovaGear 3C",
        "widget_title": "NovaGear Assistant",
        "origin": "https://novagear.example.test",
        "roles": ["support", "operator", "merchant_admin"],
    },
    "orbit-tech-store": {
        "merchant_id": "orbit-tech-store",
        "name": "Orbit Tech Store",
        "widget_title": "Orbit Support",
        "origin": "https://orbit.example.test",
        "roles": ["support", "operator", "merchant_admin"],
    },
}


class DemoTenantRegistry:
    """Keeps demo tenants in separate local stores to make isolation observable."""

    def __init__(self, graph_factory: Callable[[CommerceAgent], Any]) -> None:
        self._graph_factory = graph_factory
        self._agents = {merchant_id: self._build_agent(merchant_id) for merchant_id in DEMO_MERCHANTS}
        self._graphs = {merchant_id: graph_factory(agent) for merchant_id, agent in self._agents.items()}

    def _build_agent(self, merchant_id: str) -> CommerceAgent:
        store = SQLiteStore(":memory:")
        if merchant_id == "orbit-tech-store":
            store.products[0]["name"] = "Orbit 65W USB-C Charger"
            store.products[0]["sku"] = "ORBIT-65W"
            store.orders = {
                "ORB-20001": {
                    "order_id": "ORB-20001", "identity_suffix": "9052", "status": "processing",
                    "sku": "ORBIT-65W", "quantity": 1, "purchased_on": "2026-09-18",
                    "shipment": {"carrier": "Orbit Parcel", "tracking_number": "ORB-TRK-20001", "last_event": "Label created", "estimated_delivery": "2026-10-03"},
                }
            }
        return CommerceAgent(store)

    def merchant(self, merchant_id: str) -> dict[str, Any]:
        merchant = DEMO_MERCHANTS.get(merchant_id)
        if merchant is None:
            raise KeyError(merchant_id)
        return dict(merchant)

    def agent(self, merchant_id: str) -> CommerceAgent:
        self.merchant(merchant_id)
        return self._agents[merchant_id]

    def graph(self, merchant_id: str) -> Any:
        self.merchant(merchant_id)
        return self._graphs[merchant_id]

    def overview(self, merchant_id: str) -> dict[str, Any]:
        merchant = self.merchant(merchant_id)
        store = self.agent(merchant_id).store
        metrics = store.metrics()
        chats = metrics["chat_requests"]
        return {
            "merchant": merchant,
            "tickets": store.list_tickets(),
            "metrics": {**metrics, "handoff_rate": round(metrics["handoffs"] / chats, 4) if chats else 0},
            "recent_handoffs": store.recent_handoffs(),
            "connector_status": "simulated_only",
            "widget_snippet": f'<script src="https://widget.example.test/commerce.js" data-merchant-id="{merchant_id}"></script>',
        }
