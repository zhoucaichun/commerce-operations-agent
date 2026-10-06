from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/backend"))
from fastapi.testclient import TestClient
from commerce_agent.api import create_app
from commerce_agent.agent import CommerceAgent
from commerce_agent.auth import SyntheticAuthenticator
from commerce_agent.runtime import ModelAdapter


class ApiSecurityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(CommerceAgent(model=ModelAdapter(allow_network=False))))
        self.client.app.state.authenticator = SyntheticAuthenticator(required=True, tokens={
            "a": {"subject": "a", "role": "support", "merchant_ids": ["demo-3c-store"]},
            "b": {"subject": "b", "role": "support", "merchant_ids": ["orbit-tech-store"]},
        })

    def tearDown(self):
        self.client.close()

    def test_widget_requires_auth_and_tenant_binding(self):
        body = {"merchant_id": "demo-3c-store", "thread_id": "visitor", "message": "charger"}
        self.assertEqual(self.client.post("/api/v1/widget/chat", json=body).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/widget/chat", json=body, headers={"Authorization": "Bearer b"}).status_code, 403)

    def test_widget_uses_rate_and_duplicate_request_guards(self):
        body = {"merchant_id": "demo-3c-store", "thread_id": "visitor", "message": "charger", "idempotency_key": "request-001"}
        headers = {"Authorization": "Bearer a"}
        guard = self.client.app.state.redis_health
        with patch.object(guard, "allow", return_value=False):
            self.assertEqual(self.client.post("/api/v1/widget/chat", json=body, headers=headers).status_code, 429)
        with patch.object(guard, "acquire_idempotency_lock", return_value=False):
            self.assertEqual(self.client.post("/api/v1/widget/chat", json=body, headers=headers).status_code, 409)

    def test_same_thread_and_idempotency_keys_are_scoped_by_subject(self):
        body = {"thread_id": "shared", "message": "create a human ticket", "idempotency_key": "same-ticket-key"}
        a = self.client.post("/api/v1/chat", json=body, headers={"Authorization": "Bearer a"}).json()
        b = self.client.post("/api/v1/chat", json=body, headers={"Authorization": "Bearer b"}).json()
        self.assertNotEqual(a["thread_id"], b["thread_id"])
        self.assertNotEqual(a["tool_result_summary"][0]["evidence"]["ticket_id"], b["tool_result_summary"][0]["evidence"]["ticket_id"])

    def test_unsafe_request_id_is_replaced(self):
        response = self.client.get("/health", headers={"X-Request-ID": "<script>"})
        self.assertTrue(response.headers["X-Request-ID"].startswith("req_"))
