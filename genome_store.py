"""GENOME STORE — persistencia versionada del DigitalSelf + wiring de evidencia.

Fase 3. Requisitos:
1. Persistencia versionada (JSON atomico: tmp + rename)
2. Historial preservado + reconstruccion temporal tras reload
3. EvidenceAPI -> evidence_ledger (EL_YO 01_GOBIERNO): cada cambio = evento verificable
5. Tamper-evidence: content_hash verificado en load (integridad entre reinicios)
"""
from __future__ import annotations
import json, os, sys, tempfile
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from digital_self import (DigitalSelf, SelfEntity, EntityVersion,
                          VersionIntegrityError, ENTITY_KINDS, FUNDAMENTAL_KINDS)
from el_yo.constitution import Action, Denied

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from el_yo.evidence import EvidenceLedger   # append-only, hash-chained, flock (ya probado)
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from cognitive_api import EvidenceAPI, RequestContext


class GenomeStore(EvidenceAPI):
    """Almacen persistente del DigitalSelf. CIERRA el contrato EvidenceAPI (Fase 4)."""

    @property
    def api_version(self) -> str:
        return "v0.1"

    def _append_impl(self, ctx: RequestContext, event: dict) -> str:
        if self.ledger is None:
            raise RuntimeError("GenomeStore sin ledger: evidencia externa no disponible")
        return self.ledger.append(event)["hash"]

    def _verify_impl(self, ctx: RequestContext) -> bool:
        return self.ledger.verify() if self.ledger else False

    def __init__(self, root: str, ledger_path: str | None = None,
                 authority_did: str | None = None, today: str | None = None):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self.authority_did = authority_did   # R1: clave PUBLICA de la autoridad
        self.today = today                   # R1: frescura de autorizaciones
        self.ledger = EvidenceLedger(ledger_path) if ledger_path else None

    def _path(self, tenant: str, subject: str) -> str:
        d = os.path.join(self.root, tenant)
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"{subject}.genome.json")

    # --- serializacion ---
    @staticmethod
    def _entity_to_dict(e: SelfEntity) -> dict:
        return {"kind": e.kind, "entity_id": e.entity_id, "created_at": e.created_at,
                "active_version": e.active_version,
                "versions": [{"version": v.version, "content": v.content,
                              "provenance": v.provenance, "confidence": v.confidence,
                              "evidence": list(v.evidence), "source_ref": v.source_ref,
                              "ts": v.ts, "change_reason": v.change_reason,
                              "approved_by": v.approved_by, "content_hash": v.content_hash}
                             for v in e.versions]}

    @staticmethod
    def _entity_from_dict(d: dict) -> SelfEntity:
        e = SelfEntity(kind=d["kind"], entity_id=d["entity_id"], created_at=d["created_at"])
        e.versions = [EntityVersion(
            version=v["version"], content=v["content"], provenance=v["provenance"],
            confidence=v["confidence"], evidence=tuple(v["evidence"]),
            source_ref=v["source_ref"], ts=v["ts"], change_reason=v["change_reason"],
            approved_by=v["approved_by"], content_hash=v["content_hash"])
            for v in d["versions"]]
        e.active_version = d["active_version"]
        return e

    # --- persistencia atomica ---
    def save(self, ds: DigitalSelf) -> str:
        path = self._path(ds.tenant_id, ds.subject_id)
        data = {"contract": "2.0.0", "tenant_id": ds.tenant_id, "subject_id": ds.subject_id,
                "entities": {k: self._entity_to_dict(e) for k, e in ds.entities.items()}}
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, sort_keys=True)
        os.replace(tmp, path)          # atomico
        return path

    def load(self, tenant: str, subject: str) -> DigitalSelf:
        path = self._path(tenant, subject)
        with open(path) as f:
            data = json.load(f)
        ds = DigitalSelf(data["subject_id"], data["tenant_id"])
        for kind, ed in data["entities"].items():
            e = self._entity_from_dict(ed)
            for v in e.versions:                  # tamper-evidence entre reinicios
                v.verify_integrity()
            ds.entities[kind] = e
        return ds

    # --- cambio con evidencia (wiring EvidenceAPI -> ledger) ---
    def change(self, ds: DigitalSelf, kind: str, content: dict, provenance: str,
               confidence: float, evidence: tuple, source_ref: str,
               change_reason: str, approved_by: str = "system",
               ts: float | None = None,
               authorization: object | None = None) -> dict:
        if kind in FUNDAMENTAL_KINDS:
            # R1: autoridad verificable criptograficamente; nunca boolean/string libre
            from authority import verify_authorization, InvalidAuthorization
            if self.authority_did is None or self.today is None:
                raise Denied(f"{kind}: store sin autoridad configurada (authority_did/today)")
            try:
                approved_by = verify_authorization(authorization, self.authority_did,
                                                   kind, self.today)
            except InvalidAuthorization as e:
                raise Denied(f"{kind}: autorizacion rechazada: {e}")
        entity = ds.get(kind)
        version = entity.set(content, provenance, confidence, evidence,
                             source_ref, change_reason, approved_by, ts=ts)
        path = self.save(ds)
        event = {"type": "genome_change", "tenant": ds.tenant_id,
                 "subject": ds.subject_id, "kind": kind, "version": version,
                 "content_hash": entity.active.content_hash,
                 "change_reason": change_reason, "approved_by": approved_by,
                 "genome_file": path}
        if self.ledger:
            entry = self.ledger.append(event)      # cada cambio = evidencia verificable
            event["ledger_hash"] = entry["hash"]
        return event
