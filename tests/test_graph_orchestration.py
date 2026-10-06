from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent
from commerce_agent.graph import CommerceGraph
from commerce_agent.models import ChatRequest
from commerce_agent.runtime import ModelAdapter


class GraphOrchestrationTests(unittest.TestCase):
    def test_repeated_product_lookup_completes_missing_evidence_once(self):
        import json
        def transport(payload):
            context = json.loads(payload["messages"][1]["content"])
            if "draft_answer" in context: return {"answer": context["draft_answer"]}
            return {"action": "answer" if len(context["observations"]) >= 2 else "call_tool",
                    "intent": "product", "slots": {}, "missing_slots": [], "reason_code": "test"}
        response = CommerceGraph(CommerceAgent(), model=ModelAdapter(transport=transport)).invoke(
            ChatRequest.from_dict({"thread_id": "repeat-product", "message": "AC-65W 商品参数"}), "repeat-product")
        self.assertEqual(response.status, "completed")
        self.assertEqual([item["tool"] for item in response.tool_result_summary], ["product_search", "knowledge_search"])
        self.assertTrue(any(item["node"] == "contract_guard" for item in response.trace))

    def test_planner_receives_identity_presence_not_identity_secret(self):
        import json
        contexts = []
        def transport(payload):
            context = json.loads(payload["messages"][1]["content"])
            contexts.append(context)
            return {"action": "ask_user", "intent": "order", "slots": {}, "missing_slots": [], "reason_code": "test"}
        CommerceGraph(CommerceAgent(), model=ModelAdapter(transport=transport)).invoke(
            ChatRequest.from_dict({"thread_id": "identity-context", "message": "order ORD-10023 suffix 4821",
                                  "idempotency_key": "private-key-12345"}), "identity-context")
        self.assertTrue(contexts[0]["task_context"]["identity_suffix_supplied"])
        self.assertTrue(contexts[0]["task_context"]["idempotency_key_supplied"])
        self.assertNotIn("4821", json.dumps(contexts))
        self.assertNotIn("private-key-12345", json.dumps(contexts))

    def test_model_cannot_finish_product_without_knowledge(self):
        def transport(payload):
            if "draft_answer" in payload["messages"][1]["content"]:
                return {"answer": ""}
            import json
            context = json.loads(payload["messages"][1]["content"])
            return {"action": "answer" if context["observations"] else "call_tool", "intent": "product",
                    "slots": {}, "missing_slots": [], "reason_code": "done"}
        response = CommerceGraph(CommerceAgent(), model=ModelAdapter(transport=transport)).invoke(
            ChatRequest.from_dict({"thread_id": "evidence-gate", "message": "AC-65W 商品参数"}), "evidence-gate")
        self.assertEqual([item["tool"] for item in response.tool_result_summary], ["product_search", "knowledge_search"])
        self.assertEqual(response.status, "completed")

    def test_memory_only_request_does_not_call_business_tools(self):
        agent = CommerceAgent()
        response = CommerceGraph(agent).invoke(ChatRequest.from_dict({"thread_id": "remember-only",
            "message": "记住我的设备", "slots": {"device": "iPhone 15"}}), "remember-only")
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.tool_result_summary, [])
        self.assertEqual(agent._load_state("remember-only")["preferences"]["device"], "iPhone 15")

    def test_unknown_device_requires_clarification_and_preserves_task(self):
        import json
        def transport(payload):
            context = json.loads(payload["messages"][1]["content"])
            if "draft_answer" in context:
                return {"answer": ""}
            return {"action": "answer" if context["observations"] else "call_tool", "intent": "recommendation",
                    "slots": {"device": "unknown"}, "missing_slots": [], "reason_code": "model_plan"}
        graph = CommerceGraph(CommerceAgent(), model=ModelAdapter(transport=transport))
        first = graph.invoke(ChatRequest.from_dict({"thread_id": "compat-followup", "message": "AC-65W 兼容吗？"}), "compat-1")
        self.assertEqual(first.status, "needs_input")
        self.assertEqual(first.tool_result_summary, [])
        second = graph.invoke(ChatRequest.from_dict({"thread_id": "compat-followup", "message": "MacBook Pro 14"}), "compat-2")
        self.assertEqual(second.status, "completed")
        self.assertEqual([item["tool"] for item in second.tool_result_summary], ["compatibility_check"])

    def test_graph_records_planner_tool_and_validation_nodes(self):
        graph = CommerceGraph(CommerceAgent())
        response = graph.invoke(ChatRequest.from_dict({"thread_id": "graph", "message": "charger"}), "graph-request")
        nodes = [entry["node"] for entry in response.trace]
        self.assertEqual(response.status, "completed")
        graph_nodes = [node for node in nodes if node.startswith("graph_")]
        self.assertEqual(graph_nodes, ["graph_guard_input", "graph_load_memory", "graph_planner", "graph_tool", "graph_validate",
                                      "graph_planner", "graph_tool", "graph_validate", "graph_planner", "graph_compose", "graph_persist"])
        self.assertEqual(response.plan["intent"], "product")

    def test_handoff_uses_explicit_terminal_node(self):
        graph = CommerceGraph(CommerceAgent())
        response = graph.invoke(ChatRequest.from_dict({"thread_id": "graph-risk", "message": "refund please"}), "graph-risk-request")
        self.assertEqual(response.status, "handoff")
        self.assertEqual(response.trace[-2]["node"], "graph_handoff")
        self.assertEqual(response.trace[-1]["node"], "graph_persist")

    def test_planner_handoff_action_is_executed_as_handoff(self):
        model = ModelAdapter(transport=lambda payload: {
            "action": "handoff",
            "intent": "handoff",
            "slots": {},
            "missing_slots": [],
            "reason_code": "protected_request",
        })
        response = CommerceGraph(CommerceAgent(), model=model).invoke(
            ChatRequest.from_dict({"thread_id": "planner-handoff", "message": "please ask a human"}),
            "req-planner-handoff",
        )
        self.assertEqual(response.status, "handoff")
        self.assertIn("graph_handoff", [item["node"] for item in response.trace])
