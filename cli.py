"""CLI el-yo: status, verify, gate-check. Integra gobierno+evidencia+estados."""
from __future__ import annotations
import argparse, json, sys

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from el_yo.evidence import EvidenceLedger, TamperedError
from el_yo.constitution import Action, Denied
from el_yo.gates import AuthorizationGate, DailyCodeProvider


def cmd_status(area_path: str) -> int:
    with open(area_path) as f:
        area = json.load(f)
    comps = area["components"]
    counts = {}
    for c in comps.values():
        counts[c["state"]] = counts.get(c["state"], 0) + 1
    for k in sorted(counts):
        print(f"{k}: {counts[k]}")
    for name, c in comps.items():
        print(f"  {name}: {c['state']}")
    return 0


def cmd_verify(ledger_path: str) -> int:
    try:
        ok = EvidenceLedger(ledger_path).verify()
    except FileNotFoundError:
        print("FAIL: ledger no encontrado"); return 1
    except TamperedError as e:
        print(f"FAIL: {e}"); return 1
    print(f"OK: cadena de evidencia integra ({ledger_path})")
    return 0


def cmd_gate_check(impact: str, actor: str, phrase, key, today, second) -> int:
    derived = (key.encode() * 32)[:32]
    g = AuthorizationGate(DailyCodeProvider(derived), today, second_key_present=second)
    try:
        r = g.authorize(Action("check", impact), actor=actor, phrase=phrase)
        print(json.dumps(r)); return 0
    except Denied as e:
        print(f"DENIED: {e}"); return 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="el-yo")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.add_argument("--area", required=True)
    v = sub.add_parser("verify"); v.add_argument("--ledger", required=True)
    g = sub.add_parser("gate-check")
    g.add_argument("--impact", required=True)
    g.add_argument("--actor", default="agente")
    g.add_argument("--phrase", default=None)
    g.add_argument("--key", default="k")
    g.add_argument("--today", default="2026-10-07")
    g.add_argument("--second-key", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "status":
        return cmd_status(a.area)
    if a.cmd == "verify":
        return cmd_verify(a.ledger)
    return cmd_gate_check(a.impact, a.actor, a.phrase, a.key, a.today, a.second_key)


if __name__ == "__main__":
    sys.exit(main())
