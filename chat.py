"""OM-20 Chat = interfaz del Cognitive Twin.
USER -> CHAT -> SESSION -> CONTEXT -> COGNITIVE TWIN -> MEMORY/REFLECTION/INSIGHTS/
DECISION -> RESPONSE. NO chatbot paralelo."""
from __future__ import annotations
import sys
for _p in ('/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/01_IDENTIDAD', '/mnt/agents/output/EL_YO/02_MEMORIA', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/03_PERCEPCION', '/mnt/agents/output/EL_YO/04_CHAOS_TESTS', '/mnt/agents/output/EL_YO/04_COGNICION', '/mnt/agents/output/EL_YO/05_RAZONAMIENTO', '/mnt/agents/output/EL_YO/06_APRENDIZAJE', '/mnt/agents/output/EL_YO/07_INTENCION', '/mnt/agents/output/EL_YO/08_AGENCIA', '/mnt/agents/output/EL_YO/09_ACCION', '/mnt/agents/output/EL_YO/10_INTERACCION', '/mnt/agents/output/EL_YO/11_EMOCION', '/mnt/agents/output/EL_YO/12_AUTOCONCIENCIA', '/mnt/agents/output/EL_YO/13_CONTEXT', '/mnt/agents/output/EL_YO/14_DIGITAL_SELF', '/mnt/agents/output/EL_YO/15_COGNITIVE_TWIN', '/mnt/agents/output/EL_YO/16_APP_SPACE', '/mnt/agents/output/EL_YO/17_SOVEREIGNTY', '/mnt/agents/output/EL_YO/18_SECURITY', '/mnt/agents/output/EL_YO/19_GOVERNANCE', '/mnt/agents/output/EL_YO/20_AUDIT', '/mnt/agents/output/EL_YO/21_EVIDENCE_LEDGER', '/mnt/agents/output/EL_YO/22_TESTING_VALIDATION', '/mnt/agents/output/EL_YO/23_Investigacion_Experimentacion_y_Evolucion'):
    sys.path.insert(0, _p)
from relationship_model import SessionState, PolicyEngine
from vector_memory import MemoryRetriever
from context_assembly import ContextAssembler


class ChatPipeline:
    def __init__(self, twin, policy: PolicyEngine, retriever: MemoryRetriever | None = None,
                 tenant: str = "YO", owner: str = "yo", observability=None):
        self.twin = twin
        self.policy = policy
        self.retriever = retriever
        self.tenant, self.owner = tenant, owner
        self.obs = observability
        self.sessions: dict[str, SessionState] = {}

    def handle(self, session_id: str, user_message: str, correlation_id: str = "c") -> dict:
        corr = correlation_id
        s = self.sessions.setdefault(session_id, SessionState(session_id))
        if self.obs:
            self.obs.logger.log("INFO", "chat", "user_message", corr, session=session_id)
        s.add_turn("user", user_message)
        ctx = ContextAssembler().assemble(
            session={"session_id": session_id, "goal": s.current_goal},
            conversation=[t.content for t in s.turn_history],
            retriever=self.retriever, query=user_message,
            tenant_id=self.tenant, owner_id=self.owner)
        verdict = self.policy.evaluate(action_type="reflection")   # chat = low risk read path
        if verdict != "ALLOW":
            return {"response": None, "policy": verdict, "session": session_id}
        response = self._twin_response(user_message, ctx)
        s.add_turn("twin", response)
        if self.obs:
            self.obs.logger.log("INFO", "chat", "twin_response", corr, session=session_id)
            self.obs.metrics.inc("chat.messages")
        return {"response": response, "policy": verdict, "session": session_id,
                "context_labels": ctx["provenance_labels"]}

    def _twin_response(self, message: str, ctx: dict) -> str:
        mem = ctx.get("relevant_memory", [])
        if mem:
            return f"[twin] segun tu memoria relevante ({mem[0]['memory'][:60]}...): " \
                   f"registro tu mensaje para reflexion."
        return "[twin] mensaje registrado en la sesion; reflexion pendiente de contexto."
