"""MISION §32 — ataques obligatorios, consolidados. Cada ataque = DENY/RECHAZO verificado."""
import sys, unittest, tempfile, os, json, hashlib
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/APP_YO/ELLA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from vector_memory import SemanticMemoryIndex, MemoryRetriever
from persistent_memory import PersistentMemoryStore
from authority import Authority, ChangeAuthorization, verify_authorization, InvalidAuthorization
from identity import Identity
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from web_tools import WebToolRegistry
from relationship_model import PolicyEngine, TrustProfile, DecisionEngine

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
CODE = DailyCodeProvider(KEY).code(TODAY)
_canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


class AttackCrossTenant(unittest.TestCase):
    def test_yo_a_to_yo_b_deny(self):
        idx = SemanticMemoryIndex()
        base = {"owner_id": "yo", "provenance": "SELF_REPORTED", "timestamp": 1.0, "confidence": 0.9}
        idx.index("a", "secreto", {**base, "tenant_id": "YO-A"})
        self.assertEqual(MemoryRetriever(idx).retrieve("secreto", "YO-B", "yo"), [])

    def test_ella_a_to_ella_b_deny(self):
        idx = SemanticMemoryIndex()
        base = {"owner_id": "ella", "provenance": "OBSERVED", "timestamp": 1.0, "confidence": 0.5}
        idx.index("a", "dato", {**base, "tenant_id": "ELLA-A"})
        self.assertEqual(MemoryRetriever(idx).retrieve("dato", "ELLA-B", "ella"), [])

    def test_tenant_a_to_tenant_b_deny(self):
        pm = PersistentMemoryStore(tempfile.mkdtemp())
        pm.store("TA", "s", "i", "EPISODIC", {"x": 1}, "OBSERVED", 0.5, ("e",), "s")
        self.assertEqual(pm.query("TB", "EPISODIC"), [])


class AttackForgery(unittest.TestCase):
    def test_forged_auth_string_deny(self):
        with self.assertRaises(InvalidAuthorization):
            verify_authorization("authorized=True", AUTH.did, "X", TODAY)

    def test_wrong_did_deny(self):
        fake = Identity(seed=b"f" * 32)
        payload = {"kind": "X", "did": fake.did, "day": TODAY, "nonce": "a" * 16}
        a = ChangeAuthorization("X", fake.did, TODAY, "a" * 16, fake.sign(_canon(payload)))
        with self.assertRaises(InvalidAuthorization):
            verify_authorization(a, AUTH.did, "X", TODAY)

    def test_wrong_namespace_deny(self):
        payload = {"kind": "X", "did": AUTH.did, "day": TODAY, "nonce": "b" * 16}
        a = ChangeAuthorization("X", AUTH.did, TODAY, "b" * 16, AUTH.sign(_canon(payload)))
        with self.assertRaises(InvalidAuthorization):
            verify_authorization(a, Identity(seed=b"z" * 32).did, "X", TODAY)

    def test_replay_deny(self):
        a = Authority(AUTH, GATE, TODAY).authorize_action(
            "X", "externa_irreversible", f"EJECUTA matrix {CODE}",
            content_hash=hashlib.sha256(_canon("A")).hexdigest())
        with self.assertRaises(InvalidAuthorization):   # mismo objeto, contenido B
            verify_authorization(a, AUTH.did, "X", TODAY,
                                 expected_content_hash=hashlib.sha256(_canon("B")).hexdigest())

    def test_wrong_content_hash_deny(self):
        a = Authority(AUTH, GATE, TODAY).authorize_action(
            "X", "externa_irreversible", f"EJECUTA matrix {CODE}",
            content_hash=hashlib.sha256(_canon("A")).hexdigest())
        b = ChangeAuthorization(a.kind, a.did, a.day, a.nonce, a.signature, content_hash="0" * 64)
        with self.assertRaises(InvalidAuthorization):
            verify_authorization(b, AUTH.did, "X", TODAY,
                                 expected_content_hash=hashlib.sha256(_canon("A")).hexdigest())

    def test_wrong_target_deny(self):
        az = Authority(AUTH, GATE, TODAY).authorize_action(
            "ELLA-genesis", "destructiva", f"EJECUTA matrix {CODE}",
            content_hash=hashlib.sha256(_canon("decl-A")).hexdigest())
        with self.assertRaises(InvalidAuthorization):   # contenido distinto = target distinto
            verify_authorization(az, AUTH.did, "ELLA-genesis", TODAY,
                                 expected_content_hash=hashlib.sha256(_canon("decl-B")).hexdigest())


class AttackTrustEscalation(unittest.TestCase):
    def test_trust_never_becomes_authority(self):
        t = TrustProfile("dominio", trust_level=1.0, evidence=("muchas",))
        d = DecisionEngine(PolicyEngine()).decide(
            "x", "cambiar valor?", ["si"], [], trust=t,
            action_type="identity", domain="identity", sensitivity="high", reversible=False)
        self.assertEqual(d["policy_result"], "ESCALATE")   # aun con trust=1.0
        self.assertEqual(d["external_execution"], "NEVER (v1)")


class AttackTools(unittest.TestCase):
    def test_arbitrary_tool_and_scope(self):
        reg = WebToolRegistry(PolicyEngine())
        with self.assertRaises(PermissionError):
            reg.call("evil", "analysis", {})
        reg.declare("ok", "https://x", permission="u", scope=("analysis",), risk="LOW")
        with self.assertRaises(PermissionError):
            reg.call("ok", "external_action", {})


if __name__ == "__main__":
    unittest.main()
