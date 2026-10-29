"""Modulo de paquete rtpkg — reorganizacion del Agent Runtime (baseline-safe)."""
from __future__ import annotations
import json, hashlib
import sys

for _p in ("/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO",
           "/mnt/agents/output/EL_YO/05_RAZONAMIENTO",
           "/mnt/agents/output/EL_YO/02_MEMORIA",
           "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA",
           "/mnt/agents/output/EL_YO/23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION",
           "/mnt/agents/output/EL_YO/17_SOVEREIGNTY"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ROUTES = ("DETERMINISTIC", "LOCAL_MODEL", "GPT-4o", "HUMAN_APPROVAL")
UNIT_COSTS = {"DETERMINISTIC": 0.0, "LOCAL_MODEL": 0.001, "GPT-4o": 0.02,
              "HUMAN_APPROVAL": 0.0}
PUBLIC_IDENTITIES = ("EL_YO", "ELLA")

def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()

from el_yo.constitution import Denied

class RuntimeError_(Exception):
    code = "RUNTIME_ERROR"


class CapabilityDenied(RuntimeError_):
    code = "CAPABILITY_DENIED"


class BudgetExceeded(RuntimeError_):
    code = "BUDGET_EXCEEDED"


class CircuitOpen(RuntimeError_):
    code = "CIRCUIT_OPEN"


class TimeoutError_(RuntimeError_):
    code = "TIMEOUT"




