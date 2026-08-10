"""Deterministic advisory routing policy; never auto-denies a claim."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

Route = Literal["STRAIGHT_THROUGH", "HUMAN_REVIEW", "HARD_STOP"]

@dataclass(frozen=True)
class Claim:
    claim_id: str
    tenant_id: str
    amount_inr: Decimal
    risk_score: Decimal
    consent_verified: bool
    duplicate_of: str | None = None

@dataclass(frozen=True)
class Decision:
    route: Route
    reasons: tuple[str, ...]
    policy_version: str = "claims-routing-2026-08-09-v1"

def route_claim(claim: Claim) -> Decision:
    if not claim.claim_id or not claim.tenant_id: raise ValueError("trusted identifiers required")
    if not claim.amount_inr.is_finite() or claim.amount_inr < 0: raise ValueError("invalid amount")
    if not claim.risk_score.is_finite() or not Decimal("0") <= claim.risk_score <= Decimal("1"):
        raise ValueError("risk score must be finite and within [0,1]")
    if not claim.consent_verified:
        return Decision("HARD_STOP", ("CONSENT_OR_AUTHORITY_NOT_VERIFIED",))
    reasons=[]
    if claim.duplicate_of: reasons.append("POSSIBLE_DUPLICATE")
    if claim.amount_inr >= Decimal("500000.00"): reasons.append("HIGH_VALUE")
    if claim.risk_score >= Decimal("0.60"): reasons.append("MODEL_RISK_REVIEW")
    return Decision("HUMAN_REVIEW", tuple(reasons)) if reasons else Decision("STRAIGHT_THROUGH", ("POLICY_CHECKS_PASSED",))

def apply_override(decision: Decision, *, reviewer_id: str, ticket: str, reason: str,
                   new_route: Route) -> Decision:
    if not all(value.strip() for value in (reviewer_id, ticket, reason)): raise ValueError("complete override evidence required")
    if decision.route == "HARD_STOP" and new_route == "STRAIGHT_THROUGH":
        raise PermissionError("hard stop cannot be bypassed by ordinary override")
    return Decision(new_route, decision.reasons + (f"OVERRIDE:{ticket}:{reviewer_id}:{reason}",))
