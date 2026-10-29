"""MISION §23: Web/Mobile/Voice/API/MCP/External clients -> MISMO CognitiveTwin.
Sin memorias paralelas por cliente: todos usan ChatPipeline + ContextAssembler + Memory."""
from __future__ import annotations
import sys
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from chat import ChatPipeline


class TwinFacade:
    """Unico punto de entrada cognitivo para todos los clientes."""

    def __init__(self, chat: ChatPipeline):
        self.chat = chat
        self.clients: dict[str, dict] = {}

    def register_client(self, kind: str, client_id: str):
        if kind not in ("web", "mobile", "voice", "api", "mcp", "external"):
            raise ValueError(f"cliente no soportado: {kind}")
        self.clients[client_id] = {"kind": kind, "memory": "SHARED (via ChatPipeline)"}

    def handle(self, client_id: str, session_id: str, message: str) -> dict:
        if client_id not in self.clients:
            raise PermissionError("cliente no registrado")
        return self.chat.handle(session_id, message,
                                correlation_id=f"{client_id}:{session_id}")


class TestInteroperability:
    """Verificacion documentada en tests/test_om_gaps.py + matrix."""
