"""PERSISTENT MEMORY — contrato 04_MEMORY.md (G5).

Cada item: memory_id, tenant_id, subject_id, cognitive_instance_id, kind,
content/reference, timestamp, provenance, confidence, evidence, version,
integrity metadata (content_hash), lifecycle/state (ACTIVE/SUPERSEDED/FORGOTTEN).

Regla soberana: Memory does NOT silently mutate DigitalSelf — este modulo no
importa ni referencia DigitalSelf en absoluto (test estructural).
"""
from __future__ import annotations
import hashlib, json, os, sys, tempfile, time, uuid

MEMORY_KINDS = ("EPISODIC", "SEMANTIC", "EMOTIONAL", "RELATIONSHIP", "KNOWLEDGE")
PROVENANCE = ("OBSERVED", "INFERRED", "SELF_REPORTED", "SYSTEM_DERIVED", "UNCERTAIN")
LIFECYCLE = ("ACTIVE", "SUPERSEDED", "FORGOTTEN")


class PMemoryError(Exception):
    code = "PMEMORY_ERROR"


class TenantDenied(PMemoryError):
    code = "DENIED_TENANT"


class IntegrityError(PMemoryError):
    code = "INTEGRITY_ERROR"


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _hash(obj) -> str:
    return hashlib.sha256(_canon(obj)).hexdigest()


class PersistentMemoryStore:
    """5 memorias persistentes por tenant, con lifecycle y tamper-evidence."""

    def __init__(self, root: str, ledger_path: str | None = None):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self.ledger = None
        if ledger_path:
            sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
            from el_yo.evidence import EvidenceLedger
            self.ledger = EvidenceLedger(ledger_path)

    def _dir(self, tenant: str) -> str:
        d = os.path.join(self.root, tenant)
        os.makedirs(d, exist_ok=True)
        return d

    def _path(self, tenant: str, memory_id: str) -> str:
        return os.path.join(self._dir(tenant), f"{memory_id}.json")

    def store(self, tenant: str, subject: str, instance: str, kind: str,
              content: dict, provenance: str, confidence: float,
              evidence: tuple, source_ref: str) -> str:
        if kind not in MEMORY_KINDS:
            raise PMemoryError(f"kind desconocido: {kind}")
        if provenance not in PROVENANCE:
            raise PMemoryError(f"provenance invalido: {provenance}")
        if provenance == "INFERRED" and not evidence:
            raise PMemoryError("INFERRED exige evidence")
        mid = f"mem:{uuid.uuid4().hex[:16]}"
        item = {
            "memory_id": mid, "tenant_id": tenant, "subject_id": subject,
            "cognitive_instance_id": instance, "kind": kind, "content": content,
            "timestamp": time.time(), "provenance": provenance,
            "confidence": confidence, "evidence": list(evidence),
            "source_ref": source_ref, "version": 1,
            "content_hash": _hash(content), "lifecycle": "ACTIVE",
            "superseded_by": None, "sensitive": kind == "EMOTIONAL",
        }
        self._atomic_write(tenant, mid, item)
        self._evidence({"type": "memory_store", "memory_id": mid, "kind": kind,
                        "tenant": tenant, "version": 1})
        return mid

    def _atomic_write(self, tenant: str, mid: str, item: dict) -> None:
        path = self._path(tenant, mid)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(item, f, sort_keys=True)
        os.replace(tmp, path)

    def _evidence(self, event: dict) -> None:
        if self.ledger:
            self.ledger.append(event)

    def load(self, tenant: str, memory_id: str) -> dict:
        path = self._path(tenant, memory_id)
        with open(path) as f:
            item = json.load(f)
        if item["tenant_id"] != tenant:
            raise TenantDenied("aislamiento")
        if item["content_hash"] != _hash(item["content"]):
            raise IntegrityError(f"{memory_id}: contenido manipulado")
        return item

    def query(self, tenant: str, kind: str | None = None,
              lifecycle: str = "ACTIVE") -> list:
        out = []
        for fn in os.listdir(self._dir(tenant)):
            if not fn.endswith(".json"):
                continue
            item = self.load(tenant, fn[:-5])
            if kind and item["kind"] != kind:
                continue
            if item["lifecycle"] != lifecycle:
                continue
            out.append(item)
        return out

    def update(self, tenant: str, memory_id: str, new_content: dict,
               evidence: tuple, reason: str) -> str:
        """Versionado: preserva version anterior (SUPERSEDED), crea version nueva."""
        old = self.load(tenant, memory_id)
        if old["lifecycle"] != "ACTIVE":
            raise PMemoryError(f"{memory_id}: lifecycle {old['lifecycle']} no actualizable")
        new_id = f"mem:{uuid.uuid4().hex[:16]}"
        item = dict(old)
        item.update({"memory_id": new_id, "content": new_content, "version": old["version"] + 1,
                     "content_hash": _hash(new_content), "timestamp": time.time(),
                     "lifecycle": "ACTIVE", "evidence": list(evidence),
                     "supersedes": memory_id})
        old["lifecycle"] = "SUPERSEDED"
        old["superseded_by"] = new_id
        self._atomic_write(tenant, memory_id, old)
        self._atomic_write(tenant, new_id, item)
        self._evidence({"type": "memory_update", "from": memory_id, "to": new_id,
                        "version": item["version"], "reason": reason, "tenant": tenant})
        return new_id

    def forget(self, tenant: str, memory_id: str) -> str:
        """FORGOTTEN: tombstone con preservacion de huella (no borrado fisico)."""
        item = self.load(tenant, memory_id)
        item["lifecycle"] = "FORGOTTEN"
        item["content"] = {"forgotten": True}
        item["content_hash"] = _hash(item["content"])
        self._atomic_write(tenant, memory_id, item)
        self._evidence({"type": "memory_forget", "memory_id": memory_id, "tenant": tenant})
        return memory_id
