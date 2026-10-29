"""P10-B12/B13 ELLA Cognitive Foundation + ELLA Onboarding.

ELLA DIGITALSELF + ELLA MEMORY + ELLA EXPERIENCES + ELLA REFLECTION + ELLA INSIGHTS
= ELLA COGNITIVE TWIN FOUNDATION.

Separacion estricta: memory en root propio + tenant ELLA; reflection/insights son
funciones puras reutilizadas con los datos DE ELLA (state-in, state-out; no hay
estado de YO embebido). YO MEMORY != ELLA MEMORY por root+tenant. NADA se copia
automaticamente desde YO; lo que provenga de YO lleva provenance de origen."""
from __future__ import annotations
import os, sys, time

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, "/mnt/agents/output/APP_YO/onboarding")
sys.path.insert(0, "/mnt/agents/output/APP_YO/ELLA")
from persistent_memory import PersistentMemoryStore
from reflection import reflect
from insights import InsightTracker
from question_registry import REGISTRY


class FoundationError(Exception):
    code = "FOUNDATION_ERROR"


def yo_to_ella_provenance(record: dict, yo_ref: str) -> dict:
    """Etiquetar dato proveniente de YO con su origen (Bloque 13)."""
    r = dict(record)
    r["origin"] = {"namespace": "YO", "ref": yo_ref}
    r["provenance_subtype"] = (r.get("provenance_subtype") or "") + "+FROM_YO"
    return r


class EllaFoundation:
    TENANT = "ELLA"

    def __init__(self, ella_root: str, ledger=None, clock=None):
        self.root = os.path.join(ella_root, "ELLA")
        os.makedirs(os.path.join(self.root, "memory"), exist_ok=True)
        self.memory = PersistentMemoryStore(os.path.join(self.root, "memory"), None)
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.insights = InsightTracker(ledger=ledger, clock=self.clock)
        self.experiences: list = []

    # --- ELLA MEMORY (aislada: root propio + tenant ELLA) ---
    def store_experience(self, content: dict, provenance: str, confidence: float,
                         evidence: tuple, source_ref: str) -> str:
        mid = self.memory.store(self.TENANT, "ella", "ella-core", "EPISODIC",
                                content, provenance, confidence, evidence, source_ref)
        self.experiences.append({"id": mid, "domain": content.get("domain", "ella"),
                                 "key": source_ref, "value": content.get("key", "x"),
                                 "provenance": provenance, "ts": self.clock()})
        if self.ledger:
            self.ledger.append({"type": "ella_memory", "memory_id": mid,
                                "tenant": self.TENANT})
        return mid

    # --- ELLA REFLECTION + INSIGHTS (reutiliza G6/G10 con datos de ELLA) ---
    def reflect(self):
        ins = reflect(self.experiences, expected_domains=("ella",))
        self.insights.register_reflection_outputs(ins)
        return ins

    def twin_foundation(self, active_identity: dict) -> dict:
        """ELLA COGNITIVE TWIN FOUNDATION (scaffold post-activacion)."""
        return {
            "namespace": "ELLA",
            "DigitalSelf": active_identity,   # del scaffold de activacion (solo Identity ACTIVE)
            "Memory": {"tenant": self.TENANT, "records": len(self.memory.query(self.TENANT))},
            "Experiences": {"count": len(self.experiences)},
            "Reflection": "available (G6 reutilizado, datos ELLA)",
            "Insights": {"tracked": len(self.insights._items)},
            "autonomy": "DISABLED",
        }


class EllaOnboarding:
    """P10-B13: onboarding propio de ELLA, separado del de YO. NO copia valores/
    creencias/personalidad/memoria/experiencias de YO. Si un elemento viene de YO,
    conserva provenance de origen (yo_to_ella_provenance)."""

    def __init__(self, foundation: EllaFoundation, clock=None):
        self.f = foundation
        self.clock = clock or (lambda: time.time())

    def seed_from_yo(self, yo_records: list, yo_ref: str) -> list:
        """Siembra SOLO con etiqueta de origen YO (provenance preservado)."""
        seeded = []
        for r in yo_records:
            tagged = yo_to_ella_provenance(r, yo_ref)
            mid = self.f.store_experience(
                {"domain": "ella-seed", "key": r.get("key", "seed"),
                 "note": str(tagged.get("content", ""))[:200]},
                provenance=tagged["provenance"] if tagged["provenance"] != "UNCERTAIN" else "UNCERTAIN",
                confidence=tagged.get("confidence", 0.5),
                evidence=tuple(tagged.get("evidence", ())) + (f"yo-ref:{yo_ref}",),
                source_ref=f"yo-seed:{r.get('id', 'x')}")
            seeded.append(mid)
        return seeded

    def questions(self) -> list:
        """Mismo REGISTRY (9 categorias) pero session/namespace propios de ELLA."""
        return [{"id": q.id, "category": q.category, "goal": q.goal,
                 "namespace": "ELLA"} for q in REGISTRY]
