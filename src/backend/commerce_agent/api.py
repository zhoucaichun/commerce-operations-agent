"""FastAPI adapter for the synthetic Commerce Operations Agent."""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .agent import CommerceAgent
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

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "commerce-agent"}

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
        return {"service": "commerce-agent", **request.app.state.agent.store.metrics()}

    @app.post("/api/v1/chat")
    def chat(payload: ChatPayload, request: Request, x_request_id: str | None = Header(default=None)) -> JSONResponse:
        try:
            domain_request = ChatRequest.from_dict(payload.model_dump())
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        response = request.app.state.agent.handle(domain_request, request_id=x_request_id or request.state.request_id)
        return JSONResponse(response.as_dict())

    return app


app = create_app()
