import sys, unittest, tempfile, os, json, hashlib
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/APP_YO/ELLA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from twin_contracts import (TwinToTwinContracts, yo_model_of_ella, relational_model,
    NamespaceViolation, ContractError, ACTION_RELATIONAL_UPDATE, IMPACT_RELATIONAL)
from authority import Authority
from identity import Identity
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
CODE = DailyCodeProvider(KEY).code(TODAY)


class TestContracts(unittest.TestCase):
    def test_invariante_tres_capas(self):
        ym = yo_model_of_ella({"x": 1})
        rm = relational_model(["confianza"])
        self.assertTrue(ym["not_ella_identity"])
        self.assertEqual(ym["namespace"], "YO")
        self.assertEqual(rm["namespace"], "RELATIONAL")
        self.assertNotEqual(ym["kind"], rm["kind"])
        self.assertNotEqual(ym["content_hash"], rm["content_hash"])

    def test_namespace_violation(self):
        c = TwinToTwinContracts(AUTH.did, TODAY)
        with self.assertRaises(NamespaceViolation):
            c.propose_relational_update({"not_ella_identity": False}, {})

    def test_propose_authorize_versioning_chain(self):
        from el_yo.evidence import EvidenceLedger
        tmp = tempfile.mkdtemp()
        c = TwinToTwinContracts(AUTH.did, TODAY, ledger=EvidenceLedger(os.path.join(tmp, "l.jsonl")),
                                clock=lambda: 7.0)
        ym = yo_model_of_ella({})
        p1 = c.propose_relational_update(ym, {"ctx": 1})
        a1 = c.authorize_relational_update(p1, Authority(AUTH, GATE, TODAY).authorize_action(
            ACTION_RELATIONAL_UPDATE, IMPACT_RELATIONAL, f"EJECUTA t2t {CODE}",
            content_hash=p1["content_hash"]))
        self.assertEqual(a1["approved_by"], AUTH.did)
        self.assertEqual(c.contract_version(), 1)
        # anti-replay: misma autorizacion sobre propuesta distinta -> rechazo
        ym2 = yo_model_of_ella({"otro": 2})
        p2 = c.propose_relational_update(ym2, {"ctx": 2})
        with self.assertRaises(ContractError):
            c.authorize_relational_update(p2, Authority(AUTH, GATE, TODAY).authorize_action(
                ACTION_RELATIONAL_UPDATE, IMPACT_RELATIONAL, f"EJECUTA t2t {CODE}",
                content_hash=p1["content_hash"]))   # hash de p1, no de p2
        self.assertTrue(c.ledger.verify())

    def test_sin_autoridad_paralela(self):
        src = open("/mnt/agents/output/APP_YO/ELLA/twin_contracts.py").read()
        self.assertIn("verify_authorization", src)
        self.assertNotIn("class AuthorizationGate", src)


if __name__ == "__main__":
    unittest.main()
