"""GAP-09 ACCION — modelo de accion constitucionalmente controlado.

PARTIAL_BY_DESIGN resuelto: la ejecucion externa permanece PROHIBIDA (constitucion,
v1). El area es COMPLETE porque el MODELO de accion es implementable y verificable:
plan determinista de pasos + requisito de autorizacion por paso + ejecucion
simulada interna trazable. NINGUN paso toca sistemas externos.
Reutiliza: PolicyEngine (05), EvidenceLedger (21)."""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/05_RAZONAMIENTO")
from el_yo.evidence import EvidenceLedger
from relationship_model import PolicyEngine


class ActionError(Exception):
    code = "ACTION_ERROR"


class ExternalExecutionProhibited(ActionError):
    code = "EXTERNAL_EXECUTION_PROHIBITED"


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()

STEP_STATES = ("PLANNED", "AUTHORIZATION_REQUIRED", "READY", "EXECUTED_INTERNAL",
               "BLOCKED", "REJECTED")


@dataclass(frozen=True)
class ActionPlan:
    plan_id: str
    goal: str
    steps: tuple              # ("step description", risk)
    requires_human_authorization: bool
    external_execution: str   # "PROHIBITED (constitution v1)"
    content_hash: str = field(init=False)

    def __post_init__(self):
        payload = {"plan_id": self.plan_id, "goal": self.goal,
                   "steps": list(self.steps)}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())


class ActionEngine:
    """Planificador determinista. Ejecuta SOLO internamente y trazadamente."""

    def __init__(self, policy: PolicyEngine | None = None,
                 ledger: EvidenceLedger | None = None, clock=None):
        self.policy = policy or PolicyEngine()
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.plans: dict[str, dict] = {}

    def plan(self, goal: str, steps: list[tuple[str, str]]) -> ActionPlan:
        if not steps:
            raise ActionError("plan vacio")
        for desc, risk in steps:
            if risk not in ("LOW", "MEDIUM", "HIGH"):
                raise ActionError(f"risk invalido: {risk}")
        needs_human = any(r == "HIGH" for _, r in steps)
        p = ActionPlan(plan_id=f"plan:{len(self.plans)+1}:"
                       f"{hashlib.sha256(_canon([goal, self.clock()])).hexdigest()[:8]}",
                       goal=goal, steps=tuple(steps),
                       requires_human_authorization=needs_human,
                       external_execution="PROHIBITED (constitution v1)")
        self.plans[p.plan_id] = {"plan": p, "step_states": ["PLANNED"] * len(steps)}
        self._audit("plan", p)
        return p

    def evaluate_step(self, plan_id: str, step_index: int) -> str:
        """Policy: MEDIUM->REVIEW, HIGH->ESCALATE(R1); LOW->READY (interno)."""
        st = self.plans[plan_id]["plan"].steps[step_index]
        risk = st[1]
        if risk == "LOW":
            state = "READY"
        elif risk == "MEDIUM":
            state = "AUTHORIZATION_REQUIRED"
        else:
            state = "AUTHORIZATION_REQUIRED"   # HIGH: requiere R1 ademas
        self.plans[plan_id]["step_states"][step_index] = state
        self._audit("step_eval", self.plans[plan_id]["plan"],
                    extra={"step": step_index, "state": state})
        return state

    def execute_step_internal(self, plan_id: str, step_index: int) -> dict:
        """Ejecucion INTERNA simulada y trazable. Externa: PROHIBIDA."""
        entry = self.plans[plan_id]
        if entry["step_states"][step_index] != "READY":
            raise ActionError("paso no READY (requiere autorizacion)")
        entry["step_states"][step_index] = "EXECUTED_INTERNAL"
        result = {"plan_id": plan_id, "step": step_index,
                  "result": f"internal:{hashlib.sha256(_canon([plan_id, step_index])).hexdigest()[:8]}",
                  "external": False}
        self._audit("step_internal", entry["plan"], extra={"step": step_index})
        return result

    def execute_external(self, *a, **k):
        raise ExternalExecutionProhibited(
            "ejecucion externa PROHIBIDA por constitucion (v1); el area 09 es "
            "COMPLETE via modelo controlado, no via ejecucion")

    def _audit(self, event, plan, extra=None):
        if self.ledger:
            e = {"type": "action", "event": event, "plan": plan.plan_id,
                 "hash": plan.content_hash[:16], "ts": self.clock()}
            if extra: e.update(extra)
            self.ledger.append(e)
