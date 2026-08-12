# PostgreSQL Setup and Operations Basics from Scratch

Parent subject: `03-data-systems`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### From SQL language to a running database system

SQL describes data operations; PostgreSQL is the server that parses, plans, executes, coordinates, persists, secures, replicates, backs up, and recovers those operations. A backend engineer need not be a full-time database administrator, but must understand the service boundary. Otherwise connection storms, unsafe privileges, untested backups, long transactions, configuration mistakes, and storage exhaustion become application incidents.

PostgreSQL descends from the POSTGRES research project led by Michael Stonebraker at Berkeley, following the earlier Ingres project. It emphasizes extensible types and operators, standards-oriented SQL, multi-version concurrency control, and durable write-ahead logging. It is open source and widely used for transactional and analytical workloads.

### Server, cluster, instance, database, and schema

Terminology is overloaded across products. In PostgreSQL, a **database cluster** is one server installation/data directory managed by one server process hierarchy and containing multiple databases. It is not the same as a multi-node distributed cluster. A running PostgreSQL **server** (often informally instance) listens for connections and manages that cluster.

A **database** is an isolated catalog namespace inside the cluster. Connections target one database, and ordinary SQL cannot directly join tables across databases. A **schema** is a namespace within a database, such as `app`, `audit`, or `ml_registry`. Tables with the same unqualified name can exist in different schemas. The `search_path` controls name resolution and has security implications: production code should use controlled paths or schema-qualified names.

A **role** is an identity that can own objects, receive privileges, and optionally log in. PostgreSQL unifies “users” and “groups” as roles. A login role authenticates a connection; group roles collect privileges. Superuser bypasses most checks and should never be the routine application identity.

### Client/server connections

A PostgreSQL client connects over a Unix-domain socket or TCP using host, port (default 5432), database, user, authentication, and TLS settings. `psql` is the standard interactive terminal. An application uses a driver such as PostgreSQL JDBC or psycopg.

Each ordinary PostgreSQL connection corresponds to a backend process and consumes memory/resources. A service with 100 replicas and a pool of 50 can request 5,000 connections, far beyond many database configurations. Pool sizing must be coordinated globally. Transaction-pooling proxies such as PgBouncer reduce server connection pressure but change session-feature assumptions.

### Physical storage and write-ahead logging

PostgreSQL stores table and index data in pages, commonly 8 KiB. Modified pages are eventually written to data files. Before a change is considered durable, relevant records are written to the **write-ahead log** (WAL). Recovery replays WAL after a crash. This write-ahead principle avoids synchronously flushing every changed data page at commit.

WAL enables crash recovery, physical replication, and point-in-time recovery when archived with a base backup. It is not itself a substitute for backups: local WAL can be lost with the storage, corrupted data can be faithfully replicated, and retention is finite.

### Processes, memory, and maintenance

The server has a postmaster/main process, client backends, WAL writer, checkpointer, background writer, autovacuum workers, and other helpers depending on features/version. PostgreSQL uses shared buffers plus operating-system cache; per-operation memory such as `work_mem` can be consumed by many sorts/hash operations concurrently, so multiplying it by maximum connections is more honest than viewing it as one global allocation.

PostgreSQL's MVCC leaves old row versions that later become removable. **VACUUM** makes their space reusable and advances transaction-ID safety; **ANALYZE** updates statistics used by the planner. **Autovacuum** automates both and is essential, not optional housekeeping. `VACUUM FULL` rewrites and locks tables; it is not routine vacuum.

### Configuration layers

Server parameters have contexts: some require restart, some reload, some session change. Configuration may come from `postgresql.conf`, included files, `ALTER SYSTEM`, environment/platform settings, database/role settings, or session `SET`, subject to parameter rules. `SHOW`, `current_setting`, and `pg_settings` reveal effective values and sources.

Client authentication rules live in `pg_hba.conf`, evaluated top to bottom. A rule chooses connection type, database, user, address, and authentication method. `listen_addresses` controls server listening interfaces; pg_hba controls who can authenticate; network firewalls/security groups control reachability. All layers matter.

### Types and time

Common types include `smallint`, `integer`, `bigint`, `numeric`, `text`, `boolean`, `date`, `timestamp`, `timestamp with time zone` (`timestamptz`), `uuid`, `jsonb`, arrays, ranges, and domain/enum types. Choose by semantics.

`timestamptz` represents an absolute instant and displays it in the session time zone; it does not store an original named time zone. `timestamp without time zone` is a calendar date/time without zone interpretation. Store global event instants as `timestamptz`, usually operate in UTC, and store a separate IANA zone name when future local scheduling depends on civil-time rules.

### Backup, restore, and recovery

A backup is useful only if restorable within required recovery objectives. **Logical backups** (`pg_dump`) extract schema/data in a portable logical form and can restore selected objects; they are slower for very large databases and do not provide cluster-wide physical recovery. **Physical base backups** copy cluster storage consistently and combine with WAL for streaming replicas/PITR. Managed services expose variants through snapshots, automated backups, and restore workflows.

**RPO** is the acceptable data-loss window; **RTO** is the acceptable restoration-time window. A daily dump can have nearly 24-hour RPO and hours of RTO. If the requirement is RPO ≤5 minutes and RTO ≤30 minutes, daily dumps alone cannot satisfy it.

### Observability and safe access

System catalogs and views expose activity, locks, table/index statistics, replication, WAL, and configuration. `pg_stat_activity` shows sessions and current state; `pg_locks` shows lock requests; `pg_stat_database` summarizes database activity; `pg_stat_user_tables` exposes scans, changes, and vacuum/analyze history.

Do not query sensitive SQL text casually or grant broad monitoring access without review. Observability identities should be read-only and scoped. Application secrets belong in a secret manager, rotate, use TLS verification, and never appear in source or command history.

## 2. CORE MECHANICS

### 2.1 Install or run a disposable local instance

Use the official packages for your operating system, a managed service, or a pinned container image for learning. A disposable container example is conceptually:

```bash
docker run --name study-postgres \
  -e POSTGRES_PASSWORD=local-only-password \
  -p 127.0.0.1:5432:5432 \
  -d postgres:17
```

Pin an exact supported version in reproducible environments rather than floating tags. Bind to loopback for local-only use. The environment password may appear in tooling metadata; it is suitable only for a disposable lab, not production.

Connect:

```bash
psql "host=127.0.0.1 port=5432 dbname=postgres user=postgres sslmode=prefer"
```

Prefer `.pgpass` with strict permissions or a secret-injection mechanism over putting production passwords on command lines.

### 2.2 Navigate with psql

`psql` meta-commands begin with backslash and are client commands, not SQL:

- `\conninfo`: current connection.
- `\l`: databases.
- `\dn`: schemas.
- `\dt app.*`: tables.
- `\d+ app.claim`: detailed object definition.
- `\du`: roles.
- `\x auto`: expanded display.
- `\timing on`: client elapsed timing.
- `\q`: quit.

Use `\set ON_ERROR_STOP on` in scripts so errors stop execution. Without it, later statements may run and create partially applied setup.

### 2.3 Create least-privilege roles and namespaces

As an administrative role:

```sql
CREATE ROLE claims_owner NOLOGIN;
CREATE ROLE claims_app LOGIN PASSWORD 'replace-via-secret-manager';
CREATE DATABASE claims OWNER claims_owner;
```

Connected to `claims`:

```sql
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA app AUTHORIZATION claims_owner;
GRANT USAGE ON SCHEMA app TO claims_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO claims_app;
ALTER DEFAULT PRIVILEGES FOR ROLE claims_owner IN SCHEMA app
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO claims_app;
```

Object privileges and future default privileges are separate. `ALTER DEFAULT PRIVILEGES` applies to objects later created by the named creator role. Avoid having migration and runtime roles share broad ownership privileges.

### 2.4 Understand connection URLs and TLS

A URI resembles `postgresql://user@db.example:5432/claims?sslmode=verify-full`. `verify-full` validates the certificate chain and hostname. `require` encrypts but, depending on libpq behavior/configuration, does not provide equivalent identity verification. In regulated production, use CA-validated TLS and verify the provider/driver's exact semantics.

Set connection, statement, lock, and idle-in-transaction timeouts according to request budgets:

```sql
ALTER ROLE claims_app IN DATABASE claims SET statement_timeout='3s';
ALTER ROLE claims_app IN DATABASE claims SET lock_timeout='500ms';
ALTER ROLE claims_app IN DATABASE claims SET idle_in_transaction_session_timeout='30s';
```

These are examples, not universal values. A 3-second database statement is incompatible with a 500 ms API deadline; budgets must nest coherently.

### 2.5 Create typed tables

```sql
CREATE TABLE app.claim (
  claim_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  external_ref text NOT NULL,
  amount_paise bigint NOT NULL CHECK (amount_paise > 0),
  status text NOT NULL CHECK (status IN ('SUBMITTED','APPROVED','REJECTED','PAID')),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  payload jsonb,
  UNIQUE (tenant_id, external_ref)
);
```

`jsonb` is valuable for genuinely semi-structured attributes, not an excuse to avoid modeling keys and frequently queried invariants. Large unconstrained JSON documents can move validation, migrations, and indexing complexity into application code.

### 2.6 Inspect sessions and cancel safely

```sql
SELECT pid, usename, application_name, state,
       now()-query_start AS elapsed, wait_event_type, wait_event,
       left(query, 200) AS query_prefix
FROM pg_stat_activity
WHERE datname=current_database()
ORDER BY query_start NULLS LAST;
```

`pg_cancel_backend(pid)` requests cancellation of the current query while retaining the session. `pg_terminate_backend(pid)` ends the session and rolls back its transaction; use only with authorization and impact review. First identify owner, transaction state, blocker/blockee relationship, and application retry behavior.

### 2.7 Inspect configuration and maintenance

```sql
SELECT name, setting, unit, context, source, pending_restart
FROM pg_settings
WHERE name IN ('max_connections','shared_buffers','work_mem','statement_timeout');

SELECT relname, n_live_tup, n_dead_tup,
       last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

High dead-tuple estimates do not automatically mean `VACUUM FULL`; investigate autovacuum thresholds, long transactions preventing cleanup, churn, table size, and bloat evidence. Statistics are estimates and cumulative views may reset.

### 2.8 Logical backup and verified restore

Custom-format backup:

```bash
pg_dump --format=custom --file=claims.dump --dbname=claims
createdb claims_restore_test
pg_restore --exit-on-error --clean --if-exists \
  --dbname=claims_restore_test claims.dump
```

Verification must include schema presence, row counts/checksums appropriate to tables, constraints, sequences/identities, application smoke tests, permissions, and recovery timing. Never run `--clean` against an unresolved or production target; exact target verification is mandatory.

### 2.9 Connection pool arithmetic

Suppose server safe application connections are 180 after reserving 20 for administration/maintenance. There are 30 service replicas. A pool max of 10 requests 300 connections and is unsafe. A first allocation is floor(180/30)=6 per replica, then load test wait time and query concurrency. Autoscaling to 60 replicas halves the safe per-instance budget to 3 unless a proxy/global control changes the model.

Pool size should follow concurrent database work the server can execute, not HTTP thread count. Oversized pools increase queueing inside the database and memory use rather than creating capacity.

### 2.10 Version upgrades

Patch/minor upgrade methods depend on packaging/provider. Major PostgreSQL versions change on-disk/catalog compatibility and require a supported path such as `pg_upgrade`, logical replication, or dump/restore. Read release notes, extension compatibility, removed behavior, and planner changes; rehearse with production-scale copies; measure downtime; preserve rollback strategy and backups.

## 3. WORKED PROBLEMS

### Problem 1 — Database versus schema (easy)

Should `audit` be a separate database merely to namespace tables?

**Solution.** Usually a schema is the direct namespace within the same transactional/query boundary. A separate database adds connection and cross-database limitations and may be warranted for stronger isolation, ownership, lifecycle, or scaling—but not just to avoid name collisions.

**Trap:** treating database and schema as synonyms.

### Problem 2 — Role separation (easy)

Why should the application not connect as table owner?

**Solution.** Owners can alter/drop objects and bypass ordinary grants. A runtime role should have only required DML and sequence/function privileges; a migration/owner role changes schema through controlled delivery.

**Trap:** using superuser because permissions are inconvenient.

### Problem 3 — Timestamp choice (easy)

Store the instant a claim was received globally.

**Solution.** Use `timestamptz`, transmit ISO-8601 offsets/UTC, and compare instants. If “9:00 AM Asia/Kolkata every future weekday” is required, also retain the named IANA time zone and scheduling rule.

**Trap:** believing `timestamptz` preserves the original zone name.

### Problem 4 — Connection budget (medium)

Database supports 240 total connections; reserve 40. Forty replicas each pool 8. Assess.

**Solution.** Application budget is 200; configured demand is 320, 120 over budget. A static equal allocation is at most 5 per replica. Then account for other workloads, autoscaling, connection proxying, and measured concurrency.

**Trap:** sizing each instance independently.

### Problem 5 — RPO/RTO (medium)

Nightly dump finishes at 01:00. Failure occurs at 00:55 next day. Maximum data loss?

**Solution.** Nearly 23 hours 55 minutes if only that dump is restorable. It cannot meet a five-minute RPO. Add appropriate WAL archival/managed PITR and verify restoration.

**Trap:** equating “daily backup succeeded” with business recovery compliance.

### Problem 6 — Long idle transaction (medium)

`pg_stat_activity` shows `idle in transaction` for two hours. Why care?

**Solution.** It may retain locks and an old snapshot, preventing vacuum from reclaiming versions and causing bloat/transaction-age risk. Identify application/owner, assess work, cancel/terminate safely, then fix transaction scope and enforce idle timeout.

**Trap:** focusing only on actively running queries.

### Problem 7 — `work_mem` arithmetic (hard)

Set `work_mem=256MB` with 200 connections. Is memory capped at 256 MB?

**Solution.** No. It is roughly per sort/hash operation, and a query can have multiple nodes; parallel workers and concurrent sessions multiply it. Even one operation on each of 200 connections could imply 50 GB theoretical allocation before other memory. Tune from workload evidence, often per role/query.

**Trap:** interpreting it as one global pool.

### Problem 8 — Replica as backup (hard)

An operator drops a table and streaming replica replays the drop. Was the replica a backup?

**Solution.** No. Replication improves availability and may support failover/read scaling, but faithfully propagates logical mistakes. Recover from independent backups/PITR with retention and tested restore.

**Trap:** conflating high availability with recoverability.

### Problem 9 — Secret in URI (hard)

A deployment logs `DATABASE_URL` including password. What is the fix?

**Solution.** Rotate the exposed credential; remove/redact environment/config dumps; obtain credentials from a managed secret/workload identity mechanism when supported; restrict logs and historical artifacts; use least privilege and TLS verification; audit access. Merely deleting one current log line is insufficient.

**Trap:** treating credential exposure as a cosmetic logging issue.

## 4. REAL-WORLD / APPLIED CONTEXT

### Managed Azure Database for PostgreSQL

Managed PostgreSQL automates parts of patching, backups, monitoring, and high availability, but application responsibilities remain: connection budgets, query/index behavior, role grants, timeouts, schema changes, restore exercises, and recovery objectives. “Managed” changes the operational boundary; it does not remove it.

### PgBouncer

PgBouncer pools PostgreSQL connections. Session pooling preserves session state per client connection; transaction pooling assigns a server connection only for a transaction, scaling better but making session-scoped features such as some prepared statement/temp table/advisory-lock patterns require scrutiny. Driver and PgBouncer versions/features matter.

### MVCC and autovacuum

PostgreSQL updates create new row versions rather than overwriting in place for concurrent readers. Autovacuum cleans removable versions and prevents transaction ID wraparound. A long-lived snapshot can delay cleanup across substantial write volume, turning an application transaction leak into storage and performance degradation.

## 5. COMPARISON TABLE

| Mechanism | Protects against | Typical RPO/RTO | Limitation |
|---|---|---|---|
| Streaming replica | Primary host/storage failure | Low lag / minutes with automation | Replays deletes/corruption; lag/failover risk |
| Daily logical dump | Some logical loss, portability | Up to ~24h / potentially hours | Slow and coarse for large DB |
| Base backup + archived WAL | Physical loss, point-in-time recovery | Depends on WAL archive interval / rehearsed restore | Operational complexity/storage |
| Managed PITR | Provider-supported point-in-time restore | Provider retention/granularity | Must test new-server restore and cutover |
| Schema | Namespace inside database | Same connection/transaction | Weaker isolation than separate DB/cluster |
| Separate database | Catalog/access/lifecycle boundary | Separate connection | No ordinary cross-DB joins/transactions |
| Direct connections | Simple session semantics | One backend per connection | Connection/memory pressure |
| Transaction pool | Reuses fewer server connections | Better multiplexing | Session-state compatibility constraints |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **PostgreSQL cluster means distributed nodes.** It usually means one data directory/server collection of databases.
2. **Schema and database are interchangeable.** They have different connection and isolation boundaries.
3. **Application role should own tables.** Separate migration ownership from runtime DML.
4. **TLS `require` always verifies identity.** Use and verify appropriate certificate/hostname validation semantics.
5. **More connections increase throughput.** Beyond useful concurrency they add memory and queueing.
6. **Replica equals backup.** Replicas replay operator mistakes.
7. **Backup success proves recovery.** Only timed restore verification does.
8. **VACUUM FULL is routine maintenance.** It rewrites/locks and needs deliberate planning.
9. **work_mem is a global cap.** It can multiply per operation, query, worker, and session.
10. **timestamptz stores a timezone.** It stores an instant and displays in a session zone.
11. **Managed service removes database operations.** Responsibility is shared, not eliminated.
12. **Default privileges alter existing objects.** They affect future objects created by specified roles.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Cluster/data directory → databases → schemas → tables.
- Role can own/grant/login; runtime app should not be owner/superuser.
- Default TCP port 5432; pool globally, not per instance in isolation.
- WAL precedes durable data-page writes; enables recovery/replication.
- Autovacuum is essential for MVCC cleanup/statistics/wraparound safety.
- `timestamptz` for instants; separate zone ID for future civil schedules.
- `pg_stat_activity`, `pg_locks`, `pg_stat_user_tables`, `pg_settings` are first inspection points.
- Replica ≠ backup; backup ≠ recovery until restore is tested.
- RPO = acceptable loss; RTO = acceptable restoration time.
- `work_mem` multiplies; oversized connection pools hurt.
- Pin versions and rehearse major upgrades.

## 8. PRACTICE SET FOR SELF-TEST

1. Place these in hierarchy: table, cluster, schema, database.
2. Explain the difference between a login role and an owner/group role.
3. Choose PostgreSQL types for event instant, birthday, UUID, exact paise amount, and flexible metadata.
4. Calculate pool demand for 25 replicas with pool max 12.
5. With 150 safe application connections and 50 replicas, give the naive upper bound per replica.
6. Explain why an open transaction can block vacuum cleanup without holding an obvious table lock.
7. Choose logical or physical/PITR backup for restoring one accidentally dropped small table versus a 5 TB cluster after storage loss.
8. State checks required after a restore.
9. Explain `pg_cancel_backend` versus `pg_terminate_backend`.
10. Give three layers that must allow a remote TLS connection.

## 9. CURATED RESOURCES

- PostgreSQL current documentation, Chapter 18 “Server Setup and Operation” — authoritative cluster creation, startup, configuration, SSL, and upgrade operations.
- PostgreSQL current documentation, Chapters 19–21 “Server Configuration,” “Client Authentication,” and “Database Roles” — exact parameter, pg_hba, role, ownership, and privilege semantics.
- PostgreSQL current documentation, Chapter 25 “Routine Database Maintenance Tasks” — vacuum, analyze, reindex, and log maintenance.
- PostgreSQL current documentation, Chapter 26 “Backup and Restore” and Chapter 27 “High Availability, Load Balancing, and Replication” — logical/physical backup, WAL archival, PITR, replication, and failover foundations.
- PostgreSQL current documentation, Chapter 28 “Monitoring Database Activity” — authoritative statistics views and operational inspection.
- PostgreSQL JDBC documentation, “Initializing the Driver,” “Using SSL,” and connection properties — Java client connection/TLS/timeout behavior.
- PgBouncer official documentation, “Features” and configuration reference — session, transaction, and statement pooling compatibility.
- Michael Stonebraker and Lawrence Rowe, “The Design of POSTGRES,” 1986 — primary historical architecture and extensibility motivation.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Database and Relational Foundations:** defines keys, constraints, relationships, transactions, and normalization.
2. **SQL from Scratch:** supplies the statements the server plans and executes.
3. **Linux/Shell Foundations (Parent 05):** helps with processes, files, permissions, logs, and client commands; it can be learned in parallel.

### After

1. **PostgreSQL Modeling:** deepens PostgreSQL-specific data and tenant design.
2. **Indexes and Query Plans:** uses statistics, buffers, and EXPLAIN to optimize access.
3. **Transactions and Locking:** deepens MVCC, isolation, conflicts, and retries.
4. **Data Migrations:** changes live schemas safely using roles, locks, backups, and observability.
5. **SRE/Observability:** turns database signals and recovery drills into production objectives.

---ANSWER KEY BELOW---

1. Cluster contains databases; database contains schemas; schema contains tables.
2. LOGIN permits authentication; ownership/privilege membership can belong to NOLOGIN roles and be granted to controlled identities.
3. `timestamptz`, `date`, `uuid`, `bigint`, `jsonb` (with modeled core fields and size/validation policy).
4. 300 possible connections.
5. Three per replica, before workload-specific reservations/proxy considerations.
6. Its old MVCC snapshot can make dead tuples still potentially visible, preventing removal.
7. Logical/targeted restore may suit one table if dependencies and consistency are handled; physical base backup plus WAL/PITR suits full 5 TB recovery.
8. Schema/extensions, constraints/indexes, row/checksum evidence, privileges, sequence state, application smoke tests, recovery point, and elapsed RTO.
9. Cancel stops current statement while keeping session; terminate ends session and rolls back its open transaction.
10. Network routing/firewall, server `listen_addresses`, matching pg_hba authentication, plus valid TLS/client credentials (four valid layers).
