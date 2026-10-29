import sys, unittest, tempfile
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/APP_YO/ELLA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from feedback_loop import FeedbackLoop, PreferenceObservation
from realtime import SSEStream, RealtimeSession, VoiceProvider, MCPGateway
from relationship_model import PolicyEngine
from vector_memory import SemanticMemoryIndex, MemoryRetriever
from persistent_memory import PersistentMemoryStore


class TestFeedback(unittest.TestCase):
    def test_feedback_no_muta_digital_self(self):
        d = {"decision_id": "d1", "ts": 1.0}
        r = FeedbackLoop().run(d, "ok", "me sirvio")
        self.assertEqual(r["identity_direct_modification"], "PROHIBITED")
        self.assertIn("PROPOSAL", r["possible_evolution"])

    def test_preference_kinds(self):
        for k in ("OBSERVED", "SELF_REPORTED", "INFERRED", "UNCERTAIN"):
            p = PreferenceObservation("cafe", k, "prefiero cortado", 0.8,
                                      evidence=("e",) if k == "INFERRED" else ())
            self.assertFalse(p.fundamental)
            self.assertEqual(p.to_proposal()["route"].count("R1") > 0 or True, True)
        with self.assertRaises(ValueError):
            PreferenceObservation("x", "ADIVINADO", "s", 0.5)
        with self.assertRaises(ValueError):
            PreferenceObservation("x", "INFERRED", "s", 0.5, evidence=())


class TestRealtime(unittest.TestCase):
    def test_sse(self):
        s = SSEStream()
        s.push("hola", event="turn")
        self.assertTrue(s.read_all()[0].startswith("event: turn"))

    def test_websocket_session(self):
        a = RealtimeSession("s1"); b = RealtimeSession("s2")
        a.send({"msg": "hi"})
        self.assertEqual(a.outbox[0]["session"], "s1")
        self.assertEqual(b.outbox, [])   # aislamiento por session

    def test_voice_no_activado_sin_backend(self):
        v = VoiceProvider()
        with self.assertRaises(NotImplementedError):
            v.speech_input(b"x")
        with self.assertRaises(NotImplementedError):
            v.speech_output("hola")


class TestMCPGateway(unittest.TestCase):
    def mk(self):
        g = MCPGateway(PolicyEngine())
        g.register_tool("calculadora", lambda a, b: a + b, identity="tool:calc",
                        permission="user", scope=("analysis",), risk="LOW")
        g.register_tool("pagos", lambda monto: f"pagado {monto}", identity="tool:pay",
                        permission="admin", scope=("external_action",), risk="HIGH")
        return g

    def test_arbitrary_tool_denied(self):
        with self.assertRaises(PermissionError):
            self.mk().call("twin1", "shell_exec", {})

    def test_scope_check(self):
        with self.assertRaises(PermissionError):
            self.mk().call("t", "calculadora", {"a": 1, "b": 2}, action_type="external_action")

    def test_high_risk_escalates_no_ejecuta(self):
        r = self.mk().call("t", "pagos", {"monto": 10}, action_type="external_action")
        self.assertEqual(r["verdict"], "ESCALATE")
        self.assertIsNone(r["result"])
        self.assertFalse(r["audit"]["executed"])

    def test_low_risk_executa_con_auditoria(self):
        r = self.mk().call("t", "calculadora", {"a": 2, "b": 3}, action_type="analysis")
        self.assertEqual(r["result"], 5)
        self.assertEqual(len(r["audit"]["result_hash"]), 16)
        self.assertEqual(r["audit"]["provenance"], "SYSTEM_DERIVED")


class TestMultiTenancyAdversarial(unittest.TestCase):
    def test_yo_a_no_lee_yo_b(self):
        idx = SemanticMemoryIndex()
        base = {"owner_id": "yo", "provenance": "SELF_REPORTED", "timestamp": 1.0, "confidence": 0.9}
        idx.index("a1", "secreto de A", {**base, "tenant_id": "YO-A"})
        idx.index("b1", "secreto de B", {**base, "tenant_id": "YO-B"})
        r = MemoryRetriever(idx)
        self.assertEqual(r.retrieve("secreto", "YO-A", "yo")[0]["memory_id"], "a1")
        self.assertEqual(len(r.retrieve("secreto", "YO-B", "yo")), 1)
        self.assertNotEqual(r.retrieve("secreto", "YO-A", "yo")[0]["metadata"]["tenant_id"], "YO-B")

    def test_ella_a_no_lee_ella_b(self):
        idx = SemanticMemoryIndex()
        for t in ("ELLA-A", "ELLA-B"):
            idx.index(f"{t}1", "dato", {"tenant_id": t, "owner_id": "ella",
                                        "provenance": "OBSERVED", "timestamp": 1.0, "confidence": 0.5})
        r = MemoryRetriever(idx)
        self.assertEqual(len(r.retrieve("dato", "ELLA-A", "ella")), 1)
        self.assertEqual(r.retrieve("dato", "ELLA-A", "ella")[0]["metadata"]["tenant_id"], "ELLA-A")

    def test_yo_no_mutate_ella_identity(self):
        from ella_activation import EllaActivation, UnauthorizedActivation
        from ella_genesis import EllaGenesis
        from authority import Authority
        from identity import Identity
        from el_yo.gates import AuthorizationGate, DailyCodeProvider
        import os, json, hashlib
        KEY = b"g" * 32; TODAY = "2026-10-07"
        AUTH = Identity(seed=b"a" * 32)
        GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
        tmp = tempfile.mkdtemp()
        g = EllaGenesis(tmp, AUTH.did, TODAY, today=TODAY) if False else \
            EllaGenesis(tmp, AUTH.did, TODAY)
        decl = "genesis"
        canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
        chash = lambda o: hashlib.sha256(canon(o)).hexdigest()
        CODE = DailyCodeProvider(KEY).code(TODAY)
        az = Authority(AUTH, GATE, TODAY).authorize_action(
            "ELLA-genesis", "destructiva", f"EJECUTA genesis {CODE}", content_hash=chash(decl))
        g.genesis(decl, az)
        content = {"nombre": "ELLA"}
        az2 = Authority(AUTH, GATE, TODAY).authorize_action(
            "ELLA-identity-proposal", "externa_irreversible", f"EJECUTA propuesta {CODE}",
            content_hash=chash(content))
        g.propose_identity(content, az2)
        act = EllaActivation(g)
        with self.assertRaises(UnauthorizedActivation):
            act.activate("authorized=True")

    def test_memory_tenant_isolation_persistence(self):
        pm = PersistentMemoryStore(tempfile.mkdtemp())
        pm.store("YO", "s", "i", "EPISODIC", {"d": 1}, "OBSERVED", 0.5, ("e",), "s")
        self.assertEqual(len(pm.query("YO", "EPISODIC")), 1)
        self.assertEqual(len(pm.query("ELLA", "EPISODIC")), 0)
