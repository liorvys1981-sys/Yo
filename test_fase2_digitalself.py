import sys, time, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from digital_self import (DigitalSelf, SelfEntity, DigitalSelfError,
    InvalidProvenance, UnknownEntityKind, PROVENANCE, ENTITY_KINDS)


class TestCreacion(unittest.TestCase):
    def test_crear_self_las_7_entidades(self):
        ds = DigitalSelf("subj-1", "tenant-1")
        for k in ENTITY_KINDS:
            ds.create(k)
        self.assertTrue(ds.schema_conformant())

    def test_entidad_duplicada_rechazada(self):
        ds = DigitalSelf("s", "t")
        ds.create("Identity")
        with self.assertRaises(DigitalSelfError):
            ds.create("Identity")

    def test_kind_desconocido_rechazado(self):
        with self.assertRaises(UnknownEntityKind):
            SelfEntity(kind="Alma")

    def test_subject_tenant_obligatorios(self):
        with self.assertRaises(DigitalSelfError):
            DigitalSelf("", "t")


class TestProvenance(unittest.TestCase):
    def setUp(self):
        self.ds = DigitalSelf("s", "t")
        self.idt = self.ds.create("Identity")

    def test_cinco_etiquetas(self):
        self.assertEqual(len(PROVENANCE), 5)

    def test_provenance_invalido_rechazado(self):
        with self.assertRaises(InvalidProvenance):
            self.idt.set({}, "ADIVINADO", 0.5, ("ev:1",), "src", "test")

    def test_fundamental_no_inferido(self):
        with self.assertRaises(DigitalSelfError):
            self.idt.set({}, "INFERRED", 0.5, ("ev:1",), "src", "test")

    def test_fundamental_no_system_derived(self):
        with self.assertRaises(DigitalSelfError):
            self.idt.set({}, "SYSTEM_DERIVED", 0.5, (), "src", "test")

    def test_inferido_exige_evidencia(self):
        tr = self.ds.create("Traits")
        with self.assertRaises(DigitalSelfError):
            tr.set({}, "INFERRED", 0.5, (), "src", "test")

    def test_distinguir_observado_declarado_inferido(self):
        tr = self.ds.create("Traits")
        tr.set({"paciencia": "alta"}, "OBSERVED", 0.9, ("ev:o",), "src", "v1")
        v2 = tr.set({"paciencia": "media"}, "SELF_REPORTED", 1.0, ("ev:s",), "src", "v2")
        v3 = tr.set({"paciencia": "baja"}, "INFERRED", 0.4, ("ev:i",), "src", "v3")
        self.assertEqual(tr.version(1).provenance, "OBSERVED")
        self.assertEqual(tr.version(2).provenance, "SELF_REPORTED")
        self.assertEqual(tr.version(3).provenance, "INFERRED")
        bd = self.ds.provenance_breakdown()
        self.assertEqual((bd["OBSERVED"], bd["SELF_REPORTED"], bd["INFERRED"]), (0, 0, 1))
        self.assertEqual(tr.active.version, v3)


class TestVersionado(unittest.TestCase):
    def setUp(self):
        self.ds = DigitalSelf("s", "t")
        self.g = self.ds.create("Goals")

    def test_versiones_se_preservan(self):
        v1 = self.g.set({"meta": "correr 5k"}, "SELF_REPORTED", 0.9, ("ev:1",), "src", "crear")
        time.sleep(0.001)
        v2 = self.g.set({"meta": "correr 10k"}, "SELF_REPORTED", 0.9, ("ev:2",), "src", "ampliar")
        self.assertEqual((v1, v2), (1, 2))
        self.assertEqual(self.g.version(1).content, {"meta": "correr 5k"})
        self.assertEqual(self.g.version(2).content, {"meta": "correr 10k"})
        self.assertEqual(self.g.active_version, 2)

    def test_historial_tamper_evidence(self):
        """Dicts anidados no son congelables en Python: integridad por deteccion
        (hash sellado en EntityVersion), coherente con la filosofia evidence."""
        from digital_self import VersionIntegrityError
        self.g.set({"a": 1}, "SELF_REPORTED", 0.9, ("ev:1",), "src", "v1")
        v = self.g.version(1)
        self.assertTrue(v.verify_integrity())
        v.content["a"] = 99                       # mutacion externa posible...
        with self.assertRaises(VersionIntegrityError):
            v.verify_integrity()                  # ...pero detectada

    def test_version_inexistente(self):
        from digital_self import VersionIntegrityError
        self.g.set({"a": 1}, "SELF_REPORTED", 0.9, ("ev:1",), "src", "v1")
        with self.assertRaises(VersionIntegrityError):
            self.g.version(9)


class TestTemporalidad(unittest.TestCase):
    def test_reconstruir_estado_anterior(self):
        ds = DigitalSelf("s", "t")
        g = ds.create("Goals")
        t0 = time.time()
        time.sleep(0.002)
        g.set({"meta": "5k"}, "SELF_REPORTED", 0.9, ("ev:1",), "src", "crear")
        t1 = time.time()
        time.sleep(0.002)
        g.set({"meta": "10k"}, "SELF_REPORTED", 0.9, ("ev:2",), "src", "ampliar")
        snap = ds.reconstruct(t1)
        self.assertEqual(snap["Goals"]["content"], {"meta": "5k"})
        self.assertEqual(snap["Goals"]["version"], 1)
        snap_now = ds.reconstruct(time.time())
        self.assertEqual(snap_now["Goals"]["content"], {"meta": "10k"})

    def test_as_of_previo_al_primer_set_es_none(self):
        ds = DigitalSelf("s", "t")
        e = ds.create("Traits")
        t_pasado = time.time() - 100
        self.assertIsNone(e.as_of(t_pasado))
        e.set({"x": 1}, "OBSERVED", 0.8, ("ev:1",), "src", "v1")
        self.assertIsNotNone(e.as_of(t_pasado + 200))


class TestConfianza(unittest.TestCase):
    def test_confidence_rango(self):
        ds = DigitalSelf("s", "t")
        tr = ds.create("Traits")
        with self.assertRaises(DigitalSelfError):
            tr.set({}, "OBSERVED", 1.7, ("ev:1",), "src", "bad")

    def test_change_reason_obligatorio_en_historial(self):
        ds = DigitalSelf("s", "t")
        tr = ds.create("Traits")
        tr.set({"x": 1}, "OBSERVED", 0.8, ("ev:1",), "src", "razon-a")
        self.assertEqual(tr.version(1).change_reason, "razon-a")



class TestBeliefsFundamentalV2(unittest.TestCase):
    """v2.0.0: Beliefs es fundamental (decision soberana, evolucion trazada)."""
    def test_beliefs_rechaza_inferred(self):
        ds = DigitalSelf("s", "t")
        b = ds.create("Beliefs")
        with self.assertRaises(DigitalSelfError):
            b.set({"creencia": "x"}, "INFERRED", 0.6, ("ev:1",), "src", "test")

    def test_beliefs_rechaza_system_derived(self):
        ds = DigitalSelf("s", "t")
        b = ds.create("Beliefs")
        with self.assertRaises(DigitalSelfError):
            b.set({"creencia": "x"}, "SYSTEM_DERIVED", 0.9, (), "src", "test")

    def test_beliefs_acepta_self_reported(self):
        ds = DigitalSelf("s", "t")
        b = ds.create("Beliefs")
        v = b.set({"creencia": "el trabajo dignifica"}, "SELF_REPORTED", 1.0, ("ev:1",), "src", "declaracion")
        self.assertEqual(v, 1)

if __name__ == "__main__":
    unittest.main()
