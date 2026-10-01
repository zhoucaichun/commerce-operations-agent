"""Explicit, bounded LangGraph loop for the Commerce Agent."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agent import CommerceAgent
from .models import AgentResponse, ChatRequest
from .runtime import ActionPlan, ModelAdapter, Planner


class CommerceGraphState(TypedDict, total=False):
    request: ChatRequest
    request_id: str
    plan: ActionPlan
    response: AgentResponse
    graph_nodes: list[str]


class CommerceGraph:
    """Guard -> memory -> typed plan -> controlled tool -> validate -> compose -> persist."""

    def __init__(self, agent: CommerceAgent, model: ModelAdapter | None = None) -> None:
        self.agent = agent
        self.planner = Planner(model)
        graph = StateGraph(CommerceGraphState)
        for name, handler in (
            ("guard_input", self._guard_input), ("load_memory", self._load_memory),
            ("planner", self._planner), ("tool", self._tool), ("validate", self._validate),
            ("compose", self._compose), ("handoff", self._handoff), ("persist", self._persist),
        ):
            graph.add_node(name, handler)
        graph.add_edge(START, "guard_input")
        graph.add_edge("guard_input", "load_memory")
        graph.add_edge("load_memory", "planner")
        graph.add_edge("planner", "tool")
        graph.add_edge("tool", "validate")
        graph.add_conditional_edges("validate", self._route_after_validation, {"handoff": "handoff", "compose": "compose"})
        graph.add_edge("handoff", "persist")
        graph.add_edge("compose", "persist")
        graph.add_edge("persist", END)
        self._compiled = graph.compile()

    def invoke(self, request: ChatRequest, request_id: str) -> AgentResponse:
        state = self._compiled.invoke({"request": request, "request_id": request_id, "graph_nodes": []})
        response = state["response"]
        response.plan = state["plan"].as_dict()
        for node in state["graph_nodes"]:
            self.agent._trace(response.trace, request_id, request.thread_id, f"graph_{node}", "ok")
        return response

    @staticmethod
    def _append(state: CommerceGraphState, node: str, **values: Any) -> dict[str, Any]:
        return {"graph_nodes": [*state.get("graph_nodes", []), node], **values}

    def _guard_input(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "guard_input")

    def _load_memory(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "load_memory")

    def _planner(self, state: CommerceGraphState) -> dict[str, Any]:
        request = state["request"]
        memory = self.agent._load_state(request.thread_id)
        plan = self.planner.plan(request.message, {**memory.get("slots", {}), **request.slots})
        return self._append(state, "planner", plan=plan)

    def _tool(self, state: CommerceGraphState) -> dict[str, Any]:
        request, plan = state["request"], state["plan"]
        merged_request = ChatRequest(thread_id=request.thread_id, message=request.message, slots={**request.slots, **plan.slots}, attachments=request.attachments, idempotency_key=request.idempotency_key)
        response = self.agent.handle(merged_request, request_id=state["request_id"], planned_intent=plan.intent)
        self.agent._trace(response.trace, state["request_id"], request.thread_id, "model_planner", "used" if plan.model_used else "fallback", error_code=plan.reason_code)
        return self._append(state, "tool", response=response)

    def _validate(self, state: CommerceGraphState) -> dict[str, Any]:
        response = state["response"]
        if response.status not in {"completed", "needs_input", "handoff"}:
            response.status, response.answer = "handoff", "The request could not be validated safely and needs human review."
        return self._append(state, "validate")

    @staticmethod
    def _route_after_validation(state: CommerceGraphState) -> str:
        return "handoff" if state["response"].status == "handoff" else "compose"

    def _compose(self, state: CommerceGraphState) -> dict[str, Any]:
        response = state["response"]
        answer, used = self.planner.compose(response.answer, response.recommendations or response.tool_result_summary, response.status)
        response.answer = answer
        self.agent._trace(response.trace, state["request_id"], response.thread_id, "model_compose", "used" if used else "fallback")
        return self._append(state, "compose", response=response)

    def _handoff(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "handoff")

    def _persist(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "persist")
