from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/backend"))
from commerce_agent.agent import CommerceAgent
from commerce_agent.graph import CommerceGraph
from commerce_agent.models import ChatRequest
from commerce_agent.runtime import ModelAdapter, Planner
from commerce_agent.embeddings import SemanticEmbedder, EmbeddingError
from commerce_agent.tools import ToolRegistry, ToolDefinition, ToolError, TransientToolError
from commerce_agent.store import InMemoryStore


def request(message, thread="bounded", **kwargs):
    return ChatRequest.from_dict({"thread_id": thread, "message": message, **kwargs})


def plan(action="call_tool", intent="product", **kwargs):
    return {"action": action, "intent": intent, "slots": {}, "missing_slots": [], "reason_code": "test", **kwargs}


class BoundedAgentTests(unittest.TestCase):
    def test_knowledge_tool_receives_explicit_region(self):
        def transport(payload):
            context = json.loads(payload["messages"][1]["content"])
            if "draft_answer" in context:
                return {"answer": context["draft_answer"]}
            return plan("answer") if context["observations"] else plan(intent="policy", tool="knowledge_search")
        result = CommerceGraph(CommerceAgent(), ModelAdapter(transport)).invoke(request("shipping US"), "req-region")
        retrieval = result.tool_result_summary[0]["evidence"]["retrieval"]
        self.assertEqual(retrieval["filters"]["region"], "US")
        self.assertTrue(all(chunk["citation"]["metadata"].get("region", "GLOBAL") in {"US", "GLOBAL"} for chunk in retrieval["chunks"]))

    def test_bundle_budget_is_total_and_not_per_component(self):
        store = InMemoryStore()
        store.products = [
            {"sku": "C", "name": "charger", "category": "charger", "price_usd": 30, "regions": ["US"]},
            {"sku": "L", "name": "cable", "category": "cable", "price_usd": 10, "regions": ["US"]},
        ]
        tools = ToolRegistry(store)
        args = {"query": "charging bundle", "country": "US", "budget": "35"}
        self.assertEqual(tools.invoke("recommend_products", args)["products"], [])
        args["budget"] = "40"
        self.assertEqual(len(tools.invoke("recommend_products", args)["products"]), 2)

    def test_composer_cannot_invent_expanded_catalog_sku(self):
        planner = Planner(ModelAdapter(lambda _: {"answer": "Buy SP-FAKE-999"}))
        self.assertEqual(planner.compose("Buy AC-65W", [], "completed"), ("Buy AC-65W", False))

    def test_explicit_recommendation_is_not_a_compatibility_question(self):
        agent = CommerceAgent(model=ModelAdapter(allow_network=False))
        result = agent.handle(request("Recommend a charger for iPhone 15 under $50 in US"))
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tool_result_summary[0]["tool"], "recommend_products")

    def test_model_drives_two_tools_and_receives_real_observations(self):
        calls = []
        def transport(payload):
            context = json.loads(payload["messages"][1]["content"])
            calls.append(context)
            if "draft_answer" in context:
                return {"answer": context["draft_answer"]}
            count = len(context["observations"])
            return [plan(tool="product_search", slots={"query": "charger"}),
                    plan(tool="policy_search", intent="policy", slots={"topic": "shipping", "country": "US"}),
                    plan(action="answer")][count]
        graph = CommerceGraph(CommerceAgent(), model=ModelAdapter(transport))
        result = graph.invoke(request("charger and shipping"), "req-loop")
        self.assertEqual(result.status, "completed")
        self.assertEqual([o["tool"] for o in result.tool_result_summary], ["product_search", "policy_search"])
        self.assertIn("products", calls[1]["observations"][0]["evidence"])
        self.assertEqual(result.plan["steps"], 2)
        self.assertTrue(result.plan["model_used"])
        self.assertEqual(graph.agent.store.metrics()["chat_requests"], 1)

    def test_ask_user_does_not_execute_a_tool(self):
        model = ModelAdapter(lambda _: plan("ask_user", "compatibility", missing_slots=["device"]))
        result = CommerceGraph(CommerceAgent(), model).invoke(request("compatibility"), "req-ask")
        self.assertEqual(result.status, "needs_input")
        self.assertEqual(result.tool_result_summary, [])

    def test_repeated_action_hands_off_instead_of_spinning(self):
        result = CommerceGraph(CommerceAgent(), ModelAdapter(lambda _: plan())).invoke(request("charger"), "req-repeat")
        self.assertEqual(result.status, "handoff")
        self.assertEqual(result.handoff["reason"], "repeated_tool_action")
        self.assertEqual(len(result.tool_result_summary), 1)

    def test_six_tool_limit_is_per_task_not_lifetime(self):
        def transport(payload):
            context = json.loads(payload["messages"][1]["content"])
            return plan(slots={"query": f"charger {len(context['observations'])}"})
        result = CommerceGraph(CommerceAgent(), ModelAdapter(transport)).invoke(request("help"), "req-limit")
        self.assertEqual(result.plan["steps"], 6)
        self.assertEqual(result.handoff["reason"], "max_steps_reached")
        agent = CommerceAgent(model=ModelAdapter(allow_network=False))
        for _ in range(8):
            self.assertEqual(agent.handle(request("charger", thread="long-session")).status, "completed")

    def test_model_cannot_invent_identity_or_bypass_tool_role(self):
        model = ModelAdapter(lambda _: plan(intent="order", slots={"order_id": "ORD-10023", "identity_suffix": "4821"}))
        result = CommerceGraph(CommerceAgent(), model).invoke(request("order ORD-10023"), "req-identity")
        self.assertNotEqual(result.status, "completed")
        self.assertFalse(result.tool_result_summary)
        restricted = CommerceGraph(CommerceAgent(), ModelAdapter(lambda _: plan(intent="order")))
        result = restricted.invoke(request("hello", slots={"order_id": "ORD-10023", "identity_suffix": "4821"}), "req-role", allowed_tools=["product_search"])
        self.assertEqual(result.handoff["reason"], "tool_permission_denied")

    def test_protected_operation_never_reaches_model(self):
        model = ModelAdapter(lambda _: self.fail("protected operation sent to model"))
        result = CommerceGraph(CommerceAgent(), model).invoke(request("cancel my order"), "req-risk")
        self.assertEqual(result.status, "handoff")
        self.assertEqual(result.tool_result_summary, [])

    def test_followup_and_explicit_device_override(self):
        agent = CommerceAgent(model=ModelAdapter(allow_network=False))
        self.assertEqual(agent.handle(request("AC-65W 兼容吗？", thread="follow")).status, "needs_input")
        result = agent.handle(request("MacBook Pro 14", thread="follow"))
        self.assertEqual(result.status, "completed")
        self.assertIn("MacBook Pro 14", result.answer)
        agent.handle(request("改成 iPhone 15", thread="follow"))
        self.assertEqual(agent._load_state("follow")["slots"]["device"], "iPhone 15")
        self.assertNotIn("device", agent._load_state("other")["slots"])

    def test_new_order_does_not_reuse_previous_identity(self):
        agent = CommerceAgent(model=ModelAdapter(allow_network=False))
        agent.handle(request("订单 ORD-10023 后四位 4821"))
        result = agent.handle(request("订单 ORD-20000"))
        self.assertEqual(result.status, "needs_input")
        self.assertNotIn("identity_suffix", agent._load_state("bounded")["slots"])

    def test_composer_rejects_new_prices_and_skus(self):
        composer = Planner(ModelAdapter(lambda _: {"answer": "SKU999 only $0.01"}))
        text, used = composer.compose("SKU001 costs $19.99", [{"sku": "SKU001", "price_usd": 19.99}], "completed")
        self.assertFalse(used)
        self.assertIn("19.99", text)

    def test_identity_suffix_is_not_sent_to_model(self):
        calls = []
        def transport(payload):
            calls.append(str(payload))
            context = json.loads(payload["messages"][1]["content"])
            if "draft_answer" in context:
                return {"answer": context["draft_answer"]}
            return plan("answer" if context["observations"] else "call_tool", "order")
        CommerceGraph(CommerceAgent(), ModelAdapter(transport)).invoke(request("订单 ORD-10023 后四位 4821"), "req-redact")
        self.assertNotIn("4821", "".join(calls))


class ToolAndEmbeddingTests(unittest.TestCase):
    def test_batch_ceiling_and_content_cache(self):
        batches = []
        def transport(payload):
            batches.append(len(payload["input"]))
            return {"data": [{"index": i, "embedding": [1, 2]} for i in range(len(payload["input"]))]}
        with patch.dict("os.environ", {"COMMERCE_EMBEDDING_BATCH_SIZE": "8"}):
            embedder = SemanticEmbedder(transport=transport)
            embedder.embed_many([str(i) for i in range(21)])
            embedder.embed_many([str(i) for i in range(21)])
            self.assertEqual(batches, [8, 8, 5])
            embedder.db.close()

    def test_invalid_embedding_shape_is_not_cached(self):
        embedder = SemanticEmbedder(transport=lambda _: {"data": [{"index": 0, "embedding": [float("nan")]}]})
        with self.assertRaises(EmbeddingError):
            embedder.embed("unsafe")
        self.assertEqual(embedder.db.execute("SELECT count(*) FROM vectors").fetchone()[0], 0)
        embedder.db.close()

    def test_only_transient_reads_retry(self):
        tools = ToolRegistry(InMemoryStore())
        calls = []
        def handler(_):
            calls.append(1)
            raise ToolError("invalid arguments")
        tools._tools["product_search"] = ToolDefinition("product_search", "test", True, False, ("query",), handler)
        with self.assertRaises(ToolError):
            tools.execute("product_search", {"query": "x"})
        self.assertEqual(len(calls), 1)
        calls.clear()
        def transient(_):
            calls.append(1)
            if len(calls) == 1:
                raise TransientToolError("temporary")
            return {"products": []}
        tools._tools["product_search"] = ToolDefinition("product_search", "test", True, False, ("query",), transient)
        self.assertEqual(tools.execute("product_search", {"query": "x"}), {"products": []})
        self.assertEqual(len(calls), 2)
