-- PostgreSQL 18 two-session lab. Use a disposable database and two psql windows.
DROP TABLE IF EXISTS on_call;
DROP TABLE IF EXISTS wallet;
CREATE TABLE wallet (
  id bigint PRIMARY KEY,
  balance_minor bigint NOT NULL CHECK (balance_minor >= 0),
  version bigint NOT NULL DEFAULT 0
);
INSERT INTO wallet VALUES (1, 10000, 0), (2, 10000, 0);

CREATE TABLE on_call (
  doctor text PRIMARY KEY,
  available boolean NOT NULL
);
INSERT INTO on_call VALUES ('Asha', true), ('Bimal', true);

-- SAFE ATOMIC DEBIT (run concurrently in either session):
-- UPDATE wallet SET balance_minor=balance_minor-7000, version=version+1
-- WHERE id=1 AND balance_minor>=7000 RETURNING *;
-- Exactly one of two 7000 debits can affect a row.

-- LOST-UPDATE DEMO: in both sessions BEGIN and SELECT balance first; then set an
-- application-computed absolute value. The second update can overwrite the first.
-- BEGIN; SELECT balance_minor FROM wallet WHERE id=1;
-- UPDATE wallet SET balance_minor=3000 WHERE id=1; COMMIT;

-- PESSIMISTIC TRANSFER. Always lock wallet IDs in ascending order.
-- BEGIN;
-- SELECT * FROM wallet WHERE id IN (1,2) ORDER BY id FOR UPDATE;
-- UPDATE wallet SET balance_minor=balance_minor-2500 WHERE id=1;
-- UPDATE wallet SET balance_minor=balance_minor+2500 WHERE id=2;
-- COMMIT;

-- WRITE-SKEW DEMO. In each session:
-- BEGIN ISOLATION LEVEL REPEATABLE READ;
-- SELECT count(*) FROM on_call WHERE available;
-- Session 1: UPDATE on_call SET available=false WHERE doctor='Asha';
-- Session 2: UPDATE on_call SET available=false WHERE doctor='Bimal';
-- COMMIT both: both may commit, violating "at least one available".
-- Repeat at SERIALIZABLE: one must fail with SQLSTATE 40001; retry whole tx.

-- DELIBERATE DEADLOCK. Session 1 locks wallet 1 then 2; session 2 locks 2 then 1.
-- S1: BEGIN; SELECT * FROM wallet WHERE id=1 FOR UPDATE;
-- S2: BEGIN; SELECT * FROM wallet WHERE id=2 FOR UPDATE;
-- S1: SELECT * FROM wallet WHERE id=2 FOR UPDATE;
-- S2: SELECT * FROM wallet WHERE id=1 FOR UPDATE;
-- PostgreSQL detects the cycle and aborts one transaction (40P01).

-- Blocking graph (run in a third session):
SELECT waiter.pid AS waiting_pid, blocker.pid AS blocking_pid,
       waiter.query AS waiting_query, blocker.query AS blocking_query,
       now() - waiter.query_start AS waiting_for
FROM pg_stat_activity waiter
CROSS JOIN LATERAL unnest(pg_blocking_pids(waiter.pid)) AS b(pid)
JOIN pg_stat_activity blocker ON blocker.pid=b.pid;
