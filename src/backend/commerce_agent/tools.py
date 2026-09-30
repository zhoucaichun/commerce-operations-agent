"""Allow-listed tools backed only by repository-packaged synthetic data."""

from __future__ import annotations

from dataclasses import dataclass
import re
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
            "product_search": ToolDefinition("product_search", "Search the synthetic product catalogue.", True, False, self._product_search),
            "recommend_products": ToolDefinition("recommend_products", "Rank synthetic catalogue products using deterministic constraints.", True, False, self._recommend_products),
            "compatibility_check": ToolDefinition("compatibility_check", "Evaluate a deterministic compatibility rule.", True, False, self._compatibility_check),
            "policy_search": ToolDefinition("policy_search", "Find synthetic policy records by topic and region.", True, False, self._policy_search),
            "order_shipment_lookup": ToolDefinition("order_shipment_lookup", "Look up a verified synthetic order.", True, False, self._order_shipment_lookup),
            "create_simulated_ticket": ToolDefinition("create_simulated_ticket", "Create a local simulated support ticket.", False, True, self._create_simulated_ticket),
        }

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def invoke(self, name: str, arguments: dict[str, Any], *, idempotency_key: str | None = None) -> dict[str, Any]:
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

    @staticmethod
    def _haystack(product: dict[str, Any]) -> str:
        values = [product.get("sku", ""), product.get("name", ""), product.get("category", ""), product.get("brand", ""), product.get("device_compatibility", ""), product.get("search_aliases", ""), product.get("key_features", ""), " ".join(product.get("ports", [])), " ".join(product.get("usage_scenarios", []))]
        return " ".join(str(value) for value in values).lower()

    @staticmethod
    def _budget(value: Any) -> float | None:
        match = re.search(r"(?:\$|under\s*\$?|below\s*\$?)(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*(?:usd|dollars?)\b", str(value or ""), re.I)
        return float(match.group(1) or match.group(2)) if match else None

    def _product_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        if not query:
            raise ToolError("query is required")
        tokens = [token for token in re.findall(r"[a-z0-9-]+", query) if len(token) > 1]
        matches = [product for product in self.store.products if query in self._haystack(product) or any(token in self._haystack(product) for token in tokens)]
        return {"query": query, "products": matches[:8], "data_source": "synthetic_catalog"}

    def _recommend_products(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        device = str(arguments.get("device", "")).strip().lower()
        country = str(arguments.get("country", "US")).strip().upper()
        usage = str(arguments.get("usage_scenario", "")).strip().lower()
        category = str(arguments.get("category", "")).strip().lower()
        budget = self._budget(arguments.get("budget"))
        query_tokens = [token for token in re.findall(r"[a-z0-9-]+", f"{query} {category}") if len(token) > 2]
        ranked: list[dict[str, Any]] = []
        for product in self.store.products:
            price = product.get("price_usd")
            if budget is not None and isinstance(price, (int, float)) and price > budget:
                continue
            haystack = self._haystack(product)
            score = 0
            if device and device in str(product.get("device_compatibility", "")).lower(): score += 100
            if country and country in product.get("regions", []): score += 20
            if usage and usage in " ".join(product.get("usage_scenarios", [])).lower(): score += 15
            score += sum(5 for token in query_tokens if token in haystack)
            if category and category in str(product.get("category", "")).lower(): score += 20
            if score or not (device or category or query_tokens): ranked.append({**product, "recommendation_score": score})
        ranked.sort(key=lambda product: (-product["recommendation_score"], product.get("price_usd") is None, product.get("price_usd") or 0, product["sku"]))
        return {"criteria": {"device": device, "country": country, "budget": budget, "usage_scenario": usage, "category": category}, "products": ranked[:3], "data_source": "dify_synthetic_catalog_migration"}

    def _compatibility_check(self, arguments: dict[str, Any]) -> dict[str, Any]:
        sku, device = str(arguments.get("sku", "")).upper().strip(), str(arguments.get("device", "")).strip()
        if not sku or not device: raise ToolError("sku and device are required")
        product = next((item for item in self.store.products if item["sku"] == sku), None)
        if product is None: return {"sku": sku, "device": device, "compatible": False, "reason": "sku_not_found_in_synthetic_catalog", "rule_version": "compat-v2"}
        device_lower, declared = device.lower(), str(product.get("device_compatibility", "")).lower()
        ports = [str(port).lower() for port in product.get("ports", [])]
        direct_match = device_lower in declared
        usb_c_rule = any(token in device_lower for token in ("macbook", "ipad", "usb-c", "usb c")) and any("usb-c" in port for port in ports) and (product.get("power_w") or 0) >= 65
        compatible = direct_match or usb_c_rule
        reason = "declared_device_compatibility" if direct_match else "power_and_port_rule_passed" if usb_c_rule else "catalogue_rule_not_satisfied"
        return {"sku": sku, "device": device, "compatible": compatible, "reason": reason, "rule_version": "compat-v2"}

    def _policy_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        topic, region = str(arguments.get("topic", "")).strip().lower(), str(arguments.get("region", "CN")).strip().upper()
        if not topic: raise ToolError("topic is required")
        matches = [policy for policy in self.store.policies if policy.get("region") == region and (topic == policy.get("topic") or topic == policy.get("policy_type") or topic in str(policy.get("topic", "")) or topic in str(policy.get("policy_type", "")))]
        return {"topic": topic, "region": region, "policies": matches, "data_source": "synthetic_policy_seed"}

    def _order_shipment_lookup(self, arguments: dict[str, Any]) -> dict[str, Any]:
        order_id, identity_suffix = str(arguments.get("order_id", "")).strip().upper(), str(arguments.get("identity_suffix", "")).strip()
        if not order_id or not identity_suffix: raise ToolError("order_id and identity_suffix are required")
        order = self.store.orders.get(order_id)
        if order is None or order["identity_suffix"] != identity_suffix: return {"found": False, "reason": "order_or_identity_not_verified"}
        return {"found": True, "order": {key: value for key, value in order.items() if key != "identity_suffix"}, "data_source": "synthetic_order_seed"}

    def _create_simulated_ticket(self, arguments: dict[str, Any]) -> dict[str, Any]:
        idempotency_key, summary = str(arguments.pop("idempotency_key")), str(arguments.get("summary", "")).strip()
        if not summary: raise ToolError("summary is required")
        return self.store.create_ticket(idempotency_key, {"category": str(arguments.get("category", "general")), "summary": summary[:500], "evidence": arguments.get("evidence", [])})
