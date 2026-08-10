# SRE and Observability Capstone — Operate a Regulated Inference Platform

## Objective

Operate a multi-region claims-risk inference platform through normal load, a bad release, a zone disruption and a regional disaster. Produce executable SLO, telemetry, incident and recovery evidence proving user outcomes, data/model correctness, privacy and achieved capacity/RPO/RTO. Dashboards and architecture diagrams alone do not pass.

## Product and workload contract

- 43.2 million logical prediction requests/day, measured 6× peak-to-average: derive 3,000 RPS forecast peak.
- Availability SLO 99.9% over rolling 30 days; 99% of admitted requests ≤250 ms and 99.9% ≤1 s.
- A prediction using wrong tenant/model or unauthorized patient context is an invariant violation, not an error-budget event.
- Async audit export is complete within five minutes for 99.95% of accepted predictions; immutable source events permit replay.
- One pod's measured safe capacity is 250 useful RPS in the named test environment. Plan 30% headroom and one-of-three-zone loss.
- Regional DR: critical inference RTO ≤45 minutes, acknowledged audit-event RPO ≤30 seconds. Analytics RPO ≤15 minutes.
- Telemetry must not contain prompts, patient/account IDs, authorization material or unbounded metric labels.
- The response team must provide SEV-1 updates at least every 15 minutes for the exercise.

## Required observability design

1. Write versioned SLI specifications for availability, two latency thresholds, audit freshness and tenant/model correctness. Define valid/good/bad/excluded/missing, logical request versus attempt, measurement boundary and segments.
2. Implement counters and SLO-aligned histograms with bounded route/region/status/model-tier labels. Calculate worst-case series, including buckets, and enforce a budget.
3. Emit structured safe logs with event, trace/span, release/model digests and error category. Negative tests inject bearer token, patient ID and account number and prove redaction/rejection.
4. Propagate W3C trace context through gateway → Java API → Kafka → Python worker → model/data dependencies. Model retry and batch fan-in with distinct spans/links.
5. Deploy redundant OpenTelemetry Collectors with queue/memory limits, bounded retries and explicit drop behavior. Monitor accepted/refused/dropped data and freshness.
6. Build one landing dashboard that answers user impact first, then links exemplars/traces/logs/release changes and cause metrics.
7. Implement multi-window burn-rate paging and slow-burn ticketing. Test both true and false cases plus low/no-traffic behavior.

## Capacity and recovery calculations

Calculate average/peak, healthy pods at 30% reserve, balanced three-zone total retaining healthy capacity after one-zone loss, in-flight concurrency at p50/p99 assumptions, database/Kafka/GPU/connection/NAT/IP limits, backlog drain with ongoing arrivals, and 30-day telemetry/storage cost. Label requirement, measurement, forecast, assumption and derivation.

Produce low/base/high growth cases and one hot tenant/partition case. Prove downstream useful throughput at catch-up rate. Verify secondary-region quota, immutable artifacts, identities, private DNS, certificates, keys, configuration, backups and staff access before the drill.

## Mandatory experiments

1. Feed deterministic good/bad event counts and prove SLO budget/burn queries match independent integer calculation.
2. Restart instrumented instances and prove counter-reset queries do not generate negative/fake spikes.
3. Generate a dynamic-ID route and show route normalization/cardinality control prevents series explosion.
4. Break trace propagation across Kafka, detect the orphan/gap, then fix parent/link semantics.
5. Fail telemetry backend for 30 minutes; production latency remains within guardrail and drop/queue evidence is visible.
6. Release a configuration producing 2% errors in one region. Confirm paired burn alert, declare incident, assign IC/Ops/Comms/scribe and run one logged change queue.
7. Provide 15-minute updates, rollback/canary, verify user SLI and tenant/model audit invariant, and close only after recovery gates.
8. Remove one availability zone at 3,000-RPS forecast. Demonstrate placement and remaining reserved/downstream capacity or controlled shedding.
9. Create 3.6-million Kafka backlog while 2,000/s continues; safely deliver 5,000/s and compare measured drain with 20-minute derivation.
10. Trigger regional disaster. Fence writers, recover/promote data, identity/network/DNS/app in dependency order, canary traffic and calculate achieved RPO/RTO from timestamps.
11. Serve writes in secondary, then fail back by rebuilding/synchronizing/fencing primary; prove counts/checksums/tenant/model invariants and no acknowledged-write loss beyond objective.
12. Restore an isolated backup and verify encryption keys, schema, object/event/database consistency and application business queries—not only file existence.

## Incident and postmortem deliverables

- Incident record with impact, severity, roles, state, hypotheses, decisions, changes, evidence, updates and explicit handoff if response exceeds four hours.
- Security/privacy escalation branch for suspected cross-tenant result or credential exposure, including containment and chain of custody.
- Recovery gates: SLO burn normal across defined windows, critical segments, audit correctness, backlog/capacity, no persistence/adversary indicator and stakeholder update.
- Blameless postmortem with causal conditions, what went well/poorly/luck and no patient/account data.
- Five owned, due, prioritized and verifiable actions spanning prevention, detection, mitigation speed, response process and recovery.

## Evidence bundle

1. SLI specs, queries, independent calculator outputs and error-budget policy.
2. Metric/log/trace schemas, cardinality worksheet, sampling/retention/cost and privacy tests.
3. Alert tests, dashboards, trace/log exemplars and telemetry pipeline failure results.
4. Load-test method/data/environment/version, useful throughput, latency percentiles, errors/shed and bottleneck evidence.
5. Capacity/failure matrix, regional quota and cost/date/SKU evidence.
6. Incident timeline, commands/change IDs, communications and recovery verification.
7. Backup/restore, failover/failback timestamps and RPO/RTO/reconciliation evidence.
8. Postmortem review and verified corrective-action tracker.
9. A 30-minute oral defense plus live injected symptom.

## Mastery gates

- SLO denominator counts logical user attempts at an authoritative boundary and treats missing telemetry explicitly.
- Aggregate results cannot hide complete critical region/tenant/model-tier failure.
- Metric labels are bounded; logs/traces contain no regulated payload or credentials.
- Trace duration reasoning does not sum overlapping/parent spans or forge synchronous parents for async fan-in.
- Telemetry failure cannot collapse the production request path; loss is measured.
- Pages reflect actionable SLO threat or correctness/security invariant, not arbitrary CPU.
- One zone can fail without relying on slow autoscaling, or the documented degradation remains within contract.
- Backlog calculation uses net service minus continuing arrivals and protects downstream sinks.
- Recovery proves business flow, identity/DNS/data/model correctness—not merely running compute.
- RPO/RTO are measured from disaster/newest durable point to verified user recovery; targets are not claimed as results.
- Failover/failback fence writer authority and reconcile acknowledged data.
- Postmortem actions have owner, due date and objective closure evidence.

## Rubric (100)

| Area | Points |
|---|---:|
| SLI/SLO/error-budget specification and alerts | 20 |
| Metrics/logs/traces correctness, correlation and privacy | 20 |
| Incident command, communication and learning | 20 |
| Capacity, overload, zone-loss and backlog evidence | 20 |
| DR, backup, failover/failback and RPO/RTO proof | 15 |
| Reproducibility and oral defense | 5 |

Pass at 80+, with every mastery gate mandatory.
