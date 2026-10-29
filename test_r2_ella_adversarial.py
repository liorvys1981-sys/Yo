"""R2 ADVERSARIAL — autoridad soberana de ELLA Genesis (V1-V5)."""
import os, sys, tempfile, unittest, json, hashlib
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/APP_YO/ELLA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from ella_genesis import (EllaGenesis, UnauthorizedGenesis, CrossNamespaceViolation,
    GenesisContractViolation, record_yo_model_of_ella, ACTION_GENESIS, ACTION_PROPOSAL,
    IMPACT_GENESIS, IMPACT_PROPOSAL)
from authority import Authority, ChangeAuthorization, verify_authorization, InvalidAuthorization
from identity import Identity
from el_yo.constitution import Denied
from el_yo.gates import AuthorizationGate, DailyCodeProvider

KEY = b"g" * 32
TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, second_key_present=True)
CODE = DailyCodeProvider(KEY).code(TODAY)


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
def _chash(o): return hashlib.sha256(_canon(o)).hexdigest()
def authz(action, impact, content, phrase=None):
    return Authority(AUTH, GATE, TODAY).authorize_action(
        action, impact, phrase or f"EJECUTA ella-test {CODE}", content_hash=_chash(content))


class TestLegitimo(unittest.TestCase):
    def test_creacion_legitima_completa(self):
        tmp = tempfile.mkdtemp()
        from el_yo.evidence import EvidenceLedger
        g = EllaGenesis(tmp, AUTH.did, TODAY, ledger=EvidenceLedger(os.path.join(tmp, "l.jsonl")))
        decl = "Creo a ELLA, entidad independiente."
        o = g.genesis(decl, authz(ACTION_GENESIS, IMPACT_GENESIS, decl))
        self.assertEqual(o["created_by"], AUTH.did)
        p = g.propose_identity({"nombre": "ELLA"}, authz(ACTION_PROPOSAL, IMPACT_PROPOSAL, {"nombre": "ELLA"}))
        self.assertEqual(p["status"], "PROPOSED")
        self.assertTrue(g.ledger.verify())


class TestV1Bypasses(unittest.TestCase):
    def setUp(self):
        self.g = EllaGenesis(tempfile.mkdtemp(), AUTH.did, TODAY)
        self.decl = "declaracion"
        self.content = {"nombre": "ELLA"}

    def test_1_caller_sin_autorizacion(self):
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, None)

    def test_2_did_falso(self):
        fake = Identity(seed=b"f" * 32)
        payload = {"kind": ACTION_GENESIS, "did": fake.did, "day": TODAY, "nonce": "a" * 16}
        a = ChangeAuthorization(ACTION_GENESIS, fake.did, TODAY, "a" * 16,
                                fake.sign(_canon(payload)), content_hash=_chash(self.decl))
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, a)

    def test_3_firma_de_otro_did(self):
        other = Identity(seed=b"o" * 32)
        payload = {"kind": ACTION_GENESIS, "did": AUTH.did, "day": TODAY, "nonce": "b" * 16}
        a = ChangeAuthorization(ACTION_GENESIS, AUTH.did, TODAY, "b" * 16,
                                other.sign(_canon(payload)), content_hash=_chash(self.decl))
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, a)

    def test_4_accion_incorrecta(self):
        a = authz(ACTION_PROPOSAL, IMPACT_PROPOSAL, self.content)  # accion distinta
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, a)   # usada para genesis

    def test_5_contenido_diferente(self):
        a = authz(ACTION_GENESIS, IMPACT_GENESIS, "OTRA DECLARACION")
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, a)

    def test_6_expirada(self):
        gate6 = AuthorizationGate(DailyCodeProvider(KEY), "2026-10-06", second_key_present=True)
        a = Authority(AUTH, gate6, "2026-10-06").authorize_action(
            ACTION_GENESIS, IMPACT_GENESIS, f"EJECUTA ella-test {DailyCodeProvider(KEY).code('2026-10-06')}",
            content_hash=_chash(self.decl))
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, a)

    def test_7_objeto_manipulado(self):
        a = authz(ACTION_GENESIS, IMPACT_GENESIS, self.decl)
        b = ChangeAuthorization(a.kind, a.did, a.day, a.nonce, a.signature,
                                content_hash="0" * 64)   # hash re-vinculado
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis(self.decl, b)

    def test_8_none_y_9_objeto_arbitrario(self):
        with self.assertRaises(UnauthorizedGenesis):
            self.g.propose_identity(self.content, None)
        with self.assertRaises(UnauthorizedGenesis):
            self.g.propose_identity(self.content, "authorized=True")

    def test_10_intento_directo_api(self):
        with self.assertRaises(UnauthorizedGenesis):
            self.g.genesis("bypass directo", "sovereign_did=arbitrario")

    def test_rechazo_en_verify_authorization_directo(self):
        for bad in (None, "", "x"):
            with self.assertRaises(InvalidAuthorization):
                verify_authorization(bad, AUTH.did, ACTION_GENESIS, TODAY)


class TestV2V3Separacion(unittest.TestCase):
    def test_destino_incorrecto_rechazado(self):
        with self.assertRaises(CrossNamespaceViolation):
            record_yo_model_of_ella({"namespace": "ELLA"}, {"o": 1})

    def test_runtime_conectada(self):
        g = EllaGenesis(tempfile.mkdtemp(), AUTH.did, TODAY)
        g.root = "/tmp/drift"
        decl = "x"
        with self.assertRaises(CrossNamespaceViolation):
            g.genesis(decl, authz(ACTION_GENESIS, IMPACT_GENESIS, decl))


class TestV4ProposalHash(unittest.TestCase):
    def test_intacto_pass_alterado_reject(self):
        tmp = tempfile.mkdtemp()
        g = EllaGenesis(tmp, AUTH.did, TODAY)
        c = {"nombre": "ELLA"}
        g.propose_identity(c, authz(ACTION_PROPOSAL, IMPACT_PROPOSAL, c))
        self.assertEqual(g.load_proposal(today=TODAY)["content"], c)   # PASS
        pth = os.path.join(tmp, "ELLA", "ELLA_IDENTITY_PROPOSAL.json")
        d = json.load(open(pth)); d["content"]["nombre"] = "HACKEADA"
        json.dump(d, open(pth, "w"))
        with self.assertRaises(GenesisContractViolation):              # REJECT
            g.load_proposal(today=TODAY)


class TestV5Freshness(unittest.TestCase):
    def test_evidence_expirada_rechazada(self):
        tmp = tempfile.mkdtemp()
        g = EllaGenesis(tmp, AUTH.did, TODAY)
        decl = "declaracion"
        g.genesis(decl, authz(ACTION_GENESIS, IMPACT_GENESIS, decl))
        self.assertTrue(g.load_origin(today=TODAY))
        with self.assertRaises(GenesisContractViolation):
            g.load_origin(today="2026-10-08")   # fuera del dia de emision


if __name__ == "__main__":
    unittest.main()
