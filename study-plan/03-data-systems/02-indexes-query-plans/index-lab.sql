-- PostgreSQL 18 reproducible index/query-plan lab.
-- Run in a disposable database with: psql -f index-lab.sql
DROP TABLE IF EXISTS payment_plan_lab;
CREATE TABLE payment_plan_lab (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tenant_id integer NOT NULL,
  account_id integer NOT NULL,
  status text NOT NULL CHECK (status IN ('PENDING','SETTLED','FAILED')),
  amount_minor bigint NOT NULL CHECK (amount_minor > 0),
  created_at timestamptz NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- Deterministic one-million-row distribution: 100 tenants, 10k accounts,
-- 5% pending, 90% settled, 5% failed, 365 days of timestamps.
INSERT INTO payment_plan_lab
  (tenant_id, account_id, status, amount_minor, created_at, metadata)
SELECT
  (g % 100) + 1,
  (g % 10000) + 1,
  CASE WHEN g % 20 = 0 THEN 'PENDING'
       WHEN g % 20 = 1 THEN 'FAILED' ELSE 'SETTLED' END,
  100 + (g % 500000),
  timestamptz '2025-01-01 00:00:00+00' + (g % 31536000) * interval '1 second',
  jsonb_build_object('channel', (ARRAY['api','mobile','batch'])[1 + g % 3])
FROM generate_series(1, 1000000) AS g;

ANALYZE payment_plan_lab;

-- Baseline first. Record plan, estimated/actual rows, buffers and time.
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, amount_minor, created_at
FROM payment_plan_lab
WHERE tenant_id = 42 AND account_id = 4242
ORDER BY created_at DESC LIMIT 50;

CREATE INDEX payment_tenant_account_time
  ON payment_plan_lab (tenant_id, account_id, created_at DESC)
  INCLUDE (amount_minor, status);

CREATE INDEX payment_pending_time
  ON payment_plan_lab (tenant_id, created_at)
  WHERE status = 'PENDING';

CREATE INDEX payment_metadata_gin
  ON payment_plan_lab USING gin (metadata jsonb_path_ops);

ANALYZE payment_plan_lab;

EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)
SELECT id, amount_minor, created_at
FROM payment_plan_lab
WHERE tenant_id = 42 AND account_id = 4242
ORDER BY created_at DESC LIMIT 50;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM payment_plan_lab
WHERE tenant_id = 42 AND status = 'PENDING'
  AND created_at >= timestamptz '2025-06-01 00:00:00+00';

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM payment_plan_lab
WHERE metadata @> '{"channel":"mobile"}'::jsonb;

-- Correlation example and correction.
ALTER TABLE payment_plan_lab ALTER COLUMN tenant_id SET STATISTICS 1000;
CREATE STATISTICS payment_tenant_account_stats (dependencies, ndistinct, mcv)
  ON tenant_id, account_id FROM payment_plan_lab;
ANALYZE payment_plan_lab;

-- Operational observation.
SELECT schemaname, relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes WHERE relname = 'payment_plan_lab'
ORDER BY indexrelname;
