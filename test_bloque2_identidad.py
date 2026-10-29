import sys; sys.path.insert(0, "/mnt/agents/output/EL_YO/01_IDENTIDAD")
import json, base64, unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from identity import Identity, CredentialIssuer, CredentialVerifier, StatusList


class TestDID(unittest.TestCase):
    def test_did_format(self):
        self.assertTrue(Identity(seed=b"i" * 32).did.startswith("did:key:z6Mk"))

    def test_deterministic_seed(self):
        self.assertEqual(Identity(seed=b"x" * 32).did, Identity(seed=b"x" * 32).did)

    def test_sign_verify(self):
        idn = Identity(seed=b"i" * 32)
        sig = base64.urlsafe_b64decode(idn.sign(b"hola") + "==")
        raw = base64.urlsafe_b64decode(idn.did.split("z6Mk")[1] + "==")
        Ed25519PublicKey.from_public_bytes(raw).verify(sig, b"hola")


class TestVC(unittest.TestCase):
    def setUp(self):
        self.issuer = Identity(seed=b"i" * 32)
        self.subject = Identity(seed=b"s" * 32)
        self.vc = CredentialIssuer(self.issuer).issue(self.subject.did, {"role": "admin"})

    def test_ok(self):
        r = CredentialVerifier({self.issuer.did}, StatusList()).verify(self.vc)
        self.assertTrue(r["valid"]); self.assertEqual(r["sub"], self.subject.did)

    def test_tampered(self):
        body, sig = self.vc.rsplit(".", 1)
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        payload["vc"]["credentialSubject"]["role"] = "root"
        nuevo = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        r = CredentialVerifier({self.issuer.did}, StatusList()).verify(f"{nuevo}.{sig}")
        self.assertEqual((r["valid"], r["reason"]), (False, "bad_signature"))

    def test_expired(self):
        vc = CredentialIssuer(self.issuer).issue(self.subject.did, {}, days=-1)
        r = CredentialVerifier({self.issuer.did}, StatusList()).verify(vc)
        self.assertEqual(r["reason"], "expired")

    def test_untrusted(self):
        v = CredentialVerifier({Identity(seed=b"o" * 32).did}, StatusList())
        self.assertEqual(v.verify(self.vc)["reason"], "untrusted_issuer")

    def test_revoked(self):
        sl = StatusList(); sl.revoke(self.subject.did)
        r = CredentialVerifier({self.issuer.did}, sl).verify(self.vc)
        self.assertEqual(r["reason"], "revoked")

    def test_malformed(self):
        self.assertEqual(CredentialVerifier({self.issuer.did}, StatusList())
                         .verify("garbage")["reason"], "malformed")


if __name__ == "__main__":
    unittest.main()
