from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "eval"))

from run_rag_eval import evaluate, load_cases


class RagEvaluationTests(unittest.TestCase):
    def test_frozen_retrieval_set_has_full_recall_and_metadata_filtering(self):
        report = evaluate(load_cases())
        self.assertEqual(report["total"], 11)
        self.assertEqual(report["recall_at_k"], 1.0)
        self.assertEqual(report["metadata_filter_accuracy"], 1.0)
        self.assertEqual(report["empty_evidence_cases"], 1)


if __name__ == "__main__":
    unittest.main()
