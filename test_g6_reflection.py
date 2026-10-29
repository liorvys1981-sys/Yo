import sys, unittest, json
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from reflection import reflect, Insight, UNCERTAINTY_THRESHOLD

EXP = [
    {"id": "e1", "domain": "salud", "key": "ejercicio", "value": "hecho",
     "provenance": "OBSERVED", "ts": 1.0},
    {"id": "e2", "domain": "salud", "key": "ejercicio", "value": "hecho",
     "provenance": "OBSERVED", "ts": 2.0},
    {"id": "e3", "domain": "salud", "key": "ejercicio", "value": "hecho",
     "provenance": "OBSERVED", "ts": 3.0},
]

def types(ins):
    return {i.type for i in ins}


class TestDeteccion(unittest.TestCase):
    def test_pattern_3_ocurrencias(self):
        self.assertIn("PATTERN", types(reflect(EXP)))

    def test_sin_pattern_bajo_umbral(self):
        self.assertNotIn("PATTERN", types(reflect(EXP[:2])))

    def test_contradiccion_declarado_vs_observado(self):
        exp = EXP + [{"id": "e4", "domain": "salud", "key": "ejercicio",
                      "value": "omitido", "provenance": "SELF_REPORTED", "ts": 4.0}]
        self.assertIn("CONTRADICTION", types(reflect(exp)))

    def test_sin_contradiccion_si_coinciden(self):
        exp = EXP + [{"id": "e4", "domain": "salud", "key": "ejercicio",
                      "value": "hecho", "provenance": "SELF_REPORTED", "ts": 4.0}]
        self.assertNotIn("CONTRADICTION", types(reflect(exp)))

    def test_strength_en_5(self):
        exp = EXP + [
            {"id": "e4", "domain": "salud", "key": "ejercicio", "value": "hecho",
             "provenance": "OBSERVED", "ts": 4.0},
            {"id": "e5", "domain": "salud", "key": "ejercicio", "value": "hecho",
             "provenance": "OBSERVED", "ts": 5.0}]
        self.assertIn("STRENGTH", types(reflect(exp)))

    def test_blind_spot_y_recommendation(self):
        ins = reflect(EXP, expected_domains=("salud", "finanzas"))
        t = types(ins)
        self.assertIn("BLIND_SPOT", t)
        self.assertIn("RECOMMENDATION", t)
        bs = [i for i in ins if i.type == "BLIND_SPOT"][0]
        self.assertEqual(bs.domain, "finanzas")


class TestEtiquetadoSoberano(unittest.TestCase):
    def test_hypothesis_siempre_inferred(self):
        hyps = [i for i in reflect(EXP) if i.type == "HYPOTHESIS"]
        self.assertTrue(hyps)
        for h in hyps:
            self.assertEqual(h.provenance, "INFERRED")

    def test_uncertain_por_baja_confianza(self):
        ins = reflect(EXP)   # pattern conf = 3/5 = 0.6; hypothesis = 0.42
        hyps = [i for i in ins if i.type == "HYPOTHESIS"]
        pats = [i for i in ins if i.type == "PATTERN"]
        self.assertTrue(all(h.label != "UNCERTAIN" for h in pats))
        self.assertTrue(any(h.label == "UNCERTAIN" for h in hyps)
                        or all(h.confidence >= UNCERTAINTY_THRESHOLD for h in hyps))
        # verificacion estricta: todo output con conf < umbral lleva label UNCERTAIN
        for i in ins:
            if i.confidence < UNCERTAINTY_THRESHOLD:
                self.assertEqual(i.label, "UNCERTAIN")

    def test_campos_obligatorios_en_toda_salida(self):
        ins = reflect(EXP, expected_domains=("finanzas",))
        for i in ins:
            for campo in ("provenance", "evidence", "confidence", "ts", "version"):
                self.assertTrue(hasattr(i, campo), f"falta {campo} en {i.type}")

    def test_versionado_con_prior_insights(self):
        ins1 = reflect(EXP)
        prior = [json.loads(json.dumps(__import__("dataclasses").asdict(i))) for i in ins1]
        ins2 = reflect(EXP, prior_insights=tuple(prior))
        d = {i.id: i for i in ins2}
        for i in ins1:
            self.assertEqual(d[i.id].version, i.version + 1)

    def test_ts_derivado_del_input_determinista(self):
        ins = reflect(EXP)
        self.assertTrue(all(i.ts == 3.0 for i in ins))

    def test_determinismo_20_corridas(self):
        a = reflect(EXP, expected_domains=("finanzas",))
        for _ in range(20):
            b = reflect(EXP, expected_domains=("finanzas",))
            self.assertEqual(
                [__import__("dataclasses").asdict(x) for x in a],
                [__import__("dataclasses").asdict(x) for x in b])


class TestGuardNoEscritura(unittest.TestCase):
    def test_rechaza_digitalself(self):
        from digital_self import DigitalSelf
        ds = DigitalSelf("s", "t")
        with self.assertRaises(TypeError):
            reflect(ds)   # no es list

    def test_no_importa_modulos_de_escritura(self):
        src = open("/mnt/agents/output/EL_YO/04_COGNICION/reflection.py").read()
        for banned in ("digital_self", "genome_store", "evolution_engine"):
            self.assertNotIn(f"import {banned}", src)
            self.assertNotIn(f"from {banned}", src)

    def test_salida_no_es_escritura_a_genome(self):
        """Las inferencias no se convierten en Identity/Values/Beliefs:
        reflect() devuelve datos; no existe API de escritura en el modulo."""
        import reflection
        escritoras = [m for m in dir(reflection)
                      if any(v in m.lower() for v in ("write", "save", "store", "update",
                                                      "mutate", "commit"))]
        self.assertEqual(escritoras, [])


if __name__ == "__main__":
    unittest.main()
