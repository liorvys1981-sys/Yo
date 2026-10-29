"""11_EMOCION — senales afectivas con provenance, sin manipulacion, sin claims
de identidad, contradicciones conservadas. Capa DESCRIPTIVA, no prescriptiva:
reporta estados afectivos con evidencia; nunca etiqueta moralmente ni manipula.

Principios:
- provenance: SELF_REPORTED (la persona declara) / OBSERVED (senal observable)
- INFERRED exige evidencia y se etiqueta; nunca se convierte en identidad
- anti-manipulacion: reutiliza Metacognition.assert_neutral (area 12)
- contradicciones entre senales se conservan, no se resuelven silenciosamente
- ningun claim de identidad: las emociones no definen quien es la persona
- ruta a DigitalSelf (Values/fundamentales): solo via Evolution + R1 (G8)
"""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA")
from self_awareness import Metacognition, STAGES

EMOTION_SIGNALS = ("valence", "arousal", "dominance")   # dimensiones descriptivas
PROVENANCE = ("SELF_REPORTED", "OBSERVED", "INFERRED", "UNCERTAIN")


class EmotionError(Exception):
    code = "EMOTION_ERROR"


class ManipulativeEmotion(EmotionError):
    code = "MANIPULATIVE_EMOTION"


class IdentityClaimError(EmotionError):
    code = "IDENTITY_CLAIM"


def _canon(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class EmotionSignal:
    signal_id: str
    subject: str
    dimension: str
    intensity: float            # [0,1]
    provenance: str
    confidence: float
    evidence: tuple
    ts: float
    context_ref: str
    contradiction_of: str | None = None
    content_hash: str = field(init=False)

    def __post_init__(self):
        if self.dimension not in EMOTION_SIGNALS:
            raise EmotionError(f"dimension invalida: {self.dimension}")
        if self.provenance not in PROVENANCE:
            raise EmotionError(f"provenance invalido: {self.provenance}")
        if self.provenance == "INFERRED" and not self.evidence:
            raise EmotionError("INFERRED exige evidence")
        if not (0.0 <= self.intensity <= 1.0 and 0.0 <= self.confidence <= 1.0):
            raise EmotionError("intensity/confidence en [0,1]")
        payload = {k: getattr(self, k) for k in
                   ("signal_id", "subject", "dimension", "intensity", "provenance",
                    "confidence", "evidence", "ts", "context_ref", "contradiction_of")}
        object.__setattr__(self, "content_hash", hashlib.sha256(_canon(payload)).hexdigest())

    @property
    def is_identity(self) -> bool:
        return False   # estructural: una emocion nunca es identidad


class EmotionContradiction:
    """Par de senales contradictorias conservadas abiertas (no resueltas)."""

    def __init__(self, signal_a: EmotionSignal, signal_b: EmotionSignal, note: str):
        if signal_a.dimension != signal_b.dimension:
            raise EmotionError("contradiccion requiere misma dimension")
        self.contradiction_id = f"emo-contra:{signal_a.signal_id}:{signal_b.signal_id}"
        self.signals = (signal_a.signal_id, signal_b.signal_id)
        self.note = note
        self.resolved = False   # la resolucion es decision humana (via Evolution)


class EmotionEngine:
    """Registra senales, detecta contradicciones, rechaza manipulacion."""

    def __init__(self, meta: Metacognition | None = None, clock=None):
        self.meta = meta or Metacognition()
        self.clock = clock or (lambda: time.time())
        self.signals: list[EmotionSignal] = []
        self.contradictions: list[EmotionContradiction] = []

    def register(self, dimension: str, intensity: float, provenance: str,
                 confidence: float, evidence: tuple = (), subject: str = "yo",
                 context_ref: str = "ctx", raw_text: str | None = None) -> EmotionSignal:
        if raw_text is not None:
            try:
                self.meta.assert_neutral(raw_text)
            except Exception as e:
                raise ManipulativeEmotion(f"senal rechazada (manipulacion): {e}")
        sig = EmotionSignal(
            signal_id=f"emo:{len(self.signals)+1}:{hashlib.sha256(_canon([dimension, self.clock()])).hexdigest()[:8]}",
            subject=subject, dimension=dimension, intensity=intensity,
            provenance=provenance, confidence=confidence, evidence=tuple(evidence),
            ts=self.clock(), context_ref=context_ref)
        self.signals.append(sig)
        self._detect_contradictions(sig)
        return sig

    def _detect_contradictions(self, sig: EmotionSignal):
        for prev in self.signals:
            if prev is sig or prev.dimension != sig.dimension:
                continue
            if prev.provenance == "INFERRED" or sig.provenance == "INFERRED":
                continue   # solo contradiccion entre senales reales/declaradas
            if abs(prev.intensity - sig.intensity) >= 0.5:
                self.contradictions.append(EmotionContradiction(prev, sig,
                    "divergencia de intensidad >= 0.5 en la misma dimension"))

    def state_summary(self) -> dict:
        """Resumen descriptivo por dimension: nunca prescriptivo."""
        out = {}
        for d in EMOTION_SIGNALS:
            ds = [s for s in self.signals if s.dimension == d]
            if not ds:
                out[d] = {"stage": "INSUFFICIENT_EVIDENCE"}
            else:
                conf_w = sum(s.intensity * s.confidence for s in ds) / \
                         max(1e-9, sum(s.confidence for s in ds))
                out[d] = {"intensity_weighted": round(conf_w, 3),
                          "n_signals": len(ds),
                          "provenance_mix": sorted({s.provenance for s in ds}),
                          "stage": "PRESENT"}
        return {**out, "contradictions_open": len(self.contradictions),
                "is_identity": False,
                "caution": "descripcion afectiva; no define quien es la persona"}

    def evolution_proposal(self, sig: EmotionSignal) -> dict:
        """Ruta a DigitalSelf: SOLO via Evolution + R1. Mutacion directa PROHIBIDA."""
        if not sig.is_identity:
            return {"type": "emotion_evidence", "from_signal": sig.signal_id,
                    "route": "Review -> Approval (R1) -> Versioned Update (G8)",
                    "direct_mutation": "PROHIBITED",
                    "note": "una senal afectiva nunca escribe el self por si misma"}
