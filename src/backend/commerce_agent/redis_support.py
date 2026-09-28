"""Optional Redis guard: a safe local fallback is used when REDIS_URL is absent."""

from __future__ import annotations

import json

class RedisHealth:
    def __init__(self, url: str | None) -> None:
        self.client = None
        if url:
            try:
                import redis
            except ImportError as exc:
                raise RuntimeError("redis is required when COMMERCE_REDIS_URL is set") from exc
            self.client = redis.from_url(url, decode_responses=True)

    def ready(self) -> bool:
        return True if self.client is None else bool(self.client.ping())

    def allow(self, subject: str, limit: int = 30, window_seconds: int = 60) -> bool:
        """Fixed-window local API guard; no Redis means no distributed limit."""
        if self.client is None:
            return True
        key = f"commerce:rate:{subject}"
        value = self.client.incr(key)
        if value == 1:
            self.client.expire(key, window_seconds)
        return value <= limit

    def acquire_idempotency_lock(self, key: str, ttl_seconds: int = 15) -> bool:
        if self.client is None:
            return True
        return bool(self.client.set(f"commerce:lock:{key}", "1", nx=True, ex=ttl_seconds))

    def release_idempotency_lock(self, key: str) -> None:
        if self.client is not None:
            self.client.delete(f"commerce:lock:{key}")

    def load_checkpoint(self, thread_id: str) -> dict | None:
        """Return the last synthetic session snapshot, if Redis is configured."""
        if self.client is None:
            return None
        value = self.client.get(f"commerce:checkpoint:{thread_id}")
        return json.loads(value) if value else None

    def save_checkpoint(self, thread_id: str, state: dict, ttl_seconds: int = 3600) -> None:
        """Persist only synthetic, already-sanitised conversation state."""
        if self.client is not None:
            self.client.set(
                f"commerce:checkpoint:{thread_id}",
                json.dumps(state, ensure_ascii=False),
                ex=ttl_seconds,
            )

    def consume_tool_retry(self, request_id: str, tool_name: str, max_retries: int = 1) -> bool:
        """Atomically reserve one bounded retry for a read-only tool call."""
        if self.client is None:
            return False
        key = f"commerce:retry:{request_id}:{tool_name}"
        value = self.client.incr(key)
        if value == 1:
            self.client.expire(key, 60)
        return value <= max_retries
