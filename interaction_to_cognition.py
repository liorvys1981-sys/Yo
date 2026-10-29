"""FASE POST-284 — INTERACTION-TO-COGNITION ENGINE + RELATIONAL COGNITION.

INTERACTION->SESSION->TURN->SIGNAL->EXPERIENCE->OBSERVATION->CONTEXT->PATTERN CANDIDATE->
HYPOTHESIS->REFLECTION->EVIDENCE. No todo turno genera experiencia relevante.
Namespaces estrictos: YO_OBSERVATION / ELLA_OBSERVATION / RELATIONAL_OBSERVATION.
ELLA_OBSERVATION -/-> YO_IDENTITY; YO_OBSERVATION -/-> ELLA_IDENTITY."""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from self_awareness import CognitiveEvent, STAGES, SelfAwarenessError

INFO_KINDS = ("USER_STATED", "OBSERVED", "INFERRED", "SYSTEM_DERIVED", "UNCERTAIN",
              "IMAGINED", "GENERATED", "RELATIONAL_OBSERVATION")
NAMESPACES = ("YO_OBSERVATION", "ELLA_OBSERVATION", "RELATIONAL_OBSERVATION")


class InteractionError(Exception):
    code = "INTERACTION_ERROR"


class NamespaceViolation(InteractionError):
    code = "NAMESPACE_VIOLATION"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass
class InteractionRecord:
    interaction_id: str
    session_id: str
    relationship_id: str
    actor: str
    recipient: str
    timestamp: float
    content_reference: str
    context_reference: str
    observations: list
    user_stated_information: list
    system_observations: list
    hypotheses: list
    confidence: float
    provenance: str
    evidence_ids: tuple
    tenant_id: str
    owner_id: str
    content_hash: str = field(init=False)

    def __post_init__(self):
        payload = {k: getattr(self, k) for k in
                   ("interaction_id", "session_id", "relationship_id", "actor", "recipient",
                    "timestamp", "content_reference", "context_reference", "observations",
                    "user_stated_information", "system_observations", "hypotheses",
                    "confidence", "provenance", "evidence_ids", "tenant_id", "owner_id")}
        self.content_hash = hashlib.sha256(_canon(payload)).hexdigest()


class InformationLayer:
    """Distingue USER_STATED/OBSERVED/INFERRED/SYSTEM_DERIVED/UNCERTAIN/IMAGINED/GENERATED/
    RELATIONAL_OBSERVATION. 'ELLA: prefiero X' -> ELLA_USER_STATED_INFORMATION;
    NUNCA ELLA_IDENTITY_VALUE automaticamente."""

    def classify(self, statement: str, speaker: str, provenance: str) -> dict:
        if provenance not in INFO_KINDS:
            raise InteractionError(f"provenance invalido: {provenance}")
        who = "ELLA" if speaker.upper().startswith("ELLA") else \
              ("YO" if speaker.upper().startswith("YO") else "OTHER")
        if provenance in ("USER_STATED", "SELF_STATED") or (speaker.upper().startswith(("ELLA", "YO"))
                                                            and provenance == "USER_STATED"):
            layer = f"{who}_USER_STATED_INFORMATION"
        else:
            layer = f"{who}_{provenance}_INFORMATION"
        return {"layer": layer, "statement": statement, "provenance": provenance,
                "is_identity_value": False,
                "identity_route": "only via activation/authorization chain",
                "namespace": f"{who}_OBSERVATION" if provenance != "RELATIONAL_OBSERVATION"
                             else "RELATIONAL_OBSERVATION"}


class RelationalModel:
    """YO <-> ELLA. Conserva interacciones/experiencias/patrones/expectativas/preferencias/
    acuerdos/desacuerdos/cambios/incertidumbre/evolucion temporal. SIN autoridad sobre identidad."""

    def __init__(self, relationship_id: str, ledger=None, clock=None):
        self.relationship_id = relationship_id
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.interactions: list[InteractionRecord] = []
        self.shared_experiences: list = []
        self.patterns: list = []
        self.expectations: list = []
        self.expressed_preferences: list = []
        self.agreements: list = []
        self.disagreements: list = []
        self.changes: list = []
        self.uncertainty: list = []
        self.has_authority_over_identity = False

    def record(self, rec: InteractionRecord):
        if rec.relationship_id != self.relationship_id:
            raise InteractionError("interaction de otra relacion")
        self.interactions.append(rec)
        if self.ledger:
            self.ledger.append({"type": "relational", "interaction": rec.interaction_id,
                                "hash": rec.content_hash})

    def reconstruct(self, t: float) -> dict:
        """RELATIONSHIP @ T sin destruir historial (filtro temporal sobre copia)."""
        inter = [r for r in self.interactions if r.timestamp <= t]
        return {"relationship_id": self.relationship_id, "at": t,
                "interactions": len(inter), "patterns": list(self.patterns),
                "uncertainty": list(self.uncertainty),
                "authority_over_identity": False}


class InteractionToCognitionEngine:
    """Pipeline completo con gates de relevancia entre etapas."""

    def __init__(self, awareness, ledger=None, clock=None):
        self.awareness = awareness
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.info = InformationLayer()

    def process_turn(self, *, interaction_id: str, session_id: str, relationship_id: str,
                     actor: str, recipient: str, content_reference: str,
                     context_reference: str, statements: list, relevance: str = "HIGH",
                     tenant_id: str = "YO", owner_id: str = "yo") -> dict:
        ts = self.clock()
        # SIGNAL/EXPERIENCE: solo turnos relevantes generan experiencia
        if relevance not in ("HIGH", "MEDIUM"):
            return {"experience_created": False, "reason": f"relevance={relevance}"}
        obs, user_stated, sys_obs, hyps = [], [], [], []
        for s in statements:
            classified = self.info.classify(s["statement"], actor, s["provenance"])
            if classified["layer"].endswith("USER_STATED_INFORMATION"):
                user_stated.append(classified)
            elif s["provenance"] in ("INFERRED", "IMAGINED", "GENERATED"):
                hyps.append({**classified, "stage": "UNCERTAIN"})
            else:
                sys_obs.append(classified)
                obs.append({"stage": "PRESENT", "statement": s["statement"][:120],
                            "provenance": s["provenance"]})
        rec = InteractionRecord(interaction_id=interaction_id, session_id=session_id,
            relationship_id=relationship_id, actor=actor, recipient=recipient,
            timestamp=ts, content_reference=content_reference,
            context_reference=context_reference, observations=obs,
            user_stated_information=user_stated, system_observations=sys_obs,
            hypotheses=hyps, confidence=0.8 if relevance == "HIGH" else 0.5,
            provenance="OBSERVED", evidence_ids=(f"int:{interaction_id}",),
            tenant_id=tenant_id, owner_id=owner_id)
        if self.ledger:
            self.ledger.append({"type": "interaction", "id": interaction_id,
                                "hash": rec.content_hash})
        return {"experience_created": True, "record": rec,
                "pattern_candidates": self._pattern_candidates(rec),
                "hypotheses": hyps,
                "reflection": self.awareness.reflection_for(self._as_event(rec))}

    @staticmethod
    def _pattern_candidates(rec: InteractionRecord) -> list:
        return [{"candidate": o["statement"][:40], "stage": "UNCERTAIN",
                 "note": "candidato; requiere repeticion"} for o in rec.observations]

    @staticmethod
    def _as_event(rec: InteractionRecord) -> CognitiveEvent:
        return CognitiveEvent(
            event_id=f"ev:{rec.interaction_id}", actor=rec.actor, target=rec.recipient,
            session_id=rec.session_id, relationship_id=rec.relationship_id,
            timestamp=rec.timestamp, event_type="interaction",
            content_reference=rec.content_reference, context_reference=rec.context_reference,
            observation={"stage": "PRESENT" if rec.observations else "ABSENT",
                         "statement": rec.observations[0]["statement"] if rec.observations else ""},
            perception={"stage": "ABSENT", "statement": ""},
            interpretation={"stage": "UNKNOWN", "statement": ""},
            hypothesis={"stage": "PRESENT" if rec.hypotheses else "ABSENT",
                        "statement": rec.hypotheses[0]["statement"] if rec.hypotheses else ""},
            provenance=rec.provenance, confidence=rec.confidence,
            evidence_ids=rec.evidence_ids, temporal_validity=(rec.timestamp, rec.timestamp),
            tenant_id=rec.tenant_id, owner_id=rec.owner_id)


COGNITIVE_LENSES = (
    {"name": "Grinberg", "principle": "percepcion/realidad (especulativa)",
     "function": "lente especulativa", "component": "Perception",
     "evidence": "SPECULATIVE — NO presentar como ciencia establecida"},
    {"name": "Metzinger", "principle": "self-model != identity",
     "function": "distingue self-model de identidad", "component": "CognitiveTwinModel",
     "evidence": "PHILOSOPHICAL/COGNITIVE-SCIENCE"},
    {"name": "Friston", "principle": "prediction/action/outcome/error",
     "function": "error de prediccion en feedback loop", "component": "FeedbackLoop",
     "evidence": "THEORETICAL-NEURO"},
    {"name": "Dehaene", "principle": "global cognitive access",
     "function": "contexto disponible globalmente", "component": "ContextAssembler",
     "evidence": "COGNITIVE-SCIENCE"},
    {"name": "Tononi", "principle": "IIT (marco teorico)",
     "function": "referencia teorica; SIN afirmar conciencia artificial", "component": "lens",
     "evidence": "THEORETICAL — sin claim de conciencia"},
    {"name": "Barrett", "principle": "contexto/interpretacion/emocion",
     "function": "interpretacion contextual", "component": "Interpretation",
     "evidence": "COGNITIVE-SCIENCE"},
    {"name": "Festinger", "principle": "discrepancia cognitiva",
     "function": "CongruenceAnalyzer", "component": "CongruenceAnalyzer",
     "evidence": "SOCIAL-PSYCHOLOGY"},
    {"name": "Higgins", "principle": "actual/ideal/ought self",
     "function": "SelfContrastEngine", "component": "SelfContrastEngine",
     "evidence": "SOCIAL-PSYCHOLOGY"},
    {"name": "Metacognition", "principle": "evaluacion del propio proceso",
     "function": "Metacognition.questions_for", "component": "Metacognition",
     "evidence": "COGNITIVE-SCIENCE"},
)
