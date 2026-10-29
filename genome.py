"""Cognitive Genome — validador formal de elementos (COGNITIVE_GENOME_SPEC).

Procedencia o nada. INFERRED nunca presentado como hecho. Versionado inmutable.
"""
from __future__ import annotations

PROVENANCE = {"OBSERVED", "INFERRED", "SELF_REPORTED", "SYSTEM_DERIVED", "UNCERTAIN"}
FUNDAMENTAL_KINDS = {"value", "purpose", "belief_core"}   # identidad fundamental

REASON = type("REASON", (), {
    "MISSING_PROVENANCE": "MISSING_PROVENANCE",
    "INVALID_PROVENANCE": "INVALID_PROVENANCE",
    "INVALID_CONFIDENCE": "INVALID_CONFIDENCE",
    "INFERRED_WITHOUT_EVIDENCE": "INFERRED_WITHOUT_EVIDENCE",
    "VERSION_GAP": "VERSION_GAP",
    "MISSING_SOURCE": "MISSING_SOURCE",
    "FUNDAMENTAL_NOT_APPROVABLE": "FUNDAMENTAL_NOT_APPROVABLE",
    "FUNDAMENTAL_INFERRED": "FUNDAMENTAL_INFERRED",
})


class GenomeError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def validate_genome_element(elem: dict) -> None:
    """Valida un elemento del genoma. REJECTED(reason) o OK (sin retorno)."""
    prov = elem.get("provenance")
    if prov is None:
        raise GenomeError(REASON.MISSING_PROVENANCE)
    if prov not in PROVENANCE:
        raise GenomeError(REASON.INVALID_PROVENANCE)

    conf = elem.get("confidence")
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        raise GenomeError(REASON.INVALID_CONFIDENCE)

    if not elem.get("source", {}).get("ref"):
        raise GenomeError(REASON.MISSING_SOURCE)

    kind = elem.get("kind")
    if kind in FUNDAMENTAL_KINDS and prov in ("INFERRED", "SYSTEM_DERIVED"):
        raise GenomeError(REASON.FUNDAMENTAL_INFERRED)

    if prov == "INFERRED" and not elem.get("evidence"):
        raise GenomeError(REASON.INFERRED_WITHOUT_EVIDENCE)

    version = elem.get("version", 1)
    evolution = elem.get("evolution", [])
    if version > 1 and len(evolution) < version - 1:
        raise GenomeError(REASON.VERSION_GAP)

    for ev in evolution:
        if kind in FUNDAMENTAL_KINDS and ev.get("approved_by") != "humano":
            raise GenomeError(REASON.FUNDAMENTAL_NOT_APPROVABLE)


def provenance_breakdown(genome: list[dict]) -> dict:
    """Distinguibilidad: cuanto del genoma es declarado vs inferido vs derivado."""
    out = {p: 0 for p in PROVENANCE}
    for e in genome:
        out[e["provenance"]] = out.get(e["provenance"], 0) + 1
    return out
