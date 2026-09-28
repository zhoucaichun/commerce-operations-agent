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
