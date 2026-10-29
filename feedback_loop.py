"""Feedback capture that can propose, but never directly apply, self changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PREFERENCE_KINDS = frozenset({"OBSERVED", "SELF_REPORTED", "INFERRED", "UNCERTAIN"})


@dataclass(frozen=True)
class PreferenceObservation:
    subject: str
    kind: str
    statement: str
    confidence: float
    evidence: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("subject must be a non-empty string")
        if self.kind not in PREFERENCE_KINDS:
            raise ValueError(f"unsupported preference kind: {self.kind}")
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise ValueError("statement must be a non-empty string")
        if isinstance(self.confidence, bool) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(self.evidence, tuple):
            raise ValueError("evidence must be a tuple")
        if self.kind == "INFERRED" and not self.evidence:
            raise ValueError("inferred preferences require evidence")
        if any(not isinstance(item, str) or not item.strip() for item in self.evidence):
            raise ValueError("evidence references must be non-empty strings")

    @property
    def fundamental(self) -> bool:
        return False

    def to_proposal(self) -> dict[str, Any]:
        return {
            "type": "preference",
            "subject": self.subject,
            "kind": self.kind,
            "statement": self.statement,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "fundamental": False,
            "route": "Feedback->Proposal->Review->R1->Versioned Evolution",
            "auto_apply": False,
        }


class FeedbackLoop:
    """Convert a decision outcome and user feedback into a non-binding proposal."""

    def run(self, decision: dict, outcome: str, user_feedback: str) -> dict[str, Any]:
        if not isinstance(decision, dict):
            raise TypeError("decision must be a mapping")
        if not isinstance(outcome, str) or not isinstance(user_feedback, str):
            raise TypeError("outcome and user_feedback must be strings")
        return {
            "decision_id": decision.get("decision_id"),
            "outcome": outcome,
            "user_feedback": user_feedback,
            "identity_direct_modification": "PROHIBITED",
            "possible_evolution": "PROPOSAL only: Feedback->Observation->Review->R1",
            "auto_apply": False,
        }
