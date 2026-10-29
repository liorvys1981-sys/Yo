"""P10-B1 Question Registry — 9 categorías, preguntas con metadatos cognitivos.
Conversación cognitiva progresiva (NO test psicologico rigido)."""
from __future__ import annotations
from dataclasses import dataclass, field

CATEGORIES = ("Identity", "Values", "Beliefs", "Decisions", "Experiences",
              "Relationships", "Purpose", "Shadow", "Future")


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    goal: str
    priority: int
    activation: dict            # {"requires": [cat,...], "min_answers": n}
    expected_provenance: str    # "SELF_REPORTED"
    followup_rules: tuple       # condiciones para profundizar
    related: tuple              # categorías relacionadas
    no_repeat: bool = True


def _q(qid, cat, goal, prio, requires=(), min_answers=0, followups=(), related=()):
    return Question(id=qid, category=cat, goal=goal, priority=prio,
                    activation={"requires": list(requires), "min_answers": min_answers},
                    expected_provenance="SELF_REPORTED",
                    followup_rules=tuple(followups), related=tuple(related))


REGISTRY = (
    # Identity
    _q("q.identity.1", "Identity", "nombre/como se presenta la persona", 1),
    _q("q.identity.2", "Identity", "que la distingue de otros", 2, requires=("Identity",), min_answers=1,
       related=("Values",)),
    # Values
    _q("q.values.1", "Values", "principios no negociables", 1),
    _q("q.values.2", "Values", "valor que sacrificaria menos", 3, requires=("Values",), min_answers=1),
    # Beliefs
    _q("q.beliefs.1", "Beliefs", "creencia central sobre el mundo", 2),
    _q("q.beliefs.2", "Beliefs", "creencia que ha cambiado con el tiempo", 4,
       requires=("Beliefs",), min_answers=1, related=("Experiences",)),
    # Decisions
    _q("q.decisions.1", "Decisions", "decision importante reciente y su razon", 3),
    # Experiences
    _q("q.experiences.1", "Experiences", "experiencia que le definio", 2),
    _q("q.experiences.2", "Experiences", "experiencia que evita repetir", 4,
       requires=("Experiences",), min_answers=1, related=("Shadow",)),
    # Relationships
    _q("q.relationships.1", "Relationships", "vinculo mas importante y por que", 3),
    # Purpose
    _q("q.purpose.1", "Purpose", "para que cree que esta aqui / su mision", 2),
    _q("q.purpose.2", "Purpose", "que legado quiere dejar", 4, requires=("Purpose",), min_answers=1,
       related=("Future",)),
    # Shadow
    _q("q.shadow.1", "Shadow", "que evita enfrentar / patron no deseado", 5),
    # Future
    _q("q.future.1", "Future", "como se ve en 5-10 anos", 3),
    _q("q.future.2", "Future", "que necesita cambiar para lograrlo", 5,
       requires=("Future",), min_answers=1, related=("Shadow",)),
)
REGISTRY_BY_ID = {q.id: q for q in REGISTRY}


class RegistryError(Exception):
    code = "REGISTRY_ERROR"


def get(qid: str) -> Question:
    if qid not in REGISTRY_BY_ID:
        raise RegistryError(f"pregunta desconocida: {qid}")
    return REGISTRY_BY_ID[qid]


def categories() -> tuple:
    return CATEGORIES
