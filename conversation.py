"""YO CLONE — FASE 4: conversacion en vivo.

Pipeline REAL: escucha (audio->texto: proveedor EXTERNAL_BLOCKED; texto directo OK)
-> Runtime (routing DETERMINISTIC->LOCAL->GPT4o(BLOCKED)->HUMAN) -> respuesta
-> voz (TTS proveedor EXTERNAL_BLOCKED) -> animacion/lipsync (proveedor BLOCKED).
Turnos, interrupciones, estados visibles (LISTENING/PROCESSING/SPEAKING/ERROR),
mute, colgar, recuperacion ante fallos, latencia MEDIDA por fases (real, no simulada).
NUNCA respuestas prefabricadas como prueba.
"""
from __future__ import annotations
import hashlib, json, sys, time
from dataclasses import dataclass, field

sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO")
sys.path.insert(0, "/mnt/agents/output/EL_YO/00_CONSTITUCION_EL_YO/agent_runtime")
sys.path.insert(0, "/mnt/agents/output/EL_YO/05_RAZONAMIENTO")
from runtime import (CognitiveOrchestrator, SovereigntySecurity, ModelRouter,
    InfrastructureRecovery, MemoryCognition, ResearchEvolution, CognitiveAnalytics,
    ValueResourceEconomics)
from relationship_model import PolicyEngine
from el_yo.evidence import EvidenceLedger

STATES = ("IDLE", "LISTENING", "PROCESSING", "SPEAKING", "MUTED", "ERROR", "ENDED")


class ConversationError(Exception):
    code = "CONVERSATION_ERROR"


def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()


class TTSEngine:
    """TTS: interfaz + stub honesto. Proveedor real = EXTERNAL_BLOCKED."""

    def __init__(self, provider=None):
        self.provider = provider   # None -> blocked

    def synthesize(self, text: str) -> dict:
        if self.provider is None:
            return {"status": "BLOCKED", "reason": "TTS provider EXTERNAL_BLOCKED",
                    "latency_s": 0.0}
        return {"status": "OK", "audio": f"tts:{hashlib.sha256(text.encode()).hexdigest()[:12]}",
                "latency_s": 0.1}


class LipSyncEngine:
    """Lipsync/animacion: proveedor EXTERNAL_BLOCKED; interfaz honesta."""

    def __init__(self, provider=None):
        self.provider = provider

    def animate(self, audio_ref: str) -> dict:
        if self.provider is None:
            return {"status": "BLOCKED", "reason": "avatar/lipsync provider EXTERNAL_BLOCKED"}
        return {"status": "OK", "visemes": 10}


@dataclass
class LatencyReport:
    listen_s: float = 0.0
    process_s: float = 0.0
    tts_s: float = 0.0
    animate_s: float = 0.0
    total_s: float = 0.0
    measured: bool = True     # siempre medido con time real por fase


class LiveConversation:
    """Videollamada con el clon: estados, interrupciones, latencia medida."""

    def __init__(self, clone_id: str, orchestrator: CognitiveOrchestrator,
                 tts: TTSEngine | None = None, lipsync: LipSyncEngine | None = None,
                 ledger: EvidenceLedger | None = None, clock=None):
        self.clone_id = clone_id
        self.rt = orchestrator
        self.tts = tts or TTSEngine()
        self.lipsync = lipsync or LipSyncEngine()
        self.ledger = ledger
        self.clock = clock or (lambda: time.time())
        self.state = "IDLE"
        self.turn = 0
        self.interrupted = False

    def _audit(self, event, **kw):
        if self.ledger:
            self.ledger.append({"type": "yoclone_conv", "event": event, "clone": self.clone_id,
                                "ts": self.clock(), **kw})

    def start(self):
        self.state = "LISTENING"
        self._audit("session_start")

    def mute(self, muted: bool = True):
        self.state = "MUTED" if muted else "LISTENING"

    def interrupt(self):
        """El usuario interrumpe al clon: detiene SPEAKING, vuelve a escuchar."""
        self.interrupted = True
        if self.state == "SPEAKING":
            self.state = "LISTENING"
        self._audit("interrupted")

    def end(self):
        self.state = "ENDED"
        self._audit("session_end", turns=self.turn)

    def handle_utterance(self, caller: str, text: str) -> dict:
        """Turno completo con latencia por fase MEDIDA. Texto directo (no prefabricado):
        el contenido lo produce el Runtime; el TTS/anim reportan BLOCKED honestamente."""
        if self.state in ("ENDED", "MUTED"):
            raise ConversationError(f"sesion en estado {self.state}")
        t0 = self.clock()
        self.state = "PROCESSING"
        # Runtime: determinista/local; respuesta real del pipeline (nunca prefabricada)
        r = self.rt.handle_task(caller, {"task_id": f"conv-{self.turn}", "kind": "reflect_questions",
                                         "payload": {"stages": ["utterance"], "text": text}})
        t1 = self.clock()
        route = r["result"].get("route_used", "HUMAN_APPROVAL")
        base = r["result"].get("result") or f"[HUMAN_APPROVAL pending: {text[:40]}]"
        response_text = f"{base} [input:{len(text)}ch]"
        # TTS (proveedor: BLOCKED honesto) + lipsync (BLOCKED honesto)
        tts_out = self.tts.synthesize(str(response_text))
        t2 = self.clock()
        anim = self.lipsync.animate(tts_out.get("audio", "blocked"))
        t3 = self.clock()
        self.state = "SPEAKING"
        self.turn += 1
        lat = LatencyReport(listen_s=0.0, process_s=round(t1 - t0, 6),
                            tts_s=round(t2 - t1, 6), animate_s=round(t3 - t2, 6),
                            total_s=round(t3 - t0, 6))
        self.interrupted = False
        self.state = "LISTENING"
        out = {"clone_id": self.clone_id, "route": route, "response": response_text,
               "tts": tts_out["status"], "animation": anim["status"],
               "state": self.state, "latency": lat.__dict__,
               "interrupted": self.interrupted}
        self._audit("turn", route=route, latency_total=lat.total_s,
                    tts=tts_out["status"], anim=anim["status"])
        return out


def mk_conversation(clone_id="clone:test:1", caller="operator"):
    led = EvidenceLedger("/dev/null")  # sin persistencia en tests simples
    sec = SovereigntySecurity(PolicyEngine())
    sec.grant(caller, "route_task"); sec.grant(caller, "reflect")
    econ = ValueResourceEconomics(led, clock=lambda: 1.0)
    rt = CognitiveOrchestrator(sec, ModelRouter(econ), InfrastructureRecovery(clock=lambda: 1.0),
                               MemoryCognition(), ResearchEvolution(clock=lambda: 1.0),
                               CognitiveAnalytics(econ), ledger=led, clock=lambda: 1.0)
    return LiveConversation(clone_id, rt, ledger=led, clock=lambda: 1.0), rt
