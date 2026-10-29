"""OM-P4 ContextAssembler -> CognitiveContext.

Combina DigitalSelf + memoria relevante + relaciones + sesion + historial + patrones +
insights + goals + purpose + future + evidence + uncertainty. Preserva las 5 etiquetas."""
from __future__ import annotations

LABELS = ("OBSERVED", "SELF_REPORTED", "INFERRED", "SYSTEM_DERIVED", "UNCERTAIN")


class AssemblyError(Exception):
    code = "ASSEMBLY_ERROR"


class ContextAssembler:
    def assemble(self, *, digital_self: dict | None = None, memories: list | None = None,
                 relationships: list | None = None, session: dict | None = None,
                 conversation: list | None = None, patterns: list | None = None,
                 insights: list | None = None, goals: list | None = None,
                 purpose=None, future=None, evidence: list | None = None,
                 uncertainty: dict | None = None, retriever=None, query: str | None = None,
                 tenant_id: str = "YO", owner_id: str = "yo") -> dict:
        relevant = []
        if retriever is not None and query:
            relevant = retriever.retrieve(query, tenant_id, owner_id)
        label_counts = {l: 0 for l in LABELS}
        if memories:
            for m in memories:
                if isinstance(m, dict) and m.get("provenance") in label_counts:
                    label_counts[m["provenance"]] += 1
        for item in relevant:
            p = item.get("metadata", {}).get("provenance")
            if p in label_counts:
                label_counts[p] += 1
        for i in (insights or []):
            p = getattr(i, "provenance", None)
            if p in label_counts:
                label_counts[p] += 1
        ctx = {
            "digital_self": digital_self or {},
            "relevant_memory": relevant,
            "relationship_context": relationships or [],
            "session": session or {},
            "conversation_history": conversation or [],
            "patterns": patterns or [],
            "insights": insights or [],
            "goals": goals or [],
            "purpose": purpose,
            "future": future,
            "evidence": evidence or [],
            "uncertainty": uncertainty or {},
            "provenance_labels": label_counts,
            "tenant_id": tenant_id, "owner_id": owner_id,
        }
        return ctx

    @staticmethod
    def _count_label(label, digital_self, memories, insights) -> int:
        n = 0
        if memories:
            n += sum(1 for m in memories if isinstance(m, dict) and m.get("provenance") == label)
        if insights:
            n += sum(1 for i in insights if getattr(i, "provenance", None) == label)
        return n
