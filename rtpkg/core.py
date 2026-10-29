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

from contracts import PUBLIC_IDENTITIES
from security_resources import TaskBudget


class CognitiveOrchestrator:
    """Orquestador unico del runtime. Ninguna capacidad es identidad publica."""

    def __init__(self, security: SovereigntySecurity, router: ModelRouter,
                 recovery: InfrastructureRecovery, memory: MemoryCognition,
                 research: ResearchEvolution, analytics: CognitiveAnalytics,
                 ledger: EvidenceLedger | None = None, clock=None):
        self.security, self.router = security, router
        self.recovery, self.memory = recovery, memory
        self.research, self.analytics = research, analytics
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())

    def handle_task(self, caller: str, task: dict, authorization=None) -> dict:
        tid = task.get("task_id", f"t:{self.clock()}")
        self.security.require(caller, "route_task")
        budget = TaskBudget(task_id=tid, max_units=task.get("budget", 10.0))
        out = self.recovery.execute(
            task, lambda t: self.router.route({**t, "task_id": tid}, budget),
            breaker=task.get("breaker"))
        if self.ledger:
            self.ledger.append({"type": "runtime_task", "task_id": tid,
                                "caller": caller, "route": out["result"]["route_used"]
                                if out["result"] else "ERROR",
                                "result_hash": hashlib.sha256(
                                    str(out).encode()).hexdigest()[:16],
                                "ts": self.clock()})
        return {"task_id": tid, "caller": caller, **out}

    @staticmethod
    def public_identity_of(caller: str) -> str:
        """Las capacidades del runtime son internas: solo EL_YO/ELLA son publicas."""
        return caller if caller in PUBLIC_IDENTITIES else "INTERNAL_CAPABILITY"
