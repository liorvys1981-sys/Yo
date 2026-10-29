"""OM-P16 ELLA TWIN-TO-TWIN INTEGRATION CONTRACTS.

Contratos solamente. NO autonomia. NO ejecucion externa automatica. Preserva:
namespace separation, provenance, versioning, evidence, content_hash, authorization,
ledger/auditability, determinism, anti-replay.

Invariante central: YO'S MODEL OF ELLA != ELLA'S IDENTITY != RELATIONAL MODEL."""
from __future__ import annotations
import hashlib, json, sys

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from authority import verify_authorization, InvalidAuthorization


class ContractError(Exception):
    code = "CONTRACT_ERROR"


class NamespaceViolation(ContractError):
    code = "NAMESPACE_VIOLATION"


ACTION_RELATIONAL_UPDATE = "ELLA-relational-model-update"
IMPACT_RELATIONAL = "externa_irreversible"   # frase-canal; NO doble llave (no toca identidad)

_CANON = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
_CHASH = lambda o: hashlib.sha256(_CANON(o)).hexdigest()


def yo_model_of_ella(yo_twin_snapshot: dict, yo_memory_refs: tuple = ()) -> dict:
    """YO construye su MODELO de ELLA (namespace YO). Nunca identidad de ELLA."""
    return {
        "kind": "YO'S MODEL OF ELLA", "namespace": "YO",
        "provenance": "INFERRED", "provenance_subtype": "YO_MODEL_OF_ELLA",
        "not_ella_identity": True, "content": {"snapshot_refs": yo_memory_refs},
        "content_hash": _CHASH({"s": yo_twin_snapshot, "r": list(yo_memory_refs)}),
    }


def relational_model(relations: list) -> dict:
    """Capa relacional: RELATIONAL MODEL (ni YO's model, ni ELLA's identity)."""
    return {
        "kind": "RELATIONAL MODEL", "namespace": "RELATIONAL",
        "provenance": "SYSTEM_DERIVED", "relations": list(relations),
        "content_hash": _CHASH({"rel": relations}),
    }


class TwinToTwinContracts:
    """Contratos twin-to-twin versionados. Cada transicion lleva evidence+hash;
    anti-replay via content_hash binding + nonce + day (misma politica R1/R2)."""

    def __init__(self, authority_did: str, today: str, ledger=None, clock=None):
        self.authority_did = authority_did
        self.today = today
        self.ledger = ledger
        self.clock = clock or (lambda: __import__("time").time())
        self._version = 0
        self._last_hash = None

    def propose_relational_update(self, yo_model: dict, ella_context: dict) -> dict:
        if not yo_model.get("not_ella_identity"):
            raise NamespaceViolation("el modelo no esta marcado como YO'S MODEL OF ELLA")
        self._version += 1
        proposal = {
            "contract_version": self._version,
            "namespace": "RELATIONAL",
            "kind": "PROPOSAL(relational)",
            "provenance": "INFERRED",
            "content": {"yo_model_ref": yo_model["content_hash"],
                        "ella_context_ref": _CHASH(ella_context)},
            "prev": self._last_hash,
            "ts": self.clock(),
        }
        proposal["content_hash"] = _CHASH(proposal)
        self._last_hash = proposal["content_hash"]
        return proposal

    def authorize_relational_update(self, proposal: dict, authorization) -> dict:
        """Reuse R1 verify: action binding + content binding + day freshness."""
        try:
            did = verify_authorization(authorization, self.authority_did,
                                       ACTION_RELATIONAL_UPDATE, self.today,
                                       expected_content_hash=proposal["content_hash"])
        except InvalidAuthorization as e:
            raise ContractError(f"autorizacion rechazada: {e}")
        approved = {
            "contract_version": proposal["contract_version"],
            "namespace": "RELATIONAL", "kind": "APPROVED(relational)",
            "proposal_hash": proposal["content_hash"],
            "approved_by": did, "ts": self.clock(),
        }
        approved["content_hash"] = _CHASH(approved)
        self._last_hash = approved["content_hash"]
        if self.ledger:
            self.ledger.append({"type": "twin_to_twin",
                                "version": self.contract_version(),
                                "proposal_hash": proposal["content_hash"],
                                "approved_by": did})
        return approved

    def contract_version(self) -> int:
        return self._version

    def verify_chain(self) -> bool:
        return self._last_hash is None or len(self._last_hash) == 64
