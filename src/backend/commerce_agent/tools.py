"""Allow-listed tools backed only by repository-packaged synthetic data."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable
import time
from threading import BoundedSemaphore
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from .rag import HybridRetriever, build_knowledge_documents
from .store import InMemoryStore


class ToolError(ValueError):
    """A safe, user-visible tool failure."""


class TransientToolError(ToolError):
    """Only a transient read failure is eligible for bounded retry."""


TOOL_FIELDS = {
    "product_search": {"query"},
    "recommend_products": {"query", "device", "country", "budget", "usage_scenario", "category"},
    "compatibility_check": {"sku", "device"},
    "policy_search": {"topic", "region", "query", "as_of"},
    "knowledge_search": {"query", "kind", "region", "sku", "category", "as_of"},
    "order_shipment_lookup": {"order_id", "identity_suffix"},
    "create_simulated_ticket": {"summary", "category", "evidence"},
}
RESULT_FIELDS = {
    "product_search": {"products": list}, "recommend_products": {"products": list},
    "compatibility_check": {"compatible": bool, "reason": str},
    "policy_search": {"policies": list, "citations": list},
    "knowledge_search": {"chunks": list, "citations": list},
    "order_shipment_lookup": {"found": bool},
    "create_simulated_ticket": {"ticket_id": str, "status": str, "deduplicated": bool},
}


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    read_only: bool
    requires_idempotency: bool
    required_arguments: tuple[str, ...]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self, store: InMemoryStore, embedder=None) -> None:
        self.store = store
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="commerce-read")
        self._read_capacity = BoundedSemaphore(4)
        self.retriever = HybridRetriever(build_knowledge_documents(store.products, store.policies), embedder=embedder)
        self._tools = {
            "product_search": ToolDefinition("product_search", "Search the synthetic product catalogue.", True, False, ("query",), self._product_search),
            "recommend_products": ToolDefinition("recommend_products", "Rank synthetic catalogue products using deterministic constraints.", True, False, ("query",), self._recommend_products),
            "compatibility_check": ToolDefinition("compatibility_check", "Evaluate a deterministic compatibility rule.", True, False, ("sku", "device"), self._compatibility_check),
            "policy_search": ToolDefinition("policy_search", "Find synthetic policy records by topic and region.", True, False, ("topic",), self._policy_search),
            "knowledge_search": ToolDefinition("knowledge_search", "Retrieve cited synthetic product and FAQ knowledge using hybrid RAG.", True, False, ("query",), self._knowledge_search),
            "order_shipment_lookup": ToolDefinition("order_shipment_lookup", "Look up a verified synthetic order.", True, False, ("order_id", "identity_suffix"), self._order_shipment_lookup),
            "create_simulated_ticket": ToolDefinition("create_simulated_ticket", "Create a local simulated support ticket.", False, True, ("summary",), self._create_simulated_ticket),
        }

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def contracts(self):
        return [{"name": name, "description": tool.description, "read_only": tool.read_only,
                 "required": list(tool.required_arguments), "allowed_fields": sorted(TOOL_FIELDS[name]),
                 "requires_idempotency": tool.requires_idempotency} for name, tool in self._tools.items()]

    def execute(self, name, arguments, *, idempotency_key=None, timeout_seconds=20):
        definition = self._tools.get(name)
        if not definition:
            raise ToolError("tool is not allow-listed")
        for attempt in range(2):
            try:
                if definition.read_only:
                    if not self._read_capacity.acquire(blocking=False):
                        raise TransientToolError("read_tool_capacity_exceeded")
                    pending = self._executor.submit(self.invoke, name, arguments, idempotency_key=idempotency_key)
                    pending.add_done_callback(lambda _: self._read_capacity.release())
                    try:
                        return pending.result(timeout=timeout_seconds)
                    except FutureTimeout as exc:
                        pending.cancel()
                        raise TransientToolError("read_tool_timeout") from exc
                # Local transactional writes are not retried; timeout does not mean rollback.
                return self.invoke(name, arguments, idempotency_key=idempotency_key)
            except TransientToolError:
                if not definition.read_only or attempt:
                    raise
                self.store.increment("tool_retries")
                time.sleep(0.05)

    def invoke(self, name: str, arguments: dict[str, Any], *, idempotency_key: str | None = None) -> dict[str, Any]:
        definition = self._tools.get(name)
        if definition is None:
            raise ToolError("tool is not allow-listed")
        if not isinstance(arguments, dict):
            raise ToolError("tool arguments must be an object")
        if set(arguments) - TOOL_FIELDS[name]:
            raise ToolError("unsupported tool argument")
        for key, value in arguments.items():
            if key == "evidence":
                if not isinstance(value, list) or len(value) > 6 or any(not isinstance(item, dict) for item in value):
                    raise ToolError("invalid evidence")
            elif not isinstance(value, str) or len(value) > 4000:
                raise ToolError("tool arguments must be bounded strings")
        if "identity_suffix" in arguments and not re.fullmatch(r"[A-Za-z0-9]{4}", arguments["identity_suffix"]):
            raise ToolError("identity suffix must be exactly four characters")
        missing = [key for key in definition.required_arguments if not str(arguments.get(key, "")).strip()]
        if missing:
            raise ToolError(f"missing required tool arguments: {', '.join(missing)}")
        if definition.requires_idempotency and not idempotency_key:
            raise ToolError("idempotency_key is required for simulated writes")
        self.store.increment("tool_calls")
        self.store.increment(f"tool:{name}")
        if definition.requires_idempotency:
            arguments = {**arguments, "idempotency_key": idempotency_key}
        result = definition.handler(dict(arguments))
        if not isinstance(result, dict) or any(type(result.get(key)) is not kind for key, kind in RESULT_FIELDS[name].items()):
            raise ToolError("tool_output_schema_invalid")
        if name == "order_shipment_lookup" and result["found"] and not isinstance(result.get("order"), dict):
            raise ToolError("order_output_schema_invalid")
        return result

    @staticmethod
    def _haystack(product: dict[str, Any]) -> str:
        values = [product.get("sku", ""), product.get("name", ""), product.get("category", ""), product.get("brand", ""), product.get("device_compatibility", ""), product.get("search_aliases", ""), product.get("key_features", ""), " ".join(product.get("ports", [])), " ".join(product.get("usage_scenarios", []))]
        return " ".join(str(value) for value in values).lower()

    @staticmethod
    def _budget(value: Any) -> float | None:
        if re.fullmatch(r"\d+(?:\.\d+)?", str(value or "")):
            return float(value)
        match = re.search(r"(?:\$|under\s*\$?|below\s*\$?)(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*(?:usd|dollars?)\b", str(value or ""), re.I)
        return float(match.group(1) or match.group(2)) if match else None

    def _product_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        if not query:
            raise ToolError("query is required")
        aliases = {"充电器": "charger", "数据线": "cable", "耳机": "earbuds", "扩展坞": "hub"}
        for chinese, english in aliases.items():
            query = query.replace(chinese, english)
        tokens = [token for token in re.findall(r"[a-z0-9-]+", query) if len(token) > 1]
        matches = [product for product in self.store.products if query in self._haystack(product) or any(token in self._haystack(product) for token in tokens)]
        return {"query": query, "products": matches[:8], "data_source": "synthetic_catalog"}

    def _recommend_products(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip().lower()
        device = str(arguments.get("device", "")).strip().lower()
        country = str(arguments.get("country", "")).strip().upper()
        usage = str(arguments.get("usage_scenario", "")).strip().lower()
        category = str(arguments.get("category", "")).strip().lower()
        budget = self._budget(arguments.get("budget"))
        query_tokens = [token for token in re.findall(r"[a-z0-9-]+", f"{query} {category}") if len(token) > 2]
        ranked: list[dict[str, Any]] = []
        for product in self.store.products:
            price = product.get("price_usd")
            if budget is not None and (not isinstance(price, (int, float)) or price > budget):
                continue
            if country and country not in product.get("regions", []):
                continue
            if category and category not in str(product.get("category", "")).lower():
                continue
            if device and device not in str(product.get("device_compatibility", "")).lower():
                continue
            haystack = self._haystack(product)
            score = 0
            compatibility = str(product.get("device_compatibility", "")).lower()
            if device and device in compatibility:
                score += 100
            elif device and device.split()[0] in compatibility:
                score += 45
            if country and country in product.get("regions", []): score += 20
            if usage and usage in " ".join(product.get("usage_scenarios", [])).lower(): score += 15
            score += sum(5 for token in query_tokens if token in haystack)
            if category and category in str(product.get("category", "")).lower(): score += 20
            if "bundle" in query and any(word in str(product.get("category", "")).lower() for word in ("charger", "cable")):
                score += 30
            if not any(word in query for word in ("car", "drive", "vehicle")) and "car" in haystack:
                score -= 80
            if product.get("source") == "public_reference_catalog":
                score -= 10
            if score or not (device or category or query_tokens): ranked.append({**product, "recommendation_score": score})
        ranked.sort(key=lambda product: (-product["recommendation_score"], product.get("price_usd") is None, product.get("price_usd") or 0, product["sku"]))
        bundle_requested = any(word in query for word in ("bundle", "套装", "套餐", "setup"))
        if bundle_requested:
            chargers = [item for item in ranked if "charger" in str(item.get("category", "")).lower()]
            cables = [item for item in ranked if "cable" in str(item.get("category", "")).lower()]
            pairs = [(charger, cable) for charger in chargers for cable in cables
                     if budget is None or charger["price_usd"] + cable["price_usd"] <= budget]
            ranked = list(pairs[0]) if pairs else []
        return {"criteria": {"device": device, "country": country, "budget": budget, "usage_scenario": usage, "category": category, "bundle_requested": bundle_requested}, "products": ranked[:3], "data_source": "dify_synthetic_catalog_migration"}

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
        query = str(arguments.get("query", "")).strip()
        synonyms = {"return": "return refund exchange 退货 退款", "warranty": "warranty guarantee 保修", "shipping": "shipping delivery logistics 配送 物流", "promotion": "promotion coupon discount 优惠"}
        retrieval = self.retriever.search(f"{query} {synonyms.get(topic, topic)}", filters={"kind": "policy", "topic": topic, "region": region, **({"as_of": arguments["as_of"]} if arguments.get("as_of") else {})})
        policies = []
        for item in retrieval["chunks"]:
            metadata = item["citation"]["metadata"]
            policies.append({"policy_id": metadata["policy_id"], "topic": metadata["topic"], "region": metadata["region"], "effective_from": metadata["effective_from"], "summary": metadata["answer_text"], "source": item["citation"]["source"], "citation": item["citation"]})
        return {"topic": topic, "region": region, "policies": policies, "citations": [item["citation"] for item in retrieval["chunks"]], "retrieval": retrieval, "data_source": "hybrid_rag_synthetic_policy_kb"}

    def _knowledge_search(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise ToolError("query is required")
        kind = str(arguments.get("kind", "")).strip().lower() or None
        region = str(arguments.get("region", "")).strip().upper() or None
        retrieval = self.retriever.search(query, filters={key: value for key, value in {"kind": kind, "region": region, "sku": arguments.get("sku"), "category": arguments.get("category"), "as_of": arguments.get("as_of")}.items() if value})
        return {"query": query, "chunks": retrieval["chunks"], "citations": [item["citation"] for item in retrieval["chunks"]], "retrieval": retrieval, "data_source": "hybrid_rag_synthetic_merchant_kb"}

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
