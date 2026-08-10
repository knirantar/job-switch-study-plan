# Metrics, Logs, and Distributed Traces

**Parent:** 06 — SRE and Observability  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the executable telemetry lab

## 1. FOUNDATIONS

**Monitoring** checks known conditions; **observability** is the ability to infer a system's internal state from its outputs, including questions not anticipated when code was written. The word is borrowed from control theory, but software observability is an engineering practice rather than a magical property obtained by buying a dashboard. Instrumentation, context, reliable collection, usable schemas and operational questions determine whether telemetry helps.

Three core telemetry signals serve different evidence needs. A **metric** is a numeric measurement aggregated into a time series: “requests failed at 1.2% over five minutes.” A **log** is a timestamped event with attributes and often a message: “deployment `d-8421` failed policy `region-denied`.” A **distributed trace** models the causal path of one operation across processes: “gateway called claims API, which waited on PostgreSQL.” Current OpenTelemetry also describes baggage and an emerging profiles signal; this lesson centers on metrics, logs and traces, then shows their correlation.

A **time series** is a metric name plus one exact set of attribute/label values and timestamped samples. Every label combination creates another series. A **counter** represents an accumulated quantity that normally increases until process reset. A **gauge** is a sampled value that can rise or fall. A **histogram** aggregates observations into buckets plus count and sum, preserving a distribution approximation. A **summary** commonly calculates client-side quantiles over a window; unlike histogram buckets, those quantiles generally cannot be meaningfully aggregated across instances.

A structured log is a record with stable fields such as timestamp, severity, service, event name, trace ID and deployment digest. A **trace** groups **spans** with one trace ID. Each span represents a timed operation and has a span ID, parent relationship, name/kind, start/end, status, attributes, events and links. A root span has no parent. **Context propagation** transmits trace context across HTTP, messaging and asynchronous boundaries. The W3C `traceparent` format provides interoperable trace/span identity and flags.

Historically, operators inspected files on one machine. Horizontal scaling and microservices made that inadequate: one user operation can cross a gateway, Java API, queue, Python worker, model endpoint and database. Centralized logs made search possible; time-series monitoring made fleet trends and alerting efficient; distributed tracing restored causal request structure. OpenTelemetry emerged to standardize APIs, SDKs, semantic conventions, context and export rather than bind application code to one backend.

Without disciplined telemetry, incidents fail in two ways. Under-instrumented systems leave teams guessing. Over-instrumented systems emit millions of unbounded series, sensitive payloads and terabytes of unqueryable logs, causing the observability platform itself to fail exactly during a traffic spike. The design objective is decision-quality evidence with bounded cost and privacy—not “collect everything forever.”

## 2. CORE MECHANICS

### 2.1 Begin with questions and user paths

Start from the SLO and operational decisions. Detection questions include: Which user journey is burning budget? Is impact regional or tenant-tier-specific? Diagnostic questions include: Which dependency or release changed? Is latency queueing, network, lock, GC or downstream work? Capacity questions include: What resource saturates before useful throughput stops scaling?

For an inference API, instrument logical request count/outcome/duration, admitted versus shed work, in-flight work, queue delay, model execution duration, dependency operations, deployment/model digest and resource saturation. Avoid raw tenant, patient, prompt or account identifiers in metric attributes. High-cardinality investigation belongs in protected sampled traces/logs with defined access and retention.

### 2.2 Metric instruments and semantics

Use a counter for completed operations, bytes, failures and retries: `claims_http_requests_total`. Convert a cumulative counter into a rate over a window; counter resets after restart are normal. Never decrement a counter or interpret its raw current value as a rate.

Use a gauge for current queue depth, active connections, temperature or configured replica count. A gauge sampled every 60 seconds can miss a 10-second saturation, so scrape frequency and aggregation must match the question. Summing gauges is valid for quantities such as concurrent requests across instances but wrong for percentages unless weighted appropriately.

Use a histogram for request latency, payload size or queue wait when distribution matters. Given observations `[0.04,0.08,0.12,0.30,1.20]` seconds and classic cumulative boundaries `[0.1,0.25,0.5,1.0]`, bucket counts are `[2,3,4,4]`, `_count=5`, `_sum=1.74`. The `le="0.25"` bucket includes all three observations at or below 250 ms, so the exact threshold ratio is 60%. The `+Inf` bucket should equal count.

Choose buckets around objectives and meaningful orders of magnitude. If the only bounds are 100 ms and 1 second, a 250 ms SLO cannot be calculated exactly. Too many buckets multiply time series; too few destroy resolution. Native/exponential histograms can provide better scalable resolution depending on current backend/client support, but compatibility and schema choice must be explicit.

### 2.3 Labels and cardinality

Useful metric labels are bounded dimensions used for aggregation: service, route template, method, status class, region, model tier. Never label with raw URL, request/trace/user/patient/order IDs, exception message or arbitrary model version. Normalize `/claims/84321` to `/claims/{claimId}`.

Cardinality is multiplicative in the worst case. Twelve services × 40 routes × 3 regions × 5 status classes = 7,200 potential series for one metric. Add two million users and the theoretical product becomes 14.4 billion. Actual combinations may be lower, but this calculation is a design upper bound. Each histogram bucket adds series per combination, so 12 buckets plus sum/count can turn 7,200 combinations into roughly 100,800 series.

Enforce an attribute allowlist, cardinality budget, overflow behavior and telemetry about dropped series. A label removed at collection cannot be reconstructed later; choose bounded dimensions based on actual questions. Prefer exemplars linking an aggregate metric sample to a representative trace rather than trace ID as a label.

### 2.4 Naming, units and aggregation

Names should describe one quantity with a base unit: seconds, bytes, ratio 0–1. Prometheus convention uses `_total` for counters and `_seconds` for duration. Do not mix milliseconds and seconds under one metric. Resource attributes describe the producing entity (service name/version, deployment environment, cloud region); event attributes describe the measurement.

Aggregate numerator and denominator with the same label set. `sum(rate(bad[5m])) / sum(rate(total[5m]))` differs from averaging each pod's ratio. If pod A has 9,990/10,000 good and B has 50/100, weighted success is 99.4059%; average of 99.9% and 50% is 74.95%, a different question. Preserve only dimensions required for the decision.

### 2.5 Temporality and resets

OpenTelemetry sums/histograms support cumulative and delta temporality. Cumulative points cover from one start time to successive timestamps; delta points cover adjacent intervals. Prometheus commonly models cumulative monotonic counters, letting queries handle resets. Delta moves state cost downstream and is common in StatsD-like systems. Collector/backend transformations must preserve start times and semantics or create artificial spikes/gaps.

Distinguish an instrumentation reset from a real negative event. For a cumulative counter changing `980 → 1,020 → 12` after restart, naïve difference says `−1,008`; reset-aware rate treats the new sequence correctly. Multiple writers claiming the same resource/attribute stream can make resets indistinguishable; OpenTelemetry's single-writer principle requires unique resource identity or non-overlapping writer lifetimes.

### 2.6 Structured logging

Emit a stable JSON-like schema rather than parsing prose. A production event might contain:

```json
{"timestamp":"2026-08-09T10:20:31.482Z","severity":"ERROR","service":"claims-api","event":"dependency_timeout","trace_id":"4bf92f3577b34da6a3ce929d0e0e4736","span_id":"b2","dependency":"postgres","timeout_ms":200,"deployment":"sha256:8ac..."}
```

Use UTC RFC 3339 timestamps with sufficient precision, severity with defined meanings, stable event name and machine-queryable fields. Preserve exception type/stack when useful but deduplicate or sample repetitive stacks. A log line should describe one event, not dump an entire object graph.

Do not log authorization headers, session tokens, passwords, private keys, raw request/response bodies, patient identifiers or payment account numbers. Redaction at source is safest; collector redaction is defense in depth. Regex redaction is incomplete because secrets appear in novel fields/encodings. Use allowlisted fields and irreversible pseudonyms only when a legitimate correlation need and reidentification risk are governed.

### 2.7 Log levels and volume

`ERROR` means an operation failed in a way needing investigation; it does not mean every handled client error. `WARN` indicates abnormal but handled risk. `INFO` captures meaningful lifecycle/business-operational events, not every loop iteration. `DEBUG/TRACE` is temporary detailed evidence controlled dynamically and safely. If 2,000 requests/s produce a 1 KiB info log each, raw volume is about `2,000×86,400×1 KiB ≈ 164.8 GiB/day` before indexes/replication. One line per request is not automatically affordable.

Estimate ingestion, indexed fields, retention, replication and query scan. Metrics are efficient for aggregates; logs should preserve discrete evidence; traces sample paths. Apply tiered retention, aggregation and deletion consistent with incident, audit and privacy needs.

### 2.8 Trace structure and timing

When gateway span `a1` starts a trace, claims API span `b2` uses `a1` as parent, and database `c3` plus Redis `d4` use `b2`, the tree shows causal nesting. A span's duration includes its children, so summing every span double-counts time. The lab computes `12+36+max(41,7)=89 ms` only as a simplified non-overlapping tree exercise; real critical-path analysis uses timestamps, concurrency, network gaps and parent self-time—not naïve duration sums.

Span **status** should follow semantic conventions; expected HTTP 404 may not be an error for a lookup contract. Add span events for meaningful moments such as retry or exception. Add **links** when one operation relates to multiple parents (batch processing, messaging fan-in) rather than inventing a single false parent.

### 2.9 Context propagation

On HTTP, extract validated inbound W3C Trace Context, create a server span and inject downstream. On messaging, producer context is carried in message headers; consumer spans may be children for immediate processing or linked for delayed/fan-out semantics. Async executors/reactive streams need context capture/restore; thread-local context alone is lost when execution changes thread.

Treat external trace headers as untrusted. Validate format, do not use trace ID for authorization, and prevent arbitrary **baggage** from copying PII/secrets through every service. Baggage is transmitted to downstream systems and is not encrypted merely because it is observability context. Allowlist small non-sensitive values if needed.

### 2.10 Sampling

Head sampling decides near trace start, such as 1%; it bounds cost but can miss rare errors discovered later. Tail sampling buffers trace spans and decides after outcome, retaining errors/slow traces but adding collector memory, latency and a requirement that spans for a trace reach the same decision point. Parent-based sampling preserves trace consistency across services.

Always sampling errors sounds attractive, but an outage can make 100% of massive traffic erroneous and overload telemetry. Apply bounded adaptive/rate-limited policies, retain representative errors per route/region and record sampling probabilities. Sampling traces must not sample SLI counters: metrics should count all events (within documented telemetry loss). Logs may use deterministic/rate sampling but audit/security events have distinct retention requirements.

If 10,000 requests/s average 8 spans and 600 encoded bytes/span, unsampled trace input is `10,000×8×600 = 48 MB/s` decimal, about 4.147 TB/day before replication/index. A 1% head sample reduces expected payload to ~480 KB/s/~41.5 GB/day, but burst, compression and backend overhead still matter.

### 2.11 OpenTelemetry architecture

Instrumentation uses OTel APIs/SDK or auto-instrumentation. A **resource** identifies the entity; instrumentation scope identifies the library; semantic conventions standardize attribute/name meanings. SDK processors batch/export to an OpenTelemetry Collector. Collector receivers accept OTLP/other inputs; processors batch, filter, transform, redact, sample and enforce memory limits; exporters send to one or more backends.

OTLP 1.11 is stable for trace, metric and log signals. It supports gRPC (default port 4317) and HTTP; its hop-by-hop acknowledgments do not establish end-to-end durable delivery across a multi-hop pipeline. Export retry uses bounded backoff/jitter for retryable failures, but telemetry queues need memory/disk limits. Application correctness must never block indefinitely on observability export.

Use agent collectors for host-local buffering/context and gateway collectors for central policy/tail sampling when needed. A gateway is a dependency: deploy redundant capacity, control tenant access, restrict egress, monitor refused/dropped data and test backend outage. Do not let a telemetry retry storm compete with the production data path.

### 2.12 Correlating signals

Start at an SLO burn metric, filter bounded region/route/version, follow an exemplar to a trace, locate the slow/error span, then query logs by trace/span ID and deployment. Conversely, a deployment log links to release digest; dashboards compare before/after; a trace identifies a database operation; database metrics confirm fleet saturation.

Correlation depends on consistent service/resource naming and synchronized clocks. NTP error can make child spans appear before parents, though trace parentage still provides structure. Store trace/span IDs in logs, not as metric labels. Include release/model/config identity as bounded resource attribute or carefully controlled label; unbounded commit hashes across long retention can still grow cardinality.

### 2.13 RED, USE and golden signals

For request-driven services, RED means rate, errors and duration. For resources, USE means utilization, saturation and errors. Google's four golden signals are latency, traffic, errors and saturation. These are prompts, not schemas. Queue depth without arrival/service rate and age can mislead; CPU utilization without throttling/run queue can miss saturation; high traffic is not itself bad.

Instrument thread/connection pools, queue oldest age, JVM GC pause/allocation/heap, database pool wait, Kafka lag age and GPU utilization/memory/queue. Pair cause metrics with user symptoms. Alert on actionable SLO threat or impending hard capacity limit, not every deviation.

### 2.14 Dashboards and alerts

A service landing dashboard should show SLO success/burn/budget, traffic, latency distribution, errors by owned reason, saturation, deployments and dependency health. It answers “is there user impact?” before “which pod?” Use consistent time zones, units, links and annotations. Avoid dashboards with 80 unlabeled charts and no decision path.

An alert needs owner, urgency, condition, impact, links and first actions. Page only if a human must act now; ticket if action can wait; retain data for later otherwise. Test alerts with known synthetic failure and verify notification routing. Absence alerts (`up==0`, telemetry silence) require traffic/deployment awareness so intentionally scaled-to-zero jobs do not page.

### 2.15 Failure, security and privacy boundaries

Telemetry is lossy unless explicitly engineered otherwise. SDK queues fill, collectors restart, networks partition, backends throttle and schemas change. Monitor accepted/refused/dropped spans/logs/points, queue occupancy, export latency and query freshness using an independent path where feasible. Document whether audit records need a different durable pipeline from diagnostic logs.

Telemetry endpoints expose architecture and may accept expensive input. Authenticate/encrypt OTLP, isolate tenants, constrain attributes/message size, patch collectors, and prevent query users from reading regulated data. Logs/traces can become a secondary data breach. Encrypt, restrict, audit access, minimize content and honor retention/deletion/legal-hold requirements.

## 3. WORKED PROBLEMS

### Problem 1 — Cardinality budget

**Statement.** One histogram uses 12 services, 40 route templates, 3 regions, 5 status classes, 10 finite buckets plus `+Inf`, `_sum` and `_count`. Estimate worst-case series.

**Solution.** Label combinations are `12×40×3×5=7,200`. Classic histogram exports 11 bucket series plus sum and count = 13 series per combination, or `7,200×13=93,600`. Confirm backend conventions because `+Inf` inclusion/schema differs. Adding user ID is unacceptable.

**Mistake caught:** counting a histogram as one time series.

### Problem 2 — Weighted availability

**Statement.** Pod A has 9,990 good/10,000; pod B has 50/100. Compute fleet success.

**Solution.** `(9,990+50)/(10,000+100)=10,040/10,100≈99.4059%`. Averaging pod percentages yields 74.95%, which weights a 100-request pod equal to a 10,000-request pod. Aggregate counts first.

**Mistake caught:** average-of-averages.

### Problem 3 — Histogram threshold

**Statement.** For `[.04,.08,.12,.30,1.20]` seconds and bounds `[.1,.25,.5,1]`, produce cumulative buckets and fraction ≤.25.

**Solution.** Counts are `[2,3,4,4]`; count 5; sum 1.74 seconds; implicit `+Inf=5`. Three of five are ≤.25, so 60%. It is not 3/4; finite last bucket omits 1.20.

**Mistake caught:** treating buckets as noncumulative or last finite bucket as total.

### Problem 4 — Counter reset

**Statement.** A request counter samples `980, 1020, 12, 42` over equal intervals with restart between 1020 and 12. What is naïve versus reset-aware increment?

**Solution.** Naïve final−first is `42−980=−938`, impossible for events. Assuming reset to zero and no unobserved pre-reset increment, increments are `40 + 12 + 30 = 82`. Production `rate` extrapolation depends on timestamps/scrapes, but it detects resets rather than using raw subtraction.

**Mistake caught:** reading monotonic counters as gauges.

### Problem 5 — Trace critical path

**Statement.** Root gateway 12 ms → API 36 ms → parallel DB 41 ms and Redis 7 ms. Use the lab's simplified non-overlap model.

**Solution.** Longest branch is DB: `12+36+41=89 ms`, not sum 96 ms. In real trace timestamps, parent durations often include children, so even 89 may double count; determine wall-clock path and parent self-time.

**Mistake caught:** summing all span durations.

### Problem 6 — Sampling capacity

**Statement.** At 10,000 requests/s, 8 spans/request, 600 bytes/span, compute raw and 1% trace payload per day.

**Solution.** Raw is 48,000,000 bytes/s = 48 MB/s and `4.1472 TB/day` decimal. One percent expected is 0.48 MB/s and 41.472 GB/day. Add protocol, index, replication and burst headroom before budgeting.

**Mistake caught:** treating sampling percentage as total backend cost without overhead.

### Problem 7 — Async propagation

**Statement.** Producer publishes one message processed hours later and retried twice. Should consumer always be a direct child span?

**Solution.** Preserve producer context in message headers. Depending on semantic conventions/lifecycle, consumer processing may use a link to producer context rather than imply continuous synchronous parent duration; retries get distinct attempt spans linked/correlated to the logical message. Never put trace context in message body as business authorization.

**Mistake caught:** forcing synchronous tree semantics onto asynchronous causality.

### Problem 8 — Sensitive telemetry

**Statement.** A developer labels metrics by patient ID and logs authorization header to debug 403s. Redesign.

**Solution.** Remove patient ID from metrics; use bounded tenant tier/region/route. Never log the credential. Log principal type/object pseudonymous reference where approved, token issuer/audience/expiry metadata, requested action/scope, decision/correlation ID. Restrict traces/logs and retain minimally. Rotate credentials if exposed.

**Mistake caught:** assuming internal observability storage is a safe data sink.

### Problem 9 — Collector outage

**Statement.** Collector backend is down 30 minutes. Application SDK retries without bound and latency rises. Fix the design.

**Solution.** Telemetry export is off the request critical path with bounded batch queue, timeout, backoff/jitter and explicit drop behavior. Collector has memory limiter, persistent queue only if required/capacity-tested, redundant gateways and export telemetry. Shed diagnostic traces/logs before SLI/audit classes according to policy. Application correctness must continue.

**Mistake caught:** making observability more critical than the observed service accidentally.

## 4. REAL-WORLD / APPLIED CONTEXT

OpenTelemetry defines independent trace, metric and log signals sharing context propagation. OTLP 1.11 specifies encoding/transport between sources, collectors and backends, while explicitly leaving end-to-end delivery outside hop acknowledgment. This is why “export returned success” is not proof a multi-hop backend durably indexed data.

Prometheus's official naming guidance warns that every unique label set is a new series and explicitly rejects unbounded labels such as user IDs/email addresses. Its histogram model lets a 250 ms SLO query sum cumulative `le="0.25"` bucket rates across instances before division.

The included lab uses four spans from a fixed trace ID, five latency observations and explicit label cardinalities. Five tests pass: unsafe `user_id` is rejected; 7,200 combinations are calculated; cumulative buckets equal `[2,3,4,4]`; the simplified path is 89 ms and orphan is detected; patient/token fields redact. These standard-library tests validate teaching invariants, not full OTLP/Prometheus conformance or performance.

## 5. COMPARISON TABLE

| Signal | Best question | Typical cost shape | Main failure |
|---|---|---|---|
| Metrics | “How many/how often; is trend/SLO bad?” | bounded series × samples | cardinality explosion; lost event detail |
| Logs | “What discrete event/detail occurred?” | event bytes + indexing/retention | volume, schema drift, secrets/PII |
| Traces | “Where did this request spend/fail?” | spans × sampled requests | sampling gaps, broken propagation |
| Profiles | “Which code consumes CPU/memory?” | sampled stacks over time | overhead/symbol/privacy; OTel profile status is evolving |

| Metric type | Aggregation | Use | Avoid |
|---|---|---|---|
| Counter | rate/increase, sum | completed events/bytes/errors | current queue or decrement |
| Gauge | last/min/max/sum when meaningful | current temperature/depth/in-flight | event totals and unweighted percentage sums |
| Histogram | merge bucket counts/sum/count | latency/size distribution, SLO threshold | arbitrary buckets/cardinality |
| Summary | client window quantiles/sum/count | local quantile when aggregation unnecessary | averaging quantiles across instances |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Observability equals tool installation.** Without questions/schemas/context it is expensive noise.
2. **Metrics, logs and traces are interchangeable.** Each retains different aggregation/detail/causality.
3. **User or trace ID as metric label.** It creates unbounded cardinality; use exemplars/protected detail.
4. **Raw URL label.** Normalize route templates.
5. **Histogram is one series.** Every bucket plus sum/count multiplies label combinations.
6. **Buckets are independent.** Classic Prometheus buckets are cumulative.
7. **Average instance percentiles.** Quantiles are not generally aggregatable; merge histograms.
8. **Average ratios.** Sum compatible counts first.
9. **Raw counter difference.** Restarts create apparent negatives; use reset-aware rate/increase.
10. **Gauge rate always meaningful.** A gauge's derivative may be useful only with domain semantics.
11. **Milliseconds stored as seconds.** Units silently corrupt thresholds. Use base units/names.
12. **Log every request body.** It creates privacy, cost and incident risk.
13. **Regex redaction is complete.** Prefer field allowlists/source omission; regex is defense in depth.
14. **Debug logs harmless in production.** They can amplify volume and reveal internals/secrets.
15. **Sum span durations.** Parent/parallel time double counts. Use timestamps/critical path/self-time.
16. **Trace header is trusted identity.** It is correlation input, never authorization.
17. **Put PII in baggage.** Baggage propagates broadly and is not automatically encrypted/sanitized.
18. **Sample errors at unlimited 100%.** Incident traffic can overwhelm collection. Bound/adapt.
19. **Sample SLI metrics like traces.** SLO counts need complete/quantified measurement.
20. **Collector ACK proves durable end-to-end storage.** OTLP acknowledgment is hop-scoped.
21. **Infinite exporter retry preserves data.** It exhausts resources. Bound queues/retries and expose drops.
22. **Alert on every cause metric.** Page on actionable user impact or impending hard failure.
23. **No telemetry means healthy.** Detect absence, pipeline loss and query staleness.
24. **One dashboard serves every task.** Landing, diagnosis, capacity and audit questions differ.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Metric: aggregate trend/SLO. Log: discrete evidence. Trace: causal path. Profile: code resource use.
- Counter increases/reset → `rate`; gauge varies; histogram = cumulative buckets + count + sum.
- Series = metric name + unique label set. Cardinalities multiply; histogram series multiply again.
- Base units: seconds, bytes, ratios 0–1. Normalize routes and status classes.
- Structured log: UTC timestamp, severity, service, event, trace/span, bounded attributes; no secrets/PHI.
- Trace: trace ID, span ID, parent/link, timing, status, attributes/events.
- Propagate W3C Trace Context; validate input; never authorize with trace/baggage.
- Head sample early/cheap; tail sample outcome-aware/costly. Metrics remain complete.
- OTel: API/SDK → Collector receiver/processors/exporter → backend; OTLP is not end-to-end durability.
- Investigation: SLO metric → bounded segment → exemplar/trace → span → correlated logs → cause metrics/profile.
- Observe observability: dropped/refused points, queue, export latency, freshness and cost.

## 8. PRACTICE SET FOR SELF-TEST

1. Compute classic-histogram series for 20 services, 60 routes, 4 regions, 5 status classes and 14 total bucket/sum/count series per combination.
2. Given latency observations `[.03,.05,.11,.21,.24,.26,.8,1.4]`, build cumulative counts for `.1,.25,.5,1,+Inf` and SLO fraction ≤.25.
3. Two pods report 500/1,000 and 99,000/100,000 good. Calculate weighted success and unweighted mean of ratios.
4. Design bounded RED/USE metrics for an Azure ML inference gateway; justify every label and cardinality ceiling.
5. Rewrite a free-text log containing patient ID, bearer token, raw URL and stack trace into a safe structured event.
6. Draw spans/links for API → Kafka → three consumers, one retry and one batch combining ten messages.
7. Size raw and 2% sampled trace payload for 25,000 requests/s, 12 spans/request and 800 bytes/span per day.
8. Design a head/tail sampling policy that retains rare payment failures without collapsing during a 100% error storm.
9. Give a layer-by-layer investigation from 14.4× SLO burn to a database connection-pool regression after release.
10. Specify collector failure behavior, telemetry-loss SLO and separate audit-log durability for a healthcare platform.

## 9. CURATED RESOURCES

1. OpenTelemetry Specification 1.59, *Overview*, *Trace*, *Metrics*, *Logs*, *Context*. Exact signal APIs/data semantics and maturity.
2. OpenTelemetry Protocol Specification 1.11, [OTLP](https://opentelemetry.io/docs/specs/otlp/). Transport, responses, retry, size and hop-delivery boundary.
3. OpenTelemetry Semantic Conventions 1.43. Exact standard HTTP, database, messaging and resource names/status rules.
4. W3C Recommendation, *Trace Context Level 2*. Interoperable `traceparent`/`tracestate`, validation and privacy/security behavior.
5. Prometheus Documentation, [Metric and label naming](https://prometheus.io/docs/practices/naming/). Base units, counter names and cardinality guidance.
6. Prometheus Documentation, *Histograms and summaries* plus *Query functions*. Bucket aggregation, quantile error and reset-aware rate semantics.
7. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 6, “Monitoring Distributed Systems.” Four golden signals, symptoms versus causes and actionable monitoring.
8. Cindy Sridharan, *Distributed Systems Observability*, Chapters 2–5. Signal trade-offs, context and debugging reasoning beyond vendor configuration.
9. Ben Sigelman et al., “Dapper, a Large-Scale Distributed Systems Tracing Infrastructure.” Canonical trace/span, sampling and production tracing design.
10. Peter Bourgon and Charity Majors, “Metrics, Tracing, and Logging” (the observability trinity framing). Historical reasoning about complementary signals; contrast with current profiles/events.

## 10. RELATED TOPICS BRIDGE

### Before

1. **SLIs, SLOs and Error Budgets:** determines which user measurements and alerts matter.
2. **Distributed Failure Semantics:** retries/timeouts/idempotency define logical requests and trace causality.
3. **Cloud Identity and Networking:** network/identity events and failure layers need safe telemetry.
4. **JVM Performance:** GC, thread and allocation metrics/profiles connect runtime cause to latency.

### After

1. **Incident Response:** uses correlated signals, alert metadata and timelines under pressure.
2. **Capacity and Disaster Recovery:** uses utilization/saturation/traffic trends and recovery evidence.
3. **MLOps Monitoring:** adds data/model quality, drift and lineage to operational signals.
4. **Regulated System Design:** governs telemetry privacy, access, retention and audit separation.

---ANSWER KEY BELOW---

1. Combinations `20×60×4×5=24,000`; times 14 = 336,000 series for one histogram family at worst. Confirm actual populated combinations and backend/native histogram representation.
2. Cumulative finite counts: ≤.1 =2; ≤.25=5; ≤.5=6; ≤1=7; +Inf=8. SLO fraction ≤.25 is `5/8=62.5%`; count=8; sum=3.10 seconds.
3. Weighted `(500+99,000)/(1,000+100,000)=99,500/101,000≈98.5149%`. Unweighted mean `(50%+99%)/2=74.5%`, which answers “average pod ratio,” not user-event availability.
4. Counters for logical requests by route template/method/outcome/status class/region/model tier; duration and queue-wait histograms with SLO-aligned bounds; gauges for in-flight, queue depth/oldest age, GPU/CPU/memory and pool use; counters for shed/retry/model-load failure. Calculate ceiling from fixed enum inventories, reject model ID/tenant/request/prompt, and link exemplars to traces.
5. Example fields: timestamp, severity, `service=claims-api`, `event=dependency_failure`, `route=/patients/{patientId}`, error type, safe reason, trace/span, deployment digest. Omit/token-redact authorization and patient identity; keep stack in protected deduplicated field only if it contains no sensitive locals/messages. Use correlation ID with controlled lookup rather than raw identity.
6. Producer send span carries context. Each consumer processing attempt gets a consumer span linked/parented per messaging semantic convention; retry is a new attempt span with same message identity and link, not reused span. Batch span links all ten producer contexts because one parent would discard causality. Propagate headers separately from body and bound baggage.
7. Raw: `25,000×12×800=240,000,000 bytes/s` = 240 MB/s; per day 20.736 TB decimal. At 2% expected payload 4.8 MB/s or 414.72 GB/day, before protocol/index/replication/compression and bursts.
8. Parent-based bounded head sample for baseline/known high-value routes; tail rules retain a rate-limited representative set of errors/slow traces per route/region plus tiny baseline. Cap per-tenant/rule rates, memory and decision wait; degrade deterministically under overload and expose dropped counts. Keep unsampled SLI metrics and separately durable audit events.
9. Page from multi-window burn; confirm edge numerator/denominator/freshness; segment route/region/deployment; annotation shows release; exemplar opens slow trace; API spans show pool-wait/DB child delay; correlated timeout logs and connection-pool metrics show waiters/max reached while DB latency/CPU are normal; compare config digest before/after, rollback/canary and validate burn recovery.
10. SDK batch queues/timeouts are bounded and off request path; redundant collectors use memory limiter/batching/backoff and optionally capacity-tested persistent queue; shed lower-value traces/debug logs first; monitor accepted/refused/dropped/export freshness against a telemetry-loss objective. Security/audit events use a separate authenticated append/durable pipeline with defined RPO, access/immutability/retention and PHI minimization, not best-effort diagnostic OTLP alone.
