from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from decimal import Decimal

from claim_batch.processor import Claim, process_claims


class FixedScorer:
    def __init__(self, score: str) -> None:
        self.value = Decimal(score)

    def score(self, *, claim_id: str, amount: Decimal) -> Decimal:
        return self.value


class ProcessorTest(unittest.TestCase):
    def test_decimal_rounding_and_tags(self) -> None:
        claim = Claim.parse({"claim_id": "CLM-8421", "amount": "1250.235", "tags": "cardiac, priority "})
        self.assertEqual(claim.amount, Decimal("1250.24"))
        self.assertEqual(claim.tags, ("cardiac", "priority"))

    def test_rejects_missing_and_out_of_range_values(self) -> None:
        for row in ({"amount": "12.00"}, {"claim_id": "x", "amount": "NaN"}, {"claim_id": "x", "amount": "10000000.01"}):
            with self.subTest(row=row), self.assertRaises(ValueError):
                Claim.parse(row)

    def test_frozen_value_object(self) -> None:
        claim = Claim.parse({"claim_id": "CLM-1", "amount": "10.00"})
        with self.assertRaises(FrozenInstanceError):
            claim.amount = Decimal("20.00")  # type: ignore[misc]

    def test_generator_is_lazy(self) -> None:
        seen: list[str] = []

        def rows():
            for identifier in ("CLM-1", "CLM-2"):
                seen.append(identifier)
                yield {"claim_id": identifier, "amount": "10.00"}

        outcomes = process_claims(rows(), FixedScorer("0.75"))
        self.assertEqual(seen, [])
        self.assertEqual(next(outcomes).claim_id, "CLM-1")
        self.assertEqual(seen, ["CLM-1"])

    def test_threshold_boundary(self) -> None:
        rows = [{"claim_id": "CLM-2", "amount": "999.99"}]
        self.assertTrue(next(process_claims(rows, FixedScorer("0.80"))).needs_review)

    def test_invalid_model_output_fails_closed(self) -> None:
        rows = [{"claim_id": "CLM-3", "amount": "50.00"}]
        with self.assertRaises(ValueError):
            next(process_claims(rows, FixedScorer("1.01")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
