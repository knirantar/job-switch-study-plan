# Parent 03 — Data Systems

This parent builds from durable relational modeling through access paths,
concurrency control, derived caches, and safe production evolution.

1. [PostgreSQL Modeling](01-postgresql-modeling/lesson.md) — complete; includes an executable Java invariant lab and PostgreSQL schema.
2. [Indexes and Query Plans](02-indexes-query-plans/lesson.md) — complete; includes a deterministic one-million-row PostgreSQL lab and executable plan-math checks.
3. [Transactions and Locking](03-transactions-locking/lesson.md) — complete; includes a two-session PostgreSQL anomaly lab and tested retry-policy code.
4. [Redis and Caching](04-redis-caching/lesson.md) — complete; includes Redis CLI exercises and tested TTL/version-order simulation.
5. [Data Migrations](05-data-migrations/lesson.md) — complete; includes an expand–contract SQL lab and tested compatibility matrix.

## Parent capstone

[Multi-Tenant Payment and Clinical-Eligibility Store](CAPSTONE.md) integrates all five topics with concurrency, failure, migration, security and evidence gates.
