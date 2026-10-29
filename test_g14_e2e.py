"""G14 END-TO-END — flujo completo del Cognitive Twin en un solo test integral.

experiencias -> reflection -> insights -> evolucion (gate real EL_YO)
-> versionado -> memoria persistente -> swarm -> export soberano -> verificacion
-> tamper detectado. Composicion de G2-G12 sin nuevas capacidades.
"""
import os, sys, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')

from digital_self import DigitalSelf
from genome_store import GenomeStore
from pipeline_evolution import EvolutionPipeline
from elyo_wiring import make_elyo_gate, elyo_code
from reflection import reflect
from insights import InsightTracker
from persistent_memory import PersistentMemoryStore
from swarm import Swarm
from sovereignty import TwinExporter, TwinVerifier, HashMismatch
from identity import Identity
from authority import Authority
from authority import Authority

KEY = b"g" * 32
TODAY = "2026-10-07"


class TestE2ECompleto(unittest.TestCase):
    def test_flujo_completo_del_gemelo(self):
        tmp = tempfile.mkdtemp()
        led_path = os.path.join(tmp, "ledger.jsonl")

        # G2: DigitalSelf
        ds = DigitalSelf("subj-e2e", "tenant-e2e")
        for k in ("Identity", "Values", "Beliefs", "Goals", "Traits", "Relationships", "Experiences"):
            ds.create(k)

        # G3: GenomeStore + ledger
        E2E_AUTH = Identity(seed=b"a" * 32)
        store = GenomeStore(tmp, led_path, authority_did=E2E_AUTH.did, today=TODAY)

        # G5: memoria persistente con experiencias
        pmem = PersistentMemoryStore(tmp, led_path)
        exp_ids = []
        for i in range(1, 6):
            mid = pmem.store("tenant-e2e", "subj-e2e", "ci-1", "EPISODIC",
                             {"evento": f"lectura sesion {i}"}, "OBSERVED", 0.9,
                             (f"ev:{i}",), "diario")
            exp_ids.append(mid)
        experiences = [{"id": m, "domain": "habitos", "key": "lectura",
                        "value": "hecha", "provenance": "OBSERVED", "ts": float(i)}
                       for i, m in enumerate(exp_ids, 1)]

        # G6: reflection
        insights_g6 = reflect(experiences, expected_domains=("finanzas",))
        self.assertIn("PATTERN", {i.type for i in insights_g6})
        self.assertIn("BLIND_SPOT", {i.type for i in insights_g6})

        # G10: insights cycle
        tracker = InsightTracker(ledger=store.ledger, clock=lambda: 777.0)
        tracked = tracker.register_reflection_outputs(insights_g6)
        hyp = [i for i in tracked if i.type == "HYPOTHESIS"][0]
        CTX = __import__("cognitive_api").RequestContext(
            "tenant-e2e", "subj-e2e", "ci-1", "scope", "auth")
        tracker.state_change(CTX, hyp.id, "CONFIRMED", ("ev:verif",), confirmed_by="humano")

        # G9: swarm con 6 agentes
        swarm = Swarm(ledger=store.ledger, clock=lambda: 778.0)
        for name, caps in [("reflection", ["synthesize"]), ("pattern", ["correlate"]),
                           ("memory", ["consolidate"]), ("identity", ["propose_genome_change"]),
                           ("future", ["build_scenario"]), ("safety", ["veto"])]:
            swarm.spawn(f"ag-{name}", name, f"p {name}", caps)
        for i in range(3):
            swarm.record_correct_execution("ag-reflection", f"ev:{i}")
        self.assertEqual(swarm.promote("ag-reflection"), "approval")

        # G8+G12: evolucion con gate real EL_YO
        gate = make_elyo_gate(KEY, TODAY, second_key=True)
        pipe = EvolutionPipeline(store, gate, clock=lambda: 779.0,
                                 authority=Authority(E2E_AUTH, gate, TODAY))
        pipe.submit("r1", ds, experiences, "Goals",
                    {"objetivo": "leer diariamente"}, "SELF_REPORTED", 0.95,
                    ("ev:pattern", hyp.id), "reflection+insights", "patron confirmado")
        pipe.review("r1", "revision e2e")
        out = pipe.approve("r1", ds, f"EJECUTA e2e {elyo_code(KEY, TODAY)}")
        self.assertEqual(out["state"], "APPLIED")
        self.assertEqual(ds.get("Goals").active.content, {"objetivo": "leer diariamente"})

        # G11: export soberano + verificacion
        pkg_root = tempfile.mkdtemp()
        exporter = TwinExporter(store, Identity(seed=b"e" * 32), clock=lambda: 780.0)
        result = exporter.export(ds, pkg_root, "exp:e2e")
        self.assertEqual(TwinVerifier.full_verify(result["path"])["status"], "VERIFIED")

        # tamper: alterar audit trail -> detectado
        import shutil
        pkg2 = os.path.join(tempfile.mkdtemp(), "tampered")
        shutil.copytree(result["path"], pkg2)
        with open(os.path.join(pkg2, "self.json")) as f:
            doc = __import__("json").load(f)
        doc["entities"]["Goals"]["versions"][0]["content"] = {"objetivo": "HACKEADO"}
        with open(os.path.join(pkg2, "self.json"), "w") as f:
            __import__("json").dump(doc, f)
        with self.assertRaises((HashMismatch,)):
            TwinVerifier.verify_hashes(pkg2)

        # ledger global verificable
        self.assertTrue(store.ledger.verify())

        # invariantes soberanos finales
        self.assertEqual(hyp.state, "CONFIRMED")
        self.assertEqual(swarm.status("ag-safety").name, "safety")
        self.assertEqual(len(ds.get("Goals").versions), 1)
        snapshot = store.load("tenant-e2e", "subj-e2e")
        self.assertTrue(snapshot.get("Goals").active.verify_integrity())


if __name__ == "__main__":
    unittest.main()
