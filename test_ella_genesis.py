import os, sys, tempfile, unittest, json, hashlib
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/APP_YO/ELLA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from ella_genesis import (EllaGenesis, EllaGenesisError, CrossNamespaceViolation,
    GenesisContractViolation, UnauthorizedGenesis, record_yo_model_of_ella,
    NAMESPACE_ELLA, ACTION_GENESIS, ACTION_PROPOSAL, IMPACT_GENESIS, IMPACT_PROPOSAL)
from authority import Authority, ChangeAuthorization
from identity import Identity
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY = b"g" * 32
TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, second_key_present=True)
CODE = DailyCodeProvider(KEY).code(TODAY)
SOV = AUTH.did   # soberano verificable (R2)


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
def _chash(o): return hashlib.sha256(_canon(o)).hexdigest()


def auth_genesis(declaration):
    return AUTH.sign, Authority(AUTH, GATE, TODAY).authorize_action(
        ACTION_GENESIS, IMPACT_GENESIS, f"EJECUTA ella-genesis {CODE}",
        content_hash=_chash(declaration))


def auth_proposal(content):
    return Authority(AUTH, GATE, TODAY).authorize_action(
        ACTION_PROPOSAL, IMPACT_PROPOSAL, f"EJECUTA ella-propuesta {CODE}",
        content_hash=_chash(content))


def mk(tmp=None):
    ledger = None
    if tmp:
        from el_yo.evidence import EvidenceLedger
        ledger = EvidenceLedger(os.path.join(tmp, "ledger.jsonl"))
    return EllaGenesis(tmp or tempfile.mkdtemp(), AUTH.did, TODAY,
                       ledger=ledger, clock=lambda: 100.0)


class TestGenesisAutorizado(unittest.TestCase):
    def test_origin_record_created(self):
        g = mk()
        _, authz = auth_genesis("Yo declaro la creacion de ELLA.")
        o = g.genesis("Yo declaro la creacion de ELLA.", authz)
        self.assertEqual(o["namespace"], "ELLA")
        self.assertEqual(o["created_by"], SOV)
        self.assertEqual(o["authorized_action"], "ELLA-genesis")
        self.assertEqual(o["valid_day"], TODAY)
        self.assertEqual(o["autonomy"], "DISABLED")
        self.assertEqual(len(o["content_hash"]), 64)

    def test_origin_persisted_and_verifiable(self):
        tmp = tempfile.mkdtemp()
        g = mk(tmp)
        decl = "declaracion"
        _, authz = auth_genesis(decl)
        g.genesis(decl, authz)
        o2 = g.load_origin(today=TODAY)
        self.assertEqual(o2["created_by"], SOV)

    def test_origin_tamper_detected(self):
        tmp = tempfile.mkdtemp()
        g = mk(tmp)
        decl = "declaracion"
        _, authz = auth_genesis(decl)
        g.genesis(decl, authz)
        p = os.path.join(tmp, "ELLA", "ELLA_ORIGIN.json")
        d = json.load(open(p)); d["autonomy"] = "ENABLED"
        json.dump(d, open(p, "w"))
        with self.assertRaises(GenesisContractViolation):
            g.load_origin(today=TODAY)

    def test_genesis_sin_autorizacion_rechazada(self):
        g = mk()
        with self.assertRaises(UnauthorizedGenesis):
            g.genesis("intento sin autoridad", None)

    def test_genesis_audit_en_ledger(self):
        tmp = tempfile.mkdtemp()
        g = mk(tmp)
        decl = "declaracion"
        _, authz = auth_genesis(decl)
        g.genesis(decl, authz)
        evs = [json.loads(l)["event"] for l in open(os.path.join(tmp, "ledger.jsonl"))]
        self.assertTrue(any(e.get("event") == "genesis" and e.get("by") == SOV for e in evs))


class TestIdentityProposalV4(unittest.TestCase):
    def test_proposal_nace_proposed_no_activa(self):
        g = mk()
        content = {"nombre": "ELLA"}
        authz = auth_proposal(content)
        p = g.propose_identity(content, authz)
        self.assertEqual(p["status"], "PROPOSED")
        self.assertEqual(p["authorized_by"], SOV)

    def test_load_proposal_verifica_integridad(self):
        tmp = tempfile.mkdtemp()
        g = mk(tmp)
        content = {"nombre": "ELLA"}
        g.propose_identity(content, auth_proposal(content))
        p2 = g.load_proposal(today=TODAY)
        self.assertEqual(p2["content"], content)
        pth = os.path.join(tmp, "ELLA", "ELLA_IDENTITY_PROPOSAL.json")
        d = json.load(open(pth)); d["status"] = "ACTIVE"
        json.dump(d, open(pth, "w"))
        with self.assertRaises(GenesisContractViolation):
            g.load_proposal(today=TODAY)


class TestSeparacionYoEllaV2V3(unittest.TestCase):
    def test_cross_namespace_denegado(self):
        g = mk()
        with self.assertRaises(CrossNamespaceViolation):
            g.enforce_separation("YO", tempfile.mkdtemp())

    def test_ruta_ajena_denegada(self):
        tmp = tempfile.mkdtemp()
        g = mk(tmp)
        with self.assertRaises(CrossNamespaceViolation):
            g.enforce_separation("ELLA", tempfile.mkdtemp())   # otra ruta

    def test_modelo_rechaza_destino_ella(self):
        with self.assertRaises(CrossNamespaceViolation):
            record_yo_model_of_ella({"namespace": "ELLA"}, {"obs": "x"})

    def test_yo_model_ok_en_yo(self):
        yo = {}
        m = record_yo_model_of_ella(yo, {"nota": "curiosa"})
        self.assertEqual(m["provenance_subtype"], "YO_MODEL_OF_ELLA")
        self.assertTrue(m["not_ella_identity"])

    def test_elra_no_importa_digital_self(self):
        src = open("/mnt/agents/output/APP_YO/ELLA/ella_genesis.py").read()
        self.assertNotIn("import digital_self", src)

    def test_runtime_separation_en_genesis(self):
        g = mk()
        g.root = "/tmp/forzado"   # simular drift de ruta -> runtime check dispara
        decl = "x"
        _, authz = auth_genesis(decl)
        with self.assertRaises(CrossNamespaceViolation):
            g.genesis(decl, authz)


if __name__ == "__main__":
    unittest.main()
