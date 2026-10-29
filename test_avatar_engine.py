import sys, unittest, tempfile, os, json
sys.path.insert(0, "/mnt/agents/output/APP_YO/yoclone")
sys.path.insert(0, "/mnt/agents/output/APP_YO/yoclone/providers")
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/17_SOVEREIGNTY")
sys.path.insert(0, "/mnt/agents/output/EL_YO/14_DIGITAL_SELF")
sys.path.insert(0, "/mnt/agents/output/EL_YO/01_IDENTIDAD")
from onboarding import OnboardingEngine, ProviderTransferUnauthorized
from clone_representation import CloneBuilder, ProviderRequired
from providers.avatar_engine import AvatarEngine
from el_yo.evidence import EvidenceLedger
from identity import Identity
from authority import Authority
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY=b"g"*32; TODAY="2026-10-07"
AUTH=Identity(seed=b"a"*32); GATE=AuthorizationGate(DailyCodeProvider(KEY),TODAY,True)
CODE=DailyCodeProvider(KEY).code(TODAY)
_canon=lambda o: json.dumps(o,sort_keys=True,separators=(",",":")).encode()

def synth(seed=1): return bytes([(seed*7+i)%180+40 for i in range(2048)])

class TestAvatarEngineContract(unittest.TestCase):
    def setUp(self):
        self.led = EvidenceLedger(os.path.join(tempfile.mkdtemp(),"a.jsonl"))
        self.onb = OnboardingEngine("user-1","YO",ledger=self.led,clock=lambda:1.0)
        self.onb.grant_consent(("IMAGE",))
        for i in range(5):
            self.onb.add_capture("IMAGE", synth(i))
        self.b = CloneBuilder(clock=lambda:1.0)
        self.eng = AvatarEngine(self.onb, self.b, AUTH.did, TODAY)

    def test_1_build_clone_usa_capturas_autorizadas(self):
        c = self.eng.build_clone(0.8)
        self.assertEqual(len(c.capture_refs), 5)
        self.assertFalse(c.is_identity)

    def test_2_transferencia_sin_auth_denegada(self):
        with self.assertRaises(ProviderTransferUnauthorized):
            self.eng.transfer_to_engine("http://engine:9000", ("IMAGE",), None)

    def test_3_transferencia_con_auth_ok(self):
        content={"provider":"http://engine:9000","kinds":["IMAGE"],"user":"user-1"}
        az=Authority(AUTH,GATE,TODAY).authorize_action(
            "clone-provider-transfer","externa_irreversible",
            f"EJECUTA transferencia {CODE}",
            content_hash=__import__("hashlib").sha256(_canon(content)).hexdigest())
        r=self.eng.transfer_to_engine("http://engine:9000",("IMAGE",),az)
        self.assertTrue(r["authorized"])

    def test_4_tts_lipsync_blocked_honestos(self):
        self.assertEqual(self.eng.tts().provider, None)
        self.assertEqual(self.eng.lipsync().provider, None)
        self.assertEqual(self.eng.tts().synthesize("hola")["status"], "BLOCKED")

    def test_5_generacion_real_sigue_requiriendo_proveedor(self):
        c = self.eng.build_clone(0.8)
        with self.assertRaises(ProviderRequired):
            self.b.generate(c)

    def test_6_cero_codigo_externo_incorporado(self):
        src = open("/mnt/agents/output/APP_YO/yoclone/providers/avatar_engine.py").read()
        for banned in ["import musetalk", "import wav2lip", "from lip", "aiortc", "requests.post"]:
            self.assertNotIn(banned, src)

if __name__ == "__main__":
    unittest.main()
