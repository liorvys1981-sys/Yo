import sys, unittest, tempfile, os, json
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from self_awareness import (CognitiveEvent, SelfAwarenessEngine, CongruenceAnalyzer,
    CapabilityMirror, SelfContrastEngine, UserDefinedCriterion, Metacognition,
    STAGES, CONGRUENCE_RESULTS, PROHIBITED_EVALUATIVE, ProhibitedEvaluation,
    ConsciousnessClaimError, SelfAwarenessError)
from interaction_to_cognition import (InteractionToCognitionEngine, RelationalModel,
    InteractionRecord, InformationLayer, InteractionError, NamespaceViolation,
    COGNITIVE_LENSES)

EV = dict(actor="YO", target="ELLA", session_id="s1", relationship_id="r1",
          event_type="interaction", content_reference="ref:1", context_reference="ctx:1",
          provenance="OBSERVED", confidence=0.8, evidence_ids=("e1",),
          temporal_validity=(1.0, 2.0), tenant_id="YO", owner_id="yo")


def mk_event(obs="PRESENT", hyp="PRESENT", **kw):
    base = dict(observation={"stage": obs, "statement": "no hubo respuesta en 48h"},
                perception={"stage": "ABSENT", "statement": ""},
                interpretation={"stage": "UNKNOWN", "statement": ""},
                hypothesis={"stage": hyp, "statement": "posible percepcion de rechazo"})
    base.update(kw)
    merged = {**EV, **base}
    return CognitiveEvent(event_id="ev:test", timestamp=100.0, **merged)


class TestCognitiveEvent(unittest.TestCase):
    def test_campos_y_hash(self):
        e = mk_event()
        for c in ("event_id","actor","target","session_id","relationship_id","timestamp",
                  "event_type","content_reference","context_reference","observation",
                  "perception","interpretation","hypothesis","provenance","confidence",
                  "evidence_ids","temporal_validity","content_hash","tenant_id","owner_id"):
            self.assertTrue(hasattr(e, c), c)
        self.assertEqual(len(e.content_hash), 64)

    def test_stages_validados(self):
        for s in STAGES:
            mk_event(obs=s)
        with self.assertRaises(SelfAwarenessError):
            mk_event(obs="INVENTADO")

    def test_distincion_evento_observacion(self):
        e = mk_event(obs="PRESENT", hyp="PRESENT")
        self.assertEqual(e.fact["stage"], "FACT")          # OBSERVED + PRESENT
        e2 = mk_event(provenance="INFERRED")
        self.assertEqual(e2.fact["stage"], "NOT_FACT")     # hipotesis nunca hecho

    def test_no_contenido_innecesario_ni_secrets(self):
        e = mk_event()
        payload = json.dumps(e.__dict__)
        self.assertNotIn("chain_of_thought", payload)
        self.assertNotIn("password", payload)


class TestCongruence(unittest.TestCase):
    def test_resultados_permitidos(self):
        c = CongruenceAnalyzer()
        self.assertEqual(c.analyze({"intention": "x", "action": "x"})["result"], "ALIGNED")
        r = c.analyze({"intention": "x", "action": "y"})
        self.assertIn(r["result"], CONGRUENCE_RESULTS)
        self.assertEqual(c.analyze({})["result"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(c.analyze({"a": "x"})["result"], "INSUFFICIENT_EVIDENCE")
        r2 = c.analyze({"v1": "x", "v2": "y"}, {"explains_divergence": True})
        self.assertEqual(r2["result"], "CONTEXT_EXPLAINS")

    def test_prohibido_evaluativo(self):
        for w in PROHIBITED_EVALUATIVE:
            self.assertNotIn(w, CONGRUENCE_RESULTS)


class TestCriteriaCapabilitiesContrast(unittest.TestCase):
    def test_criterio_solo_usuario(self):
        c = UserDefinedCriterion("c1", "important", "la familia importa", "USER")
        self.assertFalse(c.fundamental)
        self.assertIn("R1", c.to_proposal()["fundamental_route"])
        with self.assertRaises(SelfAwarenessError):
            UserDefinedCriterion("c2", "important", "x", "SYSTEM")
        with self.assertRaises(SelfAwarenessError):
            UserDefinedCriterion("c3", "moral", "x", "USER")

    def test_capability_mirror(self):
        m = CapabilityMirror()
        self.assertEqual(m.classify("paciencia", ("e",), 3, False, "OBSERVED", 0.8)["kind"],
                         "OBSERVED_CAPABILITY")
        self.assertEqual(m.classify("x", (), 0, False, "INFERRED", 0.3)["kind"],
                         "UNCERTAIN_CAPABILITY")
        self.assertEqual(m.classify("x", ("e",), 1, True, "SELF_REPORTED", 0.9)["kind"],
                         "USER_CONFIRMED_CAPABILITY")
        self.assertFalse(m.classify("x", ("e",), 5, False, "OBSERVED", 0.9)["is_identity"])

    def test_contrast_reglas(self):
        r = SelfContrastEngine().contrast(present={"v": 1}, desired={"v": 2})
        self.assertIn("DESIRED != REQUIRED", r["rules"])
        self.assertFalse(r["prescriptive"])
        self.assertTrue(r["informational"])


class TestMetacognitionAntiManipulation(unittest.TestCase):
    def test_preguntas_neutrales(self):
        q = Metacognition().questions_for(mk_event())
        self.assertGreaterEqual(len(q), 8)
        for w in ("deberias", "tienes que", "miedo"):
            self.assertFalse(any(w in x.lower() for x in q))

    def test_manipulacion_rechazada(self):
        m = Metacognition()
        with self.assertRaises(ProhibitedEvaluation):
            m.assert_neutral("deberias sentir culpa")
        m.assert_neutral("que observaste realmente?")

    def test_consciousness_boundary(self):
        m = Metacognition()
        with self.assertRaises(ConsciousnessClaimError):
            m.assert_no_consciousness_claim("YO SOY CONSCIENTE")
        with self.assertRaises(ConsciousnessClaimError):
            m.assert_no_consciousness_claim("ELLA tiene experiencia subjetiva")
        m.assert_no_consciousness_claim("soporto COGNITIVE SELF-REFLECTION y METACOGNITION")
        self.assertEqual(m.capability_name(), "METACOGNITION / SELF-MODELING / COGNITIVE AWARENESS SUPPORT")


class TestEngine(unittest.TestCase):
    def test_reflexion_no_concluye_identidad(self):
        eng = SelfAwarenessEngine(clock=lambda: 1.0)
        e = eng.record_event(event_id="e1", **EV,
            observation={"stage": "PRESENT", "statement": "no hubo respuesta"},
            perception={"stage": "PRESENT", "statement": "senti rechazo"},
            interpretation={"stage": "PRESENT", "statement": "no quiere hablar"},
            hypothesis={"stage": "PRESENT", "statement": "posible rechazo"})
        r = eng.reflection_for(e)
        self.assertEqual(r["identity_conclusion"], "NONE (forbidden without Evolution+R1)")
        self.assertIn("que observaste", r["metacognitive_questions"][0].lower())

    def test_patterns_no_son_hechos(self):
        eng = SelfAwarenessEngine(clock=lambda: 1.0)
        for i in range(3):
            eng.record_event(event_id=f"e{i}", **EV,
                observation={"stage": "PRESENT", "statement": "retraso en respuesta"},
                perception={"stage": "ABSENT", "statement": ""},
                interpretation={"stage": "UNKNOWN", "statement": ""},
                hypothesis={"stage": "ABSENT", "statement": ""})
        pats = eng.detect_patterns()
        self.assertTrue(pats)
        self.assertFalse(pats[0]["is_fact"])

    def test_evolution_proposal_route(self):
        eng = SelfAwarenessEngine(clock=lambda: 1.0)
        e = eng.record_event(event_id="e1", **EV,
            observation={"stage": "PRESENT", "statement": "x"},
            perception={"stage": "ABSENT", "statement": ""},
            interpretation={"stage": "UNKNOWN", "statement": ""},
            hypothesis={"stage": "PRESENT", "statement": "y"})
        p = eng.evolution_proposal(e)
        self.assertEqual(p["direct_mutation"], "PROHIBITED")


class TestInteractionToCognition(unittest.TestCase):
    def setUp(self):
        self.eng = InteractionToCognitionEngine(SelfAwarenessEngine(clock=lambda: 9.0),
                                                clock=lambda: 9.0)

    def test_pipeline_gates(self):
        low = self.eng.process_turn(interaction_id="i0", session_id="s", relationship_id="r",
            actor="YO", recipient="ELLA", content_reference="c", context_reference="x",
            statements=[], relevance="LOW")
        self.assertFalse(low["experience_created"])
        r = self.eng.process_turn(interaction_id="i1", session_id="s", relationship_id="r",
            actor="ELLA", recipient="YO", content_reference="c", context_reference="x",
            statements=[{"statement": "prefiero el te", "provenance": "USER_STATED"}],
            relevance="HIGH")
        self.assertTrue(r["experience_created"])
        rec = r["record"]
        self.assertEqual(len(rec.content_hash), 64)
        self.assertEqual(rec.user_stated_information[0]["layer"],
                         "ELLA_USER_STATED_INFORMATION")
        self.assertFalse(rec.user_stated_information[0]["is_identity_value"])
        self.assertIn("reflection", r)

    def test_informacion_clasificada(self):
        lay = InformationLayer().classify("prefiere silencio", "ELLA", "INFERRED")
        self.assertEqual(lay["namespace"], "ELLA_OBSERVATION")
        self.assertFalse(lay["is_identity_value"])

    def test_no_todo_turno_genera_todo(self):
        r = self.eng.process_turn(interaction_id="i2", session_id="s", relationship_id="r",
            actor="YO", recipient="ELLA", content_reference="c", context_reference="x",
            statements=[{"statement": "ok", "provenance": "USER_STATED"}], relevance="MEDIUM")
        self.assertTrue(r["experience_created"])
        # MEDIUM: sin hipotesis fuertes, candidatos = solo observaciones
        self.assertIsInstance(r["pattern_candidates"], list)


class TestRelationalModel(unittest.TestCase):
    def _rec(self, iid, ts):
        return InteractionRecord(interaction_id=iid, session_id="s", relationship_id="r1",
            actor="YO", recipient="ELLA", timestamp=ts, content_reference="c",
            context_reference="x", observations=[], user_stated_information=[],
            system_observations=[], hypotheses=[], confidence=0.5, provenance="OBSERVED",
            evidence_ids=("e",), tenant_id="YO", owner_id="yo")

    def test_modelo_sin_autoridad(self):
        rm = RelationalModel("r1")
        self.assertFalse(rm.has_authority_over_identity)
        rm.record(self._rec("i1", 1.0))
        other = self._rec("i2", 2.0)
        other.relationship_id = "OTRA"
        with self.assertRaises(InteractionError):
            rm.record(other)

    def test_reconstruccion_temporal(self):
        rm = RelationalModel("r1")
        rm.record(self._rec("i1", 1.0)); rm.record(self._rec("i2", 5.0))
        snap = rm.reconstruct(3.0)
        self.assertEqual(snap["interactions"], 1)     # solo i1 (t<=3)
        self.assertEqual(len(rm.interactions), 2)     # historial intacto


class TestLenses(unittest.TestCase):
    def test_formato_y_niveles(self):
        self.assertEqual(len(COGNITIVE_LENSES), 9)
        for l in COGNITIVE_LENSES:
            self.assertTrue(all(k in l for k in ("name", "principle", "function",
                                                 "component", "evidence")))
        grin = [l for l in COGNITIVE_LENSES if l["name"] == "Grinberg"][0]
        self.assertIn("SPECULATIVE", grin["evidence"])
        ton = [l for l in COGNITIVE_LENSES if l["name"] == "Tononi"][0]
        self.assertIn("sin claim de conciencia", ton["evidence"])
