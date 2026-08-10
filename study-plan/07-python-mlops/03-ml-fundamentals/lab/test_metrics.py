#!/usr/bin/env python3
import csv
import unittest
from pathlib import Path

from metrics import brier_score, confusion, expected_cost, roc_auc


with Path(__file__).with_name("claims.csv").open(newline="", encoding="utf-8") as source:
    ROWS = list(csv.DictReader(source))
LABELS = [int(row["label"]) for row in ROWS]
SCORES = [float(row["score"]) for row in ROWS]


class MetricTest(unittest.TestCase):
    def test_confusion_at_point_six(self) -> None:
        result = confusion(LABELS, SCORES, 0.60)
        self.assertEqual((result.tp, result.fp, result.tn, result.fn), (7, 0, 11, 2))
        self.assertAlmostEqual(result.precision, 1.0)
        self.assertAlmostEqual(result.recall, 7 / 9)
        self.assertAlmostEqual(result.f1, 0.875)
        self.assertAlmostEqual(result.accuracy, 0.90)

    def test_threshold_cost_tradeoff(self) -> None:
        low = confusion(LABELS, SCORES, 0.50)
        high = confusion(LABELS, SCORES, 0.70)
        self.assertEqual((low.tp, low.fp, low.tn, low.fn), (8, 2, 9, 1))
        self.assertEqual((high.tp, high.fp, high.tn, high.fn), (5, 0, 11, 4))
        self.assertLess(expected_cost(low, 100, 1000), expected_cost(high, 100, 1000))

    def test_auc_and_brier(self) -> None:
        self.assertAlmostEqual(roc_auc(LABELS, SCORES), 97 / 99)
        self.assertAlmostEqual(brier_score(LABELS, SCORES), 0.104135)

    def test_ties_receive_half_credit(self) -> None:
        self.assertAlmostEqual(roc_auc([1, 0], [0.5, 0.5]), 0.5)

    def test_shape_and_domain_errors(self) -> None:
        with self.assertRaises(ValueError):
            confusion([1], [0.2, 0.3], 0.5)
        with self.assertRaises(ValueError):
            confusion([2], [0.2], 0.5)
        with self.assertRaises(ValueError):
            roc_auc([1, 1], [0.2, 0.3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
