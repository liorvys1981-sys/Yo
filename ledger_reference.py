"""GAP-21 estructural — referencia verificable al ledger canonico (sin duplicar)."""
from __future__ import annotations
import sys

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
from el_yo.evidence import EvidenceLedger

LEDGER_DATA_PATH = "/mnt/agents/output/EL_YO/01_GOBIERNO/evidence/ledger.jsonl"


class LedgerReference:
    """Area canonica 21: verifica el ledger fisico sin crear segunda fuente."""

    def reference(self) -> dict:
        return {"engine": "00_CONSTITUCION_EL_YO/el_yo/evidence.py",
                "data_path": LEDGER_DATA_PATH,
                "duplicated": False, "single_source_of_truth": True}

    def verify_physical_chain(self) -> bool:
        return EvidenceLedger(LEDGER_DATA_PATH).verify()

    def entry_count(self) -> int:
        with open(LEDGER_DATA_PATH) as f:
            return sum(1 for _ in f)
