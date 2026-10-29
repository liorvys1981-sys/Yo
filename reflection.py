"""G6 REFLECTION — funcion determinista pura. Sin LLM, sin red, sin reloj de pared.

Reglas soberanas (05_REFLECTION_EVOLUTION.md):
- Reflection NO modifica DigitalSelf (guard estructural: este modulo no lo importa).
- Una hipotesis NO es una verdad (HYPOTHESIS siempre provenance=INFERRED).
- Toda incertidumbre se etiqueta UNCERTAIN (confidence < 0.4).
- Toda salida conserva provenance, evidence, confidence, timestamp, version.
- Tipos diferenciados: PATTERN, CONTRADICTION, STRENGTH, BLIND_SPOT, HYPOTHESIS, RECOMMENDATION.
- Inferencias NO se convierten en Identity/Values/Beliefs: la unica ruta es
  EvolutionEngine.propose + AuthorizationGate (otro modulo; aqui no existe).
"""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass, asdict

UNCERTAINTY_THRESHOLD = 0.4
PATTERN_MIN_OCCURRENCES = 3
STRENGTH_MIN_OCCURRENCES = 5


@dataclass(frozen=True)
class Insight:
    id: str
    type: str                 # PATTERN | CONTRADICTION | STRENGTH | BLIND_SPOT | HYPOTHESIS | RECOMMENDATION
    statement: str
    domain: str
    key: str
    provenance: str           # OBSERVED | INFERRED | SYSTEM_DERIVED | UNCERTAIN
    confidence: float
    label: str                # provenance o UNCERTAIN si confidence < umbral
    evidence: tuple
    ts: float                 # derivado del input (determinista)
    version: int
    source_ids: tuple


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _iid(type_, statement) -> str:
    return "ins:" + hashlib.sha256(_canon([type_, statement])).hexdigest()[:16]


def _with_label(provenance: str, confidence: float) -> str:
    return "UNCERTAIN" if confidence < UNCERTAINTY_THRESHOLD else provenance


def reflect(experiences: list, expected_domains: tuple = (),
            prior_insights: tuple = ()) -> list:
    """ experiences: [{"id","domain","key","value","provenance","ts"}, ...]
        deterministico: mismo input -> mismo output (ts = max ts del input). """
    if not isinstance(experiences, list):
        raise TypeError("experiences debe ser list; DigitalSelf u otros objetos no aceptados")
    out: list[Insight] = []
    if not experiences and not expected_domains:
        return out

    ts = max((e["ts"] for e in experiences), default=0.0)
    versions = {}
    for p in prior_insights:
        versions[p["id"]] = p.get("version", 1)

    def emit(type_, statement, domain, key, provenance, confidence, evidence,
             source_ids) -> Insight:
        iid = _iid(type_, statement)
        return Insight(id=iid, type=type_, statement=statement, domain=domain,
                       key=key, provenance=provenance, confidence=round(confidence, 4),
                       label=_with_label(provenance, confidence),
                       evidence=tuple(evidence), ts=ts,
                       version=versions.get(iid, 0) + 1, source_ids=tuple(source_ids))

    # agrupar por (domain, key)
    groups = {}
    for e in experiences:
        groups.setdefault((e["domain"], e["key"]), []).append(e)

    for (domain, key), evs in sorted(groups.items()):
        ids = [e["id"] for e in evs]
        by_value = {}
        for e in evs:
            by_value.setdefault(e["value"], []).append(e)
        n = len(evs)

        # PATTERN: mismo valor recurrente
        for value, sub in by_value.items():
            if len(sub) >= PATTERN_MIN_OCCURRENCES:
                conf = min(1.0, len(sub) / 5.0)
                st = f"Patron: '{key}' = '{value}' en {domain} ({len(sub)} ocurrencias)"
                pat = emit("PATTERN", st, domain, key, "OBSERVED", conf,
                           [s["id"] for s in sub], [s["id"] for s in sub])
                out.append(pat)
                # STRENGTH: constancia alta
                if len(sub) >= STRENGTH_MIN_OCCURRENCES:
                    out.append(emit("STRENGTH",
                        f"Constancia: '{key}' sostenido {len(sub)} veces en {domain}",
                        domain, key, "OBSERVED", 0.8,
                        [s["id"] for s in sub], [s["id"] for s in sub]))
                # HYPOTHESIS: explicacion inferida del patron (NO verdad)
                out.append(emit("HYPOTHESIS",
                    f"Hipotesis: la regularidad en '{key}' podria indicar una rutina estable en {domain} (requiere verificacion)",
                    domain, key, "INFERRED", round(conf * 0.7, 4),
                    pat.evidence, [pat.id]))

        # CONTRADICTION: valor declarado vs observado
        declared = [e for e in evs if e["provenance"] == "SELF_REPORTED"]
        observed = [e for e in evs if e["provenance"] == "OBSERVED"]
        if declared and observed:
            d_vals = {e["value"] for e in declared}
            o_vals = {e["value"] for e in observed}
            if d_vals != o_vals:
                out.append(emit("CONTRADICTION",
                    f"Contradiccion en {domain}: declarado {sorted(d_vals)} vs observado {sorted(o_vals)} en '{key}'",
                    domain, key, "OBSERVED", 0.6,
                    ids, ids))

    # BLIND_SPOT + RECOMMENDATION: dominios esperados sin experiencias
    present = {e["domain"] for e in experiences}
    for d in expected_domains:
        if d not in present:
            bs = emit("BLIND_SPOT", f"Punto ciego: sin experiencias registradas en {d}",
                      d, "*", "SYSTEM_DERIVED", 0.5, [], [])
            out.append(bs)
            out.append(emit("RECOMMENDATION",
                f"Recomendacion: registrar experiencias en {d} para completar el modelo",
                d, "*", "SYSTEM_DERIVED", 0.5, [bs.id], [bs.id]))

    return out
