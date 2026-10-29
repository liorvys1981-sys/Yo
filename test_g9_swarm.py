import os, sys, tempfile, unittest
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
from swarm import (Swarm, Agent, UnknownCapability, TrustRampViolation,
    SafetyImmutable, TRUST_LEVELS, KNOWN_CAPABILITIES)


def mk(tmp=None):
    ledger = None
    if tmp:
        from el_yo.evidence import EvidenceLedger
        ledger = EvidenceLedger(os.path.join(tmp, "ledger.jsonl"))
    return Swarm(ledger=ledger, clock=lambda: 300.0)


class TestSpawnYManifest(unittest.TestCase):
    def test_spawn_ok(self):
        s = mk()
        a = s.spawn("ag1", "reflection", "sintetizar", ["synthesize"],
                    limits=("no_writes",), memory_scope="EXP", tools=("llm",))
        self.assertEqual((a.trust, a.active), ("shadow", True))

    def test_capacidad_desconocida_rechazada(self):
        s = mk()
        with self.assertRaises(UnknownCapability):
            s.spawn("ag1", "reflection", "x", ["robar_datos"])

    def test_duplicado_rechazado(self):
        s = mk()
        s.spawn("ag1", "memory", "x", ["consolidate"])
        with self.assertRaises(Exception):
            s.spawn("ag1", "memory", "y", ["consolidate"])

    def test_status_y_revoke(self):
        s = mk()
        s.spawn("ag1", "pattern", "x", ["correlate"])
        self.assertTrue(s.check("ag1", "correlate"))
        self.assertFalse(s.check("ag1", "veto"))
        s.revoke("ag1")
        self.assertFalse(s.check("ag1", "correlate"))

    def test_los_6_agentes_del_spec_spawnables(self):
        s = mk()
        for name, caps in KNOWN_CAPABILITIES.items():
            s.spawn(f"ag-{name}", name, f"proposito {name}", sorted(caps)[:1])
        self.assertEqual(len(s._agents), 6)


class TestTrustRamp(unittest.TestCase):
    def test_promocion_exige_evidencia(self):
        s = mk()
        s.spawn("ag1", "reflection", "x", ["synthesize"])
        with self.assertRaises(TrustRampViolation):
            s.promote("ag1")

    def test_promocion_con_evidencia(self):
        s = mk()
        s.spawn("ag1", "reflection", "x", ["synthesize"])
        for i in range(3):
            s.record_correct_execution("ag1", f"ev:{i}")
        self.assertEqual(s.promote("ag1"), "approval")
        for i in range(5):
            s.record_correct_execution("ag1", f"ev:ap{i}")
        self.assertEqual(s.promote("ag1"), "autonomous")
        with self.assertRaises(TrustRampViolation):
            s.promote("ag1")

    def test_incidente_degrada(self):
        s = mk()
        s.spawn("ag1", "reflection", "x", ["synthesize"])
        for i in range(3):
            s.record_correct_execution("ag1", f"e:{i}")
        s.promote("ag1")
        s.report_incident("ag1", "alucinacion detectada")
        self.assertEqual(s.status("ag1").trust, "shadow")

    def test_safety_inmutable_para_agentes(self):
        s = mk()
        s.spawn("safe1", "safety", "proteger", ["veto"])
        with self.assertRaises(SafetyImmutable):
            s.modify_safety_rules("safe1", {"limits": ("nada",)})
        s.modify_safety_rules("safe1", {"limits": ("v2",)}, human_confirmed=True)
        self.assertEqual(s.status("safe1").limits, ("v2",))

    def test_auditoria_en_ledger(self):
        tmp = tempfile.mkdtemp()
        s = mk(tmp)
        s.spawn("ag1", "memory", "x", ["consolidate"])
        for i in range(3):
            s.record_correct_execution("ag1", f"e:{i}")
        s.promote("ag1")
        tipos = []
        with open(os.path.join(tmp, "ledger.jsonl")) as f:
            for line in f:
                tipos.append(__import__("json").loads(line)["event"]["event"])
        self.assertIn("spawn", tipos)
        self.assertIn("promote", tipos)
        self.assertTrue(s.ledger.verify())


class TestGuardNoEscritura(unittest.TestCase):
    def test_swarm_no_importa_digital_self(self):
        src = open("/mnt/agents/output/EL_YO/08_AGENCIA/swarm.py").read()
        for banned in ("digital_self", "genome_store", "pipeline_evolution"):
            self.assertNotIn(f"import {banned}", src)
            self.assertNotIn(f"from {banned}", src)


if __name__ == "__main__":
    unittest.main()
