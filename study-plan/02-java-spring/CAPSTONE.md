# Java and Spring Capstone — Resilient Payment API

## Objective

Build a Spring Boot payment API that is correct under retries, concurrent requests, dependency failures and container memory limits. Use Java 21+ and PostgreSQL. The capstone is evidence of engineering judgment, not a CRUD demo.

Before implementation, complete all twelve lessons and demonstrate the prerequisite foundation: compile and run Java from a clean environment; explain syntax, control flow, methods, value/reference semantics, equality/hash and generic variance; show exceptions, collections, streams and concurrency with tests; produce a reproducible Maven/Gradle build; construct a minimal Spring Boot application; trace one HTTP request through validation/controller/service/repository; and explain JPA transient/managed/detached/removed states, dirty checking, flush and one N+1 repair.

## Functional contract

- `POST /v1/payments` accepts tenant-scoped idempotency key and payment command.
- New synchronous success returns 201 + Location; retry with same key/body returns identical resource/result; different body returns RFC 9457 409.
- `GET /v1/payments/{id}` enforces object/tenant authorization.
- `PATCH /v1/payments/{id}` requires ETag/If-Match and returns 412 on stale version.
- `GET /v1/payments` uses keyset cursor `(created_at,id)` with maximum page size 200.
- Gateway submission is asynchronous through transactional outbox and uses the same external idempotency identity.

## Implementation constraints

1. Constructor injection; stateless singleton services.
2. Public service transaction is reached through Spring proxy; no self-invocation dependency.
3. Unique `(tenant_id,idempotency_key)` and request hash; atomic transaction writes payment and outbox.
4. No remote call while holding database transaction/lock.
5. Gateway client has one end-to-end deadline, safe capped retry with jitter and circuit breaker; decorator order documented.
6. Virtual threads may be used for blocking I/O, but gateway/DB concurrency is explicitly bulkheaded and multiplied across replicas.
7. RFC 9457 errors contain no stack traces, secrets, card data or PHI.
8. Heap/RSS budget is documented for a 1 GiB pod; Xmx leaves measured native/nonheap headroom.

## Required tests

- Plain unit tests for domain transitions and retry policy with fake Clock/Sleeper.
- MockMvc tests for mapping, validation, JWT authorization, Problem Details, 201/409/412/429/503.
- Real PostgreSQL integration tests for migrations, unique-key concurrency, rollback and keyset query.
- Twenty concurrent identical POSTs result in one payment and one logical outbox event.
- Failure injected between payment/outbox proves atomic rollback.
- Gateway timeout proves unknown/in-progress state rather than false failure.
- Circuit opens/half-opens deterministically; global permit math tested/configured.
- Load test at 250 average/1,000 burst RPS reports throughput, p50/p95/p99, errors, pool/semaphore waits, CPU, allocation, GC and RSS.
- Soak test checks post-GC live-set/cache/queue growth.

## Failure review

Demonstrate and explain:

1. Why calling `this.persist()` bypasses transaction advice.
2. How REQUIRES_NEW can exhaust a pool.
3. Why virtual threads do not create DB connections.
4. How retry without idempotency duplicates charges.
5. Why timeout cannot declare remote payment failed.
6. How a shared cache/proxy can leak tenant data without correct key/Vary policy.

## Rubric (100)

| Area | Points |
|---|---:|
| Transaction/idempotency correctness | 20 |
| API and authorization contract | 15 |
| Failure resilience/deadline behavior | 15 |
| Testing depth and determinism | 20 |
| JVM/concurrency/capacity evidence | 15 |
| Code clarity and dependency boundaries | 10 |
| Oral defense/runbook | 5 |

Pass at 80+, with mandatory pass in transaction correctness, authorization and concurrency test. Record a 20-minute design walkthrough and answer the failure review without notes.
