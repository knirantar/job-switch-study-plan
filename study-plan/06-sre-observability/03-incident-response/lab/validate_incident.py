#!/usr/bin/env python3
"""Validate a simplified operational incident record."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


STATES = {"DECLARED": 0, "INVESTIGATING": 1, "MITIGATING": 2, "MONITORING": 3, "RESOLVED": 4}
REQUIRED_ROLES = {"incident_commander", "operations_lead", "communications_lead", "scribe"}
SENSITIVE = re.compile(r"(?i)(bearer\s|authorization:|password=|patient[_ -]?id|\b\d{12,16}\b)")


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(record: dict[str, Any], max_update_gap_minutes: int = 15) -> list[str]:
    errors: list[str] = []
    missing_roles = REQUIRED_ROLES - set(record.get("roles", {}))
    if missing_roles:
        errors.append("missing roles: " + ",".join(sorted(missing_roles)))

    updates = record.get("updates", [])
    if not updates or updates[0].get("state") != "DECLARED" or updates[-1].get("state") != "RESOLVED":
        errors.append("timeline must begin DECLARED and end RESOLVED")
    else:
        previous_time = instant(updates[0]["at"])
        previous_state = STATES[updates[0]["state"]]
        for update in updates[1:]:
            current_time = instant(update["at"])
            current_state = STATES.get(update["state"], -1)
            gap = (current_time - previous_time).total_seconds() / 60
            if gap < 0:
                errors.append("timeline is not chronological")
            if gap > max_update_gap_minutes:
                errors.append(f"update gap {gap:.0f}m exceeds {max_update_gap_minutes}m")
            if current_state < previous_state:
                errors.append(f"state regression to {update['state']}")
            previous_time, previous_state = current_time, current_state

    if record.get("resolved_at") != (updates[-1]["at"] if updates else None):
        errors.append("resolved_at does not match final update")
    impact = record.get("impact", {})
    if not all(impact.get(field) for field in ("start", "end", "summary")):
        errors.append("impact window and summary are required")
    if len(record.get("evidence", [])) < 2:
        errors.append("at least two evidence references required")
    for action in record.get("actions", []):
        if not all(action.get(field) for field in ("id", "owner", "due", "status", "verification")):
            errors.append("action lacks owner/due/status/verification")

    serialized = json.dumps(record)
    if SENSITIVE.search(serialized):
        errors.append("potential sensitive value in incident record")
    return errors


def main() -> int:
    path = Path(__file__).with_name("incident.json")
    errors = validate(json.loads(path.read_text(encoding="utf-8")))
    if errors:
        print("FAIL\n" + "\n".join(f"- {error}" for error in errors))
        return 1
    print("PASS: incident record satisfies structural, cadence, evidence, action, and privacy gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
