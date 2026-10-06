"""Versioned task regression. --live is explicit; fallback is never model success."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/backend"))
from commerce_agent.agent import CommerceAgent
from commerce_agent.config import load_local_config
from commerce_agent.embeddings import SemanticEmbedder
from commerce_agent.graph import CommerceGraph
from commerce_agent.models import ChatRequest
from commerce_agent.rag import HashingEmbedder
from commerce_agent.runtime import ModelAdapter

DATA = ROOT / "src/eval/data/agent_tasks_v2.json"


def grade(turn, response, memory):
    tools = [item["tool"] for item in response.tool_result_summary]
    checks = {"status": response.status == turn["expected_status"],
              "required_tools": all(tool in tools for tool in turn.get("required_tools", [])),
              "forbidden_tools": not any(tool in tools for tool in turn.get("forbidden_tools", [])),
              "bounded_steps": len(tools) <= 6,
              "trace": bool(response.trace)}
    if turn.get("no_tools"):
        checks["no_tools"] = not tools
    if turn.get("require_citation"):
        checks["citation"] = any(item.get("citations") for item in response.tool_result_summary)
    if turn.get("require_deduplication"):
        checks["deduplication"] = any(item.get("evidence", {}).get("deduplicated") is True for item in response.tool_result_summary)
    if turn.get("require_empty_memory"):
        checks["empty_memory"] = not memory.get("slots") and not memory.get("preferences")
    return checks


def evaluate(dataset, model, *, embedder=None, limit=0):
    agent = CommerceAgent(model=model)
    agent.tools.retriever.embedder = embedder or HashingEmbedder()
    graph = CommerceGraph(agent, model=model)
    rows = []
    tasks = dataset["tasks"][:limit] if limit else dataset["tasks"]
    for task in tasks:
        for index, turn in enumerate(task["turns"]):
            payload = {key: value for key, value in turn.items() if key in {"message", "slots", "attachments", "idempotency_key"}}
            payload["thread_id"] = "task:" + task["id"]
            started = time.perf_counter()
            response = graph.invoke(ChatRequest.from_dict(payload), f"eval:{task['id']}:{index}")
            checks = grade(turn, response, agent._load_state(payload["thread_id"]))
            rows.append({"task_id": task["id"], "scenario": task["scenario"], "turn": index + 1, "checks": checks,
                         "passed": all(checks.values()), "model_used": bool(response.plan and response.plan.get("model_used")),
                         "model_required": not turn.get("model_not_required", False),
                         "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                         "status": response.status, "answer": response.answer, "plan": response.plan,
                         "tools": response.tool_result_summary, "trace": response.trace})
    task_results = {task["id"]: all(row["passed"] for row in rows if row["task_id"] == task["id"]) for task in tasks}
    required = [row for row in rows if row["model_required"]]
    modes = Counter(item.get("evidence", {}).get("retrieval", {}).get("retrieval_mode") for row in rows for item in row["tools"] if item["tool"] in {"policy_search", "knowledge_search"})
    durations = sorted(row["elapsed_ms"] for row in rows)
    return {"suite": "agent_task_regression", "dataset_version": dataset["version"], "split": dataset["split"],
            "task_count": len(tasks), "tasks_passed": sum(task_results.values()), "turn_count": len(rows),
            "turns_passed": sum(row["passed"] for row in rows), "model_participation": sum(row["model_used"] for row in required),
            "model_required_turns": len(required), "model_diagnostics": model.diagnostics, "model_version": model.version,
            "usage": model.usage, "retrieval_modes": dict(modes), "p95_ms": durations[max(0, int(len(durations) * .95) - 1)] if durations else 0,
            "cost": None, "cost_note": "未配置计费单价；不从截图或额度推算账单", "synthetic_only": True,
            "human_semantic_judging": "not_performed", "task_results": task_results, "cases": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--report", type=Path, default=ROOT / "reports/local/agent-tasks-v2.json")
    args = parser.parse_args()
    if args.limit < 0:
        raise SystemExit("--limit must be nonnegative")
    embedder = None
    if args.live:
        load_local_config()
        model = ModelAdapter()
        embedder = SemanticEmbedder()
        if not model.enabled or not embedder.enabled:
            raise SystemExit("--live requires both chat and semantic embedding configuration")
        # One probe before indexing/evaluation; a broken network must not trigger a whole suite.
        if model.complete_json("Return JSON only.", "Return {\"status\":\"ok\"}.") is None:
            raise SystemExit("Chat probe failed; no batch evaluation was started. " + json.dumps(model.diagnostics))
        try:
            embedder.embed("ShopPilot synthetic product verification")
        except Exception:
            raise SystemExit("Embedding probe failed; no batch evaluation was started.") from None
    else:
        model = ModelAdapter(allow_network=False)
    raw = DATA.read_bytes()
    report = evaluate(json.loads(raw), model, embedder=embedder, limit=args.limit)
    report["mode"] = "live" if args.live else "offline"
    report["dataset_sha256"] = hashlib.sha256(raw).hexdigest()
    report["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    report["working_tree_dirty"] = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    valid_live = not args.live or (report["tasks_passed"] == report["task_count"] and report["model_participation"] == report["model_required_turns"] and report["retrieval_modes"].get("lexical_degraded", 0) == 0)
    report["live_subset_passed"] = args.live and valid_live
    report["live_validation_complete"] = args.live and valid_live and report["task_count"] == len(json.loads(raw)["tasks"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"cases", "task_results"}}, ensure_ascii=False))
    if report["tasks_passed"] != report["task_count"] or not valid_live:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
