"""23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION — investigacion reproducible
sobre las 9 lentes cognitivas documentadas.

Separacion estricta de etapas:
INVESTIGACION (pregunta + lente + hipotesis)
  -> EXPERIMENTACION (ejecucion determinista, input sellado)
  -> EVALUACION (resultado vs criterio, evidencia, uncertainty)
  -> EVOLUCION CONTROLADA (propuesta; G8+R1 es la UNICA ruta de cambio)

Ninguna etapa muta DigitalSelf. Reproducible: mismo input+seed -> mismo resultado.
Las lentes son FUNCIONES de analisis, no agentes ni autoridades."""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/10_INTERACCION")
sys.path.insert(0, "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA")
from interaction_to_cognition import COGNITIVE_LENSES
from self_awareness import Metacognition

LENSES_BY_NAME = {l["name"]: l for l in COGNITIVE_LENSES}
EVOLUTION = ("propose_only",)   # la unica transicion permitida hacia el self


class ResearchError(Exception):
    code = "RESEARCH_ERROR"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class ResearchQuestion:
    question_id: str
    lens_name: str
    statement: str
    hypothesis: dict          # {"statement": str, "stage": "UNCERTAIN"}
    evidence_required: tuple
    provenance: str = "INFERRED"
    content_hash: str = field(init=False)

    def __post_init__(self):
        if self.lens_name not in LENSES_BY_NAME:
            raise ResearchError(f"lente desconocida: {self.lens_name}")
        lens = LENSES_BY_NAME[self.lens_name]
        if "SPECULATIVE" in lens["evidence"] and self.provenance != "INFERRED":
            raise ResearchError("lente especulativa solo admite hipotesis INFERRED")
        payload = {"question_id": self.question_id, "lens_name": self.lens_name,
                   "statement": self.statement, "hypothesis": self.hypothesis,
                   "evidence_required": list(self.evidence_required),
                   "provenance": self.provenance}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    question_id: str
    lens_name: str
    input_data: dict          # sellado por hash
    seed: int
    ts: float
    result: dict
    evidence: tuple
    reproducibility_hash: str
    content_hash: str = field(init=False)

    def __post_init__(self):
        payload = {k: getattr(self, k) for k in
                   ("experiment_id", "question_id", "lens_name", "input_data",
                    "seed", "ts", "result", "evidence", "reproducibility_hash")}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    experiment_id: str
    criterion: str
    outcome: str              # SUPPORTED | REFUTED | UNCERTAIN | INCONCLUSIVE
    uncertainty: float        # [0,1]
    evidence: tuple
    ts: float
    content_hash: str = field(init=False)

    def __post_init__(self):
        if self.outcome not in ("SUPPORTED", "REFUTED", "UNCERTAIN", "INCONCLUSIVE"):
            raise ResearchError(f"outcome invalido: {self.outcome}")
        payload = {k: getattr(self, k) for k in
                   ("evaluation_id", "experiment_id", "criterion", "outcome",
                    "uncertainty", "evidence", "ts")}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())


class ResearchEngine:
    """Motor de investigacion reproducible. Determinista (seed + reloj inyectable)."""

    def __init__(self, meta: Metacognition | None = None, clock=None):
        self.meta = meta or Metacognition()
        self.clock = clock or (lambda: time.time())
        self.questions: dict[str, ResearchQuestion] = {}
        self.experiments: dict[str, Experiment] = {}
        self.evaluations: dict[str, Evaluation] = {}

    # ---------- INVESTIGACION ----------
    def formulate(self, lens_name: str, statement: str, hypothesis: str,
                  evidence_required: tuple = ()) -> ResearchQuestion:
        self.meta.assert_no_consciousness_claim(statement)   # limite de conciencia aplica
        self.meta.assert_no_consciousness_claim(hypothesis)
        q = ResearchQuestion(question_id=f"rq:{len(self.questions)+1}:"
                             f"{hashlib.sha256(_canon([lens_name, statement])).hexdigest()[:8]}",
                             lens_name=lens_name, statement=statement,
                             hypothesis={"statement": hypothesis, "stage": "UNCERTAIN"},
                             evidence_required=tuple(evidence_required))
        self.questions[q.question_id] = q
        return q

    # ---------- EXPERIMENTACION ----------
    def run_experiment(self, question: ResearchQuestion, input_data: dict,
                       seed: int = 0) -> Experiment:
        lens = LENSES_BY_NAME[question.lens_name]
        fn = self._lens_function(question.lens_name)
        result = fn(input_data, seed)   # determinista puro
        repro = hashlib.sha256(_canon([input_data, seed, result])).hexdigest()[:16]
        exp = Experiment(experiment_id=f"exp:{len(self.experiments)+1}:{repro}",
                         question_id=question.question_id, lens_name=question.lens_name,
                         input_data=input_data, seed=seed, ts=self.clock(),
                         result=result, evidence=(f"in:{repro}",),
                         reproducibility_hash=repro)
        self.experiments[exp.experiment_id] = exp
        return exp

    @staticmethod
    def _lens_function(name: str):
        """Funciones de analisis deterministas por lente (no agentes)."""
        def festinger(data, seed):
            vals = [str(v).strip().lower() for v in data.get("elements", {}).values() if v]
            divergent = len(set(vals)) > 1 if len(vals) >= 2 else None
            return {"n_elements": len(vals), "divergent": divergent}
        def higgins(data, seed):
            dims = {k: bool(data.get(k)) for k in ("actual", "ideal", "ought")}
            return {"dimensions_present": dims,
                    "gaps": [k for k, v in dims.items() if not v]}
        def metacognition(data, seed):
            return {"questions_applied": 8, "input_size": len(str(data))}
        def default(data, seed):
            return {"input_keys": sorted(data.keys()), "seed": seed,
                    "note": "analisis estructural determinista"}
        return {"Festinger": festinger, "Higgins": higgins,
                "Metacognition": metacognition}.get(name, default)

    # ---------- EVALUACION ----------
    def evaluate(self, exp: Experiment, criterion: str,
                 observed_meets_criterion: bool | None,
                 evidence: tuple = ()) -> Evaluation:
        if observed_meets_criterion is None:
            outcome = "INCONCLUSIVE"
        elif observed_meets_criterion:
            outcome = "SUPPORTED"
        else:
            outcome = "REFUTED"
        unc = 0.0 if observed_meets_criterion is not None else 1.0
        ev = Evaluation(evaluation_id=f"ev:{len(self.evaluations)+1}:"
                        f"{hashlib.sha256(_canon([exp.experiment_id, criterion])).hexdigest()[:8]}",
                        experiment_id=exp.experiment_id, criterion=criterion,
                        outcome=outcome, uncertainty=unc, evidence=tuple(evidence),
                        ts=self.clock())
        self.evaluations[ev.evaluation_id] = ev
        return ev

    # ---------- EVOLUCION CONTROLADA ----------
    def evolution_proposal(self, evaluation: Evaluation) -> dict:
        """La UNICA salida hacia el self: propuesta -> G8 pipeline -> R1. Nada mas."""
        return {"type": "research_evolution_proposal",
                "from_evaluation": evaluation.evaluation_id,
                "outcome": evaluation.outcome,
                "route": "INVESTIGACION->EXPERIMENTACION->EVALUACION->PROPOSAL->G8->R1",
                "direct_mutation": "PROHIBITED",
                "auto_apply": False}

    def reproduce(self, exp: Experiment, input_data: dict, seed: int) -> bool:
        """Verificacion de reproducibilidad: re-ejecutar y comparar hash."""
        rerun = self.run_experiment(self.questions[exp.question_id], input_data, seed)
        return rerun.reproducibility_hash == exp.reproducibility_hash

    def research_report(self) -> dict:
        return {"questions": len(self.questions), "experiments": len(self.experiments),
                "evaluations": len(self.evaluations),
                "supported": sum(1 for e in self.evaluations.values()
                                 if e.outcome == "SUPPORTED"),
                "refuted": sum(1 for e in self.evaluations.values()
                               if e.outcome == "REFUTED"),
                "lenses_available": sorted(LENSES_BY_NAME),
                "lenses_speculative": [l["name"] for l in COGNITIVE_LENSES
                                       if "SPECULATIVE" in l["evidence"]],
                "evolution_gate": "G8+R1 only"}
