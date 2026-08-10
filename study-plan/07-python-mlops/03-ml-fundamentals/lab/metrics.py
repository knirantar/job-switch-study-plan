#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Confusion:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def specificity(self) -> float:
        return self.tn / (self.tn + self.fp) if self.tn + self.fp else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def accuracy(self) -> float:
        total = self.tp + self.fp + self.tn + self.fn
        return (self.tp + self.tn) / total if total else 0.0


def confusion(labels: Iterable[int], scores: Iterable[float], threshold: float) -> Confusion:
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    pairs = list(zip(labels, scores, strict=True))
    for label, score in pairs:
        if label not in (0, 1) or not 0 <= score <= 1:
            raise ValueError("labels must be binary and scores within [0,1]")
        predicted = int(score >= threshold)
        key = "tp" if label == predicted == 1 else "tn" if label == predicted == 0 else "fp" if predicted else "fn"
        counts[key] += 1
    return Confusion(**counts)


def brier_score(labels: Iterable[int], scores: Iterable[float]) -> float:
    pairs = list(zip(labels, scores, strict=True))
    if not pairs:
        raise ValueError("empty dataset")
    return sum((score - label) ** 2 for label, score in pairs) / len(pairs)


def roc_auc(labels: Iterable[int], scores: Iterable[float]) -> float:
    pairs = list(zip(labels, scores, strict=True))
    positive = [score for label, score in pairs if label == 1]
    negative = [score for label, score in pairs if label == 0]
    if not positive or not negative:
        raise ValueError("AUC needs both classes")
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positive for n in negative)
    return wins / (len(positive) * len(negative))


def expected_cost(matrix: Confusion, false_positive_cost: float, false_negative_cost: float) -> float:
    return matrix.fp * false_positive_cost + matrix.fn * false_negative_cost
