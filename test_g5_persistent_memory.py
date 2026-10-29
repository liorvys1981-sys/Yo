import os, sys, tempfile, unittest, json
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from persistent_memory import (PersistentMemoryStore, PMemoryError, TenantDenied,
    IntegrityError, MEMORY_KINDS, LIFECYCLE)


def mk(tmp):
    return PersistentMemoryStore(tmp, os.path.join(tmp, "ledger.jsonl"))


class TestContrato04(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.s = mk(self.tmp)

    def test_campos_obligatorios_presentes(self):
        mid = self.s.store("t1", "s1", "ci1", "EPISODIC", {"e": "evento"},
                           "OBSERVED", 0.9, ("ev:1",), "src")
        it = self.s.load("t1", mid)
        for campo in ("memory_id", "tenant_id", "subject_id", "cognitive_instance_id",
                      "kind", "content", "timestamp", "provenance", "confidence",
                      "evidence", "version", "content_hash", "lifecycle"):
            self.assertIn(campo, it)

    def test_cinco_memorias(self):
        self.assertEqual(len(MEMORY_KINDS), 5)
        for k in MEMORY_KINDS:
            self.s.store("t1", "s1", "ci1", k, {"k": k}, "OBSERVED", 0.5, ("e",), "src")

    def test_tenant_aislado_en_disco(self):
        mid = self.s.store("t1", "s1", "ci1", "EPISODIC", {}, "OBSERVED", 0.5, ("e",), "s")
        self.assertEqual(len(self.s.query("t1", "EPISODIC")), 1)
        self.assertEqual(len(self.s.query("t2", "EPISODIC")), 0)
        with self.assertRaises(FileNotFoundError):
            self.s.load("t2", mid)

    def test_update_versiona_preservando_anterior(self):
        mid = self.s.store("t1", "s", "c", "SEMANTIC", {"sabiduria": "v1"},
                           "SYSTEM_DERIVED", 0.8, ("e:1",), "src")
        nid = self.s.update("t1", mid, {"sabiduria": "v2"}, ("e:2",), "refinamiento")
        viejo = self.s.load("t1", mid)
        nuevo = self.s.load("t1", nid)
        self.assertEqual((viejo["lifecycle"], viejo["content"]), ("SUPERSEDED", {"sabiduria": "v1"}))
        self.assertEqual((nuevo["version"], nuevo["lifecycle"]), (2, "ACTIVE"))
        self.assertEqual(nuevo["supersedes"], mid)

    def test_update_a_no_activa_falla(self):
        mid = self.s.store("t1", "s", "c", "EPISODIC", {}, "OBSERVED", 0.5, ("e",), "s")
        nid = self.s.update("t1", mid, {"v": 2}, ("e",), "r")
        with self.assertRaises(PMemoryError):
            self.s.update("t1", mid, {"v": 3}, ("e",), "doble")

    def test_forget_tombstone(self):
        mid = self.s.store("t1", "s", "c", "EMOTIONAL", {"dato": "sensible"},
                           "SELF_REPORTED", 1.0, ("e",), "s")
        self.assertTrue(self.s.load("t1", mid)["sensitive"])
        self.s.forget("t1", mid)
        it = self.s.load("t1", mid)
        self.assertEqual((it["lifecycle"], it["content"]), ("FORGOTTEN", {"forgotten": True}))
        self.assertEqual(len(self.s.query("t1", "EMOTIONAL")), 0)                    # excluido de ACTIVE
        self.assertEqual(len(self.s.query("t1", "EMOTIONAL", lifecycle="FORGOTTEN")), 1)

    def test_tamper_en_disco_detectado(self):
        mid = self.s.store("t1", "s", "c", "KNOWLEDGE", {"hecho": "x"}, "OBSERVED", 0.9, ("e",), "s")
        p = os.path.join(self.tmp, "t1", f"{mid}.json")
        d = json.load(open(p)); d["content"]["hecho"] = "MANIPULADO"
        json.dump(d, open(p, "w"))
        with self.assertRaises(IntegrityError):
            self.s.load("t1", mid)

    def test_no_mutacion_del_digital_self(self):
        """Regla soberana 04_MEMORY.md: el modulo no conoce DigitalSelf."""
        src = open("/mnt/agents/output/EL_YO/02_MEMORIA/persistent_memory.py").read()
        self.assertNotIn("from digital_self import", src)
        self.assertNotIn("DigitalSelf(", src)

    def test_inferred_sin_evidencia_rechazado(self):
        with self.assertRaises(PMemoryError):
            self.s.store("t1", "s", "c", "EPISODIC", {}, "INFERRED", 0.3, (), "s")

    def test_ledger_evidence_por_operacion(self):
        self.s.store("t1", "s", "c", "EPISODIC", {"a": 1}, "OBSERVED", 0.5, ("e",), "s")
        self.assertTrue(self.s.ledger.verify())


if __name__ == "__main__":
    unittest.main()
