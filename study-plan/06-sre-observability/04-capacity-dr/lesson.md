# Capacity Engineering and Disaster Recovery

**Parent:** 06 — SRE and Observability  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the executable capacity/recovery lab

## 1. FOUNDATIONS

**Capacity** is the useful workload a system can handle while meeting correctness, latency and reliability requirements. It is not CPU count. A service processing 5,000 requests/s with 20% errors has not delivered 5,000 requests/s of useful capacity. **Capacity planning** translates a workload model and failure scenarios into resources, quotas, limits, scaling and operational actions.

**Performance** describes behavior under a workload; **scalability** describes how behavior changes as workload/resources grow; **elasticity** is the ability to adjust resources with demand; **resilience** is the ability to continue acceptable service under faults; **recoverability** is the ability to restore service/data after disruption. Adding replicas can improve capacity and instance resilience while doing nothing for a corrupt database or regional control-plane outage.

**High availability (HA)** uses redundancy and failover to tolerate expected component/zone faults with limited interruption. **Disaster recovery (DR)** restores critical flows after a disruption beyond normal HA assumptions, often using another region and explicit procedures. **Business continuity** covers how the organization continues essential operations, including people, vendors, manual processes and communication—not only infrastructure.

A **Recovery Point Objective (RPO)** is the maximum acceptable amount of data loss expressed as time before the disaster. If disaster occurs 10:30:00 and the newest durable recoverable point is 10:29:30, achieved RPO is 30 seconds. A **Recovery Time Objective (RTO)** is maximum acceptable downtime until the defined business flow is verified. A 45-minute infrastructure deployment is not a 45-minute achieved RTO if DNS, data consistency, identity, backlog and user validation take another hour.

**MTTR** is an observed statistic whose R may mean restore, repair, recover or resolve; define it. RTO/RPO are objectives, not measured performance and not vendor SLA. **Maximum tolerable downtime (MTD)** is the business limit beyond which harm becomes unacceptable; RTO should leave margin inside it. **Backup** is an independent recoverable copy; **replication** copies changes for availability and can rapidly copy corruption/deletion/ransomware. Neither proves recovery until restored and validated.

Capacity engineering exists because average load is a dangerous planning input. Traffic varies by second, hour, campaign, payroll cycle and retry behavior. Failures reduce available capacity precisely when retries and backlog increase demand. Autoscaling reacts after measurement/provisioning warm-up and cannot rescue hard quota, IP, connection, partition, storage or downstream bottlenecks. DR capacity may be cold and unavailable during a regional emergency when many customers request quota simultaneously.

Without quantified models and drills, teams discover during failure that the remaining two zones cannot carry peak, database connection caps prevent replica scale, a Kafka backlog never drains because processing equals arrival, backups cannot be decrypted, or failback overwrites newer records. The correct artifacts are equations, assumptions, measured limits, dependency maps, tested procedures and evidence.

## 2. CORE MECHANICS

### 2.1 Build a workload model

Identify critical user flows and units: requests/s, transactions/s, events/s, bytes/s, concurrent sessions, jobs/hour, GPU-hours, stored objects and egress. Separate logical work from attempts/retries. Characterize average, percentiles, peak duration, burstiness, seasonality, daily/weekly growth, payload distribution and tenant skew.

For 43,200,000 requests/day, average is `43,200,000/86,400=500 requests/s`. With a measured 6× peak-to-average ratio, forecast peak is 3,000 requests/s. Calling 6× “measured” requires data period and known events; future product growth remains forecast/assumption. Model low/base/high and shock scenarios rather than a single false-precision number.

Use concurrency from Little's Law in stable systems: `L = λW`. At 3,000 requests/s and 200 ms average time in system, average in-flight requests are `3,000×0.2=600`. Tail latency and burst correlations need additional headroom; Little's Law does not size percentile concurrency by itself.

### 2.2 Measure safe per-unit capacity

Load test a production-like instance with representative data, dependencies, TLS, logging and resource limits. Increase offered load until one SLO or correctness limit breaches. Observe useful throughput, latency distribution, error/shed rate, CPU throttling, memory/GC, pools, queue age, network and downstream saturation. The maximum raw throughput is not safe capacity.

If one pod meets SLO at 250 useful requests/s but latency becomes unstable above that, use 250 as measured safe rate under the named environment. With 30% operational headroom, effective planning capacity is `250×0.70=175`. Peak 3,000 then requires `ceil(3000/175)=18` healthy pods. Headroom is not a substitute for explicit zone-loss and growth scenarios.

### 2.3 Find the bottleneck and scaling boundary

Every resource has a limit: CPU, memory, GC, locks, thread pools, database connections/IOPS, Kafka partitions, storage throughput, NIC/SNAT ports, API quota, model server GPU memory, downstream TPS and human operations. Increasing frontends can worsen a database bottleneck. Map capacity as a dependency graph and calculate each fan-out.

At 3,000 logical RPS, if each request averages 2.4 database queries plus 0.2 retries, DB sees 7,800 query attempts/s. If a replica holds a 40-connection pool, 18 pods can open 720 connections; a database capped at 500 will fail even before traffic. Budget shared connection pool and use backpressure, not unlimited connections.

### 2.4 Headroom and N+failure provisioning

Headroom absorbs forecast error, bursts, deployment overlap, noisy neighbors and recovery. State why 20%, 30% or 50% is chosen. For a three-zone service that needs 18 healthy pods after one zone loss and balances evenly, each remaining zone must host `ceil(18/2)=9`; provision total 27 (9 per zone). Merely running 18 as six per zone leaves 12 after loss, only two-thirds required.

This is reserved/schedulable capacity, not necessarily always active depending on platform. Verify node groups, pod topology, disruption budgets, quotas, IPs and downstream capacity allow rescheduling. If autoscaling new nodes takes 8 minutes but SLO permits seconds, capacity must already exist or service must degrade/shed safely.

### 2.5 Horizontal, vertical and partition scaling

Horizontal scale adds instances and improves fault isolation for stateless parallel work, but adds coordination, connections and cost. Vertical scale increases CPU/memory/IO on fewer instances and helps single-process/stateful limits, but has SKU ceilings, restart/migration and larger blast radius. Partitioning/sharding distributes data/work by key; it increases maximum scale and isolation but introduces routing, skew, rebalancing and cross-partition operations.

A hot tenant receiving 35% of traffic can overload one hash partition even when fleet average is 50%. Measure maximum partition/tenant/key, use sufficient partitions and consider key splitting/admission. Kafka consumer scale is capped by assigned partitions for one group; 100 consumers on 24 partitions leave most idle.

### 2.6 Autoscaling mechanics

Autoscaling is a delayed feedback controller. Metrics need observation time; controller decides; cloud provisions; application starts/warms; load balances. Scale on a signal causally related to demand and early enough: queue age/depth and arrival/service rates for workers, concurrency or RPS per pod for stateless API, GPU queue for inference. CPU can be poor when blocked on IO; average CPU can hide saturated pods.

Define min/max, scale-up aggressiveness, stabilization/cooldown, warm-up readiness and quotas. Avoid oscillation: rapidly adding/removing replicas destroys caches and connections. Test from min to shock peak. Never autoscale into a constrained database without admission/backpressure. Scheduled scaling can pre-warm known peaks; predictive scaling inherits forecast error.

### 2.7 Overload and graceful degradation

When offered load exceeds safe capacity, unbounded queues turn overload into high latency, timeouts, retries and collapse. Enforce admission limits before expensive work, bounded queues/deadlines, tenant fairness, concurrency controls, retry budgets, load shedding and degraded modes. Return explicit `429/503` with retry guidance rather than accepting work that cannot finish.

Prioritize critical healthcare/payment operations over analytics or batch. Degraded response is good only if its semantics are safe and disclosed; stale authorization/incorrect model output cannot be traded for availability. Track useful throughput and shed results separately. Overload tests should confirm the service plateaus safely rather than falls off a cliff.

### 2.8 Queue and backlog recovery

A queue has arrival rate `λ`, service rate `μ` and backlog `B`. It drains only if `μ>λ`; approximate drain time is `B/(μ−λ)`, not `B/μ`, because new work continues. For 3,600,000 events, ongoing 2,000/s and service 5,000/s, spare capacity is 3,000/s and drain is 1,200 s = 20 minutes.

Validate sinks tolerate catch-up. Running consumers at maximum can overwhelm database/APIs and recreate failure. Use rate limits and tenant fairness, measure oldest-event age, poison records, retries and actual useful rate. If `μ≤λ`, scale/change work/admit less; waiting cannot drain.

### 2.9 Storage and network capacity

Estimate retained data as rate × average encoded bytes × retention × replication × overhead, then add indexes, compaction, fragmentation and growth. At 12,000 events/s, 1,200 bytes, 7 days, replication 3 and factor 1.20, lab computes 31,352,832,000,000 bytes ≈31.35 TB decimal (≈28.52 TiB). The factor is a planning assumption; measure compression/on-disk representation.

Bandwidth at 3,000 RPS × 48 KiB p99 is not an average; a simultaneous p99 payload scenario is ~147.5 MiB/s before protocol/response/replication. Model typical and correlated high cases. Include cross-zone/region replication and egress cost. Check load balancer/NAT ports, DNS rate, private endpoint IP, subnet and quota capacity.

### 2.10 Growth, quotas and cost

Forecast with transparent math. At 8% monthly compound growth, six-month factor is `1.08^6≈1.587`, not 48% exactly. Forecast demand, unit efficiency improvements, feature changes and tenant concentration. Establish trigger lead time for database resize, repartition or quota requests; some capacity cannot be provisioned instantly.

Track limits in code/inventory and alert on consumption plus growth time-to-exhaustion. Cloud quota is often regional and SKU-specific; deployed capacity, quota and market availability differ. Reserve/commit only after balancing cost and flexibility. DR replicas, backups, egress, logging and drills have cost but an untested paper DR plan has little reliability value.

### 2.11 Failure mode analysis

For each critical flow, enumerate component/process, node, zone, region, identity, DNS, network, quota, data corruption, operator, supply-chain and vendor failures. Record effect, detection, prevention, mitigation, recovery, dependencies, likelihood/impact and test. Common-mode failures defeat redundancy: both regions sharing one identity tenant, DNS zone, CI pipeline, encryption key, schema change or human runbook.

Map blast radius. Three replicas in one zone are not zone HA. Two regions under one bad global configuration can fail simultaneously. Complexity itself adds failure modes, so invest according to business criticality.

### 2.12 RPO and data protection

Derive RPO per data flow. Accepted payment identity might require RPO 0; reproducible analytics may tolerate hours. Synchronous cross-region replication can reduce acknowledged-write loss but increases latency and may reduce availability under partition. Asynchronous replication permits lag/loss bounded by observed replication and recovery point.

Use backups with encryption, access isolation, immutability/soft delete where warranted, catalog, retention and restore tooling. A backup job success proves copy creation, not restorability, keys, dependency consistency or application correctness. Test point-in-time restore into isolated environment and reconcile counts/checksums/business invariants.

Coordinate multiple stores. Restoring database to 10:29 and object/event store to 10:31 can violate references. Use durable operation/outbox IDs, replay/idempotency and documented consistency points. RPO is not simply backup interval: a 15-minute backup may take 20 minutes and newest valid copy can be older; replication lag and corruption detection delay matter.

### 2.13 RTO and recovery sequence

Break RTO into detection/decision, access/coordination, infrastructure, data restore/promotion, application/config, DNS/traffic, backlog/reconciliation and verification. If target is 60 minutes, a serial plan consuming exactly 60 minutes has zero margin. Parallelize independent work but respect dependencies.

Define disaster declaration threshold and authority. Recovery sequence often: establish incident command; prevent further corruption; validate secondary/backup; enable identity/network/DNS; promote/restore authoritative data; deploy immutable app/config; run synthetics/invariants; shift canary traffic; expand; drain/reconcile; communicate. Automate safely and retain manual override.

### 2.14 DR topologies

**Backup/restore (cold)** has lowest steady cost and longest RTO. **Pilot light** keeps core data/minimal services ready, scaling compute during disaster. **Warm standby** runs reduced capacity in secondary and scales/receives traffic. **Active-active** serves from multiple regions, offering low failover but highest data consistency, routing, operational and cost complexity.

Choose per critical flow, not brand prestige. Active-active with a single-region database is not active-active end to end. Warm standby must have proven scale/quota and current artifacts/config/secrets. Cold restore must include infrastructure/control plane, not only database bytes.

### 2.15 Failover and split brain

Failover decides the primary writer. During network partition, two regions accepting conflicting writes can create split brain. Use consensus/single-writer leases with fencing, globally partitioned ownership, conflict resolution with domain semantics, or deliberately stop writes. DNS failover has TTL/cache/health-check delay and is not transaction coordination.

Avoid automatic regional failover based on one noisy probe. Require multi-signal health and safeguards against flapping/cascading to an undersized secondary. Test client DNS behavior, pinned endpoints, certificates, private DNS, identity and dependencies. Track which writes were acknowledged and reconcile after recovery.

### 2.16 Failback

Failback is a new risky migration, not “reverse DNS.” Primary may be stale after secondary served writes. Rebuild/synchronize, validate data and capacity, re-establish replication direction, shift canary traffic, observe, then restore normal topology. Prevent old primary from writing until fenced. Define rollback of failback.

Do not rush failback during ongoing provider instability. Temporary DR state has cost/risk and needs explicit owner/expiry, but stability and data correctness dominate convenience.

### 2.17 DR testing and evidence

Tabletops validate decisions/roles but not systems. Component restore tests validate artifacts. Partial failover/game days exercise automation. Full production-like regional drills validate end-to-end RPO/RTO and unknown dependencies with bounded risk. Use isolated data, change controls and abort criteria.

Record disaster time, last durable recoverable point, declaration, each phase, first technical availability, first verified critical-flow success, achieved RPO/RTO, data reconciliation, traffic level, failures/manual steps and corrective actions. A DR test that quietly changes the objective after missing it is a failed test with useful learning.

### 2.18 Security, privacy and operational boundaries

Backups are concentrated sensitive data. Encrypt, isolate identity/network/account, require least privilege/MFA/JIT, log access, test key recovery and protect deletion. DR must not bypass tenant isolation, audit, secrets rotation, WAF or privacy controls. Break-glass access is time-limited, monitored and reviewed.

Use masked/synthetic data in exercises where possible. If production data is restored to isolated test, retain equivalent controls and delete it verifiably. Cross-region storage may face data-residency rules; involve legal/security. Reliability replicas increase attack surface and patch/config drift; include them in normal security operations.

## 3. WORKED PROBLEMS

### Problem 1 — Peak forecast

**Statement.** 43.2 million requests/day and measured 6× peak-to-average. Compute average and forecast peak.

**Solution.** Average `43,200,000/86,400=500 RPS`; peak `500×6=3,000 RPS`. State period/method for 6× and add future growth separately.

**Mistake caught:** dividing by working hours or treating average as peak.

### Problem 2 — Headroom replicas

**Statement.** One pod safely delivers 250 RPS and policy reserves 30% headroom. Size for 3,000 RPS.

**Solution.** Planned per-pod capacity `250×0.7=175 RPS`; `ceil(3000/175)=ceil(17.143)=18` healthy pods. Confirm downstream capacity and load-test environment.

**Mistake caught:** adding 30% replicas (`ceil(12×1.3)=16`) is not identical to retaining 30% unused capacity.

### Problem 3 — One-zone loss

**Statement.** Three balanced zones must retain 18 healthy pods after one zone fails. How many total?

**Solution.** Remaining two zones need nine each, so provision nine per zone =27. Test scheduler/node/IP/quota/downstream. Eighteen total leaves only 12.

**Mistake caught:** assuming autoscaling arrives before impact.

### Problem 4 — Database connection boundary

**Statement.** 18 pods each configure pool max 40; DB max connections 500 with 80 reserved. Is it safe?

**Solution.** Application could request 720, while usable DB allowance is 420. Unsafe. Set coordinated global budget, e.g. ≤23 per pod gives 414, but deployments/zone scale/other clients require further margin; use pooler/admission and measure wait/throughput.

**Mistake caught:** sizing each pool independently.

### Problem 5 — Backlog drain

**Statement.** Backlog 3.6 million; arrivals continue 2,000/s; processing can safely reach 5,000/s. Drain time?

**Solution.** Net drain 3,000/s; `3,600,000/3,000=1,200 s=20 min`. Using 5,000 gives wrong 12 minutes. Verify sink at catch-up rate.

**Mistake caught:** ignoring continued arrivals.

### Problem 6 — Retained event storage

**Statement.** 12k events/s, 1,200 bytes, seven days, RF3, 20% factor. Estimate.

**Solution.** `12,000×1,200×604,800×3×1.2=31,352,832,000,000 bytes`, 31.35 TB decimal or ≈28.52 TiB. Add indexes and measured compression/segment behavior; factor must be justified.

**Mistake caught:** omitting replication or confusing TB/TiB.

### Problem 7 — Achieved RPO/RTO

**Statement.** Last validated durable transaction 10:29:30; disaster 10:30:00; service critical flow verified 11:15:00. Compute.

**Solution.** Achieved RPO 30 seconds; achieved RTO 45 minutes. If traffic opened at 11:05 but correctness verified at 11:15, user-flow RTO remains 45 minutes under this definition.

**Mistake caught:** measuring RTO from failover start or infrastructure readiness.

### Problem 8 — Backup versus replication

**Statement.** Synchronous replicas receive an accidental table delete. Are they DR backups?

**Solution.** No; replication correctly copies deletion. Use point-in-time/immutable isolated backups, deletion protection, least privilege and tested restore. Replicas help hardware/zone availability, while backups/replay recover logical corruption. Detection delay determines needed retention.

**Mistake caught:** treating replicas as historical recovery.

### Problem 9 — Failback correctness

**Statement.** Secondary served writes for six hours; recovered primary is immediately made writer via DNS.

**Solution.** This risks data loss/split brain. Fence primary, synchronize/rebuild from authoritative secondary, verify counts/checksums/business invariants and replication, canary traffic, then controlled writer transition with rollback. DNS alone cannot establish write ownership.

**Mistake caught:** treating failback as routing-only.

## 4. REAL-WORLD / APPLIED CONTEXT

Microsoft's current Azure reliability guidance distinguishes RPO (acceptable data-loss duration) and RTO (acceptable downtime) per critical flow and warns that zero objectives are difficult/costly. It also states untested recovery targets should not be treated as guaranteed and that platform guarantees exist only for some products.

Azure availability zones provide separate failure domains within a region for supported services, but service/SKU/region behavior differs. A workload only gains zone resilience when compute, data, network, dependencies, placement and capacity all survive the loss; checking one “zone redundant” box is insufficient.

The included standard-library lab verifies exact scenarios: 43.2M/day ×6 =3,000 peak RPS; 18 healthy replicas with 30% headroom; 27 balanced replicas for one-of-three-zone loss; 20-minute backlog drain; 31.352832 TB decimal retained data; achieved RPO 30 seconds and RTO 2,700 seconds. Six unit tests pass, including rejection when recovery/service arithmetic is impossible. They validate formulas, not Azure service limits or benchmark results.

## 5. COMPARISON TABLE

| DR pattern | Secondary state | Typical relative cost | RTO/RPO tendency | Main complexity |
|---|---|---:|---|---|
| Backup/restore | artifacts/data copies, no running app | 1× baseline + storage | longest / backup-point | restore dependencies, quota, keys |
| Pilot light | core data/minimal control running | low–medium | hours–tens min / replication | scale-up and config drift |
| Warm standby | reduced-capacity full stack | medium–high | minutes / replication | proven scaling and routing |
| Active-active | multiple regions serving | highest | lowest potential | consistency, split brain, common mode |

| Scaling | Strength | Boundary | Use |
|---|---|---|---|
| Horizontal | fault isolation/parallel stateless work | shared DB, coordination, partitions | API/workers |
| Vertical | simple, helps single-node state/memory | SKU ceiling/restart/blast radius | DB/JVM/GPU fit |
| Partition | distributed state/throughput/isolation | skew/rebalancing/cross-shard ops | Kafka/data/tenant scale |
| Shed/degrade | protects useful throughput under excess | product fairness/semantics | overload safety, not growth replacement |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **CPU count equals capacity.** Useful throughput under SLO/correctness defines capacity.
2. **Average load sizes production.** Model peaks, bursts, skew, growth and failures.
3. **Benchmark maximum is safe rate.** Use SLO boundary and headroom in named environment.
4. **Headroom covers zone loss.** Model failure capacity separately.
5. **Autoscaling is instant.** Observe/controller/provision/warm delays require reserve/degradation.
6. **Scale frontend fixes everything.** Shared DB/quota/connection limit may worsen.
7. **Per-pod pools are independent.** Sum against global downstream limits including rollout/failure.
8. **More consumers than Kafka partitions increases group throughput.** Active parallelism is partition-limited.
9. **Queue depth alone.** Need age, arrival, service and net drain.
10. **Drain time is backlog/service.** Subtract continuing arrivals.
11. **Unlimited queue preserves work.** It converts overload to timeout/resource collapse.
12. **Retries are free capacity.** They amplify attempts; enforce retry budget/deadlines/jitter.
13. **TB equals TiB.** State decimal/binary units.
14. **Replication factor omitted from storage.** Retained physical estimate multiplies it plus overhead.
15. **Quota equals available capacity.** Regional SKU stock/provision success can differ.
16. **Three replicas means zone-resilient.** Placement and remaining capacity/dependencies matter.
17. **HA equals DR.** HA handles expected local faults; DR restores beyond that boundary.
18. **Replication equals backup.** It copies logical corruption; keep isolated historical recovery.
19. **Backup success equals restore success.** Test keys, dependency consistency and application invariants.
20. **RPO equals backup interval.** Completion, lag, detection and valid recovery point determine it.
21. **RTO ends when VMs start.** End at verified critical business flow under definition.
22. **Vendor SLA proves workload RTO.** End-to-end dependencies/procedures are yours.
23. **Active-active automatically best.** It adds consistency, security, cost and operational failure modes.
24. **DNS prevents split brain.** It routes cached clients; writer fencing/consensus controls authority.
25. **Failback is reverse failover.** Primary is stale; resynchronize/fence/canary.
26. **Tabletop proves recovery.** It tests decisions, not data/tool/runtime execution.
27. **DR may bypass security.** Secondary needs equivalent identity, audit, network and privacy controls.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Average RPS = daily/86,400; peak = average × measured/forecast factor.
- Healthy replicas = `ceil(peak / (safe_per_replica × (1−headroom)))`.
- Balanced one-zone-loss total = `zones × ceil(required_healthy/(zones−1))`.
- Little: concurrency = arrival rate × time in system (stable averages).
- Backlog drain = `B/(service−arrival)` only when service > arrival.
- Storage = rate × bytes/event × retention seconds × replication × overhead.
- Useful throughput and SLO define capacity; map every shared dependency/quota.
- HA tolerates expected faults; DR restores after wider disruption; continuity includes people/process.
- RPO = disaster time − newest valid durable recoverable point.
- RTO = verified critical-flow recovery time − disaster time (per agreed definition).
- Backup ≠ replication; restore/test encryption, consistency and business invariants.
- Failover/failback require one writer/fencing, data synchronization and canary verification.

## 8. PRACTICE SET FOR SELF-TEST

1. Compute average/peak for 86.4M requests/day at 4.5× and six-month peak after 8% monthly compound growth.
2. Size healthy and three-zone one-loss replicas for 6,000 RPS, 400 safe RPS/pod and 25% headroom.
3. At 4,000 RPS, 1.8 DB calls/logical request and 0.15 retry attempts/request, calculate DB attempt rate and pool budget for max 800 with 120 reserved.
4. Compute drain time for 9M backlog, 3,500/s arrival and 6,500/s safe service; explain what happens at 3,000/s service.
5. Estimate 14-day physical storage for 8,000 2-KiB events/s, RF3 and 1.35 overhead in TB and TiB.
6. Build a capacity failure matrix for API, PostgreSQL, Kafka, NAT, subnet IP, Key Vault and on-call staff.
7. Allocate a 45-minute RTO across detection, decision, infrastructure, data, app/DNS and verification with 20% reserve.
8. Design RPO 0 for accepted payment IDs but RPO 15 minutes for analytics, including consistency/replay controls.
9. Compare cold, pilot-light, warm and active-active Azure designs for a healthcare API with 60-minute RTO/5-minute RPO.
10. Write a regional failover and failback drill with exact evidence proving achieved RPO/RTO and no tenant/data corruption.

## 9. CURATED RESOURCES

1. Microsoft Learn, [Business Continuity, High Availability, and Disaster Recovery](https://learn.microsoft.com/en-us/azure/reliability/concept-business-continuity-high-availability-disaster-recovery). Current Azure definitions and shared-responsibility framing.
2. Azure Well-Architected Framework, [Define reliability targets](https://learn.microsoft.com/en-us/azure/well-architected/reliability/metrics). Flow-level SLO/RTO/RPO/MTTR and testability requirements.
3. Azure Well-Architected Framework, *Develop a multi-region disaster recovery plan*. Criticality, thresholds, recovery-aware design, data consistency, roles and exercises.
4. Azure Well-Architected Framework, *Reliability design principles* and *Reliability checklist*. Failure modes, redundancy, scaling, self-preservation and operations.
5. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 21, “Handling Overload,” and Chapter 22, “Addressing Cascading Failures.” Load shedding, queueing, retries and collapse behavior.
6. Betsy Beyer et al., *Site Reliability Engineering*, Chapter 18, “Software Engineering in SRE,” capacity planning section, and Chapter 20, “Load Balancing in the Datacenter.” Forecasting/provisioning and distribution mechanics.
7. John Little, “A Proof for the Queuing Formula: L=λW” (Operations Research, 1961). Canonical stable-system concurrency relationship.
8. Martin Kleppmann, *Designing Data-Intensive Applications*, Chapters 5 and 9. Replication/partition/consistency trade-offs required for regional recovery.
9. NIST SP 800-34 Rev. 1, *Contingency Planning Guide for Federal Information Systems*. Business impact analysis, recovery strategy, testing and plan maintenance; adapt current organizational requirements.
10. PostgreSQL official documentation, *Continuous Archiving and Point-in-Time Recovery*. Concrete WAL/base-backup recovery mechanics for a common backend.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Capacity-Driven Design:** supplies bottleneck, Little's Law and queueing foundations.
2. **SLIs/SLOs/Error Budgets:** defines acceptable useful capacity and recovery outcomes.
3. **Metrics/Logs/Traces:** measures demand, saturation, backlog and achieved recovery.
4. **Incident Response:** declares disasters, coordinates recovery and verifies closure.

### After

1. **Python and MLOps:** GPU, data pipeline, artifact registry and model serving need capacity/DR.
2. **ML Monitoring:** model freshness/quality recovery extends infrastructure RPO/RTO.
3. **Regulated System Design:** business impact, immutable backups, residency and continuity become controls.
4. **System Design Interviews:** numeric capacity/failure calculations turn diagrams into defensible designs.

---ANSWER KEY BELOW---

1. Average `86.4M/86,400=1,000 RPS`; current peak 4,500. Six-month factor `1.08^6≈1.586874`; forecast peak ≈7,140.93 RPS, rounded according to planning units/headroom separately—not 7,140 replicas.
2. Planned pod capacity `400×.75=300`; healthy `ceil(6000/300)=20`. For three zones after one loss: `3×ceil(20/2)=30`, ten per zone, subject to node/IP/downstream/quota evidence.
3. Attempts per logical request `1.8+0.15=1.95` if retry number is additional DB attempts as stated; DB attempts 7,800/s. Usable connections `800−120=680`; allocate across normal plus rollout/zone-loss pod maximum, not only current 18. If 30 possible pods and 20% reserve on usable, per-pod max could be `floor(544/30)=18`, then load-test queue/useful throughput.
4. Net drain 3,000/s; `9,000,000/3,000=3,000 s=50 min`. At service 3,000 < arrival 3,500, backlog grows 500/s and never drains.
5. KiB=2,048 bytes; seconds=1,209,600. Bytes `8,000×2,048×1,209,600×3×1.35=80,261,361,561,600`, ≈80.261 TB decimal, ≈73.0 TiB. Add indexes/compaction and measured compression; state whether factor already includes them.
6. Matrix rows name limit/current/forecast/failure effect/detection/mitigation/test: API useful RPS and pods; PostgreSQL TPS/connections/IOPS/storage; Kafka partitions/broker disk/lag; NAT SNAT ports/throughput; subnet usable IPs during rollout/zone loss; Key Vault request quota/private DNS/identity; staff concurrent incidents/page load/handoff. Map shared dependencies and lead time.
7. Forty-five minutes with 20% reserve leaves 36 planned minutes and 9 reserve. Example: detect 3, decide/declare 3, infrastructure/identity/network 8, data promote/verify 8, app/DNS/canary 7, business-flow/reconciliation verification 7 =36. Parallelize where safe and measure from disaster, not declaration.
8. Accepted payment identity commits synchronously to quorum/durable multi-zone log before acknowledgment, uses idempotency/outbox and cross-region zero-loss strategy whose partition availability trade-off is explicit; reconcile immutable ledger. Analytics checkpoints/objects every ≤15 min, replay from durable event log, validate watermark/count/checksum. Separate recovery points and prevent analytics restore from becoming payment authority.
9. Cold backup can meet 60 min only if full restore drills (infra/data/DNS/identity) prove it; likely risky. Pilot light may fit with automated scale and ≤5-min data replication. Warm standby more confidently fits but costs running stack/capacity. Active-active provides low RTO but introduces cross-region correctness/tenant routing and highest cost. Choose pilot/warm based measured phase budget; verify Azure region/SKU/quota and regulated data residency.
10. Record controlled disaster timestamp and authoritative last durable ID/time; fence primary; declare; run documented secondary identity/network/DNS/data/app sequence; verify tenant auth, counts/checksums/idempotency and user SLO under target load; record verified time and compute RPO/RTO. Serve new writes, then failback by fencing stale primary, rebuilding/syncing from secondary, validating, reversing replication, canarying and shifting traffic. Capture every phase/manual step, abort condition, data diff and corrective action.
