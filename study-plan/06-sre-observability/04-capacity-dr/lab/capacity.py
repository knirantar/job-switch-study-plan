#!/usr/bin/env python3
"""Capacity and recovery arithmetic with explicit units."""

from __future__ import annotations

import math


def peak_rps(daily_requests: int, peak_to_average: float) -> float:
    if daily_requests < 0 or peak_to_average <= 0:
        raise ValueError("invalid workload")
    return daily_requests / 86_400 * peak_to_average


def replicas_for_peak(peak: float, safe_rps_per_replica: float, headroom: float = 0.30) -> int:
    if peak < 0 or safe_rps_per_replica <= 0 or not 0 <= headroom < 1:
        raise ValueError("invalid capacity input")
    return math.ceil(peak / (safe_rps_per_replica * (1 - headroom)))


def replicas_for_zone_loss(required_healthy: int, zones: int) -> int:
    """Balanced total whose remaining zones retain required_healthy after one zone fails."""
    if required_healthy < 1 or zones < 2:
        raise ValueError("need capacity and at least two zones")
    per_zone = math.ceil(required_healthy / (zones - 1))
    return per_zone * zones


def backlog_drain_seconds(backlog_events: int, arrival_per_second: float, service_per_second: float) -> float:
    net = service_per_second - arrival_per_second
    if backlog_events < 0 or arrival_per_second < 0 or net <= 0:
        raise ValueError("service rate must exceed continuing arrival rate")
    return backlog_events / net


def retained_bytes(rate_per_second: float, bytes_per_event: int, seconds: int, replicas: int, overhead: float) -> float:
    if min(rate_per_second, bytes_per_event, seconds, replicas) < 0 or overhead < 1:
        raise ValueError("invalid storage input")
    return rate_per_second * bytes_per_event * seconds * replicas * overhead


def achieved_rpo_seconds(last_durable_epoch: int, disaster_epoch: int) -> int:
    if last_durable_epoch > disaster_epoch:
        raise ValueError("recovery point cannot be after disaster")
    return disaster_epoch - last_durable_epoch


def achieved_rto_seconds(disaster_epoch: int, verified_service_epoch: int) -> int:
    if verified_service_epoch < disaster_epoch:
        raise ValueError("recovery cannot precede disaster")
    return verified_service_epoch - disaster_epoch
