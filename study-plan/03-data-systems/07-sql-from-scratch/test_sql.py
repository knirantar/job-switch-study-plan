import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE patient(tenant_id TEXT, patient_id TEXT, display_name TEXT,
 PRIMARY KEY(tenant_id,patient_id));
CREATE TABLE claim(claim_id TEXT PRIMARY KEY, tenant_id TEXT, patient_id TEXT,
 amount_paise INTEGER, status TEXT, created_at TEXT);
INSERT INTO patient VALUES ('T1','P1','Anaya'),('T1','P2','Kabir'),('T1','P3','Meera'),('T2','P1','Vikram');
INSERT INTO claim VALUES
 ('C1','T1','P1',129900,'PAID','2026-08-01T10:00:00Z'),
 ('C2','T1','P1',49900,'SUBMITTED','2026-08-02T10:00:00Z'),
 ('C3','T1','P2',250000,'PAID','2026-08-03T10:00:00Z'),
 ('C4','T2','P1',87500,'REJECTED','2026-08-04T10:00:00Z'),
 ('C5','T1','P2',100000,'PAID','2026-08-05T10:00:00Z');
""")

paid = db.execute("""SELECT tenant_id, COUNT(*), SUM(amount_paise)
 FROM claim WHERE status='PAID' GROUP BY tenant_id ORDER BY tenant_id""").fetchall()
assert paid == [('T1', 3, 479900)]

counts = db.execute("""SELECT p.patient_id, COUNT(c.claim_id)
 FROM patient p LEFT JOIN claim c
 ON c.tenant_id=p.tenant_id AND c.patient_id=p.patient_id AND c.status='PAID'
 WHERE p.tenant_id='T1' GROUP BY p.patient_id ORDER BY p.patient_id""").fetchall()
assert counts == [('P1', 1), ('P2', 2), ('P3', 0)]

latest = db.execute("""WITH ranked AS (
 SELECT claim_id, patient_id,
 ROW_NUMBER() OVER(PARTITION BY tenant_id,patient_id ORDER BY created_at DESC,claim_id DESC) rn
 FROM claim WHERE tenant_id='T1')
 SELECT patient_id,claim_id FROM ranked WHERE rn=1 ORDER BY patient_id""").fetchall()
assert latest == [('P1', 'C2'), ('P2', 'C5')]

no_rejected = db.execute("""SELECT p.patient_id FROM patient p
 WHERE p.tenant_id='T1' AND NOT EXISTS
 (SELECT 1 FROM claim c WHERE c.tenant_id=p.tenant_id
  AND c.patient_id=p.patient_id AND c.status='REJECTED') ORDER BY p.patient_id""").fetchall()
assert no_rejected == [('P1',), ('P2',), ('P3',)]

cursor = db.execute("UPDATE claim SET status='APPROVED' WHERE claim_id='C2' AND status='SUBMITTED'")
assert cursor.rowcount == 1
cursor = db.execute("UPDATE claim SET status='APPROVED' WHERE claim_id='C2' AND status='SUBMITTED'")
assert cursor.rowcount == 0
print("PASS: filters, aggregates, outer join, windows, anti-join, conditional update")
