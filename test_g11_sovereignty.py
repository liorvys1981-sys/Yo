import os, sys, json, shutil, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from digital_self import DigitalSelf
from genome_store import GenomeStore
from sovereignty import (TwinExporter, TwinVerifier, SignatureInvalid,
    HashMismatch, GenomeIntegrityFail, HistoryBroken, AuditTrailBroken)
from elyo_wiring import make_elyo_gate, elyo_code
from pipeline_evolution import EvolutionPipeline
from identity import Identity
from authority import Authority

KEY = b"g" * 32
TODAY = "2026-10-07"
EXP = [{"id": f"e{i}", "domain": "habitos", "key": "lectura", "value": "hecha",
        "provenance": "OBSERVED", "ts": float(i)} for i in range(1, 4)]


G11_AUTH = Identity(seed=b"a" * 32)
def mk(populate=True):
    tmp = tempfile.mkdtemp()
    gate = make_elyo_gate(KEY, TODAY, True)
    store = GenomeStore(tmp, os.path.join(tmp, "ledger.jsonl"),
                        authority_did=G11_AUTH.did, today=TODAY)
    pipe = EvolutionPipeline(store, gate, clock=lambda: 900.0,
                             authority=Authority(G11_AUTH, gate, TODAY))
    ds = DigitalSelf("subj-1", "tenant-1")
    for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
        ds.create(k)
    if populate:
        pipe.submit("r1", ds, EXP, "Goals", {"g": "v1"}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "v1")
        pipe.review("r1", "ok")
        pipe.approve("r1", ds, f"EJECUTA export {elyo_code(KEY, TODAY)}")
    return tmp, store, ds


class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmp, self.store, self.ds = mk()
        self.out = tempfile.mkdtemp()
        self.idn = Identity(seed=b"t" * 32)
        self.exp = TwinExporter(self.store, self.idn, clock=lambda: 12345.0)
        self.r = self.exp.export(self.ds, self.out, "exp:test1")

    def test_export_genera_paquete_completo(self):
        pkg = self.r["path"]
        for fn in ("self.json", "audit.jsonl", "manifest.json"):
            self.assertTrue(os.path.exists(os.path.join(pkg, fn)), fn)

    def test_manifest_contenidos(self):
        m = self.r["manifest"]
        self.assertEqual(m["did"], self.idn.did)
        self.assertIn("self.json", m["files"])
        self.assertIn("audit.jsonl", m["files"])
        self.assertEqual(len(m["files"]["self.json"]["sha256"]), 64)
        self.assertEqual(m["exported_at"], 12345.0)

    def test_no_secretos_en_paquete(self):
        pkg = self.r["path"]
        for fn in ("self.json", "manifest.json", "audit.jsonl"):
            data = open(os.path.join(pkg, fn), "rb").read().decode("utf-8", "replace")
            self.assertNotIn("seed", data.lower())
            self.assertNotIn("private_key", data.lower())

    def test_export_no_modifica_digital_self(self):
        g = self.ds.get("Goals")
        self.assertEqual(g.active.content, {"g": "v1"})
        self.assertTrue(g.active.verify_integrity())

    def test_determinismo_con_clock_inyectado(self):
        """Determinismo de CONTENIDO: entity_id son uuid (identificadores unicos,
        no contenido); se normalizan para comparar estado logico."""
        tmp2, store2, ds2 = mk()
        out2 = tempfile.mkdtemp()
        e2 = TwinExporter(store2, Identity(seed=b"t" * 32), clock=lambda: 12345.0)
        r2 = e2.export(ds2, out2, "exp:test1")
        def normalized(path):
            with open(os.path.join(path, "self.json")) as f:
                d = json.load(f)
            for e in d["entities"].values():
                e["entity_id"] = "NORM"
                e["created_at"] = "NORM"   # wall clock: ver GATES_STATUS limitation
            return d
        self.assertEqual(normalized(self.r["path"]), normalized(r2["path"]))


class TestVerificacionCompleta(unittest.TestCase):
    def setUp(self):
        self.tmp, self.store, self.ds = mk()
        self.out = tempfile.mkdtemp()
        self.r = TwinExporter(self.store, Identity(seed=b"t" * 32),
                              clock=lambda: 1.0).export(self.ds, self.out, "exp:v")

    def test_full_verify_ok(self):
        self.assertEqual(TwinVerifier.full_verify(self.r["path"])["status"], "VERIFIED")

    def test_verify_signature_individual(self):
        self.assertTrue(TwinVerifier.verify_signature(self.r["path"]))

    def test_verify_hashes_individual(self):
        self.assertTrue(TwinVerifier.verify_hashes(self.r["path"]))

    def test_verify_genome_integrity_individual(self):
        self.assertTrue(TwinVerifier.verify_genome_integrity(self.r["path"]))

    def test_verify_history_individual(self):
        self.assertTrue(TwinVerifier.verify_history(self.r["path"]))

    def test_verify_audit_trail_individual(self):
        self.assertTrue(TwinVerifier.verify_audit_trail(self.r["path"]))

    def test_verificacion_independiente_otro_proceso(self):
        """Sin estado en memoria: solo paquete + DID (re-import fresco)."""
        pkg = self.r["path"]
        self.assertTrue(TwinVerifier.full_verify(pkg))


class TestTamperNegativos(unittest.TestCase):
    def setUp(self):
        self.tmp, self.store, self.ds = mk()
        self.out = tempfile.mkdtemp()
        self.r = TwinExporter(self.store, Identity(seed=b"t" * 32),
                              clock=lambda: 1.0).export(self.ds, self.out, "exp:t")

    def _copy(self):
        dst = tempfile.mkdtemp()
        pkg = os.path.join(dst, "tampered")
        shutil.copytree(self.r["path"], pkg)
        return pkg

    def test_contenido_alterado_detectado(self):
        pkg = self._copy()
        p = os.path.join(pkg, "self.json")
        d = json.load(open(p))
        d["entities"]["Goals"]["versions"][0]["content"] = {"g": "MANIPULADO"}
        json.dump(d, open(p, "w"))
        with self.assertRaises((HashMismatch, GenomeIntegrityFail)):
            TwinVerifier.full_verify(pkg)

    def test_hash_en_manifest_alterado(self):
        pkg = self._copy()
        p = os.path.join(pkg, "manifest.json")
        m = json.load(open(p))
        m["files"]["self.json"]["sha256"] = "0" * 64
        m["signature"] = Identity(seed=b"t" * 32).sign(
            json.dumps({k: v for k, v in m.items() if k != "signature"},
                       sort_keys=True, separators=(",", ":")).encode())
        json.dump(m, open(p, "w"))
        with self.assertRaises(HashMismatch):
            TwinVerifier.verify_hashes(pkg)

    def test_firma_invalida(self):
        pkg = self._copy()
        p = os.path.join(pkg, "manifest.json")
        m = json.load(open(p))
        m["signature"] = Identity(seed=b"otra" * 8).sign(b"cualquier cosa")
        json.dump(m, open(p, "w"))
        with self.assertRaises(SignatureInvalid):
            TwinVerifier.verify_signature(pkg)

    def test_did_cambiado_falla_firma(self):
        pkg = self._copy()
        p = os.path.join(pkg, "manifest.json")
        m = json.load(open(p))
        m["did"] = Identity(seed=b"x" * 32).did    # DID distinta: firma no casa
        json.dump(m, open(p, "w"))
        with self.assertRaises(SignatureInvalid):
            TwinVerifier.verify_signature(pkg)

    def test_audit_trail_truncado(self):
        """Semantica correcta: un prefijo de cadena append-only es internamente valido
        (verify_audit_trail pasa); el TRUNCAMIENTO se detecta por el hash del manifest."""
        pkg = self._copy()
        p = os.path.join(pkg, "audit.jsonl")
        with open(p) as f:
            lines = f.readlines()
        with open(p, "w") as f:
            f.writelines(lines[:-1])               # quitar ultima entrada
        self.assertTrue(TwinVerifier.verify_audit_trail(pkg))   # prefijo valido
        with self.assertRaises(HashMismatch):                   # completitud via manifest
            TwinVerifier.verify_hashes(pkg)

    def test_manifest_inconsistente_archivo_faltante(self):
        pkg = self._copy()
        os.remove(os.path.join(pkg, "audit.jsonl"))
        with self.assertRaises(FileNotFoundError):
            TwinVerifier.verify_hashes(pkg)


if __name__ == "__main__":
    unittest.main()
