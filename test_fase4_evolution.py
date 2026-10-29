import os, sys, time, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from digital_self import DigitalSelf
from genome_store import GenomeStore
from evolution_engine import EvolutionEngine
from cognitive_api import EvidenceAPI, RequestContext, DeniedTenant
from el_yo.constitution import Denied
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from authority import Authority
from identity import Identity
from authority import Authority
from identity import Identity

KEY = b"g" * 32
TODAY = "2026-10-07"
CODE = DailyCodeProvider(KEY).code(TODAY)


AUTH_ID4 = Identity(seed=b"a" * 32)
def mk_stack(tmp, second_key=True):
    gate = AuthorizationGate(DailyCodeProvider(KEY), TODAY, second_key_present=second_key)
    store = GenomeStore(tmp, os.path.join(tmp, "ledger.jsonl"),
                        authority_did=AUTH_ID4.did, today=TODAY)
    return store, EvolutionEngine(store, gate, authority=Authority(AUTH_ID4, gate, TODAY))


def mk_ds():
    ds = DigitalSelf("subj-1", "tenant-1")
    for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
        ds.create(k)
    return ds


def phrase():
    return f"EJECUTA evolucion-identidad {CODE}"


class TestAutorizacionFundamental(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store, self.eng = mk_stack(self.tmp)
        self.ds = mk_ds()

    def test_identity_sin_autorizacion_denegado(self):
        for kind in ("Identity", "Values", "Beliefs"):
            with self.assertRaises(Denied):
                self.store.change(self.ds, kind, {"x": 1}, "SELF_REPORTED",
                                  1.0, ("e:1",), "src", "intento directo")

    def test_identity_autorizacion_valida_ok(self):
        pid = self.eng.propose(self.ds, "Identity", {"nombre": "soberano"},
                               "SELF_REPORTED", 1.0, ("e:1",), "src", "declaracion inicial")
        ev = self.eng.approve(self.ds, pid, phrase())
        self.assertEqual(ev["version"], 1)
        self.assertEqual(self.ds.get("Identity").active.content, {"nombre": "soberano"})
        self.assertIn("ledger_hash", ev)

    def test_identity_frase_invalida_denegado(self):
        pid = self.eng.propose(self.ds, "Identity", {"n": 1}, "SELF_REPORTED",
                               1.0, ("e:1",), "src", "cambio")
        with self.assertRaises(Denied):
            self.eng.approve(self.ds, pid, "AUTORIZA x codigo-mal")

    def test_identity_sin_segunda_llave_denegado(self):
        tmp = tempfile.mkdtemp()
        store, eng = mk_stack(tmp, second_key=False)
        ds = mk_ds()
        pid = eng.propose(ds, "Identity", {"n": 1}, "SELF_REPORTED", 1.0, ("e:1",), "src", "c")
        with self.assertRaises(Denied):      # gate exige doble llave (Art. 4.2)
            eng.approve(ds, pid, phrase())
        self.assertEqual(len(ds.get("Identity").versions), 0)   # sin modificar

    def test_values_y_beliefs_mismo_guard(self):
        for kind in ("Values", "Beliefs"):
            pid = self.eng.propose(self.ds, kind, {"v": kind}, "SELF_REPORTED",
                                   1.0, ("e:1",), "src", "cambio legitimo")
            ev = self.eng.approve(self.ds, pid, phrase())
            self.assertTrue(ev["approved_by"].startswith("did:key:"))  # R1: identidad verificable


class TestRechazoYAuditoria(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store, self.eng = mk_stack(self.tmp)
        self.ds = mk_ds()

    def test_rechazo_no_modifica_genome(self):
        pid = self.eng.propose(self.ds, "Beliefs", {"b": "nueva"}, "SELF_REPORTED",
                               1.0, ("e:1",), "src", "propuesta riesgosa")
        r = self.eng.reject(pid, "contradice Values vigente")
        self.assertEqual(r["state"], "rejected")
        self.assertTrue(r["genome_untouched"])
        self.assertEqual(len(self.ds.get("Beliefs").versions), 0)
        self.assertIsNotNone(r["ledger_hash"])   # rechazo auditado

    def test_rechazo_queda_en_ledger(self):
        pid = self.eng.propose(self.ds, "Values", {"v": "x"}, "SELF_REPORTED",
                               1.0, ("e:1",), "src", "p")
        self.eng.reject(pid, "no")
        tipos = []
        with open(os.path.join(self.tmp, "ledger.jsonl")) as f:
            for line in f:
                tipos.append(__import__("json").loads(line)["event"]["type"])
        self.assertIn("evolution_rejected", tipos)
        self.assertIn("evolution_proposal", tipos)


class TestEvidenciaYReconstruccion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store, self.eng = mk_stack(self.tmp)
        self.ds = mk_ds()

    def test_cada_cambio_autorizado_genera_evidencia(self):
        t_antes = time.time()
        time.sleep(0.002)
        pid = self.eng.propose(self.ds, "Identity", {"n": "v1"}, "SELF_REPORTED",
                               1.0, ("e:1",), "src", "v1")
        self.eng.approve(self.ds, pid, phrase())
        ds2 = self.store.load("tenant-1", "subj-1")
        self.assertTrue(ds2.get("Identity").active.verify_integrity())
        snap = ds2.reconstruct(t_antes)
        self.assertNotIn("Identity", snap)          # antes no existia contenido
        snap2 = ds2.reconstruct(time.time())
        self.assertEqual(snap2["Identity"]["content"], {"n": "v1"})

    def test_integridad_ledger_tras_toda_la_sesion(self):
        pid1 = self.eng.propose(self.ds, "Identity", {"a": 1}, "SELF_REPORTED", 1.0, ("e:1",), "s", "c1")
        self.eng.approve(self.ds, pid1, phrase())
        pid2 = self.eng.propose(self.ds, "Values", {"b": 2}, "SELF_REPORTED", 1.0, ("e:2",), "s", "c2")
        self.eng.reject(pid2, "revisado")
        self.assertTrue(self.store.ledger.verify())

    def test_genomestore_es_instancia_de_evidence_api(self):
        self.assertIsInstance(self.store, EvidenceAPI)
        ctx = RequestContext("tenant-1", "subj-1", "ci", "scope", "auth")
        h = self.store.append(ctx, {"type": "manual", "nota": "prueba contrato"})
        self.assertEqual(len(h), 64)
        self.assertTrue(self.store.verify(ctx))

    def test_evidence_api_ctx_ausente_denied(self):
        with self.assertRaises(DeniedTenant):
            self.store.append(None, {"x": 1})


if __name__ == "__main__":
    unittest.main()
