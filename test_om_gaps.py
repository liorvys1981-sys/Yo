import sys, unittest, tempfile, time
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from observability import Observability
from chat import ChatPipeline
from web_tools import WebToolRegistry
from relationship_model import PolicyEngine
from vector_memory import SemanticMemoryIndex, MemoryRetriever
from realtime import RealtimeSession


class TestObservability(unittest.TestCase):
    def test_correlation_reconstruct(self):
        o = Observability("test")
        c = o.correlation.id
        o.logger.log("INFO", "chat", "user_message", c, session="s1")
        o.logger.log("INFO", "memory", "retrieve", c, query="q")
        o.logger.log("INFO", "decision", "policy", c, verdict="ALLOW")
        o.metrics.inc("requests"); o.metrics.observe("op", 0.05)
        trace = o.reconstruct(c)
        self.assertEqual(len(trace), 3)
        self.assertEqual(o.metrics.snapshot()["counters"]["requests"], 1)

    def test_no_secretos_no_reasoning(self):
        o = Observability("t")
        c = o.correlation.id
        ev = o.logger.log("INFO", "x", "m", c, api_token="abc123", password="x")
        self.assertEqual(ev["fields"]["api_token"], "[REDACTED]")
        self.assertEqual(ev["fields"]["password"], "[REDACTED]")
        with self.assertRaises(ValueError):
            o.logger.log("DEBUG", "x", "m", c, chain_of_thought="privado")

    def test_health_checks(self):
        o = Observability("t")
        o.health.register("ledger", lambda: True)
        o.health.register("memory", lambda: False)
        o.health.register("boom", lambda: 1 / 0)
        r = o.health.run_all()
        self.assertEqual((r["ledger"]["status"], r["memory"]["status"], r["boom"]["status"]),
                         ("OK", "DEGRADED", "FAIL"))

    def test_audit_events(self):
        o = Observability("t")
        o.audit.record("memory.write", "twin", "mem:1", o.correlation.id, True)
        evs = o.reconstruct(o.correlation.id)
        self.assertEqual(evs[-1]["level"], "AUDIT")


class TestChat(unittest.TestCase):
    def test_pipeline_flow(self):
        idx = SemanticMemoryIndex()
        idx.index("m1", "valoro la libertad",
                  {"tenant_id": "YO", "owner_id": "yo", "provenance": "SELF_REPORTED",
                   "timestamp": 1.0, "confidence": 0.9})
        chat = ChatPipeline(twin=object(), policy=PolicyEngine(),
                            retriever=MemoryRetriever(idx))
        r = chat.handle("s1", "que valoro?", correlation_id="c1")
        self.assertIn("[twin]", r["response"])
        self.assertEqual(r["policy"], "ALLOW")
        self.assertEqual(r["context_labels"]["SELF_REPORTED"], 1)

    def test_no_parallel_bot(self):
        src = open("/mnt/agents/output/EL_YO/10_INTERACCION/chat.py").read()
        self.assertIn("Cognitive Twin", src)
        self.assertNotIn("openai", src.lower())
        self.assertNotIn("ollama", src.lower())


class TestWebTools(unittest.TestCase):
    def test_declared_scoped_authorized_audited(self):
        reg = WebToolRegistry(PolicyEngine())
        reg.declare("buscador", "https://api.x/search", permission="user",
                    scope=("analysis",), risk="LOW")
        with self.assertRaises(PermissionError):
            reg.call("shell", "analysis", {})
        with self.assertRaises(PermissionError):
            reg.call("buscador", "external_action", {})
        r = reg.call("buscador", "analysis", {"q": "x"}, actor="yo-twin")
        self.assertTrue(r["executed"])
        self.assertEqual(len(reg.audit), 3)   # not_declared + scope denial + allow


class TestTemporalMemory(unittest.TestCase):
    def test_retrieve_temporal(self):
        idx = SemanticMemoryIndex()
        for i, ts in enumerate((100.0, 200.0, 300.0)):
            idx.index(f"m{i}", f"evento {i}",
                      {"tenant_id": "YO", "owner_id": "yo", "provenance": "OBSERVED",
                       "timestamp": ts, "confidence": 0.5})
        r = MemoryRetriever(idx)
        hits = r.retrieve_temporal("evento", "YO", "yo", 150.0, 350.0)
        self.assertEqual([h["memory_id"] for h in hits], ["m1", "m2"])
        self.assertEqual(r.retrieve_temporal("evento", "YO", "yo", 0.0, 50.0), [])


class TestRealtimeReconnect(unittest.TestCase):
    def test_reconnect_resume(self):
        s = RealtimeSession("s1")
        s.send({"n": 1}, correlation_id="c1")
        s.send({"n": 2}, correlation_id="c2")
        s.ack()
        s.send({"n": 3})
        pending = s.reconnect()
        self.assertEqual([e["n"] for e in pending], [3])
        self.assertEqual(s.reconnect(), [])   # idempotente tras ack
        self.assertEqual(s.correlation_ids, ["c1", "c2"])
