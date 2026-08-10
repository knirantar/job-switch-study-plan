from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Protocol


CENT = Decimal("0.01")


class RiskScorer(Protocol):
    def score(self, *, claim_id: str, amount: Decimal) -> Decimal: ...


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    amount: Decimal
    tags: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def parse(cls, row: dict[str, str]) -> Claim:
        claim_id = row.get("claim_id", "").strip()
        if not claim_id:
            raise ValueError("claim_id is required")
        try:
            amount = Decimal(row["amount"]).quantize(CENT, rounding=ROUND_HALF_EVEN)
        except (KeyError, InvalidOperation) as error:
            raise ValueError("amount must be a decimal string") from error
        if not amount.is_finite() or not Decimal("0.00") <= amount <= Decimal("10000000.00"):
            raise ValueError("amount outside accepted range")
        tags = tuple(tag.strip() for tag in row.get("tags", "").split(",") if tag.strip())
        return cls(claim_id=claim_id, amount=amount, tags=tags)


@dataclass(frozen=True, slots=True)
class Outcome:
    claim_id: str
    amount: Decimal
    score: Decimal
    needs_review: bool


def process_claims(rows: Iterable[dict[str, str]], scorer: RiskScorer) -> Iterator[Outcome]:
    """Stream validated rows; fail explicitly on invalid input or scorer error."""
    for row in rows:
        claim = Claim.parse(row)
        score = scorer.score(claim_id=claim.claim_id, amount=claim.amount)
        if not Decimal("0") <= score <= Decimal("1"):
            raise ValueError(f"invalid score for {claim.claim_id}")
        yield Outcome(claim.claim_id, claim.amount, score, score >= Decimal("0.80"))
