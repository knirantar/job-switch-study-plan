# Service-Level Indicators, Objectives, and Error Budgets

**Parent:** 06 — SRE and Observability  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the executable SLO lab

## 1. FOUNDATIONS

Reliability is not “the server is up.” A user cares whether a meaningful operation—paying an invoice, retrieving a clinical record, receiving a model prediction—works correctly and quickly enough. A server can return HTTP 200 while serving stale, unauthorized or semantically wrong data. Conversely, a redundant internal component may report unhealthy without affecting a user. Site Reliability Engineering therefore begins with an observable contract at the service boundary.

A **service-level indicator (SLI)** is a carefully specified quantitative measure of service behavior. A **service-level objective (SLO)** is a target for that SLI over a defined window. A **service-level agreement (SLA)** is a business/legal agreement that attaches consequences to service targets. If missing the number causes an internal reliability review, it is probably an SLO; if it causes a service credit or contractual remedy, it is an SLA.

The distinction arose from the need to balance product velocity with reliability. “Never fail” is impossible in distributed systems and makes rational investment impossible. Too little reliability loses users; substantially exceeding what users need can waste engineering capacity and teach dependents to assume an undocumented level. Google SRE formalized an **error budget**: the tolerated fraction of non-good events, `1 − SLO`. Product and reliability teams can spend that budget on releases and experiments while protecting user expectations.

An event-based availability SLI is:

```text
good events / valid events
```

For a 99.9% objective, the bad-event fraction is 0.1%, or `0.001`. If 50,000,000 valid requests occur in a 30-day window, the nominal budget is `50,000,000 × 0.001 = 50,000` bad requests. This is not permission to harm any 50,000 users: safety, privacy, financial correctness and data loss may be zero-tolerance invariants outside an availability budget.

An **SLI specification** defines what counts as valid, good, bad, excluded and missing; measurement point; labels/segments; window; and data-quality policy. An **SLI implementation** is a query or instrumentation realizing that specification. A **rolling window** always considers the most recent N days; a **calendar window** resets on a boundary such as a month. Rolling windows avoid reset cliffs but are harder to explain financially. A **request-based** SLO weights every valid request; a **time-based** SLO marks intervals good/bad. They answer different questions under uneven traffic.

**Burn rate** measures how quickly budget is being consumed relative to the sustainable rate:

```text
burn rate = observed bad-event ratio / allowed bad-event ratio
```

At a 99.9% objective, a 0.2% observed error ratio burns at `0.002 / 0.001 = 2×`. Sustained for the full window, it consumes twice the available budget. A 20× incident consumes a 30-day budget in `30 / 20 = 1.5 days`. Burn rate makes alert thresholds reusable across SLO targets.

Without precise SLIs, teams alert on CPU, individual pods or raw exceptions. Those are useful diagnostic signals but poor definitions of user impact. They generate noisy pages and allow complete user-visible failures when infrastructure metrics appear normal. The goal is not fewer metrics; it is a clear separation between **symptom** signals that justify interrupting a human and **cause** signals used to diagnose them.

## 2. CORE MECHANICS

### 2.1 Start with a user journey

Work backward from a critical journey. For a payment authorization: a valid request is an authenticated, syntactically acceptable authorization attempt that reaches the owned service boundary. A good event might return the correct terminal or explicitly accepted asynchronous result within 800 ms. Client cancellations before admission, approved load tests and demonstrably invalid requests may be excluded; internal retries must not be counted as new user attempts.

For a model deployment platform, user journeys differ: submission accepted durably within 400 ms; deployment reaches a terminal state within 20 minutes; active model serves predictions within 250 ms; cancellation reaches an explicit outcome. One “API uptime” percentage cannot represent all of these.

### 2.2 Choose measurement point

Measure as close to the user as feasible: edge/load balancer for request availability, client telemetry for end-to-end experience, durable workflow timestamps for asynchronous completion. Server-side application metrics miss DNS/TLS/edge failures and requests that never arrive. Client metrics can have sampling, ad blockers, clock skew and privacy constraints. Use an authoritative boundary plus complementary synthetic/client checks and document blind spots.

For a multi-region API, per-region success can hide global routing failure if no traffic reaches a broken region. Edge logs reveal attempted requests, while synthetic probes reveal “zero observed traffic because nobody can connect.” Monitoring absence must not be interpreted as 100% success.

### 2.3 Define valid, good and bad exactly

Classify by user outcome, not status-family folklore. A server `500`, timeout or malformed response is normally bad. A user-caused `400` might be excluded, but authentication `401` could indicate a service regression and needs contextual ownership. Rate-limited `429` can be good if the public contract explicitly promises bounded admission and a correct retry response, or bad if expected in-contract traffic is rejected. A dependency `503` remains bad to your user even when the dependency caused it.

Correctness may require domain validation. A `200` prediction with the wrong tenant's model is catastrophic, not good. A duplicate payment cannot be averaged away. Define invariants and independent audit/detection because ordinary request counters may not know semantic correctness.

### 2.4 Availability versus latency SLIs

Availability is usually a good-event ratio. Latency should also use threshold ratios, such as “99% of valid interactive predictions complete under 250 ms,” rather than an average. Ten requests taking `[40,40,40,40,40,40,40,40,40,2040]` ms have a 240 ms mean, which suggests success under a 250 ms average while one user waits 2.04 seconds. Percentile/threshold distribution exposes the tail.

A threshold SLI directly yields good/bad counts: requests ≤250 ms are good. Multiple thresholds can represent experience, e.g. 99% <250 ms and 99.9% <1 s. Avoid percentiles averaged across instances or time. To aggregate classic Prometheus histograms, sum bucket rates by `le` before `histogram_quantile`; better still, compute the exact ratio at the threshold using the appropriate cumulative bucket divided by count.

### 2.5 Asynchronous and freshness SLIs

Batch/ML pipelines need completion and freshness, not HTTP response alone. Define a valid event as an expected partition/job/model request; good means the correct output is published by deadline. Freshness can be `now − event-time of newest completely processed input`, not merely last process heartbeat. A pipeline rapidly processing yesterday's backlog is alive but stale.

For 1,440 expected five-minute tenant partitions/day, a 99% daily completeness SLO allows 14.4 nominal misses, but events are integral. Decide compliance arithmetic and reporting—do not silently round up. Segment by tenant/data class so a large healthy tenant cannot mask a small regulated tenant's total outage.

### 2.6 Denominator integrity

The denominator is a security/reliability asset. If overload drops requests before instrumentation, measured success can improve while users suffer. Count at an edge before shedding, propagate a logical request ID, and distinguish logical requests from retries/attempts. If a client makes three attempts and eventually succeeds, an attempt SLI is 33.3%, while a user-outcome SLI may be 100% with increased latency; both are useful but must not be confused.

Missing telemetry needs an explicit policy. Treating missing as good rewards monitoring failure; treating all missing as bad can page on observability outage. Use independent telemetry health, bound estimated uncertainty and fail decisions safely. Never exclude incidents after the fact merely because the monitoring path failed.

### 2.7 Windows and budget arithmetic

For a request SLO, budget depends on traffic. At 99.95% and 80,000,000 requests, allowed ratio is `0.0005`, budget 40,000 bad requests. A time-based 99.95% 30-day objective allows `43,200 seconds × 0.0005 = 21.6 minutes`. These are not equivalent: a five-minute outage at peak can consume many more request failures than five minutes at night.

Use integer counts as authoritative and percentages for display. Floating-point rounding can label a boundary incorrectly. State inclusive/exclusive comparisons: does exactly 99.9000% meet a `≥99.9%` objective? Usually yes. Late-arriving logs may change a report; define completeness delay and correction policy.

### 2.8 Burn rate and time to exhaustion

If allowed bad ratio is `e = 1 − objective` and observed bad ratio is `b`, burn `r=b/e`. At 99.9%, 2% errors yield `0.02/0.001=20×`. Approximate full-window budget exhaustion under a constant rate is `window/r`: 36 hours for a 30-day window at 20×. If 40% is already spent, remaining exhaustion is `0.60×30/20 = 0.9 day = 21.6 hours`.

Burn rate is dimensionless but sampling noise matters. Two errors among 100 low-traffic requests is the same point estimate as 20,000 among one million; evidence and user impact differ. Do not page solely from a volatile ratio without enough events unless each event is individually critical.

### 2.9 Multi-window, multi-burn alerts

A short window detects quickly but is noisy; a long window confirms persistence but reacts slowly. Pair them with AND. The Google SRE Workbook derives useful starting points for a 30-day objective: page when both 5-minute and 1-hour windows exceed 14.4× (approximately 2% of monthly budget in one hour), or both 30-minute and 6-hour windows exceed 6× (5% in six hours); ticket around 1× over three days (10% in three days). Exact recommended pairs/configuration must be adapted to traffic, page load and implementation.

The lab simplifies the inputs into two paired paths and intentionally proves a hot short window plus calm long window does not page. Production PromQL should use recording rules, sufficient evaluation duration and label aggregation matching the SLI. Alert on user-impact budget threat; dashboards then pivot to causes.

### 2.10 Low-traffic services

At 10 requests/hour and 99.9% over 30 days, total is 7,200 and budget only 7.2 failed requests. One failure in an hour gives 10% hourly error and 100× burn, even if operational response cannot prevent that event. Options include synthetic transactions, grouping closely related journeys sharing a failure domain, increasing the window, selecting a product-appropriate lower objective, or changing the service so retries/fallback reduce individual harm. If each event is a high-value wire transfer, investigate individually rather than hiding it through aggregation.

### 2.11 Segmentation and aggregation

Always inspect the aggregate and critical segments: region, endpoint/journey, tenant tier, status/reason and client version. Overall 99.99% can hide one tenant at 0% if it contributes little traffic. But putting tenant ID into every metric creates unbounded cardinality and privacy exposure. Use bounded tiers/regions in metrics and protected logs/traces or scheduled SLO computations for tenant-level investigation.

Do not let retries convert dependency attempts into user events. Do not average regional success percentages: region A with 1,000,000 events at 99.9% and B with 100 at 90% has `(999,000+90)/(1,000,100) ≈ 99.899%`, not `(99.9+90)/2=94.95%`. Whether the small region deserves an independent objective is a product decision.

### 2.12 Error-budget policy

Arithmetic does nothing without agreed action. A policy names owners, SLO window/data source, budget thresholds, exceptions and review cadence. Example: above 50% consumed halfway through window, require reliability review for risky launches; exhausted budget pauses nonessential risky changes while allowing security fixes and changes demonstrably reducing the failure cause; exit requires identified cause, restored burn trend and owner approval. Do not mechanically freeze all changes, since a reliability fix is itself a change.

Define whether provider-caused failures count. From a user perspective they usually do; otherwise architecture decisions outsource the denominator. Track dependency contribution separately for remediation and vendor management. Planned maintenance also affects users and should normally count unless the contract explicitly excludes it and users truly experience the exclusion as acceptable.

### 2.13 SLO lifecycle and governance

Draft from user needs, instrument, validate against sampled raw events, run without enforcement, then negotiate target and policy. Review after product/journey changes and at least periodically. Version the specification/query. Backtest proposed changes so a denominator redefinition cannot magically replenish budget. Maintain internal objectives tighter than external SLAs to preserve response margin.

SLOs are not performance targets for individual engineers and should not be gamed. A target based solely on current performance legitimizes accidental behavior; a target chosen as 99.99 because it “looks enterprise” can cost disproportionately more. Estimate user/business harm and engineering cost, choose the loosest objective that meets the real need, and tighten with evidence.

### 2.14 Prometheus query mechanics

For monotonic counters `http_requests_total{outcome="..."}`, compute rates before division and aggregate consistent labels:

```promql
sum(rate(http_requests_total{service="claims", outcome="bad"}[5m]))
/
sum(rate(http_requests_total{service="claims", outcome=~"good|bad"}[5m]))
```

Counters reset; `rate` handles resets within its model. Do not use raw counter differences without reset handling. Ensure numerator is a subset of denominator, handle zero traffic explicitly, and avoid mixing scrape intervals/windows. For latency ≤0.25 seconds using a classic histogram:

```promql
sum(rate(http_request_duration_seconds_bucket{service="claims",le="0.25"}[5m]))
/
sum(rate(http_request_duration_seconds_count{service="claims"}[5m]))
```

This assumes the bucket boundary exists and observations/labels match. A percentile estimate is different from the fraction under the exact objective threshold.

### 2.15 Safety, privacy, and cost boundaries

Reliability measurement must not leak PHI, account IDs, request bodies or tokens into metric labels. High-cardinality labels also raise memory/query/storage cost and can take down monitoring during an incident. Use bounded dimensions, exemplars/correlation IDs with protected traces and controlled log access. Retain raw SLI evidence long enough for audit/correction, but minimize according to policy.

Availability does not overrule correctness. A fallback that returns another patient's record makes latency/availability look good while violating a safety invariant. Define explicit degraded results as good only if users accept their semantics. Cost controls and load shedding can be reliable behavior when the contract says which traffic is admitted and rejected.

## 3. WORKED PROBLEMS

### Problem 1 — Request error budget

**Statement.** A 99.9% SLO observes 50,000,000 valid requests in 30 days. It records 18,500 bad events. Compute budget, consumed fraction and remaining.

**Solution.** Allowed ratio is `0.001`; budget is 50,000. Consumption is `18,500/50,000=0.37`, or 37%. Remaining is 31,500 bad events, 63%. Actual success is `49,981,500/50,000,000=99.963%`.

**Mistake caught:** subtracting 18,500 from a time-based downtime allowance.

### Problem 2 — Time versus request objective

**Statement.** A 99.95% 30-day time SLO has a 10-minute outage. How much budget is consumed?

**Solution.** Thirty days contain 43,200 minutes. Budget is `43,200×0.0005=21.6` minutes. Ten minutes consumes `10/21.6≈46.30%`. Request-based consumption cannot be known without request counts during the outage.

**Mistake caught:** assuming all minutes carry equal request harm under a request SLO.

### Problem 3 — Burn and exhaustion

**Statement.** A 99.9% SLO observes 0.7% bad events for six hours. Compute burn and the 30-day budget fraction consumed if sustained exactly six hours.

**Solution.** Burn is `0.007/0.001=7×`. Six hours is `6/720` of 30 days, so consumed budget is `7×6/720≈0.05833`, or 5.833%. This exceeds the workbook's approximate 5%-in-six-hours paging starting point.

**Mistake caught:** calling 0.7% “small” without comparing it to allowed 0.1%.

### Problem 4 — Multi-window confirmation

**Statement.** Five-minute burn is 20×, one-hour burn is 0.5×, 30-minute and six-hour burns are 0.5×. Should a paired 14.4×/6× policy page?

**Solution.** No. The fast alert requires short **and** long fast windows above 14.4×; the one-hour window fails. Slow pair also fails. The spike remains visible and may trigger an invariant alert, but this budget-threat policy avoids a transient page.

**Mistake caught:** OR-ing the two windows within a burn-rate pair.

### Problem 5 — Aggregate masking

**Statement.** Tenant A has 999,000 good of 1,000,000 requests; tenant B has 0 good of 100. Compute aggregate and assess.

**Solution.** Aggregate is `999,000/1,000,100≈99.8900%`. It might nearly meet a loose global target while B is completely unavailable. Keep the global user-event SLO and a critical tenant/tier/journey objective or detection. Do not put arbitrary tenant IDs into a high-cardinality real-time metric without capacity/privacy design.

**Mistake caught:** treating aggregate health as proof every cohort is healthy.

### Problem 6 — Retry denominators

**Statement.** One thousand logical payment requests cause 1,180 attempts. Sixty first attempts fail; all but five logical requests eventually succeed within the promised deadline. Compute attempt and user-outcome availability.

**Solution.** We lack complete attempt failure count beyond the stated 60, so we cannot assert attempt availability from 1,180 alone. The logical outcome has 995 good/1,000 = 99.5%. Record attempts separately to reveal retry amplification. If exactly 60 total attempts failed, attempt success is 1,120/1,180≈94.915%, but that is an additional assumption.

**Mistake caught:** inventing missing counts and using retries as user requests.

### Problem 7 — Latency average trap

**Statement.** Nine requests take 40 ms and one takes 2,040 ms. Evaluate a “mean <250 ms” claim and a “99% <250 ms” claim.

**Solution.** Mean is `(9×40+2040)/10=240 ms`, so mean target passes. Only 9/10=90% complete below 250 ms, so a 99% threshold SLO fails for this sample. Small-sample percentiles need careful definition, but exact threshold counts are unambiguous.

**Mistake caught:** allowing a mean to conceal severe tail latency.

### Problem 8 — Missing telemetry

**Statement.** Edge reports 100,000 accepted requests, but service SLI telemetry contains only 96,000. Of those, 95,900 are good. Report safely.

**Solution.** Observed subset success is 99.8958%, but 4,000 outcomes are unknown—far larger than a 99.9% budget of 100 events. Do not call the SLO met. Reconcile using an independent source, alert on telemetry completeness and bound results: best case `(95,900+4,000)/100,000=99.9%`; worst case `95.9%`. Even best case sits exactly at boundary.

**Mistake caught:** dropping missing events from the denominator silently.

### Problem 9 — Low traffic

**Statement.** A service receives 10 requests/hour for 30 days with a 99.9% objective. Compute nominal bad-event budget and explain alert design.

**Solution.** Total is `10×24×30=7,200`; budget is 7.2 bad events. One hourly failure produces 10% hourly error or 100× burn. Decide based on event value: synthetic checks for detection, longer windows, product-appropriate target or fallback/retry. High-value failures may require per-event alerts, not statistical hiding.

**Mistake caught:** applying high-volume burn queries unchanged to sparse traffic.

## 4. REAL-WORLD / APPLIED CONTEXT

Google's SRE book describes Gmail availability appearing materially worse when measured at the client rather than server; service practices report improvement from roughly 99.0% to over 99.9% after client/server work. The lesson is measurement point, not a promise that any client metric automatically improves reliability.

The Google SRE Workbook derives multi-window burn alerts and offers 14.4×/1-hour for roughly 2% budget consumption, 6×/6-hour for 5%, and 1×/3-day ticketing for 10% as starting points. Its low-traffic discussion shows that at ten requests/hour and a 99.9% target, one failure creates a 10% hourly error rate and the full 30-day budget permits about seven failures.

The included Python lab uses only integer event counts and the standard library. Its verified dataset proves: 50 million events at 99.9% yield 50,000 budget events; 200 bad among 100,000 is 2× burn; 500 bad among one million consumes 50% of budget; and both windows must breach for a paired page. Six unit tests and bytecode compilation passed locally; the sub-millisecond test timer is not a production performance benchmark.

## 5. COMPARISON TABLE

| SLI style | Calculation | Strength | Failure/bias |
|---|---|---|---|
| Request-based | good valid requests / valid requests | weights actual user operations | peak traffic spends more budget; retries/denominator must be controlled |
| Time-based | good intervals / all intervals | intuitive downtime minutes | hides traffic variation and partial failures |
| Window-based | good measurement windows / windows | useful for periodic jobs | one bad event can mark whole window; resolution sensitive |
| Synthetic | successful probes / probes | detects zero-traffic/path failure | probe may not represent real auth/data/cohorts |
| Client-side | good client journeys / journeys | closest to experience | sampling/privacy/version/network attribution |
| Server/edge | good observed requests / requests | complete/cheap at owned boundary | misses pre-boundary failure or semantic client outcome |

| Availability | 30-day downtime budget | Typical interpretation |
|---:|---:|---|
| 99% | 7 h 12 min | tolerant internal/noncritical service depending on needs |
| 99.9% | 43 min 12 sec | three nines |
| 99.95% | 21 min 36 sec | common stricter target example |
| 99.99% | 4 min 19.2 sec | expensive, demanding operational discipline |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **SLO equals SLA.** An SLA has explicit consequences; an SLO guides service behavior.
2. **CPU is an SLI.** CPU explains capacity but does not directly measure a user journey.
3. **HTTP 200 is always good.** Wrong/stale/unauthorized content is bad or invariant violation.
4. **All 4xx are user fault.** Authentication/routing regressions can manifest as 4xx; specify ownership.
5. **Dependency errors excluded.** Users still experience them; count them and attribute separately.
6. **Planned maintenance excluded automatically.** It affects users unless explicitly negotiated otherwise.
7. **Server-only measurement.** It misses DNS/TLS/edge failures. Add boundary/client/synthetic evidence.
8. **Missing telemetry means no errors.** It creates uncertainty. Monitor completeness and reconcile.
9. **Attempts equal requests.** Retries inflate the denominator. Track logical outcomes and attempts separately.
10. **Average latency protects users.** Tail events disappear in the mean. Use threshold ratios.
11. **Average of percentages.** Weight by event counts or define independent segment objectives.
12. **Overall SLO protects every tenant.** A small cohort can be fully down. Segment deliberately.
13. **Tenant ID metric label by default.** It creates cardinality/privacy risk. Use bounded dimensions/protected analysis.
14. **99.9 means 43.2 minutes under every model.** That is a 30-day time calculation, not a request budget.
15. **Error budget is outage allowance to spend casually.** It is a risk-control mechanism, not planned harm.
16. **100% is safest.** It is often impossible/costly and prevents rational change; safety invariants remain separate.
17. **Pick target from current graph.** Target should come from user/business need and cost trade-off.
18. **One short burn window pages.** It is noisy. Pair short speed with long confirmation.
19. **High burn always pages sparse traffic.** Consider event count/value, synthetics and product contract.
20. **Freeze every change when exhausted.** Reliability/security fixes may be necessary; policy distinguishes risk.
21. **SLO query never changes.** Version and backtest it as journeys/instrumentation evolve.
22. **Percentile aggregation by averaging.** Aggregate distributions/buckets, not instance percentiles.
23. **Observability has no privacy cost.** Labels/logs can expose regulated identities and incur substantial storage.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- SLI = measured behavior; SLO = target/window; SLA = consequences.
- Specify valid/good/bad/excluded/missing, measurement point, segments, window and owner.
- Request availability: `good / valid`; error budget ratio: `1 − objective`.
- Budget events: `valid × (1 − objective)`.
- Burn: `observed bad ratio / allowed bad ratio`.
- Approximate exhaustion: `SLO window / burn`; adjust for already consumed budget.
- Measure user symptom for paging; use causes for diagnosis.
- Multi-window: fast short AND fast long, OR slow short AND slow long.
- Keep correctness, privacy, security and data loss invariants outside averages.
- Count logical user outcomes separately from attempts/retries.
- Missing telemetry is unknown, not good.
- 30-day time budgets: 99%=7h12m; 99.9%=43m12s; 99.95%=21m36s; 99.99%=4m19.2s.

## 8. PRACTICE SET FOR SELF-TEST

1. A 99.95% request SLO sees 72 million events and 21,600 bad. Calculate budget, consumption, remaining and actual success.
2. Calculate 28-day time budgets for 99.9%, 99.95% and 99.99%.
3. A 99.9% service burns at 12× for three hours. What fraction of a 30-day budget is spent and how long to full exhaustion if sustained?
4. Define valid/good/bad/excluded/missing for a healthcare record retrieval journey, including correctness/privacy invariants.
5. Write PromQL-style numerator/denominator logic for 99% of predictions under 250 ms and explain required histogram boundary.
6. Two regions report `(999,000/1,000,000)` and `(9,000/10,000)`. Compute weighted aggregate and explain needed segmentation.
7. Design multi-window paging and ticket thresholds for a 99.95% high-volume service; translate burn to observed error ratios.
8. Design an SLO for a daily feature pipeline with late-arriving data, reruns and 200 tenant partitions.
9. An edge counts 2 million events but application telemetry has 1.98 million. Describe bounds and operational response if 1,979,000 are good.
10. Draft a one-paragraph error-budget policy for exhausted production budget that permits necessary reliability/security work.

## 9. CURATED RESOURCES

1. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 4, “Service Level Objectives.” Canonical SLI/SLO/SLA terminology, target selection, user focus and controlled overachievement.
2. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 3, “Embracing Risk.” Error budgets as a product–reliability decision mechanism.
3. Betsy Beyer et al., *The Site Reliability Workbook*, Chapter 2, “Implementing SLOs.” Step-by-step journey/specification/implementation adoption.
4. Betsy Beyer et al., *The Site Reliability Workbook*, Chapter 5, [“Alerting on SLOs”](https://sre.google/workbook/alerting-on-slos/). Derivation and trade-offs of multi-window multi-burn alerts, including sparse traffic.
5. Google SRE, [“Production Services Best Practices”](https://sre.google/sre-book/service-best-practices/). Concrete error-budget change policy and page/ticket/log distinctions.
6. Prometheus Documentation, *Query functions* (`rate`, `histogram_quantile`) and *Histograms and summaries*. Exact counter reset, aggregation and quantile mechanics.
7. OpenSLO Specification. Vendor-neutral service-level objective schema and versionable metadata model.
8. Alex Hidalgo, *Implementing Service Level Objectives*, Chapters 3–8. Practical stakeholder negotiation, SLI construction and error-budget policy beyond the Google examples.
9. NIST SP 800-55 Vol. 1, *Measurement Guide for Information Security*. Measurement-program rigor useful for regulated reliability evidence, though not an SRE-specific SLO guide.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Capacity-Driven Design:** predicted load/failure behavior suggests attainable objectives and necessary headroom.
2. **Cloud Identity and Networking:** DNS, edge, identity and private endpoints are user-path dependencies included in SLIs.
3. **CI/CD Supply Chain:** release risk is governed using error-budget state.
4. **Distributed Failure Semantics:** timeouts, retries and idempotency determine which logical outcomes count good.

### After

1. **Metrics, Logs and Traces:** implements SLI counters/distributions and diagnoses budget burn.
2. **Incident Response:** SLO burn decides urgency; incident work restores user outcomes.
3. **Capacity and Disaster Recovery:** objectives translate into redundancy, failover and recovery requirements.
4. **MLOps Monitoring:** model quality, freshness and drift need precise indicators/objectives beyond API uptime.

---ANSWER KEY BELOW---

1. Allowed ratio `0.0005`; budget 36,000. Consumed 60%, remaining 14,400. Success `(72,000,000−21,600)/72,000,000=99.97%`.
2. Twenty-eight days = 40,320 minutes. 99.9% permits 40.32 min; 99.95% permits 20.16 min; 99.99% permits 4.032 min = 4 min 1.92 sec.
3. Three hours is `3/720` of 30 days; at 12× it spends `12×3/720=0.05`, or 5%. Sustained full-budget exhaustion is `30/12=2.5 days` from a fresh budget; after that spend, remaining time at 12× is `0.95×2.5=2.375 days`.
4. Valid: authorized well-formed retrieval attempts reaching edge for an existing supported tenant/version. Good: correct authorized record/version returned within threshold or contractually correct not-found, with no cross-tenant disclosure. Bad: timeout, 5xx, wrong/stale-beyond-bound record, authorization-service-caused denial or malformed response. Exclude proven caller-invalid/test traffic by predeclared rule; classify missing independently. Cross-tenant disclosure/unauthorized read and audit loss are invariants requiring immediate response, not budgeted failures.
5. Numerator is rate/sum of cumulative `duration_bucket{le="0.25"}` for valid prediction observations; denominator is matching duration count, aggregated across instances with identical bounded labels. The histogram must include a 0.25-second bucket; otherwise a neighboring bucket changes the defined threshold rather than approximating it silently.
6. Good total 1,008,000; valid 1,010,000; aggregate `99.80198%`. Region 2 is only 90% and must not be masked; retain global event-weighted objective plus region/journey guardrail or SLO justified by user expectations.
7. Example starting policy uses paired 5m/1h at 14.4× and 30m/6h at 6×, plus 3d ticket at 1×, adjusted after backtest. For 99.95%, allowed error is 0.0005: thresholds are `14.4×=.72%`, `6×=.30%`, `1×=.05%` observed bad ratios. Both windows within a page pair must breach.
8. Valid events are 200 expected tenant/date partitions after an agreed arrival cutoff; good means validated feature output for correct source watermark/schema published by deadline. Track timeliness and correctness separately, count a partition once despite reruns, record late-source exclusions by predeclared policy, segment regulated tier, and use durable orchestrator/storage timestamps rather than heartbeat.
9. Observed subset success is `1,979,000/1,980,000≈99.9495%`, but 20,000 are unknown. Against edge denominator, worst is `98.95%`; best is `1,999,000/2,000,000=99.95%`. At 99.9%, best meets but uncertainty is 20× the 2,000-event budget; alert telemetry health, reconcile edge IDs/outcomes and do not declare compliance until evidence completes.
10. Example: “When the rolling 30-day production availability budget is exhausted, pause nonessential releases and experiments that can increase user risk. Security patches, incident mitigations and changes with evidence that they reduce the active failure cause may proceed through expedited peer/on-call approval and canary guardrails. Resume normal release after the owner documents causes/actions, burn is below the recovery threshold for seven days, telemetry is complete and product plus SRE approve; exceptions require named approver, scope and expiry.”
