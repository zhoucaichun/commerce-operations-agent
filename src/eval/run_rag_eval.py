"""Offline retrieval evaluation for the repository-local synthetic RAG.

This evaluates retrieval and evidence behavior separately from LLM answer
quality.  It is deliberately network-free and writes no merchant data.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any


SRC = Path(__file__).resolve().parents[1]
BACKEND = SRC / "backend"
DATA = Path(__file__).resolve().parent / "data"
sys.path.insert(0, str(BACKEND))

from commerce_agent.store import InMemoryStore
from commerce_agent.tools import ToolRegistry


DATASET = DATA / "rag_retrieval_eval_v1.csv"


def load_cases(dataset: Path = DATASET) -> list[dict[str, str]]:
    with dataset.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def evaluate(cases: list[dict[str, str]], top_k: int = 4) -> dict[str, Any]:
    tools = ToolRegistry(InMemoryStore())
    rows: list[dict[str, Any]] = []
    for case in cases:
        result = tools.invoke("policy_search", {"topic": case["topic"], "region": case["region"], "query": case["query"]})
        citations = result["citations"][:top_k]
        ids = [item["document_id"] for item in citations]
        expected_empty = case["expected_empty"] == "Y"
        target = case["target_document_id"]
        if expected_empty:
            passed, reciprocal_rank = not ids, 1.0 if not ids else 0.0
        else:
            rank = ids.index(target) + 1 if target in ids else None
            passed, reciprocal_rank = rank is not None, 1.0 / rank if rank else 0.0
        regions = [str(item["metadata"].get("region", "GLOBAL")).upper() for item in citations]
        allowed_regions = {case["region"].upper(), "GLOBAL"}
        filter_passed = all(region in allowed_regions for region in regions)
        rows.append({"case_id": case["case_id"], "target_document_id": target or None, "expected_empty": expected_empty, "retrieved_document_ids": ids, "passed": passed, "reciprocal_rank": reciprocal_rank, "filter_passed": filter_passed, "retrieval_mode": result["retrieval"]["retrieval_mode"]})
    total = len(rows)
    return {
        "suite": "rag_retrieval_eval",
        "dataset": DATASET.name,
        "synthetic_data_only": True,
        "merchant_connection": "disabled",
        "total": total,
        "recall_at_k": sum(row["passed"] for row in rows) / total if total else 0.0,
        "mrr_at_k": sum(row["reciprocal_rank"] for row in rows) / total if total else 0.0,
        "metadata_filter_accuracy": sum(row["filter_passed"] for row in rows) / total if total else 0.0,
        "empty_evidence_cases": sum(row["expected_empty"] for row in rows),
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be positive")
    report = evaluate(load_cases(), args.top_k)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, ensure_ascii=False))
    if report["recall_at_k"] < 1 or report["metadata_filter_accuracy"] < 1:
        raise SystemExit("RAG retrieval evaluation failed")


if __name__ == "__main__":
    main()
