"""FASE POST-284 — SELF-AWARENESS / METACOGNITIVE ENGINE.

Espejo cognitivo mas preciso; NUNCA decide que persona debe aparecer en el espejo.
El engine NO escribe DigitalSelf. La interaccion genera evidencia, nunca autoridad
para redefinir identidad."""
from __future__ import annotations
import hashlib, json, time
from dataclasses import dataclass, field

STAGES = ("PRESENT", "ABSENT", "UNKNOWN", "UNCERTAIN", "INSUFFICIENT_EVIDENCE")
CONGRUENCE_RESULTS = ("ALIGNED", "POTENTIAL_DISCREPANCY", "UNCERTAIN",
                      "CONTEXT_EXPLAINS", "INSUFFICIENT_EVIDENCE")
PROHIBITED_EVALUATIVE = ("GOOD", "BAD", "RIGHT", "WRONG", "FAILURE", "SUCCESS")
CAPABILITY_KINDS = ("OBSERVED_CAPABILITY", "POTENTIAL_CAPABILITY",
                    "USER_CONFIRMED_CAPABILITY", "UNCERTAIN_CAPABILITY")
CONSCIOUSNESS_TERMS = ("CONSCIENTE", "CONSCIOUS", "EXPERIENCIA SUBJETIVA",
                       "SUBJECTIVE EXPERIENCE")
_ALLOWED_CAPABILITY_NAMES = COGNITIVE_NAMES = ("COGNITIVE SELF-REFLECTION", "METACOGNITION",
    "SELF-MODELING", "COGNITIVE AWARENESS SUPPORT")


class SelfAwarenessError(Exception):
    code = "SELF_AWARENESS_ERROR"


class ProhibitedEvaluation(SelfAwarenessError):
    code = "PROHIBITED_EVALUATION"


class ConsciousnessClaimError(SelfAwarenessError):
    code = "CONSCIOUSNESS_CLAIM"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class CognitiveEvent:
    """EVENT != OBSERVATION != PERCEPTION != INTERPRETATION != HYPOTHESIS != FACT.
    Cada etapa admite PRESENT/ABSENT/UNKNOWN/UNCERTAIN/INSUFFICIENT_EVIDENCE."""
    event_id: str
    actor: str
    target: str
    session_id: str
    relationship_id: str
    timestamp: float
    event_type: str
    content_reference: str
    context_reference: str
    observation: dict           # {"stage": "PRESENT", "statement": str}
    perception: dict
    interpretation: dict
    hypothesis: dict
    provenance: str
    confidence: float
    evidence_ids: tuple
    temporal_validity: tuple    # (valid_from, valid_to)
    tenant_id: str
    owner_id: str
    content_hash: str = field(init=False)

    PROVENANCE_LABELS = ("OBSERVED", "SELF_REPORTED", "INFERRED", "SYSTEM_DERIVED",
                         "UNCERTAIN")

    def __post_init__(self):
        if self.provenance not in self.PROVENANCE_LABELS:
            raise SelfAwarenessError(f"provenance invalido: {self.provenance}")
        for campo in ("observation", "perception", "interpretation", "hypothesis"):
            v = getattr(self, campo)
            if v.get("stage") not in STAGES:
                raise SelfAwarenessError(f"{campo}.stage invalido: {v.get('stage')}")
        payload = {k: getattr(self, k) for k in
                   ("event_id", "actor", "target", "session_id", "relationship_id",
                    "timestamp", "event_type", "content_reference", "context_reference",
                    "observation", "perception", "interpretation", "hypothesis",
                    "provenance", "confidence", "evidence_ids", "temporal_validity",
                    "tenant_id", "owner_id")}
        object.__setattr__(self, "content_hash",
                           hashlib.sha256(_canon(payload)).hexdigest())

    @property
    def fact(self) -> dict:
        """Solo la observacion con stage PRESENT y provenance OBSERVED es hecho."""
        if self.observation["stage"] == "PRESENT" and self.provenance == "OBSERVED":
            return {"stage": "FACT", "statement": self.observation["statement"],
                    "evidence": list(self.evidence_ids)}
        return {"stage": "NOT_FACT", "reason": "observation no PRESENT/OBSERVED"}


class CongruenceAnalyzer:
    """Compara intencion/valor/decision/accion/resultado/reflexion.
    Resultados permitidos: ALIGNED | POTENTIAL_DISCREPANCY | UNCERTAIN |
    CONTEXT_EXPLAINS | INSUFFICIENT_EVIDENCE. PROHIBIDO evaluar moralmente."""

    DIMENSIONS = ("stated_value", "belief", "goal", "intention", "decision",
                  "action", "outcome", "reflection")

    def analyze(self, elements: dict, context_notes: dict | None = None) -> dict:
        present = {k: v for k, v in elements.items() if v}
        if len(present) < 2:
            return {"result": "INSUFFICIENT_EVIDENCE",
                    "details": f"solo {len(present)} elemento(s) con evidencia"}
        values = [str(v).strip().lower() for v in present.values()]
        unique = set(values)
        if len(unique) == 1:
            return {"result": "ALIGNED", "details": "todos los elementos coinciden"}
        if context_notes and self._context_explains(present, context_notes):
            return {"result": "CONTEXT_EXPLAINS",
                    "details": "el contexto documentado explica la divergencia"}
        uncertain = any(v.get("stage") == "UNCERTAIN" if isinstance(v, dict) else False
                        for v in present.values())
        return {"result": "UNCERTAIN" if uncertain else "POTENTIAL_DISCREPANCY",
                "details": f"divergencia entre {len(present)} elementos; sin evaluacion moral"}

    @staticmethod
    def _context_explains(elements, notes) -> bool:
        return bool(notes.get("explains_divergence"))


class UserDefinedCriterion:
    """Solo el usuario define positivo/negativo/importante/aceptable/deseable...
    Un criterio temporal NUNCA se convierte en Value fundamental automaticamente."""

    ALLOWED_AXES = ("positive", "negative", "important", "acceptable", "unacceptable",
                    "desirable", "undesirable")

    def __init__(self, criterion_id: str, axis: str, statement: str, set_by: str,
                 temporal: bool = False):
        if axis not in self.ALLOWED_AXES:
            raise SelfAwarenessError(f"eje invalido: {axis}")
        if set_by != "USER":
            raise SelfAwarenessError("solo el usuario puede establecer criterios")
        self.criterion_id, self.axis, self.statement = criterion_id, axis, statement
        self.temporal = temporal
        self.fundamental = False   # NUNCA automatico

    def to_proposal(self) -> dict:
        return {"type": "criterion", "axis": self.axis, "statement": self.statement,
                "temporal": self.temporal,
                "fundamental_route": "only via Evolution + R1 if user promotes it"}


class CapabilityMirror:
    """OBSERVED | POTENTIAL | USER_CONFIRMED | UNCERTAIN. Nunca POTENTIAL -> identidad."""

    def classify(self, capability: str, evidence: tuple, frequency: int,
                 user_confirmed: bool, provenance: str,
                 confidence: float) -> dict:
        if provenance not in ("OBSERVED", "SELF_REPORTED", "INFERRED", "SYSTEM_DERIVED",
                              "UNCERTAIN"):
            raise SelfAwarenessError(f"provenance invalido: {provenance}")
        if user_confirmed and evidence:
            kind = "USER_CONFIRMED_CAPABILITY"
        elif provenance == "OBSERVED" and frequency >= 3 and evidence:
            kind = "OBSERVED_CAPABILITY"
        elif provenance == "INFERRED" and not evidence:
            kind = "UNCERTAIN_CAPABILITY"
        else:
            kind = "POTENTIAL_CAPABILITY"
        return {"capability": capability, "kind": kind, "evidence": list(evidence),
                "frequency": frequency, "provenance": provenance, "confidence": confidence,
                "is_identity": False,
                "note": "POTENTIAL_CAPABILITY nunca se convierte en identidad automaticamente"}


class SelfContrastEngine:
    """PAST/PRESENT/DESIRED/POTENTIAL. DESIRED != REQUIRED; POTENTIAL != GUARANTEED;
    PAST != PERMANENT_IDENTITY. Informativo, no prescriptivo."""

    def contrast(self, past=None, present=None, desired=None, potential=None) -> dict:
        return {
            "past": past or {"stage": "INSUFFICIENT_EVIDENCE"},
            "present": present or {"stage": "INSUFFICIENT_EVIDENCE"},
            "desired": desired or {"stage": "INSUFFICIENT_EVIDENCE"},
            "potential": potential or {"stage": "INSUFFICIENT_EVIDENCE"},
            "rules": ["DESIRED != REQUIRED", "POTENTIAL != GUARANTEED",
                      "PAST != PERMANENT_IDENTITY"],
            "prescriptive": False, "informational": True,
        }


class Metacognition:
    """Preguntas neutrales; no conducen a respuesta predeterminada; anti-manipulacion."""

    QUESTIONS = (
        "Que observaste realmente?",
        "Que parte de esto estas interpretando?",
        "Que evidencia tienes?",
        "Que otras explicaciones existen?",
        "Esto coincide con lo que dijiste que valoras?",
        "Ha ocurrido antes?",
        "Que cambio?",
        "Que aprendiste?",
    )
    MANIPULATIVE_LEXICON = ("miedo", "culpa", "verguenza", "dependencia", "coercion",
                            "presion", "aislamiento", "falsa certeza", "adulacion",
                            "deberias sentir", "tienes que")

    def questions_for(self, event: CognitiveEvent) -> list:
        out = list(self.QUESTIONS)
        if event.observation["stage"] != "PRESENT":
            out.insert(0, "Que observaste realmente?")
        if event.hypothesis["stage"] in ("PRESENT", "UNCERTAIN"):
            out.append("Que otras explicaciones existen?")
        return out

    def assert_neutral(self, text: str) -> None:
        low = text.lower()
        for w in self.MANIPULATIVE_LEXICON:
            if w in low:
                raise ProhibitedEvaluation(f"lenguaje manipulativo detectado: {w}")

    def assert_no_consciousness_claim(self, text: str) -> None:
        up = text.upper()
        for t in CONSCIOUSNESS_TERMS:
            if t in up and not any(a in up for a in _ALLOWED_CAPABILITY_NAMES):
                raise ConsciousnessClaimError(
                    f"afirmacion de conciencia prohibida: '{t}'. Usar: "
                    "COGNITIVE SELF-REFLECTION / METACOGNITION / SELF-MODELING / "
                    "COGNITIVE AWARENESS SUPPORT")

    def capability_name(self) -> str:
        return "METACOGNITION / SELF-MODELING / COGNITIVE AWARENESS SUPPORT"


class SelfAwarenessEngine:
    """Reconstruccion de procesos, discrepancias, patrones, capacidades, reflexion.
    NO escribe DigitalSelf. Produce CognitiveEvents + insights + propuestas."""

    def __init__(self, congruence: CongruenceAnalyzer | None = None,
                 capabilities: CapabilityMirror | None = None,
                 contrast: SelfContrastEngine | None = None,
                 meta: Metacognition | None = None, clock=None):
        self.congruence = congruence or CongruenceAnalyzer()
        self.capabilities = capabilities or CapabilityMirror()
        self.contrast = contrast or SelfContrastEngine()
        self.meta = meta or Metacognition()
        self.clock = clock or (lambda: time.time())
        self.events: list[CognitiveEvent] = []

    def record_event(self, **kwargs) -> CognitiveEvent:
        ev = CognitiveEvent(timestamp=kwargs.pop("timestamp", self.clock()), **kwargs)
        self.events.append(ev)
        return ev

    def reflection_for(self, event: CognitiveEvent) -> dict:
        """Reflexion estructurada: distingue hecho de interpretacion; nunca concluye identidad."""
        fact = event.fact
        return {
            "event_id": event.event_id,
            "what_happened": event.observation,
            "what_you_perceived": event.perception,
            "how_you_interpreted": event.interpretation,
            "hypothesis": event.hypothesis,
            "fact": fact,
            "metacognitive_questions": self.meta.questions_for(event),
            "identity_conclusion": "NONE (forbidden without Evolution+R1)",
            "provenance": event.provenance, "confidence": event.confidence,
        }

    def detect_patterns(self, events: list | None = None) -> list:
        evs = events if events is not None else self.events
        counts: dict[str, int] = {}
        for e in evs:
            key = f"{e.event_type}:{e.observation.get('statement', '')[:32]}"
            counts[key] = counts.get(key, 0) + 1
        return [{"pattern": k, "count": v, "stage": "PRESENT" if v >= 3 else "UNCERTAIN",
                 "provenance": "OBSERVED", "is_fact": False,
                 "note": "patron no es hecho"} for k, v in counts.items() if v >= 2]

    def evolution_proposal(self, event: CognitiveEvent) -> dict:
        """EVIDENCE->HYPOTHESIS->REFLECTION->PROPOSAL->(R1/G8). Nunca mutacion directa."""
        return {"type": "evolution_proposal", "from_event": event.event_id,
                "evidence": list(event.evidence_ids),
                "route": "Review -> Approval (R1) -> Versioned Update (G8)",
                "direct_mutation": "PROHIBITED"}
