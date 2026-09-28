"""Opt-in PostgreSQL repository integration tests for isolated synthetic data."""

import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.postgres_store import PostgresStore


@unittest.skipUnless(os.getenv("COMMERCE_POSTGRES_DSN"), "requires isolated COMMERCE_POSTGRES_DSN")
class PostgresRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ["COMMERCE_POSTGRES_DSN"]
        self.store = PostgresStore(self.dsn)

    def tearDown(self):
        self.store.close()

    def test_synthetic_catalog_policy_and_order_seeds_are_complete(self):
        self.assertEqual({item["sku"] for item in self.store.products}, {"AC-65W", "AC-100W", "CB-C2C-2M"})
        self.assertEqual({item["topic"] for item in self.store.policies}, {"return", "warranty"})
        self.assertEqual(self.store.orders["ORD-10023"]["identity_suffix"], "4821")

    def test_ticket_and_session_survive_new_repository_instance(self):
        thread_id = "postgres-repository-test"
        key = "postgres-ticket-test-001"
        state = {"thread_id": thread_id, "messages": [], "slots": {"region": "CN"}, "step_count": 1}
        self.store.save_session(thread_id, state)
        first = self.store.create_ticket(key, {"category": "test", "summary": "synthetic only", "evidence": []})
        reloaded = PostgresStore(self.dsn)
        try:
            self.assertEqual(reloaded.session(thread_id), state)
            self.assertEqual(reloaded.create_ticket(key, {"category": "test", "summary": "synthetic only", "evidence": []})["ticket_id"], first["ticket_id"])
        finally:
            reloaded.close()
