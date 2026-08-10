#!/usr/bin/env python3

import unittest

from capacity import achieved_rpo_seconds, achieved_rto_seconds, backlog_drain_seconds, peak_rps, replicas_for_peak, replicas_for_zone_loss, retained_bytes


class CapacityTest(unittest.TestCase):
    def test_peak_and_replicas(self) -> None:
        peak = peak_rps(43_200_000, 6)
        self.assertEqual(peak, 3_000)
        self.assertEqual(replicas_for_peak(peak, 250, 0.30), 18)

    def test_zone_loss_capacity(self) -> None:
        self.assertEqual(replicas_for_zone_loss(required_healthy=18, zones=3), 27)

    def test_backlog_drain_uses_net_rate(self) -> None:
        self.assertEqual(backlog_drain_seconds(3_600_000, 2_000, 5_000), 1_200)
        with self.assertRaises(ValueError):
            backlog_drain_seconds(100, 5_000, 5_000)

    def test_storage_includes_replication_and_overhead(self) -> None:
        value = retained_bytes(12_000, 1_200, 7 * 86_400, 3, 1.20)
        self.assertEqual(value, 31_352_832_000_000)

    def test_recovery_objectives_are_measured_from_failure(self) -> None:
        self.assertEqual(achieved_rpo_seconds(1_000, 1_030), 30)
        self.assertEqual(achieved_rto_seconds(1_030, 3_730), 2_700)

    def test_invalid_time_order_rejected(self) -> None:
        with self.assertRaises(ValueError):
            achieved_rpo_seconds(2_000, 1_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
