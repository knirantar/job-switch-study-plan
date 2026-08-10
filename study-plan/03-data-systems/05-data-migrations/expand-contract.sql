-- PostgreSQL 18 expand/backfill/validate/contract example.
-- Run phases in separate deployments; do not paste the entire file into production.

-- PHASE 1: EXPAND (old application remains compatible)
SET lock_timeout = '2s';
SET statement_timeout = '30s';
ALTER TABLE patient ADD COLUMN IF NOT EXISTS display_name_v2 text;

-- New app release dual-writes old display_name and display_name_v2.
-- Prefer application dual write because transformation may need domain logic.

-- PHASE 2: BATCHED BACKFILL (repeat until zero rows; commit each batch)
WITH batch AS (
  SELECT id FROM patient
  WHERE display_name_v2 IS NULL
  ORDER BY id
  FOR UPDATE SKIP LOCKED
  LIMIT 5000
)
UPDATE patient p
SET display_name_v2 = trim(p.display_name)
FROM batch
WHERE p.id=batch.id AND p.display_name_v2 IS NULL;

-- PHASE 3: PROVE EXISTING DATA WITHOUT A LONG INITIAL FULL-lock validation
ALTER TABLE patient
  ADD CONSTRAINT patient_display_name_v2_present
  CHECK (display_name_v2 IS NOT NULL) NOT VALID;
ALTER TABLE patient VALIDATE CONSTRAINT patient_display_name_v2_present;
ALTER TABLE patient ALTER COLUMN display_name_v2 SET NOT NULL;

-- PHASE 4: INDEX OUTSIDE A TRANSACTION BLOCK
CREATE INDEX CONCURRENTLY IF NOT EXISTS patient_display_name_v2_idx
  ON patient (tenant_id, display_name_v2);

-- Verify no invalid index was left after an interrupted concurrent build.
SELECT c.relname, i.indisvalid, i.indisready
FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid
WHERE c.relname='patient_display_name_v2_idx';

-- PHASE 5: CONTRACT only after every old binary/job is gone and rollback window ends.
-- ALTER TABLE patient DROP COLUMN display_name;
-- ALTER TABLE patient RENAME COLUMN display_name_v2 TO display_name;
