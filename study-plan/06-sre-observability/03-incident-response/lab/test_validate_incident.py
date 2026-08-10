#!/usr/bin/env python3

import copy
import json
import unittest
from pathlib import Path

from validate_incident import validate


BASE = json.loads(Path(__file__).with_name("incident.json").read_text(encoding="utf-8"))


class IncidentRecordTest(unittest.TestCase):
    def test_reference_record_passes(self) -> None:
        self.assertEqual(validate(BASE), [])

    def test_missing_command_role_fails(self) -> None:
        record = copy.deepcopy(BASE)
        del record["roles"]["incident_commander"]
        self.assertTrue(any("missing roles" in error for error in validate(record)))

    def test_update_gap_fails(self) -> None:
        record = copy.deepcopy(BASE)
        record["updates"][1]["at"] = "2026-08-09T10:21:00Z"
        self.assertTrue(any("update gap" in error for error in validate(record)))

    def test_state_regression_fails(self) -> None:
        record = copy.deepcopy(BASE)
        record["updates"][4]["state"] = "INVESTIGATING"
        self.assertTrue(any("state regression" in error for error in validate(record)))

    def test_sensitive_value_fails(self) -> None:
        record = copy.deepcopy(BASE)
        record["updates"][1]["message"] = "Authorization: Bearer stolen.token"
        self.assertTrue(any("sensitive" in error for error in validate(record)))

    def test_unowned_action_fails(self) -> None:
        record = copy.deepcopy(BASE)
        record["actions"][0]["owner"] = ""
        self.assertTrue(any("action lacks" in error for error in validate(record)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
