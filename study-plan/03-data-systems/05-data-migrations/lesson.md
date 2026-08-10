# Data Migrations and Zero-Downtime Schema Evolution

**Parent:** 03 — Data Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the migration lab

## 1. FOUNDATIONS

A database migration changes durable state or the rules governing it. An application deployment can often be rolled back by starting the previous binary; a destructive schema change may erase information the old binary requires. That asymmetry makes database changes a compatibility and operations problem, not merely a list of `ALTER TABLE` statements.

The database is shared across time. During a rolling deployment, old and new application instances run simultaneously. Background jobs, replicas, analytics exports and incident rollback may also use different assumptions. Therefore a safe migration must define a **compatibility window**: the set of schema and application versions that can coexist. `MigrationCompatibility.java` models four schema stages and shows why jumping from old-only to new-only is unsafe.

The core method is **expand–migrate–contract**. **Expand** adds new structures without breaking old readers/writers. **Migrate** moves existing data and application behavior while both representations coexist. **Contract** removes the old representation only after evidence proves no consumer needs it and the rollback window has closed. The method deliberately turns one risky irreversible deployment into several observable reversible steps.

There are two broad change types. A **schema migration** changes tables, columns, constraints, indexes or types. A **data migration/backfill** rewrites existing rows or moves records between systems. They interact: adding a non-null field to 500 million rows is not only DDL; existing rows need a valid value, new writes must maintain it, validation scans consume I/O, replicas receive WAL, and a rollback must understand dual state.

Database migration tools such as Flyway maintain a **schema history** recording ordered versioned scripts and checksums. This provides reproducible deployment history; it does not prove a script is safe for the table size, workload or PostgreSQL version. Redgate Flyway's current documentation describes versioned/repeatable migrations and `migrate`, `validate`, `info`, `baseline` and `repair`. `repair` changes history metadata and can align checksums; it is not a casual fix for editing an already-applied production migration.

PostgreSQL DDL is transactional in many cases, but “transactional” does not mean “online.” Commands acquire table locks, may scan/rewrite the table, generate WAL, wait for old transactions and block conflicting work. A statement that takes 50 ms after obtaining its lock can still wait minutes and form a lock queue. Exact behavior changes across PostgreSQL versions, so this lesson targets PostgreSQL 18 and links its primary documentation.

A production-safe migration has four dimensions:

- **Logical correctness:** transformed rows and constraints match business meaning.
- **Compatibility:** old/new code tolerate every intermediate state.
- **Operational safety:** bounded locks, I/O, WAL, replica lag and transaction size.
- **Recoverability:** abort, retry, roll forward and data reconciliation are rehearsed.

“Zero downtime” does not mean zero risk or zero performance effect. It means the change respects the availability objective under tested production-like scale and has controls that stop it before user impact exceeds policy.

## 2. CORE MECHANICS

### 2.1 Inventory consumers and invariants

Before SQL, identify every reader and writer: synchronous services, old fleet versions, batch jobs, CDC connectors, BI tools, replicas, exports, support queries and disaster-recovery processes. State the invariant in data terms. For a name split, decide parsing and loss rules. For cents-to-minor-unit conversion, prove range/rounding. For patient data, define consent, retention, lineage and audit requirements.

Measure table rows/bytes, write and read rates, largest tenants, null/invalid counts, index sizes, dead tuples, long transaction ages, replica lag and disk/WAL headroom. A development table with 10,000 rows cannot validate the behavior of an 800 GB table.

### 2.2 Immutable migration history

Commit migration scripts with the application. A versioned script runs once in order; do not edit it after shared environments apply it. Add a corrective migration. A repeatable migration is suitable for replaceable definitions such as views/functions when checksum changes are intentionally reapplied, not for an unbounded destructive data rewrite.

CI should start from a baseline/empty supported state, apply every migration, validate checksums, and exercise upgrade from at least the oldest supported production schema snapshot. Test idempotent operational backfill jobs separately. Restrict database credentials: application runtime should not usually have broad DDL privileges, and migration identity should be audited.

### 2.3 Expand phase

Add the new nullable column/table/index without changing old behavior. New structures must not require old binaries to populate them immediately. Example:

```sql
SET lock_timeout='2s';
ALTER TABLE patient ADD COLUMN display_name_v2 text;
```

Even adding a nullable column needs a table lock, though it is often metadata-only; `lock_timeout` prevents indefinite waiting but requires a controlled retry. `IF NOT EXISTS` can make operational retries convenient, yet it verifies only the name exists—not that type/default/semantics match. Query catalogs or migration history to verify exact desired state.

Adding a column with a volatile default can require work unlike a safe constant default; consult the exact PostgreSQL version. Avoid combining many changes into one opaque `ALTER TABLE` if their lock/rewrite risks differ.

### 2.4 Dual read and dual write

Deploy code that can operate while new values are absent. Common sequence:

1. Old readers/writers use old column.
2. New binary writes both; still reads old.
3. Backfill old rows.
4. Verify parity/completeness.
5. New binary reads new and writes both.
6. Stop old writes; new-only writer/read.
7. Contract later.

Dual writes are not automatically atomic across two databases, but two columns in one PostgreSQL row can be updated in one transaction. Put transformation in one tested domain function. If using a trigger to cover unknown writers, version/test it and plan removal; hidden triggers increase write latency and operational surprise.

Read fallback such as `COALESCE(new, transform(old))` supports mixed rows but can hide backfill gaps forever. Instrument fallback counts and require them to reach zero before constraint/contract.

### 2.5 Backfill design

Do not update 500 million rows in one transaction. It retains row versions/locks, produces a huge WAL burst, delays vacuum and makes rollback expensive. Use bounded batches with a stable cursor or `FOR UPDATE SKIP LOCKED`. The included SQL updates up to 5,000 IDs and commits each batch.

A backfill must be:

- **Idempotent:** rerunning reaches the same correct state.
- **Restartable:** checkpoint/cursor survives crashes.
- **Concurrency-safe:** it does not overwrite a newer application value.
- **Throttleable:** pause on lag, latency, lock waits or disk pressure.
- **Observable:** scanned/changed/skipped/error counts and oldest remaining key.

The predicate `WHERE new_column IS NULL` plus the same guard in the final UPDATE prevents overwriting a concurrent dual-write. But NULL may be a legitimate domain value; use a migration-state/version marker when it is. Keyset batches (`id > last_id ORDER BY id LIMIT N`) avoid deep offset work but can miss newly inserted lower keys unless dual write covers them and a final sweep verifies.

Suppose each update generates an observed average 1.8 KiB of WAL in staging including indexes, and safe replica apply headroom is 18 MiB/s. A preliminary upper throughput is `18×1024 / 1.8 ≈ 10,240 rows/s`, before normal workload and safety margin. Start far below, such as 2,000 rows/s, and adapt from actual lag/latency. These numbers are an explicit sizing example, not PostgreSQL constants.

### 2.6 Validation and reconciliation

Row count equality is weak. Validate:

- zero missing new values where required;
- transform parity with a deterministic hash or direct comparison;
- grouped counts/sums by tenant/date/status;
- minimum/maximum/range and referential violations;
- sampled semantic review for lossy transformations;
- application fallback reads and old-column writes at zero;
- replica/CDC downstream parity.

For one billion rows, full comparisons compete with production. Run incremental checks per key range and record immutable reconciliation results. Use two independent computations where risk warrants it. For regulated data, preserve lineage: transformation version, run ID, actor, time and exception handling without exposing PHI in logs.

### 2.7 Adding constraints safely

Adding a CHECK or foreign-key constraint with `NOT VALID` makes PostgreSQL enforce it for new/changed rows while skipping the initial full-table validation. Later `VALIDATE CONSTRAINT` scans existing data with a less disruptive lock profile than adding a fully validated constraint in one step. Example:

```sql
ALTER TABLE patient ADD CONSTRAINT patient_name_present
CHECK (display_name_v2 IS NOT NULL) NOT VALID;
ALTER TABLE patient VALIDATE CONSTRAINT patient_name_present;
ALTER TABLE patient ALTER COLUMN display_name_v2 SET NOT NULL;
```

The final `SET NOT NULL` behavior should be confirmed for PostgreSQL 18 and the validated proof. `NOT VALID` is not permanent completion; catalog monitoring must identify unvalidated constraints. A failed validation is useful evidence of bad legacy rows, not permission to delete them without domain review.

### 2.8 Index creation

Ordinary `CREATE INDEX` blocks writes while building. PostgreSQL 18 `CREATE INDEX CONCURRENTLY` allows inserts/updates/deletes but performs two table scans and waits for relevant transactions, doing more work and taking longer. It cannot run inside a transaction block. Failure can leave an invalid index that still consumes update overhead; inspect `pg_index.indisvalid/indisready`, then use the documented drop/retry or concurrent reindex procedure.

A concurrent unique index can start enforcing uniqueness before the command ultimately completes. Pre-scan duplicates, define conflict resolution and monitor errors. For partitioned tables, concurrent parent behavior has special restrictions; build child indexes and attach according to exact documentation.

### 2.9 Type and key changes

Changing a column type in place may rewrite the table and block. Expand with a new column of target type, dual write, batch-convert with explicit error table, validate, switch reads, then contract. Never cast money through binary floating point. Time transformations must state source zone and DST ambiguity policy.

Changing primary keys affects foreign keys, URLs, events, caches and analytics. Introduce new key alongside old, populate mapping, propagate both through contracts, migrate foreign references, and retain an identity map until every downstream consumer is proven migrated. A database rename is not a distributed rename.

### 2.10 Large table split or service extraction

Moving data to another database/service cannot be one local ACID transaction. Common sequence: initial snapshot with a high-water mark, capture concurrent changes via CDC/outbox, apply idempotently in order, validate lag/parity, shadow reads, gradually switch traffic, retain reverse/repair path, then stop old writes. Define authority at every phase; two writable masters without conflict semantics create split-brain business data.

CDC can deliver duplicates and schema changes. Events need stable identity, source position, operation, before/after or reconstructible state, and schema version. Consumers checkpoint only after durable apply. Deletes require tombstones or explicit events; a snapshot alone silently resurrects deleted rows.

### 2.11 Contract phase

Contract is the dangerous irreversible step. Preconditions:

- fleet, jobs and consumers no longer read/write old representation;
- fallback/old-write telemetry is zero for a meaningful window;
- reconciliation and constraints pass;
- rollback binary no longer depends on old schema, or rollback plan is roll-forward;
- backups/PITR and restore are tested within objectives;
- approvals and retention/legal holds are satisfied.

Drop/rename in a later release, not immediately after traffic switch. Deleting a column is logical data destruction even if storage reclamation details vary. Export required audit lineage before removal. Use lock timeout and monitor blocking.

### 2.12 Rollback versus roll forward

Rollback is easy only before incompatible writes. If new code writes values old code cannot interpret, reverting binary may corrupt data. Define a **point of no return**. Before it, disable feature and revert app. After it, roll forward with repair, or run a tested reverse transform if lossless.

Backups are not a per-migration rollback button: restoring an entire database discards newer unrelated writes unless doing complex point-in-time/reconciliation work. For destructive change, retain old column/table for a window or archive mapping in governed storage.

### 2.13 Deployment controls and observability

Use canary tenants/shards, feature flags, pause/resume backfills and explicit gates. Monitor database latency and error percentiles, lock waits, active/idle transaction ages, CPU/I/O, WAL bytes/rate, replication lag, autovacuum, disk, batch duration/rows, transformation exceptions, CDC lag and application old/new path counters.

Set `application_name` for migration sessions. Use `lock_timeout` to fail fast on lock acquisition and `statement_timeout` as an execution ceiling, chosen so legitimate work is not repeatedly killed. Do not retry DDL in a tight loop; jitter and alert. Schedule based on workload evidence, not the assumption that midnight is quiet for global users.

### 2.14 Multi-tenant and regulated boundaries

Backfill by tenant or key range so one large tenant cannot starve others and results can be reconciled independently. Maintain row-level security context or privileged migration controls carefully; bypassing RLS expands blast radius. Encrypt temporary exports, minimize data, expire them, audit access and test deletion. In healthcare/fintech, migration evidence is part of change control: approved plan, validation output, exceptions, rollback decision and final attestation.

## 3. WORKED PROBLEMS

### Problem 1 — Rename a live column

**Statement.** Rename `patient.name` to `display_name` with a mixed fleet and rollback capability.

**Solution.** Do not directly rename. Add nullable `display_name`; deploy dual-write/old-read; backfill guarded batches; reconcile equality; validate non-null; deploy new-read/dual-write; observe zero old-only writers; deploy new-only; after rollback window drop `name`. If transformation is identity, the process still protects old SQL and serialized mappings. A view/alias can bridge some read consumers but does not replace writer inventory.

**Mistake caught.** Treating a transactional rename as application-compatible.

### Problem 2 — Add mandatory `tenant_id`

**Statement.** Add non-null tenant ownership to 300 million rows.

**Solution.** Add nullable column without rewrite-heavy assumptions. Make every new write supply tenant. Backfill in 5,000-row keyset batches using authoritative ownership mapping, quarantine ambiguous rows rather than guessing. Reconcile counts by tenant and zero NULLs. Add `CHECK (tenant_id IS NOT NULL) NOT VALID`, validate, set NOT NULL, then add/validate tenant-aware foreign keys and indexes in safe phases. Test RLS before enabling.

**Mistake caught.** Defaulting all legacy rows to tenant 1 and creating a data breach.

### Problem 3 — WAL-limited backfill

**Statement.** Staging observes 2.4 KiB WAL/update. Replica budget for migration is 12 MiB/s after normal traffic.

**Solution.** Arithmetic ceiling is `12×1024/2.4 = 5,120 rows/s`. Begin perhaps 1,000–2,000/s with small transactions, measure actual primary WAL/replica lag and adapt. Pause if lag or latency crosses gate. Distribution/index count may differ in production, so the number is not a guarantee.

**Mistake caught.** Sizing by application payload bytes rather than observed WAL.

### Problem 4 — Concurrent unique index fails

**Statement.** A 600 GB table's unique index build fails after hours with duplicates.

**Solution.** Inspect catalog: the invalid index may remain and impose write overhead. Preserve evidence, identify duplicates with domain ownership, stop new duplicates using an appropriate constraint/protocol, resolve existing rows audibly, drop invalid index or use documented concurrent rebuild, and retry while monitoring. Do not call `IF NOT EXISTS`: an invalid same-name object is not success.

**Mistake caught.** Assuming failed concurrent DDL rolled back every artifact.

### Problem 5 — Backfill overwrites live write

**Statement.** Backfill selects NULL v2; application writes v2; backfill later updates using stale selected ID.

**Solution.** Repeat the guard in the UPDATE: `... WHERE id IN batch AND display_name_v2 IS NULL`. The live value now prevents overwrite. If transform must update earlier migration versions, use `migration_version < target` and compare source version. Make transformation deterministic and record conflicts.

**Mistake caught.** Guarding only the initial SELECT.

### Problem 6 — Enum rollout

**Statement.** New code emits `PAUSED`; old code crashes on unknown values.

**Solution.** First deploy tolerant readers that preserve/handle unknown values and APIs with forward-compatible enum behavior. Then expand database constraint/type to accept PAUSED, then enable writers. Only after the fleet and consumers are compatible may traffic produce it. Rollback disables emission but data containing PAUSED must still be readable.

**Mistake caught.** Database-first enum addition before reader compatibility.

### Problem 7 — Split a service database

**Statement.** Move 2 TB model-run history to a new service while writes continue.

**Solution.** Establish snapshot/source position, bulk copy by immutable key ranges, stream CDC changes with idempotent source-position application, include deletes, validate counts/hashes per tenant/date, shadow reads, then canary new reads. Keep one write authority until cutover; use outbox/forwarding during transition. Monitor CDC lag and define rollback routing/replay.

**Mistake caught.** Dual-writing two databases from request code and assuming equal success.

### Problem 8 — Flyway checksum mismatch

**Statement.** A developer edits an applied migration; validation fails in production pipeline.

**Solution.** Compare applied artifact/checksum and repository history; restore the original migration and add a new corrective version. Do not run `repair` merely to silence validation. Redgate docs say repair can realign checksums and alter schema history; use it only after explicit investigation/approval when history metadata—not desired database state—is the known problem.

**Mistake caught.** Rewriting history because current schema “looks right.”

### Problem 9 — Contract gate

**Statement.** New reads have been enabled for two hours and the team wants to drop the old column.

**Solution.** Two hours rarely proves all cron jobs, regional fleet, rollback binaries and rare paths are migrated. Require an observation window covering relevant cycles, query/log/static inventory, zero fallback/old-write counters, reconciliation, restore/rollback decision and approval. Drop in a later release with lock controls. Time alone is not proof; evidence tied to consumers is.

**Mistake caught.** Equating a successful canary with permission for irreversible deletion.

## 4. REAL-WORLD / APPLIED CONTEXT

**PostgreSQL concurrent index build.** PostgreSQL 18 documentation states concurrent creation performs two scans, waits for relevant transactions, takes more total work, and may leave an INVALID index on failure. That index is ignored for queries but can still impose update overhead. The operational lesson is concrete: monitor `pg_stat_progress_create_index`, old transactions, disk/WAL and `pg_index`, not only command exit status.

**Flyway deployment history.** Current Redgate Flyway documentation describes ordered versioned migrations recorded in a schema-history table and checksum validation. Its `repair` command can remove failed entries and realign checksums while user objects may need manual cleanup. This makes migration history a controlled artifact; CI validation and immutable applied scripts protect auditability.

**Large SaaS backfill.** A realistic tenant migration uses 5,000-row batches, commits each, caps at an initially measured 2,000 rows/s, pauses when replica replay lag exceeds 30 seconds or database p99 exceeds its error budget, and writes per-tenant counts/hashes. These thresholds are an explicit scenario, not universal settings. The key practice is closed-loop throttling against business SLOs rather than a fixed maximum-speed job.

Run `expand-contract.sql` only against a disposable schema, phase by phase. It includes the guarded batch, `NOT VALID`/validation sequence, concurrent index caveat and catalog check. `MigrationCompatibility.java` independently proves the intended coexistence matrix.

## 5. COMPARISON TABLE

| Change strategy | Availability/compatibility | Cost | Use when | Main danger |
|---|---|---|---|---|
| Direct rename/drop | breaks old SQL immediately | one DDL | offline/single controlled consumer | rolling deploy/rollback failure |
| Expand–migrate–contract | old/new coexist | multiple releases, duplicate data | live shared database | incomplete inventory/early contract |
| In-place type change | may lock/rewrite | simple code, heavy DB | proven metadata-safe small change | long lock/WAL/rewrite |
| Shadow column | phased conversion | storage/dual write/backfill | large/risky type change | divergence between representations |
| Trigger dual write | covers unknown DB writers | hidden write cost/logic | temporary centralized bridge | recursion, surprise, forgotten trigger |
| App dual write | visible domain logic | every writer must upgrade | known writers, same DB tx | missed job/service |
| CDC transfer | continuous cross-system sync | operational complexity | service/database extraction | lag, duplicates, delete loss |

| Backfill cursor | Work profile | Strength | Boundary |
|---|---|---|---|
| `OFFSET` | rescans/discards deep rows | simple | slows/changes under writes |
| keyset `id > last` | stable indexed progression | efficient/restartable | lower inserted keys need dual-write/final sweep |
| `SKIP LOCKED` batches | parallel claim/update | workers avoid blocking | inconsistent selection by design |
| partition/tenant | bounded reconciliation | isolation/throttling | skewed partitions/tenants |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Transactional DDL is zero-downtime.”** Rollback safety says nothing about lock wait or compatibility.
2. **Direct rename in rolling deploy.** Old binary still names the old column.
3. **Adding NOT NULL before backfill.** Legacy rows fail or statement scans/blocks unexpectedly.
4. **One giant UPDATE.** Huge transaction creates WAL, bloat, lag, locks and painful rollback.
5. **No final UPDATE guard.** A stale backfill overwrites a live dual-write.
6. **Offset batching at depth.** It repeatedly walks skipped rows and moving datasets confuse progress.
7. **`IF NOT EXISTS` as verification.** Same-name object may have wrong or invalid definition.
8. **Assuming concurrent index is cheap.** It takes two scans, waits and consumes I/O/WAL.
9. **Ignoring invalid index remnants.** They may continue update overhead after failed build.
10. **Editing applied migrations.** Environments diverge and checksums lose meaning.
11. **Using repair to silence validation.** It changes history metadata without proving schema/data correctness.
12. **Row counts as reconciliation.** Equal counts can contain wrong values or tenant assignments.
13. **Dual writes forever.** Permanent duplicate representations drift and raise cognitive/operational cost.
14. **Contract after a short canary.** Rare jobs, rollback versions or regions may still depend on old state.
15. **Backup equals easy rollback.** Whole-database restore can lose unrelated newer transactions.
16. **Logging bad regulated rows verbatim.** Migration diagnostics can leak PHI/financial data.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Inventory all readers/writers and state invariants before SQL.
- Expand → dual write/old read → backfill → reconcile → new read → stop old write → contract later.
- Applied versioned migrations are immutable; fix forward with a new version.
- Batch by stable key/tenant, commit small units, repeat UPDATE guard, checkpoint, throttle.
- Measure table/index bytes, workload, WAL/update, replica lag, locks, disk and vacuum.
- `NOT VALID` defers legacy scan; `VALIDATE CONSTRAINT` is a required later gate.
- `CREATE INDEX CONCURRENTLY`: outside transaction, two scans/waits, check invalid remnants.
- Reconcile values/hashes/groups, not only counts; monitor fallback/old-write paths.
- Define point of no return and roll-forward plan; backup restore is not routine rollback.
- Contract only after consumer evidence + rollback window + validation + approvals.
- Cross-database move: snapshot + source position + CDC + idempotent apply + deletes + parity.
- Protect tenant/regulated data in temp files, logs, exception tables and migration access.

## 8. PRACTICE SET FOR SELF-TEST

1. Design a five-deployment expand–contract plan to split `full_name` into `given_name` and `family_name`, including ambiguous names.
2. A table has 900 million rows; observed WAL is 3 KiB/update and safe migration headroom is 24 MiB/s. Calculate an arithmetic ceiling and a conservative starting rate.
3. Explain how a two-worker `SKIP LOCKED LIMIT 5000` backfill avoids duplicate claims and why the final UPDATE still needs a predicate.
4. Give a safe plan for adding a foreign key when 0.02% of existing rows are orphaned.
5. A concurrent index command failed, but rerun with `IF NOT EXISTS` reports success/no-op. Diagnose and repair safely.
6. Design validation evidence for converting rupees stored as text (`"1,234.50"`) to bigint paise across Indian and international formats.
7. Explain why a rollback binary can fail after the database accepts a new enum value, and design the release order.
8. Plan migration of cache keys and Kafka event schema alongside a primary-key change.
9. Define pause/abort gates for a backfill on a healthcare production primary.
10. Distinguish Flyway `validate`, `repair`, and a corrective versioned migration; state when each is legitimate.

## 9. CURATED RESOURCES

1. PostgreSQL 18 Manual, [`ALTER TABLE`](https://www.postgresql.org/docs/current/sql-altertable.html). Exact lock levels, `NOT VALID`, validation, type/default and constraint behavior.
2. PostgreSQL 18 Manual, [`CREATE INDEX`](https://www.postgresql.org/docs/current/sql-createindex.html). Primary source for concurrent build scans/waits, invalid indexes and transaction restriction.
3. PostgreSQL 18 Manual, [Progress Reporting](https://www.postgresql.org/docs/current/progress-reporting.html). Catalog views for monitoring index creation, vacuum and related long operations.
4. PostgreSQL 18 Manual, [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html). Lock compatibility and deadlock foundations for DDL planning.
5. Redgate Flyway, [Migrations](https://documentation.red-gate.com/fd/migrations-271585107.html). Current versioned/repeatable/baseline model and schema-history workflow.
6. Redgate Flyway, [Commands](https://documentation.red-gate.com/flyway/reference/commands). Exact purposes of info, validate, migrate, repair, baseline and drift tools.
7. Redgate Flyway, [Migration transaction handling](https://documentation.red-gate.com/fd/migration-transaction-handling-273973399.html). Per-migration transactions and database-specific nontransactional caveats.
8. Fowler, “Evolutionary Database Design,” martinfowler.com (with Pramod Sadalage). Canonical refactoring, transition period and database delivery practices.
9. Sadalage and Fowler, *Refactoring Databases*, Chapters 2–4 and catalog refactorings. Detailed patterns for structural/data transitions and application coordination.
10. Kleppmann, *Designing Data-Intensive Applications*, Chapters 4 and 11. Encoding evolution, dataflow compatibility, batch/stream migration and derived data.

## 10. RELATED TOPICS BRIDGE

### Before

1. **PostgreSQL Modeling.** Target constraints/types must embody the desired durable model.
2. **Indexes and Query Plans.** Backfills and validations require bounded access paths and explainable scan costs.
3. **Transactions and Locking.** DDL locks, batch commits and concurrent writers determine safety.
4. **Redis and Caching.** Cache namespaces/versions must evolve with source schema and invalidations.

### After

1. **Kafka Fundamentals.** CDC/outbox streams carry ordered, replayable changes to downstream stores.
2. **Delivery Semantics.** Migration consumers must handle duplicate/retried change events idempotently.
3. **Kubernetes Deployments.** Rolling application versions create the compatibility window expand–contract addresses.
4. **Regulated Data Design.** Lineage, retention, deletion and audit evidence constrain transformations.

---ANSWER KEY BELOW---

1. Add nullable given/family plus parse-status/raw-version; deploy dual-write old-read with a deterministic parser that marks ambiguous names; backfill batches and route ambiguity to governed review; reconcile; deploy new-read fallback/dual-write; stop old writer; only contract after all consumers/rollback window. Never invent family names.
2. `24×1024/3 = 8,192 rows/s` arithmetic ceiling. Start materially lower, perhaps 1,500–3,000/s after normal-workload margin, and adapt from WAL/lag/latency/disk; observed production bytes may differ.
3. Row locks plus SKIP LOCKED cause each worker to select currently unlocked rows. Another writer can populate a selected row before update under some structures/timing, so `WHERE target IS NULL` (or migration_version guard) at UPDATE prevents regression; commit each batch and final-sweep/reconcile.
4. Add FK `NOT VALID` so new changes are checked; identify orphan rows by tenant/owner, quarantine or repair from authoritative source with audit, prove zero orphans, then `VALIDATE CONSTRAINT`. Do not delete or attach a fake parent automatically.
5. A same-name INVALID index may remain; `IF NOT EXISTS` checks name, not validity/definition. Inspect `pg_index.indisvalid/indisready` and definition, assess overhead, drop/rebuild per PostgreSQL concurrent procedure, monitor blockers/WAL and verify final catalog/plan.
6. Preserve raw source and parser version; explicitly define accepted separators/currency/locale, decimal precision and rounding; parse with arbitrary-precision decimal, multiply by 100 exactly and range-check; quarantine ambiguity; reconcile counts/sums/min/max by tenant/currency and independently sample. Never strip punctuation blindly or use double.
7. Old exhaustive decoder crashes on unknown PAUSED after binary rollback. Deploy tolerant readers first, then database acceptance, then emitters; rollback disables emission but tolerant old-compatible readers remain. Contract old semantics only later.
8. Add new ID alongside old and immutable mapping; events carry both under a new backward-compatible schema; consumers upgrade and checkpoint; cache uses versioned new namespace with invalidation of both; migrate FKs and external references; observe old-ID usage zero before removing mapping. Avoid in-place opaque rename.
9. Pause on sustained primary p99/SLO breach, replica lag above approved threshold, WAL/disk headroom floor, lock waits/deadlocks, autovacuum/freeze risk, error/quarantine rate, CDC lag, or tenant correctness mismatch. Define numeric thresholds from baseline/capacity and an incident owner; never log PHI payloads.
10. Validate compares available/applied migration identity/checksums and should run routinely. Repair deliberately changes schema-history metadata/removes failed records after investigation and manual object cleanup. A corrective versioned migration is normal fix-forward for desired schema/data changes; it preserves immutable history.
