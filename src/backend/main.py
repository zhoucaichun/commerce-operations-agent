"""Small HTTP entry point for the dependency-free Commerce Agent MVP.

Run from the repository root with:

    python src/backend/main.py

The production FastAPI/PostgreSQL/Redis adapter is intentionally not included
in this first slice; this server makes the safety behavior locally testable.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from typing import Any
from uuid import uuid4

from commerce_agent.agent import CommerceAgent
from commerce_agent.models import ChatRequest, ValidationError


agent = CommerceAgent()


class CommerceHTTPHandler(BaseHTTPRequestHandler):
    server_version = "CommerceAgentMVP/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path == "/health":
            self._write_json(200, {"status": "ok", "service": "commerce-agent"})
            return
        if self.path == "/ready":
            self._write_json(200, {"status": "ready", "checks": {"synthetic_store": "ok"}})
            return
        if self.path == "/metrics":
            self._write_json(200, {"service": "commerce-agent", **agent.store.metrics()})
            return
        self._write_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/api/v1/chat":
            self._write_json(404, {"error": "not_found"})
            return
        request_id = self.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 64 * 1024:
                raise ValidationError("request body size must be between 1 and 65536 bytes")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            request = ChatRequest.from_dict(payload)
            response = agent.handle(request, request_id=request_id)
            self._write_json(200, response.as_dict(), request_id=request_id)
        except (ValidationError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._write_json(400, {"error": "invalid_request", "detail": str(exc)}, request_id=request_id)
        except Exception:
            self._write_json(
                500,
                {"error": "internal_error", "detail": "request stopped safely; see server diagnostics"},
                request_id=request_id,
            )

    def log_message(self, format: str, *args: Any) -> None:
        # Do not print raw URLs or bodies; the MVP keeps logs minimal by default.
        sys.stderr.write(f"commerce-agent {self.command} {self.path.split('?')[0]}\n")

    def _write_json(self, status: int, payload: dict[str, Any], request_id: str | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if request_id:
            self.send_header("X-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), CommerceHTTPHandler)


if __name__ == "__main__":
    with create_server() as server:
        print("Commerce Agent MVP listening on http://127.0.0.1:8000")
        server.serve_forever()
