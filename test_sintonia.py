import sys, unittest
sys.path.insert(0, '/mnt/agents/output/EL_YO/11_EMOCION')
sys.path.insert(0, '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA')
from sintonia_engine import SintoniaEngine, SintoniaError, InteractionParams, PARAM_RANGES


class TestSintonia(unittest.TestCase):
    def test_defaults_validos(self):
        p = InteractionParams()
        self.assertEqual(p.pacing, 3)

    def test_rangos(self):
        with self.assertRaises(SintoniaError):
            InteractionParams(pacing=9)
        with self.assertRaises(SintoniaError):
            InteractionParams(question_frequency=1.5)

    def test_signal_self_reported_pesa_mas(self):
        e = SintoniaEngine(clock=lambda: 1.0)
        p1 = e.apply_signal("preference_pacing", 1.0, "SELF_REPORTED")
        self.assertGreater(p1.pacing, 3)
        e2 = SintoniaEngine(clock=lambda: 1.0)
        p2 = e2.apply_signal("preference_pacing", 1.0, "INFERRED")
        self.assertLess(p2.pacing, p1.pacing)   # inferencia no define al usuario

    def test_provenance_invalido(self):
        e = SintoniaEngine(clock=lambda: 1.0)
        with self.assertRaises(SintoniaError):
            e.apply_signal("preference_pacing", 0.5, "IMPUESTO")

    def test_usuario_fija_y_no_se_toca(self):
        e = SintoniaEngine(clock=lambda: 1.0)
        e.fix_by_user(pacing=1, response_length=5)
        p = e.apply_signal("preference_pacing", 1.0, "SELF_REPORTED")
        self.assertEqual(p.pacing, 1)   # autonomia preservada

    def test_no_lenguaje_emocional(self):
        e = SintoniaEngine(clock=lambda: 1.0)
        with self.assertRaises(SintoniaError):
            e.generate_emotional_language("consuelo")

    def test_senal_desconocida(self):
        e = SintoniaEngine(clock=lambda: 1.0)
        with self.assertRaises(SintoniaError):
            e.apply_signal("manipular", 1.0, "SELF_REPORTED")

    def test_param_desconocido_fix(self):
        e = SintoniaEngine(clock=lambda: 1.0)
        with self.assertRaises(SintoniaError):
            e.fix_by_user(admiration=5)


if __name__ == "__main__":
    unittest.main()
