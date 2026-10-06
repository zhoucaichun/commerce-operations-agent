from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/backend"))
from commerce_agent.config import load_local_config
from commerce_agent.embeddings import SemanticEmbedder


class ModelConfigTests(unittest.TestCase):
    def test_server_only_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text('# comment\nCOMMERCE_LLM_MODEL="file-model"\nCOMMERCE_LLM_API_KEY=test-only\nNEXT_PUBLIC_SECRET=blocked\n', encoding="utf-8")
            with patch.dict(os.environ, {"COMMERCE_LLM_MODEL": "environment-model"}, clear=True):
                load_local_config(path)
                self.assertEqual(os.environ["COMMERCE_LLM_MODEL"], "environment-model")
                self.assertEqual(os.environ["COMMERCE_LLM_API_KEY"], "test-only")
                self.assertNotIn("NEXT_PUBLIC_SECRET", os.environ)

    def test_empty_embedding_overrides_reuse_chat_config(self):
        with patch.dict(os.environ, {"COMMERCE_EMBEDDING_MODEL": "embedding-test", "COMMERCE_EMBEDDING_BASE_URL": "", "COMMERCE_EMBEDDING_API_KEY": "", "COMMERCE_EMBEDDING_CACHE": "", "COMMERCE_LLM_BASE_URL": "https://example.test/v1", "COMMERCE_LLM_API_KEY": "test-only"}, clear=True):
            embedder = SemanticEmbedder()
            self.assertTrue(embedder.enabled)
            self.assertEqual(embedder.base, "https://example.test/v1")
            self.assertEqual(embedder.key, "test-only")
            embedder.db.close()

    def test_semantic_batch_cache(self):
        calls = []
        def transport(payload):
            calls.append(payload)
            return {"data": [{"index": i, "embedding": [3, 4]} for i in range(len(payload["input"]))]}
        embedder = SemanticEmbedder(transport=transport)
        self.assertEqual(embedder.embed_many(["a", "b"]), [(0.6, 0.8), (0.6, 0.8)])
        self.assertEqual(embedder.embed("a"), (0.6, 0.8))
        self.assertEqual(len(calls), 1)
        embedder.db.close()
