"""Allow-listed tools backed only by synthetic local data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .store import InMemoryStore


class ToolError(ValueError):
    """A safe, user-visible tool failure."""


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    read_only: bool
    requires_idempotency: bool
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store
        self._tools = {
            "product_search": ToolDefinition(
                "product_search",
                "Search synthetic product catalog and simulated availability.",
                True,
                False,
                self._product_search,
            ),
            "compatibility_check": ToolDefinition(
                "compatibility_check",
                "Evaluate a deterministic compatibility rule for a product and device.",
                True,
                False,
                self._compatibility_check,
            ),
            "policy_search": ToolDefinition(
                "policy_search",
                "Find synthetic policy records by topic and region.",
                True,
                False,
                self._policy_search,
            ),
            "order_shipment_lookup": ToolDefinition(
                "order_shipment_lookup",
                "Look up a synthetic order only after order and identity suffix validation.",
                True,
                False,
                self._order_shipment_lookup,
            ),
            "create_simulated_ticket": ToolDefinition(
                "create_simulated_ticket",
                "Create a local simulated support ticket; never calls a real ticket system.",
                False,
                True,
                self._create_simulated_ticket,
            ),
        }

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def invoke(
        self, name: str, arguments: dict[str, Any], *, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        definition = self._tools.get(name)
        if definition is None:
            raise ToolError("tool is not allow-listed")
        if not isinstance(arguments, dict):
            raise ToolError("tool arguments must be an object")
        if definition.requires_idempotency and not idempotency_key:
            raise ToolError("idempotency_key is required for simulated writes")
        self.store.increment("tool_calls")
        self.store.increment(f"tool:{name}")
        if definition.requires_idempotency:
            arguments = {**arguments, "idempotency_key": idempotency_key}
        return definition.handler(arguments)

    def _product_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        if not query:
            raise ToolError("query is required")
        matches = []
        for product in self.store.products:
            haystack = " ".join(
                [product["sku"], product["name"], product["category"], " ".join(product["ports"])]
            ).lower()
            if query in haystack or query in {"充电器", "charger", "cable", "线材"}:
                matches.append(product)
        return {"query": query, "products": matches[:5], "data_source": "synthetic_catalog"}

    def _compatibility_check(self, arguments: dict[str, Any]) -> dict[str, Any]:
        sku = str(arguments.get("sku", "")).upper().strip()
        device = str(arguments.get("device", "")).strip()
        if not sku or not device:
            raise ToolError("sku and device are required")
        product = next((item for item in self.store.products if item["sku"] == sku), None)
        if product is None:
            return {
                "sku": sku,
                "device": device,
                "compatible": False,
                "reason": "sku_not_found_in_synthetic_catalog",
                "rule_version": "compat-v1",
            }
        device_lower = device.lower()
        needs_usb_c = any(token in device_lower for token in ("macbook", "ipad", "usb-c", "usb c"))
        compatible = product["power_w"] >= 65 and "USB-C" in product["ports"] and needs_usb_c
        return {
            "sku": sku,
            "device": device,
            "compatible": compatible,
            "reason": "power_and_port_rule_passed" if compatible else "power_or_port_rule_not_satisfied",
            "rule_version": "compat-v1",
        }

    def _policy_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        topic = str(arguments.get("topic", "")).strip().lower()
        region = str(arguments.get("region", "CN")).strip().upper()
        if not topic:
            raise ToolError("topic is required")
        matches = [
            policy
            for policy in self.store.policies
            if policy["topic"] == topic and policy["region"] == region
        ]
        return {"topic": topic, "region": region, "policies": matches, "data_source": "synthetic_policy_seed"}

    def _order_shipment_lookup(self, arguments: dict[str, Any]) -> dict[str, Any]:
        order_id = str(arguments.get("order_id", "")).strip().upper()
        identity_suffix = str(arguments.get("identity_suffix", "")).strip()
        if not order_id or not identity_suffix:
            raise ToolError("order_id and identity_suffix are required")
        order = self.store.orders.get(order_id)
        if order is None or order["identity_suffix"] != identity_suffix:
            return {"found": False, "reason": "order_or_identity_not_verified"}
        safe_order = {key: value for key, value in order.items() if key != "identity_suffix"}
        return {"found": True, "order": safe_order, "data_source": "synthetic_order_seed"}

    def _create_simulated_ticket(self, arguments: dict[str, Any]) -> dict[str, Any]:
        idempotency_key = str(arguments.pop("idempotency_key"))
        summary = str(arguments.get("summary", "")).strip()
        if not summary:
            raise ToolError("summary is required")
        return self.store.create_ticket(
            idempotency_key,
            {
                "category": str(arguments.get("category", "general")),
                "summary": summary[:500],
                "evidence": arguments.get("evidence", []),
            },
        )
