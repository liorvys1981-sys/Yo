import json, os, subprocess, sys, tempfile, unittest

BASE = "/mnt/agents/output/EL_YO"
GOB = f"{BASE}/00_CONSTITUCION_EL_YO"


def run_cli(*args):
    return subprocess.run([sys.executable, "-c",
        f"import sys; sys.path.insert(0,'{GOB}'); sys.path.insert(0,'{BASE}/20_AUDIT'); from cli import main; sys.exit(main())"]
        + list(args), capture_output=True, text=True)


class TestCLI(unittest.TestCase):
    def test_status(self):
        area = os.path.join(tempfile.mkdtemp(), "AREA.json")
        json.dump({"components": {"x": {"state": "IMPLEMENTED"}, "y": {"state": "NOT_IMPLEMENTED"}}},
                  open(area, "w"))
        r = run_cli("status", "--area", area)
        self.assertEqual(r.returncode, 0)
        self.assertIn("IMPLEMENTED: 1", r.stdout)

    def test_verify_ok(self):
        sys.path.insert(0, GOB)
        from el_yo.evidence import EvidenceLedger
        led = EvidenceLedger(os.path.join(tempfile.mkdtemp(), "l.jsonl"))
        led.append({"e": 1})
        r = run_cli("verify", "--ledger", led.path)
        self.assertEqual((r.returncode, "OK" in r.stdout), (0, True))

    def test_verify_tamper(self):
        sys.path.insert(0, GOB)
        from el_yo.evidence import EvidenceLedger
        p = os.path.join(tempfile.mkdtemp(), "l.jsonl")
        EvidenceLedger(p).append({"e": 1})
        lines = open(p).readlines()
        lines[0] = lines[0].replace('"e": 1', '"e": 2')
        open(p, "w").writelines(lines)
        r = run_cli("verify", "--ledger", p)
        self.assertEqual(r.returncode, 1)

    def test_gate_check_allow(self):
        sys.path.insert(0, GOB)
        from el_yo.gates import DailyCodeProvider
        code = DailyCodeProvider(b"k" * 32).code("2026-10-07")
        r = run_cli("gate-check", "--impact", "externa_irreversible",
                    "--actor", "humano", "--phrase", f"AUTORIZA pago {code}",
                    "--today", "2026-10-07")
        self.assertEqual(r.returncode, 0)

    def test_gate_check_deny_destructiva(self):
        sys.path.insert(0, GOB)
        from el_yo.gates import DailyCodeProvider
        code = DailyCodeProvider(b"k" * 32).code("2026-10-07")
        r = run_cli("gate-check", "--impact", "destructiva",
                    "--actor", "humano", "--phrase", f"AUTORIZA purga {code}",
                    "--today", "2026-10-07")  # sin --second-key
        self.assertEqual((r.returncode, "DENIED" in r.stdout), (1, True))


if __name__ == "__main__":
    unittest.main()
