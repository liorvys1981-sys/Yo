"""AGENT RUNTIME — unitarias, integracion, adversariales, E2E."""
import sys, unittest, tempfile, os, json, hashlib
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime')
sys.path.insert(0, '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO')
sys.path.insert(0, '/mnt/agents/output/EL_YO/05_RAZONAMIENTO')
sys.path.insert(0, '/mnt/agents/output/EL_YO/02_MEMORIA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA')
sys.path.insert(0, '/mnt/agents/output/EL_YO/23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION')
sys.path.insert(0, '/mnt/agents/output/EL_YO/17_SOVEREIGNTY')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_IDENTIDAD')
sys.path.insert(0, '/mnt/agents/output/EL_YO/01_GOBIERNO')
from runtime import (CognitiveOrchestrator, SovereigntySecurity, ModelRouter,
    InfrastructureRecovery, CircuitBreaker, TaskBudget,
    ValueResourceEconomics, CognitiveAnalytics, MemoryCognition, ResearchEvolution,
    LocalModelStub, CapabilityDenied, BudgetExceeded, CircuitOpen, RuntimeError_,
    PUBLIC_IDENTITIES, UNIT_COSTS)

from el_yo.evidence import EvidenceLedger
from el_yo.constitution import Denied
from el_yo.gates import AuthorizationGate, DailyCodeProvider
from relationship_model import PolicyEngine
from identity import Identity
from authority import Authority

KEY = b"g" * 32; TODAY = "2026-10-07"
AUTH = Identity(seed=b"a" * 32)
GATE = AuthorizationGate(DailyCodeProvider(KEY), TODAY, True)
CODE = DailyCodeProvider(KEY).code(TODAY)
_canon = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
_chash = lambda o: hashlib.sha256(_canon(o)).hexdigest()


def authz(content):
    return Authority(AUTH, GATE, TODAY).authorize_action(
        "runtime-privileged", "externa_irreversible", f"EJECUTA runtime {CODE}",
        content_hash=_chash(content))



def _events(led):
    import json as _j
    return [_j.loads(l)["event"] for l in open(led.path)]

def mk_orchestrator(led=None):
    led = led or EvidenceLedger(os.path.join(tempfile.mkdtemp(), "l.jsonl"))
    econ = ValueResourceEconomics(led, clock=lambda: 1.0)
    sec = SovereigntySecurity(PolicyEngine(), AUTH.did, TODAY)
    rt = CognitiveOrchestrator(
        sec, ModelRouter(econ, ledger=led), InfrastructureRecovery(clock=lambda: 1.0),
        MemoryCognition(), ResearchEvolution(clock=lambda: 1.0),
        CognitiveAnalytics(econ), ledger=led, clock=lambda: 1.0)
    return rt, sec, econ, led


class UnitRouting(unittest.TestCase):
    def test_deterministic_evita_llm(self):
        rt, sec, econ, led = mk_orchestrator()
        sec.grant("ops", "route_task")
        r = rt.handle_task("ops", {"task_id": "u1", "kind": "sum", "payload": [1, 2, 3]})
        self.assertEqual(r["result"]["result"], 6)
        self.assertEqual(r["result"]["route_used"], "DETERMINISTIC")
        routes = [u["route"] for u in econ.usage]
        self.assertEqual(routes, ["DETERMINISTIC"])   # sin llamadas LLM innecesarias

    def test_local_model_resuelve(self):
        rt, sec, econ, led = mk_orchestrator()
        sec.grant("ops", "route_task")
        r = rt.handle_task("ops", {"task_id": "u2", "kind": "classify",
                                   "payload": {"doc": "x"}})
        self.assertEqual(r["result"]["route_used"], "LOCAL_MODEL")
        self.assertIn("local:", r["result"]["result"])

    def test_gpt4o_blocked_escala_humano(self):
        rt, sec, econ, led = mk_orchestrator()
        sec.grant("ops", "route_task")
        r = rt.handle_task("ops", {"task_id": "u3", "kind": "unknown_kind",
                                   "payload": {"x": 1}})
        res = r["result"]
        self.assertEqual(res["route_used"], "HUMAN_APPROVAL")
        self.assertIn("GPT-4o", res["levels_used"])
        blocked = [e for e in _events(led) if e.get("type") == "runtime_route_blocked"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["route"], "GPT-4o")

    def test_costos_registrados(self):
        rt, sec, econ, led = mk_orchestrator()
        sec.grant("ops", "route_task")
        rt.handle_task("ops", {"task_id": "c1", "kind": "sum", "payload": [1]})
        rt.handle_task("ops", {"task_id": "c2", "kind": "classify", "payload": {"a": 1}})
        a = CognitiveAnalytics(econ).summary()
        self.assertEqual(a["routes"]["DETERMINISTIC"]["cost"], 0.0)
        self.assertEqual(a["routes"]["LOCAL_MODEL"]["cost"], 0.001)
        self.assertGreater(a["total_cost"], 0.0)


class UnitRecovery(unittest.TestCase):
    def test_idempotencia(self):
        rec = InfrastructureRecovery(clock=lambda: 1.0)
        t = {"task_id": "i1", "kind": "sum", "payload": [1]}
        r1 = rec.execute(t, lambda x: 42)
        r2 = rec.execute(t, lambda x: 999)
        self.assertEqual(r1["result"], 42)
        self.assertTrue(r2["idempotent_skip"])

    def test_retries_y_timeout(self):
        rec = InfrastructureRecovery(clock=lambda: 1.0)
        n = {"i": 0}
        def flaky(t):
            n["i"] += 1
            if n["i"] < 3: raise ValueError("fallo")
            return "ok"
        r = rec.execute({"task_id": "r1"}, flaky, retries=3)
        self.assertEqual(r["result"], "ok")
        self.assertEqual(r["attempts"], 3)
        with self.assertRaises(RuntimeError_):
            rec.execute({"task_id": "r2"}, lambda t: 1 / 0, retries=2)

    def test_circuit_breaker(self):
        cb = CircuitBreaker(threshold=2)
        with self.assertRaises(ZeroDivisionError):
            cb.call(lambda: 1 / 0)
        with self.assertRaises(ZeroDivisionError):
            cb.call(lambda: 1 / 0)
        with self.assertRaises(CircuitOpen):
            cb.call(lambda: 1)
        cb.reset()
        self.assertEqual(cb.call(lambda: 7), 7)


class UnitMemoryResearch(unittest.TestCase):
    def test_memory_cognition(self):
        mc = MemoryCognition()
        mc.remember("m1", "el runtime registra uso por ruta", provenance="SYSTEM_DERIVED")
        hits = mc.recall("uso por ruta")
        self.assertEqual(hits[0]["memory_id"], "m1")
        self.assertEqual(hits[0]["metadata"]["tenant_id"], "EL_YO")

    def test_research_evolution_solo_propuesta(self):
        re_ = ResearchEvolution(clock=lambda: 1.0)
        p = re_.propose_improvement("Metacognition", "reducir llamadas LLM", evidence=("e",))
        self.assertEqual(p["direct_mutation"], "PROHIBITED")
        self.assertIn("G8->R1", p["route"])


class IntegrationE2E(unittest.TestCase):
    def test_e2e_pipeline_con_ledger(self):
        rt, sec, econ, led = mk_orchestrator()
        for c in ("route_task", "remember", "research"):
            sec.grant("operator-1", c)
        r1 = rt.handle_task("operator-1", {"task_id": "e2e-1", "kind": "ping"})
        self.assertEqual(r1["result"]["result"], "pong")
        rt.memory.remember("w1", "presupuesto del task e2e-1")
        self.assertTrue(led.verify())
        events = [e for e in _events(led) if e.get("type") in ("runtime_task", "runtime_usage")]
        self.assertGreaterEqual(len(events), 2)

    def test_privileged_op_requiere_r1(self):
        rt, sec, econ, led = mk_orchestrator()
        sec.grant("rootish", "privileged_op")
        with self.assertRaises(Denied):
            sec.privileged("rootish", "privileged_op")   # sin autorizacion
        ok = sec.privileged("rootish", "privileged_op",
                            authorization=authz({"op": "rotate"}))
        self.assertTrue(ok)
        bad = Authority(Identity(seed=b"z" * 32), GATE, TODAY).authorize_action(
            "runtime-privileged", "externa_irreversible", f"EJECUTA runtime {CODE}",
            content_hash=_chash({"op": "rotate"}))
        with self.assertRaises(Denied):
            sec.privileged("rootish", "privileged_op", authorization=bad)


class Adversarial(unittest.TestCase):
    def test_caller_sin_capability_denied(self):
        rt, sec, econ, led = mk_orchestrator()
        with self.assertRaises(CapabilityDenied):
            rt.handle_task("desconocido", {"task_id": "a1", "kind": "ping"})

    def test_zero_trust_default_deny(self):
        sec = SovereigntySecurity(PolicyEngine())
        for cap in sec.CAPABILITIES:
            self.assertFalse(sec.check("cualquiera", cap))

    def test_capability_desconocida_denied(self):
        sec = SovereigntySecurity(PolicyEngine())
        with self.assertRaises(CapabilityDenied):
            sec.grant("x", "ESCALATE_ROOT")

    def test_budget_exceeded(self):
        b = TaskBudget("t", max_units=0.0005)
        with self.assertRaises(BudgetExceeded):
            b.charge(UNIT_COSTS["LOCAL_MODEL"])

    def test_identidades_publicas_unicas(self):
        self.assertEqual(PUBLIC_IDENTITIES, ("EL_YO", "ELLA"))
        self.assertEqual(CognitiveOrchestrator.public_identity_of("EL_YO"), "EL_YO")
        self.assertEqual(CognitiveOrchestrator.public_identity_of("ELLA"), "ELLA")
        self.assertEqual(CognitiveOrchestrator.public_identity_of("orchestrator-1"),
                         "INTERNAL_CAPABILITY")
        self.assertEqual(CognitiveOrchestrator.public_identity_of("router"), "INTERNAL_CAPABILITY")
        # ninguna capacidad del runtime tiene DID publico
        import runtime
        self.assertNotIn("did:key", open(runtime.__file__).read().split("class CognitiveOrchestrator")[0])

    def test_local_model_determinista(self):
        lm = LocalModelStub()
        a = lm.generate({"kind": "classify", "payload": {"d": 1}})
        b = lm.generate({"kind": "classify", "payload": {"d": 1}})
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
