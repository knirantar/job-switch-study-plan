PRAGMA foreign_keys = ON;

CREATE TABLE tenant (
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE patient (
  patient_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL REFERENCES tenant(tenant_id),
  display_name TEXT NOT NULL,
  PRIMARY KEY (tenant_id, patient_id)
);

CREATE TABLE claim (
  claim_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  patient_id TEXT NOT NULL,
  external_ref TEXT NOT NULL,
  amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
  status TEXT NOT NULL CHECK (status IN ('SUBMITTED','APPROVED','REJECTED','PAID')),
  created_at TEXT NOT NULL,
  UNIQUE (tenant_id, external_ref),
  FOREIGN KEY (tenant_id, patient_id) REFERENCES patient(tenant_id, patient_id)
);
