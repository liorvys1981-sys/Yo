"""P10-B7 Cognitive Maturity — multi-criterio, explicable, determinista, auditable.
NO es respuestas/total. Nunca afirma que la persona 'es' algo por cantidad."""
from __future__ import annotations


class MaturityError(Exception):
    code = "MATURITY_ERROR"


def compute(session, twin_snapshot: dict | None = None) -> dict:
    answers = session.answers
    n = len(answers)
    if n == 0:
        raise MaturityError("sin respuestas: imposible evaluar madurez")

    by_cat = session.answers_by_category()
    cats = ("Identity", "Values", "Beliefs", "Decisions", "Experiences",
            "Relationships", "Purpose", "Shadow", "Future")
    covered = [c for c in cats if c in by_cat]
    coverage = len(covered) / len(cats)

    depth = min(1.0, sum(len(v) for v in by_cat.values()) / (len(cats) * 2))

    contradictions_open = len(session.contradictions_open)
    consistency = max(0.0, 1.0 - (contradictions_open / max(1, n)))

    with_evidence = sum(1 for a in answers if a.get("evidence")) / n

    uncertain = sum(1 for a in answers if a["provenance"] == "UNCERTAIN") / n
    uncertainty_score = 1.0 - uncertain

    days = len({int(a["ts"] // 86400) for a in answers})
    temporal = min(1.0, days / 3)

    entity_cov = 0.0
    purpose_fut = 0.0
    memory_patterns = 0.0
    if twin_snapshot:
        ents = twin_snapshot.get("entities", {})
        present = [k for k in ("Identity", "Values", "Beliefs", "Goals", "Traits",
                               "Relationships", "Experiences") if ents.get(k, {}).get("status") == "ACTIVE"]
        entity_cov = len(present) / 7
        purpose_fut = (1.0 if ents.get("Purpose") else 0.0) + (1.0 if ents.get("Future") else 0.0)
        memory_patterns = min(1.0, (twin_snapshot.get("memory_records", 0) / 10) +
                              (twin_snapshot.get("patterns", 0) / 5))

    criteria = {
        "coverage": {"value": round(coverage, 3),
                     "explanation": f"categorias cubiertas {len(covered)}/9: {sorted(covered)}"},
        "depth": {"value": round(depth, 3),
                  "explanation": f"{n} respuestas; profundidad por categoria limitada a 2"},
        "consistency": {"value": round(consistency, 3),
                        "explanation": f"{contradictions_open} contradicciones abiertas de {n} respuestas"},
        "evidence": {"value": round(with_evidence, 3),
                     "explanation": "fraccion de respuestas con evidencia registrada"},
        "uncertainty": {"value": round(uncertainty_score, 3),
                        "explanation": f"{sum(1 for a in answers if a['provenance']=='UNCERTAIN')} UNKNOWN de {n}"},
        "contradictions": {"value": float(contradictions_open == 0),
                           "explanation": "1.0 solo si no hay contradicciones abiertas"},
        "temporal_evolution": {"value": round(temporal, 3),
                               "explanation": f"{days} dia(s) distinto(s) de actividad"},
        "entity_coverage": {"value": round(entity_cov, 3),
                            "explanation": f"{int(entity_cov*7)}/7 entidades del DigitalSelf con evidencia"},
        "purpose_future": {"value": round(purpose_fut / 2, 3),
                           "explanation": "Purpose y Future presentes en el twin"},
        "memory_patterns": {"value": round(memory_patterns, 3),
                            "explanation": "registros de memoria + patrones acumulados"},
    }
    score = round(sum(c["value"] for c in criteria.values()) / len(criteria), 4)
    ready = coverage >= 0.8 and consistency >= 0.7 and contradictions_open == 0
    return {"score": score, "criteria": criteria, "answers": n,
            "coverage_by_category": {c: len(by_cat.get(c, [])) for c in cats},
            "ready_for_ella": ready,
            "ready_explanation": ("coverage>=0.8 y consistency>=0.7 y 0 contradicciones abiertas"
                                  if ready else
                                  "falta: cobertura<80% o consistencia<0.7 o contradicciones abiertas"),
            "caution": "la madurez NUNCA afirma que la persona 'es' algo; solo mide evidencia disponible"}
