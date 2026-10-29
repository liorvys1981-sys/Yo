"""Capability-limited agent registry with evidence-based trust promotion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


TRUST_LEVELS = ("shadow", "approval", "autonomous")
KNOWN_CAPABILITIES = {
    "identity": frozenset({"propose_identity_changes", "detect_contradictions"}),
    "memory": frozenset({"consolidate", "merge_memories", "mark_provenance"}),
    "reflection": frozenset({"synthesize", "infer_patterns"}),
    "pattern": frozenset({"correlate", "detect_patterns"}),
    "future": frozenset({"project_scenarios"}),
    "safety": frozenset({"veto", "audit_intents"}),
}
_PROMOTION_EVIDENCE = {"shadow": 3, "approval": 5}


class SwarmError(Exception):
    """Base error for swarm registration and trust operations."""


class UnknownCapability(SwarmError):
    pass


class TrustRampViolation(SwarmError):
    pass


class SafetyImmutable(SwarmError):
    pass


class AgentNotFound(SwarmError):
    pass


@dataclass
class Agent:
    agent_id: str
    kind: str
    purpose: str
    capabilities: frozenset[str]
    limits: tuple[str, ...] = ()
    memory_scope: str = "EXP"
    tools: tuple[str, ...] = ()
    trust: str = "shadow"
    active: bool = True
    evidence: list[str] = field(default_factory=list)
    promotion_evidence_start: int = 0


class Swarm:
    """Tracks agent capabilities and trust only; it does not execute agent tools."""

    def __init__(self, ledger=None, clock=None):
        self.ledger = ledger
        self.clock = clock
        self._agents: dict[str, Agent] = {}

    def spawn(
        self,
        agent_id: str,
        kind: str,
        purpose: str,
        capabilities,
        *,
        limits=(),
        memory_scope: str = "EXP",
        tools=(),
    ) -> Agent:
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise SwarmError("agent_id must be a non-empty string")
        if agent_id in self._agents:
            raise SwarmError(f"agent already exists: {agent_id}")
        if kind not in KNOWN_CAPABILITIES:
            raise SwarmError(f"unknown agent type: {kind}")
        if not isinstance(purpose, str) or not purpose.strip():
            raise SwarmError("purpose must be a non-empty string")

        requested = frozenset(capabilities)
        unknown = requested - KNOWN_CAPABILITIES[kind]
        if unknown:
            raise UnknownCapability(f"unsupported capabilities for {kind}: {sorted(unknown)}")
        if any(not isinstance(value, str) or not value.strip() for value in requested):
            raise UnknownCapability("capabilities must be non-empty strings")

        agent = Agent(
            agent_id=agent_id,
            kind=kind,
            purpose=purpose,
            capabilities=requested,
            limits=tuple(limits),
            memory_scope=memory_scope,
            tools=tuple(tools),
        )
        self._agents[agent_id] = agent
        self._audit("spawn", agent_id, {"type": kind, "capabilities": sorted(requested)})
        return agent

    def check(self, agent_id: str, capability: str) -> bool:
        agent = self._agents.get(agent_id)
        return bool(agent and agent.active and capability in agent.capabilities)

    def status(self, agent_id: str) -> Agent:
        return self._get(agent_id)

    def record_correct_execution(self, agent_id: str, evidence_ref: str) -> None:
        agent = self._get(agent_id)
        if not agent.active:
            raise TrustRampViolation("inactive agents cannot accumulate promotion evidence")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            raise TrustRampViolation("promotion requires a non-empty evidence reference")
        if evidence_ref in agent.evidence:
            raise TrustRampViolation("evidence references must be unique")
        agent.evidence.append(evidence_ref)
        self._audit("record_correct_execution", agent_id, {"evidence_ref": evidence_ref})

    def promote(self, agent_id: str) -> str:
        agent = self._get(agent_id)
        required = _PROMOTION_EVIDENCE.get(agent.trust)
        if required is None:
            raise TrustRampViolation("agent is already at maximum trust")
        available = len(agent.evidence) - agent.promotion_evidence_start
        if not agent.active or available < required:
            raise TrustRampViolation(
                f"{agent.trust} promotion requires {required} new verified executions; "
                f"found {available}"
            )
        agent.trust = TRUST_LEVELS[TRUST_LEVELS.index(agent.trust) + 1]
        agent.promotion_evidence_start = len(agent.evidence)
        self._audit("promote", agent_id, {"trust": agent.trust})
        return agent.trust

    def report_incident(self, agent_id: str, description: str) -> None:
        agent = self._get(agent_id)
        if not isinstance(description, str) or not description.strip():
            raise SwarmError("incident description must be non-empty")
        agent.trust = "shadow"
        agent.promotion_evidence_start = len(agent.evidence)
        self._audit("report_incident", agent_id, {"description": description, "trust": "shadow"})

    def modify_safety_rules(
        self, agent_id: str, rules: dict[str, Any], *, human_confirmed: bool = False
    ) -> None:
        agent = self._get(agent_id)
        if agent.kind != "safety":
            raise SafetyImmutable("only the safety agent owns safety rules")
        if not human_confirmed:
            raise SafetyImmutable("safety rules require explicit human confirmation")
        if not isinstance(rules, dict):
            raise TypeError("rules must be a mapping")
        if "limits" in rules:
            agent.limits = tuple(rules["limits"])
        self._audit("modify_safety_rules", agent_id, {"limits": agent.limits})

    def revoke(self, agent_id: str) -> None:
        agent = self._get(agent_id)
        agent.active = False
        agent.evidence.clear()
        self._audit("revoke", agent_id, {})

    def _get(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise AgentNotFound(f"unknown agent: {agent_id}") from exc

    def _audit(self, event: str, agent_id: str, details: dict[str, Any]) -> None:
        if self.ledger is not None:
            self.ledger.append({"event": event, "agent_id": agent_id, **details})
