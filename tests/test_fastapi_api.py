from pathlib import Path
import os
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from commerce_agent.api import build_agent, create_app  # noqa: E402


class FastApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        database_path = str(Path(self.temp.name) / "commerce.sqlite")
        self.client = TestClient(create_app(build_agent(database_path)))

    def tearDown(self):
        self.client.app.state.agent.store.close()
        self.client.close()
        self.temp.cleanup()

    def test_health_ready_and_request_id(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Commerce Operations Agent", page.text)
        self.assertIn("default-src 'self'", page.headers["Content-Security-Policy"])
        self.assertEqual(page.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(page.headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(self.client.get("/assets/app.js").status_code, 200)
        self.assertEqual(self.client.get("/health").json()["status"], "ok")
        self.assertEqual(self.client.get("/ready").json()["status"], "ready")
        response = self.client.post(
            "/api/v1/chat",
            headers={"X-Request-ID": "api-request-001"},
            json={"thread_id": "api-thread", "message": "查订单 ORD-10023 物流，后四位 4821"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "api-request-001")
        self.assertEqual(response.json()["request_id"], "api-request-001")

    def test_schema_rejects_unknown_fields_and_risk_is_handed_off(self):
        invalid = self.client.post("/api/v1/chat", json={"thread_id": "x", "message": "hi", "unknown": True})
        self.assertEqual(invalid.status_code, 422)
        risk = self.client.post("/api/v1/chat", json={"thread_id": "risk", "message": "请直接退款"})
        self.assertEqual(risk.status_code, 200)
        self.assertEqual(risk.json()["status"], "handoff")
        self.assertEqual(risk.json()["tool_result_summary"], [])

    def test_sqlite_ticket_is_idempotent_across_agent_restarts(self):
        payload = {"thread_id": "ticket", "message": "请转人工客服建立工单", "idempotency_key": "api-ticket-001"}
        first = self.client.post("/api/v1/chat", json=payload).json()
        reloaded = TestClient(create_app(build_agent(self.client.app.state.agent.store.database_path)))
        second = reloaded.post("/api/v1/chat", json=payload).json()
        self.assertIn("SIM-TKT-0001", first["answer"])
        self.assertIn("重复请求已复用", second["answer"])
        reloaded.app.state.agent.store.close()
        reloaded.close()

    def test_synthetic_bearer_auth_and_roles(self):
        previous_required = os.environ.get("COMMERCE_AUTH_REQUIRED")
        previous_tokens = os.environ.get("COMMERCE_DEMO_TOKENS")
        os.environ["COMMERCE_AUTH_REQUIRED"] = "true"
        os.environ["COMMERCE_DEMO_TOKENS"] = '{"viewer-token":{"subject":"synthetic-viewer","role":"viewer"},"support-token":{"subject":"synthetic-support","role":"support"}}'
        secured = TestClient(create_app(build_agent(str(Path(self.temp.name) / "secured.sqlite"))))
        try:
            self.assertEqual(secured.post("/api/v1/chat", json={"thread_id": "auth", "message": "charger"}).status_code, 401)
            self.assertEqual(secured.post("/api/v1/chat", headers={"Authorization": "Bearer viewer-token"}, json={"thread_id": "auth", "message": "charger"}).status_code, 200)
            self.assertEqual(secured.post("/api/v1/chat", headers={"Authorization": "Bearer viewer-token"}, json={"thread_id": "auth-order", "message": "order ORD-10023 tracking 4821"}).status_code, 403)
            self.assertEqual(secured.post("/api/v1/chat", headers={"Authorization": "Bearer support-token"}, json={"thread_id": "auth-order", "message": "order ORD-10023 tracking 4821"}).status_code, 200)
        finally:
            secured.app.state.agent.store.close()
            secured.close()
            if previous_required is None: os.environ.pop("COMMERCE_AUTH_REQUIRED", None)
            else: os.environ["COMMERCE_AUTH_REQUIRED"] = previous_required
            if previous_tokens is None: os.environ.pop("COMMERCE_DEMO_TOKENS", None)
            else: os.environ["COMMERCE_DEMO_TOKENS"] = previous_tokens


if __name__ == "__main__":
    unittest.main()
