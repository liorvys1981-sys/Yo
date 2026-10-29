import os, sys, time, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from digital_self import DigitalSelf, VersionIntegrityError
from genome_store import GenomeStore

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")


class TestPersistencia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.led_path = os.path.join(self.tmp, "ledger.jsonl")
        self.store = GenomeStore(self.tmp, self.led_path)

    def mk(self):
        ds = DigitalSelf("subj-1", "tenant-1")
        for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
            ds.create(k)
        return ds

    def test_save_load_roundtrip(self):
        ds = self.mk()
        self.store.change(ds, "Goals", {"meta": "5k"}, "SELF_REPORTED", 0.9,
                          ("ev:1",), "src", "crear")
        self.store.change(ds, "Goals", {"meta": "10k"}, "SELF_REPORTED", 0.9,
                          ("ev:2",), "src", "ampliar")
        ds2 = self.store.load("tenant-1", "subj-1")
        g = ds2.get("Goals")
        self.assertEqual(len(g.versions), 2)
        self.assertEqual(g.active.content, {"meta": "10k"})
        self.assertEqual(g.version(1).content, {"meta": "5k"})

    def test_reconstruccion_temporal_tras_reload(self):
        ds = self.mk()
        t0 = time.time()
        time.sleep(0.002)
        self.store.change(ds, "Traits", {"p": "a"}, "OBSERVED", 0.9, ("e:1",), "s", "v1")
        t1 = time.time()
        time.sleep(0.002)
        self.store.change(ds, "Traits", {"p": "b"}, "SELF_REPORTED", 1.0, ("e:2",), "s", "v2")
        ds2 = self.store.load("tenant-1", "subj-1")
        snap = ds2.reconstruct(t1)
        self.assertEqual(snap["Traits"]["content"], {"p": "a"})
        self.assertEqual(snap["Traits"]["version"], 1)

    def test_tamper_en_disco_detectado(self):
        ds = self.mk()
        self.store.change(ds, "Goals", {"x": 1}, "SELF_REPORTED", 0.9, ("e:1",), "s", "v1")
        path = os.path.join(self.tmp, "tenant-1", "subj-1.genome.json")
        data = open(path).read().replace('"x": 1', '"x": 99')
        open(path, "w").write(data)
        with self.assertRaises(VersionIntegrityError):
            self.store.load("tenant-1", "subj-1")

    def test_save_atomico_sin_tmp_residual(self):
        ds = self.mk()
        self.store.change(ds, "Goals", {"x": 1}, "SELF_REPORTED", 0.9, ("e:1",), "s", "v1")
        leftovers = [f for f in os.listdir(os.path.join(self.tmp, "tenant-1"))
                     if f.endswith(".tmp")]
        self.assertEqual(leftovers, [])


class TestEvidenceWiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.led_path = os.path.join(self.tmp, "ledger.jsonl")
        self.store = GenomeStore(self.tmp, self.led_path)
        self.ds = DigitalSelf("subj-1", "tenant-1")
        for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
            self.ds.create(k)

    def test_cada_cambio_produce_evento(self):
        ev1 = self.store.change(self.ds, "Goals", {"m": "a"}, "SELF_REPORTED", 0.9, ("e:1",), "s", "v1")
        ev2 = self.store.change(self.ds, "Goals", {"m": "b"}, "SELF_REPORTED", 0.9, ("e:2",), "s", "v2")
        self.assertEqual((ev1["version"], ev2["version"]), (1, 2))
        self.assertIn("ledger_hash", ev1)

    def test_ledger_verificable(self):
        for i in range(5):
            self.store.change(self.ds, "Goals", {"m": i}, "SELF_REPORTED", 0.9,
                              (f"e:{i}",), "s", f"cambio {i}")
        self.assertTrue(self.store.ledger.verify())

    def test_evento_contiene_content_hash(self):
        ev = self.store.change(self.ds, "Goals", {"m": "x"}, "SELF_REPORTED", 0.9,
                               ("e:1",), "s", "v1")
        self.assertEqual(len(ev["content_hash"]), 64)

    def test_sin_ledger_funciona_sin_evidencia_externa(self):
        store2 = GenomeStore(tempfile.mkdtemp())
        ds = DigitalSelf("s2", "t2")
        ds.create("Goals")
        ev = store2.change(ds, "Goals", {"m": 1}, "SELF_REPORTED", 0.9, ("e:1",), "s", "v1")
        self.assertNotIn("ledger_hash", ev)   # degradacion explicita, no silenciosa


if __name__ == "__main__":
    unittest.main()
