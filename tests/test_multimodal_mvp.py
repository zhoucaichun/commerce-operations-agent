from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))
from commerce_agent.agent import CommerceAgent  # noqa: E402
from commerce_agent.models import ChatRequest, ValidationError  # noqa: E402


class MultimodalMvpTests(unittest.TestCase):
    def request(self, message, attachment):
        return CommerceAgent().handle(ChatRequest.from_dict({"thread_id": "multimodal-test", "message": message, "attachments": [attachment]}))

    def test_photo_enriches_compatibility_through_controlled_rule(self):
        response = self.request("Will this charger work?", {"kind": "image", "name": "charger-demo.jpg", "mime_type": "image/jpeg", "size_bytes": 1000, "demo_scenario": "macbook_charger"})
        self.assertEqual(response.status, "completed")
        self.assertEqual(response.tool_result_summary[0]["tool"], "compatibility_check")
        self.assertEqual(response.multimodal["mode"], "synthetic_metadata_only")

    def test_battery_image_hands_off_without_tool_execution(self):
        response = self.request("Is this safe?", {"kind": "image", "name": "battery-demo.jpg", "mime_type": "image/jpeg", "size_bytes": 1000, "demo_scenario": "battery_damage"})
        self.assertEqual(response.status, "handoff")
        self.assertEqual(response.handoff["reason"], "attachment_battery_safety")
        self.assertEqual(response.tool_result_summary, [])

    def test_attachment_metadata_is_bounded(self):
        with self.assertRaises(ValidationError):
            ChatRequest.from_dict({"thread_id": "bad-attachment", "message": "hello", "attachments": [{"kind": "image", "name": "x.jpg", "mime_type": "image/jpeg", "size_bytes": 10000001}]})
