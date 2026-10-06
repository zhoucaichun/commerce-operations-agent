"""Bounded plan/tool/observation loop shared by API and direct callers."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, TypedDict
import time

from langgraph.graph import END, START, StateGraph
from .agent import CommerceAgent, MAX_STEPS
from .memory import merge_slots, model_context
from .models import AgentResponse, ChatRequest
from .multimodal import analyze_attachments
from .runtime import ActionPlan, ModelAdapter, Planner, TOOL_BY_INTENT
from .tools import ToolError


class CommerceGraphState(TypedDict, total=False):
    request: ChatRequest
    request_id: str
    plan: ActionPlan
    response: AgentResponse
    graph_nodes: list[str]
    memory: dict[str, Any]
    trace: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    steps: int
    primary_intent: str
    plans: list[dict[str, Any]]
    seen: list[str]
    allowed_tools: list[str]
    forced_intent: str | None
    terminal: bool
    multimodal: dict[str, Any] | None
    grounded_slots: dict[str, str]
    started: float
    usage_start: dict[str, int]


class CommerceGraph:
    def __init__(self, agent: CommerceAgent, model: ModelAdapter | None = None) -> None:
        self.agent = agent
        self.planner = Planner(model or agent.model)
        self._turn_lock = agent.turn_lock
        graph = StateGraph(CommerceGraphState)
        for name, handler in (("guard_input", self._guard_input), ("load_memory", self._load_memory),
                              ("planner", self._planner), ("tool", self._tool), ("validate", self._validate),
                              ("compose", self._compose), ("handoff", self._handoff), ("persist", self._persist)):
            graph.add_node(name, handler)
        graph.add_edge(START, "guard_input")
        graph.add_edge("guard_input", "load_memory")
        graph.add_conditional_edges("load_memory", self._after_memory, {"planner": "planner", "persist": "persist", "handoff": "handoff"})
        graph.add_conditional_edges("planner", self._after_plan, {"tool": "tool", "compose": "compose", "handoff": "handoff", "persist": "persist"})
        graph.add_edge("tool", "validate")
        graph.add_conditional_edges("validate", self._after_validation, {"planner": "planner", "handoff": "handoff", "persist": "persist"})
        graph.add_edge("compose", "persist")
        graph.add_edge("handoff", "persist")
        graph.add_edge("persist", END)
        self._compiled = graph.compile()

    def invoke(self, request: ChatRequest, request_id: str, *, forced_intent=None, allowed_tools=None) -> AgentResponse:
        with self._turn_lock:
            state = self._compiled.invoke({"request": request, "request_id": request_id, "graph_nodes": [],
                                          "trace": [], "observations": [], "steps": 0, "seen": [], "plans": [],
                                          "allowed_tools": list(self.agent.tools.names if allowed_tools is None else allowed_tools),
                                          "forced_intent": forced_intent, "terminal": False, "started": time.perf_counter(),
                                          "usage_start": dict(self.planner.model.usage)}, {"recursion_limit": 40})
        return state["response"]

    @staticmethod
    def _append(state, node, **values):
        return {"graph_nodes": [*state.get("graph_nodes", []), node], **values}

    def _response(self, state, status, answer, reason=None):
        handoff = None
        if status == "handoff":
            handoff = self.agent._handoff(self.agent.store, state["trace"], state["request_id"], state["request"].thread_id,
                                          reason or "safe_handoff", "已停止自动执行，请人工核实。")
        return AgentResponse(status, answer, state["request_id"], state["request"].thread_id, handoff=handoff)

    def _guard_input(self, state):
        req = state["request"]
        req = ChatRequest.from_dict({"thread_id": req.thread_id, "message": req.message, "slots": req.slots,
                                    "attachments": req.attachments, "idempotency_key": req.idempotency_key})
        self.agent.store.increment("chat_requests")
        self.agent._trace(state["trace"], state["request_id"], req.thread_id, "guard_input", "ok")
        return self._append(state, "guard_input", request=req)

    def _load_memory(self, state):
        req = state["request"]
        memory = self.agent._load_state(req.thread_id)
        memory.setdefault("messages", [])
        memory.setdefault("slots", {})
        if self.agent._forget_memory_request(req.message):
            memory = {"thread_id": req.thread_id, "messages": [], "slots": {}, "preferences": {}, "step_count": 0}
            self.agent._trace(state["trace"], state["request_id"], req.thread_id, "memory_delete", "confirmed")
            return self._append(state, "load_memory", memory=memory, terminal=True,
                                response=self._response(state, "completed", "已清除本会话的模拟记忆，未修改商家系统数据。"))
        intent = state.get("forced_intent") or self.agent._classify_intent(req.message.lower())
        if intent == "unsupported" and (memory.get("pending_input") or merge_slots({}, req.message, req.slots, intent)):
            intent = memory.get("intent", "product")
        slots = merge_slots(memory, req.message, req.slots, intent)
        multimodal = analyze_attachments(req.attachments)
        if multimodal:
            slots = {**slots, **multimodal["slots"], **req.slots}
        req = replace(req, slots=slots)
        memory["slots"] = slots
        memory["step_count"] = 0
        memory["messages"].append({"role": "user", "summary": self.agent._summarize(req.message)})
        self.agent._remember_confirmed_preferences(memory, req)
        self.agent._compact_memory(memory)
        risk = self.agent._risk_reason(req.message) or (multimodal or {}).get("risk_reason")
        values = {"request": req, "memory": memory, "primary_intent": intent, "multimodal": multimodal, "grounded_slots": dict(slots)}
        if risk:
            values["response"] = self._response(state, "handoff", "此请求涉及风险或禁止的真实写操作，不能自动执行，已建议人工接管。", risk)
            values["terminal"] = True
        return self._append(state, "load_memory", **values)

    @staticmethod
    def _after_memory(state):
        if not state["terminal"]:
            return "planner"
        return "handoff" if state["response"].status == "handoff" else "persist"

    def _planner(self, state):
        req = state["request"]
        message, slots = model_context(req.message, req.slots)
        contracts = [c for c in self.agent.tools.contracts() if c["name"] in state["allowed_tools"]]
        plan = self.planner.plan(message, slots, state["observations"], contracts)
        if not plan.model_used and not state["observations"] and state["primary_intent"] != "unsupported":
            plan = replace(plan, intent=state["primary_intent"], action="call_tool", missing_slots=[])
        if plan.slots.get("identity_suffix") or (plan.slots.get("order_id") and plan.slots["order_id"] != req.slots.get("order_id")):
            self.planner.model.record_rejection("planner_identity_rejected")
            plan = self.planner._fallback(message, slots, state["observations"])
        proposed = {k: v for k, v in plan.slots.items() if k not in {"identity_suffix", "order_id"}}
        req = replace(req, slots={**req.slots, **proposed, **state["grounded_slots"]})
        tool = plan.tool or TOOL_BY_INTENT.get(plan.intent)
        if plan.action == "answer" and not state["observations"]:
            plan = replace(plan, action="call_tool")
        if plan.action == "call_tool" and tool not in state["allowed_tools"]:
            plan = replace(plan, action="handoff", reason_code="tool_permission_denied")
        if state["steps"] >= MAX_STEPS and plan.action == "call_tool":
            plan = replace(plan, action="handoff", reason_code="max_steps_reached")
        fingerprint = f"{tool}:{sorted(req.slots.items())}"
        if plan.action == "call_tool" and fingerprint in state["seen"]:
            plan = replace(plan, action="handoff", reason_code="repeated_tool_action")
        self.agent._trace(state["trace"], state["request_id"], req.thread_id, "model_planner", "used" if plan.model_used else "fallback", error_code=plan.reason_code)
        primary = plan.intent if not state["observations"] else state["primary_intent"]
        values = {"request": req, "plan": plan, "primary_intent": primary,
                  "plans": [*state["plans"], {"action": plan.action, "intent": plan.intent, "tool": tool, "model_used": plan.model_used, "reason_code": plan.reason_code}]}
        if plan.action == "handoff":
            values["response"] = self._response(state, "handoff", "当前请求无法继续安全自动处理，已建议人工核实。", plan.reason_code)
        elif plan.action == "ask_user":
            questions = {"device": "请补充设备型号。", "device_model": "请补充设备型号。", "sku": "请补充商品 SKU。",
                         "order_id": "请提供模拟订单号。", "identity_suffix": "请补充下单身份后四位，不要提供完整身份信息。",
                         "country": "请补充配送国家或地区。", "budget": "请补充预算。"}
            values["response"] = self._response(state, "needs_input", questions.get(next(iter(plan.missing_slots), ""), "请补充设备、商品或任务目标中的一个关键条件。"))
        return self._append(state, "planner", **values)

    @staticmethod
    def _after_plan(state):
        return {"call_tool": "tool", "answer": "compose", "handoff": "handoff", "ask_user": "persist"}[state["plan"].action]

    def _tool(self, state):
        req, plan = state["request"], state["plan"]
        tool = plan.tool or TOOL_BY_INTENT.get(plan.intent)
        summaries = list(state["observations"])
        before = len(summaries)
        try:
            if tool == "knowledge_search":
                result = self.agent._call_tool(tool, {"query": req.slots.get("query") or req.message,
                                                      **({"sku": req.slots["sku"]} if req.slots.get("sku") else {})}, req, state["request_id"], state["trace"], summaries)
                response = state.get("response") or self._response(state, "completed", "")
                if not result["chunks"] and not response.answer:
                    response = self._response(state, "handoff", "没有找到可核验的知识证据，请人工核实。", "knowledge_not_found")
                elif result["chunks"]:
                    excerpt = result["chunks"][0]
                    response.answer += f" 补充知识：{excerpt['text']}（证据：{excerpt['document_id']}/{excerpt['chunk_id']}）"
            else:
                handlers = {"product_search": self.agent._handle_product, "recommend_products": self.agent._handle_recommendation,
                            "compatibility_check": self.agent._handle_compatibility, "policy_search": self.agent._handle_policy,
                            "order_shipment_lookup": self.agent._handle_order, "create_simulated_ticket": self.agent._handle_ticket}
                response = handlers[tool](req, state["memory"], state["trace"], summaries, state["request_id"],
                                          **({"include_knowledge": False} if tool == "product_search" else {}))
                previous = state.get("response")
                if previous and previous.status == "completed" and response.status == "completed":
                    response.answer = previous.answer + "\n" + response.answer
                    response.recommendations = previous.recommendations + response.recommendations
        except (ToolError, KeyError, ValueError, TypeError):
            self.agent.store.increment("failure:ToolError")
            self.agent._trace(state["trace"], state["request_id"], req.thread_id, "validate_tool_result", "error", error_code="tool_error")
            response = self._response(state, "handoff", "工具未能返回安全、可验证的结果，已停止执行。", "tool_error")
        return self._append(state, "tool", response=response, observations=summaries,
                            steps=state["steps"] + len(summaries) - before,
                            seen=[*state["seen"], f"{tool}:{sorted(req.slots.items())}"])

    def _validate(self, state):
        response = state["response"]
        if response.status not in {"completed", "needs_input", "handoff"}:
            response = self._response(state, "handoff", "结果未通过安全校验，请人工核实。", "invalid_status")
        return self._append(state, "validate", response=response)

    @staticmethod
    def _after_validation(state):
        return {"completed": "planner", "needs_input": "persist", "handoff": "handoff"}[state["response"].status]

    def _compose(self, state):
        response = state["response"]
        response.answer, used = self.planner.compose(response.answer, state["observations"], response.status)
        self.agent._trace(state["trace"], state["request_id"], response.thread_id, "model_compose", "used" if used else "fallback")
        return self._append(state, "compose", response=response)

    def _handoff(self, state):
        return self._append(state, "handoff")

    def _persist(self, state):
        response, memory = state["response"], state["memory"]
        response.trace = state["trace"]
        response.tool_result_summary = state["observations"]
        response.multimodal = state.get("multimodal")
        plans = state["plans"]
        if plans:
            response.plan = {**plans[0], "steps": state["steps"], "actions": plans,
                             "model_version": self.planner.model.version, "prompt_version": "bounded-loop-v2",
                             "elapsed_ms": round((time.perf_counter() - state["started"]) * 1000, 2),
                             "usage": {k: v - state["usage_start"].get(k, 0) for k, v in self.planner.model.usage.items()}}
        if not self.agent._forget_memory_request(state["request"].message):
            memory["slots"] = dict(state["request"].slots)
            memory["intent"] = state["primary_intent"]
            memory["pending_input"] = response.status == "needs_input"
            memory["step_count"] = state["steps"]
            memory["messages"].append({"role": "assistant", "status": response.status})
            memory["last_tools"] = [{"tool": o["tool"], "ok": o["ok"], "citations": o.get("citations", [])} for o in state["observations"]]
        self.agent._compact_memory(memory)
        for node in [*state["graph_nodes"], "persist"]:
            self.agent._trace(response.trace, state["request_id"], response.thread_id, f"graph_{node}", "ok")
        memory["last_trace"] = response.trace[-80:]
        memory["last_status"] = response.status
        self.agent._save_state(response.thread_id, memory)
        self.agent.store.increment(response.status)
        return self._append(state, "persist", response=response, memory=memory)
