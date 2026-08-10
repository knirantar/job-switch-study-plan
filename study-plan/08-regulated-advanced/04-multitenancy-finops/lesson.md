# Multitenancy and FinOps: Isolation, Fairness and Sustainable Unit Economics

**Parent:** 08 — Regulated and Advanced Systems  
**Target:** Senior Backend / AI Platform / MLOps Engineer  
**Study time:** 3–4 hours plus lab  
**Lab:** [`lab/`](lab/) — explainable shared-cost allocation and budget states with six tests

## 1. FOUNDATIONS

### Why share at all?

A **tenant** is a customer, business unit or workload population that receives a logically separate service. **Multitenancy** serves multiple tenants from some shared resources while preserving data, control, performance and accounting boundaries. Sharing improves utilization and reduces duplicated operations; it also creates blast radius, noisy-neighbor and attribution problems. The design question is never simply “single or multi-tenant.” Each tier—identity, compute, database, queue, cache, GPU, keys and observability—can occupy a different point on an isolation spectrum.

A shared platform succeeds only if four invariants hold:

1. Tenant A cannot read, modify or influence unauthorized data/actions of B.
2. One tenant's load cannot consume unbounded capacity or make other tenants miss contracted service.
3. Failures, changes and recovery preserve tenant routing and isolation.
4. Cost and value are visible enough to make responsible product/engineering decisions.

**FinOps** is a collaborative operating practice connecting engineering, finance and business around cloud/technology value. It is not merely reducing bills. **Allocation** assigns cost to owners/products/tenants; **unit economics** divides cost by a value-relevant unit; **forecasting** estimates future use/cost; **optimization** removes waste or improves price/performance without violating reliability, security or product outcomes.

### Core terms

A **pool** shares application and infrastructure; a **silo** gives a tenant dedicated resources; a **bridge** mixes them. A **deployment stamp/cell** is a repeatable bounded deployment serving a subset of tenants. **Blast radius** is the scope affected by failure/change. A **noisy neighbor** consumes disproportionate CPU, connections, IOPS, queue slots, GPU KV cache or downstream quota.

A **quota** limits consumption over a scope/window; a **rate limit** controls arrival rate; a **concurrency limit** controls simultaneous work; a **reservation** guarantees capacity; **priority** orders contention; **fair scheduling** shares a constrained resource. **Admission control** rejects/delays before overload. These controls complement autoscaling: scaling is delayed and bounded by quotas, budget and downstream capacity.

Cloud cost may be **direct** (dedicated tenant database), **shared** (cluster), or **unallocated** (untagged/support). **Showback** reports cost; **chargeback** financially assigns it. **Amortization** spreads commitments/upfront fees across usage/time. **Fully loaded cost** may include cloud, licenses, observability, support and labor—but definitions must be explicit.

## 2. CORE MECHANICS

### 2.1 Define tenant identity once and propagate safely

Map authenticated principal to trusted tenant membership. Do not accept `tenant_id` from a body as authority. Create a request context containing tenant, user/workload, roles, purpose and correlation. Propagate through RPC/message metadata with signature/authentication; consumers reauthorize rather than trusting arbitrary headers.

Every data key, cache key, object path, queue partition and search/vector filter must include tenant context where shared. A cache key `claim:C1001` is unsafe; use a trusted namespace such as `tenant:T7:claim:C1001`. Logs avoid raw sensitive tenant/user data while retaining safe correlation. Cross-tenant administrative operations need explicit elevated policy and audit.

### 2.2 Choose pool, silo, bridge or stamps

**Pool** maximizes density: shared compute/database tables, tenant-keyed rows. It has low marginal cost but larger blast radius and strongest need for flawless logical isolation. **Silo** gives dedicated database/compute/account: easier resource boundaries and custom region/SLO, but idle capacity and fleet operations cost. **Bridge** might share stateless compute but dedicate databases or GPUs to high-tier tenants.

Deployment stamps bound scale and failure. Suppose one stamp supports 500 tenants or 10,000 safe RPS. A placement service assigns tenants, keeps 25% headroom and creates the next stamp before thresholds. Large tenant C can receive a dedicated stamp while A/B share. Moving tenants requires dual-read/write or export/import planning, routing version and reconciliation; avoid embedding physical database URLs throughout code.

Isolation selection follows sensitivity, compliance/residency, performance predictability, customization, tenant count, cost and operational maturity. Dedicated infrastructure does not eliminate application authorization bugs; pooled infrastructure does not inherently mean insecure.

### 2.3 Isolate data correctly

Common database models are shared tables with `tenant_id`, schema per tenant and database per tenant. Shared tables need composite keys/unique constraints including tenant, row-level security where available, mandatory query filters and adversarial tests. A global unique `external_claim_id` may let one tenant collide with another; define uniqueness `(tenant_id, external_claim_id)`.

Schema/database-per-tenant improves backup/restore and blast-radius isolation but multiplies migrations, connection pools and monitoring. At 5,000 tenants, one 5-connection minimum pool each would imply 25,000 idle connections; route through bounded proxies/pools. Encryption keys may be per tenant/tier for cryptographic separation, with lifecycle and recovery cost.

Object storage uses tenant-scoped prefixes/containers and identity policies; do not rely on hard-to-guess paths. Search/RAG authorization filters apply before retrieval. Backups, analytics, dead-letter queues and support exports preserve tenant tags and deletion/residency.

### 2.4 Control noisy neighbors across every bottleneck

Rate limit requests with token buckets; limit concurrent expensive calls; limit input/output tokens; set query timeouts/statement cost; isolate queue partitions/consumer capacity; cap connections, storage and export size. One generic “100 requests/s” misses that a 10-token cached read and 8,000-token generation cost differently. Use weighted units based on measured resource drivers.

Hierarchical quotas combine global, tier and tenant limits. Preserve system headroom and critical healthcare/payment traffic. A tenant may burst to capacity 1,000 tokens and refill 100/s; a 1,500-unit request is rejected even after waiting because it exceeds maximum burst. Return clear 429 plus bounded retry guidance, not hidden infinite queues.

Weighted fair queueing approximates shares under contention. If premium weights A:B:C are 5:3:2, allocate about 50%/30%/20% while all are backlogged; unused share can be borrowed if policy allows. Prevent starvation with minimum service/age promotion. Fairness is multidimensional: GPU seconds, KV memory, database IOPS and outbound bandwidth may require separate schedulers.

### 2.5 Reserve, shed and scale

Reservations guarantee important tenants but waste capacity when unused unless borrowing is allowed. Design reclaim latency: bulk work borrows premium reserve but must yield within a bound. Admission uses actual bottleneck and deadlines. If accepted traffic is 800 rps at SLO while incoming is 1,200, shed 400 intentionally; accepting all may reduce completed goodput below 800.

Autoscale on queue age, admitted work units, SLO goodput, DB/GPU saturation and tenant distribution. A single hot tenant should trigger quota/isolation, not unlimited fleet growth. Maximum replicas respect provider quota, downstream capacity and cost ceiling. Pre-warm slow GPU/model/database resources.

### 2.6 Protect control plane and configuration

Tenant onboarding, tier, region, routing, quota and key configuration is control-plane state. Version it, validate transitions, authorize maker/checker for sensitive changes and audit. Data plane caches config with bounded staleness and safe fallback. A stale tier upgrade is inconvenience; stale tenant routing can disclose data, so fail closed where correctness is uncertain.

Roll out by stamp/tenant cohort, not all tenants simultaneously. Feature flags are scoped and versioned; their evaluation must never override authorization. Test rollback with schema compatibility. Provide tenant-level kill switch/quarantine for abusive or compromised integrations without disabling everyone.

### 2.7 Build a cost taxonomy

Start with billing export line items and map resource → account/subscription → environment → service → product → tenant where defensible. Enforce tags/labels through policy, but tags can change while charges arrive late; maintain effective-dated ownership. Shared discounts/commitments/taxes/support require a stated allocation policy.

Do not fabricate precision. Direct tenant GPU seconds are measurable; platform engineering salary allocation is policy. Keep **measured**, **allocated** and **estimated** fields distinct. Track unallocated cost and reduce it; silently spreading it hides ownership gaps.

### 2.8 Allocate shared cost with causal drivers

Choose drivers resembling consumption: GPU-seconds for inference compute, GiB-month for storage, requests only when requests have similar cost. The lab allocates ₹1,000 using 40% request share, 40% GPU share and 20% storage share.

Tenant A has 60% requests, 60% GPU and 20% storage: `.4×.6 + .4×.6 + .2×.2 = .52`, so ₹520. B: 30%,30%,60% → `.12+.12+.12=.36`, ₹360. C receives ₹120. Drivers sum to one and allocations conserve every cent.

Rounding independently can lose money. Three equal tenants sharing ₹1 yield ₹0.33 each = ₹0.99. The lab floors, then assigns the remaining cent by largest remainder with tenant ID tie-break: A ₹0.34, B/C ₹0.33. This is reproducible, but business policy may use another disclosed method.

### 2.9 Measure unit economics

Useful units connect cost to value: cost per successful claim adjudicated, per 1,000 approved transactions, per million inference tokens under SLO, or per active tenant—not cost/request if retries and failures inflate activity. Calculate both marginal and fully loaded cost.

If monthly platform cost is ₹3,600,000 and 24 million successful predictions, cost is ₹0.15/prediction. If 10% are retries excluded from “successful,” do not divide by all attempts. Segment by model/tier/region and quality/SLO. A cheaper model that increases manual reviews may raise total business cost.

Unit cost can fall while total cost rises due to growth; that may be healthy. Conversely total bill falls because traffic collapsed. Pair cost, utilization, quality, revenue/value and SLO.

### 2.10 Budget and forecast

Budgets are guardrails, not forecasts. The lab states `WATCH` at spend ≥80% budget, `FORECAST_BREACH` when projected total exceeds budget, and `EXCEEDED` after actual passes it. Current spend ₹70 of ₹100 with forecast ₹110 needs action even though only 70% is spent.

Forecast with business drivers and uncertainty: tenant growth, request/token distribution, seasonality, rollout, price/FX, commitments and engineering changes. Use low/base/high. If August daily run rate is ₹120k and a model launch adds measured ₹35k/day from day 16, simple 31-day forecast is `15×120k + 16×155k = ₹4.28M`, before seasonality/discount changes.

Alerts need owner and action. A budget email no one owns is theater. Tie anomaly detection to deploy/model/tenant dimensions, but investigate before automatically shutting down critical clinical/payment service.

### 2.11 Optimize in the right order

1. Eliminate waste: abandoned disks, idle endpoints, duplicate telemetry, oversized retention.
2. Improve efficiency: batching, caching, storage tiering, right-sizing, scheduling, query/model optimization.
3. Improve rates: commitments/reservations/spot after baseline is understood.
4. Improve architecture/product: pool/silo placement, model routing, async/batch, tier/pricing.

Commitments reduce rate but create utilization risk. If a one-year commitment covers 100 units/hour and actual baseline falls to 60, 40% is unused. Spot/preemptible capacity fits checkpointable batch, not an unprotected payment authorization. Cost controls never waive resilience or isolation.

### 2.12 Govern FinOps decisions

Engineering owns design and usage; finance owns accounting/forecast partnership; product owns value/pricing; leadership owns risk trade-offs. Establish weekly anomaly/optimization review and monthly allocation/forecast reconciliation. Every recommendation has baseline, expected saving, implementation cost, reliability/security impact, owner and verification date.

Avoid perverse incentives. Charging solely by request may encourage batching that harms latency, or discourage safety checks. Tenant chargeback is commercial/accounting policy and may differ from internal allocation. Explain allocation changes before they surprise customers.

### 2.13 Run the lab

```bash
cd lab
python3 -m unittest -v test_allocation.py
```

Six tests prove exact cent conservation, expected ₹520/₹360/₹120 allocation, deterministic largest-remainder rounding, weight/zero-driver validation and budget states. Production ingests versioned billing/usage data, handles late corrections/currency/tax/discounts, and publishes reproducible allocation versions.

## 3. WORKED PROBLEMS

### Problem 1 — Composite identity (easy)

Two tenants both use claim ID C1001. Schema has `PRIMARY KEY(claim_id)`. **Solution.** Use `(tenant_id, claim_id)` and enforce tenant predicate/authorization; global surrogate can remain internal. **Mistake:** assuming external IDs are globally unique.

### Problem 2 — Connection explosion (easy)

5,000 tenant databases × five idle connections. **Solution.** 25,000 minimum connections. Use bounded proxy/pool, lazy connections, shard/stamp routing and database limits. **Mistake:** evaluating database-per-tenant only for security.

### Problem 3 — Weighted fairness (medium)

Backlogged A:B:C weights 5:3:2, capacity 1,000 work units/s. **Solution.** Approximate 500/300/200 while all demand; redistribute unused share under policy. **Mistake:** fixed shares that waste idle capacity or starvation under strict priority.

### Problem 4 — Overload goodput (medium)

Safe 800 rps; incoming 1,200. Accept-all yields only 500 within SLO. **Solution.** Admit near 800 and reject/defer 400; preserve 800 goodput. Tune from tests and tenant priority. **Mistake:** calling accepted queue entries throughput.

### Problem 5 — Cost allocation (medium)

Use the lab's usage/weights for ₹1,000. **Solution.** A `.52`=₹520, B `.36`=₹360, C `.12`=₹120. Sums ₹1,000. **Mistake:** averaging raw request/GPU/storage values without normalized shares.

### Problem 6 — Rounding (medium)

Allocate ₹1 equally to A/B/C. **Solution.** Floor ₹.33 each, one cent remains; deterministic tie-break gives A ₹.34. **Mistake:** accepting ₹.99 total or rounding each to ₹.33 without reconciliation.

### Problem 7 — Unit cost (hard)

₹3.6M/month, 24M successful predictions, 3M failed/retried attempts. **Solution.** ₹0.15 per successful prediction. Per attempt would be ₹0.1333 but answers a different question. Track failure cost separately. **Mistake:** choosing denominator that flatters efficiency.

### Problem 8 — Dedicated tenant decision (hard)

Tenant X is 45% GPU load, requires India-only data and strict p99. **Solution.** Consider dedicated GPU/stamp and regional data/key boundary, priced to cover reserved peak/ops. Compare measured shared isolation/quota versus dedicated cost; migrate with routing/version/reconciliation. **Mistake:** treating dedicated as purely technical or automatically secure.

### Problem 9 — Commitment risk (hard)

Commit 100 GPU-hours/hour equivalent; optimized demand becomes 60. **Solution.** 40% commitment is unused unless workloads can safely shift. Model low/base/high before purchase and track coverage/utilization separately. **Mistake:** calling discounted rate savings without utilization.

## 4. REAL-WORLD / APPLIED CONTEXT

Azure Architecture Center presents sharing-to-isolation as a spectrum and recommends deployment stamps for bounded tenant groups. Its guidance names trade-offs among isolation, performance, reliability, cost and fleet manageability; it also warns shared caches must namespace tenant data.

AWS SaaS guidance distinguishes authentication from tenant isolation: an authenticated user is not automatically constrained to its tenant. That maps directly to server-derived tenant context and resource-level policy throughout this lesson.

Kubernetes ResourceQuota/LimitRange constrain namespace resources but do not by themselves provide SaaS tenant authorization or fair application-level GPU tokens. API Priority and Fairness protects Kubernetes API-server request classes, not your inference endpoint. Use platform primitives at their actual boundary.

The local allocation suite passes six cases in about a millisecond on CPython. This proves arithmetic invariants, not the accuracy of chosen business weights; driver selection requires governance and measured causality.

## 5. COMPARISON TABLE

| Pattern | Concrete trade-off | Use | Boundary |
|---|---|---|---|
| Pool/shared table | Highest density | Many similar tenants | Logical bug/blast radius |
| Schema per tenant | More namespace separation | Moderate fleet | Migration/catalog scale |
| DB per tenant | Backup/key/perf isolation | Regulated/high tier | Connections/fleet cost |
| Dedicated stamp | Predictable boundary | Large/custom tenant | Idle peak capacity |
| Shared stamp | Bounded pool | Scale-out cohorts | Noisy neighbors inside stamp |
| Rate quota | Limits arrivals/window | API protection | Expensive request variance |
| Work-unit quota | Models tokens/GPU/query cost | Heterogeneous work | Requires calibration |
| Reservation | Guaranteed capacity | Contracted critical tier | Idle waste |
| Spot capacity | Lower variable rate | Checkpointable batch | Preemption |
| Showback | Visibility only | Early FinOps adoption | Weak direct incentive |
| Chargeback | Financial assignment | Mature governance | Disputes/perverse incentives |
| Direct allocation | Measured tenant resource | Dedicated assets | Shared platform remains |
| Weighted allocation | Explainable shared drivers | Mixed services | Policy, not causal certainty |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Authentication equals tenant isolation—resource scope is separate.
2. Dedicated deployment needs no tenant checks—application/support paths still cross boundaries.
3. `tenant_id` in request is trusted—derive from authenticated membership.
4. Autoscaling solves noisy neighbors—cost/downstream/quota and startup remain.
5. Requests are equal—tokens, queries and GPU residency vary orders of magnitude.
6. Strict priority is fairness—low tiers can starve.
7. Tags make allocation accurate—late/missing/mutable ownership and shared costs remain.
8. Allocation equals customer invoice—internal causality and commercial pricing differ.
9. Lower bill means efficiency—traffic/value may have fallen.
10. Discount equals saving—unused commitment can cost more.
11. Cost optimization may reduce redundancy—SLO/security constraints are gates.
12. Tenant label on every metric is observability—high cardinality/cost/privacy can explode.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full lesson.

- Tenant isolation spans identity, data, cache, queue, compute, GPU, logs, backup and support.
- Derive tenant context; composite keys/predicates; negative-test cross-tenant paths.
- Pool for density, silo for boundary, bridge/stamps for graded isolation.
- Bound rate + concurrency + work units + queue; reserve/priority/fair scheduling as needed.
- Autoscale on bottleneck/goodput with cold-start, quota, downstream and budget bounds.
- Cost taxonomy: direct/shared/unallocated; measured/allocated/estimated.
- Normalize causal drivers; allocation must conserve exact total.
- Unit cost uses successful/value-relevant denominator plus quality/SLO.
- Budget ≠ forecast; use low/base/high and owned actions.
- Optimize waste → efficiency → rates → architecture/product, verifying outcomes.

## 8. PRACTICE SET FOR SELF-TEST

1. Why is cache key `patient:P1` unsafe in a pooled service?
2. Compute idle connections for 2,400 DBs with minimum pool 4.
3. Weights A:B 3:1, capacity 800 work/s, both backlogged. Shares?
4. Allocate ₹100 equally among three tenants using largest remainder and alphabetical tie-break.
5. Monthly cost ₹900,000, 6M successful jobs. Cost/job?
6. Current spend ₹75, budget ₹100, forecast ₹115. Lab state?
7. Name four cost drivers better than raw request count for mixed AI workloads.
8. Give three reasons to isolate a tenant into a dedicated stamp.
9. Why can a 30% committed-price discount yield negative savings?
10. What proves a FinOps optimization succeeded beyond a lower bill?

## 9. CURATED RESOURCES

1. [FinOps Framework](https://www.finops.org/framework/) — canonical capabilities for allocation, unit economics, forecasting, budgeting and optimization.
2. [Azure multitenant architecture approaches](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/overview) — pool/silo/stamp trade-offs across service categories.
3. [Azure tenancy models](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models) — isolation spectrum, reliability, performance and cost implications.
4. [AWS SaaS Tenant Isolation Strategies](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/) — explicit distinction between general authentication and tenant isolation.
5. [Kubernetes Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) — namespace aggregate constraints and exact enforcement boundary.
6. [Kubernetes API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/) — queueing/fairness mechanics for API-server traffic.
7. **Beyer et al., _Site Reliability Engineering_, Chapters 21 and 22** — overload handling and cascading-failure controls.
8. **Martin Kleppmann, _Designing Data-Intensive Applications_, Chapters 5 and 9** — partitioning, tenancy placement and consistency trade-offs.
9. **Dominik Tornow, “Multi-Tenancy in Kubernetes,” SIG Architecture principles/guidance** — isolation dimensions and Kubernetes boundary thinking.
10. [FOCUS specification](https://focus.finops.org/) — standardized cloud cost/usage billing dataset semantics for portable allocation analysis.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Security, Privacy and Audit** — defines isolation, identity and evidence invariants.
2. **GPU Inference** — supplies scarce-resource and work-unit drivers.
3. **Capacity and DR** — supplies safe capacity, headroom and blast-radius reasoning.
4. **Observability** — supplies bounded tenant-tier signals and cost evidence.

### After

1. **Platform Capstone** — integrates stamps, policy, quotas, cost and operational proof.
2. **System Design Interviews** — turns isolation/economics into explicit trade-offs.
3. **Product Pricing and Capacity Planning** — converts unit economics into tiers and commitments.
4. **Governance/Incident Response** — operates cross-tenant exposure, runaway cost and fairness failures.

---ANSWER KEY BELOW---

1. Tenant A and B can collide; namespace with trusted tenant context and enforce authorization.
2. `2,400×4=9,600` idle connections.
3. 600 and 200 work units/s while both demand; unused share may be borrowed under policy.
4. ₹33.34 to A, ₹33.33 each to B/C; total ₹100.
5. `₹900,000/6,000,000=₹0.15` per successful job.
6. `FORECAST_BREACH`: spend is below 80%, but forecast exceeds budget.
7. GPU-seconds, input/output tokens, KV-memory-seconds, query CPU/IO time, GiB-month, egress bytes—any four.
8. Data residency/compliance, high sensitivity, dominant/noisy load, strict SLO, custom configuration, reduced blast radius—any three with cost acknowledged.
9. Demand may fall below committed quantity; unused commitment cost can exceed on-demand cost for actual use.
10. Compare normalized unit cost plus SLO/goodput, quality/safety, reliability, utilization and business value against a versioned baseline; include implementation/operational cost.
