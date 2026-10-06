import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "backend"))

from commerce_agent.redis_support import RedisHealth


class FakeRedis:
    def __init__(self): self.values = {}
    def incr(self, key): self.values[key] = self.values.get(key, 0) + 1; return self.values[key]
    def expire(self, key, seconds): pass
    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values: return False
        self.values[key] = value; return True
    def get(self, key): return self.values.get(key)
    def delete(self, key): self.values.pop(key, None)
    def ping(self): return True


class RedisGuardTests(unittest.TestCase):
    def test_rate_limit_and_idempotency_lock(self):
        guard = RedisHealth(None); guard.client = FakeRedis()
        self.assertTrue(guard.allow("thread", limit=2))
        self.assertTrue(guard.allow("thread", limit=2))
        self.assertFalse(guard.allow("thread", limit=2))
        self.assertTrue(guard.acquire_idempotency_lock("ticket"))
        self.assertFalse(guard.acquire_idempotency_lock("ticket"))
        guard.release_idempotency_lock("ticket")
        self.assertTrue(guard.acquire_idempotency_lock("ticket"))

    def test_no_redis_is_safe_local_fallback(self):
        guard = RedisHealth(None)
        self.assertFalse(guard.allow("thread", limit=0))
        self.assertTrue(guard.acquire_idempotency_lock("ticket"))
        self.assertFalse(guard.acquire_idempotency_lock("ticket"))
        guard.release_idempotency_lock("ticket")
        self.assertTrue(guard.acquire_idempotency_lock("ticket"))

    def test_checkpoint_and_bounded_retry_state(self):
        guard = RedisHealth(None); guard.client = FakeRedis()
        state = {"thread_id": "thread", "messages": [{"role": "user", "summary": "hash"}], "slots": {}, "step_count": 1}
        guard.save_checkpoint("thread", state)
        self.assertEqual(guard.load_checkpoint("thread"), state)
        self.assertTrue(guard.consume_tool_retry("request", "product_search"))
        self.assertFalse(guard.consume_tool_retry("request", "product_search"))
