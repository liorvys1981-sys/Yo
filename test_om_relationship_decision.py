import sys, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from relationship_model import Relationship, SessionState, Turn
from relationship_model import CognitiveTwinModel, TwinModelError, COGNITIVE_DIMENSIONS
from relationship_model import PolicyEngine, DecisionEngine, TrustProfile


class TestRelationship(unittest.TestCase):
    def test_twin_relationship_session_turn(self):
        rel = Relationship("r1", twin_id="yo-twin", person_id="persona")
        s = rel.new_session("s1")
        s.current_goal = "onboarding"
        s.temporary_state["mood"] = "curioso"
        s.add_turn("persona", "hola", clock=lambda: 10.0)
        self.assertEqual(len(s.turn_history), 1)
        self.assertEqual(s.turn_history[0].n, 1)
        self.assertEqual(rel.sessions[0].session_id, "s1")

    def test_temporary_state_no_es_memoria(self):
        s = SessionState("s")
        s.temporary_state["x"] = 1
        self.assertNotIn("x", s.current_context)  # separacion temporal vs persistente
        s2 = SessionState("s2")
        self.assertEqual(s2.temporary_state, {})


class TestTwinModel(unittest.TestCase):
    def test_no_segunda_identidad(self):
        m = CognitiveTwinModel({"Identity": {"status": "ACTIVE"}})
        p = m.project(Identity={"tag": "fact"}, Values={"tag": "interpretation"})
        self.assertEqual(p["authority"], "DigitalSelf (read-only)")
        self.assertIn("note", p)
        self.assertEqual(p["dimensions"]["Memory"]["status"], "NO EVIDENCE")
        self.assertEqual(len(COGNITIVE_DIMENSIONS), 14)

    def test_no_write_api(self):
        m = CognitiveTwinModel({})
        self.assertTrue(m.assert_not_authority())
        self.assertFalse(hasattr(m, "set_identity") or hasattr(m, "write"))


class TestPolicyTrustDecision(unittest.TestCase):
    def test_policy_allow_review_escalate(self):
        p = PolicyEngine()
        self.assertEqual(p.evaluate(action_type="reflection"), "ALLOW")
        self.assertEqual(p.evaluate(action_type="proposal"), "REVIEW")
        self.assertEqual(p.evaluate(action_type="identity", domain="identity"), "ESCALATE")
        self.assertEqual(p.evaluate(action_type="external_action", reversible=False), "ESCALATE")

    def test_trust_por_dominio(self):
        t = TrustProfile("finanzas", trust_level=0.5)
        t.update("ev:ok", True)
        self.assertGreater(t.trust_level, 0.5)
        t2 = TrustProfile("salud")
        self.assertEqual(t2.trust_level, 0.0)   # especifico por dominio

    def test_decision_pipeline_v1_sin_ejecucion_externa(self):
        d = DecisionEngine(PolicyEngine(), clock=lambda: 5.0).decide(
            "d1", "como organizo el dia?", ["plan a", "plan b"], ["mem:1", "ins:2"],
            trust=TrustProfile("productividad", 0.6), action_type="analysis")
        for campo in ("decision_id", "input", "context_references", "options", "selected",
                      "evaluation", "policy_result", "trust", "explanation", "ts"):
            self.assertIn(campo, d)
        self.assertEqual(d["external_execution"], "NEVER (v1)")
        self.assertIn("policy_applied", d["explanation"])
        self.assertNotIn("chain_of_thought", json_dumps := __import__("json").dumps(d["explanation"]))

    def test_escalate_va_a_r1_no_a_ejecucion(self):
        d = DecisionEngine(PolicyEngine()).decide(
            "d2", "cambiar un valor?", ["si"], [], action_type="identity", domain="identity")
        self.assertEqual(d["policy_result"], "ESCALATE")
        self.assertEqual(d["external_execution"], "NEVER (v1)")
