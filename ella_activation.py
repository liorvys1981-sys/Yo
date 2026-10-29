"""P10-B11 ELLA IDENTITY ACTIVATION — implementa el contrato ELLA_IDENTITY_ACTIVATION/v0.1.

Flujo: PROPOSED -> SOVEREIGN AUTHORIZATION -> ACTIVATED. Reutiliza R1 (Authority,
ChangeAuthorization, verify_authorization, AuthorizationGate, identity_engine).
Anti-replay: content binding + nonce determinista + day freshness + existencia de ACTIVE."""
from __future__ import annotations
import hashlib, json, os, sys

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, "/mnt/agents/output/APP_YO/ELLA")
from authority import ChangeAuthorization, verify_authorization, InvalidAuthorization
from ella_genesis import (EllaGenesis, GenesisContractViolation, _canon, _chash,
                          NAMESPACE_ELLA)

ACTION_ACTIVATION = "ELLA-identity-activation"
IMPACT_ACTIVATION = "destructiva"   # doble llave (diseno auditado)
ALL_ENTITIES = ("Identity", "Values", "Beliefs", "Goals", "Traits",
                "Relationships", "Experiences")


class ActivationError(Exception):
    code = "ACTIVATION_ERROR"


class UnauthorizedActivation(ActivationError):
    code = "UNAUTHORIZED_ACTIVATION"


class ProposalIntegrityError(ActivationError):
    code = "PROPOSAL_INTEGRITY_ERROR"


class OriginIntegrityError(ActivationError):
    code = "ORIGIN_INTEGRITY_ERROR"


class DoubleActivation(ActivationError):
    code = "DOUBLE_ACTIVATION"


class NamespaceBindingError(ActivationError):
    code = "NAMESPACE_BINDING_ERROR"


class ExpiredAuthorization(ActivationError):
    code = "EXPIRED_AUTHORIZATION"


class EllaActivation:
    def __init__(self, genesis: EllaGenesis):
        if genesis.authority_did is None:
            raise ActivationError("genesis sin authority_did (R2-V1)")
        self.genesis = genesis
        self.today = genesis.today

    def _active_path(self):
        return self.genesis._path("ELLA_IDENTITY_ACTIVE.json")

    def _proposal_payload_hash(self, proposal: dict) -> str:
        p = {k: v for k, v in proposal.items() if k != "content_hash"}
        return _chash(p)

    def activate(self, authorization: ChangeAuthorization) -> dict:
        g = self.genesis
        # --- precondiciones: origin + proposal integros, freshness ---
        try:
            origin = g.load_origin(today=self.today)
        except GenesisContractViolation as e:
            raise OriginIntegrityError(f"origin: {e}")
        except FileNotFoundError:
            raise OriginIntegrityError("ELLA_ORIGIN no existe")
        try:
            proposal = g.load_proposal(today=self.today)
        except GenesisContractViolation as e:
            raise ProposalIntegrityError(f"proposal alterada: {e}")
        except FileNotFoundError:
            raise ProposalIntegrityError("ELLA_IDENTITY_PROPOSAL no existe")

        # --- namespace binding: la proposal tiene que vivir en namespace ELLA ---
        if proposal.get("namespace") != NAMESPACE_ELLA:
            raise NamespaceBindingError(
                f"proposal namespace={proposal.get('namespace')} != ELLA")

        # --- anti doble activacion ---
        if os.path.exists(self._active_path()):
            raise DoubleActivation("ELLA_IDENTITY_ACTIVE ya existe (anti-replay)")

        # --- autorizacion soberana (reuse R1) ---
        try:
            approved_did = verify_authorization(
                authorization, g.authority_did, ACTION_ACTIVATION, self.today,
                expected_content_hash=self._proposal_payload_hash(proposal))
        except InvalidAuthorization as e:
            msg = str(e)
            if "day mismatch" in msg or "expirada" in msg:
                raise ExpiredAuthorization(msg)
            raise UnauthorizedActivation(msg)

        # --- ACTIVE: copia inmutable del proposal + metadata soberana ---
        active = {
            "activation_id": f"ella-active:{_chash([proposal['proposal_id'], authorization.nonce])[:12]}",
            "namespace": NAMESPACE_ELLA,
            "entity": "Identity",
            "identity_status": "ACTIVE",
            "content": proposal["content"],          # copia inmutable
            "activated_by": approved_did,
            "authorization": {"action": ACTION_ACTIVATION, "nonce": authorization.nonce,
                              "day": authorization.day},
            "origin_content_hash": origin["content_hash"],
            "proposal_id": proposal["proposal_id"],
            "valid_day": self.today,
            "ts": g.clock(),
            "autonomy": "DISABLED",
            "other_entities": {e: "PENDING" for e in ALL_ENTITIES if e != "Identity"},
        }
        active["content_hash"] = _chash(active)
        with open(self._active_path(), "w") as f:
            json.dump(active, f, indent=2, sort_keys=True)
        if g.ledger:
            g.ledger.append({"type": "ella_activation",
                             "activation_id": active["activation_id"],
                             "proposal": proposal["proposal_id"], "nonce": authorization.nonce,
                             "content_hash": active["content_hash"], "by": approved_did})
        return active

    def load_active(self, today: str | None = None) -> dict:
        doc = json.load(open(self._active_path()))
        h = doc.pop("content_hash")
        if _chash(doc) != h:
            raise ActivationError("ELLA_IDENTITY_ACTIVE manipulado")
        if today is not None and doc["valid_day"] != today:
            raise ExpiredAuthorization("ACTIVE expirado (valid_day mismatch)")
        return doc

    def ella_digital_self_scaffold(self) -> dict:
        """Bloque 12: ELLA DigitalSelf tras activacion. Solo Identity ACTIVE."""
        active = self.load_active(today=self.today)
        return {
            "namespace": NAMESPACE_ELLA,
            "contract": "ELLA_SELF_GENESIS/v0.1 + ACTIVATION/v0.1",
            "entities": {"Identity": {"status": "ACTIVE", "content": active["content"],
                                       "provenance": "SELF_REPORTED",
                                       "provenance_subtype": "SOVEREIGN_DECLARATION"},
                         **{e: {"status": "PENDING"} for e in ALL_ENTITIES if e != "Identity"}},
            "autonomy": "DISABLED",
            "origin_ref": active["origin_content_hash"],
        }
