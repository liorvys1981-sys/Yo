"""G10 INSIGHTS — ciclo PATTERN/CONTRADICTION/STRENGTH/BLIND_SPOT -> INSIGHT
-> HYPOTHESIS -> CONFIRMED/REFUTED. Puro, deterministico, sin LLM ni red.

Decision de diseno (reportada): CONFIRMED exige confirmed_by='humano' + evidencia;
REFUTED puede ser determinista por el sistema con evidencia. Ambas conservan
provenance/evidence/confidence/ts/version. Ningun insight modifica DigitalSelf:
la unica ruta al self es Evolution + AuthorizationGate (este modulo no lo importa).
"""
from __future__ import annotations
import sys
from dataclasses import dataclass, field

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from cognitive_api import InsightsAPI, RequestContext

STATES = ("REGISTERED", "HYPOTHESIZED", "CONFIRMED", "REFUTED")
TRANSITIONS = {
    "REGISTERED": ["HYPOTHESIZED"],
    "HYPOTHESIZED": ["CONFIRMED", "REFUTED"],
    "CONFIRMED": [],
    "REFUTED": [],
}
FACT_TYPES = ("PATTERN", "CONTRADICTION", "STRENGTH", "BLIND_SPOT")


class InsightError(Exception):
    code = "INSIGHT_ERROR"


class InvalidInsightState(InsightError):
    code = "INVALID_STATE"


class InvalidInsightTransition(InsightError):
    code = "INVALID_TRANSITION"


class MissingEvidence(InsightError):
    code = "MISSING_EVIDENCE"


class HumanConfirmationRequired(InsightError):
    code = "HUMAN_CONFIRMATION_REQUIRED"


@dataclass
class TrackedInsight:
    id: str
    type: str                 # PATTERN | CONTRADICTION | STRENGTH | BLIND_SPOT | HYPOTHESIS
    statement: str
    provenance: str
    confidence: float
    evidence: tuple
    source: str               # id del Insight G6 origen
    state: str = "REGISTERED"
    version: int = 1
    history: list = field(default_factory=list)
    ts: float = 0.0


class InsightTracker(InsightsAPI):
    """Registra salidas de Reflection (G6) y gestiona su ciclo de vida."""

    def __init__(self, ledger=None, clock=None):
        self.ledger = ledger
        self.clock = clock or (lambda: __import__("time").time())
        self._items: dict[str, TrackedInsight] = {}

    @property
    def api_version(self) -> str:
        return "v0.1"

    # --- ingesta de salidas G6 ---
    def register_reflection_outputs(self, reflection_insights: list) -> list:
        """G6 Insight -> TrackedInsight. PATTERN/etc = REGISTERED; HYPOTHESIS = HYPOTHESIZED."""
        out = []
        for i in reflection_insights:
            if i.type == "HYPOTHESIS":
                state = "HYPOTHESIZED"   # nace como hipotesis, NUNCA confirmada
            elif i.type in FACT_TYPES:
                state = "REGISTERED"     # hecho observado/sistemico
            else:
                continue
            t = TrackedInsight(id=i.id, type=i.type, statement=i.statement,
                               provenance=i.provenance, confidence=i.confidence,
                               evidence=i.evidence, source=i.id, state=state,
                               ts=i.ts)
            self._items[t.id] = t
            self._audit("insight_registered", t)
            out.append(t)
        return out

    # --- contrato InsightsAPI ---
    def _list_impl(self, ctx: RequestContext, kind: str | None = None) -> list:
        items = list(self._items.values())
        if ctx.tenant_id:   # aislamiento: tracker es por-instancia; ctx validado por ABC
            pass
        return [i for i in items if kind is None or i.type == kind]

    def _state_change_impl(self, ctx: RequestContext, insight_id: str,
                           new_state: str, evidence: tuple,
                           confirmed_by: str = "system") -> dict:
        it = self._items.get(insight_id)
        if it is None:
            raise InvalidInsightState(f"{insight_id} no existe")
        if new_state not in STATES:
            raise InvalidInsightState(f"estado desconocido: {new_state}")
        if new_state not in TRANSITIONS[it.state]:
            raise InvalidInsightTransition(f"{it.state} -> {new_state}")
        if not evidence:
            raise MissingEvidence(f"{new_state} exige evidencia")
        if new_state == "CONFIRMED" and confirmed_by != "humano":
            raise HumanConfirmationRequired(
                "CONFIRMED exige confirmacion humana (una hipotesis no se confirma sola)")
        old = it.state
        it.state = new_state
        it.version += 1
        it.evidence = tuple(evidence)
        it.history.append({"from": old, "to": new_state, "by": confirmed_by,
                           "ts": self.clock(), "evidence": list(evidence)})
        self._audit("insight_state_change", it, extra={"from": old, "by": confirmed_by})
        return {"id": it.id, "from": old, "to": new_state, "version": it.version,
                "provenance": it.provenance, "confidence": it.confidence}

    def _audit(self, type_: str, it: TrackedInsight, extra: dict | None = None):
        if self.ledger:
            ev = {"type": type_, "insight": it.id, "insight_type": it.type,
                  "state": it.state, "version": it.version,
                  "provenance": it.provenance, "confidence": it.confidence}
            if extra:
                ev.update(extra)
            self.ledger.append(ev)
