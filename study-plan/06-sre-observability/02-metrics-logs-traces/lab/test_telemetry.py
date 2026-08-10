#!/usr/bin/env python3

import unittest

from telemetry import Span, critical_path_ms, fraction_at_or_below, histogram_counts, redact_log, series_upper_bound, validate_trace


TRACE = [
    Span("4bf92f3577b34da6a3ce929d0e0e4736", "a1", None, "gateway", 12, "OK"),
    Span("4bf92f3577b34da6a3ce929d0e0e4736", "b2", "a1", "claims-api", 36, "OK"),
    Span("4bf92f3577b34da6a3ce929d0e0e4736", "c3", "b2", "postgres", 41, "ERROR"),
    Span("4bf92f3577b34da6a3ce929d0e0e4736", "d4", "b2", "redis", 7, "OK"),
]


class TelemetryTest(unittest.TestCase):
    def test_cardinality_product(self) -> None:
        self.assertEqual(series_upper_bound({"service": 12, "route": 40, "region": 3, "status_class": 5}), 7_200)
        with self.assertRaises(ValueError):
            series_upper_bound({"user_id": 2_000_000})

    def test_histogram_is_cumulative(self) -> None:
        counts, count, total = histogram_counts([0.04, 0.08, 0.12, 0.30, 1.20], [0.1, 0.25, 0.5, 1.0])
        self.assertEqual(counts, [2, 3, 4, 4])
        self.assertEqual(count, 5)
        self.assertAlmostEqual(total, 1.74)
        self.assertEqual(fraction_at_or_below([0.04, 0.08, 0.12, 0.30, 1.20], 0.25), 0.6)

    def test_trace_structure_and_simplified_path(self) -> None:
        self.assertEqual(validate_trace(TRACE), [])
        self.assertEqual(critical_path_ms(TRACE), 89)

    def test_orphan_is_rejected(self) -> None:
        broken = TRACE + [Span(TRACE[0].trace_id, "e5", "missing", "queue", 5, "OK")]
        self.assertIn("orphan span e5", validate_trace(broken))

    def test_sensitive_log_fields_are_redacted(self) -> None:
        event = redact_log({"route": "/claims", "patient_id": "123456789012", "detail": "Authorization: Bearer secret.value"})
        self.assertEqual(event["route"], "/claims")
        self.assertEqual(event["patient_id"], "[REDACTED]")
        self.assertEqual(event["detail"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
