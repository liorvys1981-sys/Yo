import sys, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from memory_model import (MemoryStore, MemoryRecord, MEMORY_TYPES, SENSITIVE_TYPES,
    TenantDenied, MissingProvenance)


def rec(mtype="EPISODIC", tenant="t1", prov="OBSERVED", src="doc:1", conf=0.9):
    return MemoryRecord(memory_type=mtype, content={"nota": "x"}, provenance=prov,
        confidence=conf, source_ref=src, tenant_id=tenant, subject_id="s1",
        cognitive_instance_id="ci1", memory_scope="scope-a")


class TestMemorias(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()

    def test_cinco_tipos_existentes(self):
        self.assertEqual(len(MEMORY_TYPES), 5)
        for t in MEMORY_TYPES:
            self.store.store(rec(mtype=t))

    def test_emotional_sensible(self):
        r = rec(mtype="EMOTIONAL", prov="SELF_REPORTED")
        self.assertTrue(r.sensitive)

    def test_tenant_aislado(self):
        self.store.store(rec(tenant="t1"))
        with self.assertRaises(TenantDenied):
            self.store.query("t2", "EPISODIC")

    def test_tenant_ok_ve_lo_suyo(self):
        self.store.store(rec(tenant="t1"))
        self.assertEqual(len(self.store.query("t1", "EPISODIC")), 1)

    def test_provenance_invalido_rechazado(self):
        with self.assertRaises(MissingProvenance):
            rec(prov="ADIVINADO")

    def test_source_ref_obligatorio(self):
        with self.assertRaises(MissingProvenance):
            self.store.store(rec(src=""))

    def test_forget_es_supersede_no_delete(self):
        mid = self.store.store(rec())
        succ = self.store.forget("t1", mid)
        self.assertNotEqual(succ, mid)
        visibles = self.store.query("t1", "EPISODIC")
        self.assertEqual(len(visibles), 1)                 # sucesor
        self.assertTrue(visibles[0].content.get("forgotten"))
        todos = self.store.query("t1", "EPISODIC", include_superseded=True)
        self.assertEqual(len(todos), 2)                    # original preservado

    def test_consolidacion_procedencia_2o_orden(self):
        eid = self.store.store(rec(mtype="EPISODIC"))
        sid = self.store.consolidate("t1", eid, {"resumen": "leccion"})
        sem = [r for r in self.store.query("t1", "SEMANTIC")][0]
        self.assertEqual(sem.id, sid)
        self.assertEqual(sem.provenance, "SYSTEM_DERIVED")
        self.assertTrue(sem.source_ref.startswith("consolidated-from:"))

    def test_consolidar_no_episodica_falla(self):
        sid = self.store.store(rec(mtype="SEMANTIC"))
        with self.assertRaises(Exception):
            self.store.consolidate("t1", sid, {})

    def test_superseded_oculto_por_defecto(self):
        mid = self.store.store(rec())
        self.store.forget("t1", mid)
        self.assertEqual(len(self.store.query("t1", "EPISODIC")), 1)
        self.assertEqual(len(self.store.query("t1", "EPISODIC", include_superseded=True)), 2)
