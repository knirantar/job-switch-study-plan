# Spring Data JPA Fundamentals — Entities, Persistence Context, Repositories and Queries

**Parent:** 02 — Java and Spring  
**Level:** prerequisite 7  
**Study time:** 3–4 hours plus concept lab  
**Lab:** `JpaConceptLab.java`

## 1. FOUNDATIONS

### JDBC, JPA, Hibernate and Spring Data

**JDBC** is Java's database API: connections, prepared statements, result sets, transactions. **JPA** (Jakarta Persistence) is a specification for object-relational mapping and entity lifecycle. **Hibernate ORM** is a common JPA implementation. **Spring Data JPA** builds repository abstractions/query derivation on JPA. **Spring JDBC** is Spring's lower-level JDBC convenience. These are layers, not synonyms.

ORM maps relational rows/relationships to objects while tracking changes. It solves repetitive mapping and unit-of-work, but cannot remove SQL, indexes, constraints, isolation or distributed-system realities. An object graph and relational model have different shapes—the **object-relational impedance mismatch**. Lazy loading, N+1 queries, cascades and unexpected flushes come from pretending the database is an in-memory collection.

An **entity** has persistent identity and lifecycle; a **value object/embeddable** is defined by value and owned. A **persistence context** is a unit-of-work/identity map tracking managed entities. A **repository** expresses aggregate persistence operations, not a magical remote collection.

### Why the basics matter before advanced transactions

`@Transactional` operates around database work, but understanding it requires knowing when SQL executes, what managed/detached means, dirty checking, flush, lazy proxy and connection. `save` does not always issue INSERT immediately. Query method names generate queries but may be inefficient. `FetchType.EAGER` does not guarantee one SQL join. `OpenEntityManagerInView` can hide lazy loading into controller and cause N+1/long connections.

Interviewers ask entity states, first-level cache, `persist` vs `merge`, LAZY/EAGER, owning side, cascade, N+1, pagination, optimistic locking, repository methods and testing.

## 2. CORE MECHANICS

### 2.1 Relational schema remains authoritative

Design tables with primary keys, tenant-aware unique keys, foreign keys, NOT NULL, CHECK, correct numeric/time types and indexes. ORM annotations should match migrations; do not use Hibernate auto-DDL for production evolution. Flyway/Liquibase migrations are reviewed/versioned.

Example claims:

```sql
create table claim (
 id bigint generated always as identity primary key,
 tenant_id varchar(50) not null,
 external_id varchar(100) not null,
 amount_paise bigint not null check (amount_paise > 0),
 version bigint not null default 0,
 created_at timestamptz not null,
 unique (tenant_id, external_id)
);
```

Application validation improves UX; constraints win concurrency. Store money with currency/precision. `timestamptz` semantics and JDBC mappings must be tested.

### 2.2 Entity mapping

```java
@Entity @Table(name="claim", uniqueConstraints=...)
class ClaimEntity {
 @Id @GeneratedValue(strategy=IDENTITY) Long id;
 @Column(nullable=false) String tenantId;
 @Version long version;
 protected ClaimEntity() {}
}
```

JPA requires entity class rules (non-final in portable model, no-arg public/protected constructor, identity). Field access when annotations on fields; property access on getters. Keep invariants via constructors/methods while satisfying provider. Avoid Lombok `@Data` on entities: generated equals/toString traverse lazy/bidirectional relations and mutable IDs.

### 2.3 Entity states

**Transient/new:** not associated/no DB identity; **managed/persistent:** context tracks; **detached:** was managed, context closed/cleared; **removed:** scheduled deletion. `persist` makes new managed. `find` returns managed (or null); `getReference` proxy/reference may defer DB. `remove` schedules managed removal. `detach/clear` stops tracking.

`merge(detached)` copies detached state into a managed instance and returns that managed instance; passed object remains detached. Ignoring return is classic bug. Spring Data `save` chooses persist/merge based on new detection; do not call save on every already managed change—dirty checking suffices.

### 2.4 Persistence context and first-level cache

Within context, repeated find same ID returns same managed object identity and often avoids second select. This is first-level cache, mandatory and scoped to context. It is not cross-request distributed cache. Bulk SQL/native updates bypass managed state and can leave stale entities; clear/refresh appropriately.

Persistence context may grow in batch; flush and clear chunks. Never keep it across huge jobs. EntityManager is not thread-safe.

### 2.5 Dirty checking and flush

Provider snapshots/enhances managed entity; changes generate SQL at flush. Flush synchronizes context to DB but does not commit. It may occur before commit, JPQL query (flush mode), explicit `flush`. Constraint error may appear on flush/commit, not setter/save.

Transaction rollback reverses DB work, but in-memory managed object values may remain changed; discard/reload after rollback. `saveAndFlush` forces early synchronization but is not commit and often overused.

### 2.6 ID generation

IDENTITY uses DB identity and may require immediate insert to obtain ID, reducing batching. SEQUENCE supports allocation/batching on databases with sequences; configure allocation size consistent. TABLE strategy generally contention-heavy. UUID application-generated helps distributed identity but index locality/storage considerations; use suitable versions/types.

ID choice affects equality. New entities with null generated ID should not all compare equal. Common patterns use immutable natural key or cautious ID equality once non-null, often class/proxy considerations. Avoid entities as hash keys while ID/equality mutates.

### 2.7 Relationships and owning side

`@ManyToOne` commonly many claims→one customer; `@OneToMany(mappedBy="customer")` inverse collection. Owning side (foreign-key mapping) drives update. Maintain both sides in helper methods for in-memory consistency. `mappedBy` names Java field, not DB column.

Default fetch: many-to-one/one-to-one EAGER by spec; collections LAZY. Explicitly choose and query-fetch per use; EAGER can still issue N+1. Avoid huge bidirectional graphs. Often model unidirectional many-to-one and query children separately.

### 2.8 Cascade and orphan removal

Cascade propagates entity operations (PERSIST, MERGE, REMOVE, etc.), not database cascade by itself. `CascadeType.ALL` is not default best. Cascading REMOVE from many-to-many/shared reference can delete shared data. Orphan removal deletes owned child removed from relationship; only for true aggregate ownership.

Database `ON DELETE` and ORM state may differ; coordinate. Bulk delete bypasses cascades/entity callbacks. Test actual SQL.

### 2.9 Lazy loading and proxies

LAZY loads when accessed, requiring open persistence context. Outside gives LazyInitializationException. Fix by fetching required data in transaction via fetch join/entity graph/projection, not making everything eager or keeping session open through view.

Proxies can affect runtime class, final methods and equals. Calling `toString`/JSON/debugger may initialize relationships unexpectedly. DTO map inside transaction with planned query.

### 2.10 N+1 queries

Load 100 claims (1 query), access each customer lazily (up to 100 queries) = 101. Detect SQL count/tracing. Fix with join fetch for to-one/bounded graph, entity graph, batch fetching, projection, explicit bulk query. Join-fetching multiple to-many can create Cartesian explosion and pagination issues.

Do not assert “EAGER fixes N+1”; provider may select each. Measure generated SQL/query plan.

### 2.11 JPQL, derived, native and projections

JPQL queries entities/fields (`select c from ClaimEntity c`), not table names. Spring method `findByTenantIdAndStatusOrderByCreatedAtDesc` derives. Long method names become unreadable; use `@Query`, specification/query DSL or custom repository. Native SQL for DB-specific/complex operations, with mapping/coupling.

DTO/interface projections fetch only needed columns; closed interface behavior/provider specifics. Constructor projection explicit. Entity query when updating aggregate; projection for read API. Parameter binding prevents injection; never concatenate user sort/filter into JPQL/SQL—allowlist.

### 2.12 Repository interfaces

`CrudRepository<T,ID>` CRUD; `ListCrudRepository`; `PagingAndSortingRepository`; `JpaRepository` adds JPA-specific flush/batch APIs. Understand method semantics: `findById` Optional; `getReferenceById` lazy reference; `deleteById`; `save` persist/merge choice.

Repository should be scoped to aggregate root, not expose arbitrary mutable entity graph. Service owns transaction and authorization. `existsBy...` followed by save races; database constraint authoritative.

### 2.13 Pagination and sorting

`Pageable` creates offset/limit plus sort. `Page<T>` usually executes content + count; `Slice<T>` fetches next indicator without count. Large offset grows expensive and shifts under concurrent inserts. Keyset/seek uses stable ordered cursor: `(created_at,id) < (?,?)` for descending.

Allowlist sort properties; client-supplied nested arbitrary paths can expose/slow. Stable tie-break ID. Do not paginate join-fetched collections naively.

The lab demonstrates simple ID keyset after cursor.

### 2.14 Optimistic locking

`@Version` adds version predicate: `update ... set ..., version=1 where id=? and version=0`; zero rows → OptimisticLockException. It detects lost update, not prevents all business races across rows/external systems. Decide retry/reload/conflict; blind retry may overwrite user decision. Include version/ETag at API boundary.

Pessimistic locks (`PESSIMISTIC_WRITE`) block competitors and require transaction/timeouts/order; can deadlock/reduce throughput. Use when conflict cost/probability justifies and DB semantics known.

### 2.15 Transactions primer

Spring service method `@Transactional` opens/joins transaction via proxy. EntityManager bound to transaction; repository methods participate. Runtime exception rollback default; checked exception different. Self-invocation/proxy/propagation detailed in existing advanced lesson.

Keep transaction around DB state transition, not remote call/user think time. Isolation/database determines anomalies. Lazy mapping must happen inside transaction but serialization outside with DTO.

### 2.16 JDBC connection pool

DataSource pool (commonly HikariCP in Boot) lends limited connections. Transaction holds one; long remote calls consume pool. Pool size follows measured DB capacity/concurrency, not number of threads. Timeout waiting for connection reveals saturation/leak/long transaction. Always close JDBC resources (template/JPA manages when used correctly).

Open Session in View may keep persistence context through web request and allow queries during serialization; Boot defaults/version warning vary. Disable/prevent via DTO/fetch design for predictable transactions.

### 2.17 Auditing and timestamps

Spring Data auditing `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy` needs configuration/AuditorAware. It is metadata convenience, not tamper-evident security audit. Database time versus application Clock must be chosen. Bulk updates may skip entity listeners/auditing.

Use Instant for event timestamps and DB defaults where appropriate; tests verify precision/truncation/zone. Security actor from trusted context.

### 2.18 Testing repositories

`@DataJpaTest` configures JPA slice, often transactional rollback; by default embedded DB replacement can differ. Use PostgreSQL Testcontainers and disable replacement for target fidelity. Test mappings, constraints, JPQL, pagination, locking, cascade and generated SQL/query count.

Beware tests that never flush: invalid constraint may not surface. `saveAndFlush`/EntityManager flush then clear, reload to prove DB mapping rather than same first-level object.

### 2.19 Concept lab

```bash
javac JpaConceptLab.java && java JpaConceptLab
```

It models first-level identity, versioned lost-update detection and keyset pagination without claiming to implement Hibernate.

## 3. WORKED PROBLEMS

### Problem 1 — Layers (easy)

Differentiate JPA/Hibernate/Spring Data. **Solution:** specification, implementation, repository abstraction using JPA. **Mistake:** call Spring Data ORM provider.

### Problem 2 — Merge (easy)

`em.merge(detached); detached.setName(...)`. Persisted? **Solution:** merge returns managed copy; later detached change not tracked. Use returned entity. **Mistake:** merge reattaches same instance.

### Problem 3 — Flush (medium)

Unique error appears at commit not save. **Solution:** SQL/constraint deferred until flush; force flush only where boundary needs early detection and still handle commit. **Mistake:** save guarantees DB write.

### Problem 4 — N+1 (medium)

50 claims then customer name each =? **Solution:** 1 + up to 50 selects. Projection/fetch join/entity graph/batch depending cardinality. **Mistake:** LAZY alone is efficient.

### Problem 5 — Cascade (medium)

Many claims share Provider; CascadeType.REMOVE from claim→provider. **Solution:** deleting one may delete shared provider/fail FK; remove cascade. **Mistake:** ALL for convenience.

### Problem 6 — Page count (medium)

Endpoint needs “has next,” count takes 2s. **Solution:** Slice or keyset with limit+1; avoid total count. **Mistake:** Page always needed.

### Problem 7 — Optimistic conflict (hard)

Two reviewers load v3; both update. **Solution:** first writes v4; second `where version=3` affects 0 and gets conflict. Reload/present conflict, not blind overwrite. **Mistake:** version serializes external actions.

### Problem 8 — Entity JSON (hard)

Controller returns entity after transaction, lazy collection. **Solution:** LazyInitializationException or queries during OSIV/serialization/cycle. Fetch projection/DTO in service transaction. **Mistake:** make collection EAGER.

### Problem 9 — Repository test (hard)

H2 test passes PostgreSQL JSONB query. Production fails. **Solution:** dialect/type/function differences; test target PostgreSQL container and migration. **Mistake:** in-memory DB proves target SQL.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring Boot Data JPA auto-configures DataSource, EntityManagerFactory, transaction manager and repositories when classpath/properties satisfy conditions. Managed Hibernate version matters; SQL generation and defaults change across upgrades.

PostgreSQL unique composite tenant key, timestamptz and explain plans must be tested directly. Healthcare/fintech use append-only audit/ledger tables that often should not be modeled as freely cascading mutable graphs.

The concept lab's first-level map/version arithmetic mirrors invariants but cannot prove provider behavior. The correct executable evidence is a target database integration suite.

## 5. COMPARISON TABLE

| Choice | Use | Strength | Boundary |
|---|---|---|---|
| JDBC | explicit SQL/control | predictable/performance | mapping boilerplate |
| Spring JDBC | SQL with templates | less boilerplate | manual mapping |
| JPA/Hibernate | aggregate lifecycle | dirty checking/relations | hidden SQL/complex graphs |
| Spring Data JPA | repository/query abstraction | rapid conventions | method magic/ORM limits |
| entity query | updates/aggregate | managed lifecycle | overfetch |
| DTO projection | read APIs | exact columns | provider/query mapping |
| LAZY | defer relation | avoids unused load | context/N+1 |
| EAGER | always requested | simple small relation | N+1/overfetch remains |
| optimistic lock | detect conflict | read-heavy low conflict | retry/user resolution |
| pessimistic lock | block conflict | short critical DB work | deadlock/throughput |
| Page | content + total | UI needs total | count cost |
| Slice/keyset | next page | scalable feed | no arbitrary page/total |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. JPA is Hibernate—JPA specification, Hibernate implementation.
2. Repository save always INSERT—it may merge and SQL can wait until flush.
3. Flush equals commit—it synchronizes inside transaction.
4. First-level cache is Redis—it is per persistence context identity map.
5. Merge reattaches argument—it copies and returns managed.
6. EAGER makes one query—provider may still N+1/overfetch.
7. LAZY fixes performance—it can N+1/fail outside context.
8. Cascade ALL always convenient—remove can destroy shared data.
9. Bidirectional relation updates itself—maintain both sides/owning mapping.
10. Exists then save prevents duplicate—race; DB constraint.
11. H2 equals PostgreSQL—types, SQL, isolation and planner differ.
12. Entity is ideal API response—it leaks persistence/lazy graph.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- JDBC API; JPA spec; Hibernate provider; Spring Data repository layer.
- Entity states transient, managed, detached, removed.
- Persistence context = unit-of-work + identity map; EntityManager not thread-safe.
- Dirty checking writes at flush; flush ≠ commit.
- merge returns managed copy; use return.
- Plan relationships/owning side; cascade only aggregate ownership.
- LAZY/EAGER do not replace query design; detect/fix N+1.
- Projection for reads, entity for aggregate mutation.
- DB constraints authoritative; app checks for UX.
- Page does count; Slice/keyset for scalable next.
- @Version detects stale write; decide conflict behavior.
- Repository tests flush+clear+reload on target DB/migrations.

## 8. PRACTICE SET FOR SELF-TEST

1. Distinguish JDBC, JPA, Hibernate, Spring Data JPA.
2. Name four entity states.
3. What does persistence context guarantee for repeated ID find?
4. Difference flush and commit?
5. Why use returned result from merge?
6. Define owning side in bidirectional relation.
7. Explain N+1 and two fixes.
8. Page versus Slice?
9. How does @Version detect lost update?
10. Why test PostgreSQL rather than H2?

## 9. CURATED RESOURCES

1. [Jakarta Persistence 3.2 Specification](https://jakarta.ee/specifications/persistence/3.2/) — authoritative entity lifecycle, mapping, persistence context and query semantics.
2. [Hibernate ORM User Guide](https://docs.jboss.org/hibernate/orm/current/userguide/html_single/Hibernate_User_Guide.html) — provider-specific fetching, batching, locking and SQL behavior.
3. [Spring Data JPA Reference](https://docs.spring.io/spring-data/jpa/reference/) — repositories, query methods, projections, locking and auditing.
4. [Spring Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction.html) — transaction abstraction underpinning repository work.
5. [PostgreSQL Documentation: Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) — authoritative database invariants and uniqueness.
6. **Vlad Mihalcea, _High-Performance Java Persistence_, Chapters 1–13** — SQL/connection/persistence-context/fetch performance depth.
7. **Christian Bauer et al., _Java Persistence with Spring Data and Hibernate_, 2nd ed., Parts 1–3** — comprehensive ORM/Spring Data progression.
8. [Testcontainers PostgreSQL Module](https://java.testcontainers.org/modules/databases/postgres/) — target DB integration setup.
9. [Spring Data Commons repository interfaces](https://docs.spring.io/spring-data/commons/reference/repositories/core-concepts.html) — exact repository hierarchy/concepts.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Relational Modeling/PostgreSQL** — schema/constraints/indexes remain foundation.
2. **Spring Boot Fundamentals** — DataSource/JPA/repository auto-config.
3. **Spring Web** — DTO/service boundary before persistence.
4. **Collections/Generics** — repository types/entity collections.

### After

1. **Spring Core and Transactions advanced** — proxy propagation/isolation/rollback/outbox.
2. **Transactions and Locking** — database anomalies/deadlocks/retries deeply.
3. **Indexes and Query Plans** — optimize generated/explicit SQL.
4. **Data Migrations** — evolve entity/schema compatibly.
5. **Testing and Resilience** — integration, retry and failure semantics.

---ANSWER KEY BELOW---

1. JDBC low-level database API; JPA ORM specification; Hibernate JPA implementation; Spring Data JPA repository/query abstraction atop JPA.
2. Transient/new, managed/persistent, detached, removed.
3. Within one context, one managed identity instance per entity identity and repeated find can avoid another query unless state cleared/changed externally.
4. Flush sends/synchronizes SQL with DB inside transaction; commit makes transaction durable/visible per isolation and can still fail.
5. Merge copies state into and returns managed entity; argument remains detached.
6. Mapping side that owns foreign key/join table update; inverse uses mappedBy. Maintain both Java sides for consistency.
7. One parent query followed by one child query per row. Fix via projection/fetch join/entity graph/batch/bulk query depending graph/cardinality.
8. Page includes total and usually count; Slice indicates next without total; keyset scales deep traversal better than offsets.
9. Update includes expected old version in WHERE and increments; zero rows means another transaction changed/deleted it.
10. H2 differs in dialect, types, functions, constraints, locking/isolation/planner; target DB plus real migrations proves actual behavior.
