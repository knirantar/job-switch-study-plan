# Data Systems Capstone — Multi-Tenant Payment and Clinical-Eligibility Store

## Objective

Design and implement the PostgreSQL/Redis data layer for a service that stores payment authorization requests and a healthcare eligibility decision linked to each request. The capstone tests schema judgment, plan evidence, concurrency correctness, caching boundaries and live migration—not framework CRUD.

Use PostgreSQL 18 where available. Redis is optional for execution but its interface/failure tests are required. Generate at least 10 million synthetic payments locally if resources permit; otherwise use one million and explicitly explain which plan/capacity conclusions cannot be extrapolated.

## Prerequisite gate

Complete all eight lessons before implementation. Create a database and least-privilege role from a clean PostgreSQL installation, restore a backup into a disposable database, and explain the server/database/schema/table/row hierarchy. Build normalized customer/payment tables with keys and constraints; execute and explain `SELECT`, filtering, joins, grouping, subqueries, CTEs, transactions and window functions; and diagnose one failed connection and one slow query using server logs and `EXPLAIN`. The advanced store must rest on repeatable setup and SQL fluency, not GUI-only familiarity.

## Functional contract

- Every row is tenant-scoped; cross-tenant account/patient references are impossible through database constraints.
- Monetary amounts use integer minor units plus ISO currency; no floating-point money.
- A stable `(tenant_id,idempotency_key)` and request fingerprint prevent duplicated authorization.
- Payment transitions append immutable history and an outbox event in the same transaction.
- Eligibility includes source version, evaluated time, policy version and status without putting raw PHI into cache keys/events.
- History endpoint uses descending `(created_at,id)` keyset pagination with maximum 200 rows.
- Worker claims pending outbox records in batches with `FOR UPDATE SKIP LOCKED`, a lease and idempotent publication identity.

## Required schema evidence

1. ER diagram and executable DDL with PK, tenant-composite FK, UNIQUE, CHECK and NOT NULL constraints.
2. A decision record for UUID versus bigint identities, status representation, JSONB boundaries, time-zone types and deletion/retention.
3. Seed generator with documented distribution: tenant skew, 90/5/5 payment status, timestamp range and at least one correlated column pair.
4. At least five representative queries with `EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)` before/after index changes.
5. Index inventory giving each index's query/invariant owner, size, write cost hypothesis and removal gate.
6. Statistics experiment demonstrating one cardinality-estimation error and whether higher/extended statistics correct it.

## Concurrency experiments

Use two or more independent database sessions and record SQLSTATE/final rows:

- Twenty concurrent requests with the same idempotency key create one logical payment.
- Two guarded debits cannot make a balance negative.
- Reproduce on-call-style write skew under Repeatable Read, then show Serializable abort/retry.
- Reproduce a deadlock with opposing lock order, then eliminate that known cycle with sorted resource locking.
- Crash a job worker after external-effect simulation but before result commit; show why lease claiming is at least once and how consumer idempotency repairs it.
- Show blocker diagnosis with `pg_blocking_pids`, transaction age and wait event.

## Cache design and failure tests

Cache only a redacted, versioned eligibility summary. Document maximum permitted staleness and fail-open/fail-closed behavior. Implement cache-aside with:

- tenant/versioned key namespace;
- typed negative result and short TTL;
- jittered positive TTL;
- per-key single-flight or equivalent stampede control;
- source-version monotonic fill;
- durable outbox/CDC invalidation plus TTL repair;
- bounded database fallback.

Test Redis unavailable, 200 ms latency, a 5,000-request hot-key expiry wave, invalidation consumer downtime and a late stale fill. Report cache/source QPS, hit/miss by tenant/key class, coalesced waiters, stale serves and database p95/p99. Do not assert generic Redis latency from a laptop run.

## Live migration exercise

Rename/split `eligibility_status` into a new structured decision representation without downtime:

1. Inventory all readers/writers and define old/new compatibility matrix.
2. Expand nullable target columns/table with bounded lock acquisition.
3. Deploy dual-write/old-read, then a guarded restartable batch backfill.
4. Record observed WAL per updated row and throttle from replica/latency headroom.
5. Reconcile counts, hashes and semantic exceptions per tenant.
6. Add a `NOT VALID` constraint, validate it, and enforce final nullability.
7. Build required index concurrently outside a transaction and verify catalog validity.
8. Switch reads, prove fallback/old-write telemetry reaches zero, and define a rollback window.
9. Present—but do not automatically execute—the contract migration and point of no return.

Inject a backfill crash, a concurrent live update and a failed concurrent index build in a disposable environment. Demonstrate restart/no-regression and invalid-index detection.

## Operational gates

Define numeric gates from your baseline for lock wait, statement time, primary p99, error rate, WAL rate, replica lag, disk headroom, backfill exception rate and cache fallback. Include commands/dashboard queries and a named decision for pause, abort and resume. For regulated fields, show redaction, least-privilege migration identity, audit/run ID, encrypted temporary data and deletion/retention handling.

## Deliverables

1. `README.md` with architecture, assumptions and exact reproduction commands.
2. Versioned SQL migrations plus immutable checksum/history demonstration.
3. Seed and load scripts with environment/specification metadata.
4. Before/after machine-readable JSON plans and a written interpretation.
5. Concurrency harness/results with final-state assertions.
6. Cache simulator/integration tests and outage report.
7. Expand–migrate–contract runbook with gates and rollback/roll-forward decision tree.
8. Reconciliation report containing no PHI.
9. Five architecture decision records.
10. Fifteen-minute recorded oral defense.

## Mastery gates

You pass only if every mandatory gate succeeds:

- **Correctness:** database constraints make cross-tenant references and duplicate idempotency identity impossible.
- **Plan literacy:** every plan interpretation correctly handles estimates, actual rows and loops; no cost-to-milliseconds comparison.
- **Concurrency:** whole-transaction retry for `40001`/`40P01` is bounded, jittered and idempotent.
- **Cache safety:** cache loss cannot silently authorize, leak tenant/PHI data or overload the source beyond the defined bulkhead.
- **Migration safety:** an old application binary remains compatible through expand/backfill, and contract has evidence-based gates.
- **Evidence quality:** measured numbers name PostgreSQL/Redis version, machine/container resources, dataset, cache state, concurrency and repetition method.

## Failure review

Defend these without notes:

1. Why can a sequential scan be the correct plan despite an available index?
2. Why does `INCLUDE` not guarantee zero heap fetches?
3. Why can Repeatable Read allow write skew in PostgreSQL?
4. Why must a serialization retry restart all reads and decisions?
5. Why does commit-then-cache-delete still have a failure window?
6. Why are Redis keyspace notifications unsuitable as a durable invalidation log?
7. Why can a Redis lease require fencing even with compare-and-delete release?
8. Why does `CREATE INDEX CONCURRENTLY` need post-failure catalog inspection?
9. Why is an edited Flyway checksum not repaired casually?
10. Why is a backup not a simple rollback for a destructive schema migration?

## Rubric (100 points)

| Area | Points |
|---|---:|
| Relational model and tenant/regulatory safety | 18 |
| Query-plan/index evidence | 17 |
| Transaction and concurrency correctness | 20 |
| Cache design and failure containment | 15 |
| Migration compatibility and recoverability | 20 |
| Reproducibility, observability and oral defense | 10 |

Pass at 80+, but every mastery gate is mandatory. A fast benchmark cannot compensate for a correctness, tenant-isolation, recovery or evidence failure.
