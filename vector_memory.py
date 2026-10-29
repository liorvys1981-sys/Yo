"""OM-P3 Semantic/Vector Memory — SemanticMemoryIndex + MemoryRetriever.

Embedding determinista puro (hashing-trick sobre tokens, seed fijo): sin red, sin LLM,
reproducible. La similitud vectorial SOLO recupera informacion; NUNCA es autoridad
(constraint testeado)."""
from __future__ import annotations
import hashlib, math, re

DIM = 128
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"la", "el", "de", "y", "en", "a", "o", "que", "los", "las", "un", "una", "con", "por", "al"}


def _embed(text: str) -> list:
    v = [0.0] * DIM
    for tok in _TOKEN.findall(text.lower()):
        if tok in _STOP:
            continue
        h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
        v[h % DIM] += 1.0 if h >> 8 & 1 else -1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _cos(a: list, b: list) -> float:
    return round(sum(x * y for x, y in zip(a, b)), 6)


class SemanticMemoryIndex:
    """Indice vectorial con metadatos completos (tenant/owner/provenance/ts/confidence/hash)."""

    def __init__(self):
        self._items: dict[str, dict] = {}

    def index(self, memory_id: str, text: str, metadata: dict) -> str:
        for campo in ("tenant_id", "owner_id", "provenance", "timestamp", "confidence"):
            if campo not in metadata:
                raise ValueError(f"metadata obligatoria: {campo}")
        if metadata["confidence"] < 0 or metadata["confidence"] > 1:
            raise ValueError("confidence en [0,1]")
        self._items[memory_id] = {"id": memory_id, "vector": _embed(text),
                                  "text": text, "metadata": dict(metadata),
                                  "content_hash": hashlib.sha256(text.encode()).hexdigest()[:16]}
        return memory_id

    def remove(self, memory_id: str):
        self._items.pop(memory_id, None)


class MemoryRetriever:
    """Recupera por similitud SOLO dentro del tenant/owner; aislado; nunca modifica nada."""

    def __init__(self, index: SemanticMemoryIndex):
        self.index = index

    def retrieve_temporal(self, query: str, tenant_id: str, owner_id: str,
                          t_from: float, t_to: float, top_k: int = 5) -> list:
        """Recuperacion temporal: solo items con timestamp en [t_from, t_to]."""
        hits = self.retrieve(query, tenant_id, owner_id, top_k=10**6)
        out = [h for h in hits if t_from <= h["metadata"]["timestamp"] <= t_to]
        return out[:top_k]

    def retrieve(self, query: str, tenant_id: str, owner_id: str,
                 top_k: int = 5) -> list:
        qv = _embed(query)
        out = []
        for item in self.index._items.values():
            md = item["metadata"]
            if md["tenant_id"] != tenant_id or md["owner_id"] != owner_id:
                continue  # aislamiento estricto
            out.append({"memory": item["text"], "similarity": _cos(qv, item["vector"]),
                        "metadata": md, "memory_id": item["id"],
                        "content_hash": item["content_hash"]})
        out.sort(key=lambda x: -x["similarity"])
        return out[:top_k]
