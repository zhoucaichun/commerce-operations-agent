from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "infra"))

from validate_proxy_config import validate


class ProxyConfigTests(unittest.TestCase):
    def test_production_template_and_host_are_accepted(self):
        self.assertEqual(validate(ROOT / "src" / "infra" / "nginx" / "commerce-agent.conf", "agent.example.com"), [])

    def test_placeholder_host_is_rejected(self):
        self.assertTrue(validate(ROOT / "src" / "infra" / "nginx" / "commerce-agent.conf", "agent.example.invalid"))
