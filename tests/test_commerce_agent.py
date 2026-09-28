import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent  # noqa: E402
from commerce_agent.models import ChatRequest, ValidationError  # noqa: E402
from commerce_agent.store import InMemoryStore  # noqa: E402
from commerce_agent.tools import ToolError, ToolRegistry  # noqa: E402


class CommerceAgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = CommerceAgent(InMemoryStore())

    def request(self, message, **payload):
        body = {"thread_id": "test-thread", "message": message, **payload}
        return self.agent.handle(ChatRequest.from_dict(body))

    def test_order_requires_identity_suffix_and_then_returns_synthetic_result(self):
        missing = self.request("查一下订单 ORD-10023 的物流")
        self.assertEqual(missing.status, "needs_input")
        self.assertIn("后四位", missing.answer)

        complete = self.request("查一下订单 ORD-10023 的物流，后四位 4821")
        self.assertEqual(complete.status, "completed")
        self.assertIn("SIM-TRK-10023", complete.answer)
        self.assertEqual(complete.request_id.startswith("req_"), True)
        self.assertTrue(any(item["node"] == "validate_tool_result" for item in complete.trace))

    def test_compatibility_uses_rule_result(self):
        response = self.request("AC-65W 能兼容 MacBook Pro 14 吗？")
        self.assertEqual(response.status, "completed")
        self.assertIn("兼容", response.answer)
        self.assertEqual(response.tool_result_summary[0]["tool"], "compatibility_check")

    def test_policy_is_evidence_based(self):
        response = self.request("CN 的退货政策是什么？")
        self.assertEqual(response.status, "completed")
        self.assertIn("Synthetic policy", response.answer)
        self.assertEqual(response.tool_result_summary[0]["tool"], "policy_search")

    def test_real_mutations_are_handed_off_without_tool_call(self):
        response = self.request("请直接修改地址并取消订单")
        self.assertEqual(response.status, "handoff")
        self.assertEqual(response.handoff["required"], True)
        self.assertEqual(response.tool_result_summary, [])
        self.assertIn("不能", response.answer)

    def test_simulated_ticket_requires_idempotency_and_deduplicates(self):
        missing = self.request("请转人工客服建立工单")
        self.assertEqual(missing.status, "needs_input")

        first = self.request("请转人工客服建立工单", idempotency_key="ticket-test-001")
        second = self.request("请转人工客服建立工单", idempotency_key="ticket-test-001")
        self.assertEqual(first.status, "completed")
        self.assertEqual(second.status, "completed")
        self.assertIn("SIM-TKT-0001", first.answer)
        self.assertIn("重复请求已复用", second.answer)

    def test_input_and_tool_boundaries(self):
        with self.assertRaises(ValidationError):
            ChatRequest.from_dict({"thread_id": "bad id", "message": "hello"})
        with self.assertRaises(ValidationError):
            ChatRequest.from_dict({"thread_id": "ok", "message": ""})
        with self.assertRaises(ToolError):
            ToolRegistry(InMemoryStore()).invoke("delete_real_order", {})


if __name__ == "__main__":
    unittest.main()
