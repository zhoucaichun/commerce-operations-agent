from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent  # noqa: E402
from commerce_agent.models import ChatRequest  # noqa: E402
from commerce_agent.store import InMemoryStore  # noqa: E402


class DifyCatalogMigrationTests(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryStore()
        self.agent = CommerceAgent(self.store)

    def request(self, message, **slots):
        return self.agent.handle(ChatRequest.from_dict({"thread_id": f"migration-{len(message)}", "message": message, "slots": slots}))

    def test_packaged_source_has_expected_synthetic_records(self):
        self.assertEqual(len(self.store.products), 62)
        self.assertEqual(len(self.store.policies), 37)
        self.assertTrue(any(product["sku"] == "SKU005" for product in self.store.products))
        self.assertTrue(any(policy["source"] == "dify_synthetic_policy_migration" for policy in self.store.policies))

    def test_recommendation_uses_migrated_catalog_not_dify_runtime(self):
        response = self.request("I use an iPhone 15 and want a charger under $25", device_model="iPhone 15", country="US", budget="under $25")
        self.assertEqual(response.status, "completed")
        self.assertIn("SKU0", response.answer)
        self.assertNotIn("$49.90", response.answer)
        self.assertEqual(response.tool_result_summary[0]["tool"], "recommend_products")
        self.assertIn("no real Shopify catalogue", response.answer)

    def test_imported_sku_compatibility_and_policy_are_deterministic(self):
        compatibility = self.request("Will SKU005 work with MacBook Air M2?")
        self.assertEqual(compatibility.status, "completed")
        self.assertEqual(compatibility.tool_result_summary[0]["tool"], "compatibility_check")

        policy = self.request("How long is standard shipping to US?", country="US")
        self.assertEqual(policy.status, "completed")
        self.assertEqual(policy.tool_result_summary[0]["tool"], "policy_search")
        self.assertIn("dify_synthetic_policy_migration", policy.answer)


if __name__ == "__main__":
    unittest.main()
