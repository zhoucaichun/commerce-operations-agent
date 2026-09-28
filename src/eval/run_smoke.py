"""Small deterministic eval smoke; it does not call any model or real system."""

from pathlib import Path
import sys


BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from commerce_agent.agent import CommerceAgent
from commerce_agent.models import ChatRequest


CASES = (
    ("compatibility", {"thread_id": "eval-compat", "message": "AC-65W 能兼容 MacBook Pro 14 吗？"}, "completed"),
    ("order", {"thread_id": "eval-order", "message": "查订单 ORD-10023 物流，后四位 4821"}, "completed"),
    ("risk", {"thread_id": "eval-risk", "message": "请直接退款"}, "handoff"),
)


if __name__ == "__main__":
    agent = CommerceAgent()
    failures = []
    for name, payload, expected in CASES:
        actual = agent.handle(ChatRequest.from_dict(payload)).status
        print(f"{name}: {actual}")
        if actual != expected:
            failures.append(name)
    if failures:
        raise SystemExit(f"eval smoke failures: {', '.join(failures)}")
    print(f"eval smoke passed: {len(CASES)} cases")
