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

from contracts import *
from contracts import _canon, UNIT_COSTS
from security_resources import ValueResourceEconomics, TaskBudget
from self_awareness import Metacognition

class LocalModelStub:
    """LOCAL_MODEL determinista reproducible (placeholder honesto).
    Sustitucion por Ollama/OpenFang: BLOCKED (vendoring, sin red)."""

    def generate(self, task: dict) -> dict:
        h = hashlib.sha256(_canon(task.get("payload", {}))).hexdigest()
        resolved = task.get("kind") in ("classify", "draft", "analyze")
        return {"output": f"local:{h[:12]}", "tokens_out": 1 + len(h) // 16,
                "resolved": resolved, "model": "local-stub-deterministic"}


# ============ InfrastructureRecovery ============
class ModelRouter:
    """DETERMINISTIC -> LOCAL_MODEL -> GPT-4o -> HUMAN_APPROVAL.
    Evita llamadas LLM innecesarias: si la regla determinista resuelve, no se
    sube de nivel. GPT-4o: BLOCKED (sin red/clave; no inventado) -> HUMAN_APPROVAL."""

    def __init__(self, economics: ValueResourceEconomics, local_model=None,
                 ledger: EvidenceLedger | None = None):
        self.econ = economics
        self.local_model = local_model or LocalModelStub()
        self.ledger = ledger
        self.meta = Metacognition()

    def deterministic_rule(self, task: dict):
        """Reglas deterministas puras. Devuelve respuesta o None (subir de nivel)."""
        kind = task.get("kind")
        if kind == "ping":
            return {"result": "pong", "route_used": "DETERMINISTIC"}
        if kind == "echo":
            return {"result": task.get("payload"), "route_used": "DETERMINISTIC"}
        if kind == "sum":
            vals = task.get("payload", [])
            return {"result": sum(vals), "route_used": "DETERMINISTIC"}
        if kind == "constitution_check":
            return {"result": "checked", "route_used": "DETERMINISTIC"}
        if kind == "reflect_questions":
            n = len(task.get("payload", {}).get("stages", []))
            return {"result": f"questions_ready:{n}_stages",
                    "route_used": "DETERMINISTIC"}   # metacognicion estructurada: sin LLM
        if kind == "perceive_ingest":
            return {"result": "perception_route_ok", "route_used": "DETERMINISTIC"}
        return None

    def route(self, task: dict, budget: TaskBudget) -> dict:
        tid = task["task_id"]
        det = self.deterministic_rule(task)
        if det is not None:
            budget.charge(UNIT_COSTS["DETERMINISTIC"])
            self.econ.record(tid, "DETERMINISTIC", 1.0, "regla pura; sin LLM")
            return {**det, "levels_used": ["DETERMINISTIC"]}
        # LOCAL_MODEL (stub determinista; Ollama/OpenFang = BLOCKED vendoring)
        budget.charge(UNIT_COSTS["LOCAL_MODEL"])
        lm = self.local_model.generate(task)
        self.econ.record(tid, "LOCAL_MODEL", 1.0, f"tokens_out={lm['tokens_out']}")
        if lm.get("resolved"):
            return {"result": lm["output"], "route_used": "LOCAL_MODEL",
                    "levels_used": ["DETERMINISTIC", "LOCAL_MODEL"]}
        # GPT-4o: BLOCKED en este entorno (sin red/clave). No se inventa API.
        self.econ.record(tid, "GPT-4o", 0.0, "BLOCKED: provider no disponible")
        if self.ledger:
            self.ledger.append({"type": "runtime_route_blocked",
                                "task_id": tid, "route": "GPT-4o",
                                "reason": "sin red/clave; no inventado"})
        # HUMAN_APPROVAL (la unica salida para lo no resoluble aqui)
        return {"result": None, "route_used": "HUMAN_APPROVAL",
                "levels_used": ["DETERMINISTIC", "LOCAL_MODEL", "GPT-4o", "HUMAN_APPROVAL"],
                "pending": task.get("payload")}
