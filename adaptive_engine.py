"""P10-B2 Adaptive Question Engine.

Cadena: QUESTION -> USER RESPONSE -> SELF_REPORTED MEMORY -> PATTERN -> HYPOTHESIS
       -> REFLECTION -> INSIGHT -> NEXT QUESTION

Reutiliza Memory G5 (PersistentMemoryStore) y Reflection G6 (reflect).
NUNCA escribe en DigitalSelf: solo EVIDENCE/PROPUESTA hacia Evolution (Bloque 4)."""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
sys.path.insert(0, "/mnt/agents/output/APP_YO/onboarding")
from question_registry import REGISTRY, REGISTRY_BY_ID, get, CATEGORIES
from reflection import reflect
from persistent_memory import PersistentMemoryStore

UNKNOWN_MARKERS = ("unknown", "no se", "no sé", "no lo se", "sin respuesta", "?", "ns/")


class AdaptiveError(Exception):
    code = "ADAPTIVE_ERROR"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass
class OnboardingSession:
    subject_id: str = "yo"
    asked: list = field(default_factory=list)        # ids de preguntas (no_repeat)
    answers: list = field(default_factory=list)      # records de respuesta
    pending_clarifications: list = field(default_factory=list)
    contradictions_open: list = field(default_factory=list)
    unknowns: list = field(default_factory=list)
    ts_start: float = field(default_factory=lambda: __import__("time").time())

    def answers_by_category(self) -> dict:
        out = {}
        for a in self.answers:
            out.setdefault(a["category"], []).append(a)
        return out


class AdaptiveEngine:
    def __init__(self, memory: PersistentMemoryStore, clock=None, tenant: str = "YO"):
        self.memory = memory          # Memory G5 existente (Bloque 4: integracion, no paralela)
        self.clock = clock or (lambda: time.time())
        self.tenant = tenant
        self._clarify_n = 0

    # ---------- seleccion adaptativa ----------
    def next_question(self, session: OnboardingSession) -> dict:
        """Prioridad: aclaraciones pendientes > categorias vacias > followups > prioridad."""
        if session.pending_clarifications:
            c = session.pending_clarifications.pop(0)
            return {"id": c["id"], "category": "Clarification", "goal": c["goal"],
                    "kind": "clarification", "ref": c.get("ref")}
        answered_cats = set(session.answers_by_category())
        candidates = []
        for q in REGISTRY:
            if q.no_repeat and q.id in session.asked:
                continue
            if q.activation["requires"] and not set(q.activation["requires"]) <= answered_cats:
                continue
            if q.activation["min_answers"] and \
               len(session.answers_by_category().get(q.category, [])) < q.activation["min_answers"]:
                continue
            # cobertura primero: prioridad boost si categoria sin respuestas
            boost = 0 if q.category in answered_cats else -10
            candidates.append((q.priority + boost, q))
        if not candidates:
            return {"id": "q.done", "category": "DONE", "goal": "cobertura completa",
                    "kind": "terminal"}
        candidates.sort(key=lambda x: x[0])
        q = candidates[0][1]
        return {"id": q.id, "category": q.category, "goal": q.goal, "kind": "registry"}

    # ---------- cadena completa ----------
    def submit_answer(self, session: OnboardingSession, question: dict,
                      answer_text: str, evidence: tuple = ()) -> dict:
        ts = self.clock()
        qid = question["id"]
        is_unknown = answer_text.strip().lower() in UNKNOWN_MARKERS or not answer_text.strip()
        provenance = "UNCERTAIN" if is_unknown else "SELF_REPORTED"
        confidence = 0.1 if is_unknown else 0.9
        category = question.get("category", "General")

        record = {
            "question_id": qid, "category": category, "answer": answer_text,
            "ts": ts, "provenance": provenance, "confidence": confidence,
            "evidence": tuple(evidence) or (f"ans:{qid}",),
        }
        session.answers.append(record)
        session.asked.append(qid)
        if is_unknown:
            session.unknowns.append(qid)

        # -> SELF_REPORTED MEMORY (G5): contenido+contexto+ts+provenance+evidence+confidence+origen
        mem_content = {"answer": answer_text, "context": {"question": question["goal"],
                        "category": category}}
        mem_id = self.memory.store(self.tenant, session.subject_id, "onboarding",
                                   self._memory_kind(category), mem_content,
                                   provenance, confidence, record["evidence"], f"q:{qid}")

        # -> PATTERN -> HYPOTHESIS -> REFLECTION (G6) sobre el contexto cognitivo acumulado
        experiences = self._session_to_experiences(session)
        insights = reflect(experiences, expected_domains=self._expected_domains(session))
        contradictions = [i for i in insights if i.type == "CONTRADICTION"]
        patterns = [i for i in insights if i.type == "PATTERN"]

        # CONTRADICTION ENGINE (Bloque 6): registrar y generar aclaracion (no decidir verdad)
        new_clar = []
        for c in contradictions:
            if c.statement not in [x["statement"] for x in session.contradictions_open]:
                session.contradictions_open.append({"statement": c.statement,
                                                    "evidence": list(c.evidence)})
                self._clarify_n += 1
                new_clar.append({"id": f"q.clarify.{self._clarify_n}",
                                 "goal": f"Aclarar: {c.statement}",
                                 "ref": c.id})
        session.pending_clarifications.extend(new_clar)

        next_q = self.next_question(session)
        return {"record": record, "memory_id": mem_id, "patterns": patterns,
                "contradictions": contradictions, "clarification_questions": new_clar,
                "insights": insights, "next_question": next_q,
                "open_contradictions": len(session.contradictions_open),
                "unknowns": len(session.unknowns)}

    def _memory_kind(self, category: str) -> str:
        return {"Experiences": "EPISODIC", "Relationships": "RELATIONSHIP",
                "Values": "SEMANTIC", "Beliefs": "SEMANTIC", "Purpose": "SEMANTIC",
                "Future": "SEMANTIC", "Shadow": "EMOTIONAL", "Decisions": "EPISODIC",
                "Identity": "SEMANTIC"}.get(category, "KNOWLEDGE")

    def _session_to_experiences(self, session: OnboardingSession) -> list:
        out = []
        for i, a in enumerate(session.answers):
            value = (a["answer"].strip().lower().split() or ["unknown"])[0][:24]
            out.append({"id": f"a{i}", "domain": a["category"].lower(), "key": a["question_id"],
                        "value": value, "provenance": a["provenance"], "ts": a["ts"]})
        return out

    def _expected_domains(self, session: OnboardingSession) -> tuple:
        return tuple(c.lower() for c in CATEGORIES)
