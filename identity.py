"""Identidad autosoberana: DID did:key + VC firmadas + revocacion (Capa 15)."""
from __future__ import annotations
import base64, json, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

MULTIBASE_ED25519 = "z6Mk"  # prefijo did:key multibase para ed25519


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _from_b64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


class Identity:
    """Par de claves ed25519 + DID did:key. Sin red, sin terceros."""

    def __init__(self, seed: bytes | None = None):
        self._sk = Ed25519PrivateKey.from_private_bytes(seed) if seed else Ed25519PrivateKey.generate()
        self._vk = self._sk.public_key()
        raw = self._vk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.did = f"did:key:{MULTIBASE_ED25519}{_b64u(raw)}"

    @property
    def public_key_multibase(self) -> str:
        return MULTIBASE_ED25519 + _b64u(
            self._vk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))

    def sign(self, data: bytes) -> str:
        return _b64u(self._sk.sign(data))

    def export_seed(self) -> bytes:
        return self._sk.private_bytes(
            serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
            serialization.NoEncryption())


class CredentialIssuer:
    """Emite credenciales verificables W3C-VC (JWT-like compacto, eddsa)."""

    def __init__(self, identity: Identity):
        self.id = identity

    def issue(self, subject_did: str, claims: dict, days: int = 365) -> str:
        now = __import__("time").time()
        payload = {
            "iss": self.id.did, "sub": subject_did,
            "iat": int(now), "exp": int(now) + days * 86400,
            "vc": {"@context": ["https://www.w3.org/ns/credentials/v2"],
                   "type": ["VerifiableCredential"], "credentialSubject": claims},
        }
        body = _b64u(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        sig = self.id.sign(body.encode())
        return f"{body}.{sig}"


class CredentialVerifier:
    """Verifica VCs: firma, expiracion, emisor permitido y revocacion."""

    def __init__(self, trusted_issuers: set[str], status_list: "StatusList"):
        self.trusted = trusted_issuers
        self.status = status_list

    def verify(self, vc: str, now: float | None = None) -> dict:
        import time as _t
        now = _t.time() if now is None else now
        try:
            body, sig = vc.rsplit(".", 1)
            payload = json.loads(_from_b64u(body))
        except Exception:
            return {"valid": False, "reason": "malformed"}
        if payload["iss"] not in self.trusted:
            return {"valid": False, "reason": "untrusted_issuer"}
        if now > payload["exp"]:
            return {"valid": False, "reason": "expired"}
        raw_pk = _from_b64u(payload["iss"].split(MULTIBASE_ED25519)[1])
        vk = Ed25519PublicKey.from_public_bytes(raw_pk)
        try:
            vk.verify(_from_b64u(sig), body.encode())
        except Exception:
            return {"valid": False, "reason": "bad_signature"}
        if self.status.is_revoked(payload["sub"]):
            return {"valid": False, "reason": "revoked"}
        return {"valid": True, "sub": payload["sub"], "iss": payload["iss"]}


class StatusList:
    """Lista de revocacion por sujeto (simplificacion del StatusList bitstring)."""

    def __init__(self):
        self._revoked: set[str] = set()

    def revoke(self, subject_did: str) -> None:
        self._revoked.add(subject_did)

    def is_revoked(self, subject_did: str) -> bool:
        return subject_did in self._revoked
