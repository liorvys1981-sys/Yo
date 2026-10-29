"""R1 HARDENING — autoridad verificable para cambios fundamentales.

CALLER -> GenomeStore.change() -> AUTHORIZATION VERIFICATION -> REAL AUTHORITY
La autoridad = AuthorizationGate real (EL_YO) + DID ed25519 (identity_engine real).
- Authority (control plane, posee la CLAVE PRIVADA) emite ChangeAuthorization
  SOLO despues de que el gate real autorice (frase-canal + doble llave).
- GenomeStore verifica con la CLAVE PUBLICA (authority_did): cero secretos en
  storage. Vinculacion kind + frescura day + firma ed25519.
No se toca digital_self.py (contrato v2.0.0 congelado).
"""
from __future__ import annotations
import hashlib, json, sys
from dataclasses import dataclass

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/01_IDENTIDAD")
from el_yo.constitution import Action, Denied
from digital_self import FUNDAMENTAL_KINDS
from identity import Identity


class InvalidAuthorization(Denied):
    code = "INVALID_AUTHORIZATION"


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class ChangeAuthorization:
    kind: str
    did: str
    day: str
    nonce: str
    signature: str
    content_hash: str | None = None   # R2: vinculo de contenido opcional

    def payload(self) -> dict:
        p = {"kind": self.kind, "did": self.did, "day": self.day, "nonce": self.nonce}
        if self.content_hash:
            p["content_hash"] = self.content_hash
        return p

    def canonical(self) -> bytes:
        return _canon(self.payload())


class Authority:
    """Emisor de autorizaciones. Posee la clave privada (control plane / EL_YO vault).
    La unica forma de emitir: pasar el AuthorizationGate REAL."""

    def __init__(self, identity: Identity, gate, today: str):
        self.identity = identity
        self.gate = gate
        self.today = today

    def authorize_change(self, kind: str, channel_phrase: str) -> ChangeAuthorization:
        impact = "destructiva" if kind in FUNDAMENTAL_KINDS else "reversible_menor"
        return self.authorize_action(kind, impact, channel_phrase)

    def authorize_action(self, kind: str, impact: str, channel_phrase: str,
                         content_hash: str | None = None) -> ChangeAuthorization:
        """R2: accion soberana con impact explicito + vinculo de contenido."""
        self.gate.authorize(Action(kind, impact), actor="humano",
                            phrase=channel_phrase)          # gate real; Denied si falla
        base = _canon([kind, self.identity.did, self.today, channel_phrase])
        nonce = hashlib.sha256(base).hexdigest()[:16]
        payload = {"kind": kind, "did": self.identity.did,
                   "day": self.today, "nonce": nonce}
        if content_hash:
            payload["content_hash"] = content_hash
        return ChangeAuthorization(kind=kind, did=self.identity.did,
                                   day=self.today, nonce=nonce,
                                   signature=self.identity.sign(_canon(payload)),
                                   content_hash=content_hash)


def verify_authorization(auth: ChangeAuthorization, authority_did: str,
                         expected_kind: str, today: str,
                         expected_content_hash: str | None = None) -> str:
    """Verificacion criptografica con CLAVE PUBLICA. Devuelve el DID aprobador
    (identidad verificable, no string libre). Lanza InvalidAuthorization."""
    import base64
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if not isinstance(auth, ChangeAuthorization):
        raise InvalidAuthorization("objeto de autorizacion invalido")
    if auth.did != authority_did:
        raise InvalidAuthorization("DID no corresponde a la autoridad configurada")
    if auth.kind != expected_kind:
        raise InvalidAuthorization(f"kind vinculado {auth.kind} != {expected_kind}")
    if auth.day != today:
        raise InvalidAuthorization("autorizacion expirada (day mismatch)")
    if expected_content_hash is not None:
        if auth.content_hash != expected_content_hash:
            raise InvalidAuthorization("contenido no coincide con la autorizacion firmada")
    raw = base64.urlsafe_b64decode(auth.did.split("z6Mk")[1] + "==")
    try:
        Ed25519PublicKey.from_public_bytes(raw).verify(
            base64.urlsafe_b64decode(auth.signature + "=="), auth.canonical())
    except Exception as e:
        raise InvalidAuthorization(f"firma invalida: {e}")
    return auth.did      # la identidad verificada del aprobador
