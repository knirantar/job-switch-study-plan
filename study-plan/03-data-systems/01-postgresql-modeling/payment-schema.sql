CREATE TABLE tenant (
    tenant_id uuid PRIMARY KEY,
    legal_name text NOT NULL CHECK (length(btrim(legal_name)) BETWEEN 1 AND 200),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE account (
    account_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    owner_subject text NOT NULL,
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    balance_minor bigint NOT NULL CHECK (balance_minor >= 0),
    version bigint NOT NULL DEFAULT 0 CHECK (version >= 0),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    UNIQUE (tenant_id, account_id),
    UNIQUE (tenant_id, owner_subject, currency)
);

CREATE TYPE payment_status AS ENUM ('PENDING','AUTHORIZED','CAPTURED','FAILED','CANCELLED');

CREATE TABLE payment (
    payment_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    account_id uuid NOT NULL,
    idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 200),
    request_hash bytea NOT NULL CHECK (octet_length(request_hash) = 32),
    amount_minor bigint NOT NULL CHECK (amount_minor > 0),
    currency char(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    status payment_status NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
    created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    version bigint NOT NULL DEFAULT 0,
    FOREIGN KEY (tenant_id, account_id) REFERENCES account(tenant_id, account_id),
    UNIQUE (tenant_id, idempotency_key),
    CHECK (updated_at >= created_at)
);

CREATE TABLE payment_status_history (
    payment_id uuid NOT NULL REFERENCES payment(payment_id),
    sequence_no integer NOT NULL CHECK (sequence_no > 0),
    old_status payment_status,
    new_status payment_status NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    actor_subject text NOT NULL,
    PRIMARY KEY (payment_id, sequence_no)
);

CREATE TABLE outbox_event (
    event_id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant(tenant_id),
    aggregate_type text NOT NULL,
    aggregate_id uuid NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    published_at timestamptz,
    CHECK (published_at IS NULL OR published_at >= occurred_at)
);

CREATE INDEX payment_tenant_created_id_idx
    ON payment (tenant_id, created_at DESC, payment_id DESC);
CREATE INDEX outbox_unpublished_idx
    ON outbox_event (occurred_at, event_id) WHERE published_at IS NULL;

