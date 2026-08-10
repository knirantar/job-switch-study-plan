# Distributed Systems Capstone — Multi-Region Model Authorization Platform

## Objective

Design and prototype a platform that receives model-deployment requests from fintech and healthcare tenants, verifies policy, deploys asynchronously, and exposes durable status. It must behave correctly under response loss, duplicate events, Kafka rebalances, regional partitions, cache failure and backlog recovery.

The deliverable is an evidence-backed architecture and failure harness, not only a diagram.

## Product contract

- `POST /v1/deployments` accepts tenant-scoped idempotency key and immutable model digest.
- Synchronous response returns a durable operation ID within 400 ms p99 or an explicit rejected/unavailable response; timeout never means deployment failed.
- Deployment lifecycle is ordered per deployment and fully auditable.
- A mutable approved-model pointer cannot regress to an older generation.
- Healthcare authorization/consent reads cannot silently use stale data beyond the approved policy.
- Large artifacts are content-addressed in object storage; events contain digest/URI, not bytes or raw PHI.
- Clients can query/cancel, while cancellation is a request whose eventual outcome is explicit.

## Workload to design

- 40 million metadata reads/day, measured 5× peak-to-average.
- 120,000 deployment submissions/day, with a launch burst of 200/s for ten minutes.
- 12,000 lifecycle events/s platform-wide, 1.2 KiB observed compressed average, seven-day replay, RF=3 and 20% storage/headroom factor.
- 480 training/deployment jobs/day averaging 2.5 GPU-hours; six-hour 4× peak.
- Largest tenant can create 18% of requests; one model pointer may receive 80,000 reads/s.
- Three zones per region; service must survive one zone loss without waiting for autoscaling.
- Metadata read availability SLO 99.95%; deployment acceptance 99.9%; payment/consent correctness is invariant, not error-budgeted corruption.
- RPO 0 for accepted operation identities in-region, cross-region DR RPO ≤30 seconds, RTO ≤45 minutes.

## Required architecture evidence

1. Label every numeric input as requirement, measured value, forecast, assumption or derivation.
2. Calculate peak API/event rates, seven-day Kafka storage, normal/zone-loss replicas, GPU demand, cache-down source load and backlog recovery.
3. Define synchronous deadline allocation across edge, auth, policy DB, operation transaction and response reserve.
4. Specify PostgreSQL idempotency/outbox schema, Kafka topic/partition keys, event envelope/schema compatibility and consumer inbox.
5. State consistency per datum: operation state, approved pointer, public metadata, consent, analytics.
6. Map failure domains: process, zone, region, database/Kafka/cache, identity, DNS, deployment, quotas and operator credentials.
7. Define tenant admission/quotas and cost controls.

## Mandatory failure experiments

Run in disposable local/staging infrastructure and record logical requests separately from attempts:

1. Drop response after operation/outbox database commit; same idempotency key returns one operation.
2. Publish outbox event, crash before marking; consumer applies one durable effect despite duplicate.
3. Process Kafka offsets concurrently with a gap; prove only the highest contiguous offset is committed.
4. Produce aggregate version 3 before 2 in a test repair stream; consumer quarantines rather than regresses.
5. Partition regional policy replica from authority; consent-sensitive operation rejects/routes while public metadata serves explicitly bounded stale data.
6. Pause lease owner beyond expiry; a newer fencing token prevents stale mutation.
7. Remove one zone at forecast peak and verify useful throughput plus shedding remain within SLO design.
8. Disable Redis during hot-key load; bulkhead/source protection prevents database cascade.
9. Create Kafka backlog and demonstrate drain calculation matches measured order of magnitude without overwhelming sinks.
10. Recover an open circuit with bounded, jittered half-open probes.

## Workflow state machine

At minimum: `RECEIVED → POLICY_APPROVED → QUEUED → DEPLOYING → ACTIVE`, with `REJECTED`, `CANCEL_REQUESTED`, `CANCELLED`, `OUTCOME_UNKNOWN`, `COMPENSATION_PENDING`, and `FAILED_FINAL`. Every transition uses expected state version and unique command ID. Remote timeouts enter unknown/reconciliation, never invented failure. Compensations are explicit idempotent actions and retained in audit history.

## Observability and runbook

Provide dashboards/alerts for:

- logical RPS versus attempt/retry/hedge RPS;
- remaining deadline and timeout phase;
- idempotency hits/conflicts/in-progress age;
- outbox oldest unpublished age;
- Kafka per-partition lag age, rebalance and poison quarantine;
- saga state age and compensation failure;
- cache hit/miss/hot key and source fallback;
- useful throughput, shed/degraded results, CPU/RSS/GC/pools;
- database latency/locks/WAL and regional replication lag;
- GPU queue age, utilization, checkpoint/retry and tenant share.

Runbook must define pause, shed, failover, reconcile, replay and failback. Logs/events/metrics must not expose secrets or raw PHI.

## Deliverables

1. Architecture diagram and dependency/failure-domain map.
2. Completed capacity worksheet with low/base/high cases.
3. API and event contracts plus schema-compatibility fixtures.
4. Executable DDL/outbox/inbox/state machine.
5. Producer/consumer configuration rationale tied to Kafka version.
6. Failure-injection harness and captured histories/final assertions.
7. Load-test report with environment, dataset, cache state, concurrency, duration and percentiles.
8. SLO/RPO/RTO and overload/failover runbook.
9. Threat/privacy analysis for tenant isolation, authorization, replay and retained events.
10. Twenty-minute oral defense.

## Mastery gates

- One duplicate/timeout cannot create two logical deployments or external effects.
- Per-aggregate ordering is explicit; no claim of global Kafka ordering.
- Exactly-once claims name their boundary; external sinks are idempotent/reconciled.
- CAP/consistency decision is per operation and uses partition behavior, not “choose two” shorthand.
- Queue/cache/zone failure calculations include downstream protection and recovery capacity.
- Every measured number is reproducible; every assumption is visible.
- Regulated authorization fails according to approved safety policy and tenant data never crosses scope.

## Rubric (100)

| Area | Points |
|---|---:|
| Failure semantics and idempotent API | 20 |
| Kafka ordering/delivery/schema/replay | 20 |
| Consistency, saga and fencing correctness | 20 |
| Capacity, overload and recovery evidence | 20 |
| Security/privacy/tenant isolation | 10 |
| Reproducibility and oral defense | 10 |

Pass at 80+, with every mastery gate mandatory.
