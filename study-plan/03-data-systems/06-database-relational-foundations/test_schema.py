import sqlite3
from pathlib import Path

db = sqlite3.connect(":memory:")
db.executescript((Path(__file__).with_name("schema.sql")).read_text())
db.execute("INSERT INTO tenant VALUES (?, ?)", ("T1", "Hospital One"))
db.execute("INSERT INTO tenant VALUES (?, ?)", ("T2", "Hospital Two"))
db.execute("INSERT INTO patient VALUES (?, ?, ?)", ("P1", "T1", "Patient A"))
db.execute("INSERT INTO patient VALUES (?, ?, ?)", ("P1", "T2", "Patient B"))
db.execute(
    "INSERT INTO claim VALUES (?, ?, ?, ?, ?, ?, ?)",
    ("C1", "T1", "P1", "EXT-7", 129_900, "SUBMITTED", "2026-08-12T10:00:00Z"),
)

def rejected(sql, values):
    try:
        db.execute(sql, values)
    except sqlite3.IntegrityError:
        return
    raise AssertionError(f"constraint accepted invalid values: {values}")

rejected("INSERT INTO claim VALUES (?, ?, ?, ?, ?, ?, ?)",
         ("C2", "T1", "P1", "EXT-7", 100, "PAID", "2026-08-12T10:01:00Z"))
rejected("INSERT INTO claim VALUES (?, ?, ?, ?, ?, ?, ?)",
         ("C3", "T1", "P1", "EXT-8", -1, "PAID", "2026-08-12T10:01:00Z"))
rejected("INSERT INTO claim VALUES (?, ?, ?, ?, ?, ?, ?)",
         ("C4", "T1", "P9", "EXT-9", 100, "PAID", "2026-08-12T10:01:00Z"))
rejected("INSERT INTO claim VALUES (?, ?, ?, ?, ?, ?, ?)",
         ("C5", "T1", "P1", "EXT-10", 100, "UNKNOWN", "2026-08-12T10:01:00Z"))
assert db.execute("SELECT amount_paise FROM claim WHERE claim_id='C1'").fetchone() == (129_900,)
print("PASS: keys, tenant-scoped reference, uniqueness, checks, and valid row")
