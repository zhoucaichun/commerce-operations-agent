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
from .demo_tenants import DEMO_MERCHANTS, DemoTenantRegistry
from .graph import CommerceGraph
from .models import ChatRequest, ValidationError
from .sqlite_store import SQLiteStore
from .postgres_store import PostgresStore
from .redis_support import RedisHealth
from .runtime import production_readiness


class ChatPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    thread_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    slots: dict[str, str] = Field(default_factory=dict)
    attachments: list[dict[str, Any]] = Field(default_factory=list, max_length=3)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class WidgetChatPayload(ChatPayload):
    merchant_id: str = Field(min_length=3, max_length=80)


class ConsolePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    merchant_id: str = Field(min_length=3, max_length=80)
    role: str = Field(pattern="^(support|operator|merchant_admin)$")


class TicketStatusPayload(ConsolePayload):
    status: str = Field(pattern="^simulated_(open|in_progress|resolved)$")


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
    app.state.demo_tenants = DemoTenantRegistry(CommerceGraph)
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

    @app.get("/api/v1/production-readiness")
    def readiness_contract() -> dict[str, Any]:
        """Return activation gates without exposing secret values or contacting merchants."""
        gates = production_readiness()
        return {"mode": "synthetic_mvp", "gates": gates, "live_operations_enabled": False}

    @app.get("/metrics")
    def metrics(request: Request) -> dict[str, Any]:
        store = request.app.state.agent.store
        store.snapshot_metrics()
        metrics = store.metrics()
        chats = metrics["chat_requests"]
        return {"service": "commerce-agent", **metrics, "handoff_rate": round(metrics["handoffs"] / chats, 4) if chats else 0, "tool_calls_per_chat": round(metrics["tool_calls"] / chats, 2) if chats else 0, "recent_handoffs": store.recent_handoffs(), "metric_snapshots": store.metric_snapshots()}

    @app.post("/api/v1/chat")
    def chat(payload: ChatPayload, request: Request, authorization: str | None = Header(default=None), x_request_id: str | None = Header(default=None)) -> JSONResponse:
        try:
            domain_request = ChatRequest.from_dict(payload.model_dump())
        except ValidationError as exc:
            request.app.state.agent.store.increment("failure:ValidationError")
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            principal = request.app.state.authenticator.authenticate(authorization)
            message = domain_request.message.lower()
            required_role = "support" if request.app.state.agent._is_order_intent(message) or request.app.state.agent._is_ticket_intent(message) else "viewer"
            request.app.state.authenticator.authorize(principal, required_role)
        except AuthenticationError as exc:
            request.app.state.agent.store.increment("failure:AuthenticationError")
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except PermissionError as exc:
            request.app.state.agent.store.increment("failure:PermissionError")
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        guard = request.app.state.redis_health
        if not guard.allow(domain_request.thread_id):
            request.app.state.agent.store.increment("failure:RateLimitExceeded")
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

    @app.get("/api/v1/widget/config/{merchant_id}")
    def widget_config(merchant_id: str, request: Request) -> dict[str, Any]:
        try:
            merchant = request.app.state.demo_tenants.merchant(merchant_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown demo merchant") from exc
        return {"merchant_id": merchant["merchant_id"], "title": merchant["widget_title"], "origin": merchant["origin"], "mode": "synthetic_demo"}

    @app.post("/api/v1/widget/chat")
    def widget_chat(payload: WidgetChatPayload, request: Request) -> JSONResponse:
        try:
            graph = request.app.state.demo_tenants.graph(payload.merchant_id)
            agent = request.app.state.demo_tenants.agent(payload.merchant_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown demo merchant") from exc
        try:
            domain_request = ChatRequest.from_dict({**payload.model_dump(), "thread_id": f"widget:{payload.merchant_id}:{payload.thread_id}"})
        except ValidationError as exc:
            agent.store.increment("failure:ValidationError")
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        response = graph.invoke(domain_request, request_id=request.state.request_id)
        return JSONResponse({**response.as_dict(), "merchant_id": payload.merchant_id, "mode": "synthetic_demo"})

    @app.post("/api/v1/demo/console/overview")
    def console_overview(payload: ConsolePayload, request: Request) -> dict[str, Any]:
        try:
            merchant = request.app.state.demo_tenants.merchant(payload.merchant_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown demo merchant") from exc
        if payload.role not in merchant["roles"]:
            raise HTTPException(status_code=403, detail="demo role is not allowed for this merchant")
        overview = request.app.state.demo_tenants.overview(payload.merchant_id)
        overview["role"] = payload.role
        return overview

    @app.patch("/api/v1/demo/console/tickets/{ticket_id}")
    def update_demo_ticket(ticket_id: str, payload: TicketStatusPayload, request: Request) -> dict[str, Any]:
        if payload.role not in {"support", "merchant_admin"}:
            raise HTTPException(status_code=403, detail="only synthetic support roles may update simulated tickets")
        try:
            ticket = request.app.state.demo_tenants.agent(payload.merchant_id).store.update_ticket_status(ticket_id, payload.status)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="unknown demo merchant") from exc
        if ticket is None:
            raise HTTPException(status_code=404, detail="simulated ticket not found in this merchant")
        return {"ticket": ticket, "mode": "synthetic_demo"}

    return app


app = create_app()
