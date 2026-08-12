# Parent 02 — Java and Spring

The original advanced topics keep their existing paths. Study the added prerequisite
sequence first; it explicitly covers knowledge the original curriculum assumed.

## Phase A — Java prerequisites

1. [Java Language and Object Model](06-java-language-object-model/lesson.md) — syntax, types, control flow, methods, OOP, equality, records, sealed types and resources.
2. [Collections, Generics and Exceptions](07-collections-generics-exceptions/lesson.md) — collection selection/complexity, generic variance/erasure, Optional and failure design.
3. [Modern Java and Streams](08-modern-java-streams/lesson.md) — lambdas, streams/collectors, Optional, date/time and modern language features.
4. [Build Tools, Testing and Debugging](09-build-testing-debugging/lesson.md) — Maven/Gradle, dependencies, JUnit/Mockito, CI, stack traces, JFR and deterministic tests.

## Phase B — Spring Boot prerequisites

5. [Spring Boot Fundamentals](10-spring-boot-fundamentals/lesson.md) — context, beans, DI, scopes/lifecycle, starters, auto-configuration, profiles and Actuator.
6. [Spring Web, Validation and Configuration](11-spring-web-validation-config/lesson.md) — MVC request path, DTO/Jackson binding, Bean Validation, errors, CORS/CSRF and MockMvc.
7. [Spring Data JPA Fundamentals](12-spring-data-jpa-fundamentals/lesson.md) — entities, persistence context, dirty checking, fetching/N+1, repositories, queries, pagination and locking.

## Phase C — Existing advanced sequence

8. [JVM Memory and Garbage Collection](01-jvm-memory-gc/lesson.md) — complete
9. [Concurrency and Virtual Threads](02-concurrency-virtual-threads/lesson.md) — complete
10. [Spring Core and Transactions](03-spring-core-transactions/lesson.md) — complete
11. [API Design and Security](04-api-design-security/lesson.md) — complete
12. [Testing and Resilience](05-testing-resilience/lesson.md) — complete

13. [Integrated Java/Spring Capstone](CAPSTONE.md) — required parent exit artifact

## Parent completion gate

Complete every child self-test at 80%+, compile/run all included labs, deliver the capstone at 80/100 or higher, and explain Java equality/hash/generics, stream cost, Boot auto-configuration, MVC request flow, JPA entity states/N+1, proxy self-invocation, transaction propagation, JVM memory budgeting, virtual-thread bulkheads and retry/idempotency interaction without notes.
