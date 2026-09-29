"""Deterministic synthetic evaluation with a machine-readable report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from commerce_agent.agent import CommerceAgent
from commerce_agent.models import ChatRequest

BASE_CASES = (
    ("product", {"thread_id": "eval-product", "message": "charger"}, "completed"),
    ("compatibility", {"thread_id": "eval-compat", "message": "AC-65W compatible MacBook Pro 14"}, "completed"),
    ("policy", {"thread_id": "eval-policy", "message": "warranty policy"}, "completed"),
    ("order", {"thread_id": "eval-order", "message": "order ORD-10023 tracking 4821"}, "completed"),
    ("order-unverified", {"thread_id": "eval-order-bad", "message": "order ORD-10023 tracking 0000"}, "handoff"),
    ("ticket-needs-key", {"thread_id": "eval-ticket", "message": "create a human support ticket"}, "needs_input"),
    ("risk-handoff", {"thread_id": "eval-risk", "message": "refund please"}, "handoff"),
)
CASES = tuple((f"{name}-{index}", {**payload, "thread_id": f"{payload['thread_id']}-{index}"}, expected) for index in range(1, 13) for name, payload, expected in BASE_CASES) + BASE_CASES[:2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    agent, results = CommerceAgent(), []
    for name, payload, expected in CASES:
        actual = agent.handle(ChatRequest.from_dict(payload)).status
        results.append({"name": name, "expected": expected, "actual": actual, "passed": actual == expected})
    report = {"suite": "commerce_synthetic_eval", "total": len(results), "passed": sum(item["passed"] for item in results), "cases": results}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if report["passed"] != report["total"]:
        raise SystemExit("evaluation failures")


if __name__ == "__main__":
    main()
