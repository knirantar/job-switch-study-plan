# Database and Relational Foundations from Scratch

Parent subject: `03-data-systems`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why databases exist

A program's in-memory objects disappear when its process stops. Multiple service instances also need a shared, controlled account of patients, payments, jobs, models, and decisions. A **database** is an organized collection of durable data; a **database management system** (DBMS) is software that stores, retrieves, validates, protects, and coordinates access to it.

Writing JSON files may work for a single process, but it breaks under concurrent writers, partial writes, large searches, schema evolution, access control, backups, and recovery. A DBMS centralizes these hard mechanisms. It is not simply a “place to put records”; it is an integrity and concurrency boundary.

Early business systems used hierarchical and network databases. Edgar F. Codd's 1970 paper proposed the **relational model**, representing data as relations and querying it declaratively without exposing physical storage paths. SQL systems evolved from this idea. The separation between logical questions and physical access is profound: an application asks for unsettled claims, while the optimizer chooses scans, joins, and indexes.

### Data, information, metadata, and schema

**Data** is recorded representation such as `claim_id='CLM-1042'` and `amount_paise=129900`. **Information** is meaning derived from data, such as “this claim is unsettled.” **Metadata** describes data: column names, types, constraints, ownership, and timestamps. A **schema** is the formal logical structure of database objects.

A **data model** describes entities, attributes, relationships, and rules. A conceptual model speaks in business terms; a logical model maps those terms to relations and keys; a physical model chooses DBMS-specific types, indexes, partitions, and storage parameters.

### Relations, tuples, and attributes

In relational theory, a **relation** is a set of tuples sharing named attributes. In SQL, a **table** is the closest practical construct, a **row** resembles a tuple, and a **column** resembles an attribute. SQL tables can contain duplicate rows unless constrained, and SQL includes null, so SQL is not a perfect transcription of pure relational algebra.

Consider:

| claim_id | patient_id | amount_paise | status |
|---|---|---:|---|
| CLM-1042 | PAT-88 | 129900 | SUBMITTED |
| CLM-1043 | PAT-91 | 49900 | PAID |

Each column has a **domain**: allowed values and meaning. `amount_paise` is an integer minor-currency amount, not an arbitrary string. `status` should come from a defined set or referenced state table.

### Keys and identity

A **superkey** uniquely identifies rows; a **candidate key** is a minimal superkey; one candidate becomes the **primary key**. A **natural key** has domain meaning, such as a government-issued code; a **surrogate key** is introduced by the system, such as a UUID or sequence number. A **composite key** contains multiple columns.

A **foreign key** states that values in a child table must match a candidate/primary key in a referenced table, unless null is permitted. This is **referential integrity**. Without it, an invoice can refer to a patient that does not exist.

Identity choices are contracts. Email is often a poor primary key because it changes and may require case normalization. A surrogate patient ID keeps references stable, while a separate unique constraint can enforce the current business identifier.

### Constraints

Constraints make invalid states harder or impossible to persist:

- `NOT NULL` requires a value.
- `CHECK` enforces a row-level predicate.
- `UNIQUE` prevents duplicate key values, subject to DBMS null semantics.
- `PRIMARY KEY` provides unique, non-null row identity.
- `FOREIGN KEY` enforces references.
- A default supplies a value when omitted; it does not validate arbitrary provided values.

Application validation improves error messages, but database constraints protect against every writer: services, migration scripts, admin tools, and concurrent races. “We check first” is not equivalent to a unique constraint because two transactions can both observe absence and then insert.

### Relationships and cardinality

**Cardinality** describes how many instances participate:

- one-to-one: one account has one current risk profile;
- one-to-many: one patient has many claims;
- many-to-many: clinicians can belong to many care teams and teams have many clinicians.

Many-to-many relationships require an **associative table**, such as `team_member(team_id, clinician_id, joined_at)`. The relationship may have attributes of its own and is therefore a real domain object, not boilerplate.

**Optionality** matters. A claim must have a patient, so its foreign key is non-null. A payment may not yet have a settlement record, so absence is legitimate. Model absence explicitly rather than inventing IDs such as zero.

### Null and three-valued logic

SQL null means missing/unknown/not applicable depending on the column contract; those meanings should not be mixed casually. Null is not zero, empty string, or a value equal to itself. `column = NULL` is not true; use `IS NULL`. SQL predicates can evaluate true, false, or unknown, and a `WHERE` clause retains only true rows.

For `consent_expires_at`, null might mean “no expiration” or “not recorded.” Those are different business states; separate status and timestamp fields may be clearer.

### Normalization

Normalization organizes relations to reduce contradictory duplication. A **functional dependency** `X → Y` means a given X value determines exactly one Y value.

First normal form (1NF) requires scalar attributes under the conventional SQL interpretation—do not store comma-separated medication IDs. Second normal form (2NF) removes dependency on only part of a composite key. Third normal form (3NF) removes non-key attributes depending transitively on other non-key attributes.

Suppose `claim(claim_id, patient_id, patient_name, insurer_id, insurer_name)`. `claim_id → patient_id`, and `patient_id → patient_name`; patient name is transitively dependent and duplicated across claims. Split patient details into `patient`. Otherwise updating one copy creates inconsistent names, deletion of a patient's last claim loses the patient, and a patient cannot be inserted before a claim. These are update, deletion, and insertion anomalies.

Normalization is not “maximum number of tables.” It is dependency-aware integrity. **Denormalization** deliberately duplicates derived data to improve reads, but needs an ownership and reconciliation mechanism.

### Transactions at first glance

A **transaction** groups operations into a logical unit. A transfer debits one account and credits another; applying only one side corrupts money. **Atomicity** means all or none. **Consistency** means declared invariants hold across committed transactions. **Isolation** governs interference among concurrent transactions. **Durability** means committed work survives relevant failures. These are the ACID properties; later lessons treat their mechanisms and limits in depth.

## 2. CORE MECHANICS

### 2.1 Turn requirements into entities and rules

Requirement: “A tenant has patients. A patient can submit claims. Every claim has positive minor-unit amount and one current status. External claim references are unique within a tenant.”

Entities are tenant, patient, claim. Tenant-to-patient and patient-to-claim are one-to-many. Primary keys provide internal identity. A composite unique constraint `(tenant_id, external_ref)` captures scoped business uniqueness. Amount needs `CHECK(amount_paise > 0)`. Required relationships are non-null foreign keys.

### 2.2 Create a minimal schema

```sql
CREATE TABLE tenant (
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE patient (
  patient_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenant(tenant_id),
  display_name TEXT NOT NULL,
  UNIQUE (tenant_id, patient_id)
);

CREATE TABLE claim (
  claim_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  patient_id TEXT NOT NULL,
  external_ref TEXT NOT NULL,
  amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
  status TEXT NOT NULL CHECK (status IN ('SUBMITTED','APPROVED','REJECTED','PAID')),
  created_at TEXT NOT NULL,
  UNIQUE (tenant_id, external_ref),
  FOREIGN KEY (tenant_id, patient_id)
    REFERENCES patient(tenant_id, patient_id)
);
```

The composite patient reference prevents a claim in tenant A from pointing at a patient in tenant B. A plain `patient_id` foreign key would not express tenant alignment. Production PostgreSQL would use `timestamptz` rather than text for instants; the portable lab uses ISO-8601 strings.

### 2.3 Choose types by meaning and range

Use integer minor units for exact INR postings: ₹1,299 becomes `129900` paise. A signed 64-bit database integer gives far more headroom than 32-bit. Use decimal/numeric when fractional rules require scale. Use timestamp with time-zone semantics for global instants, date for calendar dates, boolean for true/false, and constrained text/enums/reference tables for state.

Do not use a universally flexible string. Strings allow `amount='twelve'`, prevent numeric ordering, and move validation into every consumer.

### 2.4 Model one-to-many and many-to-many

One-to-many places the foreign key on the “many” side. Many-to-many creates a bridge:

```sql
CREATE TABLE team_member (
  team_id TEXT NOT NULL REFERENCES care_team(team_id),
  clinician_id TEXT NOT NULL REFERENCES clinician(clinician_id),
  role TEXT NOT NULL,
  joined_at TEXT NOT NULL,
  PRIMARY KEY (team_id, clinician_id)
);
```

The composite primary key prevents duplicate membership. If a clinician can leave and rejoin and history matters, identity must include a membership ID or interval; the correct key follows the business fact being represented.

### 2.5 Normalize a repeating group

Bad: `prescription(patient_id, medication_codes='RX1,RX7,RX9')`. It cannot enforce medication references, handles commas badly, and makes membership queries expensive and fragile.

Better: `prescription`, `medication`, and `prescription_item(prescription_id, medication_id, dose, sequence_no)`. Each medication is one row; constraints and joins now express structure.

### 2.6 Decide delete behavior

Foreign-key actions include restrict/no action, cascade, and set null. Cascading deletion of a patient through claims may violate retention and audit obligations. Regulated systems commonly prohibit hard deletion of financial/clinical history, recording status changes or privacy erasure workflows instead. Cascades are suitable for genuinely subordinate objects, such as ephemeral draft line items, after explicit analysis.

### 2.7 Use transactions for multi-row invariants

```sql
BEGIN;
UPDATE account SET balance_paise = balance_paise - 50000
 WHERE account_id='A' AND balance_paise >= 50000;
-- verify exactly one row changed
UPDATE account SET balance_paise = balance_paise + 50000
 WHERE account_id='B';
COMMIT;
```

This sketches atomicity but is not a complete transfer protocol. It must verify affected-row counts, handle retryable conflicts, record a ledger entry/idempotency key, and use appropriate isolation. The foundation is that logically inseparable changes share a transaction.

### 2.8 Draw and review the model

Review each table by asking: what real fact does one row represent? What uniquely identifies it? Which columns are mandatory? Which references must share tenant? What can change? What history must remain? Which invariants require more than one row? Which deletion is legally/business permitted? A diagram is useful only when backed by executable constraints.

## 3. WORKED PROBLEMS

### Problem 1 — Identify keys (easy)

A currency table has ISO code, numeric code, name, and symbol. Choose keys.

**Solution.** ISO alphabetic code such as INR is a candidate natural key if governed and stable; numeric ISO code may also be candidate. Symbol is not unique (`$`). Choose one primary key according to integration needs and enforce the other candidate unique.

**Trap:** selecting a display name or symbol as unique identity.

### Problem 2 — Prevent negative claim amounts (easy)

Where should `amount_paise > 0` be enforced?

**Solution.** Validate in the API for a clear response and enforce a database `CHECK` for all writers. Use an integer type with sufficient range. Defense at both layers serves different purposes.

**Trap:** believing service validation closes concurrent or alternate-writer paths.

### Problem 3 — Patient-to-claim cardinality (easy)

A claim belongs to exactly one patient; a patient may have zero or many claims.

**Solution.** Put a non-null `patient_id` foreign key in claim. No claim row is required for a patient. This is mandatory many-to-one from claim and optional one-to-many from patient.

**Trap:** adding `claim_ids` as a list column on patient.

### Problem 4 — Tenant isolation key (medium)

Patient IDs are only unique inside a tenant. How can claim safely reference patient?

**Solution.** Patient has composite key/unique `(tenant_id, patient_id)`. Claim stores both and declares a composite foreign key. This makes cross-tenant reference structurally invalid.

**Trap:** validating tenant equality only in application code.

### Problem 5 — Normalize an invoice (medium)

One row stores invoice ID, customer ID/name, and three sets of product ID/name/quantity columns.

**Solution.** Create customer, invoice, product, and invoice_line. Customer name depends on customer ID; product name depends on product ID; each line is a repeating relationship identified by invoice plus line number/product according to requirements. This removes fixed three-item capacity and update anomalies.

**Trap:** merely adding more product columns.

### Problem 6 — Null semantics (medium)

Should `paid_at=NULL` mean a claim was rejected?

**Solution.** No. Null only says no payment instant is recorded; submitted, approved, rejected, and canceled claims can all lack one. Store explicit status constrained to allowed transitions, with paid_at required by a cross-column constraint when status is PAID if the DBMS/model supports it.

**Trap:** inferring business state from an overloaded null.

### Problem 7 — Concurrent uniqueness (hard)

Two instances check that external reference X is absent, then insert. How do you prevent duplicates?

**Solution.** Declare `UNIQUE(tenant_id, external_ref)`. One insert succeeds and the other conflicts according to transaction timing. Treat the conflict as idempotent replay or domain error based on payload matching. A read-before-write check alone has a race.

**Trap:** solving concurrency with an ordinary `SELECT`.

### Problem 8 — Delete a patient (hard)

A privacy request asks to delete a patient who has settled claims. Should foreign keys cascade?

**Solution.** Not automatically. Financial and clinical retention, audit, legal holds, and reconciliation may require records. Apply a governed erasure/de-identification policy to eligible attributes, preserve required ledger facts, record approvals/evidence, and restrict destructive cascades. Schema behavior must match policy.

**Trap:** treating GDPR-style erasure as unconditional physical deletion of every related row.

### Problem 9 — Denormalization decision (hard)

An analytics endpoint repeatedly joins patient region into 500 million claim rows. May region be copied?

**Solution.** First measure query/index/materialized-view options. If denormalized, define whether the copied region means region at claim time or current region, populate it transactionally/eventually with explicit lag, reconcile mismatches, and backfill safely. Duplication without time semantics produces ambiguous reports.

**Trap:** denormalizing for speed without ownership and repair.

## 4. REAL-WORLD / APPLIED CONTEXT

### PostgreSQL integrity constraints

PostgreSQL implements primary, unique, check, non-null, exclusion, and foreign-key constraints. Unique constraints normally create unique B-tree indexes. Constraints both document and enforce the model, while transactions coordinate multi-statement changes.

### FHIR resources and references

HL7 FHIR represents healthcare information as typed resources and references rather than one giant patient document. Relational persistence of FHIR-like data must preserve resource identity, version/provenance, references, codes, and search requirements. Blindly flattening or storing opaque JSON trades schema work for weaker constraints and harder querying.

### Double-entry ledgers

Financial ledgers record balanced postings rather than overwriting a single mutable balance as the only truth. The schema encodes accounts, transactions, entries, currencies, and invariants. Derived balances can be rebuilt and reconciled. This is relational modeling serving auditability, not merely CRUD storage.

## 5. COMPARISON TABLE

| Choice | Strength | Cost/risk | Prefer when |
|---|---|---|---|
| Relational DB | Constraints, joins, transactions, declarative queries | Schema/change discipline | Connected structured business data |
| Document DB | Aggregate-shaped flexible documents | Cross-document integrity/joins vary | Bounded aggregates with known access paths |
| Key-value store | Simple low-latency lookup | Limited querying/relationships | Cache, sessions, known-key access |
| Natural key | Domain-visible, no extra identifier | Can change, be wide/sensitive | Truly stable governed identifier |
| Surrogate key | Stable, compact references | Needs separate business uniqueness | Mutable/composite/sensitive domain keys |
| Normalized model | Less contradictory duplication | More joins | Source-of-truth transactional data |
| Denormalized model | Faster/simple reads | Staleness and reconciliation | Measured read need with explicit ownership |
| DB constraint | Protects every writer atomically | DB-specific evolution/error handling | Durable invariant expressible by DB |
| App validation | Rich contextual feedback | Can be bypassed/racy | Usability and rules needing external context |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **A table is just a spreadsheet.** Tables have domains, keys, constraints, relationships, transactions, and concurrent access.
2. **Every ID should be auto-increment.** Key strategy depends on distribution, exposure, stability, and business uniqueness.
3. **Foreign keys are too slow.** Integrity has cost, but deleting them transfers correctness and cleanup cost to every application.
4. **Null equals empty or zero.** It changes predicate logic and must have a precise contract.
5. **Comma-separated lists are relational.** They hide multiple facts in one attribute and defeat references.
6. **Normalization means no duplicate values anywhere.** Legitimate values repeat; normalization follows dependencies.
7. **Denormalization is always bad.** It is valid when deliberate, measured, owned, and reconcilable.
8. **Unique pre-check prevents duplicates.** Only the atomic database constraint closes the race.
9. **Cascade is convenient cleanup.** It can erase regulated or financial history.
10. **ACID means no application anomalies.** Transactions enforce specified mechanisms; incorrect boundaries and isolation still produce errors.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- One row must represent one clearly stated fact.
- Primary key: chosen unique non-null identity.
- Foreign key: referenced value must exist; use composite keys for scoped identity.
- Put FK on “many” side; bridge table for many-to-many.
- Enforce invariants in DB and validate at API boundary.
- Null is not zero/empty; use `IS NULL`.
- Normalize based on functional dependencies and anomaly prevention.
- Denormalize only with semantics, owner, update path, and reconciliation.
- Transactions group logically inseparable changes.
- Delete behavior is a domain/compliance decision.

## 8. PRACTICE SET FOR SELF-TEST

1. Identify candidate keys for a country table containing ISO alpha-2, alpha-3, numeric code, and name.
2. Model one organization with many users where email is unique only within organization.
3. Add constraints for a percentage from 0 through 100 inclusive.
4. Explain why `WHERE discharged_at = NULL` returns no true matches.
5. Normalize `employee(employee_id, department_id, department_name, manager_id)` under stated dependencies.
6. Model students taking courses with grade and enrollment date.
7. Explain the race in “SELECT then INSERT” username allocation.
8. Choose a representation for ₹12,345.67 in minor units.
9. Decide whether deleting an order should delete its immutable payment ledger entries.
10. State a transaction boundary for reserving inventory and creating a local order.

## 9. CURATED RESOURCES

- Edgar F. Codd, “A Relational Model of Data for Large Shared Data Banks,” *Communications of the ACM* 13(6), 1970 — the primary relational-model motivation and data independence argument.
- C.J. Date, *An Introduction to Database Systems*, 8th ed., Chapters 1–11 — rigorous relations, keys, integrity, algebra, and normalization.
- Hector Garcia-Molina, Jeffrey Ullman, and Jennifer Widom, *Database Systems: The Complete Book*, 2nd ed., Chapters 1–3 and 6 — modeling, relational theory, constraints, and practical schema design.
- PostgreSQL current documentation, Chapters 2 “The SQL Language,” 5 “Data Definition,” and 11 “Indexes” — authoritative PostgreSQL table, type, constraint, privilege, and index behavior.
- Martin Kleppmann, *Designing Data-Intensive Applications*, Chapter 2 “Data Models and Query Languages” — trade-offs among relational, document, graph, and impedance mismatch.
- HL7 FHIR R4, “Resource,” “References,” and “Patient” documentation — actual healthcare identity, metadata, versioning, and reference semantics.
- Martin Fowler, “Patterns of Enterprise Application Architecture,” chapters on Data Mapper and Unit of Work — connects relational persistence to application boundaries.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Programming Logic and Debugging:** provides types, contracts, invariants, and failure reasoning.
2. **Sets and Hashing:** helps with uniqueness, set operations, identity, and collisions.

### After

1. **SQL from Scratch:** uses this model to retrieve and change data declaratively.
2. **PostgreSQL Setup and Operations Basics:** instantiates these concepts in a real DBMS.
3. **PostgreSQL Modeling:** deepens types, tenant design, temporal data, and invariants.
4. **Indexes and Query Plans:** explains how logical queries become physical work.
5. **Transactions and Locking:** makes concurrent multi-row correctness precise.

---ANSWER KEY BELOW---

1. Each governed ISO code can be a candidate key; name is not reliably unique/stable. Choose one primary and enforce others unique.
2. Organization primary key; user primary key plus non-null organization FK; `UNIQUE(org_id, normalized_email)`.
3. `NOT NULL CHECK (percentage >= 0 AND percentage <= 100)` with an appropriate numeric type.
4. Comparison with null is unknown; use `IS NULL`.
5. Department name depends on department ID, so separate department; manager is an employee self-reference if that is the domain meaning.
6. Enrollment bridge with student/course FKs, grade/date attributes, and a composite key or enrollment identity matching repeat policy.
7. Concurrent transactions can both observe absence; enforce a unique constraint and handle conflict.
8. Signed sufficiently wide integer `1_234_567` paise, with currency recorded where multiple currencies exist.
9. Normally no; restrict and retain/reverse according to ledger policy rather than cascading deletion.
10. Within one database, insert order and conditionally decrement/reserve inventory in one transaction, checking affected rows; external payment needs a saga/outbox rather than pretending one DB transaction spans it.
