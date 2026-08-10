# Spring Core and Transactions — Complete Study Resource

**Parent:** `02-java-spring`  
**Child:** `03-spring-core-transactions`  
**Baseline:** Spring Framework 6.2/7 proxy concepts; verify deployed Boot/Framework versions

## 1. FOUNDATIONS

### Inversion of control

Without a container, a service constructs dependencies itself:

```java
class PaymentService {
  private final Repository repository = new PostgresRepository(...);
}
```

Construction, configuration and business logic become coupled. **Inversion of Control (IoC)** moves object creation/wiring to an external mechanism. **Dependency injection (DI)** is IoC where an object declares collaborators through constructor/factory/setter parameters and a container supplies them. Spring calls managed objects **beans** and stores creation/wiring metadata as bean definitions in an `ApplicationContext`.

DI exists to separate “what the service does” from “how its dependencies are located/configured.” Constructor injection makes requirements explicit, supports immutability and plain unit testing. A **service locator** pulls dependencies from a global registry and hides them; DI pushes them in.

Spring began in the early 2000s as a lighter alternative to heavyweight enterprise Java components, emphasizing POJOs, DI and consistent abstractions. It later added Boot’s convention/auto-configuration, but Spring Framework and Spring Boot are distinct: Framework supplies the container/AOP/data abstractions; Boot chooses defaults, discovers configuration and packages applications.

### Transactions

A database **transaction** groups operations into one atomic unit under a chosen isolation level. Spring does not invent database ACID; it coordinates transaction begin/commit/rollback and binds resources through a `PlatformTransactionManager` abstraction for JDBC/JPA/JTA and others.

Declarative `@Transactional` works primarily through **AOP proxies**. A caller invokes a proxy; transaction advice opens/joins a transaction, invokes target, then commits or rolls back. Calls that bypass the proxy bypass advice. Understanding this mechanism prevents the classic “annotation present but no transaction” failure.

### Core terms

A bean **scope** controls instance lifetime. Default singleton means one instance per bean definition per Spring container, not one per JVM/classloader/global world. Prototype creates on each retrieval, but Spring does not automatically manage complete destruction lifecycle for prototypes. Web request/session/application/websocket scopes need a web context.

An **advice** is behavior around a method; a **pointcut** selects join points; a Spring AOP **proxy** is an object intercepting calls before delegating to target. JDK dynamic proxies implement interfaces; class-based proxies subclass the target and cannot advise final/private/non-overridable methods.

**Propagation** determines how a method relates to an existing transaction. A **logical transaction scope** is annotation/method-level; a **physical transaction** is the resource transaction/connection. **Isolation** governs concurrent transaction anomalies. **Rollback-only** marks physical transaction unable to commit.

## 2. CORE MECHANICS

### 2.1 Bean discovery and configuration

Beans can come from component scanning (`@Component`, `@Service`, `@Repository`, `@Controller`) or `@Bean` factory methods in `@Configuration`. Component stereotypes communicate role; `@Repository` also participates in persistence exception translation where configured. Explicit `@Bean` suits third-party types and complex construction.

Boot auto-configuration is conditional configuration activated by classpath, properties and existing/missing beans. It is not magic: inspect condition evaluation reports and configuration metadata. User beans commonly override/back off defaults by conditions, but exact override rules and bean naming are version/config dependent.

### 2.2 Constructor injection

Prefer one constructor with final fields:

```java
@Service
final class PaymentService {
  private final PaymentRepository repository;
  PaymentService(PaymentRepository repository) { this.repository=repository; }
}
```

Spring can use the sole constructor without `@Autowired`. Field injection hides mandatory dependencies, prevents final fields and complicates plain construction. Setter injection fits optional/reconfigurable dependencies but allows incomplete intermediate state.

Constructor cycles A→B→A cannot be constructed normally and signal poor boundaries. Lazy/provider injection can break mechanics but may hide design coupling. Extract a third service or event boundary where appropriate.

### 2.3 Scope mismatch

Injecting a prototype directly into singleton resolves it once at singleton creation; it does not create one per call. Use `ObjectProvider<T>`, factory method or scoped proxy for on-demand retrieval. Injecting request scope into singleton uses a proxy that resolves current request target at method call. Calling it outside request context fails.

Singleton beans serve concurrent requests. Keep them stateless or synchronize mutable state; container singleton scope does not imply thread safety.

### 2.4 Lifecycle

Container constructs, injects, runs aware/post-processors, initialization callbacks (`@PostConstruct`, `InitializingBean`, configured method), then exposes bean; on shutdown runs destruction (`@PreDestroy`, `DisposableBean`, method) for managed singleton-like lifecycles. Avoid relying on transactional/AOP behavior during `@PostConstruct`: proxy may not yet be the call path. Start asynchronous components via lifecycle abstractions and stop them cleanly.

### 2.5 AOP proxy mechanics

External call `proxy.method()` crosses advice. Inside target, `this.otherMethod()` invokes target directly and bypasses proxy. Therefore `@Transactional`/`@Cacheable`/`@Async` on `otherMethod` will not activate under default proxy mode through self-invocation.

Best fix is refactor transactional boundary into another bean and call it externally. Self-injection is more coupled; `AopContext.currentProxy()` is discouraged. AspectJ weaving can intercept self-invocation but changes tooling/runtime model.

JDK proxy exposes interfaces. Class proxy cannot advise final class/method/private method. Do not annotate private helper expecting transaction.

### 2.6 Transaction boundary

Place transaction on service operation that enforces one database invariant, not each repository call separately. Keep transaction short: validate local data, read/update DB, enqueue outbox in same transaction, commit. Do not hold connection/locks across slow HTTP calls. Remote API cannot join ordinary local Spring transaction.

```java
@Transactional
public Payment create(Command c) {
  // idempotency insert + payment + outbox
}
```

Spring default `@Transactional`: propagation REQUIRED, isolation DEFAULT, read-write, underlying/default timeout, rollback on `RuntimeException`/`Error`, not checked exception. Customize `rollbackFor` deliberately.

### 2.7 REQUIRED

If no transaction, REQUIRED begins one; otherwise joins existing physical transaction. Inner logical scope can mark rollback-only. If outer catches inner runtime exception and tries commit, Spring throws `UnexpectedRollbackException` so caller is not falsely told commit succeeded.

Inner declarations of isolation/read-only/timeout normally do not create new physical characteristics when joining. Transaction manager validation can reject mismatches.

### 2.8 REQUIRES_NEW

Suspends outer transaction and opens independent physical transaction/resource. Inner commit survives outer rollback. Useful rarely for independent audit, but not a universal fix. Outer retains its connection while inner needs another. Official Spring docs warn pool can exhaust/deadlock unless sized beyond concurrent outer transactions by at least one for such usage.

It also breaks atomicity: audit may say success before outer fails. Decide semantics.

### 2.9 NESTED and other propagation

NESTED typically uses JDBC savepoints within one physical transaction; inner rollback can return to savepoint while outer continues. Support depends on transaction manager/resource. It is not same as independent commit.

SUPPORTS joins if present else none; MANDATORY fails without transaction; NOT_SUPPORTED suspends; NEVER fails if transaction exists. Choose from semantics, not memorization.

### 2.10 Isolation

Standard levels address anomalies:

- READ_UNCOMMITTED permits dirty reads;
- READ_COMMITTED prevents dirty reads but repeated reads may change;
- REPEATABLE_READ preserves repeated row reads under DB semantics but phantom/write-skew details vary;
- SERIALIZABLE approximates serial outcome, often via locking/serialization failures.

Database MVCC implementations differ. PostgreSQL READ_UNCOMMITTED behaves as READ_COMMITTED; its REPEATABLE READ prevents some anomalies beyond standard but serializable is needed for full serializable guarantees. Isolation alone does not replace unique constraints/atomic updates.

### 2.11 Read-only and timeout

`readOnly=true` is a hint/optimization depending on transaction manager/provider; do not treat it as universal database write prohibition. Timeouts often apply when underlying operations participate; configure JDBC/network timeouts and end-to-end deadlines too. Transaction timeout rollback cannot undo already completed remote calls.

### 2.12 Exceptions and rollback

Unchecked default rollback means a checked business exception may commit unless configured. Catching an exception inside transactional method prevents advice from seeing it unless transaction is marked rollback-only or exception rethrown. Broad `rollbackFor=Exception.class` can be appropriate but must match business semantics.

Never catch database error, continue using a transaction already marked rollback-only, and assume commit. Test rollback behavior with integration tests.

### 2.13 Transaction-bound events and outbox

`@TransactionalEventListener` can run by transaction phase, but an in-process after-commit handler can be lost if process crashes after commit before side effect. For durable cross-system publication, insert outbox row with business data in same DB transaction; a relay publishes at least once; consumers deduplicate.

`@Async` changes thread and transaction context does not automatically follow. A transaction is usually thread-bound in imperative Spring. Reactive transactions use Reactor context, a different model.

### 2.14 JPA persistence context

Within transaction, JPA first-level cache tracks managed entities and dirty changes flush at/before commit. `save` may not issue immediate SQL. Lazy associations require open persistence context or explicit fetching. Keeping “Open Session in View” can hide N+1 queries and extend persistence context into web rendering; prefer explicit transaction/fetch boundaries.

Bulk update bypasses managed entity state; clear/refresh to avoid stale objects. Flush proves SQL sent, not committed.

## 3. WORKED PROBLEMS

### Problem 1 — Constructor injection

**Statement.** Service has repository, HTTP client and optional metrics. Design injection.

**Solution.** Constructor-inject required repository/client as final interfaces. Inject a metrics implementation/no-op explicitly rather than nullable field. Plain tests construct service. No hidden context lookup.

**Mistake caught.** Field injection and reflection-only tests.

### Problem 2 — Prototype in singleton

**Statement.** Prototype RequestBuilder injected into singleton is reused. Why?

**Solution.** Dependency resolved once during singleton creation. Inject `ObjectProvider<RequestBuilder>` and call `getObject()` per need, or remove mutable builder state/create normally. Prototype scope does not imply per-method automatically.

**Mistake caught.** Confusing dependency scope with injection frequency.

### Problem 3 — Self-invocation

**Statement.** `outer()` calls `this.inner()` where inner is `@Transactional(REQUIRES_NEW)`.

**Solution.** Under default proxy mode call bypasses proxy, so REQUIRES_NEW does not activate. Move inner to separate bean and inject/call it. Test with transaction status/database outcome.

**Mistake caught.** Assuming annotation rewrites method body.

### Problem 4 — Checked exception

**Statement.** Transaction writes then throws checked `FraudReviewException`; default behavior?

**Solution.** By default checked exception does not trigger rollback, so commit may occur if it leaves proxy normally as checked exception. Configure `rollbackFor=FraudReviewException.class` or make semantic unchecked exception, based on desired outcome.

**Mistake caught.** All exceptions roll back.

### Problem 5 — UnexpectedRollback

**Statement.** Outer REQUIRED calls inner REQUIRED; inner throws runtime and marks rollback-only; outer catches and returns success.

**Solution.** Same physical transaction cannot commit. At outer commit Spring raises `UnexpectedRollbackException`. Do not swallow and promise success; restructure exception handling/transaction boundaries.

**Mistake caught.** Catching exception resets transaction.

### Problem 6 — REQUIRES_NEW pool

**Statement.** Pool10; ten threads hold outer connections then call REQUIRES_NEW.

**Solution.** Each waits for eleventh connection but all ten are held, producing pool starvation/deadlock until timeout. Need >concurrent outer resources or avoid pattern/outbox/separate flow. Official docs explicitly warn.

**Mistake caught.** New transaction is “free.”

### Problem 7 — Remote call inside transaction

**Statement.** Transaction locks order, calls payment gateway for8 seconds, then commits.

**Solution.** Lock/connection held8 seconds, increasing blocking and unknown outcome on timeout. Prefer state machine: commit pending order/outbox, invoke idempotent gateway outside DB lock, reconcile result in new transaction. Exact flow depends on business consistency.

**Mistake caught.** Local transaction makes remote call atomic.

### Problem 8 — Duplicate payment

**Statement.** Two concurrent requests share idempotency key.

**Solution.** Unique constraint `(tenant,key)` plus request hash. Transaction attempts insert; one wins. Duplicate same hash returns stored/in-progress result; different hash conflict. Check-then-insert alone races even under READ_COMMITTED.

**Mistake caught.** `@Transactional` automatically serializes all requests.

### Problem 9 — N+1

**Statement.** Load100 orders then access each lazy customer; observe101 selects.

**Solution.** Initial query plus100 lazy queries. Use projection/fetch join/entity graph or batch fetch appropriate to cardinality/pagination. Verify SQL and plan. Do not blindly fetch multiple collections causing Cartesian explosion.

**Mistake caught.** Repository method count equals SQL count.

## 4. REAL-WORLD / APPLIED CONTEXT

### Proxy evidence

The included `ProxyTransactionLab.java` uses JDK dynamic proxy to demonstrate exact call path. External `proxy.outer()` records one interception; target’s `this.inner()` records no second transaction advice. External `proxy.inner()` is intercepted. It also simulates staged commit/rollback. This is not Spring’s transaction manager, but it verifies the proxy mechanism behind the documented self-invocation boundary.

### Connection capacity

At200 transactions/s holding a connection50 ms, Little’s Law suggests10 busy connections average. If remote work extends hold to500 ms, average becomes100—before variance/headroom. Transaction scope is a capacity decision, not only correctness annotation.

### Outbox

Production payment/order systems commonly write business row and outbox atomically, then publish with CDC/poller. Relay may publish duplicates; event ID plus consumer transaction provides idempotent effect. Spring transaction synchronization alone cannot guarantee crash-safe external delivery.

## 5. COMPARISON TABLE

| Propagation | Existing transaction | Physical resource | Commit relation | Main risk/use |
|---|---|---|---|---|
| REQUIRED | joins | same | inner rollback-only affects outer | normal service facade |
| REQUIRES_NEW | suspends | new | independent | pool exhaustion, broken atomicity |
| NESTED | savepoint | same | partial rollback, outer final commit | JDBC/savepoint support |
| SUPPORTS | joins if present | maybe none | context-dependent | reads tolerant of no tx |
| MANDATORY | requires | existing | fail if absent | enforce caller boundary |
| NOT_SUPPORTED | suspends | none | nontransactional section | avoid long resource hold |

| Injection | Strength | Risk |
|---|---|---|
| constructor | explicit/immutable/testable | cycles exposed |
| setter | optional/reconfigurable | incomplete mutable state |
| field | concise | hidden dependency, poor plain tests |
| provider/scoped proxy | resolves short/prototype scope | runtime/context coupling |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Singleton means thread-safe.** Scope does not synchronize mutable fields.
2. **Prototype injected means per-call.** Injection into singleton happens once.
3. **Annotation always executes.** Proxy must intercept call.
4. **Private/final/self-invoked transactional method works.** Proxy limitations bypass advice.
5. **All exceptions rollback.** Default unchecked/Error only.
6. **Catch exception and transaction is healthy.** It may be rollback-only.
7. **REQUIRES_NEW fixes everything.** It uses independent connection/commit and may exhaust pool.
8. **Read-only forbids writes universally.** Often hint/provider behavior.
9. **Transaction spans HTTP/Kafka automatically.** Local context does not cross remote boundary.
10. **Flush equals commit.** SQL execution and durable commit differ.
11. **Transactional event guarantees delivery.** Process crash can lose in-memory handler.
12. **@Async carries transaction.** Imperative transaction is thread-bound.
13. **@Transactional serializes requests.** Isolation/constraints determine conflicts.
14. **Lazy loading is free.** It can create N+1 and context leaks.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the complete resource.

- IoC container creates/wires beans; DI pushes explicit dependencies.
- Prefer constructor injection/final fields.
- Singleton=one per bean definition/container, not thread-safe guarantee.
- Proxy external calls activate AOP; self-invocation bypasses.
- Default transaction: REQUIRED, DEFAULT isolation, read-write, unchecked rollback.
- REQUIRED joins physical tx; rollback-only can cause UnexpectedRollback.
- REQUIRES_NEW consumes independent connection/commit.
- NESTED uses savepoint where supported.
- Keep DB transaction short; no slow remote call while holding resources.
- Constraints/atomic SQL protect invariants; annotation alone does not.
- Outbox for durable external publication.
- Verify SQL, transaction outcome, proxy call path and pool waits.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain singleton bean concurrency for mutable `ArrayList` field.
2. Refactor A→B→A constructor cycle.
3. Determine transaction behavior when public nontransactional method self-calls transactional public method.
4. Outer REQUIRED calls REQUIRES_NEW audit then fails: what persists?
5. Pool20 and15 outer threads each call two sequential REQUIRES_NEW operations: minimum immediate connection need and risk.
6. Design atomic inventory decrement at READ_COMMITTED.
7. Checked `IOException` after DB write: configure/justify rollback policy.
8. Compare transactional event after-commit with outbox under crash.
9. Explain why `@Transactional` on `@PostConstruct` is unreliable.
10. Diagnose JPA bulk update followed by reading already-managed entity.

## 9. CURATED RESOURCES

1. **Spring Framework Reference, “IoC Container,” “Dependencies,” and “Bean Scopes.”** Exact DI, bean metadata, lifecycle and scope behavior.
2. **Spring Framework Reference, “Proxying Mechanisms.”** Definitive JDK/CGLIB and self-invocation limitations.
3. **Spring Framework Reference, “Using @Transactional.”** Defaults, rollback rules and proxy-mode boundaries.
4. **Spring Framework Reference, “Transaction Propagation.”** Physical/logical REQUIRED, REQUIRES_NEW pool warning and NESTED savepoints.
5. **Spring Framework Reference, “Transaction Strategies.”** PlatformTransactionManager abstraction and definitions.
6. **Spring Data JPA Reference, transactionality and locking chapters.** Repository defaults and JPA integration.
7. **Jakarta Persistence specification, transactions/persistence context sections.** Provider-neutral entity state, flush and locking semantics.
8. **PostgreSQL documentation, Transaction Isolation.** Concrete MVCC/isolation behavior for your target database.
9. **Richardson, *Microservices Patterns*, Transactional Outbox/Saga chapters.** Cross-service consistency patterns beyond local Spring transactions.

## 10. RELATED TOPICS BRIDGE

### Before

1. **JVM/Concurrency.** Singleton sharing, ThreadLocal transactions and proxy runtime require these foundations.
2. **Database transaction basics.** Spring coordinates rather than defines ACID/isolation.

### After

1. **API Design and Security.** Controllers invoke transactional services; authentication/authorization boundaries matter.
2. **Testing and Resilience.** Verify proxy, rollback, SQL, timeout and pool behavior with integration tests.
3. **PostgreSQL Transactions/Locks.** Deep database anomalies and constraints determine actual correctness.
4. **Distributed Failure Semantics.** Outbox/idempotency handle what local transactions cannot.

---ANSWER KEY BELOW---

1. One instance serves many threads; ordinary ArrayList mutations race/corrupt/visibility fails. Prefer stateless bean, concurrent structure or lock around full invariant.
2. Identify shared responsibility C and inject into both, invert one dependency via event/callback, or merge cohesive services. Lazy/provider merely postpones cycle and needs justification.
3. Self-call bypasses proxy; annotation on inner does not start transaction under default proxy mode. Externalize to another bean/proxy call.
4. Audit independent physical transaction commits and remains even though outer rolls back. Ensure audit semantics records attempt/failure accurately.
5. At one time each outer holds15 connections and each active inner needs15 more=30, despite sequential two calls. Pool20 can starve; docs recommend pool exceeding concurrent threads for REQUIRES_NEW, but redesign often better.
6. `UPDATE inventory SET qty=qty-:n WHERE sku=:sku AND qty>=:n`; affected row1 success,0 insufficient/missing. Transaction plus constraint prevents negative; handle retries/deadlocks.
7. Default would commit. Use `@Transactional(rollbackFor=IOException.class)` if failure means whole operation invalid, or catch/record if DB change intentionally persists. Policy follows business invariant.
8. After-commit in-process event can vanish on crash after commit. Outbox row commits with business data and relay retries; duplicates require consumer idempotency.
9. Bean may not yet be invoked through fully initialized proxy during lifecycle callback. Move startup operation to another bean/lifecycle event through proxy or use transaction template deliberately.
10. Bulk update bypasses persistence context, so managed entity remains stale. Clear/refresh context or use modifying-query clear behavior intentionally; understand flush ordering.
