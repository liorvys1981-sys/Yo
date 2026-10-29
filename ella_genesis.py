"""ELLA GENESIS v2 (R2) — creacion de ELLA bajo autoridad soberana verificable.

Cadena: CREATE ELLA REQUEST -> AuthorizationGate -> Authority -> autorizacion
criptografica -> verify_authorization -> ELLA_ORIGIN -> Genesis Proposal -> ledger.

V1: genesis/propose exigen ChangeAuthorization real (reuse R1, cero duplicacion).
V2/V3: record_yo_model_of_ella rechaza destino != namespace YO; enforce_separation
       es invocada en el runtime de genesis/propose.
V4: load_proposal() verifica content_hash.
V5: frescura = politica R1 (day del gate); origin registra valid_day.
Autonomia de ELLA: DISABLED (sin cambio).
"""
from __future__ import annotations
import hashlib, json, os, sys, time

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from authority import ChangeAuthorization, verify_authorization, InvalidAuthorization

NAMESPACE_YO = "YO"
NAMESPACE_ELLA = "ELLA"
ACTION_GENESIS = "ELLA-genesis"
ACTION_PROPOSAL = "ELLA-identity-proposal"
IMPACT_GENESIS = "destructiva"            # doble llave: acto soberano de creacion
IMPACT_PROPOSAL = "externa_irreversible"  # frase-canal: propuesta de identidad
FRESHNESS_DAYS = 1                        # politica R1: validez del dia de emision


class EllaGenesisError(Exception):
    code = "ELLA_GENESIS_ERROR"


class CrossNamespaceViolation(EllaGenesisError):
    code = "CROSS_NAMESPACE_VIOLATION"


class GenesisContractViolation(EllaGenesisError):
    code = "GENESIS_CONTRACT_VIOLATION"


class UnauthorizedGenesis(EllaGenesisError):
    code = "UNAUTHORIZED_GENESIS"


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _chash(obj) -> str:
    return hashlib.sha256(_canon(obj)).hexdigest()


class EllaGenesis:
    def __init__(self, root: str, authority_did: str, today: str,
                 ledger=None, clock=None):
        self.root = os.path.join(root, NAMESPACE_ELLA)
        os.makedirs(self.root, exist_ok=True)
        self._canonical_root = self.root     # R2-V3: raiz canonica para detectar drift
        self.authority_did = authority_did   # R2-V1: clave PUBLICA de la autoridad
        self.today = today                   # R2-V5: frescura (politica R1)
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())

    def _path(self, name):
        return os.path.join(self.root, name)

    def _audit(self, event):
        if self.ledger:
            self.ledger.append({"type": "ella_genesis", "namespace": NAMESPACE_ELLA,
                                **event, "ts": self.clock()})

    def _verify(self, authorization, action, content):
        try:
            did = verify_authorization(authorization, self.authority_did,
                                       action, self.today,
                                       expected_content_hash=_chash(content))
        except InvalidAuthorization as e:
            raise UnauthorizedGenesis(f"{action}: {e}")
        return did

    def _runtime_separation_check(self):
        # R2-V3: enforce_separation conectada al runtime (comparacion vs canonica)
        if os.path.abspath(self.root) != os.path.abspath(self._canonical_root):
            raise CrossNamespaceViolation(
                f"drift de ruta del namespace ELLA: {self.root} != {self._canonical_root}")
        self.enforce_separation(NAMESPACE_ELLA, self._canonical_root)

    def genesis(self, declaration: str, authorization: ChangeAuthorization) -> dict:
        """R2-V1: creacion solo con autorizacion firmada + vinculo de contenido."""
        self._runtime_separation_check()
        approved_did = self._verify(authorization, ACTION_GENESIS, declaration)
        origin = {
            "genesis_id": f"ella-genesis:{_chash([declaration, approved_did])[:12]}",
            "namespace": NAMESPACE_ELLA,
            "created_by": approved_did,
            "created_by_role": "SOVEREIGN",
            "authorized_action": ACTION_GENESIS,
            "declaration": declaration,
            "provenance": "SELF_REPORTED",
            "provenance_subtype": "SOVEREIGN_DECLARATION",
            "valid_day": self.today,            # R2-V5
            "ts": self.clock(),
            "autonomy": "DISABLED",
        }
        origin["content_hash"] = _chash(origin)
        with open(self._path("ELLA_ORIGIN.json"), "w") as f:
            json.dump(origin, f, indent=2, sort_keys=True)
        self._audit({"event": "genesis", "genesis_id": origin["genesis_id"],
                     "content_hash": origin["content_hash"], "by": approved_did})
        return origin

    def propose_identity(self, identity_content: dict,
                         authorization: ChangeAuthorization) -> dict:
        self._runtime_separation_check()
        approved_did = self._verify(authorization, ACTION_PROPOSAL, identity_content)
        proposal = {
            "proposal_id": f"ella-id:{_chash(identity_content)[:12]}",
            "namespace": NAMESPACE_ELLA,
            "entity": "Identity",
            "status": "PROPOSED",
            "content": identity_content,
            "provenance": "SELF_REPORTED",
            "provenance_subtype": "SOVEREIGN_DECLARATION",
            "authorized_by": approved_did,
            "valid_day": self.today,
            "ts": self.clock(),
        }
        proposal["content_hash"] = _chash(proposal)
        with open(self._path("ELLA_IDENTITY_PROPOSAL.json"), "w") as f:
            json.dump(proposal, f, indent=2, sort_keys=True)
        self._audit({"event": "identity_proposal", "proposal": proposal["proposal_id"],
                     "status": "PROPOSED", "by": approved_did})
        return proposal

    def _load_checked(self, name):
        doc = json.load(open(self._path(name)))
        h = doc.pop("content_hash")
        if _chash(doc) != h:
            raise GenesisContractViolation(f"{name}: contenido manipulado")
        doc["content_hash"] = h   # restaurar: los consumidores legitimos la necesitan
        return doc

    def load_origin(self, today: str | None = None) -> dict:
        origin = self._load_checked("ELLA_ORIGIN.json")
        if today is not None and origin["valid_day"] != today:   # R2-V5
            raise GenesisContractViolation("ELLA_ORIGIN expirado (valid_day mismatch)")
        return origin

    def load_proposal(self, today: str | None = None) -> dict:
        """R2-V4: verificador real del proposal."""
        p = self._load_checked("ELLA_IDENTITY_PROPOSAL.json")
        if today is not None and p["valid_day"] != today:
            raise GenesisContractViolation("proposal expirada (valid_day mismatch)")
        return p

    def verify_freshness(self, today: str) -> bool:
        """R2-V5: regla explicita — la evidencia del dia de emision es valida ese dia."""
        return today == self.today

    def enforce_separation(self, foreign_namespace: str, foreign_root: str):
        if foreign_namespace != NAMESPACE_ELLA:
            raise CrossNamespaceViolation(
                f"acceso desde namespace '{foreign_namespace}' al self de ELLA: PROHIBIDO")
        if os.path.abspath(foreign_root) != os.path.abspath(self.root):
            raise CrossNamespaceViolation("ruta ajena al namespace ELLA: PROHIBIDO")


def record_yo_model_of_ella(yo_self_entities: dict, observation: dict) -> dict:
    """R2-V2: solo destino namespace YO; rechaza cualquier otro destino."""
    if not isinstance(yo_self_entities, dict):
        raise CrossNamespaceViolation("destino debe ser dict del namespace YO")
    ns = yo_self_entities.get("namespace", NAMESPACE_YO)
    if ns != NAMESPACE_YO:
        raise CrossNamespaceViolation(
            f"YO_MODEL_OF_ELLA solo puede escribir en namespace YO, destino='{ns}'")
    model = {
        "kind": "Relationships",
        "subject": "ELLA (modelo del YO, no la entidad)",
        "observation": observation,
        "provenance": "INFERRED",
        "provenance_subtype": "YO_MODEL_OF_ELLA",
        "not_ella_identity": True,
    }
    yo_self_entities.setdefault("Relationships", []).append(model)
    return model
