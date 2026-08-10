# Transactions and Locking

**Parent:** 03 — Data Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus a two-session PostgreSQL lab

## 1. FOUNDATIONS

A transaction is a boundary around state changes that must be judged together. Transferring ₹2,500 from wallet A to B is not two unrelated updates: either both balances change or neither does. The database provides `BEGIN`, `COMMIT`, and `ROLLBACK`, but those commands do not invent the business invariant. The engineer must identify it—nonnegative balances, exactly-once ledger entry, at least one clinician on call—and choose schema constraints and concurrency control that preserve it.

The familiar **ACID** acronym names four properties. **Atomicity** means a transaction's effects commit together or are undone. **Consistency** means a successful transaction takes the database from one state satisfying declared/application invariants to another; the database cannot enforce an invariant never encoded or correctly locked. **Isolation** governs interference among concurrent transactions. **Durability** means acknowledged commits survive failures under the configured storage/replication guarantees. Durability is not the same as cross-region disaster recovery, and a committed database transaction cannot atomically retract an email already sent.

Early database systems used locks to prevent harmful overlap. Modern PostgreSQL uses **multi-version concurrency control (MVCC)**: updating a tuple creates a new version rather than overwriting it in place. A transaction reads versions visible to its **snapshot**, a logical view determined by transaction IDs and commit state. Readers generally do not block writers, but old versions must remain while an old snapshot might need them, so vacuum later reclaims them. Long-running or “idle in transaction” sessions can retain dead tuples, enlarge tables/indexes, delay transaction-ID cleanup and turn an application leak into an operational incident.

Isolation exists because concurrency creates histories that differ from any intended serial execution. A **dirty read** observes uncommitted data. A **nonrepeatable read** gets a different value when re-reading a row. A **phantom** re-runs a predicate and gets a changed row set. A **lost update** overwrites another transaction's change. **Write skew** occurs when two transactions read a shared condition and update disjoint rows, jointly breaking the condition. A **serialization anomaly** means committed outcomes cannot be explained by any one-at-a-time order.

The SQL standard describes four levels. PostgreSQL 18 implements three distinct behaviors: requested Read Uncommitted acts as Read Committed. PostgreSQL Repeatable Read is snapshot isolation and is stronger than the standard minimum because it prevents phantoms, yet it can permit write skew. Serializable uses Serializable Snapshot Isolation (SSI): it tracks read/write dependencies and aborts a transaction when necessary to ensure committed transactions have an equivalent serial ordering. Therefore, “stronger isolation” often means “the application must correctly retry more,” not “nothing fails.”

A **lock** reserves a resource in a mode compatible or incompatible with other modes. Locks may concern relations, rows, transaction IDs, advisory keys, or—in SSI—logical read predicates. A **blocking wait** is not a deadlock: it may finish when the holder commits. A **deadlock** is a cycle, such as T1 holds A and waits for B while T2 holds B and waits for A. PostgreSQL detects cycles and aborts one participant; the application must treat SQLSTATE `40P01` as a retryable transaction failure when the operation is safe to repeat.

The central senior-level idea is that concurrency correctness is an invariant-and-history problem. “We use transactions” and “we use `FOR UPDATE`” are incomplete statements. Which rows/predicate represent the invariant? Are all writers following the same protocol? What happens after a timeout when commit status is unknown? Is retry idempotent? What is the contention and latency budget?

## 2. CORE MECHANICS

### 2.1 Transaction boundaries and savepoints

Autocommit makes each SQL statement its own transaction. A multi-statement invariant needs an explicit boundary:

```sql
BEGIN;
UPDATE wallet SET balance_minor=balance_minor-2500 WHERE id=1;
UPDATE wallet SET balance_minor=balance_minor+2500 WHERE id=2;
INSERT INTO ledger(transfer_id,from_id,to_id,amount_minor)
VALUES ('018f...',1,2,2500);
COMMIT;
```

If the second update fails, the transaction enters an aborted state until rollback. A **savepoint** allows partial rollback within a transaction, but it does not make external side effects reversible. Keep transactions short: never hold row locks while awaiting user input or a remote ML endpoint.

The example is still incomplete: the debit needs a sufficient-funds guard, IDs should be locked consistently, and `transfer_id` needs a uniqueness constraint for idempotency. A better debit is atomic:

```sql
UPDATE wallet
SET balance_minor=balance_minor-2500, version=version+1
WHERE id=1 AND balance_minor>=2500
RETURNING balance_minor;
```

Zero returned rows means absent wallet or insufficient funds; distinguish them only if the API needs to, without splitting the guarded write into a racy read-then-write.

### 2.2 Snapshot visibility and tuple versions

Conceptually each tuple version has creating/deleting transaction metadata. A snapshot decides which creators/deleters are visible. Your transaction sees its own preceding writes. Another transaction's uncommitted version is invisible. At Read Committed, each statement takes a fresh snapshot, so two SELECTs can differ. At Repeatable Read and Serializable, the stable snapshot begins at the first non-transaction-control statement.

MVCC avoids many read/write waits, not all waits. Two writers targeting the same current row conflict. `SELECT ... FOR UPDATE` locks selected rows against competing modifications/locking modes. Foreign-key checks, unique insertion, DDL and index work can also wait. Visibility and locking are related but distinct: a transaction may see an old version while another owns a newer one.

### 2.3 Read Committed

Read Committed is PostgreSQL 18's default. Each command sees data committed before that command began, plus its transaction's prior changes. Suppose balance is 10,000. T1 reads 10,000. T2 atomically subtracts 2,000 and commits. T1's next SELECT sees 8,000. That nonrepeatable read is allowed.

A classic lost update happens when both services read 10,000, compute absolute values (8,000 and 7,000), then execute `SET balance_minor=:computed`. Whichever executes last overwrites the other. Avoid this with an atomic relative update, pessimistic row lock, or optimistic version predicate:

```sql
UPDATE wallet SET balance_minor=7000, version=version+1
WHERE id=1 AND version=12;
```

If affected rows is zero, someone changed version 12; reload and re-evaluate the business operation. Never retry by blindly reusing a stale absolute result.

### 2.4 Repeatable Read / snapshot isolation

A Repeatable Read transaction sees a stable snapshot and its own writes. PostgreSQL prevents dirty reads, nonrepeatable reads and phantoms at this level. When it tries to update a row changed after its snapshot, it may fail with “could not serialize access due to concurrent update”; retry the whole transaction.

Snapshot isolation can still allow write skew. Initially Asha and Bimal are both on call. T1 and T2 each read `count(*)=2`. T1 marks Asha unavailable; T2 marks Bimal unavailable. They update different rows, so both can commit at Repeatable Read, leaving zero available. The invariant spans a predicate/set, not a single conflicting row. Solutions include Serializable with retries, locking a common invariant row (for example, one rota row), or redesigning the constraint/state transition. Merely locking each doctor being changed does not serialize the shared decision.

### 2.5 Serializable and retry semantics

PostgreSQL Serializable monitors rw-dependencies via nonblocking predicate locks (`SIReadLock`). If concurrent work could form a dangerous structure inconsistent with serial execution, one transaction aborts with SQLSTATE `40001`. The database protects the history by rejecting work; the application completes the guarantee by retrying the **entire transaction** from fresh reads.

A robust retry policy:

1. Begins a new transaction and re-runs all reads/decisions.
2. Retries classified transient SQLSTATEs such as serialization failure `40001` and, where operation semantics allow, deadlock `40P01`.
3. Uses bounded attempts, exponential backoff and jitter to avoid synchronized retry storms.
4. Does not retry validation/unique/FK errors generically.
5. Preserves an idempotency key across an ambiguous client retry.
6. Emits attempt count and final outcome metrics without logging sensitive payloads.

`RetryPolicy.java` tests a small classification and backoff calculation. In real JDBC code, inspect `SQLException.getSQLState()`, roll back/close the failed transaction, and rerun through a new transaction boundary. Spring's proxy-based `@Transactional` semantics and retry advice ordering must be tested; self-invocation can bypass proxies.

### 2.6 Pessimistic row locks

`SELECT ... FOR UPDATE` is appropriate when a transaction must read state, make a nontrivial decision, then update the same entity. `FOR NO KEY UPDATE` is weaker where key columns are not changed. `FOR SHARE` and `FOR KEY SHARE` protect rows with progressively different conflicts. Choose the weakest mode that enforces the protocol, but every writer must participate.

`NOWAIT` fails immediately instead of queueing. `SKIP LOCKED` skips rows locked by another transaction and is useful for multi-worker queues:

```sql
WITH jobs AS (
  SELECT id FROM job
  WHERE status='READY'
  ORDER BY priority DESC,id
  FOR UPDATE SKIP LOCKED LIMIT 20
)
UPDATE job SET status='RUNNING', leased_until=now()+interval '2 minutes'
WHERE id IN (SELECT id FROM jobs)
RETURNING *;
```

`SKIP LOCKED` deliberately provides an inconsistent view, so it is not for financial queries. A lease needs recovery for crashed workers, attempt limits and idempotent handlers.

### 2.7 Table locks and DDL

PostgreSQL table lock modes range from `ACCESS SHARE` to `ACCESS EXCLUSIVE`. Ordinary SELECT takes AccessShare; many DDL commands need stronger modes. Stronger does not mean a lock covers more rows—it means it conflicts with more modes. A “fast metadata migration” can wait behind a long query, then cause new sessions to queue behind it. Use `lock_timeout`, inspect blockers, stage operations and understand the exact PostgreSQL-version lock behavior.

Do not casually execute `LOCK TABLE` to solve row-level invariants. It destroys concurrency and can mask poor modeling. It may be justified for rare maintenance or a genuinely table-wide consistency procedure.

### 2.8 Deadlocks and lock ordering

T1 locks wallet 1, T2 locks wallet 2, then each requests the other's row: a wait-for cycle. PostgreSQL detects it after its deadlock detection process and aborts one transaction. Prevent common cycles by sorting resource keys and locking in a global order: both transfers lock smaller wallet ID first. Keep transactions short and index predicates used by updates so statements do not touch/lock more work than expected.

`lock_timeout` limits waiting for any lock; `statement_timeout` limits total statement execution; `idle_in_transaction_session_timeout` can terminate sessions stranded inside transactions. These are safety boundaries, not substitutes for diagnosing contention. A timeout may leave the client uncertain whether the server committed if the connection failed around COMMIT; reconcile by idempotency key/status lookup.

### 2.9 Advisory locks

Advisory locks attach application meaning to a 64-bit key or pair of 32-bit keys. Transaction-level advisory locks release at transaction end; session-level locks persist until explicit unlock/session end and are easier to leak through pools. They are useful for coarse coordination such as one model promotion per `(workspace,model)` when there is no natural row to lock.

They do not enforce themselves: code that ignores the advisory protocol proceeds. Key hashing can collide unless mapping is designed; locks are scoped to one database cluster and do not coordinate another database/region. Prefer a unique constraint or locked coordination row when a durable data invariant can express the rule.

### 2.10 Optimistic versus pessimistic concurrency

Optimistic control assumes conflicts are uncommon. Read `version=12`, then update `WHERE version=12`; zero rows triggers conflict handling. It avoids holding locks across application think time but may waste work and needs a user/API conflict story. Pessimistic control locks before decision; it is simpler under high conflict but queues contenders and risks deadlocks.

For a 1% conflict rate and a 20 ms unit of work, optimistic wasted compute from conflicts is roughly 0.2 ms per initial attempt before retry overhead; at 40% it is about 8 ms and creates retry pressure. These are arithmetic illustrations, not database benchmarks. Measure actual collision distribution, especially hot keys.

### 2.11 Constraints, upserts and idempotency

Concurrency-safe correctness should be pushed into constraints where possible. `UNIQUE(tenant_id,idempotency_key)` arbitrates duplicates atomically. `INSERT ... ON CONFLICT` is an upsert primitive, but it does not make arbitrary side effects exactly once. Store request fingerprint and final response/status under the same key; reject reuse with different content; design recovery for `IN_PROGRESS` owners.

Check constraints cover one row, not arbitrary multi-row predicates. Triggers reading other rows can race unless isolation/locks coordinate writers. For money, an immutable double-entry ledger plus unique transfer identity often gives stronger auditability than only mutating balances; derived balances must reconcile to entries.

### 2.12 Observing contention

Use `pg_stat_activity` for sessions/query state and `pg_locks` for active lock objects. PostgreSQL documentation notes row-level locks are stored on disk and usually appear to waiters as waits on the holder's transaction ID, so absence of a tuple row in `pg_locks` is not proof of no row contention. `pg_blocking_pids(pid)` is a direct way to find blockers. Capture wait event, transaction age, query age, application name, sanitized query ID and blocking chain.

Never solve an incident by terminating the apparent blocker without understanding rollback cost and business operation. Prefer cancel where safe, then terminate if policy requires. Diagnose why the transaction is long: remote call inside transaction, pool leak, missing index, oversized batch, or unexpected lock order.

## 3. WORKED PROBLEMS

### Problem 1 — Atomic withdrawal

**Statement.** Balance is ₹100.00 (`10000` paise). Two concurrent requests each withdraw ₹70.00. Prevent a negative balance.

**Solution.** Execute `UPDATE wallet SET balance_minor=balance_minor-7000 WHERE id=? AND balance_minor>=7000 RETURNING balance_minor`. PostgreSQL serializes writers of the row. One changes 10,000 to 3,000. The waiting statement rechecks its condition against the current row and affects zero rows because 3,000 is below 7,000. Map zero rows to insufficient funds/absent account as specified. Add a unique withdrawal idempotency key so a network retry is not a second withdrawal.

**Mistake caught.** `SELECT balance`, application `if`, then unconditional update.

### Problem 2 — Lost profile update

**Statement.** Two clients read profile version 8. One changes phone; one changes address. Each sends the entire record.

**Solution.** Add version to update: `UPDATE profile SET phone=?,address=?,version=9 WHERE id=? AND version=8`. Exactly one succeeds. The other receives conflict, reloads version 9 and explicitly merges/reapplies its field change. HTTP can expose an ETag/`If-Match`. Patch-by-field may avoid overwriting independent columns, but cross-field invariants still require a version/transaction.

**Mistake caught.** Last-write-wins silently deletes a legitimate change.

### Problem 3 — On-call write skew

**Statement.** At least one of Asha/Bimal must be available. Each concurrently takes leave after seeing two available under Repeatable Read.

**Solution.** Because they update disjoint rows, row write conflict does not prevent both commits. Run the decision at Serializable and retry `40001`, or lock one common rota row before reading/updating. Then histories serialize: the second decision observes only one available and refuses leave. A constraint on each doctor's Boolean cannot express the group invariant.

**Mistake caught.** Assuming PostgreSQL Repeatable Read is fully serializable because it prevents phantoms.

### Problem 4 — Transfer deadlock

**Statement.** T1 transfers 1→2 while T2 transfers 2→1, each locking source then destination.

**Solution.** This creates T1 holds 1/waits 2 and T2 holds 2/waits 1. Normalize both operations: sort IDs ascending, acquire `FOR UPDATE` on 1 then 2, then apply logical direction. One waits without a cycle. Still handle `40P01` because other code paths can create cycles, and use a unique transfer key before retrying.

**Mistake caught.** Retrying only the last SQL statement in an aborted transaction.

### Problem 5 — Worker queue

**Statement.** Ten workers claim batches of 20 inference jobs without double-claiming or blocking behind one slow job.

**Solution.** In a short transaction select READY rows ordered by priority/id `FOR UPDATE SKIP LOCKED LIMIT 20`, update them to RUNNING with owner, lease expiry and incremented attempt, return jobs, then commit before inference. Handler records result idempotently. A sweeper requeues expired leases unless attempts exceed policy. This gives at-least-once execution; business effects require deduplication.

**Mistake caught.** Holding database locks during multi-minute model execution.

### Problem 6 — Retry after COMMIT timeout

**Statement.** Client sends COMMIT, connection times out, and cannot tell whether a payment committed.

**Solution.** This is an ambiguous outcome. Do not issue a new unkeyed payment. Query by stable `(tenant,idempotency_key)`; if completed, return stored outcome; if absent, safely attempt creation; if in progress, wait/reconcile according to lease policy. The request hash detects a key reused for different amount/payee. Database rollback cannot resolve a response lost after commit.

**Mistake caught.** Treating every timeout as rollback.

### Problem 7 — Long-running report

**Statement.** A 90-minute analytics transaction runs on the OLTP primary; dead tuples and replica lag grow.

**Solution.** Identify transaction age/snapshot and business owner. Move bounded reporting to a replica/warehouse/export snapshot as correctness permits. Use `SERIALIZABLE READ ONLY DEFERRABLE` when a safe serializable snapshot is required and startup waiting is acceptable. Set statement/idle transaction policy, paginate or materialize, and monitor vacuum horizons. Killing it may cause business impact, so use an incident decision rather than an automatic reflex.

**Mistake caught.** Calling MVCC “nonblocking” and ignoring old-snapshot retention.

### Problem 8 — Online DDL lock queue

**Statement.** A small `ALTER TABLE` waits behind a 20-minute query; new application requests start piling up.

**Solution.** The DDL requests a lock conflicting with the long query and can become a queue head that later requests conflict with. Abort/cancel according to runbook, deploy with a short `lock_timeout`, monitor blockers, and retry in a safe window. Break migration into PostgreSQL-version-appropriate phases. Estimate rewrite/WAL/replica effects separately from lock acquisition.

**Mistake caught.** Equating fast execution after lock acquisition with a harmless migration.

### Problem 9 — Duplicate model promotion

**Statement.** Two controllers promote different model versions to one endpoint; the process spans validation and a database pointer change.

**Solution.** Do remote validation before the critical transaction. Serialize only final choice using a locked endpoint row plus optimistic version, or a transaction-level advisory lock keyed by stable endpoint identity. Under lock, re-read desired/current state, persist versioned promotion/outbox record, commit, then reconcile external deployment idempotently. Advisory lock alone cannot atomically control the external platform.

**Mistake caught.** Holding a session advisory lock across pooled connections and remote work.

## 4. REAL-WORLD / APPLIED CONTEXT

**PostgreSQL SSI.** PostgreSQL has provided Serializable Snapshot Isolation since 9.1. PostgreSQL 18 documents that it adds dependency monitoring to Repeatable Read without additional blocking, aborting transactions that could produce serialization anomalies. Predicate locks appear as `SIReadLock`; they are conflict evidence, not ordinary blocking locks. Production applications must handle SQLSTATE `40001` for the entire transaction.

**Spring/JDBC payment service.** A realistic transfer combines `UNIQUE(tenant_id,idempotency_key)`, atomic guarded debit, credit and outbox insert inside one database transaction. The broker publish occurs later from the outbox. If serialization/deadlock aborts, the Spring transaction is rolled back and the service retries the whole method through the correctly ordered retry/transaction interceptors. Metrics separate attempts from logical requests.

**Kubernetes-style work claiming.** Database-backed dispatchers often use `FOR UPDATE SKIP LOCKED` because independent workers should take other work instead of queueing on a locked first row. The pattern is a claim/lease, not exactly-once processing. A crash after external effect but before result commit causes repetition, so handlers use operation IDs and reconciliation.

Use `concurrency-lab.sql` in two `psql` sessions. It starts with two ₹100 wallets and two available doctors, provides exact interleavings, and includes a blocker query. Record server version, isolation, SQLSTATE and final rows. These are deterministic logical outcomes; wait durations depend on your configuration and timing.

## 5. COMPARISON TABLE

| PostgreSQL 18 isolation | Snapshot scope | Dirty/nonrepeatable/phantom | Serialization anomaly | Application duty |
|---|---|---|---|---|
| Read Uncommitted | same as Read Committed | dirty no; nonrepeatable/phantom possible | possible | atomic statements/locks/versioning |
| Read Committed (default) | each statement | dirty no; others possible | possible | guard each invariant explicitly |
| Repeatable Read | transaction snapshot | none of these in PostgreSQL | possible (write skew) | retry update conflicts; lock/set design |
| Serializable | transaction + SSI dependencies | none | prevented among committed txns | retry whole tx on `40001` |

| Technique | Conflict behavior | Best fit | Main cost/failure |
|---|---|---|---|
| Atomic conditional update | row writers serialize/recheck | counters, inventory, balance guard | limited to expressible one-statement invariant |
| Optimistic version | loser affects zero rows | low contention, user editing | retries/merge UX under conflict |
| `FOR UPDATE` | waits/fails/skips per option | read-decide-write hot entity | blocking, deadlocks, lock duration |
| Serializable SSI | aborts dangerous histories | multi-row/predicate invariants | retry rate and tracking overhead |
| Unique/check/FK constraint | database arbitrates violations | structural invariants | only invariants constraint can express |
| Advisory lock | cooperative application key | coarse singleton coordination | unenforced protocol, key/scope mistakes |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“ACID means business consistency automatically.”** Two valid row updates can violate “one doctor remains”; encode/coordinate the group invariant.
2. **“Repeatable Read equals Serializable.”** PostgreSQL RR prevents phantoms but allows serialization anomalies such as write skew.
3. **“Read Uncommitted gives dirty reads.”** In PostgreSQL it maps to Read Committed.
4. **“MVCC means no blocking.”** Concurrent writers, locks, DDL, unique checks and transaction-ID waits still block.
5. **Reading then setting an absolute value.** Two reads of 10,000 followed by 8,000/7,000 can lose one change; use guarded relative update or version.
6. **Retrying a statement.** After `40001`/`40P01`, prior reads are invalid and transaction is aborted; restart the unit.
7. **Retrying every SQL error.** Unique violation `23505` may be a domain outcome; infinite generic retries amplify incidents.
8. **No retry bound/jitter.** Contenders synchronize into a retry storm. Bound attempts and expose exhaustion.
9. **External call inside transaction.** A 30-second API call holds locks/snapshot/connection; validate before or use outbox/saga.
10. **Locking rows but not predicate invariant.** Each doctor row lock does not protect “count available ≥1” if writers lock disjoint rows.
11. **Inconsistent lock order.** Source-first transfers deadlock in opposite directions; globally sort resource IDs.
12. **Using `SKIP LOCKED` for truth queries.** It omits locked rows by design; use it only for queue-like consumption.
13. **Session advisory locks in a pool.** The next borrower can inherit a leaked lock; prefer transaction scope.
14. **Assuming timeout means failure.** Network failure around commit is ambiguous; reconcile with idempotency identity.
15. **Ignoring long idle transactions.** They retain snapshots/locks and hurt vacuum even while doing no useful work.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- State invariant first; transaction/isolation/lock is the enforcement mechanism.
- PostgreSQL 18: RU=RC; RC snapshot per statement; RR stable snapshot/no phantoms but write skew possible; Serializable aborts unsafe histories.
- `40001` serialization failure and often `40P01` deadlock: rollback and retry whole idempotent transaction.
- Atomic guard: `UPDATE ... WHERE balance>=amount RETURNING ...`.
- Optimistic: `UPDATE ... WHERE id=? AND version=?`; zero rows = conflict.
- Pessimistic: `FOR UPDATE`; acquire multiple resources in stable sorted order.
- Queue: short claim transaction + `SKIP LOCKED` + lease + idempotent processing.
- Constraint beats application check for uniqueness and row-local rules.
- Never hold a transaction over user/remote/model work.
- Observe blocker graph with `pg_blocking_pids`, transaction/query age and wait events.
- Timeouts: lock, statement, idle-in-transaction solve different bounds.
- Commit response loss is ambiguous; reconcile by idempotency key.

## 8. PRACTICE SET FOR SELF-TEST

1. At Read Committed, T1 reads stock 10, T2 subtracts 7 and commits, then T1 subtracts 6 using `SET stock=4`. Name the anomaly and write a safe statement.
2. Explain why two Serializable transactions can be correct even though one returns an error. What must the service do?
3. Design concurrency control for reserving the last three beds across requests that may reserve two beds each.
4. A plan claims `FOR UPDATE SKIP LOCKED` makes job processing exactly once. Refute it with a crash timeline and repair the effects.
5. Give the wait-for graph and prevention for simultaneous transfers 9→3 and 3→9.
6. Choose optimistic or pessimistic control for (a) rarely edited profile, (b) one flash-sale inventory row, with failure handling.
7. A session is `idle in transaction` for 45 minutes. List four database/system harms and a safe response sequence.
8. Design an idempotent retry envelope for SQLSTATE `40001` when publishing an event is required.
9. When is a transaction-level advisory lock reasonable, and what three guarantees does it not provide?
10. Explain how to reproduce write skew using the included lab and the expected result under Repeatable Read versus Serializable.

## 9. CURATED RESOURCES

1. PostgreSQL 18 Manual, [Chapter 13: Concurrency Control](https://www.postgresql.org/docs/current/mvcc.html). Authoritative isolation, locking, consistency and retry behavior for the target database.
2. PostgreSQL 18 Manual, [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html). Exact anomaly table, snapshot semantics, SSI example and SQLSTATE `40001` guidance.
3. PostgreSQL 18 Manual, [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html). Complete table/row lock compatibility, deadlocks and advisory-lock scope.
4. PostgreSQL 18 Manual, [`pg_locks`](https://www.postgresql.org/docs/current/view-pg-locks.html). Exact observability columns and the important transaction-ID representation of row waits.
5. PostgreSQL 18 Manual, [Serialization Failure Handling](https://www.postgresql.org/docs/current/mvcc-serialization-failure-handling.html). Defines whole-transaction retry and relevant SQLSTATE boundaries.
6. Berenson et al., “A Critique of ANSI SQL Isolation Levels,” SIGMOD 1995. Formalizes snapshot-isolation anomalies and terminology beyond the SQL phenomena list.
7. Cahill, Röhm and Fekete, “Serializable Isolation for Snapshot Databases,” SIGMOD 2008. Foundation for detecting dangerous dependency structures under SSI.
8. Ports and Grittner, “Serializable Snapshot Isolation in PostgreSQL,” VLDB 2012. PostgreSQL implementation, predicate locks and practical behavior.
9. Kleppmann, *Designing Data-Intensive Applications*, Chapter 7, “Transactions.” Cross-system models, anomalies and serializability reasoning beyond PostgreSQL syntax.

## 10. RELATED TOPICS BRIDGE

### Before

1. **PostgreSQL Modeling.** Constraints and aggregate boundaries identify the durable invariants transactions protect.
2. **Indexes and Query Plans.** Access paths affect which rows/pages are visited, lock duration and SSI predicate-lock granularity.
3. **Spring Transactions.** Proxy boundaries, rollback rules and connection management determine whether application code creates the intended database unit.

### After

1. **Redis and Caching.** A cache is outside the database transaction, creating stale reads and dual-write failure windows.
2. **Data Migrations.** DDL locks, backfill batches and concurrent writes require transaction-aware rollout.
3. **Messaging and Kafka.** Outbox, idempotent consumers and offset coordination extend workflows beyond one database transaction.
4. **Distributed Consistency.** Once invariants span services, consensus, sagas and reconciliation replace assumptions of one ACID boundary.

---ANSWER KEY BELOW---

1. Lost update/stale overwrite. `UPDATE inventory SET stock=stock-6 WHERE sku=? AND stock>=6 RETURNING stock`; zero rows means insufficient/currently unavailable. Add operation idempotency.
2. Serializable guarantees only successfully committed histories match a serial order; abort is the enforcement mechanism. Roll back, back off with jitter, and rerun the whole transaction from fresh reads using stable idempotency identity.
3. Use one inventory row with atomic `UPDATE bed_inventory SET available=available-2 WHERE date=? AND available>=2 RETURNING`; a multi-date stay needs stable row lock order and one transaction, or Serializable with whole retry. Unique reservation key handles ambiguous retries.
4. Worker claims/commits, performs external effect, crashes before recording success; lease expires and another repeats it. Use stable job/operation ID accepted idempotently by downstream, durable result/dedupe, retries and reconciliation; describe guarantee as at least once.
5. If each locks source first: T1 holds 9 waits 3; T2 holds 3 waits 9, a cycle. Both sort `{3,9}` and lock 3 then 9, then apply directional updates; still retry deadlock safely.
6. Profile: optimistic version and conflict/merge UX because collisions rare and think time long. Flash row: atomic guarded decrement is best; pessimistic short lock if decision is more complex. Both need idempotency and bounded conflict behavior.
7. Retains old snapshot/dead tuples, delays vacuum/freeze, holds locks, consumes connection and can grow tables/indexes/replica pressure. Identify owner/query/blockers, assess rollback/business impact, cancel/terminate per runbook, fix boundary/pool leak and configure monitored timeout.
8. Transaction includes business rows plus outbox row under stable operation key; on `40001`, rollback and retry the entire unit with backoff/jitter. Publisher later sends outbox at least once; consumer dedupes event ID. Never publish inside the retried transaction before commit.
9. Reasonable for cooperative singleton work with no natural row, e.g. one promotion per endpoint. It does not constrain nonparticipants, span clusters, or atomically include remote side effects; it also does not provide durable ownership after session/transaction ends.
10. Begin two RR transactions, each counts two available, update a different doctor false, then commit; both may commit and count becomes zero. Reset and repeat Serializable; PostgreSQL aborts one with `40001`, and retry observes the remaining doctor so policy refuses the second leave.
