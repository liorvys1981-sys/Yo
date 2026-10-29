import sys, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from vector_memory import SemanticMemoryIndex, MemoryRetriever, _embed
from context_assembly import ContextAssembler, LABELS


class TestVectorMemory(unittest.TestCase):
    def test_index_retrieve(self):
        idx = SemanticMemoryIndex()
        md = lambda conf=0.9: {"tenant_id": "YO", "owner_id": "yo", "provenance": "SELF_REPORTED",
                               "timestamp": 1.0, "confidence": conf}
        idx.index("m1", "valoro la libertad y la independencia", md())
        idx.index("m2", "prefiero orden y control", md())
        r = MemoryRetriever(idx)
        hits = r.retrieve("libertad", "YO", "yo")
        self.assertEqual(hits[0]["memory_id"], "m1")
        self.assertIn("similarity", hits[0])
        self.assertIn("provenance", hits[0]["metadata"])
        self.assertEqual(len(hits[0]["content_hash"]), 16)

    def test_tenant_isolation(self):
        idx = SemanticMemoryIndex()
        md = {"tenant_id": "ELLA", "owner_id": "ella", "provenance": "OBSERVED",
              "timestamp": 1.0, "confidence": 0.8}
        idx.index("e1", "dato de ella", md)
        r = MemoryRetriever(idx)
        self.assertEqual(r.retrieve("dato", "YO", "yo"), [])
        self.assertEqual(len(r.retrieve("dato", "ELLA", "ella")), 1)

    def test_determinismo_embed(self):
        self.assertEqual(_embed("hola mundo"), _embed("hola mundo"))
        self.assertNotEqual(_embed("hola"), _embed("adios"))

    def test_metadata_obligatoria(self):
        idx = SemanticMemoryIndex()
        with self.assertRaises(ValueError):
            idx.index("x", "texto", {"tenant_id": "YO"})

    def test_similitud_no_es_autoridad(self):
        """La similitud alta no modifica nada: retriever es read-only por construccion."""
        idx = SemanticMemoryIndex()
        idx.index("m1", "x", {"tenant_id": "YO", "owner_id": "yo", "provenance": "SELF_REPORTED",
                              "timestamp": 1.0, "confidence": 1.0})
        before = dict(idx._items)
        MemoryRetriever(idx).retrieve("x", "YO", "yo")
        self.assertEqual(before, idx._items)


class TestContextAssembly(unittest.TestCase):
    def test_assemble_completo(self):
        ctx = ContextAssembler().assemble(
            digital_self={"Identity": {"status": "ACTIVE"}},
            memories=[{"provenance": "SELF_REPORTED"}, {"provenance": "INFERRED"}],
            insights=[], purpose="mision", tenant_id="YO", owner_id="yo")
        for campo in ("digital_self", "relevant_memory", "relationship_context", "session",
                      "conversation_history", "patterns", "insights", "goals", "purpose",
                      "future", "evidence", "uncertainty"):
            self.assertIn(campo, ctx)
        self.assertEqual(ctx["provenance_labels"]["SELF_REPORTED"], 1)
        self.assertEqual(ctx["provenance_labels"]["INFERRED"], 1)
        self.assertEqual(tuple(ctx["provenance_labels"]), LABELS)

    def test_retriever_integracion(self):
        idx = SemanticMemoryIndex()
        idx.index("m1", "creo en el trabajo digno",
                  {"tenant_id": "YO", "owner_id": "yo", "provenance": "SELF_REPORTED",
                   "timestamp": 1.0, "confidence": 0.9})
        ctx = ContextAssembler().assemble(retriever=MemoryRetriever(idx), query="trabajo",
                                          tenant_id="YO", owner_id="yo")
        self.assertEqual(ctx["relevant_memory"][0]["memory_id"], "m1")
