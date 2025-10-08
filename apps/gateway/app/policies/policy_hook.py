from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REVIEW = "REVIEW"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reasons: List[str] = field(default_factory=list)


@dataclass
class PolicyInput:
    intent_id: str
    agent_id: str
    customer_id: str
    amount_cents: int
    currency: str
    risk_signals: Dict[str, Any]


def evaluate_policy(data: PolicyInput) -> PolicyResult:
    """Default policy hook.

    Replace this stub with bespoke trust-and-safety logic or a call into an
    external policy engine. The default behaviour allows all traffic and
    escalates orders over $1,000 for human review.
    """

    reasons: List[str] = []

    if data.amount_cents > 100_000:
        reasons.append("Amount exceeds default review threshold ($1k)")
        return PolicyResult(decision=PolicyDecision.REVIEW, reasons=reasons)

    if data.risk_signals.get("deny"):
        reasons.append(str(data.risk_signals["deny"]))
        return PolicyResult(decision=PolicyDecision.DENY, reasons=reasons)

    if data.risk_signals.get("review"):
        reasons.append(str(data.risk_signals["review"]))
        return PolicyResult(decision=PolicyDecision.REVIEW, reasons=reasons)

    return PolicyResult(decision=PolicyDecision.ALLOW, reasons=reasons)
