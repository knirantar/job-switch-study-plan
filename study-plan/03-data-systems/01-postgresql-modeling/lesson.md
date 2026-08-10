# PostgreSQL Data Modeling — Complete Study Resource

**Parent:** `03-data-systems`  
**Child:** `01-postgresql-modeling`  
**Baseline:** PostgreSQL 18 current documentation; note deployed version differences

## 1. FOUNDATIONS

### Data modeling is invariant design

A relational model is not merely tables that mirror Java classes. It is a durable representation of business facts and constraints under concurrent access, migrations, reporting and years of evolution. Application validation can be bypassed by another service, script or race; database constraints are the final shared defense.

The **relational model**, introduced by E. F. Codd in 1970, represents data as relations (tables) of tuples (rows) over attributes (columns), manipulated declaratively. SQL implementations include nulls, bags, types and operational features beyond pure relational algebra, but the core benefit remains: specify what data means and let the database enforce/query it.

A **schema** defines tables, columns, types, constraints and relationships. A **primary key** uniquely and non-null identifies a row. A **candidate key** is any minimal unique identifier; one becomes primary, others use UNIQUE. A **foreign key** requires referenced key existence and preserves referential integrity. A **natural key** derives from domain facts (email, code); a **surrogate key** is artificial (UUID/identity). Natural keys can change or have subtle normalization; surrogate keys do not replace business uniqueness constraints.

### Functional dependencies and normalization

A functional dependency `X→Y` means X determines Y. Normalization separates facts to reduce anomalies:

- First normal form: atomic values under chosen domain/no repeating groups.
- Second: non-key attributes depend on whole composite key, not a subset.
- Third: non-key attributes do not depend transitively on key through another non-key attribute.
- BCNF: every determinant is a candidate key.

Example order line `(order_id,product_id,product_name,quantity)`: product_id determines product_name independently of order. Repeating name across lines creates update inconsistency. Move product facts to product table. Normalization is not aesthetic; it prevents insert/update/delete anomalies.

**Denormalization** intentionally duplicates/aggregates for measured read needs with an ownership/refresh correctness plan. A stale cached total is not “faster normalization.”

### Null and three-valued logic

SQL NULL means missing/unknown/not applicable, not zero or empty string. Comparisons with NULL yield UNKNOWN; use `IS NULL`. `CHECK (x>0)` passes when expression is UNKNOWN, so add NOT NULL if required. Unique-constraint handling of NULL and `NULLS NOT DISTINCT` options are database/version-specific. Nullability is a domain decision.

## 2. CORE MECHANICS

### 2.1 Entities, value objects and events

An **entity** has identity across change: payment p123 changes status. A **value object** is defined by value: Money(5000,INR). An **event** records something occurred and should usually be immutable: PaymentCaptured at time. Do not force all three into one mutable table.

Model aggregates around invariants/transaction boundaries, not object nesting. Payment status history can be separate append-only rows while payment stores current status for operational reads.

### 2.2 Keys

`bigint GENERATED ... AS IDENTITY` is compact, ordered and database-generated; it can expose volume and complicate multi-writer generation. UUID is 16-byte PostgreSQL type, globally generatable and opaque but larger/random insertion can affect index locality. PostgreSQL 18 supports UUID type per RFC 9562 and generation functions; exact UUID versions/features depend release.

Time-ordered UUIDs can improve locality but reveal time and require correct generator. Never use string `varchar(36)` when native uuid suffices. Composite key expresses scope, e.g. `(tenant_id,idempotency_key)`. A surrogate payment_id still needs that unique business key.

### 2.3 Numeric and money

Floating-point is approximate and unsuitable for exact currency totals. Options:

- `bigint amount_minor`: cents/paise, exact/fast, currency scale must be known and multiplication overflow checked;
- `numeric(p,s)`: exact decimal, supports varying scale but more CPU/storage;
- PostgreSQL `money`: fixed fractional precision and locale-sensitive input/output concerns; generally avoid in portable domain schemas.

For INR ₹50.25, minor units5025. Store currency separately and prevent adding different currencies. `numeric(19,4)` means up to15 integer and4 fractional digits; rounding rules must be business-defined.

### 2.4 Text

PostgreSQL `text` and `varchar` without length have similar general storage/performance; use length constraint only for domain/API limits, not folklore. `char(n)` blank-pads and often surprises—currency `char(3)` is defensible but text+CHECK can be clearer.

Collation affects comparison/order/unique behavior. Email case/Unicode normalization is domain-specific; `lower(email)` unique may not implement full desired identity. Store original plus canonical key computed by well-defined application/database function and test migrations.

### 2.5 Time

Use `timestamptz` for instants. PostgreSQL stores timezone-aware timestamps internally as UTC and renders in session timezone; it does not retain original zone name. Store separate IANA zone (`Asia/Kolkata`) when future local scheduling needs DST rules. Use `timestamp without time zone` for a wall-clock value intentionally lacking instant semantics.

`CURRENT_TIMESTAMP` is transaction start time; `statement_timestamp()` and `clock_timestamp()` differ. This matters for long transactions/history. The sample schema uses clock_timestamp for event wall time; choose deliberately.

### 2.6 Boolean, enums and lookup tables

Boolean fits true/false; nullable boolean introduces unknown third state. PostgreSQL ENUM enforces values and compact semantics but changing/removing/reordering values has migration implications and couples DB type. CHECK text is easy to extend in migration; lookup table supports metadata/configurable states but permits values according to FK/data lifecycle. Stable small state machines can use enum; cross-service evolution may favor text+CHECK/lookup.

### 2.7 JSON versus JSONB

`json` stores original text and reparses; `jsonb` stores decomposed binary form, supports indexing/operators, discards whitespace/key order and collapses duplicate keys according to semantics. Use JSONB for optional metadata with variable shape, not core fields needed for constraints/joins.

Validate top-level type and application schema. A JSONB “everything” column loses types, referential integrity and discoverability. SQL NULL differs from JSON `null`. Index strategy comes from actual operators/paths.

### 2.8 Constraints

Use NOT NULL, CHECK, UNIQUE, PRIMARY KEY and FOREIGN KEY. A CHECK should express row-local immutable rule; PostgreSQL assumes check condition immutable across rows/time and does not support cross-row CHECK guarantees. Cross-row uniqueness uses UNIQUE/exclusion/transactions.

Foreign key action: RESTRICT/NO ACTION protects referenced rows; CASCADE can delete huge graphs accidentally; SET NULL only when null semantically valid. Index foreign-key referencing columns for delete/update checks and joins as workload requires—PostgreSQL does not automatically create every referencing-side index.

Composite FK `(tenant_id,account_id)` prevents payment tenant t1 referencing account with same ID owned by t2, provided referenced composite unique exists. This is defense in depth for tenant isolation.

### 2.9 Generated, default and identity columns

Default applies on insert when value absent and can use volatile functions. Generated column recomputes from other current-row columns and cannot be directly overridden; PostgreSQL 18 supports stored and virtual with restrictions such as immutable expressions and no subqueries. Generated is not trigger/event history.

Identity is SQL-standard sequence-backed generation. Sequence values are not gapless: rollbacks/caching/concurrency create gaps. Never promise invoice legal numbering from a plain sequence without domain-specific controlled design.

### 2.10 Modeling state transitions

Current payment row enables fast lookup. History table with `(payment_id,sequence_no)` records transitions. Enforce allowed transitions in application or database procedure/trigger where multiple writers demand central rule. CHECK cannot compare previous row state.

Optimistic version supports conditional update. Status + timestamps need consistency: captured_at nonnull iff CAPTURED can be a CHECK, but growing state complexity may favor separate event/history.

### 2.11 Multi-tenancy

Shared schema with tenant_id is simplest/efficient but every query/constraint/index must scope tenant. Schema-per-tenant increases isolation/customization but migration/connection/search_path complexity. Database-per-tenant strongest operational isolation but expensive at scale.

Row-Level Security (RLS) can enforce policies in DB for normal roles after enabled, but owners/superusers/bypass roles and session tenant-context setup require care. RLS complements, not replaces, application authorization and tests. Connection pools must reset tenant context to prevent leakage.

### 2.12 Partitioning

Partitioning splits one logical table physically by range/list/hash. Use for very large tables when pruning/maintenance/retention benefits match query predicates. Monthly audit partitions make dropping old data fast; range bounds lower-inclusive/upper-exclusive.

Partitioning is not automatic speed. Too many partitions increase planning/operations; queries missing partition key scan many partitions. Unique constraints on partitioned table generally need partition key to guarantee global uniqueness under PostgreSQL rules. Partition only after workload/size evidence.

### 2.13 Soft delete and temporal data

`deleted_at` preserves row but every query/unique constraint must account for active rows. Partial unique index can enforce active email uniqueness. Soft delete is not audit/history/legal retention by itself. Foreign keys and cascading semantics become complex. If deletion must erase personal data, soft delete may conflict.

Temporal history can be append-only events/audit tables with valid/effective times; distinguish system time (recorded) and business valid time. Update-in-place loses prior facts unless history captured transactionally.

### 2.14 Pagination/index-aware modeling

For tenant payments ordered newest, stable key `(tenant_id,created_at DESC,payment_id DESC)` matches cursor and index. Timestamp alone is not unique. Deep offset scales poorly. Modeling and query access paths co-design indexes; index detail comes next topic.

### 2.15 Outbox

Outbox event belongs in same database transaction as aggregate mutation. Store event_id, aggregate identity/type, event type, version, payload, occurred_at, publication state. Payload schema/version avoids consumers guessing. Relay queries unpublished partial index; duplicates remain possible, so consumer deduplicates.

## 3. WORKED PROBLEMS

### Problem 1 — Payment amount

**Statement.** Store INR/USD exact amounts up to ₹10 trillion.

**Solution.** `bigint amount_minor` plus currency check works: ₹10T=1 quadrillion paise, below 9.22e18. Validate positive and arithmetic overflow. If currencies with varying fractional rules/custom decimals, numeric or currency metadata needed.

**Mistake caught.** `double precision` for exact money.

### Problem 2 — Tenant idempotency

**Statement.** Same key may be used by different tenants, once per tenant.

**Solution.** UNIQUE `(tenant_id,idempotency_key)`, NOT NULL both. Store request hash/result. Global unique key would cause cross-tenant collision/DoS; no unique allows duplicates.

**Mistake caught.** Surrogate payment ID alone encodes business uniqueness.

### Problem 3 — Cross-tenant account

**Statement.** Payment t1 references account ID belonging t2.

**Solution.** Account has UNIQUE `(tenant_id,account_id)`; payment composite FK matches both. Application auth still required, but database rejects inconsistent tenant relation.

**Mistake caught.** FK only account_id allows valid but wrong-tenant reference.

### Problem 4 — Time zone appointment

**Statement.** Schedule “09:00 America/New_York every Monday.”

**Solution.** Store local time/day/zone name and recurrence policy; compute each instant using IANA rules. A single timestamptz stores one instant, not recurring local intent. Numeric UTC offset fails DST changes.

**Mistake caught.** Storing all time as UTC solves future civil schedule semantics.

### Problem 5 — Product metadata

**Statement.** Core searchable price/status and rare vendor attributes.

**Solution.** Typed columns for identity, price, currency, status, constraints; JSONB object for vendor metadata with size/schema limits and indexes only for measured queries. Do not put FK product category only in JSON.

**Mistake caught.** JSONB as schema avoidance.

### Problem 6 — Order-line normalization

**Statement.** Rows repeat customer address and product name.

**Solution.** Separate customer/product current facts and order/order_line. However order may need immutable shipping-address snapshot and product-description/price-at-purchase because historical fact must not change with current entities. “Duplicate” can be intentional snapshot with provenance.

**Mistake caught.** Blind normalization destroys historical truth.

### Problem 7 — Soft-deleted username

**Statement.** Active usernames unique; deleted account may free name.

**Solution.** `CREATE UNIQUE INDEX ... ON user_account(tenant_id,canonical_username) WHERE deleted_at IS NULL`. Decide whether reuse/security/audit permits it. Queries must filter active.

**Mistake caught.** Plain UNIQUE prevents reuse; no index allows active duplicates.

### Problem 8 — Monthly audit retention

**Statement.** Billions audit rows retained13 months and deleted monthly.

**Solution.** Range partition by occurred_at month when queries/retention align; precreate partitions, index locally, drop/detach expired partition. Ensure default/future partition and UTC boundaries. Partition pruning requires compatible predicates.

**Mistake caught.** Partitioning by tenant when deletion/query is by month.

### Problem 9 — Sequence invoice numbers

**Statement.** Finance demands gapless legal invoice number.

**Solution.** PostgreSQL sequence cannot guarantee gapless under rollback/concurrency. Clarify legal scope (per fiscal entity/year), allocate at commit/finalization through locked counter table or specialized process, accept contention/recovery/audit. Never reuse accidentally.

**Mistake caught.** Identity/sequence is gapless.

## 4. REAL-WORLD / APPLIED CONTEXT

### Concrete PostgreSQL storage facts

PostgreSQL 18 docs list `timestamptz` at8 bytes with microsecond resolution and storage internally as UTC, `date`4 bytes and interval16 bytes. UUID native type stores RFC9562 identifiers. These payload figures exclude row/page/null bitmap/alignment/index overhead.

### Healthcare

Clinical observation facts often have coded concept, value/units, effective time, subject/encounter and provenance. Dumping a FHIR resource JSON can preserve interchange shape, but operational analytics/integrity may require typed extracted columns plus original versioned payload. PHI classification, consent and retention shape schema.

### Fintech

Ledger systems prefer immutable balanced entries over mutating one balance as sole truth. Double-entry schema asserts each transaction’s debits equal credits and derives/reconciles balances. Payment workflow table is not itself an accounting ledger.

`payment-schema.sql` provides a concrete tenant/account/payment/history/outbox model. `ModelValidationLab.java` validates domain money/key semantics and demonstrates why durable UNIQUE is required beyond its local simulation.

## 5. COMPARISON TABLE

| Choice | Strength | Cost/boundary | Use |
|---|---|---|---|
| bigint minor money | exact/fast | scale metadata/overflow | fixed-scale currencies |
| numeric(p,s) | exact flexible decimals | CPU/storage | calculations/varying scale |
| bigint identity | compact/locality | centralized/exposes order | internal high-volume key |
| UUID | distributed/opaque | 16B/larger index/locality depends version | public/distributed identity |
| normalized tables | integrity/update clarity | joins | mutable shared facts |
| denormalized snapshot | historical/read speed | duplication/refresh | immutable event/order snapshot |
| typed columns | constraints/planner/discovery | migrations | core queried facts |
| JSONB | flexible metadata/indexable | weak schema/large updates | optional evolving attributes |
| shared tenant schema | efficient operations | policy/query leakage risk | many similar tenants |
| database per tenant | strong isolation | operational cost | high-value/regulated tenants |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **ORM class equals table design.** Durable facts/invariants/access differ from object graph.
2. **Surrogate key replaces business unique.** It does not.
3. **CHECK alone rejects NULL.** UNKNOWN passes; add NOT NULL.
4. **Float for money.** Binary approximation corrupts exact totals.
5. **UTC solves time zones.** It solves instants, not future local recurrence intent.
6. **UUID is free.** Larger key/index and locality effects.
7. **VARCHAR(255) is optimization.** Choose domain limit, PostgreSQL text/varchar behavior.
8. **JSONB everything is flexible.** It removes integrity/discoverability.
9. **FK automatically indexed both sides.** Referencing-side index is not automatic.
10. **Sequence gapless.** Rollback/cache/concurrency leave gaps.
11. **Partitioning always faster.** Wrong key/many partitions worsen planning/scans.
12. **Soft delete equals audit/privacy.** It satisfies neither automatically.
13. **RLS replaces app auth.** Roles/session setup/bypass and field/action rules remain.
14. **Database enum always best.** Evolution/deployment coupling matters.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full resource.

- Model facts, identities, invariants, history and access paths.
- PK identity; UNIQUE business candidate keys; FK relationships.
- NOT NULL with CHECK; NULL uses three-valued logic.
- bigint minor/numeric for exact money, not float.
- timestamptz for instant; zone name+local rule for future schedule.
- typed core fields; JSONB bounded optional metadata.
- composite tenant FKs/uniques prevent cross-tenant relations.
- generated/default/identity have distinct timing/semantics.
- sequence not gapless.
- partition only for measured pruning/maintenance; bounds `[from,to)`.
- outbox transactionally records external event intent.
- normalize shared mutable facts; intentionally snapshot historical facts.

## 8. PRACTICE SET FOR SELF-TEST

1. Model patient appointment with local recurring time and actual occurrences.
2. Choose types/constraints for exchange rate with8 decimal places.
3. Normalize invoice, customer, line, product while preserving purchase snapshot.
4. Design tenant-scoped unique email with canonicalization policy.
5. Model payment status transitions and immutable audit.
6. Decide JSONB versus typed fields for model deployment config.
7. Design active-only unique device name under soft delete.
8. Choose partition key for logs queried/deleted by day but filtered tenant.
9. Explain SQL NULL versus JSON null in metadata.
10. Design outbox schema versioning and consumer identity.

## 9. CURATED RESOURCES

1. **PostgreSQL 18 Manual, Chapters 5 “Data Definition” and 8 “Data Types.”** Exact constraints, generated columns, partitioning and type behavior.
2. **PostgreSQL Manual, Row Security Policies.** Database-enforced tenant-row policy semantics and bypass boundaries.
3. **Codd, “A Relational Model of Data for Large Shared Data Banks” (1970).** Original relational motivation and data independence.
4. **Date, *An Introduction to Database Systems*, normalization chapters.** Formal dependencies/normal forms beyond pragmatic examples.
5. **Kleppmann, *Designing Data-Intensive Applications*, Chapters 2–3.** Data models, storage and schema evolution trade-offs.
6. **Fowler, *Patterns of Enterprise Application Architecture*, data mapping/unit-of-work chapters.** Object-relational boundary patterns.
7. **RFC 9562, UUIDs.** Current UUID formats and time-ordered variants.
8. **ISO 4217 currency code/scale data (official maintenance source).** Currency identity; note minor-unit policy must be versioned.
9. **Martin Fowler, “Accounting Patterns” / double-entry references.** Ledger correctness beyond payment-state storage.

## 10. RELATED TOPICS BRIDGE

### Before

1. **API/Spring Transactions.** API idempotency and service invariants need durable schema enforcement.
2. **Hashing/Trees.** Keys and relationships underpin indexes.

### After

1. **Indexes and Query Plans.** Access paths test whether model serves workload.
2. **Transactions and Locking.** Constraints interact with concurrent writers/MVCC.
3. **Caching.** Derived copies require ownership/invalidation.
4. **Migrations.** Schema evolution changes live durable state safely.

---ANSWER KEY BELOW---

1. Recurrence table: patient/clinician, weekday/local_time, IANA zone, start/end/policy; occurrence table stores generated scheduled_start timestamptz, status/version. DST gap/overlap policy explicit and generator version/audit.
2. `numeric(p,8)` with p sized max magnitude, NOT NULL, positive/range CHECK, base/quote currency codes and effective interval/source UNIQUE. Avoid float.
3. Customer current table; invoice stores customer ID plus legal name/address/tax snapshot; product current; line stores product ID plus description/unit price/currency/tax snapshot, quantity; invoice totals constrained/reconciled.
4. Store original email and canonical_email produced by a versioned documented canonicalizer; UNIQUE `(tenant_id,canonical_email)`, NOT NULL and length. Case/Unicode/domain rules tested; migration recomputes and resolves collisions.
5. Payment current status/version; history/event rows with sequence, old/new, actor, occurred time, reason/correlation. Transition/update/history transactionally atomic; allowed transitions central where multiple writers.
6. Typed columns for model/image/environment identity, CPU/GPU/memory, replicas, endpoint/security fields used in validation/query; JSONB for provider-specific optional settings with version/schema/size check. Do not hide secrets in JSON.
7. Partial unique index `(tenant_id,canonical_name) WHERE deleted_at IS NULL`; decide reuse/audit and filter all active queries.
8. Range partition by occurred_at daily/monthly because pruning/retention align; indexes within partition `(tenant_id,occurred_at...)`. Tenant partitioning would make time deletion touch every partition.
9. SQL NULL means column missing/unknown; JSONB value `null` is a present JSON value. `metadata IS NULL` differs from `metadata->'x' = 'null'::jsonb`; constrain metadata NOT NULL object.
10. Outbox event_id, tenant, aggregate type/id/version, event type/version, payload, occurred, trace, published state/attempt. Consumers identify event type+schema version, dedupe event_id and support compatible versions.
