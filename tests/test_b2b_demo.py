from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from commerce_agent.api import create_app  # noqa: E402


class B2BDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def tearDown(self):
        self.client.app.state.agent.store.close()
        self.client.close()

    def test_widget_uses_merchant_scoped_synthetic_order(self):
        nova = self.client.post("/api/v1/widget/chat", json={
            "merchant_id": "demo-3c-store", "thread_id": "visitor-1", "message": "order tracking",
            "slots": {"order_id": "ORD-10023", "identity_suffix": "4821"},
        })
        self.assertEqual(nova.status_code, 200)
        self.assertIn("ORD-10023", nova.json()["answer"])
        cross_tenant = self.client.post("/api/v1/widget/chat", json={
            "merchant_id": "orbit-tech-store", "thread_id": "visitor-2", "message": "order tracking",
            "slots": {"order_id": "ORD-10023", "identity_suffix": "4821"},
        })
        self.assertEqual(cross_tenant.status_code, 200)
        self.assertEqual(cross_tenant.json()["status"], "handoff")

    def test_unknown_tenant_and_console_ticket_isolation(self):
        self.assertEqual(self.client.get("/api/v1/widget/config/unknown-store").status_code, 404)
        ticket = self.client.post("/api/v1/widget/chat", json={
            "merchant_id": "demo-3c-store", "thread_id": "visitor-3", "message": "human support ticket",
            "idempotency_key": "widget-ticket-0001",
        })
        self.assertEqual(ticket.status_code, 200)
        nova = self.client.post("/api/v1/demo/console/overview", json={"merchant_id": "demo-3c-store", "role": "support"})
        orbit = self.client.post("/api/v1/demo/console/overview", json={"merchant_id": "orbit-tech-store", "role": "support"})
        self.assertEqual(len(nova.json()["tickets"]), 1)
        self.assertEqual(orbit.json()["tickets"], [])
        ticket_id = nova.json()["tickets"][0]["ticket_id"]
        updated = self.client.patch(f"/api/v1/demo/console/tickets/{ticket_id}", json={"merchant_id": "demo-3c-store", "role": "support", "status": "simulated_resolved"})
        self.assertEqual(updated.status_code, 200)
        forbidden = self.client.patch(f"/api/v1/demo/console/tickets/{ticket_id}", json={"merchant_id": "demo-3c-store", "role": "operator", "status": "simulated_resolved"})
        self.assertEqual(forbidden.status_code, 403)


class B2BWebSourceTests(unittest.TestCase):
    def test_widget_and_console_use_same_origin_bff(self):
        web = ROOT / "src" / "web"
        self.assertIn('fetch("/api/widget/chat"', (web / "app" / "widget" / "page.tsx").read_text(encoding="utf-8"))
        self.assertIn('fetch("/api/merchant/overview"', (web / "app" / "console" / "page.tsx").read_text(encoding="utf-8"))
        self.assertTrue((web / "app" / "api" / "merchant" / "overview" / "route.ts").exists())


if __name__ == "__main__":
    unittest.main()
