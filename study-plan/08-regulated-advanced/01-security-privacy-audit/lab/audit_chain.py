"""Canonical, hash-chained audit events with strict field policy."""
from __future__ import annotations
import hashlib, json, re
from typing import Any

GENESIS = "0" * 64
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN = {"password", "secret", "token", "authorization", "aadhaar", "pan", "patient_name", "card_number"}
REQUIRED = {"seq", "timestamp", "actor_id", "action", "resource_id", "decision", "prev_hash", "event_hash"}

def canonical(event: dict[str, Any]) -> bytes:
    body = {k: v for k, v in event.items() if k != "event_hash"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def find_forbidden(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            parts = set(re.split(r"[^a-z0-9]+|_", key.lower()))
            if key.lower() in FORBIDDEN or parts & FORBIDDEN:
                errors.append(f"forbidden field {path}.{key}")
            errors.extend(find_forbidden(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for i, child in enumerate(value): errors.extend(find_forbidden(child, f"{path}[{i}]"))
    return errors

def append(chain: list[dict[str, Any]], event: dict[str, Any]) -> dict[str, Any]:
    if find_forbidden(event): raise ValueError("sensitive field prohibited")
    record = dict(event)
    record["seq"] = len(chain) + 1
    record["prev_hash"] = chain[-1]["event_hash"] if chain else GENESIS
    record["event_hash"] = hashlib.sha256(canonical(record)).hexdigest()
    chain.append(record)
    return record

def verify(chain: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    previous = GENESIS
    for index, event in enumerate(chain, 1):
        if set(event) != REQUIRED: errors.append(f"event {index}: wrong fields")
        if event.get("seq") != index: errors.append(f"event {index}: bad sequence")
        if event.get("prev_hash") != previous: errors.append(f"event {index}: broken link")
        if not HEX64.fullmatch(str(event.get("event_hash", ""))): errors.append(f"event {index}: invalid hash")
        elif hashlib.sha256(canonical(event)).hexdigest() != event["event_hash"]: errors.append(f"event {index}: content changed")
        errors.extend(f"event {index}: {e}" for e in find_forbidden(event))
        previous = str(event.get("event_hash", ""))
    return errors
