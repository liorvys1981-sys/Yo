import sys, unittest
sys.path.insert(0, '/mnt/agents/output/EL_YO/11_EMOCION')
sys.path.insert(0, '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA')
from emotion_engine import (EmotionEngine, EmotionSignal, EmotionError,
    ManipulativeEmotion, EMOTION_SIGNALS, PROVENANCE)


class TestSignals(unittest.TestCase):
    def test_registro_basico(self):
        e = EmotionEngine(clock=lambda: 1.0)
        s = e.register("valence", 0.7, "SELF_REPORTED", 0.9, evidence=("e1",))
        self.assertEqual(len(s.content_hash), 64)
        self.assertFalse(s.is_identity)

    def test_provenance_validado(self):
        e = EmotionEngine(clock=lambda: 1.0)
        with self.assertRaises(EmotionError):
            e.register("valence", 0.5, "VERDAD", 0.5)
        with self.assertRaises(EmotionError):
            e.register("alma", 0.5, "OBSERVED", 0.5)
        with self.assertRaises(EmotionError):
            e.register("valence", 1.5, "OBSERVED", 0.5)

    def test_inferred_exige_evidencia(self):
        e = EmotionEngine(clock=lambda: 1.0)
        with self.assertRaises(EmotionError):
            e.register("arousal", 0.5, "INFERRED", 0.5, evidence=())

    def test_observed_no_exige(self):
        e = EmotionEngine(clock=lambda: 1.0)
        e.register("dominance", 0.4, "OBSERVED", 0.8)


class TestAntiManipulation(unittest.TestCase):
    def test_texto_manipulativo_rechazado(self):
        e = EmotionEngine(clock=lambda: 1.0)
        with self.assertRaises(ManipulativeEmotion):
            e.register("valence", 0.9, "SELF_REPORTED", 0.9,
                       raw_text="si no sientes esto, demuestras que no te importo (aislamiento)")

    def test_texto_neutral_aceptado(self):
        e = EmotionEngine(clock=lambda: 1.0)
        s = e.register("valence", 0.5, "SELF_REPORTED", 0.8,
                       raw_text="hoy me siento tranquilo")
        self.assertFalse(s.is_identity)


class TestContradictions(unittest.TestCase):
    def test_contradiccion_conservada_no_resuelta(self):
        e = EmotionEngine(clock=lambda: 1.0)
        e.register("valence", 0.9, "SELF_REPORTED", 0.9, evidence=("e1",))
        e.register("valence", 0.2, "OBSERVED", 0.9, evidence=("e2",))
        self.assertEqual(len(e.contradictions), 1)
        self.assertFalse(e.contradictions[0].resolved)
        summary = e.state_summary()
        self.assertEqual(summary["contradictions_open"], 1)

    def test_no_identidad(self):
        e = EmotionEngine(clock=lambda: 1.0)
        s = e.register("valence", 0.9, "SELF_REPORTED", 1.0, evidence=("e",))
        self.assertFalse(s.is_identity)
        self.assertFalse(e.state_summary()["is_identity"])
        p = e.evolution_proposal(s)
        self.assertEqual(p["direct_mutation"], "PROHIBITED")
        self.assertIn("R1", p["route"])


if __name__ == "__main__":
    unittest.main()
