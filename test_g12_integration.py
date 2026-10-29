import os, sys, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from elyo_wiring import make_elyo_gate, elyo_code, ElyoGateUnavailable
from authority import Authority
from identity import Identity
from digital_self import DigitalSelf
from genome_store import GenomeStore
from pipeline_evolution import EvolutionPipeline, EvolutionLocked
from el_yo.constitution import Denied

KEY = b"g" * 32
TODAY = "2026-10-07"
EXP = [{"id": f"e{i}", "domain": "habitos", "key": "lectura", "value": "hecha",
        "provenance": "OBSERVED", "ts": float(i)} for i in range(1, 4)]


G12_AUTH = Identity(seed=b"a" * 32)
def mk_stack(second_key=True):
    tmp = tempfile.mkdtemp()
    gate = make_elyo_gate(KEY, TODAY, second_key)      # GATE REAL de EL_YO
    store = GenomeStore(tmp, os.path.join(tmp, "ledger.jsonl"),
                        authority_did=G12_AUTH.did, today=TODAY)
    pipe = EvolutionPipeline(store, gate, clock=lambda: 500.0,
                             authority=Authority(G12_AUTH, gate, TODAY))
    ds = DigitalSelf("subj-1", "tenant-1")
    for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
        ds.create(k)
    return tmp, store, pipe, ds


def phrase():
    return f"EJECUTA integracion-g12 {elyo_code(KEY, TODAY)}"


class TestIdentificacionDelGateReal(unittest.TestCase):
    def test_gate_real_importable_y_con_contrato(self):
        import inspect
        from elyo_wiring import _load_elyo_gate
        AG, DP = _load_elyo_gate()
        self.assertEqual(AG.__module__, "el_yo.gates")
        self.assertTrue(callable(getattr(AG, "authorize")))
        params = inspect.signature(AG.authorize).parameters
        self.assertIn("phrase", params)

    def test_no_mock_ni_doble(self):
        src = open("/mnt/agents/output/EL_YO/17_SOVEREIGNTY/elyo_wiring.py").read()
        self.assertNotIn("class AuthorizationGate", src)   # ninguna autoridad paralela

    def test_sin_autoridad_paralela_en_impl(self):
        """APP YO no implementa NINGUNA clase de autorizacion (requisito 2)."""
        impl_dir = "/mnt/agents/output/APP_YO/impl"
        for fn in os.listdir(impl_dir):
            if fn.endswith(".py"):
                s = open(os.path.join(impl_dir, fn)).read()
                self.assertNotIn("class AuthorizationGate", s, fn)
                self.assertNotIn("class DailyCodeProvider", s, fn)
                self.assertNotIn("class AuthorizationGate", s, fn)


class TestFlujoCompletoConGateReal(unittest.TestCase):
    def test_flujo_obligatorio_approve(self):
        """APP YO Evolution Request -> Engine -> EL_YO gate -> APPROVE -> GenomeStore -> ledger."""
        tmp, store, pipe, ds = mk_stack()
        pipe.submit("r1", ds, EXP, "Beliefs", {"b": "declarada"}, "SELF_REPORTED",
                    1.0, ("e:1",), "src", "declaracion de creencia")
        pipe.review("r1", "revision")
        out = pipe.approve("r1", ds, phrase())
        self.assertEqual(out["state"], "APPLIED")
        self.assertEqual(ds.get("Beliefs").active.content, {"b": "declarada"})
        self.assertEqual(len(ds.get("Beliefs").versions), 1)
        self.assertTrue(store.ledger.verify())

    def test_deny_deja_genome_intacto(self):
        tmp, store, pipe, ds = mk_stack()
        pipe.submit("r1", ds, EXP, "Identity", {"n": "x"}, "SELF_REPORTED",
                    1.0, ("e:1",), "src", "intento")
        pipe.review("r1", "revision")
        with self.assertRaises(Denied):                  # frase invalida -> DENY real
            pipe.approve("r1", ds, "AUTORIZA nada 000000000000")
        self.assertEqual(len(ds.get("Identity").versions), 0)
        self.assertEqual(pipe._requests["r1"].state, "REVIEW")   # rollback a REVIEW
        # genome intacto en disco = CERO escrituras (no existe archivo)
        path = os.path.join(tmp, "tenant-1", "subj-1.genome.json")
        self.assertFalse(os.path.exists(path))

    def test_identity_values_beliefs_exigen_humano_real(self):
        for kind in ("Identity", "Values", "Beliefs"):
            tmp, store, pipe, ds = mk_stack()
            pipe.submit("r1", ds, EXP, kind, {"x": 1}, "SELF_REPORTED", 1.0,
                        ("e",), "s", "intento sin autorizacion")
            pipe.review("r1", "ok")
            with self.assertRaises(Denied):
                pipe.approve("r1", ds, None)             # ausente
            with self.assertRaises(Denied):
                pipe.approve("r1", ds, "frase-invalida-total")   # invalida
            self.assertEqual(len(ds.get(kind).versions), 0)

    def test_approve_produce_version_no_sobrescritura(self):
        tmp, store, pipe, ds = mk_stack()
        for i, c in enumerate([{"g": "v1"}, {"g": "v2"}], 1):
            pipe.submit(f"r{i}", ds, EXP, "Goals", c, "SELF_REPORTED", 0.9,
                        ("e",), "s", f"c{i}")
            pipe.review(f"r{i}", "ok")
            pipe.approve(f"r{i}", ds, phrase())
        g = ds.get("Goals")
        self.assertEqual([v.content for v in g.versions],
                         [{"g": "v1"}, {"g": "v2"}])
        ds2 = store.load("tenant-1", "subj-1")
        self.assertEqual(ds2.get("Goals").version(1).content, {"g": "v1"})

    def test_campos_obligatorios_conservados(self):
        tmp, store, pipe, ds = mk_stack()
        pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "r")
        pipe.review("r1", "ok")
        out = pipe.approve("r1", ds, phrase())
        self.assertEqual(len(out["content_hash"]), 64)
        v = ds.get("Goals").active
        self.assertTrue(all([v.provenance == "SELF_REPORTED", v.ts is not None,
                             v.confidence == 0.9, len(v.content_hash) == 64]))


class TestLockedYBloqueoRegistrado(unittest.TestCase):
    def test_evolution_locked_se_mantiene_con_gate_real(self):
        tmp, store, pipe, ds = mk_stack()
        pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "r")
        pipe.lock("auditoria")
        with self.assertRaises(EvolutionLocked):
            pipe.review("r1", "x")
        pipe.unlock(phrase())                            # unlock via gate real
        pipe.review("r1", "ahora")
        self.assertEqual(pipe._requests["r1"].state, "REVIEW")

    def test_bloqueo_registrado_si_falta_elyo(self):
        """Req 11: si el gate real falta -> ElyoGateUnavailable; NUNCA sustituto."""
        import elyo_wiring
        saved_path = list(sys.path)
        saved_modules = {k: v for k, v in sys.modules.items() if k.startswith("el_yo")}
        try:
            for m in list(sys.modules):
                if m.startswith("el_yo"):
                    del sys.modules[m]
            sys.path[:] = [p for p in sys.path
                           if p != "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO"]
            elyo_wiring.EL_YO_GOBIERNO = "/nonexistent/elyo"
            with self.assertRaises(ElyoGateUnavailable) as cm:
                elyo_wiring._load_elyo_gate()
            self.assertIn("BLOQUEO REGISTRADO", str(cm.exception))
        finally:
            sys.path[:] = saved_path
            sys.modules.update(saved_modules)
            elyo_wiring.EL_YO_GOBIERNO = "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO"


if __name__ == "__main__":
    unittest.main()
