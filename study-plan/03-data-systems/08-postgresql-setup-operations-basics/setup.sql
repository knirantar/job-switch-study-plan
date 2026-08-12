-- Run only in a disposable PostgreSQL database as an authorized administrator.
-- Use psql with ON_ERROR_STOP so partial setup does not continue.
\set ON_ERROR_STOP on

CREATE ROLE study_owner NOLOGIN;
CREATE ROLE study_app LOGIN PASSWORD 'DISPOSABLE-LAB-ONLY';
CREATE SCHEMA study AUTHORIZATION study_owner;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA study TO study_app;

SET ROLE study_owner;
CREATE TABLE study.claim (
  claim_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  external_ref text NOT NULL,
  amount_paise bigint NOT NULL CHECK (amount_paise > 0),
  status text NOT NULL CHECK (status IN ('SUBMITTED','APPROVED','REJECTED','PAID')),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  UNIQUE (tenant_id, external_ref)
);
RESET ROLE;

GRANT SELECT, INSERT, UPDATE, DELETE ON study.claim TO study_app;
ALTER DEFAULT PRIVILEGES FOR ROLE study_owner IN SCHEMA study
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO study_app;
