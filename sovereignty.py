"""G11 SOVEREIGNTY — export soberano y verificacion independiente del Cognitive Twin.

EXPORT -> VERIFY SIGNATURE -> VERIFY HASHES -> VERIFY GENOME INTEGRITY
-> VERIFY HISTORY -> VERIFY AUDIT TRAIL

Reglas: snapshot consistente de solo-lectura; cero secretos privados (la DID es
publica; la seed nunca se exporta); firma con identity_engine REAL de EL_YO;
deteccion de cualquier manipulacion posterior; determinista con clock inyectable.
"""
from __future__ import annotations
import hashlib, json, os, shutil, sys, uuid

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from genome_store import GenomeStore
from el_yo.evidence import EvidenceLedger


class SovereigntyError(Exception):
    code = "SOVEREIGNTY_ERROR"


class SignatureInvalid(SovereigntyError):
    code = "SIGNATURE_INVALID"


class HashMismatch(SovereigntyError):
    code = "HASH_MISMATCH"


class GenomeIntegrityFail(SovereigntyError):
    code = "GENOME_INTEGRITY_FAIL"


class HistoryBroken(SovereigntyError):
    code = "HISTORY_BROKEN"


class AuditTrailBroken(SovereigntyError):
    code = "AUDIT_TRAIL_BROKEN"


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _pubkey_from_did(did: str):
    import base64
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    raw = base64.urlsafe_b64decode(did.split("z6Mk")[1] + "==")
    return Ed25519PublicKey.from_public_bytes(raw)


class TwinExporter:
    """Exporta una instantanea completa, firmada y verificable offline."""

    def __init__(self, store: GenomeStore, identity, clock=None):
        self.store = store
        self.identity = identity            # identity_engine.Identity REAL (EL_YO)
        self.clock = clock or (lambda: __import__("time").time())

    def export(self, ds, out_root: str, export_id: str | None = None) -> dict:
        eid = export_id or f"exp:{uuid.uuid4().hex[:12]}"
        pkg = os.path.join(out_root, eid)
        os.makedirs(pkg, exist_ok=True)

        # 1-7: snapshot completo (solo lectura: GenomeStore serializa sin mutar)
        self_doc = {"contract": "2.0.0", "tenant_id": ds.tenant_id,
                    "subject_id": ds.subject_id, "exported_at": self.clock(),
                    "entities": {k: GenomeStore._entity_to_dict(e)
                                 for k, e in ds.entities.items()}}
        self_bytes = _canon(self_doc)
        self_path = os.path.join(pkg, "self.json")
        with open(self_path, "wb") as f:
            f.write(self_bytes)

        # 5/11: audit trail (copia del ledger; la cadena se verifica aparte)
        audit_path = os.path.join(pkg, "audit.jsonl")
        audit_src = self.store.ledger.path if self.store.ledger else None
        audit_bytes = b""
        if audit_src and os.path.exists(audit_src):
            with open(audit_src, "rb") as f:
                audit_bytes = f.read()
        with open(audit_path, "wb") as f:
            f.write(audit_bytes)

        # 10-11: manifest con hashes + DID publica (nunca secretos)
        manifest = {
            "export_id": eid, "format": "app-yo-twin-export/v1",
            "did": self.identity.did,
            "exported_at": self_doc["exported_at"],
            "files": {
                "self.json": {"sha256": _sha(self_bytes)},
                "audit.jsonl": {"sha256": _sha(audit_bytes)},
            },
        }
        # 9: firma del manifest canónico sin el campo signature
        manifest["signature"] = self.identity.sign(_canon(manifest))
        with open(os.path.join(pkg, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        if self.store.ledger:
            self.store.ledger.append({"type": "twin_export", "export_id": eid,
                                      "did": self.identity.did,
                                      "files": list(manifest["files"])})
        return {"export_id": eid, "path": pkg, "did": self.identity.did,
                "manifest": manifest}


class TwinVerifier:
    """Verificacion independiente: sin estado de proceso, solo el paquete + DID."""

    @staticmethod
    def _load(pkg: str):
        with open(os.path.join(pkg, "manifest.json")) as f:
            manifest = json.load(f)
        return manifest

    @staticmethod
    def verify_signature(pkg: str) -> bool:
        import base64
        m = TwinVerifier._load(pkg)
        sig = m.pop("signature")
        try:
            _pubkey_from_did(m["did"]).verify(base64.urlsafe_b64decode(sig + "=="),
                                              _canon(m))
        except Exception as e:
            raise SignatureInvalid(f"firma invalida: {e}")
        return True

    @staticmethod
    def verify_hashes(pkg: str) -> bool:
        m = TwinVerifier._load(pkg)
        for name, meta in m["files"].items():
            with open(os.path.join(pkg, name), "rb") as f:
                if _sha(f.read()) != meta["sha256"]:
                    raise HashMismatch(f"{name}: hash alterado")
        return True

    @staticmethod
    def verify_genome_integrity(pkg: str) -> bool:
        with open(os.path.join(pkg, "self.json")) as f:
            doc = json.load(f)
        for kind, e in doc["entities"].items():
            for v in e["versions"]:
                if _sha(_canon(v["content"])) != v["content_hash"]:
                    raise GenomeIntegrityFail(f"{kind} v{v['version']}: content_hash roto")
        return True

    @staticmethod
    def verify_history(pkg: str) -> bool:
        with open(os.path.join(pkg, "self.json")) as f:
            doc = json.load(f)
        for kind, e in doc["entities"].items():
            vs = e["versions"]
            if [v["version"] for v in vs] != list(range(1, len(vs) + 1)):
                raise HistoryBroken(f"{kind}: versiones no monotonas")
            if vs and e["active_version"] not in range(1, len(vs) + 1):
                raise HistoryBroken(f"{kind}: active_version invalida")
        return True

    @staticmethod
    def verify_audit_trail(pkg: str) -> bool:
        prev, n = "GENESIS", 0
        with open(os.path.join(pkg, "audit.jsonl"), "rb") as f:
            for line in f:
                entry = json.loads(line)
                h = entry.pop("hash")
                if _sha(prev.encode() + _canon(entry)) != h:
                    raise AuditTrailBroken(f"linea {n + 1}: cadena rota")
                prev = h
                n += 1
        return True

    @staticmethod
    def full_verify(pkg: str) -> dict:
        TwinVerifier.verify_signature(pkg)
        TwinVerifier.verify_hashes(pkg)
        TwinVerifier.verify_genome_integrity(pkg)
        TwinVerifier.verify_history(pkg)
        TwinVerifier.verify_audit_trail(pkg)
        return {"package": os.path.basename(pkg), "status": "VERIFIED"}
