"""DIGITAL SELF — contrato fundacional del Cognitive Twin (FROZEN).

Regla de capas:
  DigitalSelf  = estructura estable del YO (este modulo: contrato congelado)
  Memory       = registra experiencias/contexto (NO aqui)
  Reflection   = interpreta (NO aqui)
  Evolution    = propone y versiona cambios (el versionado interno es del SELF,
                 Evolution propone CAMBIOS a traves del gate; no redefine estructura)
  Cognitive Graph = relaciones, NO define identidad (NO aqui)

Inmutable despues del FREEZE: cambios a este contrato exigen gate de evolucion
con cambio de version MAYOR del contrato.
"""
from __future__ import annotations
import time, uuid
from dataclasses import dataclass, field

PROVENANCE = ("OBSERVED", "INFERRED", "SELF_REPORTED", "SYSTEM_DERIVED", "UNCERTAIN")
# v2.0.0: Beliefs promovido a fundamental (decision soberana, evolucion trazada en DIGITAL_SELF_EVOLUTION_v1_to_v2.json)
FUNDAMENTAL_KINDS = ("Identity", "Values", "Beliefs")
ENTITY_KINDS = ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences")


class DigitalSelfError(Exception):
    code = "DIGITAL_SELF_ERROR"


class InvalidProvenance(DigitalSelfError):
    code = "INVALID_PROVENANCE"


class UnknownEntityKind(DigitalSelfError):
    code = "UNKNOWN_ENTITY_KIND"


class VersionIntegrityError(DigitalSelfError):
    code = "VERSION_INTEGRITY_ERROR"


def _canon(obj) -> bytes:
    import json as _json
    return _json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class EntityVersion:
    version: int
    content: dict
    provenance: str
    confidence: float
    evidence: tuple          # inmutable
    source_ref: str
    ts: float
    change_reason: str
    approved_by: str = "system"   # "humano" obligatorio para cambios fundamentales
    content_hash: str = ""        # tamper-evidence (dicts anidados no son congelables)

    def __post_init__(self):
        import hashlib as _h
        object.__setattr__(self, "content_hash",
                           self.content_hash or _h.sha256(_canon(self.content)).hexdigest())

    def verify_integrity(self) -> bool:
        import hashlib as _h
        if _h.sha256(_canon(self.content)).hexdigest() != self.content_hash:
            raise VersionIntegrityError(
                f"version {self.version}: contenido manipulado tras el sellado")
        return True


@dataclass
class SelfEntity:
    """Entidad del Digital Self: versionada, con provenance y reconstruccion temporal."""
    kind: str
    entity_id: str = field(default_factory=lambda: f"self:{uuid.uuid4().hex[:12]}")
    created_at: float = field(default_factory=time.time)
    versions: list = field(default_factory=list)
    active_version: int = 0

    def __post_init__(self):
        if self.kind not in ENTITY_KINDS:
            raise UnknownEntityKind(self.kind)

    # --- versionado ---
    def set(self, content: dict, provenance: str, confidence: float,
            evidence: tuple, source_ref: str, change_reason: str,
            approved_by: str = "system", ts: float | None = None) -> int:
        if provenance not in PROVENANCE:
            raise InvalidProvenance(provenance)
        if self.kind in FUNDAMENTAL_KINDS and provenance in ("INFERRED", "SYSTEM_DERIVED"):
            raise DigitalSelfError(
                f"{self.kind} es fundamental: no admite {provenance} (provenance o nada)")
        if not (0.0 <= confidence <= 1.0):
            raise DigitalSelfError("confidence fuera de [0,1]")
        if not evidence and provenance == "INFERRED":
            raise DigitalSelfError("INFERRED exige evidence")
        v = EntityVersion(
            version=len(self.versions) + 1, content=content, provenance=provenance,
            confidence=confidence, evidence=tuple(evidence), source_ref=source_ref,
            ts=time.time() if ts is None else ts, change_reason=change_reason,
            approved_by=approved_by)
        self.versions.append(v)
        self.active_version = v.version          # la nueva version pasa a activa
        return v.version                          # versiones anteriores preservadas

    @property
    def active(self) -> EntityVersion:
        if not self.versions:
            raise VersionIntegrityError(f"{self.kind}: sin versiones aun")
        return self.versions[self.active_version - 1]

    def version(self, n: int) -> EntityVersion:
        if not 1 <= n <= len(self.versions):
            raise VersionIntegrityError(f"version {n} no existe")
        return self.versions[n - 1]

    # --- temporalidad: reconstruir estado anterior ---
    def as_of(self, ts: float) -> EntityVersion | None:
        """Ultima version vigente en ts (estado reconstruible; historial inmutable)."""
        prior = [v for v in self.versions if v.ts <= ts]
        return prior[-1] if prior else None

    def provenance_of_active(self) -> str:
        return self.active.provenance


class DigitalSelf:
    """El YO estable: 7 entidades. Identity/Values = fundamentales (gate reforzado)."""

    def __init__(self, subject_id: str, tenant_id: str):
        if not subject_id or not tenant_id:
            raise DigitalSelfError("subject_id y tenant_id obligatorios")
        self.subject_id = subject_id
        self.tenant_id = tenant_id
        self.entities: dict[str, SelfEntity] = {}

    def create(self, kind: str) -> SelfEntity:
        if kind in self.entities:
            raise DigitalSelfError(f"{kind} ya existe (una por self)")
        e = SelfEntity(kind=kind)
        self.entities[kind] = e
        return e

    def get(self, kind: str) -> SelfEntity:
        return self.entities[kind]

    def reconstruct(self, ts: float) -> dict:
        """Snapshot completo del self como estaba en ts (todas las entidades)."""
        snap = {}
        for kind, e in self.entities.items():
            v = e.as_of(ts)
            if v:
                snap[kind] = {"version": v.version, "content": v.content,
                              "provenance": v.provenance, "ts": v.ts}
        return snap

    def provenance_breakdown(self) -> dict:
        out = {p: 0 for p in PROVENANCE}
        for e in self.entities.values():
            if not e.versions:          # entidad vacia: sin contenido que clasificar
                continue
            out[e.active.provenance] += 1
        return out

    def schema_conformant(self) -> bool:
        """Estructura estable: las 7 entidades presentes (una por kind)."""
        return all(k in self.entities for k in ENTITY_KINDS)
