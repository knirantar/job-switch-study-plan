"""Explainable shared-cost allocation and tenant budget enforcement."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CENT=Decimal("0.01")

@dataclass(frozen=True)
class Usage:
    tenant: str
    requests: int
    gpu_seconds: Decimal
    storage_gib_month: Decimal

def allocate_shared(total: Decimal, usage: list[Usage], weights: tuple[Decimal,Decimal,Decimal]) -> dict[str,Decimal]:
    if total < 0 or not usage or any(x < 0 for x in weights) or sum(weights) != Decimal("1"):
        raise ValueError("valid total, usage, and weights summing to one required")
    if len({u.tenant for u in usage}) != len(usage): raise ValueError("duplicate tenant")
    totals=(sum(u.requests for u in usage),sum((u.gpu_seconds for u in usage),Decimal()),sum((u.storage_gib_month for u in usage),Decimal()))
    if any(t == 0 and w > 0 for t,w in zip(totals,weights)): raise ValueError("weighted driver has zero usage")
    raw={}
    for u in usage:
        shares=(Decimal(u.requests)/Decimal(totals[0]) if totals[0] else Decimal(),u.gpu_seconds/totals[1] if totals[1] else Decimal(),u.storage_gib_month/totals[2] if totals[2] else Decimal())
        raw[u.tenant]=total*sum((w*s for w,s in zip(weights,shares)),Decimal())
    # Largest-remainder cents: exact conservation with deterministic tenant tie-break.
    floor={k:v.quantize(CENT,rounding="ROUND_DOWN") for k,v in raw.items()}
    cents=int(((total-sum(floor.values()))/CENT).to_integral_value())
    order=sorted(raw,key=lambda k:(-(raw[k]-floor[k]),k))
    for tenant in order[:cents]: floor[tenant]+=CENT
    return floor

def budget_status(spend: Decimal, budget: Decimal, forecast: Decimal) -> str:
    if min(spend,budget,forecast) < 0 or budget == 0: raise ValueError("positive budget and nonnegative values required")
    if spend > budget: return "EXCEEDED"
    if forecast > budget: return "FORECAST_BREACH"
    if spend >= budget*Decimal("0.8"): return "WATCH"
    return "OK"
