"""Motor de estados AREA: transiciones validadas + evidencia (Bloque 3)."""
from __future__ import annotations
import json, time

VALID_TRANSITIONS = {
    "NOT_IMPLEMENTED": ["IMPLEMENTED", "DOCUMENTATION_ONLY", "BLOCKED"],
    "DOCUMENTATION_ONLY": ["IMPLEMENTED", "HARDWARE_DEPENDENT", "BLOCKED"],
    "IMPLEMENTED": ["PARTIAL", "HARDWARE_DEPENDENT", "COMPLETE", "BLOCKED"],
    "PARTIAL": ["IMPLEMENTED", "COMPLETE", "BLOCKED"],
    "HARDWARE_DEPENDENT": ["IMPLEMENTED", "BLOCKED"],
    "COMPLETE": [],  # terminal hasta nueva evidencia que abra revision
    "BLOCKED": ["NOT_IMPLEMENTED", "DOCUMENTATION_ONLY", "IMPLEMENTED"],
}

VALID_STATES = set(VALID_TRANSITIONS)


class StateError(Exception):
    pass


class StateEngine:
    def __init__(self, area_path: str):
        self.path = area_path
        with open(area_path) as f:
            self.area = json.load(f)

    def get(self, component: str) -> dict:
        return self.area["components"][component]

    def transition(self, component: str, new_state: str, evidence: str, actor: str = "system") -> dict:
        if new_state not in VALID_STATES:
            raise StateError(f"estado desconocido: {new_state}")
        comp = self.get(component)
        old = comp["state"]
        if new_state not in VALID_TRANSITIONS[old]:
            raise StateError(f"transicion prohibida: {old} -> {new_state} ({component})")
        comp.update(state=new_state, last_evidence=evidence,
                    updated_utc=self._now(), updated_by=actor)
        self._save()
        return {"component": component, "from": old, "to": new_state}

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.area, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _now() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
