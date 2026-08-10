# Capacity-Driven System Design

**Parent:** 04 — Distributed Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the design worksheet

## 1. FOUNDATIONS

System design is the disciplined conversion of product requirements into components, contracts, resource budgets and failure behavior. Boxes come after numbers. “Use Kafka, Redis and microservices” is not a design until it explains why those mechanisms meet a workload, consistency model, latency objective, recovery target, security boundary and cost envelope.

**Demand** is offered work: requests/s, events/s, bytes/s, jobs/hour, active sessions or model inference tokens/s. **Capacity** is useful work the system can complete while satisfying its SLO. **Utilization** is the fraction of a resource capacity currently used. **Headroom** is deliberately unused capacity for growth, variance and failures. A CPU at 50% average may still have one saturated core, a hot tenant or p99 bursts; aggregate average is not a safety proof.

A requirement must be classified. A **functional requirement** describes behavior. A **nonfunctional requirement** constrains quality: latency, availability, durability, consistency, throughput, security, compliance and cost. An **SLI** is a measured indicator; an **SLO** is its target; an **SLA** is an external agreement and consequence. “Low latency” is not actionable. “99% of authorized payment-create requests complete or return durable operation identity within 400 ms over 28 days” is closer, though exclusions and measurement point still need definition.

Capacity planning is continuous because demand, software efficiency and infrastructure change. Google SRE describes resource use as a function of demand, capacity and software efficiency, and requires organic/inorganic forecasts plus regular load tests that correlate raw resources with service capacity. A spreadsheet coefficient becomes stale when code, JVM, payload or dependency behavior changes.

The central quantitative laws are simple:

- Average rate = count / interval.
- Bandwidth = rate × bytes per item.
- Storage = rate × bytes × retention × copies × overhead.
- Little's Law in a stable system: average in-flight `L = arrival rate λ × average time W`.
- Serial availability under independent assumptions ≈ product of component availabilities.
- Backlog growth = max(0, arrival − service) × time.
- Backlog drain rate = service capacity − ongoing arrival.

These equations reveal orders of magnitude; they are not substitutes for measurement. Compression, index amplification, replication, skew, garbage collection, queueing and failure modes need experiments. Every estimate should be labeled product requirement, measured value, forecast, derived number or assumption.

Historically, performance engineering evolved from queueing theory and operations research. Queueing delay rises nonlinearly near saturation. A server at 95% utilization does not merely have 5% spare; variability can make tails explode. Architecture therefore reserves headroom, sheds load and tests beyond the knee where throughput stops scaling and latency/errors accelerate.

## 2. CORE MECHANICS

### 2.1 Clarify the contract

Start an interview with users and operations, not technology. Ask:

- What are create/read/update/list/search/batch operations?
- What is authoritative? Which invariants cannot be violated?
- Who are tenants, regions and actors? What is largest-tenant skew?
- What latency and availability per operation?
- What staleness is acceptable? Must user read own write?
- Retention, deletion, audit, RPO and RTO?
- Payload distributions and growth?
- Security, PHI/financial scope, data residency and abuse?

Resolve contradictions. A request for global linearizable writes under 20 ms and availability in every region during partition conflicts with physics/trade-offs. Explain options instead of silently weakening a requirement.

### 2.2 Traffic estimation

Suppose 86.4 million requests/day. Average is exactly `86,400,000/86,400=1,000 requests/s`. If observed peak-to-average is 4, design initial peak at 4,000/s. Do not invent 4× if product data exists; distinguish daily peak, launch impulse and tenant burst.

Split operations. If 80% reads and 20% writes, peak rough mix is 3,200 reads/s and 800 writes/s only if mix holds at peak. Background jobs, cache refresh, retries, fan-out and internal events add **amplification**. One API request that writes DB, outbox, three indexes and emits three consumers is not one unit of infrastructure work.

Forecast: current peak 4,000/s, 60% year-over-year growth, 20% launch bump gives `4000×1.6×1.2=7,680/s`. Avoid double-counting if launch is already in forecast. Present low/base/high scenarios rather than false precision.

### 2.3 Payload and bandwidth

At 4,000 responses/s × 6 KiB, application egress is 24,000 KiB/s ≈24.6 MB/s decimal before protocol/TLS overhead. Across three internal calls each carrying 6 KiB, network work triples. Model artifacts of 2 GiB do not belong in the same path as 2 KiB metadata; use object storage/CDN/local disk caching and content digests.

Use p50/p95/p99 sizes because a 200 MiB outlier can dominate memory. Bound request/response and decompressed size. Compression trades network/storage for CPU and can expose zip bombs; enforce compressed and expanded limits.

### 2.4 Storage sizing

For 10,000 events/s, 800 observed bytes/event, one day, replication factor 3 and 20% segment/index/headroom factor:

`10000×800×86400×3×1.20 = 2,488,320,000,000 bytes` ≈2.49 TB decimal/day.

For 30 days, naïvely 74.65 TB. Compression may already be in the 800 bytes; do not apply it twice. Add backups, snapshots, cross-region copies, compaction and free-space requirements. Database row payload 500 bytes can occupy much more through tuple/page headers, indexes, WAL and bloat—measure actual bytes per inserted record at representative schema.

Retention is also a recovery guarantee. If consumers need seven days to restore/replay, five-day retention is invalid regardless of disk savings. In regulated systems, longer retention increases privacy exposure; minimize event fields and separate audit requirements.

### 2.5 CPU and replica sizing

Load test one replica with production-like data/concurrency until its SLO boundary. If it sustains 500 RPS but p99 begins violating at 380, safe capacity might be 350 RPS after variance. At 4,000 peak and 25% growth headroom, normal replicas `ceil(4000×1.25/350)=15`.

For three equal zones that must survive losing one without adding capacity, remaining two zones must carry the load. A simple N+1-zone factor is `3/2`, yielding `ceil(15×1.5)=23` total replicas, distributed 8/8/7. After losing an 8-replica zone, 15 remain, matching normal requirement. `CapacityLab` verifies 23. But zone loss may also move database/cache traffic and cold-start capacity; test the complete failure mode.

CPU/request is useful: if measured 8 ms CPU per request, 4,000/s requires 32 CPU-seconds/s = 32 fully utilized cores before headroom and unevenness. Garbage collection/native overhead and blocking do not disappear. A service can be dependency-limited before CPU.

### 2.6 Memory and concurrency

Little's Law: 500 RPS at 200 ms mean latency has ~100 requests in flight. If each holds 256 KiB of request/response/intermediate data, that's ~25 MiB payload working set, excluding objects, thread stacks, caches and runtime. At 2 seconds, ~1,000 in flight and ~250 MiB. Tail requests can hold more.

Bound active concurrency and queues. Queue capacity should correspond to useful waiting time, not maximum RAM. If service capacity 500/s and you allow 100 queued, idealized extra queue wait can approach 200 ms; variability/priority change this. Reject before deadline is impossible. Virtual threads reduce thread cost, not downstream connections or per-request payload memory.

Connection pool sizing follows database capacity and transaction latency, not replica thread count. Twenty pods × 50 connections = 1,000 DB sessions. If database safely handles 300 active queries, pools merely create contention. Use per-pod allocation, transaction shortness and a pool-wait budget.

### 2.7 Queue and worker sizing

Arrival 2,000 jobs/s and processing 1,500/s grows backlog 500/s: 1.8 million/hour. To drain that backlog while arrivals continue at 1,000/s and capacity is 1,500/s, spare is 500/s, so drain is one hour. `CapacityLab` tests it.

For recovery objective, if four hours at 2,000/s creates 28.8 million backlog and must drain in two hours while 2,000/s continues, extra 4,000/s is needed, total 6,000/s. Partitions, hot keys, database and third-party quotas must all sustain it. Scaling consumers from lag can overload sinks; cap against the bottleneck.

Monitor oldest age and predicted time-to-drain, not only count. GPU jobs vary minutes/hours; weight by estimated service demand and accelerator type. Admission should include quotas and cost budgets so one tenant cannot monopolize accelerators.

### 2.8 Cache capacity

If 20,000 reads/s and 95% hit ratio, source sees 1,000/s. Cache failure exposes up to 20,000/s plus retries—20× normal source load. Either provision source for cache-down, limit fallback, serve acceptable stale data or shed. A cache that is required for capacity is a hard dependency even if data is reconstructible.

Working-set sizing uses object overhead and popularity trace. 10 million items × 1 KiB is 10.24 GB payload, not actual Redis RSS. Add keys, metadata, allocator, replication/persistence buffers and headroom from measurements. Hot key remains one-shard bottleneck.

### 2.9 Database design capacity

Estimate reads/writes, transactions/s, rows changed, index amplification, WAL, active connections and working set. A payment write may insert payment, idempotency, history and outbox plus update account and five indexes. At 800 logical writes/s, perhaps thousands of row/index changes/s.

Partition for lifecycle/query alignment, not arbitrary scale. Read replicas scale stale/consistent-read-compatible traffic, not writes or transactions requiring primary freshness. Sharding raises write capacity but adds routing, hot shard, rebalancing and cross-shard transaction complexity. Delay sharding until measured single-cluster limits and growth justify it; design tenant/aggregate keys so future partitioning is possible.

### 2.10 Availability arithmetic

If request requires independent services A and B each available 99.9%, serial path availability approximates `0.999²=0.998001` = 99.8001%. Independence is often false because they share zone/network/deployments. Adding dependencies can lower end-to-end availability even if each is “three nines.”

Redundancy availability is not simply addition. For two independent 99.9% replicas where either suffices, failure probability both down is `0.001²=0.000001`, availability 99.9999%, but only if load balancer, state consistency, capacity and failure domains work. Correlated software/config failures dominate. Use fault trees and game days.

Translate nines into allowed bad time only as intuition. 99.9% over 30 days allows about 43.2 minutes; 99.99% about 4.32 minutes. SLO is typically request-based and windowed, not literal downtime, so compute from defined indicator.

### 2.11 RPO, RTO and regional recovery

**RPO** is maximum acceptable data loss measured in time/state. **RTO** is maximum restoration time. Replication is not backup: corruption/deletion can replicate. Backup is not high availability: restore may take hours. Specify both plus restore verification.

Multi-zone handles local infrastructure; multi-region addresses regional disaster and latency/residency but adds replication lag/consistency and failover authority. If asynchronous replica lag is 30 seconds, advertised RPO 0 is false. If 80 TB restore throughput is 2 GB/s, raw transfer alone is ~40,000 seconds (~11.1 hours), excluding provisioning/replay/validation; an RTO of one hour needs another design.

Failover capacity must be warm and tested. Active-active writes need conflict/consensus semantics. Active-passive requires DNS/routing, credentials, data catch-up and regular drills. Define failback too.

### 2.12 Latency budgets and fan-out

Allocate a 500 ms deadline: edge/auth 40, service queue/compute 60, DB 120, dependency 180, serialization/network reserve 100, for example. Parallel calls take roughly max latency; serial calls sum. A fan-out to 100 shards makes overall tail depend on slowest; even if each independently meets 99th percentile, probability all 100 are under their individual p99 is `0.99^100≈36.6%`. Independence is simplistic, but shows tail amplification.

Reduce fan-out, batch, precompute, use bounded parallelism and partial/degraded results where safe. Hedging can help idempotent reads with capacity, but increases load. Propagate deadlines and cancel useless work.

### 2.13 Load balancing and skew

Round robin assumes equal request cost and healthy capacity. Google SRE notes expensive requests can consume 1,000× the CPU of cheap ones in some services. Least-loaded decisions use stale distributed observations and can herd clients. Power-of-two-choices often balances well with low coordination, but validate.

Partition skew can make average utilization misleading. If one Kafka partition has 25% traffic among 20 partitions, its consumer bottlenecks while aggregate capacity appears idle. Tenant quotas, better keys, subpartitioning semantics and work-cost-aware scheduling address skew.

### 2.14 Overload behavior

Find the **knee** with load testing: throughput rises until bottleneck, then latency/queue/errors increase. A resilient service rejects excess cheaply while useful throughput remains near maximum. A fragile one spends resources on doomed work, fails health checks, loses replicas and decreases useful throughput.

Use admission control, bounded queues, concurrency bulkheads, retry budgets, circuit breaking and graceful degradation. Recovery capacity differs from steady state because caches are cold and replicas missing. Google SRE's cascading-failure chapter shows why load may need dramatic reduction before recovery.

Prioritize correctness. Drop optional recommendations before payment authorization. For healthcare eligibility, do not serve unsafe stale authorization as “degraded.” Return explicit unavailable/pending or route to authority.

### 2.15 Cost model

Break cost into compute instance-hours, accelerator-hours, database I/O/storage/backup, Kafka storage/network, Redis memory, object operations/egress, observability ingest/retention and people/operational complexity. Egress across regions can dominate. GPU utilization can be low from queue fragmentation/model loading.

Calculate unit economics: cost per 1,000 requests, training run, model deployment or tenant-month. Include redundancy and peak headroom, not average-only cost. A managed service may cost more per raw unit but less operational risk. Present trade-offs: stronger consistency adds cross-region latency; longer retention adds storage/privacy; prewarming adds cost but improves failover.

### 2.16 Load-testing method

Use production-like data distribution, payload sizes, endpoints, TLS, dependencies or controlled stubs, cache state and concurrency. Test:

- steady ramp to find knee;
- sudden impulse;
- sustained peak/soak;
- hot tenant/key;
- cache cold/down;
- one zone/replica/dependency failure;
- retry storm and backlog catch-up.

Record throughput, successful useful throughput, p50/p95/p99, errors/shed/degraded, CPU throttling, heap/RSS/GC, connection/pool waits, DB plans/locks/WAL, network/disk, queue age and cost. State hardware/container, versions, dataset, run duration/repetitions and confidence. Client generator must not be bottleneck; use coordinated-omission-aware tooling when measuring latency under fixed arrival rates.

### 2.17 A repeatable interview sequence

1. Clarify functional/invariant/nonfunctional scope.
2. Estimate peak rates, sizes, retention and growth with labels.
3. Define APIs/events/data model and authoritative boundaries.
4. Draw critical read/write paths.
5. Size compute, storage, bandwidth, connections and queues.
6. Explain consistency, idempotency and failure behavior.
7. Add caching/partitioning only for identified bottlenecks.
8. Design availability, RPO/RTO, overload and security.
9. State observability, load tests and unknowns.
10. Revisit the hardest trade-off and evolution path.

Communicate estimates as a model, not prophecy. Interviewers value detecting an impossible requirement or hidden bottleneck more than multiplying many invented numbers.

## 3. WORKED PROBLEMS

### Problem 1 — Peak traffic

**Statement.** 86.4 million requests/day, observed peak/average 4, 80/20 read/write.

**Solution.** Average 1,000/s, peak 4,000/s. If mix holds at peak: 3,200 reads/s, 800 writes/s. Add retry/fan-out/background amplification separately. Validate peak duration and largest tenant.

**Mistake caught.** Dividing by 24 rather than 86,400 seconds or presenting assumed mix as measured.

### Problem 2 — Replica count with zone loss

**Statement.** Peak 4,000/s; 25% growth; safe replica 350/s; three zones must survive one loss.

**Solution.** Normal `ceil(4000×1.25/350)=ceil(14.286)=15`. To retain 15 after one of three zones, total `ceil(15×3/2)=23`, placed 8/8/7. Losing a zone with eight leaves 15. Check DB/cache/dependency capacity too.

**Mistake caught.** Deploying 15 total and losing one-third during zone failure.

### Problem 3 — In-flight memory

**Statement.** 2,000 RPS, 250 ms mean, 400 KiB retained/request.

**Solution.** Little's Law gives `2000×0.25=500` in flight. Payload working set `500×400 KiB=200,000 KiB≈195.3 MiB`, before object overhead, buffers, stacks, caches and runtime. At 2 s degradation it becomes 4,000 requests and ~1.53 GiB payload, likely exceeding a 1 GiB pod.

**Mistake caught.** Sizing memory from request rate without latency.

### Problem 4 — Source after cache loss

**Statement.** 20,000 reads/s, 95% cache hits, database safe at 2,500 reads/s.

**Solution.** Normal misses 1,000/s. Cache-down demand 20,000/s, 8× DB safe capacity. Limit fallback to ≤2,500 minus other workload/headroom, serve governed stale data or shed; stagger warmup and single-flight. The cache is a capacity dependency.

**Mistake caught.** Calling cache optional because source is authoritative.

### Problem 5 — Queue drain

**Statement.** Backlog 1.8 million; workers 1,500/s; ongoing arrivals 1,000/s.

**Solution.** Spare 500/s; drain `1,800,000/500=3,600 s` = one hour. If arrivals rise to 1,500/s, drain is infinite; above it backlog grows. Retention/deadlines and downstream capacity must permit catch-up.

**Mistake caught.** Dividing backlog by total service rate.

### Problem 6 — Serial availability

**Statement.** API requires two independent 99.9% services.

**Solution.** Approximate `0.999×0.999=0.998001`, or 99.8001%. To meet 99.9 end-to-end, improve components, remove hard serial dependency, use safe degradation or redundancy. Independence assumption likely overstates real availability if shared failures exist.

**Mistake caught.** Taking minimum 99.9% as path availability.

### Problem 7 — Restore objective

**Statement.** Restore 80 TB at sustained 2 GB/s; RTO one hour.

**Solution.** Decimal arithmetic `80,000 GB/2 GB/s=40,000 s≈11.1 h`, before validation/replay. One-hour RTO is impossible by bulk restore. Need warm replica/snapshot parallelism/incremental architecture and tested failover, or renegotiate RTO.

**Mistake caught.** Equating backup existence with one-hour recovery.

### Problem 8 — Fan-out tail

**Statement.** Request fans to 100 independent shards; each is under threshold 99% of time.

**Solution.** Probability all under threshold `0.99^100≈0.366`. About 63.4% have at least one slow shard under simplistic independence. Reduce fan-out, query only necessary shards, preaggregate, tolerate partial response, or use careful hedging/cancellation.

**Mistake caught.** Assigning leaf p99 directly to aggregate request p99.

### Problem 9 — Kafka storage

**Statement.** 10,000/s, 800 bytes, one day, RF3, 20% overhead.

**Solution.** 2,488,320,000,000 bytes ≈2.49 TB decimal. For seven days ~17.42 TB before extra free-space/backups. Confirm whether bytes are compressed and topic retention is per partition.

**Mistake caught.** Omitting replicas or retention seconds.

## 4. REAL-WORLD / APPLIED CONTEXT

**Google SRE capacity planning.** Google states capacity planning must include organic/inorganic demand forecasts and regular load tests mapping raw resources to service capacity. Its intent-based planning example captures requirements such as regional demand and N+2 redundancy rather than hardcoding “50 cores.” This supports maintaining equations/constraints, not static host counts.

**Overload/cascades.** Google SRE documents that overload increases latency and in-flight requests, consuming threads, RAM and backend capacity; failed replicas shift load and can snowball. The target overload curve keeps useful throughput while shedding excess instead of collapsing. Test until failure and beyond, including impulse and cache-cold cases.

**AI platform sizing.** Metadata API and training plane need separate models. Metadata might be 4,000 RPS on CPU pods; training arrival 100/hour with 2 GPU-hours mean implies 200 GPU-hours/hour average = 200 continuously occupied GPUs before peaks/fragmentation. Queue admission, accelerator types, checkpoint/retry and tenant quotas dominate; scaling API pods does not create GPUs.

The supplied calculator verifies exact example outputs for traffic, replicas, storage, serial availability, Little's Law and queue drain. It is deterministic arithmetic, not a load-test replacement. The worksheet forces every number's evidence category.

## 5. COMPARISON TABLE

| Scaling method | Helps | Does not solve | Main cost |
|---|---|---|---|
| Vertical scale | single-node CPU/RAM/IO ceiling | node/region failure, unlimited growth | larger blast/cost step |
| Stateless horizontal replicas | request CPU/availability | shared DB/hot key/state | coordination/load balancing |
| Read replicas | eligible read throughput/locality | writes, freshness-required reads | lag/failover/cost |
| Sharding | write/storage scale | cross-shard tx, hot shard | routing/rebalance/operations |
| Cache | repeated read latency/source load | authoritative correctness, miss storm | invalidation/memory/dependency |
| Queue | finite burst/async decoupling | sustained arrival > service | backlog/latency/replay |
| CDN/object store | public/immutable large content | dynamic authorization/state | invalidation/egress |

| Resilience capacity | Provisioning idea | Benefit | Risk |
|---|---|---|---|
| N+0 | exactly normal load | cheapest | any failure sheds/violates SLO |
| N+1 replica | one instance spare | simple small failure | insufficient for zone/shared loss |
| zone-failure headroom | survivors carry full demand | zonal resilience | idle cost/cold dependencies |
| active-passive region | warm/standby second region | disaster recovery | drift/untested failover/cost |
| active-active | both carry normal traffic | utilization/latency | consistency/conflict/global dependency |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Drawing before requirements.** Technology boxes cannot repair unknown invariants/SLOs.
2. **Average QPS as capacity.** Peaks, bursts, skew, retries and failures determine demand.
3. **Unlabeled invented numbers.** State assumption versus measurement/product target.
4. **Payload bytes equal storage.** Indexes, replication, WAL, backups, overhead/headroom matter.
5. **Using benchmark maximum per replica.** Safe capacity is at SLO boundary with variance/headroom.
6. **Normal replica count as resilient count.** Zone failure removes capacity when traffic is hardest.
7. **Virtual threads solve downstream capacity.** Connections, CPU and remote concurrency remain finite.
8. **Unbounded queue as resilience.** It converts overload to latency/memory and expired work.
9. **Drain rate equals worker capacity.** Subtract ongoing arrival.
10. **Cache is optional because source exists.** Cache-down amplification may exceed source by 20×.
11. **Read replicas scale every read.** Fresh/transactional reads may still require authority.
12. **Multi-region equals zero RPO/RTO.** Replication lag, authority and failover time must be measured.
13. **Backup equals HA.** Restore time/data loss differ from serving failover.
14. **Multiply independent availability blindly.** Shared deployments/quota/network correlate failures.
15. **Leaf p99 equals fan-out p99.** Slowest-of-many amplifies tail.
16. **Autoscale consumers on lag without sink limits.** It can overload database/provider.
17. **Load test only a warm steady ramp.** Cold/impulse/failure/soak reveal different boundaries.
18. **Cost only compute.** Data transfer, observability, replicas, storage and operations can dominate.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Clarify operations, invariants, SLO/consistency, tenants/regions, retention/RPO/RTO/security.
- Label each number: measured, requirement, forecast, derived, assumption.
- Average QPS = daily/86,400; peak = measured peak factor; add growth and amplification separately.
- Bandwidth = rate×bytes; storage = rate×bytes×seconds×copies×overhead.
- Little: in-flight = rate×latency (stable average).
- Normal replicas = ceil(forecast peak / safe SLO-boundary capacity).
- Three equal zones surviving one: normal×3/2, then validate placement/dependencies.
- Backlog growth = arrival−service; drain = backlog/(service−ongoing arrival).
- Cache-down source load, not normal miss load, defines failure protection.
- Serial availability roughly product only under independence; use fault domains/tests.
- RPO=data loss, RTO=restore time; replication≠backup; backup≠HA.
- Fan-out tail depends on slowest; `P(all fast)=p^n` under simplifying independence.
- Find overload knee; bound queues/concurrency/retries; shed/degrade before collapse.
- Report load-test environment, versions, data, cache, concurrency, duration/repetitions and tails.

## 8. PRACTICE SET FOR SELF-TEST

1. Calculate average and 6× peak QPS for 172.8 million requests/day; split 70/30 reads/writes.
2. Peak 12,000/s, 40% two-year growth, safe replica 600/s, three zones survive one. Calculate normal and total replicas.
3. At 8,000/s and 150 ms mean with 96 KiB/request, estimate in-flight and payload working set.
4. Size 30-day storage for 2,500 writes/s, 1.5 KiB observed record, RF3, 25% overhead.
5. Cache hit 98% at 50,000 reads/s; source safe at 4,000/s. Quantify normal/cache-down and choose controls.
6. Backlog 24 million, capacity 8,000/s, arrival 5,000/s. Calculate drain and effect if arrival rises to 8,500/s.
7. Three serial independent dependencies are each 99.95%. Approximate path availability and explain correlation caveat.
8. A 120 TB restore at 4 GB/s has a 4-hour RTO. Is raw transfer sufficient? Add missing recovery stages.
9. Design a capacity model for 240 training jobs/day averaging 3 GPU-hours with 5× six-hour peak.
10. Outline a load test that proves useful throughput remains stable beyond saturation and during one-zone loss.

## 9. CURATED RESOURCES

1. Google SRE Book, [Introduction](https://sre.google/sre-book/introduction/). Capacity planning mandate: forecasts, provisioning and regular load-test correlation.
2. Google SRE Book, [Software Engineering in SRE](https://sre.google/sre-book/software-engineering-in-sre/), Auxon case study. Intent-based capacity constraints, dependencies and performance coefficients.
3. Google SRE Book, [Handling Overload](https://sre.google/sre-book/handling-overload/). Admission, client throttling, queues and overload protections.
4. Google SRE Book, [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/). Test-to-failure method, retry amplification, cold recovery and useful-throughput collapse.
5. Google SRE Book, [Load Balancing in the Datacenter](https://sre.google/sre-book/load-balancing-datacenter/). Skew, request cost variation and distributed load-balancing algorithms.
6. Dean and Barroso, “The Tail at Scale,” CACM 2013. Quantitative fan-out tail and latency mitigation in large services.
7. Gunther, *Analyzing Computer System Performance with Perl::PDQ*, chapters on queueing and scalability. Operational queueing models and utilization/response relationships.
8. Gregg, *Systems Performance*, 2nd ed., Chapters 2–5. USE method, workload characterization, latency distributions and experimental discipline.
9. Jain, *The Art of Computer Systems Performance Analysis*, Chapters 3–5 and 19–24. Measurement, statistical comparison, experimental design and queueing foundations.
10. Barroso, Clidaras and Hölzle, *The Datacenter as a Computer*, 3rd ed. Fleet-level efficiency, tail, power and warehouse-scale architecture.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Failure Semantics.** Retries, deadlines, queues and overload define failure-amplified demand.
2. **Kafka and Eventing.** Event rate, partition throughput, retention and lag provide concrete capacity equations.
3. **Consistency and Idempotency.** Quorums, replication and dedupe add latency/storage/capacity costs.
4. **Indexes and Query Plans.** Per-request database work and safe throughput depend on access paths.

### After

1. **Azure Compute and Networking.** Quantitative requirements map to regions, zones, load balancers and service limits.
2. **Kubernetes.** Requests/limits, autoscaling, disruptions and scheduling implement replica capacity.
3. **SRE and SLOs.** Capacity signals, error budgets and overload runbooks maintain the design.
4. **MLOps Architecture.** GPU queues, artifact bandwidth and online inference need separate quantitative planes.

---ANSWER KEY BELOW---

1. Average `172,800,000/86,400=2,000/s`; 6× peak 12,000/s. If peak mix holds: 8,400 reads/s and 3,600 writes/s. Label mix assumption.
2. Forecast peak `12000×1.4=16,800/s`; normal `ceil(16800/600)=28`. Three-zone one-loss total `ceil(28×3/2)=42`, ideally 14/zone, leaving 28. Include dependency/cold-start headroom.
3. In-flight `8000×0.15=1,200`. Payload `1,200×96 KiB=115,200 KiB=112.5 MiB`, excluding runtime/caches/buffers and tail growth.
4. Bytes `2500×1536×2,592,000×3×1.25 = 37,324,800,000,000`, about 37.32 TB decimal (33.95 TiB), plus free space/backups and verified compression interpretation.
5. Normal misses 2%=1,000/s. Cache down 50,000/s, 12.5× source safe. Bound fallback below safe headroom, single-flight, acceptable stale serving, shed/rate-limit and staged warmup; test outage.
6. Spare `8000-5000=3000/s`; drain `24,000,000/3000=8,000 s` ≈2 h 13 m 20 s. At arrival 8,500, backlog grows 500/s and never drains without more capacity/shedding.
7. `0.9995^3≈0.99850075`, about 99.8501%. Shared zone, deploy, identity/network and load mean independence likely overstates; map fault tree and measured incident overlap.
8. Raw decimal transfer `120,000/4=30,000 s≈8.33 h`, already over four hours. Add provisioning, parallelism limits, decrypt/decompress, log replay, indexes, validation, DNS/traffic and application warmup; require warm replica/other design or change RTO.
9. Average 240/day=10 jobs/hour; demand 30 GPU-hours/hour = 30 occupied GPUs average. If 5× arrival for six hours and same durations, roughly 150-GPU concurrency demand during peak before variability/checkpoint/failures. Model job duration/GPU type distribution, queue wait SLO, fragmentation, quotas and headroom; simulate rather than assume fluid jobs.
10. Production-like fixed-arrival generator, dataset/payload/skew/TLS/dependencies; ramp through knee then impulse/soak, record successful throughput vs offered, p50/p95/p99, shed/errors, CPU/RSS/GC/pools/DB/cache. Remove a zone at peak, ensure survivors plus admission retain useful throughput; cold-cache/retry behavior and recovery are measured with explicit abort gates.
