"""Memory Model — 5 memorias, procedencia, tenancy, supersede (MEMORY_MODEL).

Storage: dict en memoria (decision Fase 2). La semantica es definitiva;
el backend se sustituye por SOVEREIGN post-vendoring via MemoryAPI.
"""
from __future__ import annotations
import time, uuid
from dataclasses import dataclass, field, asdict

MEMORY_TYPES = ("EPISODIC", "SEMANTIC", "EMOTIONAL", "RELATIONSHIP", "KNOWLEDGE")
PROVENANCE = {"OBSERVED", "INFERRED", "SELF_REPORTED", "SYSTEM_DERIVED", "UNCERTAIN"}
SENSITIVE_TYPES = {"EMOTIONAL"}


class MemoryError(Exception):
    code = "MEMORY_ERROR"


class TenantDenied(MemoryError):
    code = "DENIED_TENANT"


class MissingProvenance(MemoryError):
    code = "MISSING_PROVENANCE"


@dataclass
class MemoryRecord:
    memory_type: str
    content: dict
    provenance: str
    confidence: float
    source_ref: str
    tenant_id: str
    subject_id: str
    cognitive_instance_id: str
    memory_scope: str
    id: str = field(default_factory=lambda: f"mem:{uuid.uuid4().hex[:16]}")
    created_at: float = field(default_factory=time.time)
    superseded_by: str | None = None
    sensitive: bool = field(init=False)

    def __post_init__(self):
        self.sensitive = self.memory_type in SENSITIVE_TYPES
        if self.provenance not in PROVENANCE:
            raise MissingProvenance(f"provenance invalido: {self.provenance}")


class MemoryStore:
    """5 memorias con aislamiento estricto de tenant y supersede (no delete)."""

    def __init__(self):
        self._records: dict[str, MemoryRecord] = {}

    def _check_tenant(self, record: MemoryRecord, ctx_tenant: str) -> None:
        if record.tenant_id != ctx_tenant:
            raise TenantDenied("aislamiento estricto: memoria de otro tenant")

    def store(self, record: MemoryRecord) -> str:
        if not record.source_ref:
            raise MissingProvenance("source_ref obligatorio")
        self._records[record.id] = record
        return record.id

    def query(self, tenant_id: str, memory_type: str,
              include_superseded: bool = False) -> list[MemoryRecord]:
        if memory_type not in MEMORY_TYPES:
            raise MemoryError(f"tipo desconocido: {memory_type}")
        out = []
        for r in self._records.values():
            if r.memory_type != memory_type:
                continue
            self._check_tenant(r, tenant_id)
            if not include_superseded and r.superseded_by:
                continue
            out.append(r)
        return out

    def forget(self, tenant_id: str, memory_id: str,
               successor: MemoryRecord | None = None) -> str:
        r = self._records.get(memory_id)
        if r is None:
            raise MemoryError("memoria no existe")
        self._check_tenant(r, tenant_id)
        # supersede, NUNCA borrado fisico (borrado fisico = gate destructivo)
        if successor is None:
            successor = MemoryRecord(
                memory_type=r.memory_type, content={"forgotten": True},
                provenance="SYSTEM_DERIVED", confidence=1.0,
                source_ref=f"forget:{memory_id}", tenant_id=r.tenant_id,
                subject_id=r.subject_id, cognitive_instance_id=r.cognitive_instance_id,
                memory_scope=r.memory_scope)
            self._records[successor.id] = successor
        r.superseded_by = successor.id
        return successor.id

    def consolidate(self, tenant_id: str, episodic_id: str,
                    semantic_content: dict) -> str:
        """Episodica -> semantica: SYSTEM_DERIVED con procedencia de 2o orden."""
        src = self._records.get(episodic_id)
        if src is None or src.memory_type != "EPISODIC":
            raise MemoryError("origen no es EPISODIC")
        self._check_tenant(src, tenant_id)
        rec = MemoryRecord(
            memory_type="SEMANTIC", content=semantic_content,
            provenance="SYSTEM_DERIVED", confidence=src.confidence,
            source_ref=f"consolidated-from:{episodic_id}",   # procedencia de 2o orden
            tenant_id=src.tenant_id, subject_id=src.subject_id,
            cognitive_instance_id=src.cognitive_instance_id,
            memory_scope=src.memory_scope)
        self._records[rec.id] = rec
        return rec.id
