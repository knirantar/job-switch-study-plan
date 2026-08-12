from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import csv

def total_paise(amounts: list[int]) -> int:
    total = 0
    for amount in amounts:
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise TypeError("amount must be int")
        if amount < 0:
            raise ValueError("negative amount")
        total += amount
    return total

def record(value, history=None):
    history = [] if history is None else history
    history.append(value)
    return history

assert total_paise([129_900, 49_900, 25_000]) == 204_800
assert total_paise([]) == 0
try: total_paise([1, -1]); raise AssertionError("negative accepted")
except ValueError: pass
assert record("C1") == ["C1"] and record("C2") == ["C2"]
assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")
assert 0.1 + 0.2 != 0.3

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "claims.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["claim_id", "amount_paise"])
        writer.writeheader(); writer.writerow({"claim_id":"C1", "amount_paise":129900})
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"claim_id":"C1", "amount_paise":"129900"}]

assert list(zip(["C1", "C2"], [100, 200], strict=True)) == [("C1",100),("C2",200)]
try: list(zip(["C1", "C2"], [100], strict=True)); raise AssertionError("mismatch accepted")
except ValueError: pass
print("PASS: names/types, validation, defaults, decimals, files/CSV, and strict zip")
