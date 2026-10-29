"""EVOLUTION ENGINE — propose -> authorize -> approve/reject -> versioned -> evidence.

Cambios fundamentales (Identity/Values/Beliefs):
  propose() -> AuthorizationGate (frase-canal + codigo del dia + DOBLE LLAVE, Art. 4.2)
  approve() -> GenomeStore.change(authorized=True) -> evidencia
  reject()  -> genome intacto + evento de rechazo auditado en ledger
"""
from __future__ import annotations
import sys, uuid
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from el_yo.constitution import Action, Denied
from digital_self import FUNDAMENTAL_KINDS
from genome_store import GenomeStore


@dataclass
class Proposal:
    proposal_id: str
    tenant: str
    subject: str
    kind: str
    content: dict
    provenance: str
    confidence: float
    evidence: tuple
    source_ref: str
    change_reason: str
    state: str = "proposed"   # proposed | approved | rejected


class EvolutionEngine:
    def __init__(self, store: GenomeStore, gate, authority=None):
        self.store = store
        self.gate = gate
        self.authority = authority   # R1
        self._proposals: dict[str, Proposal] = {}

    def propose(self, ds, kind: str, content: dict, provenance: str,
                confidence: float, evidence: tuple, source_ref: str,
                change_reason: str) -> str:
        p = Proposal(proposal_id=f"prop:{uuid.uuid4().hex[:12]}",
                     tenant=ds.tenant_id, subject=ds.subject_id, kind=kind,
                     content=content, provenance=provenance, confidence=confidence,
                     evidence=tuple(evidence), source_ref=source_ref,
                     change_reason=change_reason)
        self._proposals[p.proposal_id] = p
        if self.store.ledger:
            self.store.ledger.append({"type": "evolution_proposal",
                                      "proposal": p.proposal_id, "kind": kind,
                                      "tenant": p.tenant, "subject": p.subject,
                                      "reason": change_reason})
        return p.proposal_id

    def approve(self, ds, proposal_id: str, channel_phrase: str) -> dict:
        p = self._proposals[proposal_id]
        # AUTORIZACION REAL: fundamental = impacto destructivo => doble llave (Art. 4.2)
        impact = "destructiva" if p.kind in FUNDAMENTAL_KINDS else "reversible_menor"
        r = self.gate.authorize(Action(p.kind, impact), actor="humano",
                                phrase=channel_phrase)
        if r["decision"] != "ALLOW":
            raise Denied("gate denego la autorizacion")
        p.state = "approved"
        if self.authority is None:
            raise Denied("engine sin Authority configurada (R1)")
        authz = self.authority.authorize_change(p.kind, channel_phrase)
        event = self.store.change(ds, p.kind, p.content, p.provenance, p.confidence,
                                  p.evidence, p.source_ref, p.change_reason,
                                  authorization=authz)
        if self.store.ledger:
            self.store.ledger.append({"type": "evolution_approved",
                                      "proposal": proposal_id, "kind": p.kind,
                                      "version": event["version"],
                                      "content_hash": event["content_hash"],
                                      "tenant": p.tenant, "subject": p.subject})
        return event

    def reject(self, proposal_id: str, reason: str) -> dict:
        p = self._proposals[proposal_id]
        p.state = "rejected"
        ev = None
        if self.store.ledger:
            ev = self.store.ledger.append({"type": "evolution_rejected",
                                           "proposal": proposal_id, "kind": p.kind,
                                           "reason": reason,
                                           "tenant": p.tenant, "subject": p.subject})
        return {"proposal": proposal_id, "state": "rejected",
                "genome_untouched": True,
                "ledger_hash": ev["hash"] if ev else None}
