"""OM-25 Observability: structured logging, metrics, tracing, correlation_id,
audit events, health checks. Reconstruye USER->REQUEST->OP->MEMORY->DECISION->RESULT->
EVIDENCE. NO secretos, NO razonamiento privado."""
from __future__ import annotations
import hashlib, json, time

_SENSITIVE = ("secret", "password", "token", "private", "seed", "key")


def _sanitize(fields: dict) -> dict:
    return {k: ("[REDACTED]" if any(s in k.lower() for s in _SENSITIVE) else v)
            for k, v in fields.items()}


class Correlation:
    def __init__(self, seed: str):
        self.id = hashlib.sha256(seed.encode()).hexdigest()[:16]


class StructuredLogger:
    def __init__(self):
        self.events: list[dict] = []

    def log(self, level: str, component: str, message: str, correlation_id: str,
            **fields) -> dict:
        if level == "DEBUG" and any("chain_of_thought" in k or "reasoning" in k for k in fields):
            raise ValueError("razonamiento privado prohibido en logs")
        ev = {"ts": time.time(), "level": level, "component": component,
              "message": message, "correlation_id": correlation_id,
              "fields": _sanitize(fields)}
        self.events.append(ev)
        return ev


class Metrics:
    def __init__(self):
        self.counters: dict[str, int] = {}
        self.latencies: dict[str, list] = {}

    def inc(self, name: str, n: int = 1):
        self.counters[name] = self.counters.get(name, 0) + n

    def observe(self, name: str, seconds: float):
        self.latencies.setdefault(name, []).append(round(seconds, 6))

    def snapshot(self) -> dict:
        return {"counters": dict(self.counters),
                "latencies": {k: {"count": len(v), "avg": round(sum(v) / len(v), 6) if v else 0}
                              for k, v in self.latencies.items()}}


class Tracer:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.spans: list[dict] = []

    def span(self, name: str, correlation_id: str, fn, **fields):
        start = time.time()
        result = fn()
        self.spans.append({"name": name, "correlation_id": correlation_id,
                           "duration_s": round(time.time() - start, 6)})
        self.logger.log("INFO", "tracer", f"span:{name}", correlation_id, **fields)
        return result


class HealthChecks:
    def __init__(self):
        self.checks: dict[str, callable] = {}

    def register(self, name: str, fn):
        self.checks[name] = fn

    def run_all(self) -> dict:
        out = {}
        for name, fn in self.checks.items():
            try:
                out[name] = {"status": "OK" if fn() else "DEGRADED"}
            except Exception as e:
                out[name] = {"status": "FAIL", "error": str(e)[:80]}
        return out


class AuditEvents:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def record(self, action: str, actor: str, target: str, correlation_id: str,
               allowed: bool, reason: str = ""):
        self.logger.log("AUDIT", "authz", action, correlation_id,
                        actor=actor, target=target, allowed=allowed, reason=reason)


class Observability:
    """Facade: trazabilidad completa sin secretos ni razonamiento privado."""

    def __init__(self, seed: str = "om"):
        self.correlation = Correlation(seed)
        self.logger = StructuredLogger()
        self.metrics = Metrics()
        self.tracer = Tracer(self.logger)
        self.health = HealthChecks()
        self.audit = AuditEvents(self.logger)

    def reconstruct(self, correlation_id: str) -> list:
        """USER->REQUEST->OP->MEMORY->DECISION->RESULT->EVIDENCE reconstruible."""
        return [e for e in self.logger.events if e["correlation_id"] == correlation_id]
