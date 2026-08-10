# Indexes and Query Plans

**Parent:** 03 — Data Systems  
**Target depth:** senior backend / AI-platform / MLOps engineer  
**Study time:** 3–4 hours plus the executable lab

## 1. FOUNDATIONS

A database query describes the result, not the physical route to it. For `SELECT * FROM payment WHERE tenant_id=42`, PostgreSQL may read every table page, walk an index, combine indexes into a bitmap, or exploit a partition. The **planner** enumerates plausible plan trees and estimates each tree's cost; the **executor** runs the chosen tree. This separation is why declarative SQL is productive—and why performance surprises occur when the planner's model differs from reality.

Without an index, locating 50 qualifying rows in 100 million rows normally means examining the whole relation: an order-of-growth of O(n). An **index** is a separately maintained access structure mapping search keys toward table tuples. A balanced B-tree search is roughly O(log n + k), where `k` is the result size, but this notation hides page reads, cache residency, tuple visibility, correlation and random I/O. An index is therefore not “free speed”: every insert/update/delete may modify it, it occupies storage, can bloat, and gives the optimizer another alternative to cost.

PostgreSQL stores table rows in a **heap** (not the heap data structure): pages with no inherent key ordering. A row version is a **tuple**. An index entry normally contains key values and a tuple identifier pointing to a heap location. Under PostgreSQL's MVCC model, index entries do not by themselves generally prove that the referenced version is visible to the current snapshot. An **index-only scan** can avoid heap access only when the index contains every required column and the visibility map says the heap page is all-visible; `Heap Fetches` reveals exceptions.

The planner works in **cost units**, not milliseconds. `seq_page_cost`, `random_page_cost`, CPU costs and estimated cardinalities feed formulas. **Cardinality** means row count; **selectivity** is the fraction surviving a predicate. If 10,000 rows survive from one million, selectivity is 0.01. Estimates come from table statistics: null fraction, number of distinct values, most-common values, histograms and physical correlation. `ANALYZE` samples data to refresh them. Stale or independence-assuming statistics can make a logically valid but disastrous plan look cheapest.

Plans are trees. Leaves access rows; parents filter, sort, aggregate or join. Read from the most deeply indented node outward. `cost=startup..total rows=... width=...` is prediction. With `ANALYZE`, `actual time=start..end rows=... loops=...` is measurement. Actual rows/time are averages per loop, so multiply by `loops` when reasoning about total repeated work. `Buffers: shared hit` means a requested block was already in PostgreSQL's buffer cache; `read` means the server requested it from the operating system. Neither alone proves physical disk latency.

Historically, database indexes descend from ordered file structures and B-trees developed for block storage. Bayer and McCreight's 1972 B-tree keeps height small by storing many keys per node. PostgreSQL adds specialized access methods because “nearby” differs by data: equality/range ordering (B-tree), inverted membership (GIN), geometric/operator families (GiST/SP-GiST), equality hashing, and block summaries for physically correlated massive tables (BRIN). The correct question is not “which index is fastest?” but “which operator, distribution, ordering and maintenance budget define this workload?”

## 2. CORE MECHANICS

### 2.1 Establish a safe baseline

Use `EXPLAIN` to predict without executing. Use `EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS)` to execute and measure. `ANALYZE` really runs data-changing statements; wrap experimental DML in `BEGIN; ... ROLLBACK;`. Compare identical SQL, parameters, data, configuration and cache state. PostgreSQL's own documentation warns that measured timings omit client network/output work and include instrumentation overhead.

Suppose a node shows `rows=100` estimated and `actual rows=12000 loops=1`. The error factor is `max(12000/100,100/12000)=120×`; investigate statistics before forcing a plan. If an inner node says `actual rows=3 loops=10000`, it emitted about 30,000 rows total, not three. The supplied `PlanMath.java` makes both calculations executable.

### 2.2 Sequential, index and bitmap scans

A **sequential scan** walks table pages and filters tuples. It is correct for any predicate and often cheapest when a large fraction is needed or the table is tiny. An **index scan** walks an index in key order and visits heap tuples; it shines for selective queries and can satisfy `ORDER BY`. A **bitmap index scan** builds a bitmap of candidate heap locations, then a bitmap heap scan visits heap pages in physical order. It amortizes heap access when thousands of scattered rows qualify. Multiple bitmaps can use `BitmapAnd` or `BitmapOr`.

For one million 8 KB pages, a full scan requests roughly 7.6 GiB. If an index identifies 40 rows on 35 heap pages, it may touch a few index pages plus 35 heap pages. If 600,000 rows qualify across nearly all pages, index navigation adds work, so a sequential scan is sensible. These are illustrative page counts, not latency claims.

### 2.3 B-tree and column order

B-tree supports equality, inequalities, ranges, ordered output, prefix searches such as `LIKE 'abc%'` under suitable collation/operator class, and min/max traversal. For `(tenant_id, account_id, created_at DESC)`, equality on the leading columns plus a range/order on time is ideal:

```sql
SELECT id, amount_minor
FROM payment
WHERE tenant_id=42 AND account_id=4242
ORDER BY created_at DESC LIMIT 50;
```

Column order follows access patterns, not a universal “most selective first” rule. With B-tree, equality-constrained leading columns followed by range/order columns usually bound the scan. PostgreSQL 18 can use skip scan in suitable distributions, but do not treat it as permission to ignore leading-column design. Boundary cases: a query on only `account_id` may not efficiently use this index; `ORDER BY created_at ASC` can scan backward when all ordering directions reverse, but mixed direction requirements may need explicit definitions.

### 2.4 Covering and index-only scans

`INCLUDE` stores payload columns without making them search keys:

```sql
CREATE INDEX payment_lookup
ON payment(tenant_id, account_id, created_at DESC)
INCLUDE (amount_minor, status);
```

This can cover a read returning those fields. It also enlarges entries, reduces fan-out, increases write amplification, and may exceed tuple-size limits. Even a covering index can show heap fetches when pages are not all-visible—common on frequently updated tables. Vacuum maintains the visibility map, so “index-only” depends on write behavior and maintenance.

### 2.5 Partial, expression and unique indexes

A **partial index** contains only rows satisfying a predicate:

```sql
CREATE INDEX payment_pending ON payment(tenant_id, created_at)
WHERE status='PENDING';
```

If 5% of 100 million payments are pending, it indexes about five million rather than 100 million entries. The query predicate must logically imply the index predicate at planning time; a generic parameterized `status=$1` may fail that proof. Partial unique indexes implement conditional invariants, such as one live username.

An **expression index** materializes a computed key, e.g. `CREATE UNIQUE INDEX ... ON users(tenant_id, lower(email));`. The query must use a matching expression, and indexed functions must be immutable. A unique index is both access path and concurrency-safe constraint; an application-side “check then insert” is racy.

### 2.6 GIN, GiST, SP-GiST, hash and BRIN

**GIN** is an inverted index: one document/array produces entries for contained tokens or keys. It fits `jsonb @>`, arrays and full-text search, but writes may be heavier and it cannot perform ordinary B-tree ordering. `jsonb_ops` supports more operators; `jsonb_path_ops` is smaller/specialized mainly for containment and jsonpath matching.

**GiST** is a framework for balanced search trees over operator-defined approximations, used for geometric, range, nearest-neighbor and extension types. Results may be **lossy**, requiring heap rechecks. **SP-GiST** partitions non-balanced spaces such as tries or quadtrees. **Hash** supports equality only. **BRIN** stores summaries for page ranges; it is tiny and effective when values such as append-time correlate with physical order, but returns candidate ranges for recheck. A one-billion-row append-only event table can make BRIN attractive; a randomly distributed tenant key usually does not.

### 2.7 Selectivity and statistics

If `status` has 90% `SETTLED`, 5% `PENDING`, 5% `FAILED`, assuming uniformity would predict 333,333 of one million for each. A most-common-values list corrects this. Histograms approximate ranges between sampled boundaries. `n_distinct` supports equality estimates. Increase a column's statistics target when important skew is missed, accepting more planning/catalog/analyze work.

Single-column statistics often assume predicates are independent. If each account belongs to exactly one tenant, `tenant_id=42 AND account_id=4242` is correlated. Multiplying individual selectivities can severely under-estimate. `CREATE STATISTICS s (dependencies, ndistinct, mcv) ON tenant_id,account_id FROM payment; ANALYZE payment;` lets PostgreSQL model relationships. Extended statistics improve estimates; they are not access structures.

### 2.8 Join algorithms

A **nested loop** takes each outer row and probes/scans the inner side. With 50 outer rows and an indexed unique lookup, about 50 cheap probes is excellent. With 100,000 outer rows and an unindexed 10-million-row inner scan, it is catastrophic. `loops` exposes repetition.

A **hash join** builds an in-memory hash table from one input then probes with the other; it suits equality joins and substantial unsorted inputs. If memory is insufficient, `Batches > 1` indicates spill partitioning. A **merge join** consumes both sides in join-key order; it handles equality and some inequalities and can exploit existing ordering. Sorting may dominate if neither input is ordered.

### 2.9 Sorts, aggregation and memory

Plan Sort nodes report algorithm and `Memory` or `Disk`. A disk-backed external merge signals the operation exceeded its effective `work_mem`; blindly increasing global `work_mem` is dangerous because it applies per operation, potentially multiple times per query and session. `HashAggregate` similarly may batch/spill. Prefer reducing rows early, useful index ordering, and session-level testing before configuration changes.

### 2.10 Pagination and sargability

Offset pagination must find/discard preceding rows and can shift under concurrent writes. Keyset pagination uses the ordered key:

```sql
WHERE (created_at,id) < (:cursor_time,:cursor_id)
ORDER BY created_at DESC,id DESC LIMIT 50
```

The unique tie-breaker prevents omissions among equal timestamps. A predicate is **sargable** when an access method can use it to bound a search. `WHERE created_at::date='2025-06-01'` commonly blocks a plain timestamp index; rewrite as `created_at >= ... AND created_at < ...`, or intentionally add a matching expression index. Avoid implicit casts on indexed columns.

### 2.11 Lifecycle and production operation

Indexes can bloat as MVCC versions churn. Autovacuum, fillfactor, update patterns and HOT updates matter. `CREATE INDEX CONCURRENTLY` reduces blocking of writes but takes more work/time and cannot run inside a transaction block; failed builds can leave invalid indexes. Inspect `pg_stat_user_indexes`, but zero scans does not automatically mean safe deletion: an index may enforce uniqueness, support rare critical jobs, or statistics may have reset. Capture representative workload evidence and rollback strategy.

## 3. WORKED PROBLEMS

### Problem 1 — Diagnose a 120× estimate error

**Statement.** A scan estimates 100 rows but returns 12,000 once. What does that mean and what should you do?

**Solution.** (1) Calculate `max(12000/100,100/12000)=120×`. (2) Confirm `loops=1`; otherwise multiply actual rows by loops for total work but compare per-loop estimates consistently. (3) Run `ANALYZE`; inspect `pg_stats` for skew. (4) If predicates are correlated, create extended MCV/dependency statistics. (5) Re-run the same parameters. Only then reconsider indexes/query shape. An estimate error is evidence about the model, not proof a specific index is missing.

**Trap.** Comparing cost units with milliseconds or immediately disabling a join type.

### Problem 2 — Design a feed index

**Statement.** Fetch the newest 50 payments for one tenant and account from 200 million rows, returning amount and status.

**Solution.** The predicates have equality on tenant/account and descending time order. Build `(tenant_id,account_id,created_at DESC) INCLUDE (amount_minor,status)`. Add `id DESC` if timestamps tie and pagination needs total order. Query with the same ordering and a composite keyset cursor. This bounds one key range and stops after 50; INCLUDE may enable index-only scans on all-visible pages.

**Trap.** Indexing only `created_at` or assuming INCLUDE guarantees zero heap fetches.

### Problem 3 — Explain a sequential scan despite an index

**Statement.** `status='SETTLED'` matches 900,000 of one million rows; a status B-tree exists, but PostgreSQL scans sequentially.

**Solution.** Nearly every heap page will be visited. An index scan would additionally traverse index pages and make heap visits, often less sequentially. The planner rationally chooses the full scan. If the workload wants pending rows (5%), use a partial pending index; do not force the settled query through the index.

**Trap.** Treating “Seq Scan” as inherently bad.

### Problem 4 — Fix correlated selectivity

**Statement.** Each account ID belongs to one tenant. The planner treats `tenant_id=42 AND account_id=4242` independently and underestimates rows.

**Solution.** Refresh statistics, then create `CREATE STATISTICS payment_tenant_account (dependencies, ndistinct, mcv) ON tenant_id,account_id FROM payment;` and `ANALYZE payment;`. Dependencies model that account predicts tenant; MCV captures common pairs; ndistinct helps grouped cardinality. Keep the composite B-tree separately because statistics do not retrieve rows.

**Trap.** Believing extended statistics replace an index.

### Problem 5 — Read nested-loop totals

**Statement.** An inner index scan reports `actual rows=3 loops=10000` and 0.020 ms end time.

**Solution.** Values are average per execution. It emitted roughly `3×10000=30000` rows and spent about `0.020×10000=200 ms` inside that node (subject to plan timing accounting). Determine why 10,000 probes occur and whether outer cardinality was expected. A hash join may help only after considering result size, memory and ordering.

**Trap.** Reporting three rows and 0.020 ms total.

### Problem 6 — Repair a non-sargable date query

**Statement.** An index exists on `created_at`, but `created_at::date = DATE '2025-06-01'` scans the table.

**Solution.** Use a half-open UTC range: `created_at >= TIMESTAMPTZ '2025-06-01 00:00:00+00' AND created_at < TIMESTAMPTZ '2025-06-02 00:00:00+00'`. The B-tree can navigate to the lower bound and stop at the upper. For business-local dates, compute correct UTC boundaries using the intended IANA zone; days around DST need not be 24 hours.

**Trap.** Using `BETWEEN` through midnight of the next day, double-counting the boundary.

### Problem 7 — Choose JSONB indexing

**Statement.** Metadata contains channel and provider payload. Queries use `metadata @> '{"channel":"mobile"}'`; no ordering by JSON fields is needed.

**Solution.** Validate with the actual operator and workload, then consider `GIN(metadata jsonb_path_ops)`. It is specialized for containment/jsonpath and often smaller than default `jsonb_ops`, but supports fewer operators. If channel is required, frequently filtered and governed, promote it to a typed column with B-tree instead of hiding core schema in JSON.

**Trap.** Creating a B-tree on the whole JSONB value and expecting containment support.

### Problem 8 — Select an index for a billion append-only events

**Statement.** Events are physically appended in occurred-time order; queries scan week-long time ranges, retention is time-based.

**Solution.** Consider partitioning by time and a BRIN on `occurred_at` per large partition. BRIN summarizes ranges of heap pages and stays tiny; correlation makes range summaries selective. Test `pages_per_range` against scan false positives. If queries fetch a handful of exact timestamps or need order/limit, B-tree may still be needed.

**Trap.** Using BRIN for randomly scattered tenant IDs because the table is large.

### Problem 9 — Safe production index rollout

**Statement.** Add an index to a write-heavy 800 GB table with a strict availability objective.

**Solution.** Confirm query and cardinality evidence; estimate extra disk and replica/WAL impact; create with `CONCURRENTLY` outside a transaction; monitor phase/progress, lock waits, replication lag and disk; detect invalid remnants on failure; `ANALYZE`; compare plans over representative parameters; retain a drop/rollback plan. Roll out query use gradually. Concurrent creation reduces write blocking, not resource consumption.

**Trap.** Running ordinary `CREATE INDEX` during peak load or assuming concurrent means harmless.

## 4. REAL-WORLD / APPLIED CONTEXT

**Payment history API.** `index-lab.sql` generates exactly 1,000,000 deterministic rows: 100 tenants, 10,000 accounts and a 90/5/5 status split. Run the baseline and indexed plans locally. Report your PostgreSQL version, hardware/container limits, cold/warm state, plan, buffers and row-estimate error; do not copy a time from another machine as a promise.

**PostgreSQL's documented regression example.** PostgreSQL 18 documentation shows a 10,000-row join where a bitmap scan feeds a hash join, with 100 joined rows and 440 shared-buffer hits in that documented run. It explicitly says estimates/timings can vary because statistics sampling and costs are platform-dependent. The important transferable evidence is the node structure, rows/loops semantics and buffer accounting—not the 3.036 ms shown on its environment.

**Observability workload.** Time-ordered logs commonly combine partition pruning, BRIN for broad time ranges, B-tree `(service_id,occurred_at DESC)` for service feeds, and GIN/full-text facilities for token search. One giant GIN over every arbitrary label can create expensive writes; mature platforms bound label cardinality, distinguish governed columns from optional attributes, and test retention/index-build behavior on production-scale distributions.

## 5. COMPARISON TABLE

| Approach | Operators/access | Storage/write trade-off | Use when | Avoid when |
|---|---|---|---|---|
| Sequential scan | Any filter; reads relation | No extra index writes | large fraction or tiny table | selective latency query on huge table |
| B-tree | equality, range, order, prefix | ordered entries; each write maintained | OLTP keys, range + LIMIT | containment/token membership |
| Hash | equality | separate hash structure | equality-only measured niche | ranges/order; B-tree already adequate |
| GIN | membership, JSONB, arrays, text | many entries/document; write-heavy | containment/search | frequent updates or ordered output |
| GiST | operator-class dependent, KNN/ranges | may be lossy/recheck | geometry, ranges, extensions | ordinary scalar equality/range better served by B-tree |
| SP-GiST | partitioned search spaces | operator-class dependent | tries, quadtrees, non-balanced spaces | unsupported operator/type |
| BRIN | block-range summaries | extremely compact; false positives | huge physically correlated tables | random distribution/exact point lookup |
| Partial B-tree | same as B-tree within predicate | smaller, less write work outside predicate | rare stable subset, conditional uniqueness | generic predicates planner cannot imply |
| Covering B-tree | B-tree plus returned payload | larger entries/lower fan-out | stable read-heavy table, few payload fields | hot updates/wide columns |

| Join | Best shape | Memory/order need | Failure mode |
|---|---|---|---|
| Nested loop | small outer + cheap indexed inner | little | repeated large inner work |
| Hash join | large equality join | hash table; may batch/spill | skew, memory pressure, no inequality |
| Merge join | ordered inputs | sorts unless already ordered | sort cost; unsuitable operator |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Every query needs an index.”** Indexing a 90%-selective status query may add writes without improving its scan. Index the workload, not every column.
2. **“Most selective column always goes first.”** `(tenant,account,time)` reflects equality scope and ordering; isolated selectivity is not a full access pattern.
3. **“Cost is milliseconds.”** `cost=100` is a planner unit. Compare alternatives inside the same cost model; measure actual time separately.
4. **Ignoring loops.** Three rows over 10,000 loops means about 30,000 emissions.
5. **Trusting a single warm run.** Cache, checkpoints, autovacuum and concurrent load change observations. Record controlled repetitions and percentiles at the service boundary.
6. **Forcing index scans.** `enable_seqscan=off` is a diagnostic experiment, not the normal fix. Repair estimates, schema or query.
7. **Assuming index-only means heap-free.** A covering index on a write-hot table can make many heap visibility checks.
8. **Making a huge INCLUDE list.** Wider indexes reduce fan-out and magnify I/O/write cost. Return only justified payload.
9. **Function-wrapping indexed columns.** `lower(email)` or `created_at::date` requires matching expression design or a sargable rewrite.
10. **Missing tie-breakers.** Time-only pagination loses/duplicates rows with identical timestamps; order by `(time,id)`.
11. **Using offset at deep pages.** `OFFSET 1000000` still discovers/discards a million rows and is unstable under writes.
12. **Adding `work_mem` globally.** Many concurrent sorts/hash operations multiply memory use. Test per session and reduce data first.
13. **Dropping zero-scan indexes blindly.** Statistics reset; unique indexes enforce correctness; rare incident paths matter.
14. **Benchmarking toy uniform data.** Production skew/correlation drives plan choice. The included lab deliberately has skew but must still be adapted to actual distributions.
15. **Running `EXPLAIN ANALYZE UPDATE` casually.** It executes the update. Use a transaction and rollback for experiments.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Read plans deepest node outward; prediction: `cost/rows/width`; measurement: `actual/rows/loops`.
- Estimate error factor: `max(actual/estimate, estimate/actual)`; investigate repeated large errors.
- Multiply per-loop actual rows/time by loops to understand repetition.
- B-tree: equality/range/order. GIN: membership. GiST/SP-GiST: operator-defined spaces. BRIN: correlated block ranges.
- Composite B-tree: equality prefix, then range/order; validate skip-scan behavior rather than relying on it.
- `INCLUDE` covers output but visibility may still require heap fetches.
- Partial index queries must imply the predicate.
- `ANALYZE` updates statistics; extended statistics model cross-column relationships.
- Seq scan is reasonable for large selectivity; bitmap is middle ground; index scan for selective/order-sensitive reads.
- Nested loop: small outer. Hash: equality/bulk. Merge: ordered inputs.
- `EXPLAIN ANALYZE` executes; rollback experimental DML.
- Pagination: unique composite keyset cursor, same comparison and order.

## 8. PRACTICE SET FOR SELF-TEST

1. A node estimates 8 rows and reports `actual rows=2,400 loops=5`. Calculate per-loop estimate error and total emitted rows. Name two likely investigation paths.
2. Design one index for `WHERE tenant_id=? AND status=? AND created_at>=? ORDER BY created_at DESC LIMIT 100`; status has three values and all are queried. Explain column order.
3. A covering scan reports 80,000 heap fetches after heavy updates. Explain why and propose operational checks.
4. Choose between B-tree, GIN and BRIN for: exact device ID; JSONB containment; month range over append-ordered telemetry.
5. Rewrite `WHERE lower(email)=lower(?)` safely for case-insensitive uniqueness and lookup. State one Unicode/canonicalization risk.
6. An equality join builds a 12 GB hash with 32 batches under a 256 MB memory budget. Give three remedies or investigations without globally raising memory.
7. Design stable descending pagination where 5,000 events can share one millisecond.
8. Explain why a prepared statement with `status=$1` might not use `WHERE status='PENDING'` partial index.
9. Give a safe measurement protocol for testing an index on a 500-million-row production-like table.
10. Decide whether to drop an index whose `idx_scan` is zero and list evidence required.

## 9. CURATED RESOURCES

1. PostgreSQL 18 Manual, [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html). Canonical semantics for plan trees, rows/loops, buffers, timing caveats and side effects.
2. PostgreSQL 18 Manual, [CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html). Exact syntax, access methods, INCLUDE, predicates, storage parameters and concurrent builds.
3. PostgreSQL 18 Manual, Chapter 11: [Indexes](https://www.postgresql.org/docs/current/indexes.html). Primary treatment of index types, multicolumn, expression, partial and index-only behavior.
4. PostgreSQL 18 Manual, [Statistics Used by the Planner](https://www.postgresql.org/docs/current/planner-stats.html). Catalog statistics, target control and extended-statistics motivation.
5. PostgreSQL 18 Manual, [How the Planner Uses Statistics](https://www.postgresql.org/docs/current/planner-stats-details.html). Worked row-estimation mathematics and multivariate examples beyond this lesson.
6. PostgreSQL 18 Manual, [Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html). Connects MVCC cleanup, visibility maps, ANALYZE and index-only behavior.
7. Bayer and McCreight, “Organization and Maintenance of Large Ordered Indices,” *Acta Informatica* 1 (1972). Original B-tree motivation and invariants.
8. Goetz Graefe, “Modern B-Tree Techniques,” *Foundations and Trends in Databases* 3(4), 2011. Deep survey of implementation techniques and trade-offs.
9. Markus Winand, *SQL Performance Explained*, chapters 1–3. Practical access paths and composite-index reasoning across SQL databases; contrast vendor details with PostgreSQL docs.

## 10. RELATED TOPICS BRIDGE

### Before

1. **PostgreSQL Modeling.** Keys, constraints, types and workload-shaped schemas define what indexes can enforce and retrieve.
2. **Complexity Analysis.** Growth models help reason about scans and trees, while database costs add storage hierarchy and selectivity.
3. **Trees/Heaps/Tries.** Balanced-tree invariants make B-tree height and ordered traversal intuitive.

### After

1. **Transactions and Locking.** MVCC visibility, locks and isolation explain heap versions, concurrent index changes and correctness.
2. **Redis and Caching.** Optimize the authoritative query before adding a derived copy and invalidation problem.
3. **Data Migrations.** Online index creation and schema evolution require lock, WAL, disk and rollback planning.
4. **Observability.** Service percentiles, traces, query IDs and database statistics connect a plan to user-visible latency.

---ANSWER KEY BELOW---

1. Per-loop factor `2400/8=300×`; total rows `2400×5=12000`. Refresh/inspect statistics and correlation/skew; inspect predicate types/parameters and plan children.
2. `(tenant_id,status,created_at DESC)` because two equalities bound the leading prefix and time bounds/orders the remainder. Add tie-breaker `id DESC`; INCLUDE only justified outputs. Low status cardinality does not by itself make it unusable after tenant equality.
3. MVCC visibility is not derivable from index entries for pages not marked all-visible. Check autovacuum/vacuum progress and settings, dead tuples/update rate, visibility map coverage, long transactions and whether index width is still worthwhile.
4. Device ID B-tree; JSONB containment GIN with operator class chosen from operators; append-correlated month ranges BRIN (often with time partitions), validated against false-positive page ranges.
5. Use a documented canonical value column or unique expression index on an immutable canonicalizer and query the exact same expression. Lowercasing alone may mishandle Unicode, locale, normalization or provider-specific email semantics.
6. Reduce/filter/project build input; improve estimates/statistics and join order; add an access path enabling a selective nested loop or useful ordering/merge; partition/preaggregate; test bounded session `work_mem`. Confirm skew and concurrent memory before configuration changes.
7. `ORDER BY occurred_at DESC,id DESC`; next predicate `(occurred_at,id)<(:time,:id)`. Encode both in an opaque cursor and use snapshot/product semantics appropriate to concurrent inserts.
8. At generic-plan time PostgreSQL cannot prove an unknown parameter equals the literal partial-index predicate for every execution. Use query shapes/plans intentionally and validate custom versus generic planning; do not concatenate unsafe SQL.
9. Clone representative scale/distribution and configuration; baseline identical parameter sets; capture plan/rows/loops/buffers/WAL and service latency; repeat cold/warm with concurrency; size disk/WAL/replica impact; build concurrently with monitoring; analyze; canary and retain rollback.
10. Do not decide from zero alone. Check statistics reset time, primary/replicas, query logs and seasonal/jobs/incidents; determine whether it backs UNIQUE/PK; measure size/write cost and overlapping indexes; get owner review and a reversible monitored removal procedure.
