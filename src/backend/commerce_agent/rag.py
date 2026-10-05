"""Evidence-first hybrid RAG for repository-packaged synthetic knowledge.

This module is deliberately dependency-light: it supplies deterministic
chunking, a local hashed-vector index, lexical BM25 scoring, metadata filters,
fusion/re-ranking and auditable citations.  The hashing embedder is a local
offline fallback for reproducible tests, not a claim of production semantic
embedding quality.  A managed embedding provider can replace it behind the
same ``EmbeddingProvider`` interface when credentials and data approval exist.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
import hashlib
import math
import re
from typing import Any, Iterable


def _tokens(value: str) -> list[str]:
    latin = re.findall(r"[a-z0-9][a-z0-9+._-]*", value.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]{1,8}", value)
    grams = [text[index : index + 2] for text in chinese for index in range(max(0, len(text) - 1))]
    return latin + chinese + grams


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    text: str
    source: str
    version: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    title: str
    text: str
    source: str
    version: str
    metadata: dict[str, Any]


class HashingEmbedder:
    """A deterministic local vectorizer used only for offline/demo operation."""

    mode = "local_hashing_demo"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimensions
        for token, count in Counter(_tokens(text)).items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[index] += sign * (1.0 + math.log(count))
        norm = math.sqrt(sum(value * value for value in vector))
        return tuple(value / norm for value in vector) if norm else tuple(vector)


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _chunks(document: KnowledgeDocument, size: int = 560, overlap: int = 80) -> list[KnowledgeChunk]:
    clean = re.sub(r"\s+", " ", document.text).strip()
    if not clean:
        return []
    pieces: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        if end < len(clean):
            boundary = clean.rfind(" ", start + size // 2, end)
            end = boundary if boundary > start else end
        pieces.append(clean[start:end].strip())
        if end == len(clean):
            break
        start = max(end - overlap, start + 1)
    return [
        KnowledgeChunk(f"{document.document_id}#c{index + 1}", document.document_id, document.title, piece, document.source, document.version, dict(document.metadata))
        for index, piece in enumerate(pieces)
    ]


def build_knowledge_documents(products: Iterable[dict[str, Any]], policies: Iterable[dict[str, Any]]) -> list[KnowledgeDocument]:
    """Transform structured catalog/policy data into versioned RAG documents."""
    documents: list[KnowledgeDocument] = []
    for policy in policies:
        policy_id = str(policy["policy_id"])
        region = str(policy.get("region", "GLOBAL")).upper()
        summary = str(policy.get("summary", "")).strip()
        keywords = ", ".join(policy.get("keywords", []))
        route_topic = str(policy.get("policy_type") or policy.get("topic", "")).lower()
        documents.append(KnowledgeDocument(
            document_id=f"policy:{policy_id}", title=f"{region} {policy.get('topic', 'policy')} policy",
            text=f"Policy ID: {policy_id}. Region: {region}. Topic: {policy.get('topic', '')}. {summary} Keywords: {keywords}.",
            source=str(policy.get("source", "synthetic_policy_seed")), version=str(policy.get("effective_from", "synthetic-v1")),
            metadata={"kind": "policy", "policy_id": policy_id, "topic": route_topic, "subcategory": str(policy.get("topic", "")).lower(), "region": region, "effective_from": str(policy.get("effective_from", "")), "answer_text": summary},
        ))
    for product in products:
        sku = str(product["sku"])
        documents.append(KnowledgeDocument(
            document_id=f"product:{sku}", title=f"Product knowledge: {sku} {product.get('name', '')}",
            text=(f"SKU: {sku}. Name: {product.get('name', '')}. Category: {product.get('category', '')}. "
                  f"Compatible devices: {product.get('device_compatibility', '')}. Ports: {', '.join(product.get('ports', []))}. "
                  f"Usage: {', '.join(product.get('usage_scenarios', []))}. Features: {product.get('key_features', '')}. "
                  f"Limitations: {product.get('limitations', '')}. Warranty: {product.get('warranty_months', '')} months. "
                  f"Regions: {', '.join(product.get('regions', []))}. This is a synthetic demonstration catalog record."),
            source=str(product.get("source", "synthetic_catalog")), version=str(product.get("catalog_version", "catalog-v1")),
            metadata={"kind": "product", "sku": sku, "category": str(product.get("category", "")).lower(), "regions": list(product.get("regions", [])), "source_of_truth": "structured_catalog"},
        ))
    documents.extend([
        KnowledgeDocument("faq:regional-availability", "Synthetic regional availability FAQ", "Regional availability is a synthetic catalog attribute. It is not live inventory and must be verified before a purchase commitment.", "synthetic_merchant_kb_v1", "2026.10-v1", {"kind": "faq", "topic": "availability", "region": "GLOBAL"}),
        KnowledgeDocument("faq:charging-safety", "Synthetic charging safety FAQ", "For a power compatibility question, use the structured compatibility rule and the product SKU. Do not infer safety, certification, or device support from a semantically similar document.", "synthetic_merchant_kb_v1", "2026.10-v1", {"kind": "faq", "topic": "compatibility", "region": "GLOBAL"}),
        KnowledgeDocument("faq:returns-evidence", "Synthetic returns evidence FAQ", "Return and warranty replies must cite the policy region and effective version. If retrieval returns no applicable policy, the assistant must say that it cannot verify the policy and offer human review.", "synthetic_merchant_kb_v1", "2026.10-v1", {"kind": "faq", "topic": "return", "region": "GLOBAL"}),
    ])
    return documents


class HybridRetriever:
    """Small, inspectable hybrid retriever with hard metadata filters."""

    def __init__(self, documents: Iterable[KnowledgeDocument], embedder: HashingEmbedder | None = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self.chunks = [chunk for document in documents for chunk in _chunks(document)]
        self._vectors = {chunk.chunk_id: self.embedder.embed(f"{chunk.title} {chunk.text}") for chunk in self.chunks}
        self._terms = {chunk.chunk_id: Counter(_tokens(f"{chunk.title} {chunk.text}")) for chunk in self.chunks}
        self._doc_lengths = {chunk.chunk_id: sum(terms.values()) for chunk, terms in ((item, self._terms[item.chunk_id]) for item in self.chunks)}
        self._average_length = sum(self._doc_lengths.values()) / max(1, len(self._doc_lengths))
        self._document_frequency: Counter[str] = Counter()
        for terms in self._terms.values():
            self._document_frequency.update(terms.keys())

    def search(self, query: str, *, limit: int = 4, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        query = query.strip()
        if not query:
            return {"query": query, "chunks": [], "retrieval_mode": self.embedder.mode}
        filters = filters or {}
        candidates = [chunk for chunk in self.chunks if self._matches(chunk, filters)]
        # Policies use a jurisdiction override model: when an exact regional
        # record exists, a GLOBAL fallback must not outrank or dilute it.
        requested_region = str(filters.get("region", "")).upper()
        if filters.get("kind") == "policy" and requested_region:
            regional = [chunk for chunk in candidates if str(chunk.metadata.get("region", "")).upper() == requested_region]
            if regional:
                candidates = regional
        query_terms = Counter(_tokens(query))
        query_vector = self.embedder.embed(query)
        scored: list[tuple[float, KnowledgeChunk, float, float]] = []
        for chunk in candidates:
            lexical = self._bm25(query_terms, self._terms[chunk.chunk_id], self._doc_lengths[chunk.chunk_id])
            vector = max(0.0, _cosine(query_vector, self._vectors[chunk.chunk_id]))
            exact_bonus = 0.18 if any(term in chunk.title.lower() for term in query_terms if len(term) > 3) else 0.0
            region_bonus = 1.0 if requested_region and str(chunk.metadata.get("region", "")).upper() == requested_region else 0.0
            score = lexical + vector + exact_bonus + region_bonus
            if score > 0:
                scored.append((score, chunk, lexical, vector))
        scored.sort(key=lambda row: (-row[0], row[1].chunk_id))
        results = []
        for score, chunk, lexical, vector in scored[:limit]:
            results.append({
                "chunk_id": chunk.chunk_id, "document_id": chunk.document_id, "title": chunk.title, "text": chunk.text,
                "score": round(score, 4), "lexical_score": round(lexical, 4), "vector_score": round(vector, 4),
                "citation": {"document_id": chunk.document_id, "chunk_id": chunk.chunk_id, "source": chunk.source, "version": chunk.version, "metadata": chunk.metadata},
            })
        return {"query": query, "chunks": results, "retrieval_mode": self.embedder.mode, "candidate_count": len(candidates), "filters": filters}

    def _bm25(self, query_terms: Counter[str], document_terms: Counter[str], document_length: int) -> float:
        score, count, k1, b = 0.0, len(self._terms), 1.4, 0.75
        for term, query_frequency in query_terms.items():
            frequency = document_terms.get(term, 0)
            if not frequency:
                continue
            idf = math.log(1 + (count - self._document_frequency[term] + 0.5) / (self._document_frequency[term] + 0.5))
            denominator = frequency + k1 * (1 - b + b * document_length / max(1, self._average_length))
            score += query_frequency * idf * (frequency * (k1 + 1) / denominator)
        return score

    @staticmethod
    def _matches(chunk: KnowledgeChunk, filters: dict[str, Any]) -> bool:
        metadata = chunk.metadata
        kind = filters.get("kind")
        if kind and metadata.get("kind") != kind:
            return False
        topic = filters.get("topic")
        if topic:
            aliases = {
                "return": {"return", "returns"}, "returns": {"return", "returns"},
                "promotion": {"promotion", "promo"}, "promo": {"promotion", "promo"},
            }
            accepted_topics = aliases.get(str(topic), {str(topic)})
            if metadata.get("topic") not in accepted_topics:
                return False
        region = str(filters.get("region", "")).upper()
        if region:
            candidate_region = str(metadata.get("region", "GLOBAL")).upper()
            regions = {str(item).upper() for item in metadata.get("regions", [])}
            if candidate_region not in {"GLOBAL", region} and region not in regions:
                return False
        effective_from = str(metadata.get("effective_from", ""))
        as_of = str(filters.get("as_of", date.today().isoformat()))
        return not effective_from or effective_from <= as_of
