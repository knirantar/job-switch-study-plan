# Reliability, Availability, and Failure Basics from Scratch

Parent subject: `06-sre-observability`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Reliability is an outcome, not a component count

**Reliability** is the probability that a system performs its required function correctly for a stated time under stated conditions. **Availability** is the proportion/probability that the service is usable when required. **Durability** concerns retaining data. **Correctness** concerns producing the right result. A service returning a fast HTTP 200 with the wrong payment decision is available at the protocol layer but unreliable at the user/business layer.

The conditions and function must be explicit. “The API is reliable” says little. “Authenticated tenants can submit a valid claim and retrieve the committed status within 2 seconds, with no duplicate claim and no cross-tenant disclosure” is testable. Reliability includes latency, data integrity, freshness, security, and business semantics where users depend on them.

Reliability engineering grew from safety-critical and industrial systems, telecommunications, hardware, and software operations. Hardware theory often assumes failure rates and repair distributions; software does not wear out physically, but defects, change, load, dependencies, configuration, and operator actions create failures. Quantitative models are useful only when their assumptions are stated.

### Fault, error, and failure

A **fault** is a cause, such as a defective deployment, expired certificate, disk loss, or malformed message. An **error** is an incorrect internal state, such as corrupt cache state or exhausted connection pool. A **failure** is externally observable deviation from the required service. One fault may stay latent, create many errors, or cascade into multiple failures.

A **failure mode** describes how something fails: crash, omission, timeout, stale response, corruption, duplicate, overload, unauthorized access, or Byzantine/arbitrary behavior. A **failure effect** describes consequences. **Failure Mode and Effects Analysis (FMEA)** systematically lists component/function, mode, causes, local/system effects, detection, prevention/mitigation, and residual risk.

### Dependability vocabulary

- **Mean time to failure (MTTF):** average operating time before non-repairable failure under a model.
- **Mean time between failures (MTBF):** average time between repairable failures, often uptime interval.
- **Mean time to repair/restore (MTTR):** average time to restore service; organizations must define whether diagnosis and validation are included.
- **Mean time to detect (MTTD):** time from failure start to detection.
- **Mean time to acknowledge (MTTA):** time to responder acknowledgment.

For a simple repairable component, steady-state availability is approximated by `MTBF / (MTBF + MTTR)`. If MTBF=720 hours and MTTR=2 hours, availability≈99.723%. This assumes stationary independent cycles and a meaningful mean; real incident distributions and scheduled maintenance may violate it.

Improving MTTR can be cheaper and more controllable than preventing every failure: automated detection, rollback, failover, runbooks, and rehearsals. But a ten-minute data corruption can create permanent harm, so availability alone never replaces safety/durability.

### Failure domains and correlated failure

A **failure domain** is a set of components likely to fail together: process, host, rack, zone, region, software version, deployment pipeline, identity provider, DNS, account, or human team. Redundancy helps only when replicas do not share the fault that matters.

Two instances on one host do not protect host loss. Instances across zones may still share a regional database or broken release. Multi-region replicas may share globally pushed configuration, credentials, DNS, or code. Identify physical, logical, operational, and organizational common causes.

### Redundancy

**Active-active** replicas serve simultaneously. **Active-passive** keeps standby capacity/state and promotes it. **N+1** means one extra unit beyond required capacity; **N+2** tolerates two unit failures under assumptions. Redundancy can be spatial (different zones), temporal (retry/checkpoint), informational (error-correcting copies), or functional (fallback implementation).

If two independent components each have availability A and either suffices with perfect failover, combined availability is `1-(1-A)^2`. At A=.99, result .9999. If both depend on one .99 database, path availability is about `.9999×.99=.989901`, worse than either replicated frontend suggests. Independence and failover perfection are strong assumptions.

### Series systems and dependency paths

When all serial components must work, availability multiplies under independence. Five dependencies each .999 yield `.999^5≈.99501`. Reliability decreases as mandatory fan-out grows. Reduce dependencies in the critical path, cache/degrade safely, replicate, or improve weakest components.

Dependency criticality is operation-specific. Claim submission may require identity, database, and idempotency store; viewing static help should work without them. A whole service should not become unavailable because a noncritical recommendation engine fails.

### Graceful degradation

**Graceful degradation** preserves the highest-value safe capability under failure. Examples: serve cached public catalog with freshness label; disable recommendations while checkout works; queue nonurgent analytics; route uncertain clinical decisions to human review. It is not returning fabricated defaults.

A fallback must preserve invariants and expose quality. Returning “no medications” when the clinical database timed out is unsafe because unknown becomes none. Returning “temporarily unavailable; use verified clinical workflow” is reliable degradation.

### Overload and cascading failure

Overload occurs when offered work exceeds sustainable capacity. Queues grow, latency rises, callers time out and retry, connections/memory accumulate, health checks fail, load shifts to remaining instances, and a local saturation becomes a cascade.

Queueing delay rises sharply as utilization approaches 100%, even before nominal throughput is exceeded. Maintain headroom, bound queues/concurrency, set deadlines, reject excess early, shed lower-priority work, apply backpressure, retry with budget/jitter, and protect dependencies. Autoscaling is delayed and cannot rescue an already collapsing shared database.

### Blast radius and bulkheads

**Blast radius** is the scope affected by a fault. Partition resources by tenant, workload priority, region, cell/stamp, queue, connection pool, or credentials so one noisy tenant or deployment does not consume all capacity. **Bulkheads** isolate resource pools like ship compartments.

Isolation trades utilization and complexity. A single global pool is efficient but couples all callers; per-tenant pools prevent domination but waste capacity and create many limits. Hierarchical fairness—global bound plus tenant quotas/reservations—often balances both.

### Recovery, failover, and failback

**Failover** moves service to redundant capacity. **Recovery** restores normal ability/data. **Failback** returns to a preferred topology. These are separate, risky transitions. Automated failover needs trustworthy detection, fencing old authority, sufficient standby capacity, dependency/DNS routing, and data-point validation.

A backup is recovery input, not recovered service. RPO defines acceptable data loss measured in time/version; RTO defines acceptable restoration time. Recovery tests must restore at realistic scale, validate application behavior and permissions, and exercise failback. High availability handles some immediate component failures; disaster recovery handles larger loss and prolonged restoration.

### Risk and reliability investment

Risk combines likelihood and impact, but simple multiplication can hide catastrophic low-frequency events. Include safety, regulatory, privacy, financial, reputational, and recovery consequences. Reliability has cost and opportunity trade-offs. Error budgets later provide a product mechanism; threat modeling, FMEA, chaos/failure testing, and business impact analysis find what to protect.

## 2. CORE MECHANICS

### 2.1 Define the user journey

For claim submission, success requires authorized request, valid input, one durable claim under idempotency key, response/status within deadline, audit record, and no tenant leak. Count malformed/unauthorized requests separately from service failures. Define what happens if response is lost after commit: retry with the same key returns the same outcome.

This journey definition leads directly to useful SLIs. CPU is diagnostic; it does not define submission reliability.

### 2.2 Calculate simple availability

Service had three incidents in 30 days lasting 12, 25, and 8 minutes. Total period 43,200 minutes; unavailable 45; observed time availability `(43200-45)/43200≈99.8958%`. If only 20% users were affected in one incident, a request-based SLI may represent impact better than binary time.

At 99.9%, a 30-day allowance is 43.2 minutes. One 45-minute full outage consumes more than the monthly allowance. Do not round 99.8958 to 99.9 and claim compliance if objective mathematics/policy says otherwise.

### 2.3 MTBF/MTTR model

Ten incidents over 8,760 hours, total repair time 20 hours. Approximate operating hours 8,740; MTBF≈874 hours; MTTR=2 hours; availability model `874/(876)=99.7717%`. Direct measured unavailability is `20/8760=0.2283%`, same under the constructed data.

Means hide tail: nine 10-minute incidents and one 18.5-hour incident have similar total but very different response risk. Track distributions and severity.

### 2.4 Analyze serial and parallel designs

API .999, identity .9995, DB .9999, all mandatory and independent: `.999×.9995×.9999≈.99840065` (99.8401%). To improve, removing identity from every cached public read is operation-specific; making identity two .9995 replicas gives theoretical `1-(.0005)^2=.99999975`, but shared control/data stores must be modeled.

Avoid multiplying published SLAs as if they are independent probabilities. SLA is contractual measurement, not necessarily component random availability.

### 2.5 Size failure capacity

Peak 18,000 rps; safe instance capacity 1,200. Need 15 healthy. Across three zones, tolerate one zone loss: the two surviving zones must contain at least 15, so provision 8 per zone=24 total. This provides 19,200 surviving capacity, 6.7% headroom—likely still too low for imbalance/spikes, so measure and add safety.

N+1 works only for one unit. If one zone contains eight units, adding one total is not zone redundancy.

### 2.6 Bound overload

At 2,000 rps arrival and 50 ms service, average concurrency by Little's Law is 100. If latency reaches 500 ms, concurrency becomes 1,000. Set global concurrent-work cap perhaps from load tests, bounded queue, and immediate 429/503 for overflow. Retryable responses include delay guidance, but clients must use total budgets and jitter.

Prioritize critical `authorize-payment` over analytics export. Reserve capacity and ensure lower-priority tasks cannot exhaust DB connections/thread pools used by critical work.

### 2.7 FMEA example

Failure mode: TLS certificate expires on gateway. Cause: renewal job succeeded but deployment binding failed. Effect: all new client handshakes fail. Detection: synthetic TLS expiry/load check and remaining-validity alert. Prevention: automated issuance plus binding validation, overlap rotation. Mitigation: deploy previous/new valid certificate; protect private key. Evidence: expiry, gateway config version, handshake metrics. Residual risk: shared CA/control-plane issue.

Score severity/occurrence/detectability only as prioritization; numeric RPN can imply false precision.

### 2.8 Design degradation

Model-scoring dependency fails. For low-risk recommendation, omit score and label unavailable. For payment fraud, use conservative rule engine/manual review according to policy; do not auto-approve with zero score. For clinical decision, suspend automated decision and require qualified human workflow. Degradation is domain-specific.

### 2.9 Run a failure experiment

Hypothesis: losing one zone keeps p99 under 400 ms and error under 0.5% at peak. Preconditions: recovery path/capacity verified, abort thresholds, owner, window, no competing change. Inject removal of zonal targets, observe traffic redistribution, saturation, DB connections, user SLI. Abort on safety threshold; restore; record evidence and remediation.

Chaos is controlled hypothesis testing, not random production breakage.

### 2.10 Reduce common-mode risk

Use staged deployments by zone/cell, independent credentials and quotas where appropriate, versioned configuration with canary, multiple DNS resolvers, backup account/region, diverse dependency paths, and break-glass identity. Diversity can introduce complexity/latent incompatibility, so exercise it. Two implementations maintained by one flawed specification can share a semantic fault.

## 3. WORKED PROBLEMS

### Problem 1 — Availability from downtime (easy)

Twenty minutes unavailable in a 30-day month.

**Solution.** `1-20/43200=.999537...` = 99.9537%.

**Trap:** reporting 99.95 without showing measurement window/scope.

### Problem 2 — MTBF approximation (easy)

MTBF 1,000 h, MTTR 1 h. Availability?

**Solution.** `1000/1001≈99.9001%` under simple steady-state assumptions.

**Trap:** subtracting one hour from 1,000 rather than using cycle length.

### Problem 3 — Serial dependencies (easy)

Two mandatory independent 99% components.

**Solution.** `.99²=.9801` or 98.01% path availability.

**Trap:** averaging to 99%.

### Problem 4 — Parallel redundancy (medium)

Two independent 99% replicas, either sufficient, perfect routing.

**Solution.** Both fail probability `.01²=.0001`; availability 99.99%.

**Trap:** adding 99+99 or ignoring load balancer/common dependency.

### Problem 5 — Error budget (medium)

99.95% request objective over 10 million requests.

**Solution.** Bad budget `.0005×10,000,000=5,000` requests. Define valid denominator and rounding policy.

**Trap:** using all bot/malformed requests without SLI contract.

### Problem 6 — Overload backlog (medium)

Arrival 1,500/s, service 1,200/s for 10 minutes.

**Solution.** Net 300/s×600=180,000 queued if unbounded. This is delayed failure; bound/shedding is required.

**Trap:** calling the service successful because it accepted all messages.

### Problem 7 — Zone capacity (hard)

Three zones, five instances each, 1,000 rps safe, peak 11,000. Survive a zone?

**Solution.** Ten survivors handle 10,000, so no. Six/zone leaves 12,000 after loss, only 9.1% headroom; likely provision/test more.

**Trap:** normal 15,000 capacity.

### Problem 8 — Unsafe fallback (hard)

Consent service times out; system treats null as consent granted.

**Solution.** Violates privacy/safety. Fail closed for protected access, possibly route to approved emergency workflow with audit. Cache only valid consent under bounded freshness/revocation design.

**Trap:** availability optimization overriding authorization.

### Problem 9 — Correlated replicas (hard)

Three-zone service deploys broken config globally at once. Does zonal redundancy help?

**Solution.** No; configuration is common-mode. Stage/canary configuration by cell/zone, validate schema/invariants, retain rollback and independent control path.

**Trap:** considering only hardware faults.

## 4. REAL-WORLD / APPLIED CONTEXT

### Netflix Hystrix and resilience patterns

Hystrix popularized timeouts, circuit breakers, bulkheads, and fallbacks for service dependencies. The library is maintenance-only, but patterns remain in Resilience4j and service meshes. A breaker protects capacity; it does not repair a dependency, and unsafe fallback can be worse than failure.

### Google SRE overload control

Google SRE literature treats overload as a reliability problem, using load shedding, graceful degradation, retries with budgets, and capacity planning. Accepting unlimited work converts immediate explicit rejection into high-latency collapse.

### Cell-based architecture

Large SaaS systems partition tenants into deployment cells/stamps with independent compute/data limits. A cell failure affects a subset rather than everyone. Routing/control planes remain shared risks, and tenant placement/rebalancing needs tooling.

## 5. COMPARISON TABLE

| Concept | Measures/does | Example | Limitation |
|---|---|---|---|
| Reliability | Correct function over time/conditions | Correct claim workflow | Requires precise function |
| Availability | Usable proportion/probability | Successful request fraction | Can ignore correctness/durability |
| Durability | Data retained | Committed ledger survives | Does not ensure access |
| MTBF | Average interval between failures | 720 h | Mean/stationarity hides tail |
| MTTR | Average restore duration | 30 min | Definition varies |
| Active-active | All replicas serve | Multi-zone APIs | Conflicts/shared dependencies |
| Active-passive | Standby promotes | Database replica | Failover lag/capacity/testing |
| Retry | Temporal redundancy | Transient read failure | Amplification/duplicates |
| Bulkhead | Isolates resources | Per-priority pool | Lower utilization/complexity |
| Graceful degradation | Preserves safe core | Disable recommendations | Domain correctness essential |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Availability equals reliability.** Wrong results can be quickly available.
2. **Durability equals backup.** Authorized deletion/corruption can persist/replicate.
3. **More replicas always help.** Common faults and insufficient surviving capacity remain.
4. **Independent probability math applies to cloud zones automatically.** Software/control dependencies correlate.
5. **MTBF predicts the next failure.** It is an aggregate model.
6. **Average MTTR tells the full story.** Tail/severity distributions matter.
7. **Autoscaling prevents overload.** It reacts with delay and may overload dependencies.
8. **Queues solve capacity mismatch.** Sustained positive backlog grows without bound.
9. **Fallback means return a default.** Defaults can violate safety/business truth.
10. **Failover proves recovery.** Data validation and failback remain.
11. **Chaos means random faults.** It requires hypothesis, bounds, abort, evidence.
12. **99.9 rounds up from anything near it.** Objectives require exact measurement policy.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Fault causes error; externally visible deviation is failure.
- Reliability = correct function under stated time/conditions.
- Availability ≠ correctness ≠ durability ≠ recovery.
- Simple A≈MTBF/(MTBF+MTTR).
- Serial independent path: multiply availability.
- Either-of-two independent: `1-(1-A)^2`.
- Redundancy needs fault-domain independence and surviving capacity.
- Bound queues/concurrency; shed early; protect critical priorities.
- Fallback must preserve domain safety and expose uncertainty.
- Failover, recovery, and failback are distinct.
- RPO loss; RTO restoration; test both at scale.
- Stage changes to reduce common-mode blast radius.

## 8. PRACTICE SET FOR SELF-TEST

1. Distinguish fault, error, and failure for an expired DB certificate.
2. Compute availability for MTBF 500 h and MTTR 30 min.
3. Compute serial availability of .999 and .9999.
4. Compute ideal either-replica availability for two .995 replicas.
5. Calculate bad requests allowed by 99.9% over 25 million.
6. Calculate backlog for 4,000/s arrival and 3,500/s service over 20 minutes.
7. Design safe degradation when optional recommendation service fails.
8. Explain why two regions sharing one identity tenant may correlate.
9. List fields in an FMEA row.
10. State a zone-loss experiment hypothesis and abort condition.

## 9. CURATED RESOURCES

- Patrick O'Connor and Andre Kleyner, *Practical Reliability Engineering*, 5th ed., Chapters 1–4 and 16 — reliability definitions, failure data, models, and software reliability.
- Betsy Beyer et al., *Site Reliability Engineering*, Chapters 3, 4, 6, 21, 22, and 34 — risk, SLOs, monitoring, overload, cascading failure, and testing reliability.
- Michael Nygard, *Release It!*, 2nd ed., Chapters 3–5 — stability patterns, circuit breakers, bulkheads, timeouts, and production failure.
- John Allspaw and Jesse Robbins, *Web Operations*, chapters on resilient architectures and operations — production-focused reliability practice.
- IEC 60812:2018, “Failure modes and effects analysis (FMEA and FMECA)” — canonical systematic failure-analysis process.
- AWS Builders' Library, “Avoiding overload in distributed systems,” “Timeouts, retries, and backoff with jitter,” and “Static stability using Availability Zones” — concrete capacity and failure patterns.
- Microsoft Azure Well-Architected Framework, Reliability pillar — Azure-specific fault domains, redundancy, recovery, degradation, and testing guidance.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Production Operations:** establishes ownership, change, runbooks, and incident context.
2. **Distributed Systems Foundations:** establishes partial failure, replication, partitions, and consistency.
3. **Cloud Foundations:** establishes zones/regions, scaling, storage, and shared dependencies.

### After

1. **Monitoring and Alerting:** detects reliability symptoms and guides action.
2. **SLIs/SLOs/Error Budgets:** defines precise objectives and allowable unreliability.
3. **Failure Semantics:** implements timeout/retry/breaker/bulkhead mechanics.
4. **Incident Response:** mitigates realized failures.
5. **Capacity and DR:** sizes surviving systems and proves recovery.

---ANSWER KEY BELOW---

1. Fault: expired certificate; error: new DB TLS connections cannot authenticate/pool exhausts; failure: user operations time out/fail.
2. `500/(500+.5)=99.9001%` approximately.
3. `.9989001` = 99.89001%.
4. `1-.005²=.999975` = 99.9975% under assumptions.
5. `.001×25,000,000=25,000`.
6. 500/s×1,200=600,000.
7. Omit recommendations with explicit unavailable status while preserving core transaction; do not fabricate a recommendation.
8. Credential/config/control-plane outage or policy error can affect both; diversify/recover access as threat model requires.
9. Function/component, failure mode, cause, local/system effect, severity/likelihood/detection, controls, mitigation, owner/residual risk.
10. Example: one-zone loss keeps error<.5%, p99<400 ms at peak; abort if payment/clinical correctness fails, error>2%, or surviving saturation crosses tested safe bound.
