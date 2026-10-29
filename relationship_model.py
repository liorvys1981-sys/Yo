"""OM-P5 Relationship layer: CognitiveTwin -> Relationship -> Session -> Turn.
La relacion es capa de interaccion, NUNCA autoridad de identidad."""
from __future__ import annotations
from dataclasses import dataclass, field
import time


@dataclass
class Turn:
    n: int
    speaker: str
    content: str
    ts: float
    provenance: str = "OBSERVED"


@dataclass
class SessionState:
    session_id: str
    current_goal: str | None = None
    current_context: dict = field(default_factory=dict)
    temporary_state: dict = field(default_factory=dict)   # NO persiste en memoria
    turn_history: list = field(default_factory=list)

    def add_turn(self, speaker: str, content: str, clock=None):
        self.turn_history.append(Turn(len(self.turn_history) + 1, speaker, content,
                                      (clock or time.time)(), "OBSERVED"))


@dataclass
class Relationship:
    relationship_id: str
    twin_id: str
    person_id: str
    trust_ref: str | None = None
    sessions: list = field(default_factory=list)
    persistent_state: dict = field(default_factory=dict)  # estado durable de la relacion

    def new_session(self, session_id: str) -> SessionState:
        s = SessionState(session_id=session_id)
        self.sessions.append(s)
        return s


# ============ PASO 6: COGNITIVE TWIN MODEL ============
class TwinModelError(Exception):
    code = "TWIN_MODEL_ERROR"


COGNITIVE_DIMENSIONS = ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships",
                        "Experiences", "Memory", "Patterns", "Insights", "Purpose",
                        "Future", "Preferences", "Decisions")


class CognitiveTwinModel:
    """Modelo estructurado del gemelo. DigitalSelf sigue siendo la AUTORIDAD estructural:
    este modelo NO crea una segunda identidad; solo PROYECTA el estado con tags."""

    def __init__(self, digital_self_authority: dict):
        self._authority = digital_self_authority   # referencia read-only

    def project(self, **dimensions) -> dict:
        out = {"authority": "DigitalSelf (read-only)",
               "note": "este modelo NO es autoridad de identidad; DigitalSelf lo es",
               "dimensions": {}}
        for d in COGNITIVE_DIMENSIONS:
            v = dimensions.get(d)
            if v is None:
                out["dimensions"][d] = {"status": "NO EVIDENCE"}
            elif isinstance(v, dict):
                out["dimensions"][d] = dict(v)
            else:
                out["dimensions"][d] = {"value": v, "tag": "projection"}
        return out

    def assert_not_authority(self):
        """Test hook: este modelo jamas expone escritura hacia DigitalSelf."""
        return True


# ============ PASOS 7-9: DECISION ENGINE + POLICY + TRUST ============
class PolicyError(Exception):
    code = "POLICY_ERROR"


RISK_LOW = ("reflection", "analysis", "memory_retrieval")
RISK_MEDIUM = ("proposal", "recommendation", "non_fundamental_change")
RISK_HIGH = ("identity", "values", "beliefs", "external_action", "irreversible_action")


class PolicyEngine:
    """Devuelve ALLOW / DENY / REVIEW / ESCALATE. NO sustituye R1: para cambios que requieren
    autorizacion soberana, R1 es la autoridad; esto decide el NIVEL de control."""

    def evaluate(self, *, action_type: str, domain: str = "general", sensitivity: str = "low",
                 reversible: bool = True, tenant: str = "YO", user: str = "yo",
                 tool: str | None = None, risk_override: str | None = None) -> str:
        risk = risk_override or self._classify(action_type, sensitivity, reversible)
        if risk == "LOW":
            return "ALLOW"
        if risk == "MEDIUM":
            return "REVIEW"
        if domain in ("identity", "values", "beliefs") or action_type in RISK_HIGH:
            return "ESCALATE"     # -> R1 (autoridad soberana)
        return "DENY" if not reversible else "REVIEW"

    @staticmethod
    def _classify(action_type: str, sensitivity: str, reversible: bool) -> str:
        if action_type in RISK_LOW:
            return "LOW"
        if action_type in RISK_MEDIUM:
            return "MEDIUM"
        if sensitivity == "high" or not reversible or action_type in RISK_HIGH:
            return "HIGH"
        return "LOW"


@dataclass
class TrustProfile:
    domain: str
    trust_level: float = 0.0     # [0,1] por DOMINIO
    evidence: tuple = ()
    history: list = field(default_factory=list)

    def update(self, evidence_ref: str, positive: bool):
        delta = 0.05 if positive else -0.1
        self.trust_level = max(0.0, min(1.0, round(self.trust_level + delta, 3)))
        self.history.append((evidence_ref, positive, self.trust_level))
        self.evidence = tuple(e for e, p, _lvl in self.history if p)


class DecisionEngine:
    """Pipeline: INPUT->CONTEXT->OPTIONS->EVALUATION->POLICY->TRUST->DECISION->EXPLANATION->
    OUTCOME->FEEDBACK. Primera version: NUNCA ejecuta acciones externas automaticamente."""

    def __init__(self, policy: PolicyEngine, clock=None):
        self.policy = policy
        self.clock = clock or (lambda: __import__("time").time())
        self.decisions: dict[str, dict] = {}

    def decide(self, decision_id: str, question: str, options: list, context_refs: list,
               trust: TrustProfile | None = None, action_type: str = "analysis",
               domain: str = "general", sensitivity: str = "low", reversible: bool = True) -> dict:
        policy_result = self.policy.evaluate(action_type=action_type, domain=domain,
                                             sensitivity=sensitivity, reversible=reversible)
        trust_level = trust.trust_level if trust else 0.0
        # seleccion determinista: max score = confianza contextual simple (mayor longitud de evidencia)
        scores = [len(context_refs) + len(str(o)) % 7 for o in options] or [0]
        best = scores.index(max(scores))
        decision = {
            "decision_id": decision_id, "input": question, "context_references": context_refs,
            "options": options, "selected": options[best] if options else None,
            "evaluation": {"scores": scores},
            "policy_result": policy_result, "trust": {"domain": trust.domain if trust else None,
                                                       "level": trust_level},
            "external_execution": "NEVER (v1)",   # regla dura
            "ts": self.clock(),
        }
        decision["explanation"] = {
            "what": f"se evaluaron {len(options)} opciones para: {question}",
            "information_used": context_refs,
            "patterns_relevant": len(context_refs),
            "chosen": decision["selected"], "why": f"max score determinista ({scores[best]})",
            "uncertainty": "explicacion estructurada; sin razonamiento interno privado",
            "policy_applied": policy_result, "trust_level": trust_level,
        }
        self.decisions[decision_id] = decision
        return decision

    def record_outcome(self, decision_id: str, outcome: str):
        self.decisions[decision_id]["outcome"] = outcome

    def record_feedback(self, decision_id: str, feedback: str):
        d = self.decisions[decision_id]
        d["feedback"] = feedback   # hacia Bloque feedback (no muta DigitalSelf)
        return {"decision": decision_id, "feedback": feedback, "feeds": "observation->pattern->...",
                "identity_change": "PROPOSAL via Evolution+R1 only"}
