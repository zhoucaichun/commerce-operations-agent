"""Synthetic-only Compose integration smoke, including API restart persistence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request


def request(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    response = urllib.request.urlopen(urllib.request.Request(f"{url}/api/v1/chat", body, {"Content-Type": "application/json"}), timeout=10)
    return json.loads(response.read())


def wait_ready(url: str, timeout_seconds: int = 20) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            ready = json.loads(urllib.request.urlopen(f"{url}/ready", timeout=2).read())
            if ready["status"] == "ready":
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError("Compose API did not become ready after restart")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--restart-api", action="store_true")
    args = parser.parse_args()
    wait_ready(args.url)
    assert request(args.url, {"thread_id": "compose-product", "message": "charger"})["status"] == "completed"
    assert request(args.url, {"thread_id": "compose-policy", "message": "warranty policy"})["status"] == "completed"
    assert request(args.url, {"thread_id": "compose-order", "message": "order ORD-10023 tracking 4821"})["status"] == "completed"
    ticket = {"thread_id": "compose-ticket", "message": "create a human support ticket", "idempotency_key": "compose-restart-ticket-001"}
    first = request(args.url, ticket)
    assert first["status"] == "completed", first
    if args.restart_api:
        root = Path(__file__).resolve().parents[2]
        subprocess.run(["docker", "compose", "-p", "commerce-agent", "-f", "src/infra/docker-compose.yml", "restart", "api"], cwd=root, check=True)
        wait_ready(args.url)
    second = request(args.url, ticket)
    assert second["status"] == "completed" and "SIM-TKT-" in second["answer"], second
    print("compose smoke passed: product, policy, order, ticket idempotency and restart persistence")


if __name__ == "__main__":
    main()
