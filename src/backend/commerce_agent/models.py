"""Input and output models for the local simulated Commerce Agent.

The MVP intentionally uses standard-library dataclasses so it can be exercised
without network access or unreviewed third-party dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


MAX_MESSAGE_LENGTH = 4000
THREAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$")


class ValidationError(ValueError):
    """Raised when an API input is invalid or unsafe to process."""


@dataclass(frozen=True)
class ChatRequest:
    thread_id: str
    message: str
    slots: dict[str, str] = field(default_factory=dict)
    idempotency_key: str | None = None

    @classmethod
    def from_dict(cls, payload: Any) -> "ChatRequest":
        if not isinstance(payload, dict):
            raise ValidationError("request body must be a JSON object")

        thread_id = payload.get("thread_id")
        if not isinstance(thread_id, str) or not THREAD_ID_PATTERN.fullmatch(thread_id):
            raise ValidationError("thread_id is required and must be a safe identifier")

        message = payload.get("message")
        if not isinstance(message, str):
            raise ValidationError("message is required")
        message = message.strip()
        if not message:
            raise ValidationError("message must not be empty")
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValidationError(f"message exceeds {MAX_MESSAGE_LENGTH} characters")
        if any(ord(char) < 32 and char not in "\t\n\r" for char in message):
            raise ValidationError("message contains unsupported control characters")

        raw_slots = payload.get("slots", {})
        if raw_slots is None:
            raw_slots = {}
        if not isinstance(raw_slots, dict):
            raise ValidationError("slots must be an object")
        slots: dict[str, str] = {}
        for key, value in raw_slots.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidationError("slots must contain string keys and values")
            if len(key) > 64 or len(value) > 256:
                raise ValidationError("slot key or value is too long")
            slots[key] = value.strip()

        idempotency_key = payload.get("idempotency_key")
        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not re.fullmatch(
                r"[A-Za-z0-9_.:-]{8,128}", idempotency_key
            ):
                raise ValidationError("idempotency_key must be 8-128 safe characters")

        return cls(
            thread_id=thread_id,
            message=message,
            slots=slots,
            idempotency_key=idempotency_key,
        )


@dataclass
class AgentResponse:
    status: str
    answer: str
    request_id: str
    thread_id: str
    tool_result_summary: list[dict[str, Any]] = field(default_factory=list)
    handoff: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "answer": self.answer,
            "request_id": self.request_id,
            "thread_id": self.thread_id,
            "tool_result_summary": self.tool_result_summary,
            "handoff": self.handoff,
            "trace": self.trace,
        }
