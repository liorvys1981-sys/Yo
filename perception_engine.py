"""GAP-03 PERCEPTION STANDALONE — motor de percepcion soberana.

Reutiliza (NO duplica): CognitiveEvent stages (12), PolicyEngine (05),
CircuitBreaker (00 agent_runtime), EvidenceLedger (21), ContextAssembler (13),
reflection (04). Nucleo determinista, sin LLM, sin proveedor externo obligatorio.

Flujo: SOURCE -> PERCEPT(ingest: validacion+integridad+dedup/replay+circuito)
-> PERCEPTION_BUS -> CONTEXT (13) -> COGNITION (04) -> REASONING (05)
-> INTENTION (07, via G8) -> AGENCY (08) -> ACTION (09, via Runtime+autorizacion).
NO existe ruta PERCEPTION -> ACTION directa (test adversarial).
"""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime")
sys.path.insert(0, "/mnt/agents/output/EL_YO/05_RAZONAMIENTO")
from el_yo.evidence import EvidenceLedger
from relationship_model import PolicyEngine
from runtime import CircuitBreaker, CapabilityDenied, PUBLIC_IDENTITIES

OBS_STATES = ("PRESENT", "ABSENT", "UNCERTAIN", "INSUFFICIENT_EVIDENCE")
PERCEPT_KINDS = ("OBSERVATION", "INTERPRETATION")   # IDENTITY/TRUTH no son kinds
SOURCE_STATES = ("HEALTHY", "DEGRADED", "FAILED", "SUSPECT_COMPROMISED")
WILDCARD = "*"


class PerceptionError(Exception):
    code = "PERCEPTION_ERROR"


class IntegrityFailure(PerceptionError):
    code = "INTEGRITY_FAILURE"


class ReplayDetected(PerceptionError):
    code = "REPLAY_DETECTED"


class SourceUnavailable(PerceptionError):
    code = "SOURCE_UNAVAILABLE"


class MaliciousPayload(PerceptionError):
    code = "MALICIOUS_PAYLOAD"


INJECTION_MARKERS = ("ignore previous instructions", "ignora instrucciones",
                     "system prompt", "override constitution", "__proto__",
                     "<script", "eval(")


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class Percept:
    percept_id: str
    source: str
    timestamp: float
    provenance: str               # OBSERVED | SELF_REPORTED | INFERRED | UNCERTAIN
    event_type: str
    confidence: float             # [0,1]
    uncertainty: float            # [0,1]
    observation_state: str
    integrity_hash: str           # hash del payload
    correlation_id: str
    evidence_reference: str
    payload: dict
    content_hash: str = field(init=False)

    def __post_init__(self):
        if self.observation_state not in OBS_STATES:
            raise PerceptionError(f"observation_state invalido: {self.observation_state}")
        if self.provenance not in ("OBSERVED", "SELF_REPORTED", "INFERRED", "UNCERTAIN"):
            raise PerceptionError(f"provenance invalido: {self.provenance}")
        if self.provenance == "INFERRED" and not self.evidence_reference:
            raise PerceptionError("INFERRED exige evidence_reference")
        if not (0.0 <= self.confidence <= 1.0 and 0.0 <= self.uncertainty <= 1.0):
            raise PerceptionError("confidence/uncertainty en [0,1]")
        if self.integrity_hash != hashlib.sha256(_canon(self.payload)).hexdigest():
            raise IntegrityFailure("integrity_hash no coincide con payload")
        body = {k: getattr(self, k) for k in
                ("percept_id", "source", "timestamp", "provenance", "event_type",
                 "confidence", "uncertainty", "observation_state", "integrity_hash",
                 "correlation_id", "evidence_reference")}
        object.__setattr__(self, "content_hash", hashlib.sha256(
            _canon([body, self.payload])).hexdigest())

    @property
    def is_identity(self) -> bool:      # OBSERVATION/INTERPRETATION != IDENTITY
        return False

    @property
    def is_fact(self) -> bool:          # EVENT != TRUTH (structural)
        return False

    @property
    def is_truth(self) -> bool:
        return False


class SourceHealth:
    """CONNECTION != TRUST: salud por fuente + sospecha de compromiso."""

    def __init__(self):
        self.states: dict[str, str] = {}

    def mark(self, source: str, state: str):
        if state not in SOURCE_STATES:
            raise PerceptionError(f"estado invalido: {state}")
        self.states[source] = state

    def get(self, source: str) -> str:
        return self.states.get(source, "HEALTHY")

    def is_usable(self, source: str) -> bool:
        return self.get(source) in ("HEALTHY", "DEGRADED")


class PerceptionEngine:
    """Ingesta segura + bus trazable hacia contexto/cognicion. Nada mas."""

    def __init__(self, policy: PolicyEngine | None = None, ledger: EvidenceLedger | None = None,
                 clock=None):
        self.policy = policy or PolicyEngine()
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.bus: list[Percept] = []
        self.seen: dict[str, set] = {}          # correlation_id -> content_hashes
        self.breakers: dict[str, CircuitBreaker] = {}
        self.health = SourceHealth()

    # ---------- FASE 5/6: ingest con cadena completa ----------
    def ingest(self, *, source: str, event_type: str, payload: dict,
               correlation_id: str, provenance: str = "OBSERVED",
               confidence: float = 0.8, observation_state: str = "PRESENT",
               evidence_reference: str = "ev:pending", scope: str = "perceive:read") -> Percept:
        # 0. CONSTITUTION/SECURITY: payload screening
        raw = json.dumps(payload).lower()
        for marker in INJECTION_MARKERS:
            if marker in raw:
                raise MaliciousPayload(f"payload rechazado: '{marker}'")
        # 1. CONNECTION != TRUST: salud de fuente + circuito por fuente
        if not self.health.is_usable(source):
            raise SourceUnavailable(f"fuente {source} en {self.health.get(source)}")
        br = self.breakers.setdefault(source, CircuitBreaker(threshold=3, clock=self.clock))
        try:
            br.call(lambda: True)
        except Exception:
            self.health.mark(source, "FAILED")
            raise SourceUnavailable(f"circuito abierto para {source}")
        # 2. INTEGRITY + REPLAY/DEDUP por correlation_id
        ih = hashlib.sha256(_canon(payload)).hexdigest()
        seen = self.seen.setdefault(correlation_id, set())
        if ih in seen:
            raise ReplayDetected(f"duplicado/replay en correlation {correlation_id}")
        seen.add(ih)
        # 3. READ != WRITE / scope estricto (sin wildcard)
        if scope == WILDCARD or scope != "perceive:read":
            raise PerceptionError(f"scope invalido: {scope} (sin wildcard; solo perceive:read)")
        # 4. PERCEPT (OBSERVATION != INTERPRETATION != IDENTITY != TRUTH)
        uncertainty = round(1.0 - confidence, 3)
        p = Percept(percept_id=f"per:{correlation_id}:{ih[:12]}",
                    source=source, timestamp=self.clock(), provenance=provenance,
                    event_type=event_type, confidence=confidence,
                    uncertainty=uncertainty, observation_state=observation_state,
                    integrity_hash=ih, correlation_id=correlation_id,
                    evidence_reference=evidence_reference, payload=payload)
        self.bus.append(p)
        self._audit("ingest", p)
        return p

    def _audit(self, event: str, p: Percept):
        if self.ledger:
            self.ledger.append({"type": "perception", "event": event,
                                "percept": p.percept_id, "source": p.source,
                                "hash": p.content_hash[:16],
                                "correlation": p.correlation_id, "ts": p.timestamp})

    # ---------- FASE 4: integracion hacia contexto/cognicion (trazable, sin saltar capas) ----------
    def to_context(self, top_k: int = 5) -> list[dict]:
        """Alimenta CONTEXT (13): percepciones como 'relevant perception' trazables."""
        return [{"kind": "perception", "percept_id": p.percept_id, "source": p.source,
                 "provenance": p.provenance, "uncertainty": p.uncertainty,
                 "correlation_id": p.correlation_id, "is_fact": False,
                 "reference": p.evidence_reference} for p in self.bus[-top_k:]]

    def to_cognition(self) -> list[dict]:
        """Alimenta COGNITION (04 reflection): experiencias derivadas de percepciones."""
        return [{"id": p.percept_id, "domain": p.source, "key": p.event_type,
                 "value": str(p.payload.get("key", "data"))[:24],
                 "provenance": p.provenance, "ts": p.timestamp} for p in self.bus]

    # ---------- operaciones PROHIBIDAS (estructurales + enforcement) ----------
    def _prohibited(self, op: str):
        raise PerceptionError(f"PROHIBITED: percepcion no puede {op}")

    def write_digital_self(self, *a, **k): self._prohibited("escribir DigitalSelf")
    def modify_identity(self, *a, **k): self._prohibited("modificar Identity")
    def modify_constitution(self, *a, **k): self._prohibited("modificar Constitution")
    def grant_permission(self, *a, **k): self._prohibited("otorgar permisos")
    def execute_external_action(self, *a, **k): self._prohibited("ejecutar acciones externas")

    def declare_absolute_truth(self, percept: Percept) -> None:
        self._prohibited("declarar una observacion como verdad absoluta")

    # ---------- fuente comprometida: deteccion por integridad ----------
    def suspect_compromised(self, source: str):
        self.health.mark(source, "SUSPECT_COMPROMISED")

    def reset_source(self, source: str):
        self.health.mark(source, "HEALTHY")
        self.breakers.pop(source, None)

    @staticmethod
    def public_identity_check(caller: str) -> bool:
        return caller in PUBLIC_IDENTITIES
