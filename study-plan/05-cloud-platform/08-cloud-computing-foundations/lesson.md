# Cloud Computing Foundations from Scratch

Parent subject: `05-cloud-platform`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### What cloud computing solves

Traditional infrastructure requires forecasting demand, buying hardware, waiting for delivery, installing it, operating facilities, and carrying spare capacity for peaks and failures. Cloud computing provides network-accessible pools of configurable compute, storage, networking, databases, and higher-level services that can be provisioned quickly and measured as usage.

NIST's widely used definition identifies five essential characteristics: on-demand self-service, broad network access, resource pooling, rapid elasticity, and measured service. Cloud is not simply “someone else's computer.” The differentiators are programmatic control planes, shared resource pools, service abstractions, elastic allocation, and consumption/accounting models.

Cloud grew from virtualization, utility computing, distributed systems, large-scale data centers, and web APIs. Virtual machines isolate workloads on shared hosts; infrastructure APIs make capacity programmable; managed services shift operational responsibilities to providers. The benefits come with dependency on provider regions/control planes, service limits, variable cost, identity configuration, and shared-responsibility boundaries.

### Control plane and data plane

The **control plane** creates/configures resources: provision VM, change firewall, assign identity, update deployment. The **data plane** serves workload traffic or data operations: process HTTP request, read object, execute SQL. A control-plane outage may prevent new scaling/configuration while existing data-plane resources continue. Design and incident response should distinguish them.

Infrastructure desired state is eventually reconciled. An API returning “accepted” may start an asynchronous operation; resource readiness requires polling/events and idempotent orchestration. Control-plane calls need their own retry and rate-limit policy, separate from application data-path calls.

### Service models: IaaS, PaaS, SaaS, and serverless

**Infrastructure as a Service (IaaS)** exposes virtual compute, networks, disks, and related primitives. Customer manages operating system, runtime, application, data, and much security configuration.

**Platform as a Service (PaaS)** manages more of the OS/runtime/scaling/deployment substrate. Customer manages application, data, identities/config, and service-specific behavior.

**Software as a Service (SaaS)** delivers a complete application; customer manages users, configuration, data governance, integrations, and endpoints.

**Serverless** describes services where customers do not provision servers directly, commonly event-driven functions or managed runtimes with per-use scaling. Servers still exist. Cold starts, concurrency quotas, execution limits, network setup, state, observability, and cost per invocation remain. “No server management” is a responsibility shift, not absence of operations.

### Deployment models

Public cloud offers provider-owned shared infrastructure. Private cloud provides cloud-like operation for one organization. Hybrid connects on-premises/private and public environments. Multi-cloud uses multiple providers. Hybrid/multi-cloud can satisfy latency, sovereignty, acquisitions, or risk requirements, but adds identity, networking, skills, tooling, consistency, data movement, and support complexity. Avoid it as a slogan.

### Regions, availability zones, and fault domains

A **region** is a provider geographic area containing multiple isolated locations/services. An **availability zone** is a provider-defined fault-isolated location within a region with independent power/networking to a documented degree. Terminology and service topology vary. A fault domain is the actual correlated-failure boundary—host, rack, zone, region, software deployment, identity provider, or shared dependency.

Deploying three replicas in one zone protects process/host failures, not zone loss. Deploying across zones protects more physical failures, but a shared database, DNS, certificate, deployment, quota, or code defect can still fail all. Multi-region adds larger latency, replication/consistency, failover, data residency, and cost decisions.

### Compute

Virtual machines offer OS control and stable instances. VM sizes combine vCPU, memory, storage/network limits, architecture, GPU, and price. Containers package processes but still run on compute nodes or managed container substrates. Functions run bounded event handlers with platform scaling. Batch services schedule finite jobs; GPU services expose accelerators.

**Vertical scaling** increases one instance size. It is simple but bounded and may require restart. **Horizontal scaling** adds instances and requires stateless/request distribution or partitioned state. Autoscaling observes a metric and changes desired capacity; delays mean it cannot instantly handle sharp peaks. Keep warm headroom, queue/admit work, and choose predictive/scheduled scaling when justified.

### Storage

**Object storage** stores immutable/mutable objects addressed by key in buckets/containers; it scales broadly and supports metadata/lifecycle, but is not a POSIX filesystem. **Block storage** exposes volumes to hosts, suited to filesystems/databases with attachment/performance semantics. **File storage** exposes shared hierarchical files via network protocols.

Performance dimensions include capacity, IOPS, throughput, latency, request size, concurrency, and durability/availability. A disk advertising 3,000 IOPS at 16 KiB requests provides at most about 46.875 MiB/s from that IOPS limit (`3000×16KiB`), even if throughput limit is higher. At 1 MiB requests, throughput limit likely dominates. Provision from workload shape.

Durability probability concerns data loss; availability concerns access. “Eleven nines durability” is not eleven nines availability and does not replace backup/versioning. Accidental deletion, credential compromise, application corruption, retention configuration, and region loss need separate controls.

### Databases and managed data services

Managed relational databases automate infrastructure, patching options, backups, monitoring, and replication to documented degrees. Customer still owns schema, queries/indexes, connection pools, roles, encryption choices, retention, recovery testing, versions, and capacity. NoSQL services trade data models and consistency for scale/latency patterns. Caches are derived accelerators, not source of truth unless deliberately designed.

Choose a service from invariants and access patterns, not “managed is always better.” Managed constraints can limit extensions, superuser access, filesystem control, cross-region behavior, or upgrades; self-management increases operational burden.

### Identity and shared responsibility

Cloud access is governed by identities, credentials/tokens, roles/policies, resource hierarchy, and audit. Human administrators use federated identity and just-in-time elevation; workloads use managed/workload identities rather than embedded long-lived secrets. Least privilege limits actions, resources, conditions, and duration.

Under **shared responsibility**, the provider secures the cloud infrastructure and managed service layers it controls; the customer secures configuration, identities, data, application, and remaining stack. Boundary changes by service model. Provider encryption capability does not ensure your public bucket is private, your keys are rotated, or your application authorization is correct.

### Elasticity, quotas, and capacity

Elasticity is the ability to acquire/release resources with demand. It is not infinite. Every service has quotas, regional SKU capacity, rate limits, provisioning delay, and dependency limits. Autoscaling an API from 20 to 100 replicas can overwhelm a database connection limit, exhaust IP addresses, or hit image-pull registry limits.

Capacity is end-to-end: compute, connections, partitions, storage IOPS, network, downstream quotas, and people/operations. Load testing must include scaling transitions and failure conditions.

### Cost model

Cloud cost includes compute time, storage capacity and operations, managed service tiers, data transfer, public IP/NAT/gateways, logs/metrics, backups, support, licenses, and engineering. Egress can dominate data-intensive systems. Unit economics expresses cost per useful outcome: per 1,000 claims, training run, tenant, or million tokens.

Reserved/committed pricing reduces predictable base cost in exchange for commitment. Spot/preemptible compute discounts interruptible capacity, suitable for checkpointable batch, not single-replica critical state. Rightsizing means selecting resources from measured utilization and performance, not simply reducing size.

## 2. CORE MECHANICS

### 2.1 Map responsibility by service

For a VM-hosted PostgreSQL database, provider manages facility/physical host/hypervisor; customer manages guest OS patches, PostgreSQL install/config/backup/HA, firewall, identities, schema, and data. For managed PostgreSQL, provider manages OS/database binaries and automated HA/backup features per SLA; customer still configures network, roles, parameters, schema, queries, pool, retention/PITR, and restore verification.

Create a RACI-like table for every critical component. “Managed by cloud” without exact documentation creates gaps.

### 2.2 Availability arithmetic

Availability target 99.9% permits about 43.83 minutes downtime in a 30.4375-day average month (`43830 min × .001`). 99.99% permits about 4.383 minutes; 99.999% about 26.3 seconds.

For independent serial dependencies each 99.9%, combined availability is `.999^3≈99.7003%`, about 2.19 hours/month unavailable. Independence is optimistic, and end-to-end SLO may define errors differently. Adding services usually reduces availability unless redundancy/degradation changes the path.

Two active replicas each independently available 99% with successful service when either works yield `1-(.01)^2=99.99%` under ideal failover and independence. Shared load balancer/database/deployment invalidates that simple model.

### 2.3 Size compute from throughput

Peak 12,000 requests/s; one instance safely handles 800 at target latency. Minimum for peak is 15. To tolerate one zone loss when three zones carry equal capacity and retain target, each two-zone remainder must handle all traffic: total provisioned needs `15×3/2=22.5`, round/layout to 24 (8/zone). Then add autoscaling transition and imbalance headroom. Measure safe capacity under representative dependency latency.

### 2.4 Autoscaling signals

CPU scaling works for CPU-bound stateless requests, but a service blocked on DB can have low CPU while queues grow. Better signals include concurrency per instance, queue age, request latency, or custom work metric. Scaling on lag needs service-rate math and cooldown. Protect downstream with maximum replicas, connection budgets, and admission.

Suppose each replica pool max is 8 and DB budget is 240. Scaling beyond 30 replicas can exceed budget. Configure pool/scale coordination or a proxy, not independent defaults.

### 2.5 Choose storage by access

- Millions of model artifacts read by key and distributed: object storage, versioning/checksums/lifecycle.
- PostgreSQL data directory needing low-latency random writes: durable block storage according to service architecture.
- Shared legacy application expecting directory/file locking: managed file storage after semantic/performance testing.
- Container ephemeral scratch: local/ephemeral disk, with no durability assumption.

Do not mount object storage and assume POSIX rename/locking/consistency semantics. Adapt the application or choose a filesystem service.

### 2.6 Estimate monthly data and cost units

At 20,000 events/s, average 1 KiB/event: `20,000×86,400≈1.728 billion events/day`, about 1.648 TiB/day using binary bytes, before replication/index/compression. Thirty days ≈49.44 TiB raw. With replication factor 3, physical payload alone ≈148.3 TiB before overhead.

Cost model:

```text
monthly = compute_hours×rate
        + storage_GB_month×rate
        + request_count×request_rate
        + egress_GB×rate
        + observability + backup + support
```

Use current provider calculators for actual rates; the equation exposes drivers and sensitivity. Prices are region/time-specific and must not be memorized as timeless facts.

### 2.7 Design backup and recovery

Define RPO/RTO per data. Enable versioning/soft delete where useful, but keep independent recovery controls. For a database with RPO 5 minutes, continuous log/PITR is needed; for RTO 30 minutes, rehearse restore and connection cutover at production scale. Cross-region backup protects regional loss but creates residency/key/access questions.

Backup encryption key loss makes backup unusable. Test identity, keys, DNS, application configuration, and data—not only bytes.

### 2.8 Select region(s)

Consider user latency, data residency, service/SKU availability, quotas, price, carbon/organizational policy, network to dependencies, and disaster correlation. A fintech ledger may use one primary region with zonal synchronous HA and a governed cross-region recovery copy rather than active-active writes, preserving invariant simplicity. A static artifact CDN can be globally active more easily.

### 2.9 Apply tags/labels and ownership

Every resource should identify service, environment, owner, cost center, data classification, criticality, and lifecycle where supported. Tags are mutable metadata, not access control by themselves unless policies explicitly and safely use them. Enforce through IaC/policy and inventory orphaned resources.

### 2.10 Avoid cloud lock-in slogans

Portability has layers: source language, container format, orchestration API, data format, operational behavior, identity, networking, managed database features, observability, and staff skill. Abstract only where an evidence-based alternative/future move justifies ongoing cost. Using lowest-common-denominator services can sacrifice reliability and speed while still retaining data/network lock-in.

## 3. WORKED PROBLEMS

### Problem 1 — Service model (easy)

Classify VM, managed web runtime, and hosted email application.

**Solution.** IaaS, PaaS, SaaS respectively. Boundaries vary, so list actual managed layers rather than rely only on label.

**Trap:** saying SaaS means customer has no security responsibility.

### Problem 2 — Downtime budget (easy)

Monthly allowance for 99.95% over 30 days?

**Solution.** 43,200 minutes ×0.0005=21.6 minutes.

**Trap:** subtracting percentage incorrectly.

### Problem 3 — Storage throughput (easy)

2,000 IOPS with 32 KiB requests gives what IOPS-limited throughput?

**Solution.** 64,000 KiB/s = 62.5 MiB/s, before other caps/overhead.

**Trap:** equating IOPS with bytes/s without request size.

### Problem 4 — Zone failure capacity (medium)

Three zones, 6 instances each, safe 500 rps/instance, traffic 7,000 rps. Survive one zone?

**Solution.** After failure 12×500=6,000, below 7,000. Normal capacity 9,000 is irrelevant. Need at least 14 surviving instances; with equal zones, at least 7/zone (21 total) gives exactly 7,000 and needs further headroom.

**Trap:** using normal 22% headroom as proof.

### Problem 5 — Connection amplification (medium)

Autoscaler max 80 replicas, pool 10, DB safe 300. Risk?

**Solution.** Configured demand 800, 2.67× budget. Coordinate max replicas/pool, use global proxy/admission, reserve admin/migrations, and load test. Pool min connections can create storms during scale-out.

**Trap:** assuming pools open only when harmless.

### Problem 6 — Object durability (medium)

Provider advertises extremely high object durability. Can backups be omitted?

**Solution.** No. Durability protects against provider media loss under stated scope, not authorized deletion, ransomware credentials, application overwrite/corruption, retention mistakes, or account loss. Use versioning/immutability/separate-account copies and tested recovery per threat model.

**Trap:** conflating durability, availability, and recoverability.

### Problem 7 — Serial dependency availability (hard)

API path requires three independent 99.95% services. Approximate combined.

**Solution.** `.9995^3≈.99850075` = 99.8501%, roughly 64.8 minutes downtime in 30 days. Actual errors and correlated failures require measurement.

**Trap:** claiming path remains 99.95%.

### Problem 8 — Spot GPU training (hard)

Use discounted interruptible GPUs for a 20-hour training job?

**Solution.** Yes only if checkpoint/resume is reliable and frequent, dataset/artifacts durable, interruption notices handled, capacity fallback exists, and expected lost work plus engineer delay remains economical. A non-checkpointable 20-hour run may repeatedly lose all progress.

**Trap:** comparing hourly rates only.

### Problem 9 — Multi-cloud resilience (hard)

Does deploying identical services to two clouds guarantee availability?

**Solution.** No. Shared code, CI, identity, DNS, data replication/conflict, secrets, operators, dependencies, and traffic control can fail both. It adds coordination complexity and may reduce reliability unless independently engineered and regularly exercised.

**Trap:** treating provider diversity as automatic fault independence.

## 4. REAL-WORLD / APPLIED CONTEXT

### Azure regions and availability zones

Azure resources can be zonal or zone-redundant depending on service/region. A VM architecture may place instances across zones behind a load balancer; a managed database may provide zone-redundant HA under specific tiers. Verify current regional service support, SLA, maintenance, failover, and data-path behavior in official docs.

### Cloud object storage

Azure Blob Storage, Amazon S3, and Google Cloud Storage store objects with versioning/lifecycle/replication options. They support huge namespace and throughput but charge across capacity, operations, retrieval tiers, and transfer. Model artifacts should include immutable versions and cryptographic checksums; mutable “latest” pointers should not be the only identity.

### Serverless inference/API

Functions can handle bursty lightweight preprocessing or webhook work, scaling toward zero. Large models, GPU residency, long inference, predictable low latency, or sustained load often suit provisioned/managed serving. Cost crossover depends on duration, memory, concurrency, cold start, and platform quotas.

## 5. COMPARISON TABLE

| Option | Control | Scaling | Billing | Best fit | Main cost |
|---|---|---|---|---|---|
| VM/IaaS | High OS control | Manual/autoscale groups | Provisioned time | Custom runtime/stateful legacy | Patching/operations |
| Managed app/PaaS | App-level | Platform-supported | Instance/use tier | Standard web/API | Platform constraints |
| Containers/Kubernetes | Portable process/orchestration control | Pod+node scaling | Nodes/control plane/services | Multi-service platform | Operational complexity |
| Functions | Handler-level | Event/concurrency | Invocation/duration | Bursty bounded event work | Cold starts/limits/per-use cost |
| Object storage | Object API | Massive namespace | GB+operations+transfer | Artifacts, backups, media | Non-POSIX semantics |
| Block storage | Volume blocks | Resize/tier-dependent | GB+IOPS/throughput | DB/filesystem volumes | Attachment/zone constraints |
| Managed database | Schema/query control | Tier/read replicas | Provisioned/serverless units | Transactional data | Service constraints/cost |
| Self-managed DB | Full | Engineer-built | VM/storage + labor | Special control/extensions | HA, backup, patch burden |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Cloud is unlimited capacity.** Quotas, SKU scarcity, rate limits, and provisioning delay exist.
2. **Serverless has no servers/operations.** Responsibility shifts; limits and behavior remain.
3. **Three replicas equal zone resilience.** Placement/fault domains decide.
4. **Managed means provider owns everything.** Customer owns data, identity, config, queries, and recovery validation.
5. **Autoscaling solves overload instantly.** Signal/provision/warm delays require headroom/admission.
6. **Object storage is a filesystem.** Semantics and performance differ.
7. **Durability equals availability and backup.** They address different outcomes.
8. **Average utilization proves rightsizing.** Peaks, tail latency, failures, and per-resource bottlenecks matter.
9. **Multi-cloud removes lock-in/risk.** It adds data, identity, tooling, and operational coupling.
10. **Cloud price is compute hourly rate.** Transfer, operations, logs, backup, support, and labor matter.
11. **Adding dependencies preserves SLA.** Serial availability multiplies downward.
12. **Source commit identifies deployed bytes.** Artifact digest/provenance is required.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Cloud: on-demand, network access, pooling, elasticity, measured service.
- Control plane configures; data plane serves work.
- IaaS→PaaS→SaaS shifts more layers to provider; customer responsibility remains.
- Region contains provider-defined zones; map actual fault domains.
- Horizontal scale needs distributed/stateless/partitioned design.
- Autoscaling has delay and downstream limits.
- Object vs block vs file storage have different semantics.
- Durability ≠ availability ≠ backup/recovery.
- Monthly downtime = period × (1−availability).
- Serial independent availability multiplies; redundancy requires independent paths/failover.
- Capacity must survive planned failure and peak.
- Cost = compute + storage + operations + transfer + observability + backup + support/labor.

## 8. PRACTICE SET FOR SELF-TEST

1. List NIST's five cloud characteristics.
2. Map customer/provider responsibility for OS patching on VM versus managed database.
3. Compute 99.99% monthly downtime for a 30-day month.
4. Calculate IOPS-limited throughput for 5,000 operations/s at 8 KiB.
5. Peak requires 18 instances; three equal zones must tolerate one loss. Minimum evenly divisible total before extra headroom?
6. Calculate raw daily volume at 10,000 events/s and 2 KiB/event.
7. Explain control-plane versus data-plane outage behavior.
8. Choose storage for model artifact, DB volume, and shared POSIX directory.
9. Explain why scaling replicas can crash the database.
10. Name six non-compute cloud cost drivers.

## 9. CURATED RESOURCES

- Peter Mell and Timothy Grance, NIST SP 800-145, “The NIST Definition of Cloud Computing” — primary characteristics, service models, and deployment models.
- Microsoft Azure Well-Architected Framework, pillars and “Shared responsibility in the cloud” — official reliability, security, cost, operations, and performance guidance for the target Azure background.
- Microsoft Azure Architecture Center, “Compute decision tree,” “Data storage technology choices,” and “Availability zones and regions” — exact Azure service-selection and topology considerations.
- Thomas Erl, Ricardo Puttini, and Zaigham Mahmood, *Cloud Computing: Concepts, Technology & Architecture*, chapters on fundamental concepts/mechanisms — vendor-neutral vocabulary and mechanisms.
- Brendan Burns, *Designing Distributed Systems*, 2nd ed., introductory and single-node/service patterns — cloud-native composition and operational patterns.
- Google, *Site Reliability Engineering*, Chapters 4, 18, and 21 — SLOs, monitoring, and overload handling that constrain elastic architecture.
- FinOps Foundation, *FinOps Framework*, capabilities on allocation, unit economics, forecasting, and optimization — cost as engineering/operations discipline rather than one-time billing review.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Linux and Shell:** supplies host/process/filesystem/resource operation.
2. **Git:** supplies versioned configuration, review, and release identity.
3. **Networking:** supplies IP, DNS, TLS, latency, and load balancing.

### After

1. **Cloud Networking, DNS, TLS, and Load Balancing:** builds exact secure traffic paths.
2. **Containers:** packages workloads for cloud compute.
3. **Kubernetes:** provides orchestration and reconciliation across failure domains.
4. **Terraform:** makes control-plane desired state declarative/versioned.
5. **Cloud Identity and Networking:** deepens Azure RBAC, workload identity, private endpoints, and deny-by-default policy.
6. **SRE:** converts architecture into measurable availability/capacity/recovery.

---ANSWER KEY BELOW---

1. On-demand self-service, broad network access, resource pooling, rapid elasticity, measured service.
2. Customer patches VM OS; provider handles underlying OS/database platform for managed DB per service, customer config/schema/access remains.
3. 43,200×0.0001=4.32 minutes.
4. 40,000 KiB/s=39.0625 MiB/s.
5. `18×3/2=27`, nine per zone.
6. 864 million events/day ×2 KiB ≈1.609 TiB/day.
7. Control outage may block provisioning/config while existing workload data path continues; data-plane outage affects requests/data operations.
8. Object, block, managed file storage respectively.
9. Each replica adds connections/query concurrency; aggregate exceeds DB connections/CPU/IOPS and causes queueing feedback.
10. Storage capacity, storage operations, data transfer/egress, logs/metrics/traces, backups, managed tiers, IP/NAT/gateways, support, licenses, labor (any six).
