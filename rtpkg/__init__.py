"""Public facade for the reorganized agent runtime."""

from importlib import import_module

_EXPORT_MODULES = {
    "BudgetExceeded": "contracts",
    "CapabilityDenied": "contracts",
    "CircuitOpen": "contracts",
    "PUBLIC_IDENTITIES": "contracts",
    "ROUTES": "contracts",
    "RuntimeError_": "contracts",
    "TimeoutError_": "contracts",
    "UNIT_COSTS": "contracts",
    "ResourceManager": "security_resources",
    "SovereigntySecurity": "security_resources",
    "TaskBudget": "security_resources",
    "ValueResourceEconomics": "security_resources",
    "LocalModelStub": "models",
    "ModelRouter": "models",
    "CircuitBreaker": "resilience",
    "InfrastructureRecovery": "resilience",
    "CognitiveAnalytics": "cognition",
    "MemoryCognition": "cognition",
    "ResearchEvolution": "research",
    "CognitiveOrchestrator": "core",
}

__all__ = list(_EXPORT_MODULES)


def __getattr__(name):
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value
