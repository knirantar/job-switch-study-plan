# Kafka and Event-Driven Systems

**Parent:** 04 — Distributed Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus executable exercises

## 1. FOUNDATIONS

An event is a durable statement that something happened: payment 90017 was authorized, model version 12 was promoted, eligibility decision 73 was evaluated. An event is not merely an asynchronous function call. It has identity, time, producer, business meaning and a schema that other systems may retain and replay long after the producing code is gone.

Apache Kafka is a distributed append-only log. Producers append records to **topics**. A topic is divided into **partitions**, each an ordered sequence of records identified by monotonically increasing **offsets**. Brokers store partition replicas; one replica is leader for client reads/writes and followers replicate it. Consumers pull records and track their position. Kafka retains records by time/size or compacts by key independently of whether a consumer has read them, enabling replay and multiple independent subscribers.

Traditional queues often remove or hide a message after acknowledgement. A log retains history, and each consumer group has its own progress. This supports audit pipelines, CDC, stream processing and rebuilding derived views. It also creates operational responsibilities: retention must exceed recovery/replay needs; slow consumers accumulate lag; replay can repeat side effects; schemas must remain readable; partitions constrain ordering and parallelism.

Ordering is local. Kafka guarantees records are read in written order within a topic-partition. It does not create one global total order across partitions. A key normally selects a partition, so all events for `payment-90017` can remain ordered if every producer uses the same stable key and partitioning contract. Changing partition count or key algorithm may map future events differently; consumers should still carry aggregate version and detect gaps/regressions.

Delivery terms must name the boundary. **At-most-once** may lose but does not redeliver after the chosen acknowledgement point. **At-least-once** retries and can duplicate. **Exactly-once** is always scoped. Kafka's idempotent producer prevents duplicate log appends from producer retries in its session/identity semantics. Kafka transactions can atomically write records to Kafka partitions and consumer offsets, with consumers using `read_committed`. They do not atomically include an arbitrary HTTP service or PostgreSQL transaction unless a separate protocol exists.

Kafka was designed at LinkedIn to handle high-volume durable activity streams with sequential I/O, batching and partitioned parallelism. Its performance comes partly from append-only logs, OS page cache, batching and zero-copy paths—not from treating each event like an independent database row. But throughput figures depend on hardware, message size, replication, acknowledgements, compression, partitions and client configuration. Benchmark your topology; do not quote a vendor graph as an SLO.

For a senior engineer, the critical questions are: What is the event contract? Which key defines ordering? What can duplicate? When is an offset committed? How is a database side effect deduplicated? What happens to a poison event? Can the consumer replay within retention? How much storage and catch-up capacity are required? Who may see sensitive fields?

## 2. CORE MECHANICS

### 2.1 Records, topics, partitions and offsets

A Kafka record has topic, optional key, value, headers, timestamp and assigned partition/offset. The offset is a position, not a globally unique event ID and not stable across copying to another topic. Include an application `event_id` such as UUID and aggregate identity/version in the payload/envelope.

Partitions provide parallelism. In a consumer group, at most one consumer at a time owns a given partition; one consumer may own multiple partitions. With 12 partitions, a group can actively process at most 12 partitions in parallel, even if it runs 20 instances (eight are idle for that subscription). One consumer can process multiple records concurrently only if it preserves required per-key/partition ordering and offset safety.

Too few partitions cap throughput; too many add metadata, files, leader/rebalance and operational costs. Partition count is not a tuning knob to change casually because the default key-to-partition mapping can change when count changes. Size using measured per-partition produce/consume throughput, future rate, key skew and recovery time.

### 2.2 Keys and ordering

Choose the smallest aggregate whose events need order: payment ID, account ID, patient ID, model deployment ID. Keying all events by tenant preserves tenant-wide order but can create hot partitions and unnecessary serialization. Keying randomly maximizes balance but loses aggregate order.

If payment events v1, v2, v3 share key, one partition gives order. Still include `aggregate_version` because events can be missing from retention, filtered, copied incorrectly or produced by a buggy key. A consumer expecting version 2 but receiving 3 should quarantine/request repair rather than blindly apply. `KafkaSemanticsLab` demonstrates duplicate event rejection and version-gap detection.

A hot key cannot be split across partitions without weakening or redesigning its ordering semantics. Techniques include subkeying independent entities, sharded counters with aggregation, or a sequencer—each changes the model.

### 2.3 Producer batching, compression and acknowledgement

The producer batches records per partition. `batch.size` caps a batch buffer; `linger.ms` may wait briefly for more records; compression works better across batches. Larger batches raise throughput/compression but consume memory and add latency under low traffic. `delivery.timeout.ms` bounds send completion across retries; `request.timeout.ms` bounds a request wait and should align with broker replication timing.

Kafka 4.2 producer `acks` meanings:

- `acks=0`: no broker acknowledgement; producer cannot know loss and retries are ineffective.
- `acks=1`: leader acknowledges local append; immediate leader loss before follower replication can lose it.
- `acks=all`: current in-sync replicas acknowledge; strongest available setting.

Durability also needs topic replication and `min.insync.replicas`. A common example is replication factor 3, min ISR 2, producer acks all: writes fail when too few in-sync replicas remain rather than accepting a less-durable record. Availability versus durability is explicit. Apache Kafka 4.2 notes Eligible Leader Replicas can change exact min-ISR semantics, so validate cluster mode.

### 2.4 Idempotent producer

Network loss after append can make a producer retry. Without idempotence, both original and retry may appear. Kafka idempotent production uses producer identity and sequence numbers so the broker recognizes duplicate batches. Kafka 4.2 enables idempotence by default when no conflicting settings exist; requirements include `acks=all`, retries greater than zero and max in-flight requests per connection at most 5. Explicit incompatible settings can disable it or cause configuration error.

This guarantee concerns duplicates written by that producer protocol, not duplicate business commands, application restart with new logical event, or consumer side effects. If the service receives the same payment twice and constructs two different event IDs, producer idempotence correctly writes both. Application idempotency remains required.

### 2.5 Kafka transactions

A producer with stable `transactional.id` can atomically write to multiple Kafka partitions. A consume-transform-produce application can add output records and source consumer offsets to the same Kafka transaction. Downstream `isolation.level=read_committed` ignores aborted/uncommitted transactional records. Fencing prevents an old producer epoch with the same transactional identity from continuing.

Transactions increase coordination/latency and have timeout limits. Kafka 4.2 producer default `transaction.timeout.ms` is documented as 60 seconds, bounded by broker maximum. Long transactions stall read-committed visibility. Use stable, uniquely assigned transactional IDs across instances; accidental reuse fences a live producer.

Kafka transaction does not include a PostgreSQL update. For Kafka input → database output, use an idempotent sink: transactionally insert event ID (unique) and business change, then commit offset only after database commit. Crash after DB commit before offset commit causes redelivery; unique event ID makes the repeated DB transaction a no-op/returns prior result.

### 2.6 Consumer groups and rebalancing

Consumers with the same `group.id` divide partitions; different groups each receive the stream independently. Membership or subscription changes cause assignment changes through a rebalance protocol. A consumer must stop work/revoke safely, commit only completed offsets and initialize newly assigned partitions.

`max.poll.interval.ms` bounds time between polls before the group considers a consumer failed; `session.timeout.ms`/heartbeats detect membership loss. If processing takes minutes, polling records then blocking can trigger reassignment while old work continues, causing duplicates/concurrency. Decouple poll and bounded workers carefully, pause partitions, or use an appropriate queue/long-operation pattern. Do not simply raise timeouts without bounding shutdown and recovery.

Cooperative rebalancing can reduce full-stop movement, but it does not eliminate correctness duties. Static membership can reduce churn on brief restarts but delays replacement under some failures. Version-specific group protocols/configuration must follow Kafka 4.2 docs and client compatibility.

### 2.7 Offset commit patterns

The committed offset is normally the **next record to read**. If record offset 41 has been durably processed, commit 42. Auto-commit can mark records before application effects finish depending on processing structure; manual control is clearer for side effects.

- Commit before effect: crash after commit loses effect → at-most-once failure.
- Effect then commit: crash between them repeats record → at-least-once; sink must dedupe.
- Kafka transaction for Kafka-to-Kafka: output and offsets commit atomically within Kafka.

With parallel processing inside a partition, record 45 may finish before 44. Committing 46 would lose 44 on crash. Track the highest contiguous completed offset, or keep per-partition serial processing. This subtlety is common in interviews.

### 2.8 Database-to-Kafka: transactional outbox

Writing business row then publishing creates a dual-write gap. In one database transaction, write business state plus outbox event. A relay/CDC publisher reads committed outbox rows and sends Kafka. Marking published is another boundary, so duplicates can occur: send succeeds, relay crashes before marking, then sends again. Give event stable ID; consumers dedupe.

Do not delete outbox immediately without audit/replay plan. Partition/retain it, monitor oldest unpublished age and attempts, and quarantine irrecoverable payload/schema errors. CDC such as Debezium can stream a database log/outbox; it reduces polling but still needs schema, ordering, duplicate and operational handling.

### 2.9 Event schema and evolution

An event envelope should include event ID/type/schema version, occurred time, producer, tenant, aggregate type/ID/version, correlation/causation/trace IDs and typed data. `event-contract.json` is concrete. Do not expose card numbers, secrets or raw PHI. Event streams are copied, retained and broadly consumed; minimization is a security control.

Prefer facts in past tense (`PaymentAuthorized`) over commands pretending to be facts. Distinguish event time from ingestion time. Avoid exposing internal database table shape as a public event contract.

Schema compatibility:

- Backward compatible: new reader can read old data.
- Forward compatible: old reader can read new data.
- Full: both directions across supported versions.

Adding an optional field with default is often compatible; removing/renaming required field or changing type may not be. Compatibility depends on serialization system and reader behavior. Registry checks are necessary but cannot prove semantic compatibility—for example changing `amount_minor` from paise to rupees while retaining integer type passes structural checks but corrupts meaning. Include units and contract tests with real previous schemas.

### 2.10 Retention and compaction

Delete retention removes old segments by time/size. `retention.ms` is effectively a maximum consumer outage/replay window: a consumer lagging beyond it can lose required history. `retention.bytes` applies per partition in Kafka 4.2, so multiply by partitions for topic total before replication/overhead.

Log compaction retains the latest record per key eventually, not immediately and not only one record at all times. Tombstones represent deletion and themselves have retention behavior. Compaction is useful for reconstructing latest state/config, but consumers must handle multiple historical values and tombstones. Do not compact an immutable audit log if every event is required.

Storage sizing example: 10,000 events/s × 800 bytes × 86,400 seconds × replication 3 × 1.20 overhead = 2,488,320,000,000 bytes (~2.49 TB decimal) per day. It omits indexes, compression effects, headroom and other topics. The lab verifies arithmetic. Measure actual compressed bytes and replication layout.

Kafka 4.2 tiered storage separates local and remote retention but requires a configured remote-storage implementation and has documented limitations, including no support for compacted topics in that version's page. Treat feature/version/provider specifics as architecture constraints.

### 2.11 Consumer lag and capacity

Lag is latest offset minus consumer position, but offsets count records, not seconds or work. Track oldest unprocessed event age and processing-rate headroom. If arrival is 2,000/s and processing 1,500/s, lag grows 500/s: 1.8 million records/hour. Once arrival drops to 1,000/s, spare 500/s drains that backlog in one hour.

To recover a four-hour outage within two hours while normal arrival continues, consumers need sustained capacity `arrival + backlog/7200`. Partition count, hot keys and downstream rate limit may cap it. Autoscaling from lag without protecting database/API sinks can move the outage downstream.

### 2.12 Poison events, retries and dead-letter handling

A **transient** dependency error should retry with bounded backoff without blocking a whole partition indefinitely. A **poison event** deterministically fails due to schema/data/bug. Infinite retry stops later events and increases lag. Options:

- stop the partition and alert for strict ordering/correctness;
- quarantine to a governed retry/DLQ stream with original bytes, metadata and error category, then continue;
- skip only when business policy explicitly accepts loss.

A DLQ is not a trash can. It needs access controls, retention, alerting, ownership, repair tooling, replay identity and prevention of recursive failure. In healthcare/fintech, payload may be sensitive; avoid copying unnecessary PHI and preserve audit lineage.

Retry topics delay without blocking source partitions but can reorder relative to later events. If aggregate order matters, pause that key/partition or use version-aware buffering/reconciliation. Document the choice.

### 2.13 Replays and side effects

Replay is a core log advantage and a common incident source. A consumer that sends emails, charges cards or calls a model endpoint may repeat external actions. Separate pure projection rebuild from effects, gate live-effect code during replay, or have downstream idempotency keys derived from event ID. Use a new consumer group for shadow/rebuild; start offsets explicitly; cap throughput; protect downstream systems.

Record consumer version, replay range, purpose, rate and owner. Validate output before swapping a rebuilt view. Privacy deletion may conflict with long retention/replay; use minimization, crypto-shredding/compaction/tombstones and governed policies appropriate to law and architecture.

### 2.14 Observability and operations

Producer metrics: record/error/retry rate, request latency, batch size, compression ratio, buffer exhaustion, delivery timeout. Broker: under-replicated/offline partitions, ISR changes, request latency, disk/network, controller health, replication lag. Consumer: records/s, lag and age per partition, poll/process time, rebalance frequency/duration, commit failures, duplicates, poison/DLQ and sink latency.

Alert on user-relevant lag age and durability risk, not a single global sum. One hot partition can be hidden by 99 idle partitions. Include topic/partition/group in diagnostics but avoid high-cardinality raw event IDs in metrics. Trace asynchronous causality with trace/correlation IDs and links rather than pretending one continuous synchronous span.

## 3. WORKED PROBLEMS

### Problem 1 — Partition key

**Statement.** Payment lifecycle events must be ordered; tenant-wide ordering is unnecessary. Choose a key.

**Solution.** Key by stable payment ID. All versions of one payment map to one partition, while a tenant's payments distribute. Include tenant in authorization/envelope and aggregate version for gap detection. Keying by tenant creates hot/serialized partitions; random key breaks lifecycle order.

**Mistake caught.** Claiming Kafka has topic-wide order across partitions.

### Problem 2 — Consumer parallelism

**Statement.** Topic has 12 partitions; group deploys 20 single-threaded consumers. How many can actively own partitions?

**Solution.** At most 12 consumers own one or more partitions, so at least eight are idle for that topic/group. More instances can aid failover but not active partition parallelism. Raise partitions only after measuring and considering key remapping/operational cost.

**Mistake caught.** Assuming consumers, not partitions, define unlimited parallelism.

### Problem 3 — Retention storage

**Statement.** 10,000 events/s, 800 bytes average, one day, RF=3, 20% overhead. Estimate bytes.

**Solution.** `10000×800×86400×3×1.2=2,488,320,000,000 bytes`, about 2.49 TB decimal (2.26 TiB). Compression may reduce payload, while indexes/headroom increase it; measure actual broker segment bytes. Retention-bytes is per partition.

**Mistake caught.** Forgetting replication or multiplying after assuming compressed size without evidence.

### Problem 4 — Offset/effect crash

**Statement.** Consumer writes PostgreSQL then crashes before committing Kafka offset.

**Solution.** Record is redelivered. In one DB transaction, insert `event_id` into processed-event table with UNIQUE and apply business update. First succeeds; duplicate detects existing identity and does not repeat effect. Then commit offset. Keep dedupe at least as long as possible redelivery/replay guarantee.

**Mistake caught.** Calling manual offset commit exactly once.

### Problem 5 — Parallel offset gap

**Statement.** Offsets 40–45 process concurrently; 45 finishes, 44 has not. May consumer commit 46?

**Solution.** No: committed 46 means resume at 46, losing 44 after crash. Commit only highest contiguous completed next offset—44 if 40–43 complete and 44 pending—or keep partition serial. Buffer completion acknowledgements and advance watermark when gaps close.

**Mistake caught.** Committing maximum finished offset.

### Problem 6 — Outbox failure

**Statement.** Relay publishes event, crashes before marking outbox published.

**Solution.** On restart it publishes same stable event ID again. Kafka idempotent producer may not cover a logically repeated send across relay/application behavior, so consumer dedupes event ID. Relay marking is idempotent; monitor attempts/age. Business row and original outbox were atomic, preventing missing event.

**Mistake caught.** Claiming outbox prevents duplicates.

### Problem 7 — Schema change

**Statement.** Rename required `amount` to `amount_minor` and change rupees to paise.

**Solution.** This is structurally and semantically breaking. Add new field/schema version while retaining old for a compatibility window; producers populate both consistently with exact decimal conversion; deploy consumers understanding new and old; validate amounts/units; stop old readers, then remove only in a later major contract. A schema registry cannot infer unit correctness.

**Mistake caught.** Treating same numeric type as compatible semantics.

### Problem 8 — Poison event with strict order

**Statement.** Payment v7 cannot deserialize; v8 and v9 follow in same partition.

**Solution.** If lifecycle order is mandatory, do not apply v8/v9. Stop/pause partition, quarantine v7 securely with metadata, alert owner, deploy compatible reader/repair and resume/replay. Sending v7 to DLQ and continuing would create a version gap; a consumer can detect and buffer/reconcile only if that protocol is designed.

**Mistake caught.** “Always DLQ and continue.”

### Problem 9 — Lag recovery

**Statement.** Arrival 2,000/s, consumption 1,500/s for one hour. Then arrival is 1,000/s, capacity remains 1,500/s.

**Solution.** Backlog grows `(2000-1500)×3600=1,800,000`. Spare capacity becomes 500/s, so drain takes `1,800,000/500=3,600 s` = one hour. Verify retention exceeds outage+recovery and downstream tolerates 1,500/s.

**Mistake caught.** Using total consumption 1,500/s as backlog drain rate while new traffic continues.

## 4. REAL-WORLD / APPLIED CONTEXT

**Kafka durability configuration.** Apache Kafka 4.2 documents idempotence enabled by default absent conflicts, requiring acks all, retries and at most five in-flight requests per connection. It documents RF=3/min ISR=2/acks all as a typical durability setup. These guarantees apply within stated Kafka protocol/configuration—not external databases.

**Payment outbox.** PostgreSQL transaction writes payment version 7 and `payment.authorized` outbox event. Debezium or a relay publishes to Kafka keyed by payment ID. Fraud, ledger and notification groups consume independently. Ledger applies event ID + update atomically; notification derives an idempotency key for its provider. Replay rebuilds fraud projection without resending email.

**ML platform events.** Training run state uses run ID key and versions; large model artifacts stay in object storage, while event carries immutable URI, digest and metadata. A model promotion topic may be compacted for current pointer plus a separate immutable audit topic. Raw training data/PHI is not embedded in long-retained events.

The included event JSON is a concrete version-2 contract. `KafkaSemanticsLab` executes partition determinism, one-day storage arithmetic, backlog, duplicate and version-gap behavior without claiming to emulate Kafka internals.

## 5. COMPARISON TABLE

| Choice | Guarantee/use | Throughput/availability | Failure boundary |
|---|---|---|---|
| `acks=0` | no broker confirmation | lowest acknowledgement latency | silent loss; no useful retry evidence |
| `acks=1` | leader local append | available with leader | leader failure before replication can lose |
| `acks=all`, RF3, minISR2 | ISR acknowledgement/durability posture | rejects when insufficient ISR | still needs storage/cluster/DR design |
| Idempotent producer | dedup producer protocol retries | slight protocol state | not business/consumer exactly-once |
| Kafka transaction | atomic Kafka records+offsets | coordinator/latency/timeout | excludes arbitrary external systems |
| DB idempotent sink | repeated input, one DB effect | unique/index write | retention/replay identity required |
| Transactional outbox | DB state and intent atomic | relay/CDC complexity | duplicate publish remains possible |

| Retention | Best use | Replay behavior | Risk |
|---|---|---|---|
| Delete by time/size | immutable event history window | all records within retained segments | slow consumer can fall off end |
| Log compaction | latest value per key reconstruction | historical duplicates/tombstones remain transiently | not full audit history |
| Local + tiered | long replay with smaller broker-local set | old reads use remote tier | provider/version limits and latency |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Kafka guarantees global order.”** Order is per partition; keys define which events share it.
2. **“More consumers always increase throughput.”** Active group parallelism is capped by partitions.
3. **Random keys for balance.** They destroy aggregate order and make reconstruction harder.
4. **Changing partition count harmlessly.** Default key mapping may change for future records.
5. **`acks=all` means every configured replica forever.** It means current ISR; min ISR/configuration matters.
6. **Producer idempotence is business idempotence.** Duplicate commands with new event identities still append.
7. **Kafka transactions include PostgreSQL.** They atomically cover Kafka operations, not arbitrary sinks.
8. **Auto/manual commit equals exactly once.** Commit timing trades loss versus duplicates; sink idempotency matters.
9. **Committing maximum parallel completion.** Gaps before that offset are lost on restart.
10. **Outbox removes duplicates.** It removes DB/event missing dual-write gap; relay can repeat publishes.
11. **DLQ every failure and continue.** Strictly ordered aggregates can be corrupted by skipping a version.
12. **Schema registry proves semantics.** Units/meaning can change while types remain compatible.
13. **Lag count alone is enough.** Record cost varies; oldest age and per-partition skew matter.
14. **Queue absorbs sustained overload.** Arrival greater than service grows without bound until retention/storage.
15. **Replay is safe because consumers are idempotent.** External email/payment effects need their own identity/gating.
16. **Put model binaries/PHI in events.** Retention/copying/security and payload cost make object references/minimization safer.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Topic → partitions → ordered offsets; no order across partitions.
- Key by aggregate needing order; include event ID + aggregate version.
- Group: one partition owned by at most one consumer at a time; partitions cap parallelism.
- Kafka 4.2 strong producer posture: acks all + replication + min ISR; idempotence default if no conflicts.
- Idempotent producer dedupes producer retries, not business commands/consumer effects.
- Kafka transaction: Kafka writes + offsets; `read_committed`; external DB still needs protocol.
- Side effect then offset = at least once; unique event ID + business update in one sink transaction.
- Parallel per partition: commit highest contiguous completed offset, not maximum finished.
- DB→Kafka: transactional outbox; duplicates still possible, missing committed intent prevented.
- Retention is recovery SLA; size by rate × bytes × seconds × RF × overhead/headroom.
- Lag growth = arrival − service; drain uses spare capacity after ongoing arrivals.
- DLQ/quarantine has owner, security, retention and replay; strict order may require partition stop.
- Schema compatibility includes semantics, units and old/new fixtures, not only registry syntax.

## 8. PRACTICE SET FOR SELF-TEST

1. A topic has 24 partitions and 36 consumers in one group; then six consumers fail. State active/idle counts before and assignment capacity after.
2. Size seven-day storage for 4,000 events/s, 1,200-byte observed compressed records, RF=3 and 15% overhead.
3. Explain the exact failure that makes effect-then-offset at least once and implement the sink transaction in pseudocode.
4. Offsets 100–105 run concurrently; 100,101,103,104 finish. What next offset may be safely committed?
5. Choose partition keys for account ledger, payment lifecycle and global configuration; discuss hot-key/order trade-offs.
6. Design an outbox table, relay state and monitoring for 20,000 events/s.
7. An old consumer ignores unknown fields but crashes on unknown enum. Is adding an enum forward-compatible? Give rollout.
8. Consumer lag is 9 million, arrival 3,000/s, capacity 5,000/s. Calculate drain time while arrival continues and name constraints that could invalidate it.
9. A poison clinical event contains PHI and blocks one partition. Design quarantine, access, repair and resumption.
10. Explain what Kafka exactly-once can and cannot guarantee for Kafka input → Kafka output → email provider.

## 9. CURATED RESOURCES

1. Apache Kafka 4.2, [Introduction](https://kafka.apache.org/documentation/). Canonical event/topic/partition/key/order and platform capability overview.
2. Apache Kafka 4.2, [Producer Configs](https://kafka.apache.org/42/configuration/producer-configs/). Exact acks, retries, delivery timeout, idempotence, in-flight and transactional-ID behavior.
3. Apache Kafka 4.2, [Consumer Configs](https://kafka.apache.org/42/configuration/consumer-configs/). Exact group, poll, heartbeat, isolation and offset-reset controls.
4. Apache Kafka 4.2, [Topic Configs](https://kafka.apache.org/42/configuration/topic-configs/). Retention, compaction, min ISR and per-partition size semantics.
5. Apache Kafka 4.2, [Design](https://kafka.apache.org/42/design/). Replication, log, delivery semantics, transactions and consumer position internals.
6. Apache Kafka 4.2, [Tiered Storage](https://kafka.apache.org/42/operations/tiered-storage/). Local/remote retention configuration and version-specific limitations.
7. Kreps, Narkhede and Rao, “Kafka: a Distributed Messaging System for Log Processing,” NetDB 2011. Original architecture/motivation and early measured design.
8. Kleppmann, *Designing Data-Intensive Applications*, Chapters 11–12. Event logs, stream-table duality, time, joins and fault tolerance beyond client settings.
9. Richardson, *Microservices Patterns*, chapters “Transactional Outbox,” “Polling Publisher” and “Transaction Log Tailing.” Cross-database publication patterns and trade-offs.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Failure Semantics.** Retries, ambiguous outcomes, queues and backpressure explain duplicate delivery and lag.
2. **Transactions and Locking.** Local atomicity enables outbox and idempotent consumer-side database effects.
3. **Data Migrations.** CDC, schema compatibility and replay move durable data safely.

### After

1. **Consistency and Idempotency.** Duplicate/order/replication semantics become end-to-end workflow guarantees.
2. **Capacity-Driven System Design.** Partitions, rate, bytes, retention and recovery targets determine cluster/consumer sizing.
3. **Observability.** Per-partition lag age, ISR, rebalance and attempt metrics become SLO signals.
4. **MLOps Pipelines.** Training, registry and deployment lifecycles use versioned events without embedding large artifacts.

---ANSWER KEY BELOW---

1. Before: 24 active owners and 12 idle. After six arbitrary consumers fail, 30 remain, still enough for 24 active and six idle after rebalance, assuming healthy membership; partition movement may temporarily pause work.
2. `4000×1200×604800×3×1.15 = 10,014,336,000,000 bytes`, about 10.01 TB decimal (9.11 TiB). Add headroom/indexes and validate whether 1,200 already reflects compression; retention.bytes is per partition.
3. DB commit succeeds; process dies before Kafka offset commit; record redelivers. Begin DB tx, insert event ID UNIQUE; if new, apply business mutation; commit DB; then commit next Kafka offset. Duplicate finds ID and skips/returns prior effect before offset commit.
4. Commit next offset 102: offsets 100–101 are contiguous complete, while 102 is unfinished. Finishing 103/104 cannot move watermark over 102.
5. Ledger key account ID for total account order (hot account risk); payment key payment ID for lifecycle order/distribution; global config may use config-name key in compacted topic, accepting one hot key per config and version checks. Tenant key is broader than needed.
6. Outbox: event ID PK, aggregate/key/version, type/schema, payload/reference, occurred time, status/lease/attempt/published time. Write with business tx; partition/claim batches; publish stable ID/key; mark after ack; retry duplicates. Monitor oldest unpublished age, rate, attempts/errors, table/WAL/disk and Kafka latency.
7. No, not for an exhaustive old reader: new writer can send a value old consumer cannot decode. Deploy tolerant/readers understanding new enum first, then permit schema and emitters; keep old value/unknown handling through rollback window.
8. Spare capacity `5000-3000=2000/s`; `9,000,000/2000=4,500 s` = 75 minutes. Partition/hot-key parallelism, downstream limits, variable event cost, rebalances, new rate and retention can invalidate it.
9. Pause partition for strict order; copy encrypted/minimized original plus topic/partition/offset/schema/error to restricted quarantine, alert named clinical-data owner, fix reader/data under audit, replay same event ID and verify aggregate version, then resume. Set retention/deletion/access logs; do not expose PHI in generic logs/DLQ dashboards.
10. Kafka transaction can atomically consume offsets and produce output records, and read-committed consumers avoid aborted outputs. Email provider lies outside Kafka; crash after email send before durable acknowledgement can resend. Derive provider idempotency key from event ID or record a durable effect/reconciliation protocol.
