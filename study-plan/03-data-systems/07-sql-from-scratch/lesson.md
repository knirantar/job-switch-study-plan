# SQL from Scratch: Queries, Joins, Aggregation, and Safe Changes

Parent subject: `03-data-systems`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### What SQL is trying to solve

SQL is a **declarative** language for relational data. You describe the result you want—paid claims per tenant, patients without active consent, the latest model deployment per endpoint—and the database chooses an execution strategy. In an imperative loop, you specify iteration and lookup mechanics yourself. SQL separates the logical question from physical execution, allowing an optimizer to choose indexes, join order, parallelism, and algorithms as statistics and storage change.

IBM researchers developed SEQUEL while implementing ideas from Codd's relational model; it evolved into SQL and became standardized. Its enduring value is not syntax convenience. A precise data question can be expressed as algebraic operations and evaluated close to the data, with transactions and permissions. Without this layer, each application reimplements filtering, joining, grouping, concurrency, and integrity inconsistently.

SQL is not one perfectly uniform language. ISO standards define a core, while PostgreSQL, MySQL, SQL Server, Oracle, and SQLite add dialects and differ in types, null handling at edges, date functions, upserts, identity generation, and administrative commands. Learn the relational ideas first and verify dialect-specific behavior in official documentation.

### Tables, rows, columns, and result sets

A query reads one or more input relations and produces a **result set** with rows and columns. The result is conceptually unordered unless an `ORDER BY` is present. Physical insertion order, primary-key order, or yesterday's observed output is not a contract.

SQL commonly operates as a **bag** or multiset language: duplicate rows can appear. `SELECT` preserves duplicates; `SELECT DISTINCT` removes duplicate projected rows. This differs from pure relational theory's set semantics and matters for joins and counts.

### Query clauses and logical processing order

A basic query is written:

```sql
SELECT tenant_id, COUNT(*) AS paid_claims
FROM claim
WHERE status = 'PAID'
GROUP BY tenant_id
HAVING COUNT(*) >= 2
ORDER BY paid_claims DESC, tenant_id
LIMIT 20;
```

Its useful conceptual evaluation order is `FROM`/`JOIN`, `WHERE`, `GROUP BY`, `HAVING`, `SELECT`, `DISTINCT`, `ORDER BY`, then `LIMIT/OFFSET`. Optimizers may transform execution while preserving semantics. This order explains why a select-list alias is often unavailable in `WHERE`: the projection has not logically occurred.

### Expressions, predicates, and null

An expression returns a value. A predicate is a condition used for filtering or joining. Comparison operators include `=`, `<>`, `<`, `<=`, `>`, and `>=`. `BETWEEN` is inclusive at both ends; this is often dangerous for timestamps, where half-open ranges are clearer.

SQL uses three-valued logic: true, false, and unknown. Comparisons involving null generally produce unknown. `WHERE` retains true only. Use `IS NULL` and `IS NOT NULL`. `COUNT(column)` counts non-null values, while `COUNT(*)` counts rows. `NOT IN` can surprise when its subquery includes null; `NOT EXISTS` is usually a safer anti-join expression.

### Selection, projection, and joins

**Selection** filters rows; **projection** chooses/computes columns. A **join** combines rows satisfying a relationship. An inner join retains matching pairs. A left outer join retains all left rows and supplies nulls for unmatched right-side columns. Cross join produces every pair.

If one patient has three claims, joining patient to claim produces three rows for that patient. Joins do not merely “add columns”; cardinality multiplies according to matching rows. Incorrect join predicates can create a Cartesian explosion and corrupt aggregates.

### Aggregation and grouping

Aggregate functions summarize a group: `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX`. `GROUP BY` creates groups based on key values. Every selected expression must be grouped, aggregated, or otherwise functionally permitted by the DBMS. `WHERE` filters input rows before grouping; `HAVING` filters groups after aggregation.

An average of averages is generally wrong when group sizes differ. Combine sums and counts or aggregate raw rows. If hospital A has average 100 ms across 1,000 requests and B averages 500 ms across 10 requests, `(100+500)/2=300` is wrong; combined mean is `(100×1000+500×10)/1010≈103.96 ms`.

### Subqueries, CTEs, and windows

A **subquery** is a query nested in another statement. It may be scalar, set-valued, or correlated with an outer row. A **common table expression** (CTE), introduced with `WITH`, names a query result for readability or recursion. It is not automatically a performance improvement; materialization/inlining behavior is database/version dependent.

A **window function** computes across related rows without collapsing them into one row per group. `ROW_NUMBER`, `RANK`, running `SUM`, and `LAG` support latest-row selection, rankings, cumulative values, and change detection. `PARTITION BY` creates independent windows; `ORDER BY` defines sequence; a frame defines which neighboring rows participate.

### Data-changing statements

`INSERT` creates rows, `UPDATE` changes rows, and `DELETE` removes rows. They are powerful set operations. Omitting `WHERE` from `UPDATE` or `DELETE` affects every row. A production-safe workflow previews the predicate with `SELECT`, runs within a transaction where appropriate, checks affected-row counts, and preserves audit/recovery requirements.

SQL injection occurs when untrusted input changes statement structure. Parameterized queries send values separately from SQL syntax. Escaping by hand is not a sound general defense. Parameters cannot replace arbitrary identifiers such as sort-column names; allow-list those and construct only trusted fragments.

## 2. CORE MECHANICS

The executable lab uses tenants, patients, and claims with real minor-unit amounts and timestamps.

### 2.1 SELECT and aliases

```sql
SELECT claim_id,
       amount_paise,
       amount_paise / 100.0 AS amount_rupees
FROM claim;
```

Projection can rename output with `AS` and compute values. Preserve integer minor units as the stored truth; converting to display currency is presentation. Avoid `SELECT *` in stable application contracts because new columns change payloads, increase I/O, and can expose sensitive fields.

### 2.2 Filtering precisely

```sql
SELECT claim_id, status, created_at
FROM claim
WHERE tenant_id = 'T1'
  AND status IN ('APPROVED', 'PAID')
  AND created_at >= '2026-08-01T00:00:00Z'
  AND created_at <  '2026-09-01T00:00:00Z';
```

The half-open interval includes every August instant regardless of fractional precision and composes without overlap. `BETWEEN start AND '2026-08-31 23:59:59'` misses higher-precision values and embeds calendar assumptions.

`LIKE 'CLM-%'` matches a prefix; `_` matches one character and `%` any sequence. Case sensitivity is dialect/collation specific. Search semantics need an explicit normalization/collation design.

### 2.3 Sorting and limiting

```sql
SELECT claim_id, amount_paise, created_at
FROM claim
ORDER BY amount_paise DESC, created_at ASC, claim_id ASC
LIMIT 3;
```

Tie-break with a unique column for deterministic output. `LIMIT` without order means arbitrary rows. Large `OFFSET` pagination may scan/discard many rows and shifts under concurrent inserts. Keyset pagination uses the last ordered key tuple.

### 2.4 Inner and outer joins

```sql
SELECT p.patient_id, p.display_name, c.claim_id, c.status
FROM patient AS p
JOIN claim AS c
  ON c.tenant_id = p.tenant_id
 AND c.patient_id = p.patient_id
WHERE p.tenant_id = 'T1';
```

Both tenant and patient ID belong in the predicate because identity is tenant-scoped. To find patients with no claims:

```sql
SELECT p.patient_id
FROM patient p
LEFT JOIN claim c
  ON c.tenant_id=p.tenant_id AND c.patient_id=p.patient_id
WHERE c.claim_id IS NULL;
```

Putting `c.status='PAID'` in `WHERE` after a left join rejects null-extended rows and effectively makes it inner. Put right-side match restrictions in `ON` when unmatched left rows must remain.

### 2.5 Aggregates and conditional aggregation

```sql
SELECT tenant_id,
       COUNT(*) AS total,
       SUM(CASE WHEN status='PAID' THEN 1 ELSE 0 END) AS paid,
       SUM(CASE WHEN status='PAID' THEN amount_paise ELSE 0 END) AS paid_paise
FROM claim
GROUP BY tenant_id
HAVING COUNT(*) >= 2;
```

This returns one row per tenant. In PostgreSQL, `COUNT(*) FILTER (WHERE status='PAID')` is clearer. Be deliberate about null: `SUM` over no rows returns null, while a `CASE ... ELSE 0` within an existing group yields zero.

### 2.6 EXISTS and anti-joins

```sql
SELECT p.patient_id
FROM patient p
WHERE EXISTS (
  SELECT 1 FROM claim c
  WHERE c.tenant_id=p.tenant_id
    AND c.patient_id=p.patient_id
    AND c.status='PAID'
);
```

`EXISTS` expresses existence without multiplying patient rows by every matching claim. For “no paid claim,” use `NOT EXISTS`. The `SELECT 1` value is conventional; existence is what matters.

### 2.7 CTEs

```sql
WITH paid_by_patient AS (
  SELECT tenant_id, patient_id, SUM(amount_paise) AS paid_paise
  FROM claim WHERE status='PAID'
  GROUP BY tenant_id, patient_id
)
SELECT p.display_name, x.paid_paise
FROM paid_by_patient x
JOIN patient p USING (tenant_id, patient_id)
WHERE x.paid_paise >= 100000;
```

The CTE gives a name and clean boundary to the aggregate. Do not assume it executes once or creates an indexable temporary table; inspect the plan in the target database.

### 2.8 Window functions

```sql
SELECT claim_id, patient_id, amount_paise,
       ROW_NUMBER() OVER (
         PARTITION BY tenant_id, patient_id
         ORDER BY created_at DESC, claim_id DESC
       ) AS recency_rank,
       SUM(amount_paise) OVER (
         PARTITION BY tenant_id, patient_id
         ORDER BY created_at, claim_id
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS running_paise
FROM claim;
```

`ROW_NUMBER=1` identifies one deterministic latest row per patient when filtered in an outer query. `ROWS` makes a physical row frame explicit; default `RANGE` frames can include peers with identical ordering values, unexpectedly jumping a running total.

### 2.9 Inserts, updates, deletes, and upserts

Insert explicit columns:

```sql
INSERT INTO claim
  (claim_id, tenant_id, patient_id, external_ref, amount_paise, status, created_at)
VALUES
  ('C9','T1','P1','EXT-9',87500,'SUBMITTED','2026-08-12T10:00:00Z');
```

Safe state transition:

```sql
UPDATE claim
SET status='PAID'
WHERE claim_id='C9' AND status='APPROVED';
```

Require exactly one affected row. Zero means missing/already transitioned/wrong state; more than one violates identity assumptions. PostgreSQL's `INSERT ... ON CONFLICT` can implement atomic conflict handling, but the conflict key and replay semantics must be explicit.

### 2.10 Parameterization

In JDBC:

```java
var sql = "SELECT claim_id FROM claim WHERE tenant_id=? AND status=?";
try (var ps = connection.prepareStatement(sql)) {
    ps.setString(1, tenantId);
    ps.setString(2, status);
    try (var rs = ps.executeQuery()) { /* map rows */ }
}
```

Input `"T1' OR '1'='1"` remains a literal value, not executable syntax. Apply least-privilege database roles too; parameterization does not limit what valid queries a compromised application credential can perform.

## 3. WORKED PROBLEMS

Assume claims: C1/T1/P1/₹1299/PAID, C2/T1/P1/₹499/SUBMITTED, C3/T1/P2/₹2500/PAID, C4/T2/P1/₹875/REJECTED.

### Problem 1 — Filter paid claims (easy)

Return T1 paid claims greater than ₹1,000.

**Solution.** `WHERE tenant_id='T1' AND status='PAID' AND amount_paise > 100000`. C1 is 129,900 paise and qualifies; C3 is another tenant. Compare integral minor units, not formatted strings.

**Trap:** comparing rupee display strings lexicographically.

### Problem 2 — Count semantics (easy)

A five-row table has two null `paid_at` values. What are `COUNT(*)` and `COUNT(paid_at)`?

**Solution.** 5 and 3 respectively. `COUNT(*)` counts rows; `COUNT(expression)` counts non-null evaluated values.

**Trap:** expecting both counts to be five.

### Problem 3 — Monthly timestamp range (easy)

Select all August 2026 instants.

**Solution.** Use `ts >= '2026-08-01T00:00:00Z' AND ts < '2026-09-01T00:00:00Z'`, with time-zone policy matching the business definition. It covers arbitrary fractional precision.

**Trap:** ending at `23:59:59` on August 31.

### Problem 4 — Join cardinality (medium)

P1 has two claims and P2 one. How many rows result from an inner patient/claim join?

**Solution.** Three, one per matching claim. Patient P1 appears twice. Counting joined rows is claim count, not distinct patient count; use `COUNT(DISTINCT patient key)` if that is genuinely required.

**Trap:** assuming joins preserve one row per left record.

### Problem 5 — Preserve zero-claim patients (medium)

Return every patient and its paid-claim count, including zero.

**Solution.** Left join claims with `c.status='PAID'` in `ON`, group by patient key, and `COUNT(c.claim_id)`. Counting `*` would give one for the null-extended row.

**Trap:** right-side filter in `WHERE`, which deletes zero-match patients.

### Problem 6 — Weighted average (medium)

Combine latency groups: 1,000 requests at 100 ms average and 10 at 500 ms.

**Solution.** Total latency 100,000+5,000=105,000 ms; total count 1,010; average ≈103.96 ms. Store/aggregate sum and count or compute over raw rows.

**Trap:** average of averages = 300 ms.

### Problem 7 — Latest row per endpoint (hard)

Return the newest deployment for each endpoint with deterministic ties.

**Solution.** In a CTE, calculate `ROW_NUMBER() OVER (PARTITION BY endpoint_id ORDER BY deployed_at DESC, deployment_id DESC) rn`; outer query filters `rn=1`. The unique deployment ID resolves equal timestamps.

**Trap:** `GROUP BY endpoint_id, MAX(deployed_at)` while selecting unrelated version columns.

### Problem 8 — NOT IN and null (hard)

Why can `id NOT IN (SELECT blocked_id FROM blocklist)` return no rows when blocklist contains null?

**Solution.** Comparisons against null yield unknown; the conjunction implied by NOT IN cannot become true. Use correlated `NOT EXISTS` with equality, or exclude null explicitly if semantics warrant.

**Trap:** treating null as a value that simply fails equality.

### Problem 9 — Injection-safe sorting (hard)

Users choose `amount` or `created` sort order. Can the column name be a parameter?

**Solution.** Bind parameters represent values, not SQL identifiers. Map the external enum to fixed trusted fragments: `amount → amount_paise`, `created → created_at`; reject all others, then append a fixed ASC/DESC choice. Bind all actual values normally.

**Trap:** concatenating the raw query parameter.

## 4. REAL-WORLD / APPLIED CONTEXT

### Feature engineering

MLOps pipelines use SQL to create point-in-time features: rolling claim counts, most recent laboratory result before prediction time, or account velocity. A join that accidentally includes future rows creates target leakage. Window functions and explicit event-time predicates are core ML correctness tools, not only analytics conveniences.

### Reconciliation

Financial reconciliation groups ledger entries by currency, settlement date, and external reference, then compares counts and exact minor-unit sums. Conditional aggregates locate missing, duplicated, or imbalanced postings. SQL excels because the output is a declarative discrepancy set that can be audited and rerun.

### PostgreSQL query optimization

PostgreSQL transforms a query into a plan using table statistics and cost estimates. Equivalent SQL forms are often optimized similarly, but not always; indexes, distributions, correlation, memory, and version matter. `EXPLAIN (ANALYZE, BUFFERS)` supplies execution evidence, covered in the advanced index lesson.

## 5. COMPARISON TABLE

| Construct | Output shape | Use | Common hazard |
|---|---|---|---|
| `WHERE` | Filters input rows | Pre-aggregation predicates | Cannot directly filter aggregate result |
| `HAVING` | Filters groups | Aggregate predicates | Using it where early WHERE filtering is clearer |
| Inner join | Matching pairs only | Required relationship | Drops unmatched rows |
| Left join | All left + matches | Optional relationship/zero counts | Right filter in WHERE collapses it |
| `EXISTS` | Boolean per outer row | Existence check | Correlation key omitted |
| Join | May multiply rows | Need columns from both sides | Inflated aggregates |
| `GROUP BY` | One row per group | Collapse to summaries | Loses row detail |
| Window | Retains input rows | Ranking/running values | Wrong partition/order/frame |
| Offset pagination | Skip N rows | Small stable admin lists | O(N) discard and shifting pages |
| Keyset pagination | Continue after key tuple | Large ordered feeds | More complex composite cursor |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Results are naturally ordered.** Only `ORDER BY` provides order.
2. **`SELECT *` is harmless.** It expands contracts, I/O, and exposure.
3. **`= NULL` tests null.** Use `IS NULL`.
4. **`BETWEEN` is ideal for months.** Inclusive endpoints are fragile for timestamps; use half-open ranges.
5. **Left join plus right WHERE still preserves left rows.** It rejects null-extended rows.
6. **COUNT(*) and COUNT(column) are identical.** The latter ignores null.
7. **Joining only adds columns.** One-to-many joins multiply rows.
8. **Average of averages works.** It requires equal group weights.
9. **A CTE always materializes or speeds a query.** Behavior is DBMS/version/query dependent.
10. **Parameterized queries accept identifiers.** They bind values; allow-list structural choices.
11. **LIMIT without order gives “first.”** First is undefined.
12. **UPDATE can be tried and inspected afterward.** Preview, transact, verify row count, and plan recovery first.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Logical order: FROM/JOIN → WHERE → GROUP → HAVING → SELECT → ORDER → LIMIT.
- No `ORDER BY` means no guaranteed order.
- Null: use `IS NULL`; WHERE keeps true, not unknown.
- `COUNT(*)` rows; `COUNT(x)` non-null x.
- Right-side filters in `ON` preserve left-join unmatched rows.
- `WHERE` before aggregation; `HAVING` after.
- Window functions keep row detail; GROUP BY collapses it.
- Deterministic order needs unique tie-breaker.
- Prefer `NOT EXISTS` for null-safe anti-join semantics.
- Parameterize values; allow-list identifiers/order directions.
- Check affected rows for state transitions.

## 8. PRACTICE SET FOR SELF-TEST

1. Write a query returning APPROVED claims of at least ₹500 for tenant T7.
2. Explain the result of `WHERE status <> 'PAID'` for null status.
3. Return tenants with at least 100 claims.
4. Return every tenant, including those with zero claims, and its claim count.
5. Find patients who have no rejected claims.
6. Return the top three claims by amount with deterministic ties.
7. Calculate a running paid amount per patient ordered by paid time and ID.
8. Write a safe conditional update from SUBMITTED to APPROVED.
9. Explain why `SUM(amount)` can be doubled after joining claims to two tags.
10. Design an allow-listed sort input mapping for `amount_desc` and `newest`.

## 9. CURATED RESOURCES

- PostgreSQL current documentation, Chapter 2 “The SQL Language” and Chapter 7 “Queries” — authoritative selection, joins, grouping, CTE, window, sorting, and limit behavior.
- PostgreSQL current documentation, Sections 9.21 “Aggregate Functions” and 9.22 “Window Functions” — exact null, aggregate, frame, rank, and running calculation semantics.
- Alan Beaulieu, *Learning SQL*, 3rd ed., Chapters 3–16 — progressive query practice from filtering through analytics and transactions.
- Anthony Molinaro and Robert de Graaf, *SQL Cookbook*, 2nd ed. — production-shaped recipes for reporting, dates, hierarchy, windows, and transformations.
- Itzik Ben-Gan, *T-SQL Window Functions*, 3rd ed., Chapters 1–5 — rigorous window ordering/frame reasoning; syntax concepts transfer though dialect differs.
- OWASP, “SQL Injection Prevention Cheat Sheet” — canonical parameterization, stored procedure, allow-list, and least-privilege defenses.
- Martin Kleppmann, *Designing Data-Intensive Applications*, Chapter 2 — relational querying and declarative/imperative trade-offs.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Database and Relational Foundations:** supplies relations, keys, null, constraints, and cardinality.
2. **Programming Logic:** supplies predicates, types, state, and safe failure handling.

### After

1. **PostgreSQL Setup and Operations Basics:** runs these statements against a managed server and explains roles/connections/storage.
2. **PostgreSQL Modeling:** deepens schema types and invariants.
3. **Indexes and Query Plans:** explains the physical cost of logical SQL.
4. **Transactions and Locking:** makes concurrent writes and isolation safe.
5. **ML Fundamentals/Lifecycle:** applies SQL windows and point-in-time joins to leakage-safe features.

---ANSWER KEY BELOW---

1. `SELECT ... FROM claim WHERE tenant_id='T7' AND status='APPROVED' AND amount_paise>=50000` (parameters in application code).
2. Unknown, so the row is not retained; add explicit null semantics if needed.
3. `SELECT tenant_id, COUNT(*) FROM claim GROUP BY tenant_id HAVING COUNT(*)>=100`.
4. Left join tenant to claim and `COUNT(claim_id)`, grouped by tenant key.
5. Correlated `NOT EXISTS` matching patient/tenant and `status='REJECTED'`.
6. `ORDER BY amount_paise DESC, claim_id ASC LIMIT 3` (or another unique tie-breaker).
7. `SUM(amount_paise) OVER (PARTITION BY tenant_id,patient_id ORDER BY paid_at,claim_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` filtered appropriately.
8. `UPDATE claim SET status='APPROVED' WHERE claim_id=? AND status='SUBMITTED'`; require one affected row.
9. Each claim row is repeated once per matching tag before aggregation; pre-aggregate or use correct grain rather than blindly DISTINCT-ing money.
10. Map exact enum values to fixed fragments `amount_paise DESC, claim_id` and `created_at DESC, claim_id DESC`; reject everything else.
