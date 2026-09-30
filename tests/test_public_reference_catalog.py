from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.agent import CommerceAgent
from commerce_agent.models import ChatRequest
from commerce_agent.store import InMemoryStore


class PublicReferenceCatalogueTests(unittest.TestCase):
    def test_public_reference_rows_are_labelled_and_traceable(self):
        store = InMemoryStore()
        rows = [product for product in store.products if product.get("source") == "public_reference_catalog"]
        self.assertGreaterEqual(len(rows), 4)
        self.assertTrue(all(product.get("source_url", "").startswith("https://") for product in rows))
        self.assertTrue(all(product.get("source_checked_at") == "2026-09-30" for product in rows))
        self.assertTrue(all(product.get("stock") == "not_connected" for product in rows))

    def test_bundle_ranking_avoids_car_charger_without_vehicle_context(self):
        agent = CommerceAgent(InMemoryStore())
        response = agent.handle(ChatRequest(thread_id="bundle-regression", message="Recommend a charging bundle for iPhone 15"))
        self.assertEqual(response.status, "completed")
        self.assertTrue(response.recommendations)
        self.assertNotIn("car charger", response.recommendations[0]["name"].lower())
        self.assertIn("no real Shopify catalogue", response.answer)


if __name__ == "__main__":
    unittest.main()
