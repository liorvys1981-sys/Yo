"""Modulo de paquete rtpkg — reorganizacion del Agent Runtime (baseline-safe)."""
from __future__ import annotations
import hashlib, json, time
import sys

for _p in ("/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO",
           "/mnt/agents/output/EL_YO/05_RAZONAMIENTO",
           "/mnt/agents/output/EL_YO/02_MEMORIA",
           "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA",
           "/mnt/agents/output/EL_YO/23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION",
           "/mnt/agents/output/EL_YO/17_SOVEREIGNTY"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from research_engine import ResearchEngine

class ResearchEvolution:
    """Mejora propuesta via motor de investigacion (23); cambio solo G8+R1."""

    def __init__(self, engine: ResearchEngine | None = None, clock=None):
        self.engine = engine or ResearchEngine(clock=clock)
        self.clock = clock or (lambda: time.time())

    def propose_improvement(self, lens_name: str, statement: str, evidence: tuple = ()) -> dict:
        q = self.engine.formulate(lens_name, statement, f"hipotesis: {statement[:60]}")
        exp = self.engine.run_experiment(q, {"elements": {"a": statement}}, seed=0)
        ev = self.engine.evaluate(exp, "non_empty", True, evidence=evidence)
        return self.engine.evolution_proposal(ev)


# ============ CognitiveAnalytics ============
