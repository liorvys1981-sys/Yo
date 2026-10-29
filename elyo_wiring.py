"""G12 WIRING — factoria del AuthorizationGate REAL de EL_YO/SAOS17.

Reglas: ninguna autoridad paralela en APP YO. Si el gate real no esta
disponible o no cumple el contrato -> ElyoGateUnavailable (bloqueo REGISTRADO,
nunca sustituto silencioso, requisito 11).
"""
from __future__ import annotations
import sys

EL_YO_GOBIERNO = "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO"
_REQUIRED_METHODS = ("authorize",)


class ElyoGateUnavailable(Exception):
    code = "ELYO_GATE_UNAVAILABLE"


def _load_elyo_gate():
    if EL_YO_GOBIERNO not in sys.path:
        sys.path.insert(0, EL_YO_GOBIERNO)
    try:
        from el_yo.gates import AuthorizationGate, DailyCodeProvider
        from el_yo.constitution import Action, Denied
    except ImportError as e:
        raise ElyoGateUnavailable(
            f"AuthorizationGate real no importable desde {EL_YO_GOBIERNO}: {e}. "
            "BLOQUEO REGISTRADO: no se creara sustituto.") from e
    for m in _REQUIRED_METHODS:
        if not callable(getattr(AuthorizationGate, m, None)):
            raise ElyoGateUnavailable(
                f"AuthorizationGate real carece de '{m}'. BLOQUEO REGISTRADO.")
    return AuthorizationGate, DailyCodeProvider


def make_elyo_gate(key: bytes, today: str, second_key: bool = True):
    """Construye el AuthorizationGate REAL de EL_YO. Cero logica duplicada."""
    AuthorizationGate, DailyCodeProvider = _load_elyo_gate()
    return AuthorizationGate(DailyCodeProvider(key), today,
                             second_key_present=second_key)


def elyo_code(key: bytes, today: str) -> str:
    _, DailyCodeProvider = _load_elyo_gate()
    return DailyCodeProvider(key).code(today)
