# Client–Server, APIs, RPC, and Messaging from Scratch

Parent subject: `04-distributed-systems`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### A process boundary changes the programming model

Inside one process, a Java method call transfers control through memory managed by one runtime. Across processes, the caller serializes data, uses a protocol over a network or IPC channel, waits or continues, and interprets a response or later event. Either process can fail independently; messages can be delayed, duplicated, reordered, or lost; versions can differ; authentication and authorization become mandatory.

The **client–server model** assigns a client to initiate requests and a server to listen and respond. A process can be both: an API server may be a client of PostgreSQL and a model server. These are roles in an interaction, not permanent machine types.

Early network applications defined purpose-specific protocols. Remote Procedure Call (RPC) systems attempted to make remote interaction resemble a local call. Distributed-object systems later exposed remote objects. REST emphasized resources and uniform HTTP semantics. Message-oriented middleware decoupled senders from receiver availability. Each approach addresses a different coupling problem; none erases partial failure.

The classic warning “a remote call is not a local call” exists because convenient stubs can conceal latency, serialization, authentication, version skew, fan-out, and ambiguous outcome. Good abstractions reduce boilerplate while keeping operational semantics visible.

### Processes, endpoints, and protocols

A **process** is a running program with its own address space and operating-system resources. An **endpoint** is a reachable service address plus protocol, such as `https://claims.example/v1/claims` or a Kafka topic and partition. A **protocol** defines message format, ordering, state transitions, and error behavior.

An **API** is a contract through which software capabilities are used. A network API includes operations/resources, request and response schemas, authentication, authorization, errors, idempotency, rate limits, pagination, compatibility, and service-level expectations. An OpenAPI file that lists fields but omits behavior is incomplete.

### Serialization and schemas

Serialization converts in-memory data to bytes. JSON is textual, self-describing at the field-name level, and broadly interoperable. Protocol Buffers, Avro, and Thrift use schemas and compact binary encodings. Serialization does not preserve every language concept automatically: object identity, arbitrary subclasses, decimal precision, timestamps, time zones, and unknown fields need contracts.

A **schema** defines field names/numbers, types, requiredness/default behavior, and structure. **Backward compatibility** means a new reader can consume old data or, depending on convention, old consumers can tolerate new producer output; teams must state the direction precisely. **Forward compatibility** is the complementary direction. Safe evolution often adds optional fields, preserves stable field numbers, supplies semantic defaults, and delays removals until all consumers migrate.

JSON numbers have no universal fixed integer width. JavaScript historically represents numbers as IEEE-754 double and cannot exactly represent every integer above `2^53-1`. Sending a 64-bit ledger identifier as a JSON number can lose precision in some clients; use a string when cross-language exactness demands it.

### Request/response and RPC

In request/response, a client sends a request and awaits a response. HTTP APIs and RPC frameworks fit this model. **RPC** presents a named remote operation such as `GetClaim(GetClaimRequest)`. Generated stubs serialize requests and decode responses. gRPC commonly uses Protocol Buffers and HTTP/2, supports unary calls and streaming, and communicates typed status.

Synchronous does not necessarily mean one operating-system thread blocks; async runtimes can suspend work. Semantically, however, the caller needs the result before proceeding. This creates temporal coupling: both sides and the path must be available within the deadline.

A **deadline** is the latest useful completion time. A timeout is a configured waiting limit, sometimes per phase. Absolute deadline propagation prevents each hop from independently consuming a full timeout. Cancellation is cooperative: the caller stopping its wait does not prove the server stopped or rolled back.

### REST and resource semantics

REST is an architectural style described by Roy Fielding, including client/server separation, stateless interactions, cache constraints, uniform interfaces, layers, and optional code-on-demand. In practice, “REST API” often means resource-oriented HTTP.

Resources have identifiers and representations. `GET /claims/C1` retrieves; `POST /claims` can create under a server-selected identifier; `PUT /claims/C1` replaces desired state; `PATCH` applies a change; `DELETE` requests removal. HTTP method safety and idempotency guide caching and retries, but business operations still need explicit rules.

Do not encode every action as CRUD mechanically. `POST /payments/{id}/capture` can be clearer than pretending capture is a field update, provided idempotency and state-transition semantics are defined.

### Messaging, queues, topics, and logs

In asynchronous messaging, a producer sends a message without waiting for final business processing. A **broker** stores/routes messages. A **queue** typically distributes messages among competing consumers so one logical consumer handles each delivery. **Publish/subscribe** delivers a publication to multiple independent subscriptions. A **log** such as Kafka is an ordered append-only sequence per partition; consumers track positions and can replay retained records.

A producer acknowledgment means the broker accepted/durably stored according to configuration; it does not mean the downstream business action completed. A consumer acknowledgment/offset commit means the consumer claims processing reached a chosen boundary; crashes around that boundary create redelivery or loss depending on order.

### Delivery semantics

**At-most-once** avoids redelivery but may lose messages. **At-least-once** retries/redelivers, so duplicates are possible. **Exactly-once** is always scoped: one broker transaction, one stream topology, or one transactional boundary. It does not magically make an external email, payment network, database, and Kafka update globally exactly once.

The robust default is at-least-once transport plus idempotent processing and reconciliation. A message has a stable event/command ID. The consumer atomically records that ID with its local state change, then acknowledges. Side effects outside the transaction need their own idempotency or an outbox/inbox workflow.

### Commands, events, and queries

A **command** requests an action: `CapturePayment`. It has an intended handler and may be rejected. An **event** states a fact that happened: `PaymentCaptured`. Consumers should not reinterpret a past-tense fact as an instruction to its producer. A **query** asks for data without intentionally changing business state.

Names affect coupling. An event named `SendWelcomeEmail` is really a command. `CustomerRegistered` lets email, analytics, and fraud consumers react independently. Events require provenance, occurrence time, schema version, stable identity, and domain meaning.

### Coupling dimensions

Services can be coupled in time (must be online together), schema, deployment/version, identity, ordering, throughput, and failure. Async messaging reduces temporal coupling and absorbs bursts, but adds eventual consistency, duplicate handling, queue lag, poison messages, operational state, and harder tracing. It is not automatically more scalable or reliable.

## 2. CORE MECHANICS

### 2.1 Design an HTTP resource contract

```http
POST /v1/claims
Authorization: Bearer <token>
Idempotency-Key: 9ca45191-e810-4ada-9090-8f6946724530
Content-Type: application/json

{"externalReference":"HOSP-2026-991",
 "patientId":"P-88","amountPaise":129900,"currency":"INR"}
```

Possible outcomes:

- `201 Created` with `Location: /v1/claims/C-1042` for new creation.
- same logical response for a replay with the same key and same request fingerprint;
- `409 Conflict` if the key is reused with a different payload;
- `400` malformed syntax/type, `422` well-formed but domain-invalid if that convention is chosen;
- `401` missing/invalid authentication, `403` authenticated but unauthorized;
- `429` rate limited and `503` temporarily unavailable with bounded retry guidance.

The service atomically stores `(tenant,key,fingerprint,outcome)` with creation. Tenant scope prevents one customer from probing another's keys.

### 2.2 Choose status codes and errors

Return machine-readable stable codes and safe context:

```json
{
  "type":"https://errors.example/claim-state-conflict",
  "title":"Claim state conflict",
  "status":409,
  "code":"CLAIM_NOT_SUBMITTED",
  "traceId":"01J58D9K8B3D9M8NQ2H7"
}
```

Do not expose stack traces, SQL, tokens, or clinical payloads. Correlation IDs support diagnosis but do not replace server logs/traces. Decide whether missing and forbidden resources both return 404 to prevent enumeration.

### 2.3 Pagination

Offset pagination `?limit=50&offset=100000` is simple but the database may scan/discard 100,000 rows, and concurrent inserts shift pages. Keyset pagination orders by `(created_at,claim_id)` and returns an opaque cursor encoding the last tuple plus query context. The next predicate is lexicographic: values after the tuple under the same direction.

Cursors should be integrity protected, bounded in lifetime if necessary, and not leak sensitive internals. A page size of 100 with a 2 KB representation yields about 200 KB before compression/headers; set maximums to protect server and client memory.

### 2.4 RPC schemas and compatibility

Protocol Buffer example:

```proto
message GetClaimRequest { string claim_id = 1; }
message Claim {
  string claim_id = 1;
  int64 amount_paise = 2;
  string currency = 3;
  optional string adjudication_reason = 4;
}
service ClaimService {
  rpc GetClaim(GetClaimRequest) returns (Claim);
}
```

Never reuse removed field number 4 for a different meaning; reserve it/name if removed. Adding field 4 is wire-compatible when old consumers ignore unknown fields, but semantic compatibility still requires that its absence has a safe meaning.

### 2.5 Deadlines and fan-out

An aggregator has 400 ms total and calls identity then, in parallel, claims and risk. Reserve 60 ms ingress/auth and 40 ms response/safety. Identity gets at most 100 ms; parallel calls have at most remaining 200 ms. Giving every call 400 ms can exceed the end-to-end deadline.

If fan-out calls 50 shards and each succeeds independently with probability 99.9%, probability all succeed is `0.999^50≈95.12%`. Fan-out amplifies tail failure. Use partial-result semantics only when domain-safe, reduce fan-out, replicate/aggregate data, and budget hedging carefully.

### 2.6 Queue mechanics and backpressure

Arrival 2,000 messages/s, consumer capacity 1,600/s creates backlog at 400/s. In ten minutes backlog grows 240,000 messages. If producers stop, drain time at 1,600/s is 150 seconds. If arrivals continue at 1,000/s during recovery, net drain is 600/s and takes 400 seconds.

Backpressure controls admission or slows producers when downstream capacity is insufficient. A queue buffers finite bursts; it cannot solve sustained arrival above service rate. Monitor age of oldest message, not only count, because business timeliness depends on delay.

### 2.7 Consumer processing boundary

Unsafe commit-before-work:

1. Receive M.
2. Commit offset/ack.
3. Write database.
4. Crash before step 3 → message lost.

Work-before-ack:

1. Receive M with event ID.
2. Begin local transaction.
3. If inbox already contains ID, no-op; otherwise update state and insert inbox ID.
4. Commit.
5. Ack/commit offset.
6. Crash after step 4 before step 5 → redelivery, inbox deduplicates.

This produces effectively-once local state under the stated database boundary, not universal exactly-once side effects.

### 2.8 Outbox pattern

When a service must change its database and publish an event, writing DB then publishing can crash between actions. A **transactional outbox** writes business state and an outbox row in one database transaction. A relay publishes pending rows and marks/observes them. Publish can duplicate, so event IDs and idempotent consumers remain necessary. Change data capture can relay the log instead of polling.

### 2.9 Poison messages and dead-letter handling

A poison message repeatedly fails because of invalid data, incompatible schema, or deterministic bug. Infinite immediate retry blocks progress and wastes capacity. Classify failures: transient gets bounded backoff; permanent goes to quarantine/dead-letter with original envelope, error code, attempt metadata, and protected payload. Alert on rates/age and provide an audited replay after correction. A dead-letter queue is not a deletion bin.

### 2.10 API versus event versioning

Prefer compatible additive evolution. For HTTP, tolerate unknown response fields, avoid changing field meaning/type, and maintain documented deprecation windows. URI `/v2` is useful for breaking resource semantics but creates parallel support cost. Header/media versioning can be precise but operationally less visible.

For events, immutable facts may be retained for years. Use schema registry compatibility checks, stable event type identity, explicit semantic version/migration, and upcasters/readers when necessary. “Add optional field” can still break a consumer that rejects unknown fields; contract tests must include real consumers.

## 3. WORKED PROBLEMS

### Problem 1 — Local versus remote call (easy)

Name four new failure concerns when `repository.find(id)` becomes network RPC.

**Solution.** Serialization/schema compatibility, DNS/connectivity/TLS/auth, latency/deadline, partial/ambiguous failure, server version/capacity, and retry duplication are valid. At least four must shape the contract.

**Trap:** treating generated stubs as local method semantics.

### Problem 2 — GET retry (easy)

Can a timed-out GET be retried?

**Solution.** GET is intended safe and idempotent, so bounded retry is normally valid, but respect overall deadline, rate limits, server behavior, and authentication. A badly designed GET with side effects violates the protocol contract.

**Trap:** saying every GET retry is always harmless without bounds.

### Problem 3 — Queue growth (easy)

Producer 900/s, consumers 750/s for eight minutes. Backlog?

**Solution.** Net 150/s × 480 s = 72,000 messages, assuming steady rates and no initial backlog.

**Trap:** using total producer rate instead of net difference.

### Problem 4 — Idempotency key reuse (medium)

Same tenant sends same key with ₹1,000 then ₹2,000.

**Solution.** Reject the second request as conflict because fingerprint differs. Returning the first response silently could mislead the caller; processing again defeats idempotency.

**Trap:** deduplicating solely by key without payload identity.

### Problem 5 — JSON integer (medium)

Can Java `long` value 9,007,199,254,740,993 be safely consumed as a JavaScript number?

**Solution.** It exceeds `2^53-1=9,007,199,254,740,991`, the largest consecutively exact integer in binary64. Encode exact identifier as a decimal string or use an agreed BigInt-capable representation.

**Trap:** assuming JSON “number” has Java long semantics.

### Problem 6 — Fan-out reliability (medium)

Twenty independent calls each succeed 99.5%. All-success probability?

**Solution.** `0.995^20≈90.46%`. Even high individual success creates weak aggregate success. Independence may also be false due to common dependencies.

**Trap:** averaging success percentages or subtracting only 0.5% once.

### Problem 7 — Ack ordering (hard)

Compare ack-before-write and write-before-ack.

**Solution.** Ack-before-write can lose on crash. Write-before-ack can redeliver after committed work. Use atomic inbox/state update for idempotent replay, then ack. External effects need further controls.

**Trap:** claiming write-before-ack is exactly once by itself.

### Problem 8 — Async does not mean complete (hard)

API returns `202 Accepted` after enqueue. Has claim adjudication succeeded?

**Solution.** No. It confirms acceptance into a defined asynchronous workflow. Return a job/resource identifier, status endpoint or callback/event contract, terminal failure states, expiry, and authorization. Broker acknowledgment is not business success.

**Trap:** using 202 as a successful domain outcome.

### Problem 9 — Outbox duplicates (hard)

Relay publishes event then crashes before marking it sent. What happens?

**Solution.** It may publish again. Stable event ID and idempotent consumer/inbox are required. Outbox closes DB-change-versus-publish loss, not duplicate delivery.

**Trap:** marketing the outbox as global exactly once.

## 4. REAL-WORLD / APPLIED CONTEXT

### gRPC

gRPC generated clients and servers use Protocol Buffers, HTTP/2, unary and streaming RPCs, metadata, deadlines, and status codes. Production users must configure deadline propagation, message limits, keepalive, load balancing, TLS/mTLS, retry policy, and observability. Generated typing does not define business compatibility.

### Apache Kafka

Kafka stores ordered records in partitions. Producer acknowledgment configuration and replication affect durability; consumer groups assign partitions; offsets represent progress. Ordering is per partition, not across a topic. A key controls partition placement, so choosing patient or account key trades parallelism for per-entity order.

### AWS/Azure queue-style services

Managed queues such as Azure Service Bus and Amazon SQS expose visibility/lock durations, retries, dead-lettering, duplicate-detection options, sessions/FIFO variants, and quotas. A lock expiring during long processing causes redelivery; renew or size it and still keep consumers idempotent.

## 5. COMPARISON TABLE

| Style | Temporal coupling | Typical latency | Main strength | Main cost |
|---|---|---|---|---|
| REST/HTTP | Caller waits | Interactive ms–s | Universal, cache/proxy semantics | Manual schema/behavior discipline |
| gRPC unary | Caller waits | Low overhead interactive | Typed contracts, streaming ecosystem | Browser/proxy/debug compatibility considerations |
| Queue | Receiver can be offline | Queueing + processing | Buffering, competing consumers | Duplicates, lag, DLQ, eventual result |
| Pub/sub | Subscribers independent | Async | Fan-out and extensibility | Versioning and per-subscriber operations |
| Partitioned log | Consumers replay | Async | Ordered per partition, retention/replay | Partition planning and lag management |
| At-most-once | No duplicate delivery | May lose | Noncritical telemetry | Missing work |
| At-least-once | Redelivery | Duplicates | Durable business workflows | Idempotency required |
| Scoped exactly-once | Within documented boundary | Coordination overhead | Simplifies supported topology | Does not cover arbitrary external effects |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **RPC is a local call over the network.** It has independent failure, version, security, and time.
2. **REST means JSON over HTTP.** REST includes constraints and resource semantics.
3. **POST cannot be idempotent.** The method is not inherently idempotent, but application keys can make an operation idempotent.
4. **202 means completed.** It means accepted for processing under a defined contract.
5. **Broker ack means business success.** It normally means broker acceptance/durability level.
6. **Queues create capacity.** They buffer bursts; sustained overload grows lag without bound.
7. **Exactly once is global.** It is scoped and external effects need their own guarantees.
8. **Commit offset before work to avoid duplicates.** That risks loss.
9. **Outbox eliminates duplicates.** It prevents an atomicity gap but relay publication can repeat.
10. **Adding an optional field is always safe.** Semantic defaults and consumer parsers can still break.
11. **Offset pagination is fine at every scale.** Deep offsets cost work and shift with writes.
12. **Async is automatically decoupled.** Schema, ordering, capacity, and ownership coupling remain.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Remote call adds serialization, latency, security, version skew, and partial failure.
- API contract = schema + semantics + errors + auth + idempotency + limits + compatibility.
- Deadline is end-to-end usefulness; propagate remaining budget.
- JSON exact integers above `2^53-1` need cross-language care.
- Queue buffers; topic/pub-sub fans out; log retains ordered partitions.
- Command asks; event states a fact; query reads.
- At-most-once may lose; at-least-once duplicates; exactly-once is scoped.
- State + inbox ID in one transaction, then acknowledge.
- State + outbox in one transaction; consumers still deduplicate.
- Backlog growth = (arrival − service) × time.
- `202` needs job/status/terminal-failure contract.

## 8. PRACTICE SET FOR SELF-TEST

1. Design statuses for creating an already-existing resource with the same versus different idempotency payload.
2. Calculate payload volume for 250 records at 1.5 KB each.
3. At 3,000 messages/s in and 2,400/s out for 15 minutes, calculate backlog.
4. If arrivals stop, calculate drain time at 2,400/s.
5. Explain why a gRPC cancellation does not prove server rollback.
6. Choose queue, pub/sub, or synchronous API for: payment authorization needed before checkout response; audit fact consumed by five teams; one of 20 workers resizing images.
7. Define safe removal of protobuf field number 7.
8. Explain why ordering by timestamp alone is not deterministic.
9. Calculate all-success probability for ten independent 99% dependencies.
10. State the transaction boundary for inbox deduplication.

## 9. CURATED RESOURCES

- Roy Fielding, *Architectural Styles and the Design of Network-based Software Architectures*, dissertation, Chapter 5 — primary definition and motivation of REST constraints.
- RFC 9110, “HTTP Semantics” — authoritative methods, safety, idempotency, statuses, representations, and caching semantics.
- gRPC official documentation, “Core concepts, architecture and lifecycle,” “Deadlines,” and “Retry” — exact unary/streaming, cancellation, deadline, and configured retry behavior.
- Protocol Buffers official “Language Guide” and “Updating A Message Type” — field numbering, unknown fields, presence, and compatibility rules.
- Apache Kafka documentation, “Introduction,” “Design,” producer configs, and consumer configs — partitions, ordering, groups, acknowledgments, delivery, and transactions.
- Gregor Hohpe and Bobby Woolf, *Enterprise Integration Patterns*, chapters on Message Channel, Point-to-Point, Publish-Subscribe, Dead Letter Channel, and Idempotent Receiver — canonical messaging patterns.
- Chris Richardson, *Microservices Patterns*, Chapters 3 and 4 — interprocess communication, transactional messaging, outbox, sagas, and idempotent consumers.
- Martin Kleppmann, *Designing Data-Intensive Applications*, Chapters 4 and 11 — encoding/evolution and stream processing semantics.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Computer Networking:** supplies DNS, transport, TLS, HTTP, latency, and load balancing.
2. **SQL and Transactions:** supplies local atomic state used by inbox/outbox.
3. **Spring Web Fundamentals:** supplies controllers, validation, serialization, and client code.

### After

1. **Distributed Systems Foundations:** formalizes time, failure, replication, and coordination.
2. **Failure Semantics:** deepens deadlines, retries, backoff, breakers, and overload.
3. **Kafka and Eventing:** specializes partitioned logs, consumer groups, schemas, and capacity.
4. **Consistency and Idempotency:** proves cross-service state and replay behavior.
5. **System Design:** chooses communication style under workload and failure constraints.

---ANSWER KEY BELOW---

1. Return/replay same logical outcome for same scoped key+fingerprint; reject different fingerprint as conflict.
2. 375 KB before envelope/protocol overhead.
3. Net 600/s × 900 s = 540,000.
4. 225 seconds.
5. Cancellation is a signal; request may already have committed or ignore/observe it late.
6. Synchronous API; pub/sub; queue with competing consumers.
7. Stop producing it, ensure all readers tolerate absence, reserve number/name permanently, and never reuse its meaning.
8. Multiple rows can share timestamp; add a unique tie-breaker and matching cursor.
9. `0.99^10≈90.44%`.
10. Check/insert stable message ID and apply local business change atomically in one DB transaction; acknowledge afterward.
