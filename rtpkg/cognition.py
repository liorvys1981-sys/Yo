"""Modulo de paquete rtpkg — reorganizacion del Agent Runtime (baseline-safe)."""
from __future__ import annotations
import hashlib, json, time
import sys

for _p in ("/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO",
           "/mnt/agents/output/EL_YO/05_RAZONAMIENTO",
           "/mnt/agents/output/EL_YO/02_MEMORIA",
           "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA",
           "/mnt/agents/output/EL_YO/23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION",
           "/mnt/agents/output/EL_YO/17_SOVEREIGNTY"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from vector_memory import SemanticMemoryIndex, MemoryRetriever

class MemoryCognition:
    """Contexto de trabajo del runtime sobre la memoria canonica (area 02)."""

    def __init__(self, index: SemanticMemoryIndex | None = None,
                 tenant: str = "EL_YO", owner: str = "runtime"):
        self.index = index or SemanticMemoryIndex()
        self.tenant, self.owner = tenant, owner
        self.retriever = MemoryRetriever(self.index)

    def remember(self, memory_id: str, text: str, provenance: str = "SYSTEM_DERIVED",
                 confidence: float = 0.5) -> str:
        return self.index.index(memory_id, text,
                                {"tenant_id": self.tenant, "owner_id": self.owner,
                                 "provenance": provenance, "timestamp": self.retriever and __import__("time").time(),
                                 "confidence": confidence})

    def recall(self, query: str, top_k: int = 3) -> list:
        return self.retriever.retrieve(query, self.tenant, self.owner, top_k)


# ============ SovereigntySecurity ============
class CognitiveAnalytics:
    def __init__(self, economics: ValueResourceEconomics):
        self.econ = economics

    def summary(self) -> dict:
        by_route: dict[str, dict] = {}
        for u in self.econ.usage:
            r = by_route.setdefault(u["route"], {"calls": 0, "cost": 0.0})
            r["calls"] += 1
            r["cost"] = round(r["cost"] + u["cost"], 6)
        return {"routes": by_route, "total_cost":
                round(sum(u["cost"] for u in self.econ.usage), 6),
                "total_calls": len(self.econ.usage),
                "avoided_llm_calls": sum(1 for u in self.econ.usage
                                         if u["route"] == "DETERMINISTIC")}


# ============ CognitiveOrchestrator ============
