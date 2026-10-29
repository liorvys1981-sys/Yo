"""Adaptador aislado del motor de avatar (candidato: ai-avatar-system, MIT).

Interfaz + gates + contratos. NINGUN codigo del repositorio externo se copia
aqui; el adaptador define el CONTRATO que un futuro despliegue del motor
implementaria, y fuerza los gates soberanos existentes:
- generacion solo via CloneBuilder con capturas autorizadas (provenance)
- transferencia de datos al motor solo via authorize_provider_transfer (R1)
- TTS/lipsync reportan BLOCKED hasta proveedor real
Estado: contrato verificable sin hardware; ejecucion real = YC-INT-5/6.
"""

from __future__ import annotations
import sys

sys.path.insert(0, "/mnt/agents/output/APP_YO/yoclone")
sys.path.insert(0, "/mnt/agents/output/APP_YO/yoclone/providers")
from onboarding import OnboardingEngine, ProviderTransferUnauthorized
from clone_representation import CloneBuilder, ProviderRequired
from conversation import TTSEngine, LipSyncEngine


class AvatarEngine:
    """Puente entre yoclone y un motor de avatar self-hosted (p.ej. ai-avatar-system).
    Todo pasa por los gates soberanos; sin autorizacion no hay llamada al motor."""

    def __init__(self, onboarding: OnboardingEngine, builder: CloneBuilder,
                 authority_did: str, today: str):
        self.onb = onboarding
        self.builder = builder
        self.authority_did = authority_did
        self.today = today

    def build_clone(self, fidelity: float):
        refs = tuple(c["sha256"] for c in self.onb.captures if c["kind"] == "IMAGE" and c["quality"]["ok"])
        return self.builder.register(self.onb.user_id, refs, fidelity)

    def transfer_to_engine(self, engine_endpoint: str, data_kinds: tuple, authorization) -> dict:
        # gate R1 reutilizado (ya probado en la suite yoclone tests 10-12)
        return self.onb.authorize_provider_transfer(
            engine_endpoint, data_kinds, authorization, self.authority_did, self.today)

    def tts(self) -> TTSEngine:
        return TTSEngine(provider=None)   # BLOCKED hasta proveedor real

    def lipsync(self) -> LipSyncEngine:
        return LipSyncEngine(provider=None)
