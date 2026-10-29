"""OM-22 External tools/Web infrastructure: declared, scoped, authorized,
policy checked, audited. CAPABILITY != AUTHORITY. Sin ejecucion externa automatica."""
from __future__ import annotations


class WebToolRegistry:
    def __init__(self, policy):
        self.policy = policy
        self.tools: dict[str, dict] = {}
        self.audit: list = []

    def declare(self, name: str, endpoint: str, *, permission: str, scope: tuple,
                risk: str = "MEDIUM"):
        if name in self.tools:
            raise ValueError(f"ya declarada: {name}")
        self.tools[name] = {"endpoint": endpoint, "permission": permission,
                            "scope": tuple(scope), "risk": risk, "declared": True}

    def call(self, name: str, action_type: str, args: dict, actor: str = "twin") -> dict:
        if name not in self.tools:
            self.audit.append({"tool": name, "actor": actor, "allowed": False,
                               "reason": "not_declared"})
            raise PermissionError(f"herramienta no declarada: {name}")
        t = self.tools[name]
        if action_type not in t["scope"]:
            self.audit.append({"tool": name, "actor": actor, "allowed": False, "reason": "scope"})
            raise PermissionError(f"scope {action_type} no permitido")
        verdict = self.policy.evaluate(action_type=action_type, risk_override=t["risk"])
        entry = {"tool": name, "actor": actor, "allowed": verdict == "ALLOW",
                 "verdict": verdict, "args_hash": str(hash(str(sorted(args.items()))))[:12]}
        self.audit.append(entry)
        if verdict != "ALLOW":
            return {"executed": False, "verdict": verdict,
                    "note": "no automatic execution; authorization required"}
        return {"executed": True, "verdict": verdict, "result_stub": "DECLARED-ONLY"}
