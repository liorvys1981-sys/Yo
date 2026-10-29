"""G8 EVOLUTION PIPELINE — maquina de estados completa, determinista, sin LLM.

EXPERIENCES -> PATTERN -> HYPOTHESIS -> REFLECTION -> PROPOSED -> REVIEW
            -> APPROVAL -> VERSIONED UPDATE        (o REJECTED)

Reglas: EVOLUTION_LOCKED real; gate inalienable (AuthorizationGate en approve,
para TODOS los kinds); rechazo no toca el genome; versionado preserva historial;
cada transicion evidencia en ledger; reloj inyectable (determinismo).
"""
from __future__ import annotations
import sys
from dataclasses import dataclass, field

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from reflection import reflect
from digital_self import FUNDAMENTAL_KINDS
from el_yo.constitution import Action, Denied

STATES = ("INIT", "PATTERNED", "HYPOTHESIZED", "REFLECTED", "PROPOSED",
          "REVIEW", "APPROVED", "APPLIED", "REJECTED")
TRANSITIONS = {
    "INIT": ["PATTERNED"],
    "PATTERNED": ["HYPOTHESIZED"],
    "HYPOTHESIZED": ["REFLECTED"],
    "REFLECTED": ["PROPOSED"],
    "PROPOSED": ["REVIEW", "REJECTED"],
    "REVIEW": ["APPROVED", "REJECTED"],
    "APPROVED": ["APPLIED"],
    "APPLIED": [],
    "REJECTED": [],
}


class EvolutionPipelineError(Exception):
    code = "PIPELINE_ERROR"


class InvalidTransition(EvolutionPipelineError):
    code = "INVALID_TRANSITION"


class EvolutionLocked(EvolutionPipelineError):
    code = "EVOLUTION_LOCKED"


@dataclass
class ChangeRequest:
    request_id: str
    tenant: str
    subject: str
    kind: str                 # entidad DigitalSelf objetivo
    new_content: dict
    provenance: str
    confidence: float
    evidence: tuple
    source_ref: str
    change_reason: str
    state: str = "INIT"
    history: list = field(default_factory=list)   # [{from,to,ts,note}]
    artifacts: dict = field(default_factory=dict) # insights por etapa


class EvolutionPipeline:
    def __init__(self, store, gate, clock=None, authority=None):
        self.store = store
        self.gate = gate
        self.authority = authority   # R1: emisor firmante (tras gate real)
        self.clock = clock or (lambda: __import__("time").time())
        self._requests: dict[str, ChangeRequest] = {}
        self._locked = False

    # --- EVOLUTION_LOCKED: mecanismo real ---
    def lock(self, reason: str):
        self._locked = True
        self._ev(None, {"type": "evolution_locked", "reason": reason})

    def unlock(self, channel_phrase: str):
        r = self.gate.authorize(Action("unlock", "externa_irreversible"),
                                actor="humano", phrase=channel_phrase)
        if r["decision"] != "ALLOW":
            raise Denied("unlock denegado por gate")
        self._locked = False
        self._ev(None, {"type": "evolution_unlocked"})

    def _check_unlocked(self):
        if self._locked:
            raise EvolutionLocked("EVOLUTION_LOCKED activo: ninguna transicion permitida")

    def _transition(self, req: ChangeRequest, to: str, note: str = ""):
        self._check_unlocked()
        if to not in TRANSITIONS[req.state]:
            raise InvalidTransition(f"{req.state} -> {to}")
        event = {"type": "pipeline_transition", "request": req.request_id,
                 "from": req.state, "to": to, "ts": self.clock(), "note": note,
                 "kind": req.kind, "tenant": req.tenant, "subject": req.subject}
        req.state = to
        req.history.append({"from": event["from"], "to": to, "ts": event["ts"], "note": note})
        self._ev(req, event)

    def _ev(self, req, event: dict):
        if self.store.ledger:
            h = self.store.ledger.append(event)
            event["ledger_hash"] = h["hash"]
        if req is not None:
            req.artifacts.setdefault("ledger", []).append(event)

    # --- pipeline ---
    def submit(self, request_id: str, ds, experiences: list, kind: str,
               new_content: dict, provenance: str, confidence: float,
               evidence: tuple, source_ref: str, change_reason: str) -> ChangeRequest:
        self._check_unlocked()
        req = ChangeRequest(request_id=request_id, tenant=ds.tenant_id,
                            subject=ds.subject_id, kind=kind, new_content=new_content,
                            provenance=provenance, confidence=confidence,
                            evidence=tuple(evidence), source_ref=source_ref,
                            change_reason=change_reason)
        self._requests[request_id] = req
        insights = reflect(experiences)                       # EXPERIENCES -> PATTERN...
        req.artifacts["insights"] = insights
        self._transition(req, "PATTERNED", f"{len([i for i in insights if i.type=='PATTERN'])} patterns")
        self._transition(req, "HYPOTHESIZED",
                         f"{len([i for i in insights if i.type=='HYPOTHESIS'])} hypothesis")
        self._transition(req, "REFLECTED", "reflection digest generado")
        self._transition(req, "PROPOSED", change_reason)
        return req

    def review(self, request_id: str, notes: str) -> str:
        req = self._requests[request_id]
        self._transition(req, "REVIEW", notes)
        return req.state

    def reject(self, request_id: str, reason: str) -> dict:
        req = self._requests[request_id]
        self._transition(req, "REJECTED", reason)
        return {"request": request_id, "state": "REJECTED", "genome_untouched": True}

    def approve(self, request_id: str, ds, channel_phrase: str) -> dict:
        req = self._requests[request_id]
        self._transition(req, "APPROVED", "gate pending")     # transicion REVIEW->APPROVED
        # GATE INALIENABLE: todos los kinds pasan por AuthorizationGate
        impact = "destructiva" if req.kind in FUNDAMENTAL_KINDS else "reversible_menor"
        try:
            r = self.gate.authorize(Action(req.kind, impact), actor="humano",
                                    phrase=channel_phrase)
        except Denied:
            req.state = "REVIEW"          # rollback de transicion al denegar
            raise
        if r["decision"] != "ALLOW":
            req.state = "REVIEW"
            raise Denied(f"gate denego: {req.kind}")
        if self.authority is None:
            raise Denied("pipeline sin Authority configurada (R1)")
        authz = self.authority.authorize_change(req.kind, channel_phrase)
        ev = self.store.change(ds, req.kind, req.new_content, req.provenance,
                               req.confidence, req.evidence, req.source_ref,
                               req.change_reason, ts=self.clock(),
                               authorization=authz)
        self._transition(req, "APPLIED", f"version {ev['version']}")
        req.artifacts["applied"] = ev
        return {"request": request_id, "state": "APPLIED", "version": ev["version"],
                "content_hash": ev["content_hash"], "ledger_hash": ev.get("ledger_hash")}
