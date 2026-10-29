import os, sys, tempfile, unittest, json
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from digital_self import DigitalSelf
from genome_store import GenomeStore
from pipeline_evolution import (EvolutionPipeline, InvalidTransition,
                                EvolutionLocked, STATES, TRANSITIONS)
from el_yo.constitution import Denied
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from authority import Authority
from identity import Identity
from authority import Authority
from identity import Identity

KEY = b"g" * 32
TODAY = "2026-10-07"
CODE = DailyCodeProvider(KEY).code(TODAY)
EXP = [
    {"id": "e1", "domain": "habitos", "key": "lectura", "value": "hecha",
     "provenance": "OBSERVED", "ts": 1.0},
    {"id": "e2", "domain": "habitos", "key": "lectura", "value": "hecha",
     "provenance": "OBSERVED", "ts": 2.0},
    {"id": "e3", "domain": "habitos", "key": "lectura", "value": "hecha",
     "provenance": "OBSERVED", "ts": 3.0},
]


AUTH_ID = Identity(seed=b"a" * 32)
def mk():
    tmp = tempfile.mkdtemp()
    gate = AuthorizationGate(DailyCodeProvider(KEY), TODAY, second_key_present=True)
    store = GenomeStore(tmp, os.path.join(tmp, "ledger.jsonl"),
                        authority_did=AUTH_ID.did, today=TODAY)
    pipe = EvolutionPipeline(store, gate, clock=lambda: 1000.0,
                             authority=Authority(AUTH_ID, gate, TODAY))
    ds = DigitalSelf("subj-1", "tenant-1")
    for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
        ds.create(k)
    return tmp, store, pipe, ds


def phrase():
    return f"EJECUTA evolucion {CODE}"


class TestPipelineCompleto(unittest.TestCase):
    def test_pipeline_happy_path(self):
        tmp, store, pipe, ds = mk()
        req = pipe.submit("r1", ds, EXP, "Goals",
                          {"objetivo": "leer 30 min"}, "SELF_REPORTED", 0.9,
                          ("ev:1",), "src", "patron lectura detectado")
        self.assertEqual(req.state, "PROPOSED")
        pipe.review("r1", "revision ok")
        self.assertEqual(req.state, "REVIEW")
        out = pipe.approve("r1", ds, phrase())
        self.assertEqual(out["state"], "APPLIED")
        self.assertEqual(ds.get("Goals").active.content, {"objetivo": "leer 30 min"})
        self.assertEqual(out["version"], 1)

    def test_todas_las_transiciones_validas_documentadas(self):
        _, _, pipe, ds = mk()
        req = pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                          ("e",), "s", "r")
        pipe.review("r1", "ok")
        pipe.approve("r1", ds, phrase())
        recorrido = [h["to"] for h in req.history]
        self.assertEqual(recorrido, ["PATTERNED", "HYPOTHESIZED", "REFLECTED",
                                     "PROPOSED", "REVIEW", "APPROVED", "APPLIED"])

    def test_transicion_invalida_rechazada(self):
        _, _, pipe, ds = mk()
        req = pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                          ("e",), "s", "r")
        with self.assertRaises(InvalidTransition):
            pipe._transition(req, "APPLIED")   # saltarse REVIEW/APPROVED

    def test_determinismo_mismo_input(self):
        _, _, pipe, ds = mk()
        a = pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                        ("e",), "s", "r")
        b = pipe.submit("r2", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                        ("e",), "s", "r")
        self.assertEqual([h["ts"] for h in a.history], [h["ts"] for h in b.history])
        self.assertEqual([h["to"] for h in a.history], [h["to"] for h in b.history])


class TestGateYFundamentales(unittest.TestCase):
    def test_identity_sin_autorizacion(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Identity", {"n": "x"}, "SELF_REPORTED", 1.0,
                    ("e",), "s", "cambio")
        pipe.review("r1", "ok")
        with self.assertRaises(Denied):
            pipe.approve("r1", ds, "frase mala")
        self.assertEqual(len(ds.get("Identity").versions), 0)

    def test_values_sin_autorizacion(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Values", {"v": "x"}, "SELF_REPORTED", 1.0,
                    ("e",), "s", "cambio")
        pipe.review("r1", "ok")
        with self.assertRaises(Denied):
            pipe.approve("r1", ds, None)
        self.assertEqual(len(ds.get("Values").versions), 0)

    def test_beliefs_sin_autorizacion(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Beliefs", {"b": "x"}, "SELF_REPORTED", 1.0,
                    ("e",), "s", "cambio")
        pipe.review("r1", "ok")
        with self.assertRaises(Denied):
            pipe.approve("r1", ds, f"EJECUTA x {'0'*12}")
        self.assertEqual(len(ds.get("Beliefs").versions), 0)

    def test_fundamental_con_autorizacion_valida(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Beliefs", {"b": "declarada"}, "SELF_REPORTED",
                    1.0, ("e",), "s", "declaracion")
        pipe.review("r1", "ok")
        out = pipe.approve("r1", ds, phrase())
        self.assertEqual(out["state"], "APPLIED")
        self.assertEqual(out["version"], 1)

    def test_gate_inalienable_en_no_fundamental(self):
        """Ningun agente salta el gate: en approve SIEMPRE se invoca gate.authorize,
        aun para kinds reversibles (que por diseno no exigen frase)."""
        _, _, pipe, ds = mk()
        llamadas = []
        original = pipe.gate.authorize
        def espia(action, actor, phrase=None):
            llamadas.append((action.kind, action.impact, actor, phrase))
            return original(action, actor, phrase)
        pipe.gate.authorize = espia
        pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "r")
        pipe.review("r1", "ok")
        out = pipe.approve("r1", ds, phrase())
        self.assertEqual(out["state"], "APPLIED")
        self.assertEqual(len(llamadas), 2)   # R1: gate en pipeline + gate en Authority
        self.assertTrue(all(l[:3] == ("Goals", "reversible_menor", "humano") for l in llamadas))


class TestLockedYRechazo(unittest.TestCase):
    def test_evolution_locked_bloquea_todo(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "r")
        pipe.lock("incidente de seguridad")
        with self.assertRaises(EvolutionLocked):
            pipe.review("r1", "intento")
        with self.assertRaises(EvolutionLocked):
            pipe.submit("r2", ds, EXP, "Goals", {"g": 2}, "SELF_REPORTED", 0.9,
                        ("e",), "s", "otro")
        pipe.unlock(phrase())
        pipe.review("r1", "ahora si")
        self.assertEqual(pipe._requests["r1"].state, "REVIEW")

    def test_rechazo_no_modifica_genome(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Goals", {"g": "malo"}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "propuesta")
        r = pipe.reject("r1", "contradice patron")
        self.assertEqual((r["state"], r["genome_untouched"]), ("REJECTED", True))
        self.assertEqual(len(ds.get("Goals").versions), 0)


class TestVersionadoYEvidencia(unittest.TestCase):
    def test_nueva_version_sin_sobrescribir(self):
        tmp, store, pipe, ds = mk()
        for i, obj in enumerate([{"g": "v1"}, {"g": "v2"}], 1):
            pipe.submit(f"r{i}", ds, EXP, "Goals", obj, "SELF_REPORTED", 0.9,
                        ("e",), "s", f"cambio {i}")
            pipe.review(f"r{i}", "ok")
            pipe.approve(f"r{i}", ds, phrase())
        g = ds.get("Goals")
        self.assertEqual((g.version(1).content, g.version(2).content,
                          g.active.content), ({"g": "v1"}, {"g": "v2"}, {"g": "v2"}))

    def test_reconstruccion_del_estado_anterior(self):
        tmp, store, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Goals", {"g": "antes"}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "v1")
        pipe.review("r1", "ok")
        out = pipe.approve("r1", ds, phrase())
        ds2 = store.load("tenant-1", "subj-1")
        self.assertEqual(ds2.reconstruct(0.0), {})           # antes de todo
        self.assertEqual(ds2.reconstruct(1e12)["Goals"]["content"], {"g": "antes"})

    def test_cada_transicion_genera_evidencia(self):
        tmp, store, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "r")
        pipe.review("r1", "ok")
        pipe.approve("r1", ds, phrase())
        eventos = []
        with open(os.path.join(tmp, "ledger.jsonl")) as f:
            for line in f:
                eventos.append(json.loads(line)["event"]["type"])
        transiciones = [e for e in eventos if e == "pipeline_transition"]
        self.assertEqual(len(transiciones), 7)   # PATTERNED,HYPOTHESIZED,REFLECTED,PROPOSED,REVIEW,APPROVED,APPLIED
        self.assertTrue(store.ledger.verify())

    def test_content_hash_en_applied(self):
        _, _, pipe, ds = mk()
        pipe.submit("r1", ds, EXP, "Goals", {"g": 1}, "SELF_REPORTED", 0.9,
                    ("e",), "s", "r")
        pipe.review("r1", "ok")
        out = pipe.approve("r1", ds, phrase())
        self.assertEqual(len(out["content_hash"]), 64)


if __name__ == "__main__":
    unittest.main()
