"""Deterministic Commerce Graph-style loop for the first MVP slice."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import re
import time
from typing import Any
from uuid import uuid4

from .models import AgentResponse, ChatRequest, ValidationError
from .multimodal import analyze_attachments
from .store import InMemoryStore
from .tools import ToolError, ToolRegistry


MAX_STEPS = 6
PROMPT_VERSION = "rules-v1"


class CommerceAgent:
    def __init__(self, store: InMemoryStore | None = None, checkpoint_store=None, retry_store=None) -> None:
        self.store = store or InMemoryStore()
        self.tools = ToolRegistry(self.store)
        self.checkpoint_store = checkpoint_store
        self.retry_store = retry_store

    def handle(self, request: ChatRequest, request_id: str | None = None) -> AgentResponse:
        request_id = request_id or f"req_{uuid4().hex}"
        self.store.increment("chat_requests")
        trace: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        state = self._load_state(request.thread_id)
        multimodal = analyze_attachments(request.attachments)
        if multimodal and multimodal["slots"]:
            request = ChatRequest(
                thread_id=request.thread_id,
                message=request.message,
                slots={**request.slots, **multimodal["slots"]},
                attachments=request.attachments,
                idempotency_key=request.idempotency_key,
            )
        state["messages"].append({"role": "user", "summary": self._summarize(request.message)})
        state["slots"].update(request.slots)
        if multimodal:
            state["slots"].update(multimodal["slots"])
            self._trace(trace, request_id, request.thread_id, "normalize_multimodal", multimodal["mode"])

        self._trace(trace, request_id, request.thread_id, "guard_input", "ok")
        risky = (multimodal or {}).get("risk_reason") or self._risk_reason(request.message)
        if risky:
            handoff = self._handoff(
                self.store,
                trace,
                request_id,
                request.thread_id,
                reason=risky,
                summary="该请求涉及首版禁止的真实写操作，已停止自动执行。",
            )
            self._save_state(request.thread_id, state)
            return AgentResponse(
                status="handoff",
                answer="我不能在首版中直接执行退款、取消订单、修改真实地址或库存变更；可以为你整理事实并提交人工处理申请。",
                request_id=request_id,
                thread_id=request.thread_id,
                handoff=handoff,
                trace=trace, multimodal=multimodal,
            )

        self._trace(trace, request_id, request.thread_id, "load_context", "ok")
        if state.get("step_count", 0) >= MAX_STEPS:
            handoff = self._handoff(
                self.store,
                trace,
                request_id,
                request.thread_id,
                reason="max_steps_reached",
                summary=f"会话已达到最多 {MAX_STEPS} 步，停止继续调用工具。",
            )
            self._save_state(request.thread_id, state)
            return AgentResponse(
                status="handoff",
                answer=f"本会话已达到最多 {MAX_STEPS} 步自动处理限制，已停止继续尝试并建议人工接管。",
                request_id=request_id,
                thread_id=request.thread_id,
                handoff=handoff,
                trace=trace,
            )
        text = request.message.lower()
        try:
            if self._is_order_intent(text):
                response = self._handle_order(request, state, trace, summaries, request_id)
            elif self._is_compatibility_intent(text):
                response = self._handle_compatibility(request, state, trace, summaries, request_id)
            elif self._is_policy_intent(text):
                response = self._handle_policy(request, state, trace, summaries, request_id)
            elif self._is_ticket_intent(text):
                response = self._handle_ticket(request, state, trace, summaries, request_id)
            elif self._is_recommendation_intent(text):
                response = self._handle_recommendation(request, state, trace, summaries, request_id)
            elif self._is_product_intent(text):
                response = self._handle_product(request, state, trace, summaries, request_id)
            else:
                handoff = self._handoff(
                    self.store,
                    trace,
                    request_id,
                    request.thread_id,
                    reason="unsupported_intent",
                    summary="无法在受控工具白名单内确认该问题。",
                )
                response = AgentResponse(
                    status="handoff",
                    answer="我还不能可靠确认这个问题。请补充商品、兼容性、政策、订单物流，或明确说明需要人工客服协助。",
                    request_id=request_id,
                    thread_id=request.thread_id,
                    handoff=handoff,
                )
        except ValidationError:
            raise
        except (ToolError, KeyError) as exc:
            self.store.increment(f"failure:{type(exc).__name__}")
            handoff = self._handoff(
                self.store,
                trace,
                request_id,
                request.thread_id,
                reason="tool_error",
                summary="受控工具未能安全返回可验证结果。",
                error_code=type(exc).__name__,
            )
            response = AgentResponse(
                status="handoff",
                answer="我暂时无法验证足够的信息，已停止继续尝试并建议人工处理。",
                request_id=request_id,
                thread_id=request.thread_id,
                handoff=handoff,
            )

        response.tool_result_summary = summaries
        response.trace = trace
        response.multimodal = multimodal
        state["step_count"] = min(MAX_STEPS, state.get("step_count", 0) + len(summaries))
        state["messages"].append({"role": "assistant", "status": response.status})
        self._save_state(request.thread_id, state)
        self.store.increment(response.status)
        return response

    def _load_state(self, thread_id: str) -> dict[str, Any]:
        checkpoint = self.checkpoint_store.load_checkpoint(thread_id) if self.checkpoint_store else None
        return checkpoint or self.store.session(thread_id)

    def _save_state(self, thread_id: str, state: dict[str, Any]) -> None:
        self.store.save_session(thread_id, state)
        if self.checkpoint_store:
            self.checkpoint_store.save_checkpoint(thread_id, state)

    def _handle_order(self, request, state, trace, summaries, request_id):
        order_id = request.slots.get("order_id") or self._find_order_id(request.message)
        identity_suffix = request.slots.get("identity_suffix") or self._find_suffix(request.message)
        if not order_id:
            return AgentResponse(
                status="needs_input",
                answer="请提供模拟订单号（例如 ORD-10023），我才能继续查询。",
                request_id=request_id,
                thread_id=request.thread_id,
            )
        if not identity_suffix:
            return AgentResponse(
                status="needs_input",
                answer="为保护订单信息，请补充下单时绑定的邮箱或手机号后四位。当前只接受脱敏后四位。",
                request_id=request_id,
                thread_id=request.thread_id,
            )
        result = self._call_tool(
            "order_shipment_lookup",
            {"order_id": order_id, "identity_suffix": identity_suffix},
            request,
            request_id,
            trace,
            summaries,
        )
        if not result.get("found"):
            handoff = self._handoff(
                self.store,
                trace,
                request_id,
                request.thread_id,
                reason="order_not_verified",
                summary="订单号或身份后缀未通过模拟校验。",
            )
            return AgentResponse(
                status="handoff",
                answer="我无法验证该订单与身份后缀是否匹配，已停止继续查询。",
                request_id=request_id,
                thread_id=request.thread_id,
                handoff=handoff,
            )
        order = result["order"]
        shipment = order["shipment"]
        return AgentResponse(
            status="completed",
            answer=(
                f"模拟订单 {order['order_id']} 当前状态为“{order['status']}”。"
                f"承运商：{shipment['carrier']}；运单号：{shipment['tracking_number']}；"
                f"轨迹：{shipment['last_event']}；"
                f"预计送达：{shipment['estimated_delivery']}。"
            ),
            request_id=request_id,
            thread_id=request.thread_id,
        )

    def _handle_compatibility(self, request, state, trace, summaries, request_id):
        sku = request.slots.get("sku") or self._find_sku(request.message)
        device = request.slots.get("device") or self._find_device(request.message)
        if not sku:
            return AgentResponse(
                status="needs_input",
                answer="请补充要确认的商品 SKU（例如 AC-65W）。",
                request_id=request_id,
                thread_id=request.thread_id,
            )
        if not device:
            return AgentResponse(
                status="needs_input",
                answer="请补充设备型号或接口信息（例如 MacBook Pro 14）。",
                request_id=request_id,
                thread_id=request.thread_id,
            )
        result = self._call_tool(
            "compatibility_check",
            {"sku": sku, "device": device},
            request,
            request_id,
            trace,
            summaries,
        )
        verdict = "兼容" if result["compatible"] else "暂不能确认兼容"
        return AgentResponse(
            status="completed",
            answer=f"基于规则版本 {result['rule_version']}，{sku} 与 {device}：{verdict}。依据：{result['reason']}。",
            request_id=request_id,
            thread_id=request.thread_id,
        )

    def _handle_policy(self, request, state, trace, summaries, request_id):
        text = request.message.lower()
        if any(word in text for word in ("shipping", "delivery", "logistics", "ship to")):
            topic = "shipping"
        elif any(word in text for word in ("warranty", "guarantee")):
            topic = "warranty"
        elif any(word in text for word in ("coupon", "discount", "student")):
            topic = "promotion"
        else:
            topic = "return"
        region = request.slots.get("region") or request.slots.get("country") or ("US" if any(word in text for word in ("us", "united states")) else "CN")
        result = self._call_tool(
            "policy_search", {"topic": topic, "region": region}, request, request_id, trace, summaries
        )
        if not result["policies"]:
            return AgentResponse(
                status="handoff",
                answer="没有找到适用的模拟政策记录，建议人工核实。",
                request_id=request_id,
                thread_id=request.thread_id,
                handoff=self._handoff(
                    self.store, trace, request_id, request.thread_id, "policy_not_found", "政策数据不足。"
                ),
            )
        policy = result["policies"][0]
        return AgentResponse(
            status="completed",
            answer=f"{policy['summary']}（适用地区：{policy['region']}；生效日：{policy['effective_from']}；来源：{policy['source']}）",
            request_id=request_id,
            thread_id=request.thread_id,
        )

    def _handle_recommendation(self, request, state, trace, summaries, request_id):
        device = request.slots.get("device") or request.slots.get("device_model") or self._find_device(request.message) or ""
        country = request.slots.get("country") or request.slots.get("region") or "US"
        budget = request.slots.get("budget") or request.slots.get("budget_text") or request.message
        usage_scenario = request.slots.get("usage_scenario") or ""
        category = self._product_query(request.message)
        result = self._call_tool(
            "recommend_products",
            {"query": request.message, "device": device, "country": country, "budget": budget, "usage_scenario": usage_scenario, "category": category},
            request, request_id, trace, summaries,
        )
        products = result["products"]
        if not products:
            return AgentResponse(status="needs_input", answer="I could not find a synthetic catalogue match. Please add a device model, category, country, or budget.", request_id=request_id, thread_id=request.thread_id)
        formatted = "; ".join(
            f"{item['sku']} {item['name']}" + (f" (${item['price_usd']:.2f})" if isinstance(item.get("price_usd"), (int, float)) else "")
            for item in products
        )
        qualifier = f" for {device}" if device else ""
        evidence = [{key: item.get(key) for key in ("sku", "name", "category", "price_usd", "device_compatibility", "usage_scenarios", "source")} for item in products]
        return AgentResponse(status="completed", answer=f"From the migrated synthetic ShopPilot catalogue, my recommended match{qualifier} is: {formatted}. These are demonstration-only products and availability; no real Shopify catalogue or inventory was queried.", request_id=request_id, thread_id=request.thread_id, recommendations=evidence)

    def _handle_product(self, request, state, trace, summaries, request_id):
        query = request.slots.get("query") or self._product_query(request.message)
        result = self._call_tool("product_search", {"query": query}, request, request_id, trace, summaries)
        if not result["products"]:
            return AgentResponse(
                status="completed",
                answer="模拟商品目录中没有找到匹配项；如需进一步核实，请提供 SKU 或更具体的用途。",
                request_id=request_id,
                thread_id=request.thread_id,
            )
        products = "；".join(
            f"{item['sku']}（{item['name']}，{item['power_w']}W，库存状态：{item['stock']}）"
            for item in result["products"]
        )
        return AgentResponse(
            status="completed",
            answer=f"模拟商品目录匹配结果：{products}。库存仅为演示数据，不会扣减。",
            request_id=request_id,
            thread_id=request.thread_id,
        )

    def _handle_ticket(self, request, state, trace, summaries, request_id):
        if not request.idempotency_key:
            return AgentResponse(
                status="needs_input",
                answer="创建模拟客服工单前，请提供本次请求的 idempotency_key（8-128 个安全字符）。",
                request_id=request_id,
                thread_id=request.thread_id,
            )
        result = self._call_tool(
            "create_simulated_ticket",
            {"category": "customer_support", "summary": request.message, "evidence": []},
            request,
            request_id,
            trace,
            summaries,
        )
        dedupe_note = "（重复请求已复用同一工单）" if result["deduplicated"] else ""
        return AgentResponse(
            status="completed",
            answer=f"已创建模拟客服工单 {result['ticket_id']}，状态：{result['status']}。{dedupe_note}不会触达真实客服系统。",
            request_id=request_id,
            thread_id=request.thread_id,
        )

    def _call_tool(self, name, arguments, request, request_id, trace, summaries):
        self._trace(trace, request_id, request.thread_id, "plan_next_action", name)
        started = time.perf_counter()
        try:
            result = self.tools.invoke(name, arguments, idempotency_key=request.idempotency_key)
        except ToolError as exc:
            definition = self.tools._tools.get(name)
            can_retry = bool(definition and definition.read_only and self.retry_store)
            if can_retry and self.retry_store.consume_tool_retry(request_id, name):
                self._trace(trace, request_id, request.thread_id, "tool_retry", "retrying", type(exc).__name__)
                result = self.tools.invoke(name, arguments, idempotency_key=request.idempotency_key)
            else:
                self._trace(trace, request_id, request.thread_id, "validate_tool_result", "error", type(exc).__name__)
                raise
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        self._trace(trace, request_id, request.thread_id, "validate_tool_result", "ok", elapsed_ms=elapsed_ms)
        summaries.append({"tool": name, "ok": True, "result_keys": sorted(result.keys())})
        return result

    @staticmethod
    def _trace(trace, request_id, thread_id, node, outcome, error_code=None, elapsed_ms=0.0):
        trace.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "thread_id": thread_id,
                "node": node,
                "outcome": outcome,
                "prompt_version": PROMPT_VERSION,
                "elapsed_ms": elapsed_ms,
                "error_code": error_code,
            }
        )

    @staticmethod
    def _handoff(store, trace, request_id, thread_id, reason, summary, error_code=None):
        store.increment("handoffs")
        store.increment(f"handoff:{reason}")
        store.record_handoff(reason)
        CommerceAgent._trace(trace, request_id, thread_id, "human_review", reason, error_code)
        return {"required": True, "reason": reason, "summary": summary}

    @staticmethod
    def _summarize(message: str) -> str:
        digest = hashlib.sha256(message.encode("utf-8")).hexdigest()[:12]
        return f"message_hash:{digest};length:{len(message)}"

    @staticmethod
    def _risk_reason(message: str) -> str | None:
        text = message.lower()
        patterns = {
            "real_refund_or_return_action": ("我要退款", "申请退款", "直接退款", "退钱"),
            "real_order_cancellation": ("取消订单", "帮我取消", "直接取消"),
            "real_address_mutation": ("修改地址", "改收货地址", "更改地址"),
            "real_inventory_mutation": ("扣库存", "改库存", "锁库存"),
        }
        for reason, keywords in patterns.items():
            if any(keyword in text for keyword in keywords):
                return reason
        return None

    @staticmethod
    def _is_order_intent(text):
        return any(word in text for word in ("订单", "物流", "包裹", "轨迹", "order", "tracking"))

    @staticmethod
    def _is_compatibility_intent(text):
        return any(word in text for word in ("兼容", "能用", "适配", "compatible", "charger for", "work with", "will work", "charger work"))

    @staticmethod
    def _is_policy_intent(text):
        return any(word in text for word in ("政策", "退货政策", "退换", "保修", "return policy", "warranty", "shipping", "delivery", "student discount", "coupon"))

    @staticmethod
    def _is_ticket_intent(text):
        return any(word in text for word in ("人工", "客服", "工单", "投诉", "human", "ticket"))

    @staticmethod
    def _is_product_intent(text):
        return any(word in text for word in ("商品", "充电器", "线", "推荐", "sku", "charger", "cable"))

    @staticmethod
    def _is_recommendation_intent(text):
        return any(word in text for word in ("recommend", "recommendation", "best", "bundle", "under $", "accessory", "which charger", "which cable", "want a", "need a", "i use an"))

    @staticmethod
    def _find_order_id(message):
        match = re.search(r"\b(ORD-[0-9]{4,})\b", message.upper())
        return match.group(1) if match else None

    @staticmethod
    def _find_suffix(message):
        matches = re.findall(r"(?<!\d)(\d{4})(?!\d)", message)
        return matches[-1] if matches else None

    @staticmethod
    def _find_sku(message):
        match = re.search(r"\b(AC-(?:65|100)W|CB-C2C-2M|SKU[0-9]{3})\b", message.upper())
        return match.group(1) if match else None

    @staticmethod
    def _find_device(message):
        match = re.search(r"(MacBook(?: (?:Air|Pro))?(?: [A-Z0-9]+)?|iPhone(?: [0-9]{1,2})?(?: Pro)?|iPad(?: Pro)?|Samsung Galaxy S[0-9]+|Google Pixel [0-9]+|USB-C(?: 接口)?)", message, re.I)
        return match.group(1) if match else None

    @staticmethod
    def _product_query(message):
        text = message.lower()
        if any(word in text for word in ("线", "cable")):
            return "cable"
        return "charger"
