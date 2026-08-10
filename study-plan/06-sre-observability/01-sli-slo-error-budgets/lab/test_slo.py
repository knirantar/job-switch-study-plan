#!/usr/bin/env python3

import unittest

from slo import Window, budget_consumed, budget_events, burn_rate, qualifies_multiwindow_page


class SloTest(unittest.TestCase):
    def test_monthly_request_budget(self) -> None:
        self.assertAlmostEqual(budget_events(50_000_000, 0.999), 50_000)

    def test_burn_rate(self) -> None:
        self.assertAlmostEqual(burn_rate(Window(good=99_800, total=100_000), 0.999), 2.0)

    def test_budget_consumed(self) -> None:
        self.assertAlmostEqual(budget_consumed(Window(good=999_500, total=1_000_000), 0.999), 0.5)

    def test_fast_page_needs_both_windows(self) -> None:
        hot = Window(good=98_000, total=100_000)  # 2% errors = 20x burn
        calm = Window(good=99_950, total=100_000)  # 0.05% errors = 0.5x burn
        self.assertFalse(qualifies_multiwindow_page(hot, calm, calm, calm, 0.999))
        self.assertTrue(qualifies_multiwindow_page(hot, hot, calm, calm, 0.999))

    def test_slow_page_pair(self) -> None:
        slow = Window(good=99_300, total=100_000)  # 0.7% errors = 7x burn
        calm = Window(good=99_950, total=100_000)
        self.assertTrue(qualifies_multiwindow_page(calm, calm, slow, slow, 0.999))

    def test_invalid_window_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Window(good=11, total=10)
        with self.assertRaises(ValueError):
            Window(good=0, total=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
