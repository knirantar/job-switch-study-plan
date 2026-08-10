import unittest
from decimal import Decimal
from decision_policy import Claim, apply_override, route_claim

def claim(**changes):
    values=dict(claim_id="C1001",tenant_id="T7",amount_inr=Decimal("18500.00"),risk_score=Decimal("0.20"),consent_verified=True)
    values.update(changes); return Claim(**values)

class PolicyTest(unittest.TestCase):
    def test_low_risk_straight_through(self): self.assertEqual("STRAIGHT_THROUGH",route_claim(claim()).route)
    def test_threshold_is_inclusive(self): self.assertEqual("HUMAN_REVIEW",route_claim(claim(risk_score=Decimal("0.60"))).route)
    def test_high_value_routes_to_human(self): self.assertIn("HIGH_VALUE",route_claim(claim(amount_inr=Decimal("500000.00"))).reasons)
    def test_model_never_denies(self): self.assertEqual("HUMAN_REVIEW",route_claim(claim(risk_score=Decimal("0.99"))).route)
    def test_missing_authority_hard_stops(self): self.assertEqual("HARD_STOP",route_claim(claim(consent_verified=False)).route)
    def test_nan_rejected(self):
        with self.assertRaises(ValueError): route_claim(claim(risk_score=Decimal("NaN")))
    def test_hard_stop_cannot_be_ordinary_override(self):
        with self.assertRaises(PermissionError): apply_override(route_claim(claim(consent_verified=False)),reviewer_id="u7",ticket="INC-1",reason="urgent",new_route="STRAIGHT_THROUGH")
    def test_override_requires_evidence(self):
        with self.assertRaises(ValueError): apply_override(route_claim(claim()),reviewer_id="u7",ticket="",reason="review",new_route="HUMAN_REVIEW")

if __name__ == "__main__": unittest.main()
