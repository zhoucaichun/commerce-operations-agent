"""Opt-in model evaluation over the migrated Dify regression datasets.

This command is deliberately inert by default: ``--dry-run`` only validates
the datasets and writes a plan.  ``--live`` is required before a configured
model endpoint can receive any synthetic prompt.
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

from commerce_agent.agent import CommerceAgent
from commerce_agent.graph import CommerceGraph
from commerce_agent.models import ChatRequest
from commerce_agent.runtime import ModelAdapter
from commerce_agent.config import load_local_config


DATASETS = (
    "dify_eval_full_100.csv",
    "dify_eval_regression_30.csv",
    "dify_eval_regression_extra_15.csv",
)


def load_cases() -> list[dict[str, str]]:
    """Load only reviewed, repository-local synthetic Dify cases."""
    cases: list[dict[str, str]] = []
    for filename in DATASETS:
        # The historical full dataset was exported with a UTF-8 BOM; utf-8-sig
        # accepts it while remaining compatible with the other two exports.
        with (DATA / filename).open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                row["dataset"] = filename
                cases.append(row)
    return cases


def expected_status(row: dict[str, str]) -> str | None:
    if row.get("should_handoff") == "Y":
        return "handoff"
    if row.get("should_ask_followup") == "Y":
        return "needs_input"
    return None


def evaluate_live(cases: list[dict[str, str]], model: ModelAdapter) -> list[dict[str, Any]]:
    graph = CommerceGraph(CommerceAgent(), model=model)
    results: list[dict[str, Any]] = []
    for index, row in enumerate(cases, start=1):
        request = ChatRequest.from_dict({
            "thread_id": f"dify-model-eval-{row['case_id']}-{index}",
            "message": row["user_query"],
        })
        response = graph.invoke(request, f"dify-model-eval-{row['case_id']}-{index}")
        route_expected = expected_status(row)
        intent_actual = response.plan.get("intent") if response.plan else None
        results.append({
            "case_id": row["case_id"],
            "dataset": row["dataset"],
            "expected_intent": row["intent_label"],
            "actual_intent": intent_actual,
            "intent_passed": intent_actual == row["intent_label"],
            "expected_status": route_expected,
            "actual_status": response.status,
            "route_passed": route_expected is None or response.status == route_expected,
            "model_planner_used": bool(response.plan and response.plan.get("model_used")),
            "expected_keypoints": row["expected_keypoints"],
        })
    return results


def build_report(cases: list[dict[str, str]], model: ModelAdapter, live: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "suite": "dify_model_eval",
        "mode": "live" if live else "dry_run",
        "datasets": list(DATASETS),
        "total": len(cases),
        "model_version": model.version,
        "model_diagnostics": getattr(model, "diagnostics", {}),
        "synthetic_data_only": True,
        "merchant_connection": "disabled",
    }
    if not live:
        report["message"] = "Dry run only: no model endpoint was called. Re-run with --live after configuring an approved provider."
        return report
    results = evaluate_live(cases, model)
    route_scored = [result for result in results if result["expected_status"] is not None]
    report.update({
        "intent_passed": sum(result["intent_passed"] for result in results),
        "intent_accuracy": sum(result["intent_passed"] for result in results) / len(results) if results else 0,
        "route_scored": len(route_scored),
        "route_passed": sum(result["route_passed"] for result in route_scored),
        "route_accuracy": (sum(result["route_passed"] for result in route_scored) / len(route_scored)) if route_scored else None,
        "model_planner_used": sum(result["model_planner_used"] for result in results),
        "model_diagnostics": getattr(model, "diagnostics", {}),
        "cases": results,
    })
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Call the configured model with local synthetic Dify prompts.")
    parser.add_argument("--limit", type=int, default=0, help="Evaluate only the first N cases; useful for a low-cost trial.")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    cases = load_cases()
    if args.limit:
        if args.limit < 1:
            raise SystemExit("--limit must be positive")
        cases = cases[:args.limit]
    if args.live:
        load_local_config()
    model = ModelAdapter()
    if args.live and not model.enabled:
        raise SystemExit("--live requires COMMERCE_LLM_BASE_URL, COMMERCE_LLM_API_KEY, and COMMERCE_LLM_MODEL. No request was sent.")
    report = build_report(cases, model, args.live)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
