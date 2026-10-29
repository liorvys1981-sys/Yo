import sys; sys.path.insert(0, "/mnt/agents/output/EL_YO/19_GOVERNANCE")
import json, unittest, tempfile, os
from state_engine import StateEngine, StateError


def mk(tmp):
    p = os.path.join(tmp, "AREA.json")
    with open(p, "w") as f:
        json.dump({"components": {
            "webhook_gateway": {"state": "IMPLEMENTED"},
            "saos_v17": {"state": "NOT_IMPLEMENTED"},
            "nodo_gpu": {"state": "HARDWARE_DEPENDENT"},
            "nube": {"state": "DOCUMENTATION_ONLY"}}}, f)
    return p


class TestEstados(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.eng = StateEngine(mk(self.tmp))

    def test_valida(self):
        r = self.eng.transition("saos_v17", "BLOCKED", evidence="fuente no disponible")
        self.assertEqual(r["to"], "BLOCKED")

    def test_prohibida_doc_a_complete(self):
        with self.assertRaises(StateError):
            self.eng.transition("nube", "COMPLETE", evidence="sin pruebas")

    def test_estado_desconocido(self):
        with self.assertRaises(StateError):
            self.eng.transition("nube", "FANTASMA", evidence="x")

    def test_hw_a_implemented(self):
        self.assertEqual(self.eng.transition("nodo_gpu", "IMPLEMENTED",
                                             evidence="GPU instalada")["to"], "IMPLEMENTED")

    def test_persistencia(self):
        self.eng.transition("webhook_gateway", "COMPLETE", evidence="23/23 PASS")
        self.assertEqual(StateEngine(self.eng.path).get("webhook_gateway")["state"], "COMPLETE")

    def test_complete_terminal(self):
        self.eng.transition("webhook_gateway", "COMPLETE", evidence="ok")
        with self.assertRaises(StateError):
            self.eng.transition("webhook_gateway", "PARTIAL", evidence="x")


if __name__ == "__main__":
    unittest.main()
