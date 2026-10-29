import os, sys, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from reflection import reflect
from insights import (InsightTracker, STATES, TRANSITIONS, InvalidInsightState,
    InvalidInsightTransition, MissingEvidence, HumanConfirmationRequired)
from cognitive_api import InsightsAPI, RequestContext

EXP = [
    {"id": "e1", "domain": "habitos", "key": "lectura", "value": "hecha",
     "provenance": "OBSERVED", "ts": 1.0},
    {"id": "e2", "domain": "habitos", "key": "lectura", "value": "hecha",
     "provenance": "OBSERVED", "ts": 2.0},
    {"id": "e3", "domain": "habitos", "key": "lectura", "value": "hecha",
     "provenance": "OBSERVED", "ts": 3.0},
]
CTX = RequestContext("t1", "s1", "ci1", "scope", "auth")


def mk(tmp=None, clock_val=700.0):
    ledger = None
    if tmp:
        from el_yo.evidence import EvidenceLedger
        ledger = EvidenceLedger(os.path.join(tmp, "ledger.jsonl"))
    return InsightTracker(ledger=ledger, clock=lambda: clock_val)


class TestRegistro(unittest.TestCase):
    def test_fact_types_quedan_registered(self):
        tr = mk()
        out = tr.register_reflection_outputs(reflect(EXP))
        fact = [i for i in out if i.type in ("PATTERN", "STRENGTH")]
        self.assertTrue(all(i.state == "REGISTERED" for i in fact))

    def test_hypothesis_nace_hypothesized_nunca_confirmed(self):
        tr = mk()
        out = tr.register_reflection_outputs(reflect(EXP))
        hyps = [i for i in out if i.type == "HYPOTHESIS"]
        self.assertTrue(hyps)
        self.assertTrue(all(i.state == "HYPOTHESIZED" for i in hyps))
        self.assertFalse(any(i.state == "CONFIRMED" for i in out))

    def test_campos_conservados(self):
        tr = mk()
        out = tr.register_reflection_outputs(reflect(EXP))
        for i in out:
            self.assertTrue(all([i.provenance, i.evidence is not None,
                                 0 <= i.confidence <= 1, i.ts == 3.0, i.version >= 1,
                                 i.source]))


class TestTransicionesValidas(unittest.TestCase):
    def setUp(self):
        self.tr = mk()
        out = self.tr.register_reflection_outputs(reflect(EXP))
        self.fact = [i for i in out if i.type == "PATTERN"][0]
        self.hyp = [i for i in out if i.type == "HYPOTHESIS"][0]

    def test_registered_a_hypothesized(self):
        r = self.tr.state_change(CTX, self.fact.id, "HYPOTHESIZED", ("ev:p",))
        self.assertEqual((r["from"], r["to"], r["version"]), ("REGISTERED", "HYPOTHESIZED", 2))

    def test_hypothesis_a_refuted_sistema(self):
        r = self.tr.state_change(CTX, self.hyp.id, "REFUTED",
                                 ("e4", "contradiccion observada"), confirmed_by="system")
        self.assertEqual(r["to"], "REFUTED")

    def test_hypothesis_a_confirmed_requiere_humano(self):
        r = self.tr.state_change(CTX, self.hyp.id, "CONFIRMED", ("ev:c",),
                                 confirmed_by="humano")
        self.assertEqual((r["to"], r["version"]), ("CONFIRMED", 2))
        self.assertEqual(r["provenance"], "INFERRED")   # provenance preservado

    def test_confirmed_refuted_terminales(self):
        self.tr.state_change(CTX, self.hyp.id, "REFUTED", ("e",))
        with self.assertRaises(InvalidInsightTransition):
            self.tr.state_change(CTX, self.hyp.id, "CONFIRMED", ("e",),
                                 confirmed_by="humano")


class TestTransicionesInvalidas(unittest.TestCase):
    def setUp(self):
        self.tr = mk()
        out = self.tr.register_reflection_outputs(reflect(EXP))
        self.hyp = [i for i in out if i.type == "HYPOTHESIS"][0]

    def test_estado_desconocido(self):
        with self.assertRaises(InvalidInsightState):
            self.tr.state_change(CTX, self.hyp.id, "VERDAD", ("e",))

    def test_salto_directo_a_confirmed_sin_paso(self):
        tr = mk()
        out = tr.register_reflection_outputs(reflect(EXP))
        fact = [i for i in out if i.type == "PATTERN"][0]
        with self.assertRaises(InvalidInsightTransition):
            tr.state_change(CTX, fact.id, "CONFIRMED", ("e",), confirmed_by="humano")

    def test_hypothesis_no_confirmada_automaticamente(self):
        with self.assertRaises(HumanConfirmationRequired):
            self.tr.state_change(CTX, self.hyp.id, "CONFIRMED", ("e",))  # system por defecto

    def test_state_change_sin_evidencia(self):
        with self.assertRaises(MissingEvidence):
            self.tr.state_change(CTX, self.hyp.id, "REFUTED", ())

    def test_insight_inexistente(self):
        with self.assertRaises(InvalidInsightState):
            self.tr.state_change(CTX, "ins:nada", "REFUTED", ("e",))

    def test_tracker_es_insights_api(self):
        self.assertIsInstance(self.tr, InsightsAPI)
        with self.assertRaises(Exception):
            self.tr.state_change(None, self.hyp.id, "REFUTED", ("e",))   # ctx ausente


class TestAuditoria(unittest.TestCase):
    def test_cada_state_change_auditable(self):
        tmp = tempfile.mkdtemp()
        tr = mk(tmp)
        out = tr.register_reflection_outputs(reflect(EXP))
        hyp = [i for i in out if i.type == "HYPOTHESIS"][0]
        tr.state_change(CTX, hyp.id, "REFUTED", ("e4",))
        tipos = []
        import json as J
        with open(os.path.join(tmp, "ledger.jsonl")) as f:
            for line in f:
                tipos.append(J.loads(line)["event"]["type"])
        self.assertEqual(tipos.count("insight_registered"), len(out))
        self.assertEqual(tipos.count("insight_state_change"), 1)
        self.assertTrue(tr.ledger.verify())

    def test_evidencia_y_confidence_conservadas_en_refutado(self):
        tr = mk()
        out = tr.register_reflection_outputs(reflect(EXP))
        hyp = [i for i in out if i.type == "HYPOTHESIS"][0]
        conf0 = hyp.confidence
        tr.state_change(CTX, hyp.id, "REFUTED", ("e4", "e5"), confirmed_by="system")
        self.assertEqual(hyp.evidence, ("e4", "e5"))
        self.assertEqual(hyp.confidence, conf0)
        self.assertEqual(hyp.version, 2)
        self.assertEqual(hyp.history[-1]["to"], "REFUTED")

    def test_determinismo(self):
        def run():
            tr = mk(clock_val=42.0)
            out = tr.register_reflection_outputs(reflect(EXP))
            hyp = [i for i in out if i.type == "HYPOTHESIS"][0]
            tr.state_change(CTX, hyp.id, "REFUTED", ("e4",))
            return [(h["from"], h["to"], h["ts"]) for h in hyp.history]
        self.assertEqual(run(), run())

    def test_no_toca_digital_self(self):
        src = open("/mnt/agents/output/EL_YO/04_COGNICION/insights.py").read()
        for banned in ("digital_self", "genome_store", "pipeline_evolution", "evolution_engine"):
            self.assertNotIn(f"import {banned}", src)
            self.assertNotIn(f"from {banned}", src)


if __name__ == "__main__":
    unittest.main()
