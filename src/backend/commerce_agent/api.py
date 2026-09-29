"""FastAPI adapter for the synthetic Commerce Operations Agent."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .agent import CommerceAgent
from .auth import AuthenticationError, SyntheticAuthenticator
from .graph import CommerceGraph
from .models import ChatRequest, ValidationError
from .sqlite_store import SQLiteStore
from .postgres_store import PostgresStore
from .redis_support import RedisHealth


class ChatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    thread_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    slots: dict[str, str] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


def build_agent(database_path: str | None = None) -> CommerceAgent:
    dsn = os.getenv("COMMERCE_POSTGRES_DSN")
    return CommerceAgent(PostgresStore(dsn) if dsn else SQLiteStore(database_path or os.getenv("COMMERCE_DB_PATH", ":memory:")))


def create_app(agent_instance: CommerceAgent | None = None) -> FastAPI:
    app = FastAPI(title="Commerce Operations Agent", version="0.2.0")
    app.state.agent = agent_instance or build_agent()
    app.state.redis_health = RedisHealth(os.getenv("COMMERCE_REDIS_URL"))
    app.state.authenticator = SyntheticAuthenticator()
    app.state.agent.checkpoint_store = app.state.redis_health
    app.state.agent.retry_store = app.state.redis_health
    app.state.graph = CommerceGraph(app.state.agent)
    frontend_dir = Path(os.getenv("COMMERCE_FRONTEND_DIR", Path(__file__).resolve().parents[2] / "frontend"))

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "commerce-agent"}

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

    @app.get("/ready")
    def ready(request: Request) -> dict[str, Any]:
        try:
            request.app.state.agent.store.ready()
            request.app.state.redis_health.ready()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="synthetic store unavailable") from exc
        return {"status": "ready", "checks": {"storage": "ok", "redis": "ok"}}

    @app.get("/metrics")
    def metrics(request: Request) -> dict[str, Any]:
        metrics = request.app.state.agent.store.metrics()
        chats = metrics["chat_requests"]
        return {"service": "commerce-agent", **metrics, "handoff_rate": round(metrics["handoffs"] / chats, 4) if chats else 0, "tool_calls_per_chat": round(metrics["tool_calls"] / chats, 2) if chats else 0}

    @app.post("/api/v1/chat")
    def chat(payload: ChatPayload, request: Request, authorization: str | None = Header(default=None), x_request_id: str | None = Header(default=None)) -> JSONResponse:
        try:
            domain_request = ChatRequest.from_dict(payload.model_dump())
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            principal = request.app.state.authenticator.authenticate(authorization)
            message = domain_request.message.lower()
            required_role = "support" if request.app.state.agent._is_order_intent(message) or request.app.state.agent._is_ticket_intent(message) else "viewer"
            request.app.state.authenticator.authorize(principal, required_role)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        guard = request.app.state.redis_health
        if not guard.allow(domain_request.thread_id):
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        locked = False
        if domain_request.idempotency_key:
            locked = guard.acquire_idempotency_lock(domain_request.idempotency_key)
            if not locked:
                raise HTTPException(status_code=409, detail="idempotent request is already in progress")
        try:
            response = request.app.state.graph.invoke(domain_request, request_id=x_request_id or request.state.request_id)
            request.app.state.agent._trace(response.trace, response.request_id, response.thread_id, "authorize", principal.role)
        finally:
            if locked:
                guard.release_idempotency_lock(domain_request.idempotency_key)
        return JSONResponse(response.as_dict())

    return app


app = create_app()
