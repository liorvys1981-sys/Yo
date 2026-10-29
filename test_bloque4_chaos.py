import json, hashlib, threading, unittest, tempfile, os, sys
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from el_yo.evidence import EvidenceLedger, TamperedError


class TestChaos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.led = EvidenceLedger(os.path.join(self.tmp, "l.jsonl"))

    def test_corte_mid_write_detectado(self):
        self.led.append({"evento": 1})
        with open(self.led.path, "a") as f:
            f.write('{"ts": 1, "evento": 2, "prev": "roto"')
        with self.assertRaises((TamperedError, json.JSONDecodeError)):
            self.led.verify()

    def test_restart_preserva_cadena(self):
        e1 = self.led.append({"n": 1})
        e2 = EvidenceLedger(self.led.path).append({"n": 2})
        self.assertEqual(e2["prev"], e1["hash"])
        self.assertTrue(EvidenceLedger(self.led.path).verify())

    def test_concurrencia_50_threads_integridad(self):
        def worker(i):
            EvidenceLedger(self.led.path).append({"worker": i})
        ts = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertTrue(self.led.verify())

    def test_tamper_linea_8(self):
        for i in range(10):
            self.led.append({"i": i})
        lines = open(self.led.path).readlines()
        lines[7] = lines[7].replace('"i": 7', '"i": 99')
        open(self.led.path, "w").writelines(lines)
        with self.assertRaises(TamperedError):
            self.led.verify()

    def test_determinismo_hash_canonical(self):
        e1 = self.led.append({"b": 2, "a": 1})
        canon = json.dumps({"event": {"a": 1, "b": 2}, "prev": "GENESIS", "ts": e1["ts"]},
                           sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(b"GENESIS" + canon).hexdigest(), e1["hash"])


if __name__ == "__main__":
    unittest.main()
