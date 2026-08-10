# Capacity-driven design worksheet

Fill this before drawing components.

1. Functional operations and invariant owner.
2. Users/tenants/regions; largest tenant and abuse boundary.
3. Daily/peak reads and writes; peak shape, burst duration and annual growth.
4. Payload/request/response/event/artifact sizes with percentile distributions.
5. Latency SLO by operation and end-to-end deadline allocation.
6. Availability target, excluded cases, consistency model and stale-read bound.
7. Retention, backup, RPO, RTO and replay/catch-up objectives.
8. CPU/request, memory/in-flight, DB connections, network and storage equations.
9. Normal, one-zone-failed, cache-cold and dependency-degraded capacity.
10. Admission, rate limits, queues, retry budget and degradation priorities.
11. Security/tenant/privacy/data-residency constraints.
12. Cost drivers, uncertainty ranges and the measurements needed to replace estimates.

For each number label it: measured, product requirement, forecast, derived, or assumption.
