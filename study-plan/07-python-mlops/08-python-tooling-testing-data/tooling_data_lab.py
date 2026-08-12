import csv, json, math, unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypedDict

class ClaimPayload(TypedDict):
    claim_id: str
    amount_paise: int

def parse_amount(raw: str) -> int:
    if not isinstance(raw, str): raise TypeError("amount must be text")
    if raw == "" or not raw.isdecimal(): raise ValueError("invalid integer")
    value = int(raw)
    if value > 10**12: raise ValueError("too large")
    return value

def strict_json(record):
    return json.dumps(record, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":"))

class Tests(unittest.TestCase):
    def test_amount_boundaries(self):
        self.assertEqual(parse_amount("0"), 0)
        self.assertEqual(parse_amount("129900"), 129900)
        for invalid in ("", "-1", "12.5", " 1"):
            with self.assertRaises(ValueError): parse_amount(invalid)
        with self.assertRaises(TypeError): parse_amount(None)  # type: ignore[arg-type]

    def test_strict_json(self):
        self.assertEqual(strict_json({"₹": 100, "a": 1}), '{"a":1,"₹":100}')
        with self.assertRaises(ValueError): strict_json({"score": math.nan})

    def test_csv_contract(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/"claims.csv"
            with path.open("w",encoding="utf-8",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=["claim_id","amount_paise"])
                writer.writeheader(); writer.writerow({"claim_id":"C,1","amount_paise":"129900"})
            with path.open(encoding="utf-8",newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(rows,[{"claim_id":"C,1","amount_paise":"129900"}])

if __name__ == "__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
    print("PASS: unit boundaries, strict JSON, temporary CSV, and portable stdlib tooling")
