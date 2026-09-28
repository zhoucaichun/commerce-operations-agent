"""Explicit LangGraph orchestration for the synthetic Commerce Agent."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agent import CommerceAgent
from .models import AgentResponse, ChatRequest


class CommerceGraphState(TypedDict, total=False):
    request: ChatRequest
    request_id: str
    plan: str
    response: AgentResponse
    graph_nodes: list[str]


class CommerceGraph:
    """Planner -> controlled tools -> validation -> optional handoff graph.

    The tool execution remains in :class:`CommerceAgent`, which owns the
    allow-list, identity checks and simulated-write idempotency rules.
    """

    def __init__(self, agent: CommerceAgent) -> None:
        self.agent = agent
        graph = StateGraph(CommerceGraphState)
        graph.add_node("guard_input", self._guard_input)
        graph.add_node("planner", self._planner)
        graph.add_node("tool", self._tool)
        graph.add_node("validate", self._validate)
        graph.add_node("handoff", self._handoff)
        graph.add_edge(START, "guard_input")
        graph.add_edge("guard_input", "planner")
        graph.add_edge("planner", "tool")
        graph.add_edge("tool", "validate")
        graph.add_conditional_edges("validate", self._route_after_validation, {"handoff": "handoff", "end": END})
        graph.add_edge("handoff", END)
        self._compiled = graph.compile()

    def invoke(self, request: ChatRequest, request_id: str) -> AgentResponse:
        state = self._compiled.invoke({"request": request, "request_id": request_id, "graph_nodes": []})
        response = state["response"]
        for node in state["graph_nodes"]:
            self.agent._trace(response.trace, request_id, request.thread_id, f"graph_{node}", "ok")
        return response

    @staticmethod
    def _append(state: CommerceGraphState, node: str, **values: Any) -> dict[str, Any]:
        return {"graph_nodes": [*state.get("graph_nodes", []), node], **values}

    def _guard_input(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "guard_input")

    def _planner(self, state: CommerceGraphState) -> dict[str, Any]:
        message = state["request"].message.lower()
        plan = "controlled_lookup" if any(token in message for token in ("order", "tracking", "charger", "policy", "ticket")) else "controlled_classification"
        return self._append(state, "planner", plan=plan)

    def _tool(self, state: CommerceGraphState) -> dict[str, Any]:
        response = self.agent.handle(state["request"], request_id=state["request_id"])
        return self._append(state, "tool", response=response)

    def _validate(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "validate")

    @staticmethod
    def _route_after_validation(state: CommerceGraphState) -> str:
        return "handoff" if state["response"].status == "handoff" else "end"

    def _handoff(self, state: CommerceGraphState) -> dict[str, Any]:
        return self._append(state, "handoff")
