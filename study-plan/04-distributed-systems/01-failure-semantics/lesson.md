# Failure Semantics in Distributed Systems

**Parent:** 04 — Distributed Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus failure-injection drills

## 1. FOUNDATIONS

Inside one process, a function usually returns a value or throws. Across a network, a caller can send a request, wait, and receive nothing. Nothing is not a single outcome. The request may never have reached the server; it may be queued; the server may have committed and lost the response; the response may be delayed; the client may be partitioned while the server remains healthy. A timeout proves the caller stopped waiting. It does not prove the operation did not happen.

That ambiguity is the defining feature of distributed failure. A **distributed system** has independently executing components communicating through channels with variable delay and partial failure. **Partial failure** means one component or link fails while others continue. A process cannot perfectly distinguish a crashed peer from a slow or partitioned peer using finite waiting alone. Timeouts are therefore local decisions, not oracles.

Engineers describe failures by semantics. A **fail-stop** process halts and is detectable by an ideal mechanism; real systems only approximate this. A **crash fault** stops execution, perhaps recovering later. An **omission fault** loses a send or receive. A **timing fault** responds outside the required interval. A **Byzantine fault** behaves arbitrarily or maliciously. Most product backends are designed mainly for crash, omission and timing faults, while security boundaries may require Byzantine thinking.

Networks can delay, drop, duplicate and reorder messages. TCP provides an ordered byte stream for one connection while it exists; it does not tell your application whether a transaction committed when the connection breaks, nor does it supply exactly-once business processing. DNS, connection establishment, TLS, proxies, load balancers, queues and application handlers each have separate failure and timeout behavior.

The motivation for resilience mechanisms is to turn uncertain lower-level behavior into an explicit product contract. A **deadline** says when the result stops being useful. A **timeout** bounds one wait. A **retry** creates another attempt. **Backoff** spaces attempts. **Jitter** randomizes spacing so clients do not synchronize. A **circuit breaker** suppresses attempts when failure evidence is high. A **bulkhead** caps one dependency's resource use. **Load shedding** rejects work early to preserve useful throughput. None supplies correctness alone; each changes load and failure shape.

Distributed-systems theory formalizes limits. Fischer, Lynch and Paterson showed that in a fully asynchronous message-passing model, deterministic consensus cannot guarantee termination with even one possible crash. FLP does not say practical consensus is impossible; real systems use clocks, randomized behavior and partial-synchrony assumptions, accepting that progress can pause during adverse periods. The lesson for interviews is precise assumptions: safety (“nothing bad happens”) and liveness (“something good eventually happens”) are separate.

For a senior engineer, failure is part of the API. State whether an operation is safe, idempotent, retryable, cancelable and observable. Define what a caller receives for rejected, timed out, in-progress, committed and unknown outcomes. Then prove the design under concurrency and injected failure.

## 2. CORE MECHANICS

### 2.1 Failure domains and correlated failure

A **failure domain** is a set of components likely to fail together: process, VM, host, rack, availability zone, region, identity provider, DNS zone, deployment version or shared database. Three replicas on one node are not three independent failure domains. Multi-zone copies can still share a faulty release or exhausted account quota.

Map dependency edges and shared resources. If frontend A and worker B both depend on the same connection pool or Redis shard, apparent independent paths can fail together. Avoid assuming probabilities multiply unless independence is justified. Two components each advertised at 99.9% availability do not automatically yield 99.9999% together; serial dependency can approximate `0.999×0.999=0.998001`, or about 99.8001%, before correlated failures.

### 2.2 Timeout versus deadline

A **timeout** is a duration allowed for an operation/stage. An absolute **deadline** is the latest completion time for the end-to-end request. Deadlines compose better: downstream services receive the remaining time instead of each starting a fresh 500 ms timeout.

Suppose the user budget is 800 ms. Authentication consumes 90 ms, service queueing/logic 125 ms, and 85 ms is reserved for response serialization/network. Remaining downstream budget is `800-90-125-85=500 ms`, as tested in `FailurePolicyLab.java`. If service B then calls C, B propagates the remaining deadline, subtracting its own reserve. Starting a 700 ms database query would create work whose answer arrives after the caller has abandoned it.

Timeout coverage must include DNS resolution, connection acquisition, TCP/TLS handshake, request write, response headers/body and pool waits as appropriate. A socket read timeout alone may omit earlier phases. Conversely, one too-small end-to-end timeout can classify normal cold connection establishment as failure. Pre-establishing connections may reduce this deployment-specific tail, but measurement must include cold and warm paths.

Use a monotonic clock for elapsed durations inside a process. Wall clocks can jump from synchronization or administrative changes. Across processes, propagate deadlines in a representation/protocol that accounts for clock uncertainty, often as timeout remaining rather than trusting identical wall clocks.

### 2.3 Unknown outcome and idempotency

Consider `POST /payments`. The database commits; the response packet is lost; client times out. Retrying with a new identity can charge twice. The correct state is **unknown**, not failed. Client supplies stable tenant-scoped idempotency key and request fingerprint. Server atomically stores the key, fingerprint, state and result with business mutation. Same key/same request returns the same outcome; same key/different request is conflict.

Idempotency means applying the same logical operation multiple times has the same intended effect as once. HTTP method semantics help—GET is intended safe/idempotent, PUT/DELETE idempotent under their resource meaning—but server bugs and downstream side effects still matter. Do not retry POST merely because status is 503 unless an idempotency contract exists.

Exactly-once end-to-end is usually implemented as at-least-once delivery plus durable deduplication/transactional effects. Dedupe records need scope, retention and response semantics. If keys expire after 24 hours but a mobile client retries after 36, duplication is again possible; retention is part of the guarantee.

### 2.4 Retry classification

Retry only when all three hold:

1. Failure may be transient (for example selected connect failures, 429, 502, 503, 504, SQLSTATE `40001`).
2. Operation is safe/idempotent or protected by stable idempotency identity.
3. Enough deadline and retry budget remains for a useful attempt.

Do not retry malformed requests, authorization denial, most 4xx domain errors or deterministic validation failures. A timeout is potentially transient but ambiguous. Connection-refused before sending bytes differs from response loss after server commit, though client libraries may not always expose enough detail.

Retry at one deliberate layer. If browser, gateway and service each make four total attempts, one user action can create `4³=64` leaf attempts. Google SRE uses this exact multiplicative reasoning. `FailurePolicyLab.maxLeafAttempts(4,3)` verifies 64. Prefer the layer that understands idempotency, deadline and error meaning.

### 2.5 Exponential backoff and jitter

With base 25 ms, capped exponential delay before retry number `r` can be `min(1000,25×2^r)`. Without jitter, thousands of clients failing together retry at 25, 50, 100... ms together—a **thundering herd**. Full jitter chooses uniformly from `[0,cap]`. At retry 3, cap is 200 ms; deterministic random fraction 0.5 yields 100 ms in the lab.

Backoff does not reduce total attempt count by itself; it spreads it and gives recovery time. Cap attempts, cap total retry time, honor server `Retry-After` where applicable, and maintain a **retry budget** (for example attempts attributable to retries no more than 10% of successful originals over a window). A budget prevents retries from becoming the dominant load during outage.

Randomness must not make unit tests flaky: inject RNG/sleeper/clock, test bounds and state transitions, and use production randomness at runtime.

### 2.6 Cancellation and cooperative abort

When a deadline expires, cancel downstream work where protocols support it. Cancellation is advisory: the server may already have committed or may ignore it. Check remaining deadline before expensive stages and propagate cancellation through futures/reactive chains. Database statement timeout and HTTP request cancellation can save capacity, but cleanup must release connections, permits and temporary resources.

Never use thread interruption as proof a remote effect did not occur. Represent operation state durably and reconcile ambiguous results. A long-running ML job should return an operation ID, support status query/cancel request and define terminal states; synchronous connection lifetime should not be the only ownership record.

### 2.7 Bulkheads and bounded concurrency

A **bulkhead** isolates resource capacity. Give dependency A 40 concurrent permits and B 20 so A's latency cannot consume every request thread/connection. Bound queues as well as active work. Little's Law relates average in-flight work `L`, arrival rate `λ` and response time `W`: `L=λW` in stable conditions. At 500 requests/s and 200 ms average, expected in-flight is `500×0.2=100`. If latency rises to 2 seconds with arrival unchanged, it becomes about 1,000, multiplying memory/connections.

Unbounded queues convert overload into latency and memory exhaustion. Once deadline cannot be met, reject cheaply (HTTP 429 for caller quota/rate, often 503 for capacity) instead of doing useless work. Prioritize only with explicit fairness; one enterprise tenant must not starve smaller tenants.

Global concurrency equals per-instance limit times active replicas and retry/hedge behavior. Forty dependency permits across 25 pods can produce 1,000 concurrent calls. Size against downstream capacity, not local comfort.

### 2.8 Circuit breakers

A breaker is CLOSED while calls flow. After a configured failure signal it becomes OPEN and fails fast. After an open interval it moves HALF_OPEN and permits a small number of probes; success closes, failure reopens. This state machine is tested in the lab.

Breaker design needs a minimum sample volume, sliding window, failure/slow-call classification, open duration and half-open concurrency. Five failures out of five at 2 a.m. differs from five out of 50,000. Fleet-local breakers can synchronize and then probe together; jitter open intervals and cap probes. Breakers do not replace timeouts, retry budgets or load shedding. They can block recovery if health classification is wrong.

### 2.9 Rate limiting, load shedding and graceful degradation

Rate limiting enforces policy before overload; load shedding protects capacity during overload. Token bucket permits bursts up to bucket capacity with refill rate. A bucket of 200 and refill 100/s can accept a burst of 200, then about 100/s steady. Distributed enforcement can be approximate or centralized; define scope and failure posture.

Degradation returns cheaper but useful output: cached model metadata instead of live aggregation, delayed optional enrichment, smaller search scope, asynchronous acceptance, or read-only behavior. Never degrade authorization, financial amount or clinical safety silently. Attach explicit freshness/quality metadata when users or downstream logic care.

Google SRE documents overload as a primary cause of cascading failure. When replicas fail, traffic moves to survivors, increasing their load and causing more failure. Recovery may require shedding far below the original healthy QPS because only a fraction of capacity is alive and caches are cold.

### 2.10 Hedged requests

A hedge sends a duplicate to another replica after a delay to cut tail latency, taking the first response. It increases load and is appropriate only for safe/idempotent requests, independent replicas, sufficient capacity and a carefully chosen trigger (often a high percentile rather than immediately). Cancel loser work. If every request is hedged, traffic nearly doubles; under overload, hedging worsens the tail it was meant to fix.

### 2.11 Health checks and failover

**Liveness** asks whether process should restart. **Readiness** asks whether it should receive traffic. A dependency outage should not necessarily fail liveness and restart every healthy process. Deep health checks through all dependencies can amplify load and remove all replicas simultaneously. Readiness should reflect ability to serve the relevant path without flapping.

Failover is a capacity event. If region B holds 40% traffic and fails, region A must absorb it or shed/degrade. Active-passive capacity that is untested/cold can fail on promotion. DNS TTL, client caching, connection pools, data lag and write authority determine recovery; “multi-region” alone is not a guarantee.

### 2.12 Queues and asynchronous boundaries

Queues decouple arrival from processing but do not create capacity. Backlog growth rate is arrival minus service. At 2,000 jobs/s arrival and 1,500/s processing, backlog grows 500/s: 1.8 million in one hour. Track oldest-message age, not only depth; priority and variable job cost can make depth misleading.

Bound retention and payload sizes, use dead-letter/quarantine policies carefully, and make consumers idempotent. Backpressure should reach producers through admission controls rather than letting storage fill. Acknowledging async acceptance means the API contract becomes “durably queued,” not “business operation completed.”

### 2.13 Observability and failure testing

Track logical requests separately from attempts. Record end-to-end deadline, remaining budget at each hop, timeout phase, retry reason/attempt, idempotency outcome, breaker state, bulkhead permits/queue, shed/degraded counts, dependency latency/errors and useful work completed after caller cancellation. Trace IDs correlate attempts; idempotency keys should be hashed/redacted if sensitive.

Test latency injection, packet loss, response loss after commit, process kill, replica loss, exhausted pools, cold cache, DNS/TLS delays and clock skew where relevant. Ramp and impulse load reveal different failures. Abort chaos if data integrity or production SLO guardrails are crossed; experiments need hypothesis, blast radius and rollback.

## 3. WORKED PROBLEMS

### Problem 1 — Budget a request

**Statement.** API deadline is 800 ms. Auth used 90 ms, local work 125 ms, and response reserve is 85 ms. How much can be offered downstream?

**Solution.** `800-90-125-85=500 ms`. Propagate at most 500 ms, preferably reserving any downstream cleanup/serialization explicitly. If only 40 ms remains and dependency's known minimum useful time is 80 ms, reject/degrade rather than starting doomed work.

**Mistake caught.** Giving every hop a fresh 800 ms timeout.

### Problem 2 — Retry amplification

**Statement.** Mobile, gateway and service each allow four total attempts. How many database attempts can one action create?

**Solution.** Worst-case multiplicative attempts are `4×4×4=64`. Centralize retry at the layer with operation semantics, make other layers pass failures, and enforce an end-to-end attempt/retry budget. Four attempts means initial plus three retries; vocabulary must be explicit.

**Mistake caught.** Adding retry counts (`4+4+4=12`).

### Problem 3 — Ambiguous payment

**Statement.** Client times out after server commits ₹1,250 payment.

**Solution.** Return/represent unknown locally; retry using the same tenant idempotency key and same request fingerprint. Server's unique key retrieves stored/in-progress result. If fingerprint differs, reject conflict. Reconcile by operation status; never create a new key automatically. Persist payment and key atomically.

**Mistake caught.** Mapping timeout to failed and issuing a fresh payment.

### Problem 4 — Concurrency capacity

**Statement.** 20 pods each allow 60 concurrent model-registry calls; registry safely handles 500.

**Solution.** Fleet permits total `20×60=1,200`, already 2.4× safe capacity before retries. Allocate global budget with headroom, e.g. 400 total means 20 per pod at 20 pods, then account for autoscaling and unequal traffic. A central/adaptive limiter or distributed quota may be needed as replica count changes.

**Mistake caught.** Sizing only one pod's semaphore.

### Problem 5 — Queue overload via Little's Law

**Statement.** Arrival is 300/s; average service latency rises from 100 ms to 3 s.

**Solution.** Stable average in-flight rises from `300×0.1=30` to `300×3=900`. If pool/queue holds 200, it saturates; waiting increases latency further. Bound admission, shed after useful deadline, degrade optional work and reduce retries. Little's Law assumes stable averages; an overloaded, growing queue is not steady state, but calculation exposes pressure.

**Mistake caught.** Adding threads indefinitely to cure downstream latency.

### Problem 6 — Circuit recovery storm

**Statement.** 1,000 pods open breakers for exactly 30 seconds, then each sends 10 half-open probes.

**Solution.** At second 30, 10,000 probes can hit a recovering service simultaneously. Jitter open duration, permit one/few probes per pod or coordinate/fleet-limit, ramp traffic, and require success evidence. Preserve normal retry/bulkhead budgets for probes.

**Mistake caught.** Treating half-open as full traffic restoration.

### Problem 7 — Backlog growth

**Statement.** Inference jobs arrive at 2,000/s and workers complete 1,500/s for 45 minutes.

**Solution.** Net `500/s`. Over `45×60=2,700 s`, backlog adds `1,350,000` jobs. If processing stays 1,500/s and arrivals later stop, drain takes 900 seconds (15 minutes). If arrivals continue at 1,000/s, spare drain rate is 500/s and drain takes 2,700 seconds. Apply admission/degradation and scale based on bottleneck.

**Mistake caught.** Saying a queue absorbs unlimited sustained overload.

### Problem 8 — Safe hedge

**Statement.** Read-only metadata has p99 800 ms and median 40 ms across independent replicas; target is 500 ms.

**Solution.** Experiment with a hedge after perhaps measured p95, only for idempotent GETs and when fleet has capacity. Send second replica request, take first, cancel loser, and cap hedge rate. Measure total attempt load and correlated tail. Do not hedge writes or all calls at time zero. The trigger must come from actual latency distribution, not the illustrative numbers.

**Mistake caught.** Doubling all traffic to improve tails during overload.

### Problem 9 — Health-check cascade

**Statement.** Database slows; every API readiness and liveness check queries it. Orchestrator restarts/removes all replicas.

**Solution.** Liveness should check process ability to progress, not every dependency. Readiness may expose path-specific ability with hysteresis, but avoid simultaneous fleet removal. Continue degraded endpoints if safe, shed database-dependent paths, and protect health-check resources. Test dependency failure and restart behavior.

**Mistake caught.** Calling a deep dependency check “more accurate” without feedback analysis.

## 4. REAL-WORLD / APPLIED CONTEXT

**Amazon retry guidance.** Amazon's Builders' Library emphasizes that timeout does not imply no side effect, and recommends timeouts, capped retries, backoff and jitter based on downstream latency/failure behavior. It discusses choosing timeouts from latency percentiles plus network/connection realities. Apply the method to measured service percentiles; do not copy one timeout across services.

**Google cascading failures.** Google's SRE book gives a concrete retry amplification example: three layers each making four attempts can create 64 database attempts. It also shows a service healthy around 10,000 QPS may need load reduced near 1,000 QPS to recover if only 10% of replicas remain. These are case examples illustrating positive feedback, not universal thresholds.

**Payment and ML operations.** A payment request uses an idempotency key and durable status because response loss after commit is ambiguous. A model training submission returns an operation ID and queues durably; retries query/reuse that identity. Both propagate deadlines for synchronous steps, but long training has separate lifecycle, cancellation and reconciliation rather than one HTTP timeout.

Run `failure-drills.md` in a disposable staging stack. Record original logical QPS and attempt QPS separately; otherwise retries can look like organic traffic. `FailurePolicyLab.java` verifies the pure policy arithmetic/state machine.

## 5. COMPARISON TABLE

| Mechanism | Primary purpose | Benefit | Failure/cost | Required companion |
|---|---|---|---|---|
| Timeout | bound one wait | releases caller resources | ambiguous outcome; premature failure | idempotency/status reconciliation |
| Deadline | bound end-to-end usefulness | composes across hops | clock/budget propagation errors | reserves and cancellation |
| Retry | survive transient fault | raises success probability | load amplification/duplicates | classification, idempotency, budget |
| Exponential backoff+jitter | spread retries | recovery time, desynchronization | added latency; attempts remain | deadline/attempt cap |
| Circuit breaker | suppress likely failures | fail fast/protect dependency | false opens, recovery herd | timeout, bulkhead, probe control |
| Bulkhead | isolate resource use | limits blast radius | capacity fragmentation/rejection | fleet-wide sizing |
| Load shedding | preserve useful throughput | avoids queue/meltdown | explicit errors/degraded UX | priority/fairness and client backoff |
| Hedge | reduce tail for safe reads | first-result latency | extra load/cost | delayed trigger, cancellation, cap |
| Queue | temporal decoupling | absorbs finite bursts | backlog/latency/storage | admission, age SLO, idempotency |

| Outcome observed by caller | What is known | Safe next action |
|---|---|---|
| Explicit validation/authorization error | request rejected before effect by contract | fix request; do not retry automatically |
| Explicit committed success | effect acknowledged | return/store result |
| Retryable overload response | server rejected or asks delay per contract | budgeted retry with backoff if safe |
| Timeout/connection loss after send | effect unknown | same idempotency identity + status/reconcile |
| Cancellation | caller no longer waits | do not assume remote rollback |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Timeout means failure.”** It means no response before local bound; side effect may have committed.
2. **Fresh timeout per hop.** Latencies sum beyond the user's deadline; propagate remaining budget.
3. **Socket timeout covers everything.** DNS, pool, connect/TLS and write phases may be outside it.
4. **Retry all errors.** Permanent/auth/validation failures waste capacity and may duplicate effects.
5. **Retry at every layer.** Attempts multiply; four attempts across three layers becomes 64.
6. **Backoff without jitter.** Clients remain synchronized on exponential boundaries.
7. **Unlimited attempts.** Outage turns into sustained retry traffic; cap and budget.
8. **POST retry without idempotency.** Response loss can duplicate charge/job.
9. **Circuit breaker as timeout.** A closed breaker still needs per-attempt deadline; breaker uses aggregate evidence.
10. **Global breaker for unrelated tenants/endpoints.** One fault can deny healthy traffic; scope failure domains deliberately.
11. **Unbounded queues absorb bursts.** Sustained overload becomes memory growth and expired work.
12. **Per-pod bulkhead is global protection.** Autoscaling multiplies total downstream concurrency.
13. **Hedging every request.** Nearly doubles load and worsens overload.
14. **Dependency in liveness check.** Dependency outage can restart the whole fleet and create a cascade.
15. **Queue equals completion.** Async acceptance proves durable enqueue only, not business success.
16. **Three replicas mean independent safety.** Shared zone, release, quota or database can fail all.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Partial failure: timeout cannot distinguish slow, partitioned, crashed or committed-with-lost-response.
- Propagate deadline remaining; cover queue/pool/DNS/connect/TLS/read phases; reserve response time.
- Retry iff transient + safe/idempotent + deadline/budget remains.
- Attempts multiply across layers; centralize retry.
- Capped exponential backoff + jitter + max attempts/time + retry budget.
- Stable idempotency key/fingerprint; timeout after send = unknown, reconcile status.
- Bulkhead active work and queue; fleet capacity = per-instance × replicas × attempts/hedges.
- Little's Law: in-flight ≈ rate × latency in stable conditions.
- Breaker CLOSED→OPEN→limited HALF_OPEN→CLOSED/OPEN; jitter recovery.
- Shed early when work cannot meet deadline; degrade only semantics-safe features.
- Queue absorbs finite burst, not sustained arrival > service; monitor oldest age.
- Liveness is process progress; readiness is traffic eligibility; dependency checks can cascade.
- Observe logical requests and physical attempts separately; inject response loss after commit.

## 8. PRACTICE SET FOR SELF-TEST

1. A 1,200 ms deadline has spent 240 ms in gateway and 310 ms locally; reserve 150 ms. Calculate downstream budget and state when not to start a known 600 ms p50 call.
2. Four layers each make three total attempts. Calculate maximum leaf attempts and redesign retry ownership.
3. Design an idempotency record and API responses for a model-deployment POST whose commit response can be lost.
4. At 700 requests/s, latency rises from 80 ms to 1.5 s. Use Little's Law and propose bulkhead/queue limits conceptually.
5. A dependency returns 429 with `Retry-After: 2`; only 300 ms remains. What should the caller do and why?
6. Design breaker parameters/evidence for a low-volume healthcare dependency with five calls per minute; explain minimum-volume risk.
7. A 10,000-job queue receives 1,200/s and processes 900/s. How long until 100,000 depth, ignoring changes? What metric is more user-relevant?
8. Explain a response-loss injection that proves a timeout is ambiguous without corrupting production.
9. Decide whether to hedge a patient-authorization read and an immutable model-manifest read; justify safety and load.
10. Map at least five shared failure domains for a “three-zone” service using one identity provider, one database and one deployment pipeline.

## 9. CURATED RESOURCES

1. Amazon Builders' Library, [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/). Production reasoning for timeout selection, retry safety, capped backoff and jitter.
2. Amazon Builders' Library, [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/). Durable client identity, semantic equivalence and late-arriving request design.
3. Google SRE Book, [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/). Concrete overload feedback, 64-attempt amplification, shedding and recovery examples.
4. Google SRE Book, [Handling Overload](https://sre.google/sre-book/handling-overload/). Client-side throttling, queue management and overload protections.
5. Google SRE Book, [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/), Dean and Barroso, CACM 2013. Tail amplification and carefully controlled hedged requests in large fan-outs.
6. Fischer, Lynch and Paterson, “Impossibility of Distributed Consensus with One Faulty Process,” JACM 1985. Precise asynchronous consensus impossibility assumptions and safety/liveness distinction.
7. Saltzer, Reed and Clark, “End-to-End Arguments in System Design,” TOCS 1984. Why lower layers cannot fully provide application-level correctness guarantees.
8. Nygard, *Release It!*, 2nd ed., Chapters 4–5. Circuit breaker, bulkhead, stability patterns and production failure narratives.
9. Kleppmann, *Designing Data-Intensive Applications*, Chapters 8–9. Network/process/clock faults, truth, consensus and practical models.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Transactions and Locking.** A local commit can succeed while its response is lost, creating the unknown outcome.
2. **API Design and Security.** Method semantics, idempotency keys, status codes and deadlines are public contracts.
3. **Testing and Resilience.** Deterministic clock/sleeper tests and controlled injection verify policies before chaos.
4. **Redis and Caching.** Cache failure and stampedes are common cascading-failure paths.

### After

1. **Kafka and Eventing.** Queued asynchronous work introduces duplicate delivery, ordering, poison messages and lag.
2. **Consistency and Idempotency.** Replication and cross-service workflows formalize stale reads and deduplicated effects.
3. **Capacity-Driven System Design.** Deadlines, queues, bulkheads and failure-domain capacity become quantitative architecture.
4. **SRE and Observability.** SLOs, burn rates, incidents and load tests operationalize failure behavior.

---ANSWER KEY BELOW---

1. Remaining `1200-240-310-150=500 ms`. A call with 600 ms p50 is unlikely to finish within 500 even before tail/network; reject/degrade or use a faster path rather than start doomed work.
2. `3^4=81` leaf attempts. Let the layer with business idempotency/error knowledge own a bounded retry; other layers propagate result/deadline, and enforce end-to-end retry budget.
3. Unique `(tenant,idempotency_key)`, request fingerprint, operation ID, state (`IN_PROGRESS/SUCCEEDED/FAILED_RETRYABLE/FAILED_FINAL`), result/error reference, timestamps/lease. Same key+fingerprint returns status/result; different fingerprint is 409. Persist operation/outbox atomically; timeout prompts GET/retry same key.
4. In-flight rises from `700×0.08=56` to `700×1.5=1050` under stable arithmetic. Cap dependency concurrency below measured safe fleet capacity, bound queue by useful deadlines, shed/degrade before saturation, and limit retries; load-test since overloaded queues are non-steady-state.
5. Two seconds exceeds 300 ms remaining, so do not retry within this request. Return appropriate overload/deadline response or async option; ignoring Retry-After creates guaranteed-late work.
6. Use a longer rolling time window/minimum sample and perhaps consecutive/failure-rate plus slow-call evidence; five failures could be all traffic but one failure is 20%. Half-open with one probe and jitter; do not infer population health from tiny sample without domain-specific safety posture.
7. Need 90,000 additional jobs at net `1200-900=300/s`, so 300 seconds (5 minutes). Oldest-message age/time-to-start is more user-relevant than raw depth when job costs/priorities vary.
8. In disposable staging, process a keyed operation, commit it, then proxy/drop the response. Client must time out, retry same key/status lookup, receive the one stored resource, and assert one business/outbox row. Record attempt/logical counts.
9. Authorization may be stale and safety-critical; do not hedge unless both replicas provide suitable consistent authority and extra load/security are approved—often fail closed/status-specific. Immutable content-addressed manifest GET is idempotent and safer to hedge after measured tail threshold with capacity/cancellation cap.
10. Examples: zone/host; shared regional database; identity provider; DNS/control plane; account quotas; one release artifact/feature flag; CI/CD pipeline; shared Redis/Kafka cluster; network egress; operator credential. Zones cover hardware domains, not these correlated dependencies.
