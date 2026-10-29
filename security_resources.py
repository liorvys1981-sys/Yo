from __future__ import annotations
import hashlib, json, time
import sys
from dataclasses import dataclass, field

for _p in ("/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO",
           "/mnt/agents/output/EL_YO/05_RAZONAMIENTO"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contracts import UNIT_COSTS, BudgetExceeded, CapabilityDenied
from el_yo.constitution import Action, Denied
from el_yo.evidence import EvidenceLedger
from relationship_model import PolicyEngine

@dataclass
class TaskBudget:
    task_id: str
    max_units: float = 10.0
    spent: float = 0.0

    def charge(self, units: float):
        if self.spent + units > self.max_units:
            raise BudgetExceeded(f"{self.task_id}: {self.spent}+{units}>{self.max_units}")
        self.spent = round(self.spent + units, 6)

class ValueResourceEconomics:
    """Costo/uso por ruta, registrado. Sin costo oculto."""

    def __init__(self, ledger: EvidenceLedger | None = None, clock=None):
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.usage: list[dict] = []

    def record(self, task_id: str, route: str, units: float = 1.0, detail: str = ""):
        cost = round(units * UNIT_COSTS[route], 6)
        entry = {"task_id": task_id, "route": route, "units": units,
                 "unit_cost": UNIT_COSTS[route], "cost": cost,
                 "ts": self.clock(), "detail": detail}
        self.usage.append(entry)
        if self.ledger:
            self.ledger.append({"type": "runtime_usage", **entry})
        return cost

class ResourceManager:
    """Asigna presupuestos por tarea y rastrea uso activo (composicion de
    TaskBudget + ValueResourceEconomics; sin logica de costo duplicada)."""

    def __init__(self, economics):
        self.econ = economics
        self.active = {}

    def allocate(self, task_id, max_units=10.0):
        b = TaskBudget(task_id=task_id, max_units=max_units)
        self.active[task_id] = b
        return b

    def release(self, task_id):
        b = self.active.pop(task_id, None)
        return {"task_id": task_id, "spent": b.spent if b else 0.0}

    def usage_of(self, task_id):
        b = self.active.get(task_id)
        return b.spent if b else 0.0


# ============ ModelRouter ============

class SovereigntySecurity:
    """Zero-trust + least-privilege + constitucion. Privilegio real: R1."""

    CAPABILITIES = ("route_task", "remember", "recall", "research", "reflect", "perceive", "privileged_op")

    def __init__(self, policy: PolicyEngine, authority_did: str | None = None,
                 today: str | None = None):
        self.policy = policy
        self.authority_did = authority_did
        self.today = today
        self.grants: dict[str, set] = {}

    def grant(self, caller: str, capability: str):
        if capability not in self.CAPABILITIES:
            raise CapabilityDenied(f"capability desconocida: {capability}")
        self.grants.setdefault(caller, set()).add(capability)

    def check(self, caller: str, capability: str) -> bool:
        # zero-trust: no caller es de confianza por defecto
        return capability in self.grants.get(caller, set())

    def require(self, caller: str, capability: str):
        if not self.check(caller, capability):
            raise CapabilityDenied(f"{caller} sin capability '{capability}'")

    def privileged(self, caller: str, capability: str, authorization=None) -> bool:
        """Operacion privilegiada: capability + policy ESCALATE + autorizacion R1."""
        self.require(caller, capability)
        verdict = self.policy.evaluate(action_type="identity", domain="identity")
        if verdict != "ESCALATE":
            raise CapabilityDenied("policy no escalo como se esperaba")
        if authorization is None:
            raise Denied("operacion privilegiada exige autorizacion R1")
        sys.path.insert(0, "/mnt/agents/output/EL_YO/17_SOVEREIGNTY")
        from authority import verify_authorization, InvalidAuthorization
        try:
            verify_authorization(authorization, self.authority_did,
                                 "runtime-privileged", self.today)
        except InvalidAuthorization as e:
            raise Denied(str(e))
        return True


# ============ ResearchEvolution ============

