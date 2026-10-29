"""OM-P11/P12 Interfaces desacopladas: SSE, WebSocket, Voice. Sin acoplar a proveedor.
Transporte en memoria (determinista); produccion intercambia el backend."""
from __future__ import annotations


class SSEStream:
    def __init__(self):
        self.events: list[str] = []

    def push(self, data: str, event: str = "message") -> str:
        payload = f"event: {event}\ndata: {data}\n\n"
        self.events.append(payload)
        return payload

    def read_all(self) -> list:
        return list(self.events)


class RealtimeSession:
    """WebSocket-style session en memoria: send/recv con aislamiento por session_id,
    reconnect (resume desde ultimo evento entregado) y correlation_id."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.inbox: list = []
        self.outbox: list = []
        self._cursor = 0
        self.correlation_ids: list = []

    def reconnect(self) -> list:
        """Resume: entrega los eventos no confirmados desde el ultimo cursor."""
        pending = self.outbox[self._cursor:]
        self._cursor = len(self.outbox)
        return pending

    def ack(self):
        self._cursor = len(self.outbox)

    def send(self, message: dict, correlation_id: str | None = None):
        self.outbox.append({"session": self.session_id, **message})
        if correlation_id:
            self.correlation_ids.append(correlation_id)



    def recv(self, message: dict):
        self.inbox.append({"session": self.session_id, **message})


class VoiceProvider:
    """Interfaz: SpeechInput/SpeechOutput/RealtimeSession de voz. Sin proveedor acoplado."""

    def __init__(self, backend=None):
        self.backend = backend   # None = no activado (regla: no activar comerciales innecesariamente)

    def speech_input(self, audio_bytes: bytes) -> dict:
        if self.backend is None:
            raise NotImplementedError("VoiceProvider sin backend: interfaz lista, proveedor NO activado")
        return self.backend.transcribe(audio_bytes)

    def speech_output(self, text: str) -> bytes:
        if self.backend is None:
            raise NotImplementedError("sin backend")
        return self.backend.synthesize(text)


class MCPGateway:
    """Cognitive Twin -> Permission Layer -> Policy -> (Authorization) -> MCP -> Tool -> Result
    -> Evidence. Cada herramienta: identity/permission/scope/audit/provenance/result.
    NUNCA: twin -> arbitrary tool."""

    def __init__(self, policy):
        self.policy = policy
        self.tools: dict[str, dict] = {}
        self.audit_log: list = []

    def register_tool(self, name: str, handler, *, identity: str, permission: str,
                      scope: tuple, risk: str = "LOW"):
        self.tools[name] = {"handler": handler, "identity": identity,
                            "permission": permission, "scope": tuple(scope), "risk": risk}

    def call(self, twin_id: str, tool: str, args: dict, tenant: str = "YO",
             action_type: str = "analysis") -> dict:
        if tool not in self.tools:
            raise PermissionError(f"herramienta no registrada: {tool} (arbitrary tool DENEGADO)")
        t = self.tools[tool]
        if action_type not in t["scope"]:   # scope estricto, sin wildcards
            raise PermissionError(f"scope {action_type} no permitido para {tool}")
        verdict = self.policy.evaluate(action_type=action_type, tool=tool,
                                       risk_override=t["risk"])
        if verdict in ("DENY", "ESCALATE") and t["risk"] != "LOW":
            entry = {"twin": twin_id, "tool": tool, "verdict": verdict, "executed": False}
            self.audit_log.append(entry)
            return {"result": None, "verdict": verdict, "audit": entry,
                    "note": "ESCALATE -> R1 (autoridad soberana)"}
        result = t["handler"](**args)
        entry = {"twin": twin_id, "tool": tool, "verdict": verdict, "executed": True,
                 "provenance": "SYSTEM_DERIVED", "result_hash":
                 __import__("hashlib").sha256(str(result).encode()).hexdigest()[:16]}
        self.audit_log.append(entry)
        return {"result": result, "verdict": verdict, "audit": entry}
