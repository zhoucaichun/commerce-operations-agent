from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "infra"))
from validate_production_docs import validate


class ProductionDocumentationTests(unittest.TestCase):
    def test_required_safety_guidance_is_present(self):
        self.assertEqual(validate(), [])
