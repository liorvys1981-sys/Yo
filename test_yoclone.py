"""YO CLONE — pruebas FASE 8. Fixtures sinteticos; nunca datos biometricos reales."""
import sys, unittest, tempfile, os, json
sys.path.insert(0, '/mnt/agents/output/APP_YO/yoclone')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime')
sys.path.insert(0, '/mnt/agents/output/EL_YO/05_RAZONAMIENTO')
sys.path.insert(0, '/mnt/agents/output/EL_YO/17_SOVEREIGNTY')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
from onboarding import (OnboardingEngine, OnboardingError, ConsentRequired,
    ProviderTransferUnauthorized, image_quality_score, MIN_PHOTOS)
from clone_representation import CloneBuilder, CloneError, ProviderRequired, NAMESPACE
from conversation import LiveConversation, ConversationError, mk_conversation
from el_yo.evidence import EvidenceLedger
from identity import Identity
from authority import Authority
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
CODE = DailyCodeProvider(KEY).code(TODAY)
_canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


def synth_image(quality="good", seed=1):
    """Fixture sintetico determinista (NO biometrico real)."""
    if quality == "good":
        return bytes([(seed * 7 + i) % 180 + 40 for i in range(2048)])
    if quality == "dark":
        return bytes([10] * 2048)
    return bytes([i % 8 for i in range(32)])   # corrupto/pobre


def mk_onb():
    led = EvidenceLedger(os.path.join(tempfile.mkdtemp(), "o.jsonl"))
    return OnboardingEngine("user-1", "YO", ledger=led, clock=lambda: 1.0), led


class TestConsentimiento(unittest.TestCase):
    def test_1_explicacion_previa(self):
        e, _ = mk_onb()
        self.assertIn("consentimiento", e.explanation_text().lower() or "cancelar")

    def test_2_sin_consentimiento_no_captura(self):
        e, _ = mk_onb()
        with self.assertRaises(ConsentRequired):
            e.add_capture("IMAGE", synth_image())

    def test_3_consentimiento_por_scope(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        e.add_capture("IMAGE", synth_image())
        with self.assertRaises(ConsentRequired):
            e.add_capture("VOICE", b"voz sintetica")

    def test_4_scopes_invalidos(self):
        e, _ = mk_onb()
        with self.assertRaises(OnboardingError):
            e.grant_consent(("ALMA",))

    def test_5_revocacion_implicita_eliminar(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        c = e.add_capture("IMAGE", synth_image())
        e.remove_capture(c["sha256"])
        self.assertEqual(e.captures, [])

    def test_6_cancelar_borra_todo(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        e.add_capture("IMAGE", synth_image())
        e.cancel()
        self.assertEqual(e.captures, [])


class TestCalidadCaptura(unittest.TestCase):
    def test_7_calidad_buena_vs_mala(self):
        self.assertTrue(image_quality_score(synth_image("good"))["ok"])
        self.assertFalse(image_quality_score(synth_image("dark"))["ok"])
        self.assertFalse(image_quality_score(synth_image("poor"))["ok"])

    def test_8_progreso_y_umbral(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        e.add_capture("IMAGE", synth_image("dark"))    # no cuenta ok
        p = e.progress()
        self.assertTrue(p["needs_more"])
        for i in range(MIN_PHOTOS):
            e.add_capture("IMAGE", synth_image("good", seed=i))
        p2 = e.progress()
        self.assertTrue(p2["ready"])

    def test_9_max_fotos(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        for i in range(10):
            e.add_capture("IMAGE", synth_image("good", seed=100 + i))
        with self.assertRaises(OnboardingError):
            e.add_capture("IMAGE", synth_image("good", seed=999))


class TestTransferenciaProveedor(unittest.TestCase):
    def test_10_transferencia_requiere_auth_r1(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        with self.assertRaises(ProviderTransferUnauthorized):
            e.authorize_provider_transfer("avatar-corp", ("IMAGE",), None, AUTH.did, TODAY)

    def test_11_transferencia_con_auth_valida(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        content = {"provider": "avatar-corp", "kinds": ["IMAGE"], "user": "user-1"}
        az = Authority(AUTH, GATE, TODAY).authorize_action(
            "clone-provider-transfer", "externa_irreversible",
            f"EJECUTA transferencia {CODE}",
            content_hash=__import__("hashlib").sha256(_canon(content)).hexdigest())
        r = e.authorize_provider_transfer("avatar-corp", ("IMAGE",), az, AUTH.did, TODAY)
        self.assertTrue(r["authorized"])

    def test_12_transferencia_sin_consentimiento(self):
        e, _ = mk_onb()
        content = {"provider": "x", "kinds": ["IMAGE"], "user": "user-1"}
        az = Authority(AUTH, GATE, TODAY).authorize_action(
            "clone-provider-transfer", "externa_irreversible",
            f"EJECUTA transferencia {CODE}",
            content_hash=__import__("hashlib").sha256(_canon(content)).hexdigest())
        with self.assertRaises(ConsentRequired):
            e.authorize_provider_transfer("x", ("IMAGE",), az, AUTH.did, TODAY)


class TestRepresentacionClon(unittest.TestCase):
    def test_13_clon_no_es_identidad(self):
        b = CloneBuilder(clock=lambda: 1.0)
        c = b.register("user-1", ("sha:1", "sha:2"), 0.75)
        self.assertFalse(c.is_identity)
        self.assertFalse(c.is_sovereign)
        self.assertEqual(c.namespace, NAMESPACE)

    def test_14_registro_requiere_capturas(self):
        b = CloneBuilder(clock=lambda: 1.0)
        with self.assertRaises(CloneError):
            b.register("user-1", (), 0.5)

    def test_15_generacion_sin_proveedor_bloqueada(self):
        b = CloneBuilder(clock=lambda: 1.0)
        c = b.register("user-1", ("sha:1",), 0.7)
        with self.assertRaises(ProviderRequired):
            b.generate(c)   # EXTERNAL_BLOCKED honesto: no se simula replica

    def test_16_consistencia_evaluable(self):
        b = CloneBuilder(clock=lambda: 1.0)
        c = b.register("user-1", ("sha:a", "sha:b"), 0.8)
        r = b.consistency_report(c)
        self.assertTrue(r["all_provenanced"])
        self.assertFalse(r["is_identity"])


class TestConversacion(unittest.TestCase):
    def setUp(self):
        self.conv, _ = mk_conversation()

    def test_17_estados_y_sesion(self):
        self.assertEqual(self.conv.state, "IDLE")
        self.conv.start()
        self.assertEqual(self.conv.state, "LISTENING")
        self.conv.mute(True)
        self.assertEqual(self.conv.state, "MUTED")
        self.conv.mute(False)
        self.conv.end()
        self.assertEqual(self.conv.state, "ENDED")

    def test_18_turno_con_latencia_medida(self):
        self.conv.start()
        r = self.conv.handle_utterance("operator", "hola clon")
        self.assertIn(r["state"], ("LISTENING",))
        self.assertTrue(r["latency"]["measured"])
        self.assertGreaterEqual(r["latency"]["total_s"], 0)
        self.assertEqual(r["tts"], "BLOCKED")       # honesto
        self.assertEqual(r["animation"], "BLOCKED") # honesto

    def test_19_interrupcion(self):
        self.conv.start()
        self.conv.handle_utterance("operator", "primero")
        self.conv.interrupt()
        self.assertTrue(self.conv.interrupted)

    def test_20_no_respuestas_prefabricadas(self):
        self.conv.start()
        r1 = self.conv.handle_utterance("operator", "cuentame algo")
        r2 = self.conv.handle_utterance("operator", "otra cosa distinta")
        self.assertEqual(r1["route"], "DETERMINISTIC")
        self.assertNotEqual(r1["response"], r2["response"])  # pipeline real, no fijo

    def test_21_sesion_terminada_rechaza(self):
        self.conv.start(); self.conv.end()
        with self.assertRaises(ConversationError):
            self.conv.handle_utterance("operator", "hola")

    def test_22_mute_rechaza_turno(self):
        self.conv.start(); self.conv.mute(True)
        with self.assertRaises(ConversationError):
            self.conv.handle_utterance("operator", "hola")


class TestInvariantesYMemoria(unittest.TestCase):
    def test_23_evento_no_es_verdad_en_capturas(self):
        e, _ = mk_onb()
        e.grant_consent(("IMAGE",))
        c = e.add_capture("IMAGE", synth_image())
        self.assertEqual(c["provenance"], "USER_PROVIDED")  # dato, no verdad absoluta

    def test_24_aislamiento_entre_usuarios(self):
        e1, _ = mk_onb()
        e2 = OnboardingEngine("user-2", "YO", clock=lambda: 1.0)
        e1.grant_consent(("IMAGE",))
        e2.grant_consent(("IMAGE",))
        c1 = e1.add_capture("IMAGE", synth_image(seed=42))
        self.assertNotIn(c1["sha256"], [c["sha256"] for c in e2.captures])

    def test_25_eliminacion_completa(self):
        e, led = mk_onb()
        e.grant_consent(("IMAGE",))
        e.add_capture("IMAGE", synth_image())
        r = e.delete_all()
        self.assertEqual(r["removed"], 1)
        self.assertEqual(e.captures, [])
        self.assertTrue(led.verify())


if __name__ == "__main__":
    unittest.main()
