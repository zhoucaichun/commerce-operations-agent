from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent
from commerce_agent.models import ChatRequest
from commerce_agent.store import InMemoryStore
from commerce_agent.tools import ToolRegistry


class HybridRagPipelineTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryStore()
        self.tools = ToolRegistry(self.store)

    def test_corpus_is_substantially_larger_than_migrated_dify_seed(self):
        self.assertGreaterEqual(len(self.store.products), 270)
        self.assertGreaterEqual(len(self.tools.retriever.chunks), 300)
        self.assertEqual(self.tools.retriever.embedder.mode, "local_hashing_demo")

    def test_policy_retrieval_uses_region_as_hard_filter_and_returns_versioned_citation(self):
        result = self.tools.invoke("policy_search", {"topic": "shipping", "region": "US", "query": "How long does standard delivery take?"})
        self.assertTrue(result["policies"])
        self.assertEqual(result["policies"][0]["region"], "US")
        self.assertEqual(result["citations"][0]["document_id"], "policy:POL001")
        self.assertEqual(result["retrieval"]["retrieval_mode"], "local_hashing_demo")

    def test_policy_topic_aliases_preserve_dify_return_and_promo_records(self):
        returned = self.tools.invoke("policy_search", {"topic": "return", "region": "US", "query": "return window"})
        promoted = self.tools.invoke("policy_search", {"topic": "promotion", "region": "US", "query": "bundle discount"})
        self.assertTrue(returned["policies"])
        self.assertTrue(promoted["policies"])

    def test_region_specific_policy_ranks_before_global_fallback(self):
        result = self.tools.invoke("policy_search", {"topic": "return", "region": "CN", "query": "CN 的退货政策"})
        self.assertEqual(result["policies"][0]["region"], "CN")

    def test_policy_does_not_fabricate_when_no_applicable_evidence_exists(self):
        result = self.tools.invoke("policy_search", {"topic": "battery_recycling", "region": "BR", "query": "battery recycling rule"})
        self.assertEqual(result["policies"], [])

    def test_agent_trace_and_answer_keep_retrieval_evidence(self):
        agent = CommerceAgent(self.store)
        response = agent.handle(ChatRequest.from_dict({"thread_id": "rag-policy", "message": "How long is standard shipping to US?", "slots": {"country": "US"}}))
        self.assertEqual(response.status, "completed")
        self.assertIn("policy:POL001", response.answer)
        self.assertEqual(response.tool_result_summary[0]["tool"], "policy_search")
        self.assertTrue(response.tool_result_summary[0]["citations"])
        self.assertTrue(any(item["node"] == "retrieval_evidence" for item in response.trace))


if __name__ == "__main__":
    unittest.main()
