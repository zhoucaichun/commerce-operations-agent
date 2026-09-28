from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
