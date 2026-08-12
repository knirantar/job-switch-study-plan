# Parent 06 — SRE and Observability

This parent turns user-visible reliability objectives into telemetry, incident action,
capacity and tested recovery.

No production-operations, reliability, or monitoring knowledge is assumed.

## Phase A — Prerequisites

1. [Production Operations Foundations](05-production-operations-foundations/lesson.md) — environments, releases, configuration, ownership, runbooks, changes, on-call, service lifecycle and operational evidence.
2. [Reliability, Availability, and Failure Basics](06-reliability-availability-failure-basics/lesson.md) — failure domains, redundancy, degradation, overload, repair, risk and quantitative availability foundations.
3. [Monitoring and Alerting from Scratch](07-monitoring-alerting-basics/lesson.md) — signals, metrics/logs/events/traces, dashboards, thresholds, anomaly detection, alert quality, routing and initial diagnosis.

## Phase B — Existing advanced sequence

4. [SLIs, SLOs, and Error Budgets](01-sli-slo-error-budgets/lesson.md) — complete; includes exact request/time budgets, multi-window burn alerts, low-traffic treatment, and six passing calculator tests.
5. [Metrics, Logs, and Traces](02-metrics-logs-traces/lesson.md) — complete; includes Prometheus/OpenTelemetry mechanics, cardinality/cost, correlation/sampling, and five passing telemetry-policy tests.
6. [Incident Response](03-incident-response/lesson.md) — complete; includes incident command, security containment/evidence, recovery verification, postmortems, and six passing incident-record policy tests.
7. [Capacity and Disaster Recovery](04-capacity-dr/lesson.md) — complete; includes safe capacity, overload/backlog, zone-loss sizing, backup/failover/failback, and six passing capacity/RPO/RTO tests.

After all seven lessons, complete the [SRE and Observability Capstone](CAPSTONE.md), including its mandatory zone-loss, incident and regional-recovery experiments.
