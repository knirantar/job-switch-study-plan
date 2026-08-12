# Monitoring and Alerting from Scratch

Parent subject: `06-sre-observability`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why observe a system

Production systems change continuously: traffic, data, releases, dependencies, hardware, certificates, and attacks. **Monitoring** collects and evaluates information about known aspects of a system over time. **Observability** is the ability to infer internal state from external outputs, especially for questions not predetermined. Telemetry supports both, but installing a metrics agent does not automatically make a system observable.

The first purpose is user protection: detect meaningful failure, guide diagnosis, confirm mitigation, and learn. Secondary purposes include capacity, security, cost, product behavior, audit, and planning. Monitoring every available number without a question creates cost and noise.

Early operations watched host up/down and resource thresholds. Modern distributed systems require service-level outcomes and cross-component correlation. A host CPU alert can miss a correctness failure and page during harmless batch work. Start from critical user journeys, then connect symptoms to causes.

### Signals and telemetry types

A **signal** is measured evidence. Common telemetry:

- **Metric:** numeric measurement over time, e.g. request count or queue depth.
- **Log:** timestamped event record with fields and context.
- **Trace:** representation of one request/workflow across operations called spans.
- **Event:** discrete state change such as deployment, autoscale, failover, or config update.
- **Profile:** aggregated samples of code/resource behavior, such as CPU stack frequency.

Metrics aggregate cheaply and show trends; logs give event detail; traces show causal request path; profiles reveal where runtime resources are spent. They complement rather than replace one another. Correlation uses timestamps, service/resource identity, trace/request/event IDs, deployment digest, and tenant-safe dimensions.

### Metric types

A **counter** monotonically increases except reset, e.g. total requests. Derive a rate over a window; raw counter value is rarely actionable. A **gauge** moves up/down, e.g. queue depth or current memory. A **histogram** counts observations in buckets and tracks count/sum, allowing aggregation and percentile approximation. A **summary** may calculate client-side quantiles with limited cross-instance aggregation depending implementation.

Do not average percentiles. If instance A p99=100 ms and B p99=1,000 ms, the fleet p99 is not 550 ms; request volume/distribution matters. Aggregate histogram buckets or raw distributions.

A metric includes name, value, timestamp, and **labels/dimensions** such as service, route, method, status class, region, and version. Every unique label combination is a time series. Unbounded labels—user ID, request ID, raw URL, exception message—create cardinality explosion, memory/storage/query cost, and instability.

### Logs

Structured logs use stable fields rather than prose parsing:

```json
{"time":"2026-08-12T10:42:17.123Z","level":"ERROR",
 "service":"claims-api","event":"dependency_timeout",
 "dependency":"postgresql","route":"POST /v1/claims",
 "durationMs":750,"traceId":"01J5...","version":"sha256:..."}
```

Log the decision/outcome and safe identifiers, not passwords, tokens, PAN/CVV, or clinical payload. Redaction at collection is weaker than never emitting. Define retention and access by classification. Sampling high-volume success logs saves cost; retain error/security/audit evidence according to requirements.

### Traces and spans

A trace contains spans with start/duration, parent relationship, service/operation, status, and attributes. Context propagates across HTTP/RPC and messaging. A trace can show 700 ms total consisting of 20 ms gateway, 30 ms app, 600 ms DB pool wait/query, and 50 ms response.

Sampling chooses which traces to retain. Head sampling decides near trace start and may miss rare failures; tail sampling decides after observing outcome but requires buffering/coordination. Keep all critical errors/high latency where feasible and sample common successes, respecting privacy and cost. A trace is evidence for selected requests, not fleet-wide statistics unless sampling is accounted for.

### User symptoms and resource causes

Google SRE's “four golden signals” are latency, traffic, errors, and saturation. The RED method monitors Rate, Errors, Duration for request-driven services. USE monitors Utilization, Saturation, Errors for resources. Apply them together:

- User symptom: successful claim rate falls, p99 rises.
- Service demand: request rate and payload mix.
- Resource cause: DB pool saturation, CPU throttling, queue age, disk latency.

Alert primarily on user-impact/SLO risk; diagnose with cause signals. Cause alerts may page when immediate action prevents impact, e.g. disk will fill within two hours and automated remediation cannot act.

### Baselines, thresholds, and anomalies

A **static threshold** compares to a fixed value, suitable for hard limits or well-known safe capacity. A **dynamic threshold** compares to historical/seasonal baseline. **Anomaly detection** identifies unusual patterns statistically. It can detect unknown deviations but also pages on harmless launches/holidays and miss gradual degradation.

A threshold needs direction, aggregation, scope, window, minimum traffic, and persistence. “CPU >80%” omits whether one sample, mean, max, all instances, five minutes, and whether user impact occurs. Hysteresis uses different fire/clear conditions to prevent flapping.

### Alerts, pages, tickets, and notifications

An **alert rule** evaluates a signal and creates state. A **notification** routes that state. A **page** interrupts on-call for urgent action. A ticket is asynchronous work; dashboards are observation. Not every alert should page.

A good page is:

- user/business meaningful or imminently threatening;
- urgent;
- actionable by recipient;
- specific in service/scope/severity;
- linked to dashboard/runbook/recent changes;
- deduplicated/grouped/inhibited during root-cause incidents;
- tested and owned.

Alert fatigue causes missed real incidents. Measure pages per shift, acknowledgment, actionable rate, false positives, duplicates, manual toil, and after-hours load. Delete or redesign unactionable alerts rather than merely increasing thresholds.

### Alert state and missing data

Rules often have pending/firing/resolved states. A `for: 5m` condition requires continuous truth for five minutes, filtering spikes but delaying detection. Missing samples can mean service down, collector down, scrape failed, no traffic, or query error. Decide per signal: absence of heartbeat may be failure; absence of errors during zero traffic is normal.

Counter resets on restart must not appear as negative traffic. Rate functions account for resets when used correctly. Late/out-of-order data and clocks affect logs/traces; telemetry pipeline health needs its own monitoring without infinite self-dependency.

### Dashboards

A dashboard answers a question for an audience. A service overview should show SLO/user journeys, traffic, errors, latency distributions, saturation, dependencies, deployments/config events, and regional/version breakdown. Start broad, then link drill-down.

Avoid dashboards with 100 unlabeled charts, inconsistent time zones, hidden units, and auto-scaled axes that exaggerate noise. Display units, definitions, target lines, query links, freshness, and ownership. A dashboard is not an alert; nobody watches it continuously.

### Synthetic and real-user monitoring

**Synthetic monitoring** sends controlled requests from chosen locations, catching DNS/TLS/routing/auth/workflow issues even with no users. It requires safe test identities/data cleanup and should not mutate real records unintentionally. **Real-user monitoring** measures actual client experience and device/network diversity but can be sparse, sampled, privacy-sensitive, and delayed.

Black-box monitoring observes external behavior; white-box uses internals. Both are required. An internal health endpoint can be green while public DNS or identity is broken.

## 2. CORE MECHANICS

### 2.1 Define a metric contract

For HTTP requests:

```text
http_server_requests_total{
 service="claims-api", route="POST /v1/claims",
 method="POST", status_class="2xx", region="centralindia",
 version="sha256:ab12..."
}
```

Use templated route, not raw `/claims/C-1042`; status class or bounded status code; bounded version/region. Define counter inclusion: when incremented, retries, canceled requests, authentication, and success semantics. Technical 2xx may not mean business success, so add domain outcome counters with bounded reason codes.

### 2.2 Compute rate and error ratio

Over five minutes, valid requests 600,000 and service-attributable bad 3,000. Error ratio=.005=0.5%; throughput=2,000 rps. Do not divide rate of errors by mismatched denominator/window/labels. Exclude invalid requests only according to documented SLI, not to improve charts.

At low traffic, 1 failure/2 requests=50% but may not warrant immediate page; use longer windows, minimum event counts, synthetic checks, and absolute safety rules. For critical payment double-charge, one event may page regardless rate.

### 2.3 Histogram percentile

Buckets are cumulative: ≤100 ms: 900, ≤250: 980, ≤500: 995, ≤1000:1000. p99 target rank=990, which lies in 250–500 bucket. Histogram quantile interpolates under distribution assumption, so approximate p99 between 250 and 500 ms; bucket design limits accuracy. Put tighter buckets around SLO threshold.

If the exact SLO is ≤300 ms, directly calculate good/total using a 300 ms bucket rather than derive approximate p99.

### 2.4 Cardinality arithmetic

Labels: 20 services × 40 routes × 5 statuses × 4 regions × 8 versions =128,000 possible series for one metric. Add one million user IDs and theoretical space explodes to 128 billion. Even sparse active subsets are costly. Put request/user IDs in sampled logs/traces with access controls, never metric labels.

Cardinality budgets should be per metric/service and monitored. Remove old version series through retention; avoid encoding timestamp or exception text.

### 2.5 Create an alert

Page: claim submission error ratio exceeds SLO burn threshold for fast and slow windows, with minimum 1,000 requests, across the user-facing service. Include service/region/version breakdown link, last deployments, trace exemplars, runbook, severity, and owner.

Simpler beginner rule: error ratio >5% for 5 minutes AND >1% for 30 minutes AND requests >1,000/5m. Dual windows reduce transient noise while catching sustained impact. The advanced lesson derives multi-window burn rates exactly.

### 2.6 Alert routing and inhibition

Route by service owner, environment, severity, and data/security category. Group all instance alerts for one service/region. If regional gateway outage fires, inhibit downstream “instance unreachable” pages while retaining diagnostic signals. Maintenance silences require owner, exact matchers, start/end, reason, and expiry; never blanket-silence production indefinitely.

Security/privacy alerts may route to incident/security teams with restricted content. Do not place sensitive payload in pager notifications.

### 2.7 Monitor a queue

Queue depth alone lacks rate context. Monitor arrival rate, completion rate, retry/dead-letter rate, age of oldest message, processing duration, consumer availability, and capacity. Backlog 100,000 can be fine at 100,000/s and disastrous at 100/s. Oldest age directly expresses timeliness.

If arrival 2,000/s and service 1,600/s, growth 400/s. After 15 minutes depth adds 360,000. Alert on age/SLO burn and sustained negative service margin; automate scaling only within downstream capacity.

### 2.8 Monitor certificates and backups

Certificate: days remaining, renewal job success, new secret/version created, gateway binding loaded, external TLS synthetic. Alert progression: ticket at 30 days, page when automated recovery failed and urgent remaining window, immediate page on handshake impact.

Backup: job success is insufficient. Monitor last successful backup/WAL archive age, storage/immutability, restore-test success and duration, recovered point, integrity/application validation. A green backup job with failed encryption key access is false safety.

### 2.9 Correlate a deployment

Emit deployment event with service, environment, old/new artifact digest, config/model/schema versions, actor/pipeline, rollout phase, and time. Overlay it on error/latency/resource charts and add version label to bounded metrics. If canary error rises only on new version, stop rollout; if both rise simultaneously, investigate shared dependency/load.

### 2.10 Initial triage from an alert

1. Confirm user impact and alert validity/time/scope.
2. Check SLI, traffic, regions/tenants/versions.
3. Check recent deployment/config/model/infrastructure events.
4. Compare dependency errors/latency and saturation.
5. Sample correlated traces/logs without sensitive overexposure.
6. Declare/escalate by impact; choose safe mitigation.
7. Verify recovery on user SLI, not only cause metric.

Do not spend 30 minutes perfecting root cause while users suffer if a safe rollback exists.

## 3. WORKED PROBLEMS

### Problem 1 — Counter or gauge (easy)

Classify total completed requests and current queue depth.

**Solution.** Counter and gauge. Derive request rate from counter; gauge can decrease.

**Trap:** resetting request counter every dashboard interval in application.

### Problem 2 — Error ratio (easy)

240 bad among 120,000 valid requests in 60 s.

**Solution.** .002=0.2%; total 2,000 rps, bad 4 rps.

**Trap:** reporting 240% or dividing by successes only.

### Problem 3 — Series count (easy)

10 routes, 5 statuses, 3 regions, 4 versions.

**Solution.** 600 possible series for one full Cartesian metric.

**Trap:** adding dimension counts instead of multiplying.

### Problem 4 — Average percentiles (medium)

Instance A p99 100 ms at 99% traffic; B p99 2 s at 1%. Is fleet p99 1.05 s?

**Solution.** No. Quantiles cannot be averaged; combine histogram distributions/request samples. Fleet p99 depends on both entire distributions and volumes.

**Trap:** weighted or unweighted p99 averaging.

### Problem 5 — Missing metric (medium)

Error metric disappears. Healthy?

**Solution.** Unknown. Could mean zero errors, no traffic, crashed exporter/service, scrape failure, or query mismatch. Pair total traffic/up heartbeat and telemetry-pipeline health; encode zero where appropriate.

**Trap:** absence interpreted as zero.

### Problem 6 — Alert persistence (medium)

Rule true for four minutes, false one, true five with `for:5m`.

**Solution.** First interval never fires and resets; second reaches firing after five continuous minutes, subject to evaluation interval semantics.

**Trap:** summing non-contiguous true minutes.

### Problem 7 — Queue risk (hard)

Depth 500,000, arrival 10,000/s, completion 9,500/s. What else and what trend?

**Solution.** Growth 500/s; depth adds 30,000/min. Need oldest age and required deadline, retry/DLQ, capacity, downstream saturation. If rates persist, queue never drains.

**Trap:** depth threshold without flow/time.

### Problem 8 — Sensitive cardinality (hard)

Engineer adds patient ID and exception message labels to errors.

**Solution.** Reject: unbounded cardinality and PHI/sensitive exposure. Use bounded error code/route/service metric; safe patient/request reference only in tightly controlled sampled logs/traces/audit if justified.

**Trap:** believing labels are harmless metadata.

### Problem 9 — Alert quality (hard)

CPU >80% pages nightly during expected batch; users unaffected and no action.

**Solution.** Remove page or route capacity ticket; alert on user SLO/saturation margin or batch deadline. If CPU predicts collapse, add persistence/headroom and actionable runbook. Track deletion as reliability improvement.

**Trap:** raising threshold to 90% without fixing semantics.

## 4. REAL-WORLD / APPLIED CONTEXT

### Prometheus

Prometheus scrapes labeled time series and evaluates PromQL rules. Counters, gauges, histograms, recording rules, Alertmanager grouping/routing/inhibition/silences, and exporters form a common Kubernetes stack. Pull does not eliminate push needs for short-lived jobs; Pushgateway has lifecycle semantics to understand.

### OpenTelemetry

OpenTelemetry defines vendor-neutral APIs/SDKs, semantic conventions, and collector pipelines for traces, metrics, and logs. Context propagation and resource attributes correlate services. Instrumentation can add CPU/network cost and sensitive attributes; configure sampling/processors/export queues and observe collectors.

### Azure Monitor

Azure Monitor combines platform metrics, activity/resource logs, Log Analytics, Application Insights, alerts, workbooks, and action groups. Azure ML/AKS/PostgreSQL each expose different signals. Central workspaces ease correlation but require RBAC, retention, ingestion cost, and data residency design.

## 5. COMPARISON TABLE

| Signal | Strength | Typical cost | Best question | Limitation |
|---|---|---:|---|---|
| Metrics | Aggregate/trend/alert | Low per point, cardinality-sensitive | Is fleet behavior changing? | Limited event context |
| Logs | Rich discrete details | High volume/index cost | What happened at this event? | Search/noise/privacy |
| Traces | Cross-service path/timing | Sampling/storage | Where did this request spend time? | Sample bias/context propagation |
| Profiles | Code/resource stacks | Sampling overhead | What code consumes CPU/memory? | Less business context |
| Synthetic | Controlled external journey | Scheduled traffic | Can a user path work now? | Limited scenarios/test identity |
| RUM | Actual user experience | Client/privacy complexity | What users experience? | Sampling/device/network noise |
| Static threshold | Simple/predictable | Low | Is hard safe bound crossed? | Seasonality/noise |
| Anomaly model | Adaptive patterns | Model/tuning cost | Is behavior unusual? | False positives/explainability |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Monitoring and observability are synonyms.** Monitoring checks known signals; observability supports novel inference.
2. **More telemetry is always better.** Cost/noise/privacy and unclear semantics harm.
3. **CPU is a user SLI.** It is usually a cause/saturation signal.
4. **Counter value is traffic.** Use a reset-aware rate.
5. **Missing equals zero.** It can mean telemetry/service failure.
6. **Percentiles can be averaged.** Aggregate distributions/histograms.
7. **Request ID belongs in metric label.** It creates near-one series per request.
8. **Every threshold should page.** Urgency/actionability are required.
9. **Dashboard replaces alert.** Nobody continuously watches it.
10. **One health endpoint covers public path.** DNS/TLS/identity/gateway may fail externally.
11. **Alert resolved means incident recovered.** Verify user journey and correctness/backlog.
12. **Backup success means recoverable.** Restore evidence is required.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Start with user journey; causes come after symptoms.
- Golden signals: latency, traffic, errors, saturation.
- RED for services; USE for resources.
- Counter increases/reset; gauge moves; histogram aggregates distributions.
- Rate counters; never average percentiles.
- Series = Cartesian label values; keep labels bounded/non-sensitive.
- Logs detail events; traces detail paths; profiles detail code cost.
- Alert requires scope + threshold + aggregation + window + traffic + persistence.
- Page urgent, actionable user risk; ticket nonurgent work.
- Treat missing data explicitly.
- Correlate deployment/config/model events.
- Verify mitigation on user SLI.

## 8. PRACTICE SET FOR SELF-TEST

1. Classify current connections, total errors, and request duration distribution.
2. Calculate error rate for 750 failures among 2.5 million.
3. Calculate series for 25 routes×6 statuses×4 regions×10 versions.
4. Explain why raw URL is a bad route label.
5. Design a low-traffic availability alert.
6. Define telemetry for a Kafka consumer.
7. Choose page, ticket, or dashboard for disk 60% full and forecast exhaustion in 14 days.
8. Explain head versus tail trace sampling.
9. List a service overview dashboard row order.
10. Define recovery verification after DB pool alert resolves.

## 9. CURATED RESOURCES

- Betsy Beyer et al., *Site Reliability Engineering*, Chapter 6 “Monitoring Distributed Systems” — golden signals, symptoms versus causes, alert simplicity and actionability.
- Betsy Beyer et al., *The Site Reliability Workbook*, Chapters 4–5 “Monitoring” and “Alerting on SLOs” — practical signal and alert design.
- Prometheus official documentation, “Metric types,” “Naming,” “Histograms and summaries,” “Alerting rules,” and Alertmanager configuration — authoritative Prometheus semantics.
- OpenTelemetry specification and semantic conventions, sections on traces, metrics, logs, resources, context, and sampling — vendor-neutral telemetry contracts.
- Charity Majors, Liz Fong-Jones, and George Miranda, *Observability Engineering*, Chapters 1–8 — high-cardinality event thinking, debugging unknowns, and socio-technical practice.
- Brendan Gregg, *Systems Performance*, 2nd ed., Chapters 2–4 — scientific method, observability tools, methodologies including USE.
- Microsoft Learn, “Azure Monitor overview,” “Application Insights,” “Azure Monitor alerts,” and “Log Analytics workspaces” — official Azure signal, query, alert-routing, and retention/cost mechanisms.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Production Operations:** supplies ownership, runbooks, changes, and on-call action.
2. **Reliability/Failure Basics:** defines outcomes, fault modes, overload, and recovery.
3. **Linux/Networking/Cloud:** supplies resource and protocol signals.

### After

1. **SLIs/SLOs/Error Budgets:** converts user signals into objectives and burn alerts.
2. **Metrics, Logs, and Traces:** deepens Prometheus/OpenTelemetry mechanics, sampling, and cost.
3. **Incident Response:** turns a page into roles, mitigation, communication, and evidence.
4. **Capacity/DR:** uses trends, forecasts, saturation, and recovery measurements.
5. **ML Lifecycle:** monitors drift, quality, features, and delayed outcomes in addition to service health.

---ANSWER KEY BELOW---

1. Gauge, counter, histogram.
2. `.0003`=0.03%.
3. 6,000.
4. IDs/query values create unbounded cardinality and may expose sensitive data; use templated route.
5. Combine longer ratio window/minimum absolute failures with external synthetic; one critical correctness/security event may have an absolute alert.
6. Arrival/completion rates, lag/depth, oldest age, processing latency, retries, DLQ, partitions/assignment, consumer health, downstream saturation.
7. Ticket/capacity workflow, unless forecast becomes urgent and automation cannot act.
8. Head decides at start cheaply but lacks outcome; tail buffers until outcome and can retain errors/slow traces at operational cost.
9. User SLI/SLO, traffic, errors, latency, saturation, dependencies, deployments/config, regional/version/tenant-safe breakdown and links.
10. User success/latency restored, queue/backlog draining, pool wait and DB cause stable, no lost/duplicate/corrupt operations, synthetic succeeds, continued observation.
