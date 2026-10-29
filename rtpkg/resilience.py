"""Modulo de paquete rtpkg — reorganizacion del Agent Runtime (baseline-safe)."""
from __future__ import annotations
import sys
import hashlib, json, time

for _p in ("/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO",
           "/mnt/agents/output/EL_YO/05_RAZONAMIENTO",
           "/mnt/agents/output/EL_YO/02_MEMORIA",
           "/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA",
           "/mnt/agents/output/EL_YO/23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION",
           "/mnt/agents/output/EL_YO/17_SOVEREIGNTY"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contracts import _canon, CircuitOpen, RuntimeError_


class CircuitBreaker:
    def __init__(self, threshold: int = 3, clock=None):
        self.threshold, self.fails, self.opened = threshold, 0, False
        self.clock = clock or (lambda: time.time())

    def call(self, fn, *args, **kw):
        if self.opened:
            raise CircuitOpen("circuito abierto")
        try:
            r = fn(*args, **kw)
            self.fails = 0
            return r
        except Exception:
            self.fails += 1
            if self.fails >= self.threshold:
                self.opened = True
            raise

    def reset(self):
        self.fails, self.opened = 0, False
class InfrastructureRecovery:
    """Idempotencia, retries con backoff, timeouts, circuit breaker."""

    def __init__(self, clock=None):
        self.clock = clock or (lambda: time.time())
        self.seen: set[str] = set()

    def idempotency_key(self, task: dict) -> str:
        return hashlib.sha256(_canon([task.get("task_id"), task.get("kind"),
                                      task.get("payload")])).hexdigest()[:16]

    def execute(self, task: dict, fn, *, retries: int = 3, timeout_s: float = 5.0,
                breaker: CircuitBreaker | None = None) -> dict:
        key = self.idempotency_key(task)
        if key in self.seen:
            return {"result": None, "idempotent_skip": True, "key": key}
        last = None
        for attempt in range(retries):
            start = self.clock()
            try:
                call = (lambda: breaker.call(fn, task)) if breaker else (lambda: fn(task))
                r = call()
                self.seen.add(key)
                return {"result": r, "attempts": attempt + 1, "key": key,
                        "duration": round(self.clock() - start, 6)}
            except CircuitOpen:
                raise
            except Exception as e:
                last = e
                time.sleep(0)   # backoff determinista (sin espera real; reloj inyectable)
        raise RuntimeError_(f"agotados {retries} intentos: {last}")


# ============ MemoryCognition ============
