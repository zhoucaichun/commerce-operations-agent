"""Batched semantic embedding adapter with model/content-keyed SQLite cache."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Protocol
from urllib.request import Request, urlopen


class EmbeddingProvider(Protocol):
    mode: str
    def embed(self, text: str) -> tuple[float, ...]: ...
    def embed_many(self, texts: list[str]) -> list[tuple[float, ...]]: ...


class EmbeddingError(ValueError):
    pass


class SemanticEmbedder:
    mode = "semantic_api"

    def __init__(self, transport=None, cache_path: str | None = None):
        self.model = os.getenv("COMMERCE_EMBEDDING_MODEL", "")
        self.base = (os.getenv("COMMERCE_EMBEDDING_BASE_URL") or os.getenv("COMMERCE_LLM_BASE_URL", "")).rstrip("/")
        self.key = os.getenv("COMMERCE_EMBEDDING_API_KEY") or os.getenv("COMMERCE_LLM_API_KEY", "")
        self.timeout = float(os.getenv("COMMERCE_EMBEDDING_TIMEOUT_SECONDS", "15"))
        self.transport = transport
        self.batch_size = max(1, min(10, int(os.getenv("COMMERCE_EMBEDDING_BATCH_SIZE", "8") or "8")))
        self.lock = RLock()
        path = cache_path or os.getenv("COMMERCE_EMBEDDING_CACHE") or ":memory:"
        if path != ":memory:":
            Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    @property
    def enabled(self):
        return self.transport is not None or bool(self.model and self.base and self.key)

    def embed(self, text):
        return self.embed_many([text])[0]

    def embed_many(self, texts):
        if not self.enabled:
            raise EmbeddingError("embedding_not_configured")
        with self.lock:
            keys = [hashlib.sha256((self.base + "\0" + self.model + "\0" + text).encode()).hexdigest() for text in texts]
            vectors = []
            for key in keys:
                row = self.db.execute("SELECT value FROM vectors WHERE key=?", (key,)).fetchone()
                vectors.append(tuple(json.loads(row[0])) if row else None)
            missing = [i for i, vector in enumerate(vectors) if vector is None]
            for start in range(0, len(missing), self.batch_size):
                batch = missing[start:start + self.batch_size]
                payload = {"model": self.model, "input": [texts[i] for i in batch]}
                try:
                    if self.transport:
                        raw = self.transport(payload)
                    else:
                        endpoint = self.base + ("/embeddings" if self.base.endswith("/v1") else "/v1/embeddings")
                        req = Request(endpoint, json.dumps(payload).encode(), headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"}, method="POST")
                        with urlopen(req, timeout=self.timeout) as response:
                            raw = json.loads(response.read())
                    data = sorted(raw["data"], key=lambda item: item["index"])
                    if [item["index"] for item in data] != list(range(len(batch))):
                        raise ValueError()
                    for index, item in zip(batch, data):
                        values = item["embedding"]
                        if not isinstance(values, list) or not values or not all(type(v) in (int, float) and math.isfinite(v) for v in values):
                            raise ValueError()
                        norm = math.sqrt(sum(v * v for v in values))
                        if not norm:
                            raise ValueError()
                        vector = tuple(v / norm for v in values)
                        vectors[index] = vector
                        self.db.execute("INSERT OR REPLACE INTO vectors VALUES (?,?)", (keys[index], json.dumps(vector)))
                    self.db.commit()
                except Exception as exc:
                    self.db.rollback()
                    raise EmbeddingError("embedding_request_or_shape_failed") from exc
            if len({len(vector) for vector in vectors}) > 1:
                raise EmbeddingError("embedding_dimension_mismatch")
            return vectors
