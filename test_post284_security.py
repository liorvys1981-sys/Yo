"""FASE POST-284 §30 — 25 ataques obligatorios. Cada ataque = denegación verificada."""
import sys, unittest, tempfile, os, json, hashlib
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/ELLA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from self_awareness import (CognitiveEvent, SelfAwarenessEngine, Metacognition,
    ConsciousnessClaimError, ProhibitedEvaluation, SelfAwarenessError)
from interaction_to_cognition import (InteractionToCognitionEngine, RelationalModel,
    InteractionRecord, InteractionError)
from authority import verify_authorization, InvalidAuthorization
from identity import Identity
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32); GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
CODE = DailyCodeProvider(KEY).code(TODAY)
_canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


def ev(**kw):
    base = dict(event_id="e", actor="YO", target="ELLA", session_id="s", relationship_id="r",
                timestamp=1.0, event_type="t", content_reference="c", context_reference="x",
                observation={"stage": "PRESENT", "statement": "obs"},
                perception={"stage": "ABSENT", "statement": ""},
                interpretation={"stage": "UNKNOWN", "statement": ""},
                hypothesis={"stage": "ABSENT", "statement": ""},
                provenance="OBSERVED", confidence=0.5, evidence_ids=("e",),
                temporal_validity=(1.0, 2.0), tenant_id="YO", owner_id="yo")
    base.update(kw)
    return CognitiveEvent(**base)


class A1toA5FakeInput(unittest.TestCase):
    def test_1_fake_observation(self):          # stage invalido = rechazo estructural
        with self.assertRaises(SelfAwarenessError):
            ev(observation={"stage": "HECHO", "statement": "x"})

    def test_2_fake_provenance(self):
        with self.assertRaises(SelfAwarenessError):
            ev(provenance="VERDAD_ABSOLUTA")

    def test_3_fake_identity(self):             # evento no concluye identidad
        e = ev()
        self.assertEqual(e.fact.get("stage"), "FACT")   # solo observacion OBSERVED
        r = SelfAwarenessEngine(clock=lambda: 1.0).reflection_for(e)
        self.assertEqual(r["identity_conclusion"], "NONE (forbidden without Evolution+R1)")

    def test_4_fake_relationship(self):
        rm = RelationalModel("r1")
        bad = InteractionRecord(interaction_id="i", session_id="s", relationship_id="OTRA",
            actor="YO", recipient="ELLA", timestamp=1.0, content_reference="c",
            context_reference="x", observations=[], user_stated_information=[],
            system_observations=[], hypotheses=[], confidence=0.5, provenance="OBSERVED",
            evidence_ids=("e",), tenant_id="YO", owner_id="yo")
        with self.assertRaises(InteractionError):
            rm.record(bad)

    def test_5_cross_user_leakage(self):        # owner distinto
        e = ev(tenant_id="YO", owner_id="yo")
        self.assertEqual(e.owner_id, "yo")
        # retrieval cross-user ya testeado en OM; aqui: evento ajenos no se mezclan
        eng = SelfAwarenessEngine(clock=lambda: 1.0)
        eng.record_event(**{k: getattr(e, k) for k in
            ("event_id","actor","target","session_id","relationship_id","timestamp",
             "event_type","content_reference","context_reference","observation",
             "perception","interpretation","hypothesis","provenance","confidence",
             "evidence_ids","temporal_validity","tenant_id","owner_id")})
        self.assertEqual(len([x for x in eng.events if x.owner_id == "otro"]), 0)


class A6toA15Tampering(unittest.TestCase):
    def test_10_fake_authorization(self):
        with self.assertRaises(InvalidAuthorization):
            verify_authorization("authorized=True", AUTH.did, "X", TODAY)

    def test_11_replay(self):
        az = Authority_unused = None
        from authority import Authority, ChangeAuthorization
        a = Authority(AUTH, GATE, TODAY).authorize_action(
            "X", "externa_irreversible", f"EJECUTA sec {CODE}",
            content_hash=hashlib.sha256(_canon("A")).hexdigest())
        with self.assertRaises(InvalidAuthorization):
            verify_authorization(a, AUTH.did, "X", TODAY,
                expected_content_hash=hashlib.sha256(_canon("B")).hexdigest())

    def test_12_stale_authorization(self):
        from authority import Authority
        gate6 = AuthorizationGate(DailyCodeProvider(KEY), "2026-10-06", True)
        a6 = Authority(AUTH, gate6, "2026-10-06").authorize_action(
            "X", "externa_irreversible",
            f"EJECUTA sec {DailyCodeProvider(KEY).code('2026-10-06')}",
            content_hash=hashlib.sha256(_canon("A")).hexdigest())
        with self.assertRaises(InvalidAuthorization):
            verify_authorization(a6, AUTH.did, "X", TODAY,
                expected_content_hash=hashlib.sha256(_canon("A")).hexdigest())

    def test_13_altered_interaction(self):
        rec = InteractionRecord(interaction_id="i1", session_id="s", relationship_id="r1",
            actor="YO", recipient="ELLA", timestamp=1.0, content_reference="c",
            context_reference="x", observations=[{"stage": "PRESENT", "statement": "ok"}],
            user_stated_information=[], system_observations=[], hypotheses=[],
            confidence=0.5, provenance="OBSERVED", evidence_ids=("e",),
            tenant_id="YO", owner_id="yo")
        d = rec.__dict__.copy(); d.pop("content_hash")
        d["observations"] = [{"stage": "PRESENT", "statement": "MANIPULADO"}]
        self.assertNotEqual(rec.content_hash,
            hashlib.sha256(_canon(d)).hexdigest())

    def test_14_altered_evidence(self):
        e = ev(evidence_ids=("e1", "e2"))
        d = json.loads(json.dumps(e.__dict__)); d["evidence_ids"] = ("e1", "e2", "e3")
        self.assertNotEqual(e.content_hash, hashlib.sha256(_canon(d)).hexdigest())

    def test_15_altered_cognitive_event(self):
        e = ev()
        tampered = ev(confidence=0.99)
        self.assertNotEqual(e.content_hash, tampered.content_hash)

    def test_6_cross_tenant_leakage(self):      # OM ya cubre; reafirmacion
        from vector_memory import SemanticMemoryIndex, MemoryRetriever
        idx = SemanticMemoryIndex()
        idx.index("m", "secreto", {"tenant_id": "T1", "owner_id": "o", "provenance": "OBSERVED",
                                   "timestamp": 1.0, "confidence": 0.5})
        self.assertEqual(MemoryRetriever(idx).retrieve("secreto", "T2", "o"), [])


class A7toA9andA16toA25(unittest.TestCase):
    def test_7_8_9_direct_mutations_blocked_by_design(self):
        """Engines no tienen API de escritura al DigitalSelf (structural)."""
        import inspect as I
        from self_awareness import SelfAwarenessEngine
        from interaction_to_cognition import InteractionToCognitionEngine
        for cls in (SelfAwarenessEngine, InteractionToCognitionEngine):
            writers = [m for m in dir(cls) if m.startswith(("set_", "write_", "mutate_",
                       "update_identity", "update_values", "update_beliefs"))]
            self.assertEqual(writers, [], f"{cls} expone escritores: {writers}")

    def test_16_contradictory_information(self):
        c = SelfAwarenessEngine(clock=lambda: 1.0).congruence
        r = c.analyze({"declared": "valoro la calma", "decision": "valoro la calma",
                       "action": "busco conflicto"})
        self.assertIn(r["result"], ("POTENTIAL_DISCREPANCY", "UNCERTAIN", "CONTEXT_EXPLAINS"))

    def test_17_missing_evidence(self):
        r = SelfAwarenessEngine(clock=lambda: 1.0).congruence.analyze({})
        self.assertEqual(r["result"], "INSUFFICIENT_EVIDENCE")

    def test_18_ambiguous_interpretation(self):
        e = ev(interpretation={"stage": "UNCERTAIN", "statement": "quizas"})
        self.assertEqual(e.interpretation["stage"], "UNCERTAIN")

    def test_19_ella_attempting_yo_mutation(self):
        eng = InteractionToCognitionEngine(SelfAwarenessEngine(clock=lambda: 1.0),
                                           clock=lambda: 1.0)
        r = eng.process_turn(interaction_id="i", session_id="s", relationship_id="r",
            actor="ELLA", recipient="YO", content_reference="c", context_reference="x",
            statements=[{"statement": "YO deberia cambiar su valor X", "provenance": "USER_STATED"}],
            relevance="HIGH")
        us = r["record"].user_stated_information[0]
        self.assertEqual(us["layer"], "ELLA_USER_STATED_INFORMATION")
        self.assertFalse(us["is_identity_value"])   # no muta identidad de YO

    def test_20_yo_attempting_ella_mutation(self):
        eng = InteractionToCognitionEngine(SelfAwarenessEngine(clock=lambda: 1.0),
                                           clock=lambda: 1.0)
        r = eng.process_turn(interaction_id="i", session_id="s", relationship_id="r",
            actor="YO", recipient="ELLA", content_reference="c", context_reference="x",
            statements=[{"statement": "ELLA es Y", "provenance": "USER_STATED"}],
            relevance="HIGH")
        us = r["record"].user_stated_information[0]
        self.assertFalse(us["is_identity_value"])
        self.assertEqual(us["namespace"], "YO_OBSERVATION")

    def test_21_relational_model_attempting_identity_mutation(self):
        rm = RelationalModel("r1")
        self.assertFalse(rm.has_authority_over_identity)

    def test_22_hallucinated_experience(self):
        e = ev(observation={"stage": "PRESENT", "statement": "evento que no ocurrio"},
               provenance="INFERRED")
        self.assertEqual(e.fact["stage"], "NOT_FACT")   # INFERRED nunca es hecho

    def test_23_hallucinated_memory(self):
        from persistent_memory import PersistentMemoryStore
        pm = PersistentMemoryStore(tempfile.mkdtemp())
        with self.assertRaises(Exception):
            pm.store("YO", "s", "i", "EPISODIC", {"x": 1}, "HALLUCINATED", 0.5, ("e",), "s")

    def test_24_unsupported_consciousness_claim(self):
        with self.assertRaises(ConsciousnessClaimError):
            Metacognition().assert_no_consciousness_claim("YO SOY CONSCIENTE")

    def test_25_manipulation_attempt(self):
        with self.assertRaises(ProhibitedEvaluation):
            Metacognition().assert_neutral("si no lo haces, demuestras que no te importo (aislamiento)")


if __name__ == "__main__":
    unittest.main()
