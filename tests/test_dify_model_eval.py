from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "eval"))

from run_dify_model_eval import build_report, expected_status, load_cases


class DifyModelEvaluationTests(unittest.TestCase):
    def test_all_migrated_dify_cases_are_loaded(self):
        cases = load_cases()
        self.assertEqual(len(cases), 145)
        self.assertEqual(cases[0]["case_id"], "E001")
        self.assertTrue(all(item["dataset"].startswith("dify_eval_") for item in cases))

    def test_dry_run_is_network_free_and_reports_scope(self):
        report = build_report(load_cases(), model=type("Disabled", (), {"version": "disabled"})(), live=False)
        self.assertEqual(report["mode"], "dry_run")
        self.assertEqual(report["total"], 145)
        self.assertEqual(report["merchant_connection"], "disabled")

    def test_expected_route_only_scores_explicit_dify_flags(self):
        self.assertEqual(expected_status({"should_handoff": "Y", "should_ask_followup": "N"}), "handoff")
        self.assertEqual(expected_status({"should_handoff": "N", "should_ask_followup": "Y"}), "needs_input")
        self.assertIsNone(expected_status({"should_handoff": "N", "should_ask_followup": "N"}))
