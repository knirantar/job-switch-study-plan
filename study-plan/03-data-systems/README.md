# Parent 03 — Data Systems

This parent builds from durable relational modeling through access paths,
concurrency control, derived caches, and safe production evolution.

No database or SQL knowledge is assumed. Complete the prerequisite phase first.

## Phase A — Database prerequisites

1. [Database and Relational Foundations](06-database-relational-foundations/lesson.md) — data persistence, tables, keys, constraints, relationships, normalization and a tested SQLite schema lab.
2. [SQL from Scratch](07-sql-from-scratch/lesson.md) — querying, filtering, joins, grouping, subqueries, CTEs, window functions and safe data changes.
3. [PostgreSQL Setup and Operations Basics](08-postgresql-setup-operations-basics/lesson.md) — clusters, databases, schemas, roles, connections, types, configuration, backup and routine inspection.

## Phase B — Existing advanced sequence

4. [PostgreSQL Modeling](01-postgresql-modeling/lesson.md) — complete; includes an executable Java invariant lab and PostgreSQL schema.
5. [Indexes and Query Plans](02-indexes-query-plans/lesson.md) — complete; includes a deterministic one-million-row PostgreSQL lab and executable plan-math checks.
6. [Transactions and Locking](03-transactions-locking/lesson.md) — complete; includes a two-session PostgreSQL anomaly lab and tested retry-policy code.
7. [Redis and Caching](04-redis-caching/lesson.md) — complete; includes Redis CLI exercises and tested TTL/version-order simulation.
8. [Data Migrations](05-data-migrations/lesson.md) — complete; includes an expand–contract SQL lab and tested compatibility matrix.

## Parent capstone

[Multi-Tenant Payment and Clinical-Eligibility Store](CAPSTONE.md) integrates all eight topics with querying, modeling, concurrency, failure, migration, security and evidence gates.
