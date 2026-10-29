import sys, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from genome import validate_genome_element, provenance_breakdown, GenomeError, REASON, PROVENANCE


def elem(**kw):
    base = {"id": "gen:test:001", "kind": "preference", "content": {"x": 1},
            "provenance": "SELF_REPORTED", "confidence": 0.8,
            "source": {"type": "conversation", "ref": "doc:1"},
            "version": 1, "evidence": [], "evolution": []}
    base.update(kw)
    return base


class TestValidador(unittest.TestCase):
    def test_ok_minimo(self):
        validate_genome_element(elem())   # no raise

    def test_missing_provenance(self):
        e = elem(); del e["provenance"]
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(e)
        self.assertEqual(cm.exception.reason, REASON.MISSING_PROVENANCE)

    def test_provenance_invalido(self):
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(elem(provenance="ADIVINADO"))
        self.assertEqual(cm.exception.reason, REASON.INVALID_PROVENANCE)

    def test_confidence_fuera_rango(self):
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(elem(confidence=1.5))
        self.assertEqual(cm.exception.reason, REASON.INVALID_CONFIDENCE)

    def test_inferred_sin_evidencia(self):
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(elem(provenance="INFERRED", evidence=[]))
        self.assertEqual(cm.exception.reason, REASON.INFERRED_WITHOUT_EVIDENCE)

    def test_inferred_con_evidencia_ok(self):
        validate_genome_element(elem(provenance="INFERRED", evidence=["ev:1"]))

    def test_version_gap(self):
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(elem(version=3, evolution=[{"from": 1, "to": 2}]))
        self.assertEqual(cm.exception.reason, REASON.VERSION_GAP)

    def test_fundamental_inferring_rechazado(self):
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(elem(kind="value", provenance="INFERRED", evidence=["ev:1"]))
        self.assertEqual(cm.exception.reason, REASON.FUNDAMENTAL_INFERRED)

    def test_fundamental_system_derived_rechazado(self):
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(elem(kind="purpose", provenance="SYSTEM_DERIVED"))
        self.assertEqual(cm.exception.reason, REASON.FUNDAMENTAL_INFERRED)

    def test_fundamental_requiere_aprobacion_humana_en_evolucion(self):
        e = elem(kind="value", version=2, evolution=[
            {"from": 1, "to": 2, "approved_by": "agente"}])
        with self.assertRaises(GenomeError) as cm:
            validate_genome_element(e)
        self.assertEqual(cm.exception.reason, REASON.FUNDAMENTAL_NOT_APPROVABLE)

    def test_distinguibilidad(self):
        g = [elem(provenance=p) for p in
             ["OBSERVED", "INFERRED", "SELF_REPORTED", "SYSTEM_DERIVED", "UNCERTAIN"]]
        b = provenance_breakdown(g)
        self.assertEqual(set(b), PROVENANCE)
        self.assertTrue(all(v == 1 for v in b.values()))

    def test_determinismo_50x(self):
        e = elem()
        results = []
        for _ in range(50):
            try:
                validate_genome_element(e); results.append("OK")
            except GenomeError as ex:
                results.append(ex.reason)
        self.assertEqual(set(results), {"OK"})
