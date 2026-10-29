import sys, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from cognitive_api import (RequestContext, CognitiveAPI, MemoryAPI,
    DeniedTenant, Unprovenanced, EvolutionLocked, ReplayStale)

CTX = RequestContext("t", "s", "c", "m", "a")


class TestContexto(unittest.TestCase):
    def test_completo_ok(self):
        self.assertIs(RequestContext.require(CTX), CTX)

    def test_none_denied(self):
        with self.assertRaises(DeniedTenant):
            RequestContext.require(None)

    def test_incompleto_denied(self):
        with self.assertRaises(DeniedTenant):
            RequestContext.require(RequestContext("t1", "", "c", "m", "a"))

    def test_errores_canonicos(self):
        for exc, code in [(DeniedTenant, "DENIED_TENANT"), (Unprovenanced, "UNPROVENANCED"),
                          (EvolutionLocked, "EVOLUTION_LOCKED"), (ReplayStale, "REPLAY_STALE")]:
            self.assertEqual(exc().code, code)


class TestInterfaces(unittest.TestCase):
    def test_base_no_instanciable(self):
        with self.assertRaises(TypeError):
            CognitiveAPI()

    def test_memory_api_no_instanciable_sin_impl(self):
        with self.assertRaises(TypeError):
            MemoryAPI()

    def test_stub_concreto_ok(self):
        class Stub(MemoryAPI):
            def _store_impl(self, ctx, record): return "id"
            def _query_impl(self, ctx, memory_type, filters=None): return []
            def _forget_impl(self, ctx, memory_id): return "succ"
        stub = Stub()
        self.assertEqual(stub.store(CTX, {}), "id")
        self.assertEqual(stub.api_version, "v0.1")

    def test_enforcement_tenant_estructural(self):
        class StubMalicioso(MemoryAPI):   # omite validar: no puede, la ABC valida
            def _store_impl(self, ctx, record): return "id"
            def _query_impl(self, ctx, memory_type, filters=None): return []
            def _forget_impl(self, ctx, memory_id): return "succ"
        with self.assertRaises(DeniedTenant):
            StubMalicioso().store(None, {})     # la ABC rechaza antes de _impl
