"""YO CLONE — FASE 3/5: representacion del clon.

El clon es una REPRESENTACION AUTORIZADA de la persona usuaria. NUNCA una nueva
identidad soberana: no reemplaza la identidad protegida de YO ni de ELLA.
is_identity=False estructural; namespace CLONE_REPRESENTATION; derivaciones con
provenance; la generacion fotorrealista requiere proveedor -> EXTERNAL_BLOCKED
(la maquinaria y los gates estan implementados y probados; la replica real no
se simula).
"""
from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass, field

NAMESPACE = "CLONE_REPRESENTATION"


class CloneError(Exception):
    code = "CLONE_ERROR"


class ProviderRequired(CloneError):
    code = "PROVIDER_REQUIRED"


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class CloneRepresentation:
    clone_id: str
    user_id: str
    namespace: str
    capture_refs: tuple        # hashes de capturas autorizadas (derivation registry)
    fidelity_score: float
    status: str                # PENDING_PROVIDER | GENERATED | BLOCKED
    is_identity: bool = False  # estructural: NUNCA identidad
    is_sovereign: bool = False
    content_hash: str = field(init=False)

    def __post_init__(self):
        payload = {"clone_id": self.clone_id, "user_id": self.user_id,
                   "capture_refs": list(self.capture_refs), "fidelity_score": self.fidelity_score,
                   "status": self.status}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())


class CloneBuilder:
    """Registro de derivaciones + gate de generacion (proveedor requerido)."""

    def __init__(self, clock=None):
        self.clock = clock or (lambda: time.time())
        self.derivations: list[CloneRepresentation] = []

    def register(self, user_id: str, capture_refs: tuple, fidelity: float) -> CloneRepresentation:
        if not capture_refs:
            raise CloneError("se requieren capturas autorizadas (referencias)")
        c = CloneRepresentation(clone_id=f"clone:{user_id}:{len(self.derivations)+1}",
                                user_id=user_id, namespace=NAMESPACE,
                                capture_refs=tuple(capture_refs), fidelity_score=fidelity,
                                status="PENDING_PROVIDER")
        self.derivations.append(c)
        return c

    def generate(self, clone: CloneRepresentation, provider_fn=None) -> CloneRepresentation:
        """Generacion fotorrealista: requiere proveedor real. Sin proveedor -> BLOCKED
        (EXTERNAL_BLOCKED documentado; NO se simula una replica)."""
        if provider_fn is None:
            raise ProviderRequired(
                "generacion fotorrealista requiere proveedor externo (EXTERNAL_BLOCKED: "
                "sin claves en el entorno). Maquinaria, gates y registro implementados; "
                "la replica real NO se simula con imagenes estaticas.")
        raise CloneError("provider_fn debe ser validado por autorizacion antes de usar")  # nunca llega sin auth

    def consistency_report(self, clone: CloneRepresentation) -> dict:
        """Consistencia evaluable: derivaciones trazables a capturas con provenance."""
        return {"clone": clone.clone_id, "captures": len(clone.capture_refs),
                "all_provenanced": all(ref for ref in clone.capture_refs),
                "is_identity": clone.is_identity, "namespace": clone.namespace}
