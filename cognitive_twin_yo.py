"""P10-B8 Cognitive Twin de YO — snapshot que distingue hecho/memoria/hipotesis/
interpretacion/incertidumbre/proyeccion. NO fabrica atributos sin evidencia."""
from __future__ import annotations

TAGS = ("fact", "memory", "hypothesis", "interpretation", "uncertainty", "projection")


def _entity_view(entity_versions) -> dict:
    if not entity_versions:
        return {"status": "NO EVIDENCE"}
    active = entity_versions[-1]
    return {"status": "ACTIVE", "provenance": active.get("provenance"),
            "confidence": active.get("confidence"), "version": active.get("version"),
            "tag": "fact" if active.get("provenance") in ("OBSERVED", "SELF_REPORTED")
                   else "interpretation"}


def build_twin(digital_self_entities: dict, session=None,
               memory_counts: dict | None = None, patterns: list | None = None,
               insights: list | None = None) -> dict:
    ents = {k: _entity_view(v) for k, v in digital_self_entities.items()}
    n_answers = len(session.answers) if session else 0
    unc = len(session.unknowns) if session else 0
    return {
        "Identity": ents.get("Identity", {"status": "NO EVIDENCE"}),
        "Values": ents.get("Values", {"status": "NO EVIDENCE"}),
        "Beliefs": ents.get("Beliefs", {"status": "NO EVIDENCE"}),
        "Goals": ents.get("Goals", {"status": "NO EVIDENCE"}),
        "Traits": ents.get("Traits", {"status": "NO EVIDENCE"}),
        "Relationships": ents.get("Relationships", {"status": "NO EVIDENCE"}),
        "Experiences": ents.get("Experiences", {"status": "NO EVIDENCE"}),
        "Memory": {"status": "ACTIVE" if memory_counts else "NO EVIDENCE",
                   "counts": memory_counts or {}, "tag": "memory",
                   "records": sum((memory_counts or {}).values())},
        "Patterns": {"items": [{"statement": p.statement, "confidence": p.confidence,
                                 "tag": "interpretation"} for p in (patterns or [])],
                     "tag": "interpretation"},
        "Reflections": {"count": n_answers, "tag": "memory"},
        "Insights": {"items": [{"type": i.type, "statement": i.statement,
                                "state": getattr(i, "state", "REGISTERED"),
                                "tag": "hypothesis" if i.type == "HYPOTHESIS" else "interpretation"}
                               for i in (insights or [])]},
        "Purpose": ents.get("Values", {"status": "NO EVIDENCE"}),
        "Future": {"status": "ACTIVE" if ents.get("Goals", {}).get("status") == "ACTIVE"
                   else "NO EVIDENCE", "tag": "projection"},
        "uncertainty": {"unknowns": unc, "tag": "uncertainty"},
        "entities": ents,
    }



class CognitiveTwinContextPort:
    """Explicit ingress for external app context.

    This port records contextual observations separately from DigitalSelf and
    does not mutate identity, values, beliefs, traits, or the cognitive genome.
    Production deployments may replace the in-memory receipt store with the
    existing persistence/event bus adapter while preserving this contract.
    """
    def __init__(self, max_receipts: int = 10000):
        if max_receipts < 1:
            raise ValueError("max_receipts must be >= 1")
        self.max_receipts = max_receipts
        self.external_context_events = []
        self._event_hashes = set()

    def ingest_context(self, context: dict, *, event: dict):
        if not isinstance(context, dict) or not isinstance(event, dict):
            raise TypeError("context and event must be dictionaries")
        if context.get("tenant_id") != event.get("tenant_id"):
            raise ValueError("tenant mismatch between context and event")
        if context.get("owner_id") != event.get("owner_id"):
            raise ValueError("owner mismatch between context and event")
        if context.get("external_event_is_identity") is not False:
            raise ValueError("external event must not be promoted to identity")
        if context.get("external_data_is_truth") is not False:
            raise ValueError("external data must not be promoted to truth")
        event_hash = event.get("content_hash")
        if not event_hash:
            raise ValueError("event content hash required")
        if event_hash in self._event_hashes:
            return {"accepted": True, "duplicate": True, "event_hash": event_hash}
        if len(self.external_context_events) >= self.max_receipts:
            raise RuntimeError("Cognitive Twin context inbox capacity reached")
        receipt = {
            "event_hash": event_hash,
            "event_id": event.get("event_id"),
            "app_id": event.get("app_id"),
            "tenant_id": event.get("tenant_id"),
            "owner_id": event.get("owner_id"),
            "provenance": event.get("provenance"),
            "context": context,
            "identity_mutated": False,
            "truth_promoted": False,
        }
        self.external_context_events.append(receipt)
        self._event_hashes.add(event_hash)
        return {"accepted": True, "duplicate": False, "event_hash": event_hash}
