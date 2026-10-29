"""COGNITIVE API — interfaces ABC entre APP YO y EL_YO Control Plane.

Contratos. La ABC fuerza validacion de contexto de tenant en METODOS CONCRETOS;
la implementacion va en _impl_* abstractos. Asi ningun implementador puede
omitir la validacion (enforcement estructural, no por convencion).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


class CognitiveAPIError(Exception):
    code = "GENERIC"


class DeniedPolicy(CognitiveAPIError):
    code = "DENIED_POLICY"


class DeniedTenant(CognitiveAPIError):
    code = "DENIED_TENANT"


class Unprovenanced(CognitiveAPIError):
    code = "UNPROVENANCED"


class EvolutionLocked(CognitiveAPIError):
    code = "EVOLUTION_LOCKED"


class ReplayStale(CognitiveAPIError):
    code = "REPLAY_STALE"


@dataclass(frozen=True)
class RequestContext:
    """Obligatorio en TODA consulta. Campo vacio => DeniedTenant."""
    tenant_id: str
    subject_id: str
    cognitive_instance_id: str
    memory_scope: str
    authorization_scope: str

    @classmethod
    def require(cls, ctx: "RequestContext | None") -> "RequestContext":
        if ctx is None or not all([ctx.tenant_id, ctx.subject_id,
                                   ctx.cognitive_instance_id,
                                   ctx.memory_scope, ctx.authorization_scope]):
            raise DeniedTenant("contexto de tenant incompleto")
        return ctx


class CognitiveAPI(ABC):
    """Base abstracta: ninguna implementacion concreta sin version de contrato."""

    @property
    @abstractmethod
    def api_version(self) -> str:
        """Version del contrato que implementa (breaking changes exigen gate)."""
        ...


class MemoryAPI(CognitiveAPI):
    @property
    def api_version(self) -> str:
        return "v0.1"

    def store(self, ctx: RequestContext, record: dict) -> str:
        RequestContext.require(ctx)
        return self._store_impl(ctx, record)

    def query(self, ctx: RequestContext, memory_type: str, filters: dict | None = None) -> list:
        RequestContext.require(ctx)
        return self._query_impl(ctx, memory_type, filters)

    def forget(self, ctx: RequestContext, memory_id: str) -> str:
        RequestContext.require(ctx)
        return self._forget_impl(ctx, memory_id)

    @abstractmethod
    def _store_impl(self, ctx: RequestContext, record: dict) -> str: ...

    @abstractmethod
    def _query_impl(self, ctx: RequestContext, memory_type: str,
                    filters: dict | None = None) -> list: ...

    @abstractmethod
    def _forget_impl(self, ctx: RequestContext, memory_id: str) -> str: ...


class EvidenceAPI(CognitiveAPI):
    """append/verify de evidencia; implementacion concreta = GenomeStore (Fase 4)."""

    @property
    def api_version(self) -> str:
        return "v0.1"

    def append(self, ctx: RequestContext, event: dict) -> str:
        RequestContext.require(ctx)
        return self._append_impl(ctx, event)

    def verify(self, ctx: RequestContext) -> bool:
        RequestContext.require(ctx)
        return self._verify_impl(ctx)

    @abstractmethod
    def _append_impl(self, ctx: RequestContext, event: dict) -> str: ...

    @abstractmethod
    def _verify_impl(self, ctx: RequestContext) -> bool: ...


class InsightsAPI(CognitiveAPI):
    """INSIGHT -> hipotesis -> confirmado/refutado. Nunca verdad automatica."""

    @property
    def api_version(self) -> str:
        return "v0.1"

    def list(self, ctx: RequestContext, kind: str | None = None) -> list:
        RequestContext.require(ctx)
        return self._list_impl(ctx, kind)

    def state_change(self, ctx: RequestContext, insight_id: str, new_state: str,
                     evidence: tuple, confirmed_by: str = "system") -> dict:
        RequestContext.require(ctx)
        return self._state_change_impl(ctx, insight_id, new_state, evidence, confirmed_by)

    @abstractmethod
    def _list_impl(self, ctx: RequestContext, kind: str | None = None) -> list: ...

    @abstractmethod
    def _state_change_impl(self, ctx: RequestContext, insight_id: str,
                           new_state: str, evidence: tuple,
                           confirmed_by: str = "system") -> dict: ...
