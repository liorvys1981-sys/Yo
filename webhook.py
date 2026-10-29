"""Frontera de webhooks: HMAC-SHA256 + timestamp anti-replay (Capa 16)."""
from __future__ import annotations
import hashlib, hmac
import time


class WebhookValidator:
    def __init__(self, secret: bytes, tolerance: int = 300):
        if len(secret) < 16:
            raise ValueError("secret >= 16 bytes")
        self._secret = secret
        self.tolerance = tolerance
        self._seen_ts: dict[str, int] = {}

    def sign(self, ts: int, payload: bytes, endpoint: str = "default") -> str:
        msg = f"{endpoint}.{ts}.".encode() + payload
        return hmac.new(self._secret, msg, hashlib.sha256).hexdigest()

    def validate(self, payload: bytes, signature: str, ts: int, endpoint: str = "default",
                 ip: str = "", allowlist: set | None = None,
                 now: int | None = None) -> bool:
        now = int(time.time()) if now is None else now
        if abs(now - ts) > self.tolerance:
            return False
        if allowlist is not None and ip not in allowlist:
            return False
        expected = self.sign(ts, payload, endpoint)
        if not hmac.compare_digest(expected, signature):
            return False
        last = self._seen_ts.get(endpoint, 0)
        if ts <= last:
            return False
        self._seen_ts[endpoint] = ts
        return True
