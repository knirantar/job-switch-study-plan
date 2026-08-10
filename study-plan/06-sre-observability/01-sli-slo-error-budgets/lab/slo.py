#!/usr/bin/env python3
"""Exact event-based SLO and burn-rate calculations using integer counts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Window:
    good: int
    total: int

    def __post_init__(self) -> None:
        if self.total <= 0 or self.good < 0 or self.good > self.total:
            raise ValueError("require 0 <= good <= total and total > 0")

    @property
    def bad(self) -> int:
        return self.total - self.good

    @property
    def success_ratio(self) -> float:
        return self.good / self.total


def budget_events(total: int, objective: float) -> float:
    if total < 0 or not 0.0 < objective < 1.0:
        raise ValueError("invalid total or objective")
    return total * (1.0 - objective)


def burn_rate(window: Window, objective: float) -> float:
    return (window.bad / window.total) / (1.0 - objective)


def budget_consumed(window: Window, objective: float) -> float:
    budget = budget_events(window.total, objective)
    return window.bad / budget


def qualifies_multiwindow_page(
    fast_short: Window,
    fast_long: Window,
    slow_short: Window,
    slow_long: Window,
    objective: float,
) -> bool:
    fast = burn_rate(fast_short, objective) > 14.4 and burn_rate(fast_long, objective) > 14.4
    slow = burn_rate(slow_short, objective) > 6.0 and burn_rate(slow_long, objective) > 6.0
    return fast or slow
