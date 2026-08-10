#!/usr/bin/env python3
"""Minimal telemetry checks using only Python's standard library."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


SAFE_LABELS = {"service", "route", "method", "status_class", "region", "model_tier"}
SECRET_PATTERN = re.compile(
    r"(?i)(authorization\s*[:=]|bearer\s+[a-z0-9._-]+|password\s*[:=]|\b\d{12}\b)"
)


@dataclass(frozen=True)
class Span:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    service: str
    duration_ms: int
    status: str


def series_upper_bound(label_values: dict[str, int]) -> int:
    """Worst-case Cartesian product; actual series can be lower."""
    total = 1
    for label, values in label_values.items():
        if label not in SAFE_LABELS or values < 1:
            raise ValueError(f"unsafe label/cardinality: {label}={values}")
        total *= values
    return total


def histogram_counts(observations: Iterable[float], bounds: list[float]) -> tuple[list[int], int, float]:
    values = list(observations)
    if bounds != sorted(bounds) or len(set(bounds)) != len(bounds):
        raise ValueError("histogram bounds must be unique and sorted")
    cumulative = [sum(value <= bound for value in values) for bound in bounds]
    return cumulative, len(values), math.fsum(values)


def fraction_at_or_below(observations: Iterable[float], threshold: float) -> float:
    values = list(observations)
    if not values:
        raise ValueError("empty observation set")
    return sum(value <= threshold for value in values) / len(values)


def validate_trace(spans: Iterable[Span]) -> list[str]:
    spans = list(spans)
    by_id = {span.span_id: span for span in spans}
    errors: list[str] = []
    if len(by_id) != len(spans):
        errors.append("duplicate span_id")
    roots = [span for span in spans if span.parent_span_id is None]
    if len(roots) != 1:
        errors.append(f"expected one root, found {len(roots)}")
    for span in spans:
        if span.parent_span_id is not None and span.parent_span_id not in by_id:
            errors.append(f"orphan span {span.span_id}")
        if span.duration_ms < 0:
            errors.append(f"negative duration {span.span_id}")
    return errors


def critical_path_ms(spans: Iterable[Span]) -> int:
    """Longest root-to-leaf sum for this simplified non-overlap exercise."""
    spans = list(spans)
    errors = validate_trace(spans)
    if errors:
        raise ValueError(", ".join(errors))
    children: dict[str | None, list[Span]] = {}
    for span in spans:
        children.setdefault(span.parent_span_id, []).append(span)

    def visit(span: Span, active: set[str]) -> int:
        if span.span_id in active:
            raise ValueError("cycle")
        next_active = active | {span.span_id}
        descendants = children.get(span.span_id, [])
        return span.duration_ms + max((visit(child, next_active) for child in descendants), default=0)

    return visit(children[None][0], set())


def redact_log(fields: dict[str, str]) -> dict[str, str]:
    blocked_keys = {"authorization", "password", "token", "patient_id", "account_number"}
    clean: dict[str, str] = {}
    for key, value in fields.items():
        clean[key] = "[REDACTED]" if key.lower() in blocked_keys or SECRET_PATTERN.search(value) else value
    return clean


def status_counts(spans: Iterable[Span]) -> Counter[str]:
    return Counter(span.status for span in spans)
