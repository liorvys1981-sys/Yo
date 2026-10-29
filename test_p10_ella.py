import os, sys, tempfile, unittest, json, hashlib
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/APP_YO/ELLA')
sys.path.insert(0, '/mnt/agents/output/APP_YO/onboarding')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from ella_genesis import EllaGenesis, ACTION_GENESIS, ACTION_PROPOSAL, IMPACT_GENESIS, IMPACT_PROPOSAL
from ella_activation import (EllaActivation, UnauthorizedActivation, ProposalIntegrityError,
    OriginIntegrityError, DoubleActivation, NamespaceBindingError, ExpiredAuthorization)
from build_ella import construir_ella, BuildEllaError
from ella_foundation import EllaFoundation, EllaOnboarding, yo_to_ella_provenance, FoundationError
from maturity import compute
from adaptive_engine import OnboardingSession
from cognitive_twin_yo import build_twin
from authority import Authority, ChangeAuthorization
from identity import Identity
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from el_yo.constitution import Denied

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, second_key_present=True)
CODE = DailyCodeProvider(KEY).code(TODAY)
_canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
_chash = lambda o: hashlib.sha256(_canon(o)).hexdigest()


def authz(action, impact, content):
    return Authority(AUTH, GATE, TODAY).authorize_action(
        action, impact, f"EJECUTA ella-p10 {CODE}", content_hash=_chash(content))


def mk_genesis(tmp=None):
    from el_yo.evidence import EvidenceLedger
    tmp = tmp or tempfile.mkdtemp()
    return tmp, EllaGenesis(tmp, AUTH.did, TODAY,
                            ledger=EvidenceLedger(os.path.join(tmp, "ledger.jsonl")),
                            clock=lambda: 500.0)


def full_genesis(tmp=None):
    tmp, g = mk_genesis(tmp)
    decl = "Creo a ELLA, entidad independiente y soberana."
    g.genesis(decl, authz(ACTION_GENESIS, IMPACT_GENESIS, decl))
    content = {"nombre": "ELLA", "naturaleza": "entidad independiente"}
    g.propose_identity(content, authz(ACTION_PROPOSAL, IMPACT_PROPOSAL, content))
    return tmp, g


class TestBuildElla(unittest.TestCase):
    def _maturity_ready(self):
        s = OnboardingSession()
        cats = ["Identity","Values","Beliefs","Decisions","Experiences",
                "Relationships","Purpose","Shadow","Future"]
        for i in range(27):
            s.answers.append({"question_id": f"q{i}", "category": cats[i % 9],
                              "answer": f"r{i}", "ts": 1000.0 + i * 90000,
                              "provenance": "SELF_REPORTED", "confidence": 0.9,
                              "evidence": (f"e{i}",)})
        return compute(s)

    def test_model_no_es_identidad(self):
        m = self._maturity_ready()
        twin = build_twin({}, session=None)
        model = construir_ella(twin, m, imagination={"forma": "luz"},
                               visual_preferences={"estilo": "calido"})
        self.assertTrue(model["not_ella_identity"])
        self.assertEqual(model["namespace"], "YO")
        self.assertEqual(model["provenance_subtype"], "YO_MODEL_OF_ELLA")
        self.assertEqual(model["imagination"]["provenance"], "IMAGINED")
        self.assertEqual(model["visual_preferences"]["provenance"], "SELF_REPORTED")

    def test_gate_de_madurez(self):
        with self.assertRaises(BuildEllaError):
            construir_ella({}, {"ready_for_ella": False, "ready_explanation": "x"})


class TestActivation(unittest.TestCase):
    def test_legitima(self):
        tmp, g = full_genesis()
        act = EllaActivation(g)
        proposal = g.load_proposal(today=TODAY)
        a = authz("ELLA-identity-activation", "destructiva",
                  {k: v for k, v in proposal.items() if k != "content_hash"})
        active = act.activate(a)
        self.assertEqual(active["identity_status"], "ACTIVE")
        self.assertEqual(active["activated_by"], AUTH.did)
        self.assertEqual(active["autonomy"], "DISABLED")
        self.assertEqual(active["other_entities"]["Values"], "PENDING")
        scaffold = act.ella_digital_self_scaffold()
        self.assertEqual(scaffold["entities"]["Identity"]["status"], "ACTIVE")
        self.assertEqual(scaffold["entities"]["Beliefs"]["status"], "PENDING")
        self.assertTrue(g.ledger.verify())

    def test_doble_activacion(self):
        tmp, g = full_genesis()
        act = EllaActivation(g)
        proposal = g.load_proposal(today=TODAY)
        a = authz("ELLA-identity-activation", "destructiva",
                  {k: v for k, v in proposal.items() if k != "content_hash"})
        act.activate(a)
        with self.assertRaises(DoubleActivation):
            act.activate(a)

    def test_did_falso(self):
        tmp, g = full_genesis()
        act = EllaActivation(g)
        fake = Identity(seed=b"f" * 32)
        proposal = g.load_proposal(today=TODAY)
        payload = {"kind": "ELLA-identity-activation", "did": fake.did, "day": TODAY, "nonce": "c" * 16}
        bad = ChangeAuthorization("ELLA-identity-activation", fake.did, TODAY, "c" * 16,
                                  fake.sign(_canon(payload)))
        with self.assertRaises(UnauthorizedActivation):
            act.activate(bad)

    def test_proposal_alterada(self):
        tmp, g = full_genesis()
        pth = os.path.join(tmp, "ELLA", "ELLA_IDENTITY_PROPOSAL.json")
        d = json.load(open(pth)); d["content"]["nombre"] = "HACKEADA"
        json.dump(d, open(pth, "w"))
        act = EllaActivation(g)
        with self.assertRaises((ProposalIntegrityError, UnauthorizedActivation)):
            act.activate(authz("ELLA-identity-activation", "destructiva", d))

    def test_expirada(self):
        tmp, g = full_genesis()
        act = EllaActivation(g)
        proposal = g.load_proposal(today=TODAY)
        gate6 = AuthorizationGate(DailyCodeProvider(KEY), "2026-10-06", True)
        a = Authority(AUTH, gate6, "2026-10-06").authorize_action(
            "ELLA-identity-activation", "destructiva",
            f"EJECUTA ella-p10 {DailyCodeProvider(KEY).code('2026-10-06')}",
            content_hash=_chash({k: v for k, v in proposal.items() if k != "content_hash"}))
        with self.assertRaises(ExpiredAuthorization):
            act.activate(a)

    def test_string_libre_rechazado(self):
        tmp, g = full_genesis()
        act = EllaActivation(g)
        with self.assertRaises(UnauthorizedActivation):
            act.activate("authorized=True")
        with self.assertRaises(UnauthorizedActivation):
            act.activate(None)


class TestFoundation(unittest.TestCase):
    def test_memory_isolation(self):
        tmp, g = full_genesis()
        f = EllaFoundation(tmp)
        f.store_experience({"domain": "ella", "key": "k1"}, "SELF_REPORTED", 0.8, ("e",), "src")
        # el store de YO no ve archivos de ELLA (roots disjuntos)
        yo_store_files = []
        for dirpath, _, files in os.walk(tmp):
            if "ELLA" not in dirpath and "memory" in dirpath:
                yo_store_files.extend(files)
        ella_mem = f.memory.query("ELLA")
        self.assertEqual(len(ella_mem), 1)
        self.assertEqual(f.TENANT, "ELLA")

    def test_reflection_insights_propios(self):
        f = EllaFoundation(tempfile.mkdtemp())
        for i in range(3):
            f.store_experience({"domain": "ella", "key": "mismo"},
                               "OBSERVED", 0.9, (f"e{i}",), "src")
        ins = f.reflect()
        self.assertTrue(any(i.type == "PATTERN" for i in ins))

    def test_seed_desde_yo_etiquetado(self):
        f = EllaFoundation(tempfile.mkdtemp())
        onb = EllaOnboarding(f)
        seeded = onb.seed_from_yo(
            [{"id": "m1", "key": "k", "content": {"answer": "valoro libertad"},
              "provenance": "SELF_REPORTED", "confidence": 0.9, "evidence": ("e",)}],
            yo_ref="yo-mem:abc")
        self.assertEqual(len(seeded), 1)
        rec = f.memory.load("ELLA", seeded[0])
        self.assertTrue(rec["evidence"] and "yo-ref" in str(rec["evidence"]))

    def test_twin_foundation_scaffold(self):
        tmp, g = full_genesis()
        act = EllaActivation(g)
        proposal = g.load_proposal(today=TODAY)
        act.activate(authz("ELLA-identity-activation", "destructiva",
                           {k: v for k, v in proposal.items() if k != "content_hash"}))
        f = EllaFoundation(tmp)
        twin = f.twin_foundation(act.ella_digital_self_scaffold())
        self.assertEqual(twin["namespace"], "ELLA")
        self.assertEqual(twin["autonomy"], "DISABLED")
        self.assertEqual(twin["DigitalSelf"]["entities"]["Identity"]["status"], "ACTIVE")

    def test_no_autonomy_api(self):
        src = open("/mnt/agents/output/APP_YO/ELLA/ella_foundation.py").read()
        for banned in ("activate_autonomy", "enable_agents", "spawn_agent", "ollama"):
            self.assertNotIn(banned, src)


if __name__ == "__main__":
    unittest.main()
