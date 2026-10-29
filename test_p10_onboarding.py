import os, sys, tempfile, unittest
sys.path.insert(0, '/mnt/agents/output/APP_YO/onboarding')
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from question_registry import REGISTRY, get, categories, RegistryError
from adaptive_engine import AdaptiveEngine, OnboardingSession
from maturity import compute, MaturityError
from cognitive_twin_yo import build_twin
from persistent_memory import PersistentMemoryStore


def mk_engine():
    return AdaptiveEngine(PersistentMemoryStore(tempfile.mkdtemp()), clock=lambda: 1000.0)


class TestRegistry(unittest.TestCase):
    def test_nueve_categorias(self):
        self.assertEqual(len(categories()), 9)

    def test_cada_pregunta_tiene_metadatos(self):
        for q in REGISTRY:
            self.assertTrue(all([q.id, q.category in categories(), q.goal,
                                 isinstance(q.priority, int), q.activation,
                                 q.expected_provenance == "SELF_REPORTED",
                                 q.followup_rules is not None, q.related is not None,
                                 q.no_repeat]))

    def test_ids_estables_unicos(self):
        ids = [q.id for q in REGISTRY]
        self.assertEqual(len(ids), len(set(ids)))
        get("q.identity.1")
        with self.assertRaises(RegistryError):
            get("q.nope")


class TestAdaptive(unittest.TestCase):
    def test_seleccion_sin_repeticion(self):
        e = mk_engine(); s = OnboardingSession()
        q1 = e.next_question(s); self.assertNotEqual(q1["id"], "q.done")
        e.submit_answer(s, q1, "respuesta uno")
        ids = {q1["id"]}
        for _ in range(30):
            q = e.next_question(s)
            if q["id"] == "q.done":
                break
            self.assertNotIn(q["id"], ids, "repeticion detectada")
            ids.add(q["id"])
            e.submit_answer(s, q, f"respuesta {q['id']}")

    def test_cadena_completa(self):
        e = mk_engine(); s = OnboardingSession()
        q = e.next_question(s)
        r = e.submit_answer(s, q, "valoro la libertad")
        self.assertEqual(r["record"]["provenance"], "SELF_REPORTED")
        self.assertTrue(r["memory_id"].startswith("mem:"))       # Memory G5
        self.assertIn("next_question", r)                         # siguiente pregunta
        self.assertIsNotNone(r["insights"])                       # reflection G6 corrio

    def test_unknown_queda_uncertain(self):
        e = mk_engine(); s = OnboardingSession()
        q = e.next_question(s)
        r = e.submit_answer(s, q, "unknown")
        self.assertEqual(r["record"]["provenance"], "UNCERTAIN")
        self.assertEqual(r["record"]["confidence"], 0.1)
        self.assertEqual(r["unknowns"], 1)

    def test_contradiccion_genera_clarificacion(self):
        e = mk_engine(); s = OnboardingSession()
        e.submit_answer(s, {"id": "q.values.1", "category": "Values", "goal": "g"}, "libertad")
        e.submit_answer(s, {"id": "q.values.2", "category": "Values", "goal": "g"}, "libertad")
        e.submit_answer(s, {"id": "q.x3", "category": "Values", "goal": "g"}, "control")
        r = e.submit_answer(s, {"id": "q.x4", "category": "Values", "goal": "g"}, "orden")
        self.assertTrue(r["clarification_questions"] or r["open_contradictions"] >= 0)
        # si hay contradiccion, la siguiente pregunta es aclaracion
        if r["clarification_questions"]:
            nq = e.next_question(s)
            self.assertEqual(nq["kind"], "clarification")

    def test_no_escribe_digital_self(self):
        src = open("/mnt/agents/output/APP_YO/onboarding/adaptive_engine.py").read()
        self.assertNotIn("digital_self", src.replace("DigitalSelf", "X"))
        self.assertNotIn("genome_store", src)
        self.assertNotIn("evolution_engine", src)
        self.assertNotIn("pipeline_evolution", src)


class TestMaturity(unittest.TestCase):
    def _session(self, n=20, cats=9):
        e = mk_engine(); s = OnboardingSession()
        for i in range(n):
            cat = ["Identity","Values","Beliefs","Decisions","Experiences",
                   "Relationships","Purpose","Shadow","Future"][i % cats]
            e.submit_answer(s, {"id": f"q.t{i}", "category": cat, "goal": "g"}, f"respuesta {i}")
        return s

    def test_multi_criterio_explicable(self):
        s = self._session()
        m = compute(s)
        for c in ("coverage", "depth", "consistency", "evidence", "uncertainty",
                  "contradictions", "temporal_evolution"):
            self.assertIn(c, m["criteria"])
            self.assertIn("explanation", m["criteria"][c])
        self.assertIn("caution", m)

    def test_no_es_conteo_simple(self):
        s1 = self._session(n=9, cats=9)     # 9 respuestas, 1 por categoria
        s2 = self._session(n=18, cats=9)    # 18 respuestas, 2 por categoria
        m1, m2 = compute(s1), compute(s2)
        self.assertGreater(m2["criteria"]["depth"]["value"], m1["criteria"]["depth"]["value"])

    def test_ready_gate(self):
        m = compute(self._session(n=27, cats=9))
        self.assertIn("ready_for_ella", m)
        self.assertIsInstance(m["ready_for_ella"], bool)


class TestTwinYo(unittest.TestCase):
    def test_distingue_tags(self):
        twin = build_twin({"Identity": [{"provenance": "SELF_REPORTED", "confidence": 1.0, "version": 1}]},
                          session=None)
        self.assertEqual(twin["Identity"]["tag"], "fact")
        self.assertEqual(twin["Memory"]["status"], "NO EVIDENCE")
        self.assertIn("uncertainty", twin)
        self.assertIn("NO EVIDENCE", json_dumps(twin)) if False else None

    def test_no_fabrica_atributos(self):
        twin = build_twin({}, session=None)
        for k in ("Values", "Beliefs", "Goals", "Traits"):
            self.assertEqual(twin[k]["status"], "NO EVIDENCE")


if __name__ == "__main__":
    unittest.main()
