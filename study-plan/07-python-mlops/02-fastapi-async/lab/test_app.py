from __future__ import annotations

import asyncio
import unittest
from decimal import Decimal

from fastapi.testclient import TestClient

from app import app


HEADERS = {"x-api-key": "lab-key-2026"}


class ApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

    def test_health_and_openapi(self) -> None:
        self.assertEqual(self.client.get("/livez").json(), {"status": "alive"})
        self.assertEqual(self.client.get("/readyz").status_code, 200)
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/v1/scores", schema["paths"])
        self.assertNotIn("/livez", schema["paths"])

    def test_authentication_is_required(self) -> None:
        response = self.client.post("/v1/scores", json={"claim_id": "CLM-42", "amount": "1250.00"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "invalid credentials"})

    def test_strict_body_contract(self) -> None:
        accepted = self.client.post("/v1/scores", headers=HEADERS, json={"claim_id": "CLM-42", "amount": "1250.00"})
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.json()["risk_score"], "0.125")

        for body in (
            {"claim_id": "42", "amount": "1250.00"},
            {"claim_id": "CLM-42", "amount": "NaN"},
            {"claim_id": "CLM-42", "amount": "1.00", "tenant": "other"},
            {"claim_id": "CLM-42", "amount": 1250.00},
        ):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/v1/scores", headers=HEADERS, json=body).status_code, 422)

    def test_response_threshold(self) -> None:
        response = self.client.post("/v1/scores", headers=HEADERS, json={"claim_id": "CLM-9", "amount": "8000.00"})
        self.assertTrue(response.json()["needs_review"])

    def test_deadline_maps_to_504(self) -> None:
        async def slow(_: Decimal) -> Decimal:
            await asyncio.sleep(0.3)
            return Decimal("0.1")

        self.client.app.state.runtime.scorer.score = slow
        response = self.client.post("/v1/scores", headers=HEADERS, json={"claim_id": "CLM-7", "amount": "1.00"})
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json(), {"detail": "scoring deadline exceeded"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
