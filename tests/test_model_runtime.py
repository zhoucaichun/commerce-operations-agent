from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent
from commerce_agent.graph import CommerceGraph
from commerce_agent.models import ChatRequest
from commerce_agent.runtime import ModelAdapter, Planner, production_readiness
from commerce_agent.connectors import DisabledShopifyConnector, MerchantConnectorError


class ModelRuntimeTests(unittest.TestCase):
    def test_unconfigured_model_uses_safe_deterministic_plan(self):
        plan = Planner(ModelAdapter()).plan("recommend a bundle for iPhone 15", {})
        self.assertFalse(plan.model_used)
        self.assertEqual(plan.intent, "recommendation")

    def test_invalid_model_authority_is_rejected(self):
        model = ModelAdapter(lambda _: {"action": "call_tool", "intent": "delete_orders", "slots": {}})
        plan = Planner(model).plan("please help", {})
        self.assertFalse(plan.model_used)
        self.assertEqual(plan.intent, "product")

    def test_model_plan_is_schema_checked_and_cannot_skip_tools(self):
        model = ModelAdapter(lambda _: {"action": "call_tool", "intent": "recommendation", "slots": {"device": "iPhone 15"}, "missing_slots": [], "reason_code": "test"})
        graph = CommerceGraph(CommerceAgent(), model=model)
        response = graph.invoke(ChatRequest.from_dict({"thread_id": "model-plan", "message": "recommend accessories"}), "model-plan-request")
        self.assertTrue(response.plan["model_used"])
        self.assertEqual(response.plan["intent"], "recommendation")
        self.assertTrue(any(item["tool"] == "recommend_products" for item in response.tool_result_summary))

    def test_qwen_schema_mode_is_explicit_and_still_uses_local_validation(self):
        received = []
        with patch.dict("os.environ", {"COMMERCE_LLM_PROVIDER": "qwen_openai_compatible", "COMMERCE_LLM_RESPONSE_MODE": "json_schema"}, clear=False):
            model = ModelAdapter(lambda payload: received.append(payload) or {"action": "call_tool", "intent": "product", "slots": {}, "missing_slots": [], "reason_code": "test"})
            plan = Planner(model).plan("show chargers", {})
        self.assertTrue(plan.model_used)
        self.assertEqual(model.version, "qwen_openai_compatible:test-model")
        self.assertEqual(received[0]["response_format"]["type"], "json_schema")
        self.assertTrue(received[0]["response_format"]["json_schema"]["strict"])

    def test_adapter_reports_only_safe_failure_categories(self):
        model = ModelAdapter(lambda _: (_ for _ in ()).throw(OSError("do not expose endpoint details")))
        self.assertIsNone(model.complete_json("system", "user"))
        self.assertEqual(model.diagnostics["attempted"], 1)
        self.assertEqual(model.diagnostics["transport_error"], 1)
        self.assertNotIn("do not expose endpoint details", str(model.diagnostics))

    def test_invalid_model_plan_records_local_schema_rejection(self):
        model = ModelAdapter(lambda _: {"intent": "product"})
        plan = Planner(model).plan("show chargers", {})
        self.assertFalse(plan.model_used)
        self.assertEqual(model.diagnostics["planner_schema_rejected"], 1)

    def test_memory_requires_explicit_remember_and_can_be_deleted(self):
        agent = CommerceAgent()
        agent.handle(ChatRequest.from_dict({"thread_id": "memory", "message": "remember my device", "slots": {"device": "iPhone 15"}}))
        self.assertEqual(agent._load_state("memory")["preferences"]["device"], "iPhone 15")
        response = agent.handle(ChatRequest.from_dict({"thread_id": "memory", "message": "delete my memory"}))
        self.assertEqual(response.status, "completed")
        self.assertEqual(agent._load_state("memory")["slots"], {})

    def test_readiness_never_claims_live_operations(self):
        self.assertIn("llm_configured", production_readiness())

    def test_live_merchant_connector_is_disabled_without_authorization(self):
        connector = DisabledShopifyConnector()
        self.assertEqual(connector.readiness()["status"], "disabled")
        with self.assertRaises(MerchantConnectorError):
            connector.sync_catalogue("demo-tenant")
