"""One entry for offline regression and explicit, separately labelled live checks."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Calls configured services; consumes quota")
    parser.add_argument("--limit", type=int, default=3, help="Live task limit; offline always uses full suite")
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    env = os.environ.copy()
    if not args.live:
        env = {key: value for key, value in env.items() if not key.startswith("COMMERCE_")}
    commands = (["src/eval/run_agent_eval.py", "--live", "--limit", str(args.limit), "--report", "reports/model/agent-live.json"],) if args.live else (
        ["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"],
        ["src/eval/run_smoke.py"],
        ["src/eval/run_agent_eval.py", "--report", "reports/local/agent-tasks-v2.json"],
        ["src/eval/run_rag_eval.py", "--report", "reports/local/rag-v2.json"],
        ["src/eval/run_evaluation.py", "--report", "reports/local/deterministic-v2.json"],
    )
    for command in commands:
        result = subprocess.run([sys.executable, *command], cwd=ROOT, env=env)
        if result.returncode:
            raise SystemExit(result.returncode)
    print("Live subset checks passed; not a full release evaluation." if args.live else "Offline checks passed; no model service was called.")


if __name__ == "__main__":
    main()
