# Parent 04 — Distributed Systems

This parent moves from partial-failure semantics through event streams and
cross-service correctness into quantitative architecture.

No networking, RPC, messaging, or distributed-systems knowledge is assumed.

## Phase A — Prerequisites

1. [Computer Networking from Scratch](05-computer-networking-foundations/lesson.md) — packets, addressing, DNS, TCP/UDP, TLS, HTTP, proxies, load balancers and quantitative latency.
2. [Client–Server, APIs, RPC, and Messaging](06-client-server-rpc-messaging-basics/lesson.md) — process boundaries, contracts, serialization, request/response, queues, delivery semantics and compatibility.
3. [Distributed Systems Foundations](07-distributed-systems-foundations/lesson.md) — nodes, time, partial failure, replication, partitioning, consensus vocabulary and impossibility boundaries.

## Phase B — Existing advanced sequence

4. [Failure Semantics](01-failure-semantics/lesson.md) — complete; includes controlled failure drills and a tested deadline/retry/breaker policy lab.
5. [Kafka and Eventing](02-kafka-eventing/lesson.md) — complete; includes a versioned event contract and tested partition/capacity/deduplication lab.
6. [Consistency and Idempotency](03-consistency-idempotency/lesson.md) — complete; includes a saga state machine and tested clock/quorum/deduplication lab.
7. [Capacity-Driven System Design](04-capacity-system-design/lesson.md) — complete; includes a design worksheet and tested traffic/storage/availability/queue calculator.

## Parent capstone

[Multi-Region Model Authorization Platform](CAPSTONE.md) integrates networking, service communication, distributed foundations, failure semantics, Kafka, consistency/idempotency and quantitative design under fintech/healthcare constraints.
