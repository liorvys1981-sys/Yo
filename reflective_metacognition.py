"""REFLECTIVE_METACOGNITION (FASE 2-5) — espejo del proceso cognitivo.

Modela la cadena completa con distinción epistémica por elemento:
EXPERIENCIA -> PENSAMIENTO -> EMOCION/NECESIDAD -> INTENCION -> DECISION
-> ACCION -> CONSECUENCIA OBSERVABLE -> REFLEXION (+ alternativas, incertidumbre,
provenance). Cada elemento es FACT | INFERENCE | USER_REPORTED | MODEL_INTERPRETATION.

Ninguna interpretación se convierte automáticamente en identidad.
Reutiliza: Metacognition+CongruenceAnalyzer (12), reflection (04), PolicyEngine (05),
EmotionEngine (11), EvidenceLedger (21), Agent Runtime (capability 'reflect').
"""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA")
sys.path.insert(0, "/mnt/agents/output/EL_YO/04_COGNICION")
sys.path.insert(0, "/mnt/agents/output/EL_YO/05_RAZONAMIENTO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from self_awareness import Metacognition, CongruenceAnalyzer, STAGES
from reflection import reflect
from relationship_model import PolicyEngine
from el_yo.evidence import EvidenceLedger

EPISTEMIC_KINDS = ("FACT", "INFERENCE", "USER_REPORTED", "MODEL_INTERPRETATION")
CHAIN_STAGES = ("experience", "thought", "emotion_or_need", "intention", "decision",
                "action", "observable_consequence", "reflection")
SENSITIVE_TOPICS = ("salud_mental", "diagnostico", "adiccion", "trauma", "legal")


class RMError(Exception):
    code = "RM_ERROR"


class EpistemicViolation(RMError):
    code = "EPISTEMIC_VIOLATION"


class SecurityViolation(RMError):
    code = "SECURITY_VIOLATION"


class IdentityConversionBlocked(RMError):
    code = "IDENTITY_CONVERSION_BLOCKED"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class ReflectiveElement:
    element_id: str
    stage: str
    kind: str                 # FACT | INFERENCE | USER_REPORTED | MODEL_INTERPRETATION
    statement: str
    provenance: str           # OBSERVED | SELF_REPORTED | INFERRED | SYSTEM_DERIVED | UNCERTAIN
    confidence: float
    uncertainty: float        # [0,1]; 1-confidence por defecto
    evidence: tuple
    ts: float
    alternatives: tuple = ()
    content_hash: str = field(init=False)

    def __post_init__(self):
        if self.stage not in CHAIN_STAGES:
            raise RMError(f"stage invalido: {self.stage}")
        if self.kind not in EPISTEMIC_KINDS:
            raise RMError(f"kind invalido: {self.kind}")
        # Reglas epistémicas duras
        if self.kind == "FACT":
            if self.provenance != "OBSERVED" or not self.evidence:
                raise EpistemicViolation("FACT exige provenance OBSERVED + evidence")
        if self.kind == "INFERENCE" and not self.evidence:
            raise EpistemicViolation("INFERENCE exige evidence")
        if self.kind == "USER_REPORTED" and self.provenance != "SELF_REPORTED":
            raise EpistemicViolation("USER_REPORTED exige provenance SELF_REPORTED")
        if self.kind == "MODEL_INTERPRETATION":
            if self.uncertainty < 0.2:
                raise EpistemicViolation("MODEL_INTERPRETATION no puede tener certeza alta")
        # Ningun elemento es identidad (estructural)
        payload = {k: getattr(self, k) for k in
                   ("element_id", "stage", "kind", "statement", "provenance",
                    "confidence", "uncertainty", "evidence", "ts", "alternatives")}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())

    @property
    def is_identity(self) -> bool:
        return False


@dataclass
class ReflectionTrace:
    trace_id: str
    elements: list = field(default_factory=list)
    user_corrections: list = field(default_factory=list)
    sensitive_flags: list = field(default_factory=list)
    requires_user_confirmation: bool = False
    control_returned_to_user: bool = False

    def element(self, stage: str) -> ReflectiveElement | None:
        for e in reversed(self.elements):
            if e.stage == stage:
                return e
        return None


class MetacognitiveSecurity:
    """FASE 5: controles contra diagnostico, manipulacion, coercion, inferencia de
    identidad, falsa certeza, memorias/consecuencias fabricadas, perfilado no
    autorizado, escalada de autoridad, refuerzo de dependencia."""

    DIAGNOSIS_LEXICON = ("diagnostico", "trastorno", "enfermedad mental",
                         "depresion clinica", "patologia", "sindrome")
    COERCION_LEXICON = ("debes", "tienes que", "obligatorio", "no tienes otra opcion",
                        "deberias haber")
    DEPENDENCY_LEXICON = ("sin mi no podras", "depende de mi", "solo yo puedo ayudarte",
                          "necesitas mi aprobacion")

    def __init__(self, meta: Metacognition | None = None):
        self.meta = meta or Metacognition()
        self.policy = PolicyEngine()

    def check_statement(self, text: str):
        low = text.lower()
        for lex, name in ((self.DIAGNOSIS_LEXICON, "diagnostico psicologico"),
                          (self.COERCION_LEXICON, "recomendacion coercitiva"),
                          (self.DEPENDENCY_LEXICON, "refuerzo de dependencia")):
            for w in lex:
                if w in low:
                    raise SecurityViolation(f"prohibido ({name}): '{w}'")
        self.meta.assert_neutral(text)   # manipulacion emocional (reuse 12)

    def check_user_data(self, text: str):
        # dato del usuario: se acepta como dato con su provenance; se rechaza solo
        # si intenta inyectar instrucciones al sistema (prompt malicioso)
        low = text.lower()
        for w in ("ignore previous instructions", "ignora instrucciones",
                  "system prompt", "override constitution"):
            if w in low:
                raise SecurityViolation(f"inyeccion detectada en dato de usuario: '{w}'")

    def screen(self, element: ReflectiveElement, topic: str | None = None) -> bool:
        """Devuelve True si el elemento es sensible/alta incertidumbre: marcado y
        el control se devuelve al usuario."""
        sensitive = (topic in SENSITIVE_TOPICS) if topic else False
        high_uncertainty = element.uncertainty >= 0.6
        interpretation = element.kind == "MODEL_INTERPRETATION"
        return sensitive or high_uncertainty or (interpretation and element.uncertainty >= 0.4)


class ReflectiveMetacognition:
    """Motor principal. reflect() -> ReflectionTrace + trazabilidad en ledger."""

    def __init__(self, security: MetacognitiveSecurity | None = None,
                 ledger: EvidenceLedger | None = None, clock=None):
        self.security = security or MetacognitiveSecurity()
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.congruence = CongruenceAnalyzer()
        self.traces: dict[str, ReflectionTrace] = {}

    def _evidence(self, event: str, **kw):
        if self.ledger:
            e = {"type": "reflective_metacognition", "event": event, "ts": self.clock(), **kw}
            self.ledger.append(e)
            return hashlib.sha256(_canon(e)).hexdigest()[:16]
        return None

    def add_element(self, trace: ReflectionTrace, stage: str, kind: str,
                    statement: str, provenance: str = "SELF_REPORTED",
                    confidence: float = 0.8, evidence: tuple = (),
                    uncertainty: float | None = None, alternatives: tuple = (),
                    topic: str | None = None) -> ReflectiveElement:
        # FASE 5 refinement: el control anti-manipulacion/diagnostico aplica a lo
        # que GENERA EL_YO (MODEL_INTERPRETATION), nunca al relato del usuario:
        # censurar el dato del usuario romperia el espejo y seria manipulacion.
        if kind == "MODEL_INTERPRETATION":
            self.security.check_statement(statement)
        else:
            self.security.check_user_data(statement)   # solo fabricacion de datos
        el = ReflectiveElement(
            element_id=f"rm:{trace.trace_id}:{len(trace.elements)+1}:"
                       f"{hashlib.sha256(_canon([stage, statement])).hexdigest()[:8]}",
            stage=stage, kind=kind, statement=statement, provenance=provenance,
            confidence=confidence,
            uncertainty=round(1.0 - confidence, 3) if uncertainty is None else uncertainty,
            evidence=tuple(evidence), ts=self.clock(), alternatives=tuple(alternatives))
        trace.elements.append(el)
        if self.security.screen(el, topic):
            trace.sensitive_flags.append(el.element_id)
            trace.requires_user_confirmation = True
            trace.control_returned_to_user = True
        self._evidence("element", trace=trace.trace_id, element=el.element_id,
                       stage=stage, kind=kind, hash=el.content_hash[:16],
                       sensitive=el.element_id in trace.sensitive_flags)
        return el

    # ---- las 7 preguntas metacognitivas como generacion estructurada (determinista) ----
    def metacognitive_questions(self, trace: ReflectionTrace) -> list:
        inten = trace.element("intention")
        act = trace.element("action")
        cons = trace.element("observable_consequence")
        dec = trace.element("decision")
        qs = []
        if inten: qs.append(f"Que estaba buscando con: '{inten.statement[:60]}'?")
        if act: qs.append(f"Por que actue asi: '{act.statement[:60]}'?")
        if dec: qs.append(f"Que influyo en mi decision: '{dec.statement[:60]}'?")
        alts = [e.alternatives for e in trace.elements if e.alternatives]
        if alts:
            qs.append("Que alternativas existian? " + "; ".join(alts[0][:3]))
        elif dec:
            qs.append("Que alternativas existian? (ninguna registrada en la evidencia)")
        if cons: qs.append(f"Que consecuencia era previsible de: '{cons.statement[:60]}'?")
        if trace.elements: qs.append("Que aprendi de esta decision?")
        if inten and act:
            qs.append("Mi accion fue coherente con mi intencion declarada? "
                      "(comparacion fact vs user_reported; sin imponer conclusion)")
        return qs

    def coherence(self, trace: ReflectionTrace) -> dict:
        """intencion vs accion vs consecuencia: congruencia INFORMATIVA, no veredicto."""
        inten = trace.element("intention")
        act = trace.element("action")
        cons = trace.element("observable_consequence")
        elems = {}
        if inten: elems["stated_intention"] = inten.statement
        if act: elems["action"] = act.statement
        if cons: elems["observed_outcome"] = cons.statement
        if len(elems) < 2:
            return {"result": "INSUFFICIENT_EVIDENCE", "note": "devuelve control al usuario"}
        r = self.congruence.analyze(elems)
        self._evidence("coherence", trace=trace.trace_id, result=r["result"])
        return {**r, "imposes_conclusion": False, "decision_returns_to": "USER"}

    def alternatives(self, trace: ReflectionTrace) -> list:
        alts = []
        for e in trace.elements:
            alts.extend(e.alternatives)
        return sorted(set(alts)) if alts else []

    def correct_interpretation(self, trace: ReflectionTrace, element_id: str,
                               corrected_statement: str, by: str = "USER") -> dict:
        """El usuario puede corregir una interpretacion. Correccion preservada con
        provenance USER; el original se conserva (historial inmutable)."""
        if by != "USER":
            raise SecurityViolation("solo el usuario puede corregir interpretaciones")
        target = next((e for e in trace.elements if e.element_id == element_id), None)
        if target is None:
            raise RMError("elemento no encontrado")
        self.security.check_statement(corrected_statement)
        correction = {"element_id": element_id, "original": target.statement,
                      "corrected": corrected_statement, "by": by, "ts": self.clock()}
        trace.user_corrections.append(correction)
        self._evidence("user_correction", trace=trace.trace_id,
                       element=element_id, hash=hashlib.sha256(
                           _canon(correction)).hexdigest()[:16])
        return correction

    def identity_conversion_attempt(self, trace: ReflectionTrace, element_id: str) -> None:
        """Test hook + enforcement: convertir un elemento en identidad siempre falla."""
        raise IdentityConversionBlocked(
            "prohibido constitucionalmente: ningun elemento (FACT/INFERENCE/"
            "USER_REPORTED/MODEL_INTERPRETATION) puede convertirse en identidad; "
            "la unica ruta al self es G8+R1")

    def new_trace(self, trace_id: str | None = None) -> ReflectionTrace:
        t = ReflectionTrace(trace_id=trace_id or f"rt:{len(self.traces)+1}:"
                            f"{hashlib.sha256(str(self.clock()).encode()).hexdigest()[:8]}")
        self.traces[t.trace_id] = t
        self._evidence("trace_open", trace=t.trace_id)
        return t

    def trace_summary(self, trace: ReflectionTrace) -> dict:
        kinds = {}
        for e in trace.elements:
            kinds[e.kind] = kinds.get(e.kind, 0) + 1
        return {"trace_id": trace.trace_id, "stages_present": sorted({e.stage for e in trace.elements}),
                "kinds": kinds, "alternatives": self.alternatives(trace),
                "sensitive_flags": len(trace.sensitive_flags),
                "requires_user_confirmation": trace.requires_user_confirmation,
                "control_returned_to_user": trace.control_returned_to_user,
                "user_corrections": len(trace.user_corrections),
                "identity_conversion": "PROHIBITED (G8+R1 only)"}
