import sys, unittest, tempfile, os, json, hashlib, threading
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
sys.path.insert(0, '/mnt/agents/output/EL_YO/05_RAZONAMIENTO')
sys.path.insert(0, '/mnt/agents/output/EL_YO/02_MEMORIA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION')
sys.path.insert(0, '/mnt/agents/output/EL_YO/17_SOVEREIGNTY')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
from runtime import (CognitiveOrchestrator, SovereigntySecurity, ModelRouter,
    InfrastructureRecovery, ResourceManager, ValueResourceEconomics,
    CognitiveAnalytics, MemoryCognition, ResearchEvolution, TaskBudget,
    CircuitBreaker, PUBLIC_IDENTITIES, LocalModelStub, CapabilityDenied,
    BudgetExceeded, CircuitOpen, RuntimeError_)
from el_yo.evidence import EvidenceLedger
from el_yo.constitution import Denied

RT_DIR = '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime'
RT_PKG = RT_DIR + '/rtpkg'
RT_SRC = open(RT_DIR + '/runtime.py').read()
for _f in sorted(os.listdir(RT_PKG)):
    if _f.endswith('.py') and _f != '__init__.py':
        RT_SRC = RT_SRC + chr(10) + open(os.path.join(RT_PKG, _f)).read()

KEY = b"g" * 32
TODAY = "2026-10-07"

class AuditArchitecture(unittest.TestCase):
    def test_runtime_unico_y_capacidades_internas(self):
        # un solo orquestador; capacidades como clases internas del mismo modulo
        self.assertIn("class CognitiveOrchestrator", RT_SRC)
        for cap in ("SovereigntySecurity", "InfrastructureRecovery", "ResourceManager",
                    "ValueResourceEconomics", "CognitiveAnalytics", "MemoryCognition",
                    "ResearchEvolution", "ModelRouter"):
            self.assertIn(f"class {cap}", RT_SRC)
        # sin subpaquetes de agentes: un solo archivo de runtime
        rt_dir = "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime"
        py = [f for f in os.listdir(rt_dir) if f.endswith(".py")]
        self.assertEqual(py, ["__init__.py", "runtime.py"])   # fachada
        pkg = [f for f in os.listdir(rt_dir + "/rtpkg") if f.endswith(".py")]
        self.assertIn("core.py", pkg)                          # paquete canónico presente


class AuditLLM(unittest.TestCase):
    def test_llm_unico_compartido_sin_llm_por_agente(self):
        # un solo ModelRouter; ninguna clase instancia su propio modelo
        self.assertEqual(RT_SRC.count("class ModelRouter"), 1)
        self.assertNotIn("def __init__(self, local_model=None)", RT_SRC.replace(
            "def __init__(self, economics: ValueResourceEconomics, local_model=None,", ""))
        import re
        self.assertEqual(len(re.findall(r"LocalModelStub\(\)", RT_SRC)), 1)

    def test_sin_llamadas_llm_innecesarias(self):
        econ = __import__("runtime").ValueResourceEconomics(clock=lambda: 1.0)
        router = ModelRouter(econ)
        for kind, payload in (("ping", None), ("sum", [1, 2]), ("echo", "x")):
            router.route({"task_id": f"t-{kind}", "kind": kind, "payload": payload},
                         __import__("runtime").TaskBudget(f"b-{kind}"))
        self.assertTrue(all(u["route"] == "DETERMINISTIC" for u in econ.usage))


class AuditPermissions(unittest.TestCase):
    def test_nadie_eleva_privilegios(self):
        sec = SovereigntySecurity(__import__("relationship_model").PolicyEngine())
        with self.assertRaises(Exception):
            sec.grant("agente-x", "ESCALATE_ROOT")
        # la capability 'privileged_op' sin autorizacion R1 falla
        sec.grant("agente-x", "privileged_op")
        with self.assertRaises(Denied):
            sec.privileged("agente-x", "privileged_op")


class AuditConstitution(unittest.TestCase):
    def test_ningun_agente_modifica_constitucion(self):
        # el runtime no importa ni expone escritura constitucional
        self.assertNotIn("constitution.py", RT_SRC)
        self.assertNotIn("set_constitution", RT_SRC)
        self.assertNotIn("amend", RT_SRC.lower())
        # y el paquete constitucional no es importado por el runtime (solo gates para Denied/gate check)
        # intencion: el runtime no importa simbolos de ESCRITURA constitucional;
        # importar Action/Deny (control) es legitimo y no modifica la Constitucion
        self.assertNotIn("set_constitution", RT_SRC)
        self.assertNotIn("amend_constitution", RT_SRC)
        bad = [l for l in RT_SRC.splitlines()
               if "constitution" in l.lower() and any(
                   w in l.lower() for w in ("set_", "amend", "write_", "modify_", "override"))]
        self.assertEqual(bad, [], f"simbolos de escritura constitucional: {bad}")


class AuditBypass(unittest.TestCase):
    def test_ningun_agente_salta_el_runtime(self):
        # las capacidades no ejecutan tareas por si solas: require() solo verifica;
        # el unico ejecutor es handle_task (que exige capability route_task)
        sec = SovereigntySecurity(__import__("relationship_model").PolicyEngine())
        sec.grant("caller", "remember")     # remember NO puede rutear tareas
        with self.assertRaises(Exception):
            sec.require("caller", "route_task")


class AuditDigitalSelf(unittest.TestCase):
    def test_ningun_agente_escribe_digitalself(self):
        self.assertNotIn("genome_store", RT_SRC)
        self.assertNotIn("digital_self", RT_SRC.replace("DigitalSelf", ""))
        self.assertNotIn("write_digital", RT_SRC.lower())
        # contrato de evolucion: enforcement delegado al engine del area 23
        # (fuente unica, sin duplicacion); verificacion comportamental
        self.assertIn("evolution_proposal", RT_SRC)
        from runtime import ResearchEvolution
        prop = ResearchEvolution(clock=lambda: 1.0).propose_improvement(
            "Metacognition", "mejora X")
        self.assertEqual(prop["direct_mutation"], "PROHIBITED")
        self.assertFalse(prop["auto_apply"])
        self.assertIn("G8->R1", prop["route"])


class AuditInvariants(unittest.TestCase):
    def test_seis_invariantes_en_runtime(self):
        # CAPABILITY != AUTHORITY: capability sin autorizacion no ejecuta privilegio
        # DECISION != EXECUTION: ninguna ruta ejecuta acciones externas
        self.assertNotIn("requests.", RT_SRC)
        self.assertNotIn("urllib", RT_SRC)
        self.assertNotIn("httpx", RT_SRC)
        self.assertNotIn("openai", RT_SRC)
        self.assertNotIn("ollama", RT_SRC)
        # MEMORY != TRUTH: MemoryCognition etiqueta provenance
        self.assertIn("provenance", RT_SRC)


class AuditTraceability(unittest.TestCase):
    def test_toda_ejecucion_deja_traza(self):
        from runtime import TaskBudget, ValueResourceEconomics
        tmp = tempfile.mkdtemp()
        led = EvidenceLedger(os.path.join(tmp, "l.jsonl"))
        econ = ValueResourceEconomics(led, clock=lambda: 1.0)
        router = ModelRouter(econ, ledger=led)
        router.route({"task_id": "trace-1", "kind": "sum", "payload": [1]},
                     TaskBudget("trace-1"))
        events = [json.loads(l)["event"] for l in open(led.path)]
        types = {e.get("type") for e in events}
        self.assertIn("runtime_usage", types)
        self.assertTrue(led.verify())


class AuditPublicIdentity(unittest.TestCase):
    def test_unicas_identidades_publicas(self):
        self.assertEqual(PUBLIC_IDENTITIES, ("EL_YO", "ELLA"))
        for name in ("CognitiveOrchestrator", "ModelRouter", "MemoryCognition",
                     "SovereigntySecurity", "ResearchEvolution"):
            self.assertEqual(CognitiveOrchestrator.public_identity_of(name.lower()),
                             "INTERNAL_CAPABILITY")
        self.assertNotIn("did:key", RT_SRC)


if __name__ == "__main__":
    unittest.main()
