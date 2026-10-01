"""Model-safe planning, composition, and production-readiness primitives.

The module deliberately uses the OpenAI-compatible HTTP shape through the
standard library.  It never makes a network call unless all three LLM
environment variables are configured.  A missing or invalid model response
always falls back to the deterministic runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
import re
from typing import Any, Callable
from urllib import request as urlrequest


ALLOWED_INTENTS = {"product", "recommendation", "compatibility", "policy", "order", "ticket", "handoff"}
TOOL_BY_INTENT = {
    "product": "product_search",
    "recommendation": "recommend_products",
    "compatibility": "compatibility_check",
    "policy": "policy_search",
    "order": "order_shipment_lookup",
    "ticket": "create_simulated_ticket",
}
PROHIBITED_COMPOSER_CLAIMS = ("refund confirmed", "order cancelled", "inventory updated", "address changed", "live shopify")


@dataclass(frozen=True)
class ActionPlan:
    action: str
    intent: str
    slots: dict[str, str] = field(default_factory=dict)
    missing_slots: list[str] = field(default_factory=list)
    reason_code: str = "deterministic_fallback"
    model_used: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModelAdapter:
    """Optional, bounded OpenAI-compatible model adapter.

    ``transport`` exists for deterministic tests; production uses the standard
    library HTTP client only when explicitly configured by environment.
    """

    def __init__(self, transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        self.provider = os.getenv("COMMERCE_LLM_PROVIDER", "openai_compatible").strip().lower()
        self.base_url = os.getenv("COMMERCE_LLM_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("COMMERCE_LLM_API_KEY", "")
        self.model = os.getenv("COMMERCE_LLM_MODEL", "")
        self.response_mode = os.getenv("COMMERCE_LLM_RESPONSE_MODE", "json_object").strip().lower()
        self.timeout_seconds = float(os.getenv("COMMERCE_LLM_TIMEOUT_SECONDS", "8"))
        self._transport = transport

    @property
    def enabled(self) -> bool:
        return self._transport is not None or bool(self.base_url and self.api_key and self.model)

    @property
    def version(self) -> str:
        return f"{self.provider}:{self.model or 'test-model'}" if self.enabled else "disabled"

    def complete_json(self, system: str, user: str, schema: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        response_format: dict[str, Any] = {"type": "json_object"}
        # Qwen DashScope's OpenAI-compatible mode and several approved gateways
        # support this shape.  Unsupported endpoints safely fail closed below and
        # the deterministic planner/composer remains in control.
        if self.response_mode == "json_schema" and schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "commerce_agent_response", "strict": True, "schema": schema},
            }
        payload = {
            "model": self.model or "test-model",
            "temperature": 0,
            "response_format": response_format,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            if self._transport:
                return self._transport(payload)
            body = json.dumps(payload).encode("utf-8")
            req = urlrequest.Request(
                f"{self.base_url}/chat/completions", body, method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            with urlrequest.urlopen(req, timeout=self.timeout_seconds) as response:  # nosec B310: operator-configured endpoint
                raw = json.loads(response.read().decode("utf-8"))
            content = raw["choices"][0]["message"]["content"]
            return json.loads(self._strip_fence(content)) if isinstance(content, str) else None
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def _strip_fence(value: str) -> str:
        return re.sub(r"^```(?:json)?\s*|\s*```$", "", value.strip(), flags=re.I)


class Planner:
    """Creates a typed plan and rejects model-selected authority expansion."""

    def __init__(self, model: ModelAdapter | None = None) -> None:
        self.model = model or ModelAdapter()

    def plan(self, message: str, slots: dict[str, str]) -> ActionPlan:
        candidate = self.model.complete_json(
            "You are a commerce planner. Return JSON only with action, intent, slots, missing_slots, reason_code. "
            "Allowed actions: call_tool, ask_user, handoff. Allowed intents: product, recommendation, compatibility, policy, order, ticket, handoff. "
            "Never perform an operation, invent evidence, or request secret/full identity data.",
            json.dumps({"message": message[:4000], "verified_slots": slots}, ensure_ascii=False),
            self._plan_schema(),
        )
        validated = self._validate(candidate)
        return validated if validated else self._fallback(message, slots)

    def compose(self, answer: str, evidence: list[dict[str, Any]], status: str) -> tuple[str, bool]:
        if status != "completed":
            return answer, False
        candidate = self.model.complete_json(
            "Return JSON only: {\"answer\": string}. Rephrase only the supplied answer/evidence. "
            "Do not add facts, claims of live data, commitments, or operational actions.",
            json.dumps({"draft_answer": answer, "evidence": evidence}, ensure_ascii=False),
            self._compose_schema(),
        )
        if not isinstance(candidate, dict) or not isinstance(candidate.get("answer"), str):
            return answer, False
        rendered = candidate["answer"].strip()
        if not rendered or len(rendered) > 3000 or any(claim in rendered.lower() for claim in PROHIBITED_COMPOSER_CLAIMS):
            return answer, False
        known_skus = {str(item.get("sku")) for item in evidence if item.get("sku")}
        mentioned_skus = set(re.findall(r"\b(?:SKU\d{3}|AC-\d+W|CB-[A-Z0-9-]+)\b", rendered.upper()))
        if mentioned_skus - known_skus:
            return answer, False
        return rendered, True

    @staticmethod
    def _plan_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["action", "intent", "slots", "missing_slots", "reason_code"],
            "properties": {
                "action": {"type": "string", "enum": ["call_tool", "ask_user", "handoff"]},
                "intent": {"type": "string", "enum": sorted(ALLOWED_INTENTS)},
                "slots": {"type": "object", "additionalProperties": {"type": ["string", "number", "integer"]}},
                "missing_slots": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                "reason_code": {"type": "string", "maxLength": 100},
            },
        }

    @staticmethod
    def _compose_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["answer"],
            "properties": {"answer": {"type": "string", "maxLength": 3000}},
        }

    @staticmethod
    def _validate(candidate: Any) -> ActionPlan | None:
        if not isinstance(candidate, dict):
            return None
        action, intent = candidate.get("action"), candidate.get("intent")
        if action not in {"call_tool", "ask_user", "handoff"} or intent not in ALLOWED_INTENTS:
            return None
        if action == "call_tool" and intent not in TOOL_BY_INTENT:
            return None
        raw_slots = candidate.get("slots", {})
        raw_missing = candidate.get("missing_slots", [])
        if not isinstance(raw_slots, dict) or not isinstance(raw_missing, list):
            return None
        slots = {str(key): str(value)[:256] for key, value in raw_slots.items() if isinstance(key, str) and isinstance(value, (str, int, float))}
        missing = [str(item)[:64] for item in raw_missing if isinstance(item, str)][:5]
        return ActionPlan(action=action, intent=intent, slots=slots, missing_slots=missing, reason_code=str(candidate.get("reason_code", "model_plan"))[:100], model_used=True)

    @staticmethod
    def _fallback(message: str, slots: dict[str, str]) -> ActionPlan:
        text = message.lower()
        if any(word in text for word in ("refund", "cancel order", "change address", "退款", "取消订单", "修改地址", "扣库存")):
            return ActionPlan("handoff", "handoff", reason_code="protected_operation")
        if any(word in text for word in ("order", "tracking", "物流", "订单", "包裹")):
            return ActionPlan("call_tool" if slots.get("order_id") else "ask_user", "order", missing_slots=[] if slots.get("order_id") else ["order_id"], reason_code="order_route")
        if any(word in text for word in ("compatible", "work with", "兼容", "能用", "适配")):
            return ActionPlan("call_tool", "compatibility", reason_code="compatibility_route")
        if any(word in text for word in ("policy", "warranty", "shipping", "return", "政策", "退货", "保修")):
            return ActionPlan("call_tool", "policy", reason_code="policy_route")
        if any(word in text for word in ("human", "ticket", "客服", "人工", "工单")):
            return ActionPlan("call_tool", "ticket", reason_code="ticket_route")
        if any(word in text for word in ("recommend", "bundle", "accessory", "推荐", "套餐", "套装")):
            return ActionPlan("call_tool", "recommendation", reason_code="recommendation_route")
        return ActionPlan("call_tool", "product", reason_code="product_route")


def production_readiness() -> dict[str, bool]:
    """Expose configuration gates without inspecting or leaking secret values."""
    return {
        "llm_configured": bool(os.getenv("COMMERCE_LLM_BASE_URL") and os.getenv("COMMERCE_LLM_API_KEY") and os.getenv("COMMERCE_LLM_MODEL")),
        "merchant_connector_configured": bool(os.getenv("COMMERCE_SHOPIFY_CONNECTOR_ENABLED") == "true"),
        "oidc_configured": bool(os.getenv("COMMERCE_OIDC_ISSUER") and os.getenv("COMMERCE_OIDC_AUDIENCE")),
        "production_mode": os.getenv("COMMERCE_PRODUCTION_MODE") == "true",
    }
