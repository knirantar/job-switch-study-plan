# Testing and Resilience — Complete Study Resource

**Parent:** `02-java-spring`  
**Child:** `05-testing-resilience`  
**Goal:** prove correctness and controlled failure, not merely increase test count

## 1. FOUNDATIONS

### Why tests exist

Software changes continually. A test is executable evidence that a behavior holds under specified conditions. It reduces regression risk, documents contracts and enables refactoring. It cannot prove absence of all bugs unless the state space is exhaustively verified; confidence depends on what behavior, boundary and failure modes the tests actually cover.

**Verification** asks whether we built the system according to specification. **Validation** asks whether the system solves the right user problem. A unit test can verify a calculation while missing that business rule itself is wrong.

A **test oracle** decides expected result. An **assertion** compares observation to oracle. A **fixture** is test setup/state. A **test double** substitutes a collaborator: dummy fills parameter, stub returns canned result, fake supplies working simplified implementation, spy records calls, mock verifies programmed interactions. Overusing mocks couples tests to implementation order and allows a fictional system where components agree only with mocks.

### Why resilience is part of testing

Distributed dependencies fail slowly, partially and ambiguously. Resilience means a system maintains acceptable service and recovers under expected faults. It is not “never fails.” Techniques—timeouts, retries, circuit breakers, bulkheads, rate limits, fallback—change behavior and can cause harm when stacked blindly. A retry multiplies load during outage; a fallback can serve stale/unsafe data; a circuit breaker can hide recovery.

Testing and resilience belong together because failure policies must be proven with deterministic tests and exercised under realistic network/database behavior. Happy-path unit coverage does not validate timeout budgets, duplicate requests, pool exhaustion or rollback.

### Quality vocabulary

A **regression** reintroduces broken behavior. **Flaky test** passes/fails without relevant code change because of time, order, concurrency, external state or randomness. **Coverage** reports executed code branches/lines, not correctness. **Mutation testing** alters code to see whether tests detect changes; surviving mutations reveal weak or equivalent assertions.

A **timeout** limits waiting. A **deadline** is absolute remaining end-to-end time. A **retry** repeats a failed operation. **Backoff** spaces attempts; **jitter** randomizes to prevent synchronized retry storms. A **circuit breaker** stops calls after failure evidence and probes recovery. A **bulkhead** isolates resource capacity. **Fallback** returns degraded alternative. **Load shedding** rejects work to protect useful service.

## 2. CORE MECHANICS

### 2.1 Test pyramid and portfolio

Unit tests are numerous, fast and isolated. Integration tests validate boundaries such as PostgreSQL/JPA, HTTP serialization or Spring proxy transactions. Contract tests validate consumer/provider schemas/semantics. End-to-end tests exercise deployed paths but are slow and diagnostically broad. Load/soak/chaos/security tests target nonfunctional behavior.

The “pyramid” is a cost heuristic, not fixed percentages. Risk determines portfolio. A repository using PostgreSQL-specific SQL needs real-Postgres integration; mocking EntityManager cannot prove it. A pure pricing function deserves exhaustive unit/parameterized tests.

### 2.2 Unit test structure

Arrange inputs/collaborators, act once, assert externally visible outcome. A strong name encodes condition and result: `withdraw_rejectsWhenBalanceInsufficient_withoutChangingBalance`. Test one behavior concept, not necessarily one assertion.

Test boundaries/partitions: zero, min/max, just below/at/above threshold, empty/single/many, duplicates, null if allowed, overflow, invalid state. Parameterized tests reduce duplication while retaining clear case names.

Do not expose private methods only for tests. Test through public behavior or extract cohesive collaborator.

### 2.3 State versus interaction testing

Prefer state/output assertions when possible. Verify interactions when interaction **is** contract: one payment gateway call with idempotency key, no call on validation failure. Avoid asserting every getter/order/internal helper. A refactor should not break behavior-preserving tests.

Mockito default returns can hide missing setup; strict stubbing helps. Never mock value objects unnecessarily. A fake repository can support unit domain tests but is not substitute for SQL constraint/isolation tests.

### 2.4 Spring slice and MVC tests

Plain unit test constructs controller/service directly. `MockMvc` exercises `DispatcherServlet`, mappings, binding, conversion, validation and exception handling without live HTTP server. It does not reproduce every servlet-container/network behavior. Web-layer slice tests load focused components; full `@SpringBootTest` loads broad context and is slower.

Use real end-to-end HTTP tests for filters/TLS/proxy/container/client behavior as required. Spring docs explicitly distinguish MockMvc mock servlet behavior from live server.

### 2.5 Database integration

Use same database engine/version for SQL, locking, isolation and types. H2 differs from PostgreSQL in syntax, MVCC, JSON, constraints and query planner. Testcontainers runs a real disposable DB with known state, at startup cost.

Test migrations from empty and previous schema; constraints under concurrency; transaction rollback; indexes/plans for critical queries. Test transaction annotations through Spring proxy, not by directly `new`ing service.

Transactional test rollback can hide after-commit behavior and production commit constraints. Commit explicitly when testing outbox/event/constraint timing.

### 2.6 Contract tests

Provider OpenAPI/schema tests verify syntax. Consumer-driven contracts capture actual consumer expectations. Compatibility tests cover optional/missing fields, unknown enum values, Problem Details and idempotency. A contract passing does not prove authorization/business semantics; add security tests.

### 2.7 Deterministic time/randomness/concurrency

Inject `Clock` instead of calling `Instant.now()` throughout. Inject deterministic random/id generators. Use fake scheduler/sleeper for retries; do not make unit suite wait real seconds. Avoid `Thread.sleep` for ordering; use latches/barriers/futures and bounded awaits.

JUnit preemptive timeout can execute in separate thread and break Spring ThreadLocal transaction context; current JUnit guidance distinguishes same-thread timeout. Understand mechanism before using.

Concurrency correctness needs invariant/stress tools such as jcstress plus deterministic orchestrated tests; one repeated unit test is evidence, not proof.

### 2.8 Property-based and mutation tests

Property-based testing generates cases and shrinks failure. Examples: sorting output is ordered/permutation; idempotent request repeated yields same resource; encode/decode round trip; balance never negative. It finds boundaries humans omit.

Mutation testing changes `>` to `>=`, removes call or alters return. If tests still pass, either tests are weak, mutation equivalent, or behavior unspecified. Mutation score is diagnostic, not target to game.

### 2.9 Timeouts and deadline budgeting

Every remote call needs connect/read/overall timeout shorter than caller deadline. If ingress deadline800 ms, allocate budget across local processing and downstream, retaining response margin. Nested layers must use remaining deadline, not each reset800 ms. Timeout outcome can be unknown for side effects.

Timeout alone does not cancel remote computation reliably. Propagate cancellation where protocol/client supports and design idempotency/reconciliation.

### 2.10 Retries

Retry only transient failures and safe operations. DNS/config/auth/validation 4xx generally not retryable; 429/503 may be with `Retry-After` and deadline. Writes require idempotency.

Use capped exponential backoff with jitter. Base100 ms yields nominal100,200,400; full jitter samples `[0,delay]`. Total worst nominal waits before fourth attempt700 ms plus operation times—must fit deadline. Maximum attempts includes initial call in Resilience4j default semantics.

Avoid retry amplification: gateway3× service3× DB3× can create up to27 DB attempts for one request. Retry at one appropriate layer with budgets/metrics.

### 2.11 Circuit breaker

Closed permits calls and records outcomes. When failure/slow-call threshold over a minimum window is exceeded, open rejects quickly. After wait duration, half-open permits limited probes; success closes, failure reopens.

Breaker is not retry and not rate limiter. Configure per dependency/operation where failure behavior correlates; one global breaker lets failing endpoint disable healthy ones. Count only relevant failures—business 404 may be success from dependency health perspective. Observe state transitions/rejections.

### 2.12 Bulkheads

Semaphore bulkhead caps concurrent calls; thread-pool bulkhead uses separate executor/queue. At100 RPS and200 ms dependency time, Little’s Law implies20 average in flight; choose permits with measured tails/headroom and global replicas. Reject/wait only within deadline. Separate critical and optional workload pools prevents noisy neighbor.

### 2.13 Rate limiting and load shedding

Token bucket permits bursts up to bucket then refill rate; leaky bucket smooths; fixed windows have boundary bursts; sliding window more accurate/costly. Apply tenant/user/business-flow fairness and global capacity.

Load shed early before consuming scarce DB/thread resources. Return429 for client quota and503 for unavailable capacity as contract dictates. Prioritize essential operations carefully.

### 2.14 Fallback

Fallback must be semantically safe. Cached product recommendation may degrade; stale account balance or authorization decision may not. Mark stale/source/time; never convert payment failure into false success. Fallback itself needs bounds and monitoring.

### 2.15 Composition order

Order changes behavior. Retry inside circuit breaker may record one overall failure; breaker inside retry records every failed attempt. Time limiter around total retries differs from per-attempt timeout. Bulkhead placement controls whether waiting counts. Draw decorator order and test actual library semantics.

### 2.16 Load, soak and fault injection

Load test realistic payload/distribution, warm-up, steady duration and saturation; report throughput, p50/p95/p99, errors, CPU, GC, pool/queue waits and dependency capacity. Coordinated omission can underreport latency if generator waits for response rather than maintaining arrivals.

Soak detects leaks/slow accumulation. Fault injection adds latency, resets, 503, dropped acknowledgements, DB deadlocks and pod termination. Run controlled blast radius with rollback/observability; chaos without hypotheses is random damage.

## 3. WORKED PROBLEMS

### Problem 1 — Withdrawal tests

**Statement.** Test account withdrawal.

**Solution.** Cases amount700/balance1000 succeeds leaves300; amount1001 fails unchanged; amount0/negative rejected; exact1000 leaves0; overflow impossible by domain type/validation. Assert state, not internal method calls.

**Mistake caught.** Only happy path and line coverage.

### Problem 2 — Transaction rollback

**Statement.** Payment+outbox must rollback together.

**Solution.** Spring integration with real DB/proxy invokes service, injects failure after payment before outbox, then verifies neither row committed. A plain unit mock cannot prove transaction manager/DB behavior.

**Mistake caught.** Directly constructing service with `@Transactional` and expecting proxy.

### Problem 3 — Idempotency concurrency

**Statement.** 20 concurrent same-key requests.

**Solution.** Latch releases 20 workers against real unique constraint. Assert one payment, one idempotency record, all responses reference same result or documented in-progress. Different payload same key409. Repeat under DB engine.

**Mistake caught.** Sequential retry test misses check-then-insert race.

### Problem 4 — Retry budget

**Statement.** Three attempts, per attempt200 ms timeout, waits100/200 ms; total deadline800 ms.

**Solution.** Worst nominal =600 operation+300 waits=900 ms, already exceeds deadline. Reduce attempts/per-attempt or stop based on remaining time. Add jitter while respecting absolute deadline.

**Mistake caught.** Counting only backoff or only final attempt.

### Problem 5 — Retry storm

**Statement.** 1,000 RPS, dependency failing, three attempts.

**Solution.** Up to3,000 attempts/s before timing overlap; nested three layers up to27,000. Use one retry layer, jitter, breaker, budget and load shedding. Metrics separate original requests and attempts.

**Mistake caught.** Retries improve availability without load cost.

### Problem 6 — Circuit window

**Statement.** Last20 calls have12 failures, minimum10, threshold50%.

**Solution.** Failure rate60%, so opens when evaluation occurs under configured sliding-window semantics. If only6 calls, minimum not met and should not open. Test relevant exception classification.

**Mistake caught.** Opening on first failure despite configured minimum.

### Problem 7 — Bulkhead

**Statement.** Dependency supports40 global concurrent; five pods.

**Solution.** Equal theoretical8/pod leaves zero headroom/other clients. Choose ≤7 or coordinated limiter, account autoscaling and separate operations. Acquire before scarce connection and bound wait by deadline.

**Mistake caught.** 40 permits on every pod.

### Problem 8 — Flaky time test

**Statement.** Test sleeps100 ms expecting async completion.

**Solution.** Replace sleep with CountDownLatch/future and await up to bounded timeout; inject executor if needed. Assert completion signal/result. Sleep can be too short on CI and always wastes time.

**Mistake caught.** Making sleep longer rather than deterministic.

### Problem 9 — Safe fallback

**Statement.** Recommendation and authorization dependencies fail.

**Solution.** Recommendation can return empty/cached labeled result within product policy. Authorization should fail closed or use explicitly validated local policy—not cached allow by convenience. Different data criticality requires different fallback.

**Mistake caught.** One generic fallback for every dependency.

## 4. REAL-WORLD / APPLIED CONTEXT

### Spring test spectrum

Spring’s MockMvc runs DispatcherServlet with mock servlet request/response, covering mappings, binding, conversion, validation and exception handlers without live server. Official docs note differences from end-to-end HTTP/container behavior. Use each at its intended boundary.

### Real database

Testcontainers documentation explicitly trades slower startup for actual database compatibility and known clean state. PostgreSQL-specific JSONB, locking/isolation and migrations warrant real PostgreSQL tests. Reuse can speed local work but isolation/reproducibility must remain.

### Resilience4j

Resilience4j provides modular retry/circuit breaker/rate limiter/bulkhead/time limiter. Its retry defaults documented currently include3 maximum attempts and500 ms fixed wait; never accept defaults without workload/deadline review. The included lab implements deterministic fake-sleeper exponential retry and fake-clock circuit states to make policy testable without wall-clock sleeps.

## 5. COMPARISON TABLE

| Test type | Proves | Speed/fidelity | Does not prove |
|---|---|---|---|
| unit | local logic/contracts | fastest/isolated | wiring, SQL, proxy, network |
| Spring slice/MockMvc | focused framework boundary | fast-medium | live container/network/full config |
| integration/Testcontainers | real DB/broker/wiring | medium-slow/high boundary fidelity | whole deployed path |
| contract | consumer/provider compatibility | medium | business/security correctness |
| end-to-end | critical deployed journey | slow/broad | exhaustive edge diagnosis |
| load/soak | capacity/tails/leaks | expensive | functional completeness |
| fault/chaos | behavior under injected failure | controlled risk | unknown uncontrolled failures |

| Pattern | Purpose | Main danger |
|---|---|---|
| timeout | bound wait | remote effect continues/poor budget |
| retry | transient recovery | amplification/duplicates |
| breaker | stop likely-failing calls | bad classification/shared blast radius |
| bulkhead | isolate concurrency | local vs global mis-sizing |
| rate limit | control starts over time | unfair key/window bursts |
| fallback | degraded response | stale/unsafe false success |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Coverage equals quality.** Executed lines may have no meaningful assertions.
2. **Mock everything.** Tests validate invented interactions, not integration.
3. **H2 equals PostgreSQL.** SQL/MVCC/types differ.
4. **Transactional test proves commit hooks.** Auto rollback may hide commit behavior.
5. **Sleep synchronizes.** It creates flakes/waste.
6. **Preemptive timeout harmless.** Separate thread can escape Spring transaction context.
7. **Retry all errors.** Permanent/auth/validation failures amplify.
8. **Retry write without idempotency.** Duplicate effects.
9. **Timeout means failure.** Outcome may be unknown.
10. **Circuit breaker is retry/rate limiter.** Different state/control.
11. **Per-pod bulkhead is global.** Replica multiplication.
12. **Fallback always improves availability.** Unsafe stale data can worsen correctness.
13. **Load average enough.** p99/errors/saturation and open-loop arrivals matter.
14. **Chaos in production first.** Start hypothesis, test, staging/small blast radius.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full resource.

- Test behavior/risk, not implementation lines.
- Unit local logic; real integration for DB/proxy/network; few critical E2E.
- Inject Clock/random/sleeper/executor; latches over sleeps.
- Same DB version for SQL/isolation/constraints.
- Timeout every remote call under one end-to-end deadline.
- Retry transient + idempotent only; cap exponential jitter; one layer.
- Breaker closed/open/half-open; classify failures/minimum window.
- Bulkhead isolates concurrency; multiply replicas.
- Rate limit starts/time; semaphore limits in-flight.
- Fallback only when semantically safe and observable.
- Load report throughput, p95/p99, errors and saturation.
- Test failure composition and decorator order.

## 8. PRACTICE SET FOR SELF-TEST

1. Build test matrix for payment amount validation and overflow.
2. Choose unit/slice/integration/E2E tests for `POST /payments`.
3. Explain why a mocked repository cannot validate unique-key race.
4. Calculate worst retry duration for attempts4, timeout150 ms, waits50/100/200.
5. Design jitter test without random nondeterminism.
6. Circuit window100, minimum20, threshold40%, 9 failures in20: state transition?
7. Arrival600/s, dependency250 ms, six pods: estimate global in-flight and per-pod bulkhead baseline.
8. Decide fallback for model recommendation, payment balance and feature flag.
9. Design 30-minute soak evidence for memory leak.
10. Explain decorator-order difference: retry outside breaker vs breaker outside retry.

## 9. CURATED RESOURCES

1. **JUnit 5 User Guide, assertions, parameterized tests, extensions and timeouts.** Exact modern Java test APIs and timeout thread-mode caveats.
2. **Mockito documentation, strictness and argument matching.** Correct interaction-double usage and common traps.
3. **Spring Framework Reference, Testing and MockMvc chapters.** Context caching, slices, MVC boundary and end-to-end differences.
4. **Testcontainers for Java, database modules.** Real dependency integration patterns and compatibility rationale.
5. **Resilience4j docs, Retry, CircuitBreaker, Bulkhead, RateLimiter, TimeLimiter.** Concrete state/config/decorator semantics.
6. **Meszaros, *xUnit Test Patterns*.** Test doubles, fixture smells and maintainability vocabulary.
7. **Freeman & Pryce, *Growing Object-Oriented Software, Guided by Tests*.** Outside-in design and collaboration tests.
8. **Google Testing Blog, “Test Sizes” and hermetic-test guidance.** Portfolio and reproducibility practices.
9. **AWS Builders’ Library, “Timeouts, retries, and backoff with jitter.”** Production retry math and pitfalls.
10. **Gil Tene, “How NOT to Measure Latency.”** Coordinated omission and tail-latency measurement.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Spring Transactions/API Security.** Tests must cross proxy, database and HTTP/security boundaries.
2. **Concurrency/Virtual Threads.** Deterministic scheduling, interruption and bulkheads require it.

### After

1. **PostgreSQL/Data Systems.** Integration tests deepen into plans, locks and migrations.
2. **Distributed Failure Semantics.** Retry/breaker behavior gains idempotency and message delivery models.
3. **SRE/Observability.** Load/fault evidence becomes SLOs, alerts and incident learning.
4. **CI/CD.** Test portfolio becomes pipeline gates and progressive delivery.

---ANSWER KEY BELOW---

1. Invalid null/missing/type, negative, zero, min1, typical, max allowed, max+1, `Long.MAX_VALUE`, decimal/currency precision, cross-field currency rules. Assert safe Problem Details and no repository call for invalid.
2. Unit service validation/idempotency decisions; MockMvc mapping/auth/validation/error; real PostgreSQL transaction/unique/outbox concurrency; E2E one critical create/retry journey through live HTTP/security.
3. Mock serially returns programmed values and lacks DB atomic unique constraint/isolation/interleaving. Only real concurrent DB test proves one winner/exception handling.
4. Operation worst4×150=600 ms; waits50+100+200=350; total950 ms excluding jitter/scheduling. Must fit deadline.
5. Inject Random/source returning known fractions or inject interval function; assert bounds/distribution property separately with fixed seed. Unit policy should not sleep real time.
6. 9/20=45%, minimum met and threshold exceeded, so breaker opens at evaluation under exact window semantics.
7. `L=600×.25=150` global average if600 is global; about25/pod evenly. Add tail/headroom but cap by dependency. If600 per pod, global900 and150/pod—clarify scope.
8. Recommendation empty/stale labeled may be safe; payment balance should fail/unknown rather than fabricate; feature flag may use last-known/default only if rollout safety policy defines fail-open/closed per flag.
9. Constant representative load; collect post-GC live set, allocation rate, RSS/native, class histograms/dominators at intervals, queue/cache cardinality, GC/JFR and throughput. Warm-up baseline; leak evidence is rising retained floor, not sawtooth.
10. Retry outside breaker: each retry invokes breaker and can count each attempt/open mid-sequence. Breaker outside retry may see one decorated overall failure while retries occur inside, depending library. Time/bulkhead/rejection metrics and behavior differ; test chosen composition.
