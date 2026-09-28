"""Optional Redis guard: a safe local fallback is used when REDIS_URL is absent."""

from __future__ import annotations

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
