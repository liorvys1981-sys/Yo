"""GAP-11 SINTONIA RELACIONAL — ajuste seguro de parametros de interaccion.

La sintonia NUNCA genera lenguaje emocional; ajusta PARAMETROS (ritmo, longitud,
frecuencia de preguntas, formalidad) segun senales con provenance. Garantias del
Cognitive Mirror intactas: MetacognitiveSecurity bloquea manipulacion/diagnostico/
dependencia; autonomia humana preservada (el usuario puede fijar parametros).
"""
from __future__ import annotations
import hashlib, json, sys
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA")
from self_awareness import Metacognition


class SintoniaError(Exception):
    code = "SINTONIA_ERROR"


PARAM_RANGES = {"pacing": (1, 5), "response_length": (1, 5),
                "question_frequency": (0.0, 1.0), "formality": (1, 5)}


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass
class InteractionParams:
    pacing: int = 3
    response_length: int = 3
    question_frequency: float = 0.5
    formality: int = 3
    fixed_by_user: bool = False
    content_hash: str = field(init=False)

    def __post_init__(self):
        for p, (lo, hi) in PARAM_RANGES.items():
            v = getattr(self, p)
            if not (lo <= v <= hi):
                raise SintoniaError(f"{p} fuera de rango [{lo},{hi}]")
        self.content_hash = hashlib.sha256(_canon(self.__dict__)).hexdigest()


class SintoniaEngine:
    """Ajusta parametros por feedback/senales. Sin generacion de lenguaje."""

    def __init__(self, meta: Metacognition | None = None, clock=None):
        self.meta = meta or Metacognition()
        import time as _t
        self.clock = clock or (lambda: _t.time())
        self.params = InteractionParams()

    def apply_signal(self, kind: str, value: float, provenance: str) -> InteractionParams:
        """kind: 'preference_pacing'|'preference_length'|'preference_formality'|
        'preference_questions'. value en [0,1]. provenance validado."""
        if self.params.fixed_by_user:
            return self.params   # autonomia: parametros fijados por el usuario no se tocan
        if provenance not in ("SELF_REPORTED", "OBSERVED", "INFERRED", "UNCERTAIN"):
            raise SintoniaError(f"provenance invalido: {provenance}")
        # senales INFERRED tienen peso menor (no definir al usuario por inferencia)
        weight = 1.0 if provenance == "SELF_REPORTED" else (0.5 if provenance == "OBSERVED" else 0.2)
        if kind == "preference_pacing":
            self.params.pacing = max(1, min(5, round(1 + 4 * value * weight + self.params.pacing * (1 - weight))))
        elif kind == "preference_length":
            self.params.response_length = max(1, min(5, round(1 + 4 * value * weight + self.params.response_length * (1 - weight))))
        elif kind == "preference_questions":
            self.params.question_frequency = round(max(0.0, min(1.0,
                value * weight + self.params.question_frequency * (1 - weight))), 3)
        elif kind == "preference_formality":
            self.params.formality = max(1, min(5, round(1 + 4 * value * weight + self.params.formality * (1 - weight))))
        else:
            raise SintoniaError(f"senal desconocida: {kind}")
        self.params.__post_init__()
        return self.params

    def fix_by_user(self, **params):
        """El usuario fija parametros explicitamente (autonomia)."""
        for k, v in params.items():
            if k not in PARAM_RANGES:
                raise SintoniaError(f"parametro desconocido: {k}")
            setattr(self.params, k, v)
        self.params.fixed_by_user = True
        self.params.__post_init__()
        return self.params

    def generate_emotional_language(self, *a, **k):
        raise SintoniaError(
            "PROHIBIDO: la sintonia no genera lenguaje emocional; solo ajusta "
            "parametricos. Manipulacion/dependencia/diagnostico quedan bloqueados "
            "por MetacognitiveSecurity y por ausencia estructural de esta capacidad")
