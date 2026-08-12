# SaaS Multitenancy and Cloud Cost Foundations

Parent subject: `08-regulated-advanced`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### SaaS is a product and operating model

Software as a Service delivers an application/platform to multiple customers over a managed lifecycle. **Multitenancy** means multiple tenants share some application/infrastructure while each experiences a logically isolated environment, configuration, identity, data, performance and billing boundary.

A **tenant** may be company, hospital, business unit, workspace, payer, or regulated data controller. A user can belong to multiple tenants with different roles. Tenant is not synonymous with user, subscription, region, or database. Define the tenant boundary from contracts, identity, data ownership, isolation and billing.

Sharing improves utilization and operating consistency, but creates cross-tenant disclosure, noisy neighbor, blast radius, customization, deletion, metering and cost-allocation challenges. Isolation is end-to-end, not merely a `tenant_id` column.

### Control plane and data plane

The SaaS **control plane** manages tenant provisioning, subscriptions/entitlements, identity federation, placement, configuration, keys, quotas, upgrades, and lifecycle. The **data plane** serves tenant application requests/data. A compromised control plane can affect every tenant; isolate privileges, audit, and keep data-plane operation statically stable where possible.

Provisioning is a workflow: create tenant identity/metadata, choose region/stamp/tier, allocate resources/keys/namespaces, configure federation, seed roles/policies, validate, and activate. It must be idempotent, compensatable, observable and resumable. Partial provisioning should not expose default shared resources.

### Tenant lifecycle

States might be `REQUESTED→PROVISIONING→ACTIVE→SUSPENDED→CLOSING→DELETING→DELETED`, with failed/quarantined. Suspension blocks use but retains data. Closing initiates export/retention/contract checks. Deletion respects legal holds and backup expiry. Re-using a tenant identifier can attach old cache/object/audit data; use immutable unique IDs and never recycle casually.

Offboarding revokes federation/users/workload credentials, disables traffic/jobs/webhooks, exports data, removes active/derived data, expires backup, destroys tenant keys where appropriate, releases domains/IPs/quotas, and retains minimal billing/audit evidence.

### Isolation dimensions

- **Identity:** tenant membership/role from authoritative auth context.
- **Compute:** shared processes, namespaces, nodes, clusters, or dedicated.
- **Data:** row, schema, database, account, region.
- **Network:** routes, policies, private endpoints.
- **Encryption/key:** shared service key, per-tenant key, customer-managed key.
- **Performance:** quotas, queues, pools, rate/concurrency, capacity reservations.
- **Operations:** logs/backups/support/admin access and incident blast radius.
- **Customization:** configuration/model/prompts/features without code forks.

Isolation level follows risk/tier/economics. Shared table with row-level policy can be strong when every access path enforces it and tests prove it; database-per-tenant can still leak through shared cache/log/admin.

### Silo, pool, bridge, and cell

**Silo** dedicates stack/resources per tenant: strongest physical/logical separation and customization, highest cost/operational fleet. **Pool** shares resources with tenant-aware logic: efficient, greater blast/noisy-neighbor risk. **Bridge** mixes, e.g. shared app plus database per tenant. **Cell/stamp** groups bounded tenants in independent repeated stacks, reducing blast radius and scaling horizontally.

Placement maps tenant to cell/region/tier and is authoritative, highly available and cached safely. Moving tenants requires versioned routing, data replication/cutover, dual-read/write avoidance or protocol, validation, DNS/jobs/events, rollback, and audit.

### Tenant context

Authenticate token/session and derive membership. Server resolves tenant from trusted subject/organization claim, host/domain mapping, or explicit selected tenant validated against membership. Do not trust arbitrary `X-Tenant-Id` alone. Propagate context through request, DB session/query, cache key, event envelope, object path, logs, metrics (bounded), traces and downstream token.

Async jobs must carry immutable tenant ID and authorization purpose captured/reauthorized as policy requires. Background “system” identity should not become universal bypass.

### Data isolation

Shared tables use composite keys/foreign keys containing tenant and queries scoped by tenant. Database row-level security can enforce policy but connection-pool session context must reset correctly, table owners/bypass roles restricted, migrations and admin queries tested. Unique constraints often include tenant.

Cache key=`tenant:id`, never id alone. Object storage prefixes/accounts and IAM scope per tenant/tier; signed URLs short-lived and scoped. Search/vector indexes need tenant filter/namespace before results. Backups and analytics preserve tenant ownership and deletion.

### Noisy neighbors and fairness

One tenant can consume CPU, DB connections, queue partitions, GPU tokens, storage IOPS, cache, network, or third-party quota. Use global bounds plus per-tenant token buckets/concurrency/queues, weighted fair scheduling, reserved capacity for critical tiers, maximum payload/tokens, and admission.

**Hard quota** rejects beyond limit. **Soft quota** allows burst with alert/overage. **Entitlement** is product permission/limit. **Rate limit** controls time rate; **concurrency limit** controls in-flight; **budget** controls cumulative use/cost. Define response, retry/reset, visibility and support override.

Fairness does not mean equal: paid tiers and clinical urgency may have weights/reservations, but starvation and policy must be explicit. Weighted fair queueing approximates shares when demand exists; idle allocation can be borrowed.

### Metering

Metering records billable/operational usage: requests, seats, storage GB-hours, training GPU-seconds, input/output tokens, model calls, egress, jobs. A usage event needs event ID, tenant, meter/version, quantity/unit, occurrence and ingestion time, resource/tier/region, source and correction linkage.

Meters must be idempotent, immutable/correctable, auditable and reconcile to provider/source. Late/duplicate/out-of-order events occur. Pricing changes should not reinterpret old usage; version rating rules. Never use raw observability metrics as invoices without billing-grade integrity/completeness.

### Cost, price, revenue, and margin

**Cost** is expense to deliver. **Price** charged. **Revenue** recognized income. **Gross margin**=(revenue−cost of revenue)/revenue. Cloud bill is not total cost: licenses, support, third-party API, observability, payment fees and operations can be cost of service depending accounting.

Unit cost=`allocated service cost/useful units`. Examples ₹ per 1,000 claims, per successful inference, per active tenant. A failed/retried request still costs but may not be billable; track cost per attempted and successful outcome.

### Direct, shared, fixed, variable cost

Direct resource maps one tenant/service. Shared cost needs allocation. Fixed/provisioned cost exists regardless short-term use; variable grows with usage. **Marginal cost** is next unit; average cost includes idle/shared fixed.

Allocation methods:

- direct tags/resource ownership;
- proportional usage (CPU/GPU seconds, bytes, tokens);
- equal split (simple, often unfair);
- revenue/headcount allocation (financial view, weak engineering signal);
- activity-based drivers;
- unallocated/shared platform bucket with transparency.

Allocation should reconcile exactly to invoice, avoid false precision, and not incentivize harmful behavior. A platform team allocated by request count might discourage batching or penalize lightweight requests; use resource-weighted units.

### Cloud cost mechanics

Compute cost = provisioned/consumed time×rate, adjusted commitments/spot. Storage includes GB-month, operations, retrieval, redundancy. Network egress and NAT/gateway, logs/traces, backups, managed database tiers, GPUs, licenses and support matter. Pricing changes by region/date/tier.

Commitments/reservations cover stable base load for discount but create utilization risk. Spot handles interruptible jobs with checkpoint/fallback. Rightsizing uses CPU/memory/GPU/IOPS/latency—not average CPU alone. Scaling to zero saves idle but cold start/availability may not fit.

### FinOps

FinOps is collaboration among engineering, finance, product, procurement and leadership to maximize business value of cloud. Phases/capabilities include inform (allocation/visibility), optimize (rightsizing/rates/architecture), operate (budgets/governance), plus planning/forecasting/unit economics.

Cost anomaly alert must account for seasonality and usage. A 30% cost increase with 50% successful transactions may improve unit cost. Conversely flat cost with traffic down 50% worsens efficiency.

Budgets are not automatic safe kill switches for critical healthcare/payment service. Use forecasts, approvals, quotas, tier limits, and graceful controls; never abruptly stop patient-critical workload because monthly budget crossed.

## 2. CORE MECHANICS

### 2.1 Tenant-aware request

Gateway validates issuer/audience/signature, selected tenant membership and routes to cell. Service stores immutable `TenantContext(tenant_id,user_id,roles,purpose,trace)`. Repository API requires context and applies tenant in every key/query. DB role/RLS adds defense. Cache/event/log use tenant. Response object authorization rechecked. Tests mutate every identifier/tenant.

### 2.2 Shared schema

```sql
CREATE TABLE claim(
 tenant_id uuid NOT NULL,
 claim_id uuid NOT NULL,
 patient_id uuid NOT NULL,
 amount_paise bigint NOT NULL,
 PRIMARY KEY(tenant_id,claim_id),
 FOREIGN KEY(tenant_id,patient_id) REFERENCES patient(tenant_id,patient_id)
);
```

Composite foreign key prevents cross-tenant patient. Indexes begin tenant where query does. RLS policy uses trusted session setting; transaction-pool connection sets/resets locally and runtime role cannot bypass. Bulk/admin path separately authorized/audited.

### 2.3 Rate/concurrency quotas

Tenant A entitlement100rps burst200; B20rps burst40. Token bucket refills per second and consumes per request cost (large inference can cost tokens proportional input/output). Global limit protects service. Concurrency cap prevents 100 slow requests consuming all. 429 includes retry/reset and usage view. Billing overage separate from safety limit.

### 2.4 Weighted fair capacity

Total GPU scheduler100 units/s; weights premium3, standard1 for two active tenants. If both backlogged, shares75/25. If premium uses40, standard can borrow remaining60 depending policy. Add max per tenant and critical reserved lane. Fair scheduling works over time; individual large jobs need preemption/chunking.

### 2.5 Usage event

```json
{"eventId":"u-123","tenantId":"T1","meter":"llm.tokens.v2",
 "quantity":4500,"unit":"token","occurredAt":"...","region":"centralindia",
 "resource":"endpoint:e7","sourceRequest":"r-9","correctionOf":null}
```

Collector inbox deduplicates event ID, validates nonnegative/unit/meter, stores immutable. Corrections add inverse/replacement. Aggregate by billing period after late-event window; reconcile provider model usage and gateway counts.

### 2.6 Allocate shared bill

Shared GPU cost ₹120,000. Tenant usage GPU-seconds A50k,B30k,C20k total100k. Allocate ₹60k,₹36k,₹24k exactly. Per GPU-second ₹1.20. If reserved idle20% not attributed, policy may allocate used proportionally or show ₹24k platform idle and allocate ₹48k/₹28.8k/₹19.2k; disclose.

Use integer paise/largest remainder so allocation sums exactly.

### 2.7 Unit economics

Monthly allocated service cost ₹500,000; successful claims2,000,000→₹0.25/claim. Attempts2.2M→₹0.227/attempt. Revenue₹800,000→gross profit₹300k, margin37.5% if all cost qualifies. If retries rise while successes flat, cost/success worsens.

Break down compute .10, DB .04, LLM .06, observability .02, support .03 per success to prioritize.

### 2.8 Commitment coverage

Hourly demand p10=80,p50=120,p90=200 units. Commit80 stable base; on-demand/spot handles variable. Committing p90 risks 40–120 idle most hours. Evaluate discount, term, growth, flexibility, utilization and opportunity; pooled commitments may improve.

Coverage=committed-used applicable/eligible use; utilization=used commitment/purchased. High coverage with low utilization can waste; optimize both.

### 2.9 Cost anomaly

Expected daily ₹10k±seasonal; actual₹15k. Decompose quantity×rate: traffic +20%, tokens/request +25%, unit rate unchanged → cost ~1.5×. Cause prompt/retrieval context grew. Check quality benefit; cap context/cache/routing, not blindly downgrade model. Correlate deployment config.

### 2.10 Tenant move

Create destination resources/keys; snapshot/copy with encryption; replicate changes; validate counts/checksums/domain; update placement with version/fencing; quiesce or controlled cutover; drain old jobs/events; verify traffic/performance/data; retain rollback; destroy old after window/retention. Ensure callbacks/DNS/private links and usage billing attribution switch exactly once.

## 3. WORKED PROBLEMS

### Problem 1 — Tenant versus user (easy)

Consultant belongs to hospital A and B. One tenant?

**Solution.** One identity/user with separate memberships/roles in two tenant boundaries; selected tenant context explicit.

**Trap:** tenant ID permanently stored on user.

### Problem 2 — Cache key (easy)

Both tenants have claim ID C1. Safe key?

**Solution.** Include tenant and resource/version, e.g. `claim:T1:C1:v3`, plus auth/freshness policy.

**Trap:** UUID-looking ID assumed global.

### Problem 3 — Gross margin (easy)

Revenue₹1M,cost₹650k.

**Solution.** (1M−650k)/1M=35%.

**Trap:** profit/cost=53.8% called margin.

### Problem 4 — Allocation (medium)

₹90k shared cost, usage60/30/10%.

**Solution.** ₹54k,₹27k,₹9k.

**Trap:** percentages not reconciling due rounding.

### Problem 5 — Noisy neighbor (medium)

Tenant sends long LLM prompts; request-rate limit not exceeded but GPU OOM.

**Solution.** Meter/limit weighted tokens and concurrent KV memory, max context/output, admission by memory, per-tenant/global budgets and fair queue.

**Trap:** request count alone.

### Problem 6 — RLS pool (medium)

Connection retains T1 session setting then serves T2.

**Solution.** Cross-tenant leak. Set transaction-local context, reset, pool hooks, no bypass role, integration/adversarial tests; consider separate pools/databases by risk.

**Trap:** middleware variable assumed DB policy.

### Problem 7 — Meter duplicate (hard)

Usage event redelivered.

**Solution.** Stable event ID/inbox unique makes idempotent. Do not sum twice. Correction new linked event, never overwrite billed history silently.

**Trap:** at-least-once broker assumed exactly once.

### Problem 8 — Dedicated tier (hard)

Does database-per-tenant guarantee isolation?

**Solution.** Improves data/resource boundary but shared app/cache/log/control plane/admin/backup/network can leak/cascade. Threat-model end-to-end.

**Trap:** one dedicated component equals silo.

### Problem 9 — Budget kill (hard)

Hospital exceeds monthly inference budget during emergency.

**Solution.** Safety policy may allow controlled overage/critical reserved path and escalate, not hard stop. Shed noncritical work, notify, record cost/approval. Product/legal policy predefines.

**Trap:** finance threshold overriding patient safety.

## 4. REAL-WORLD / APPLIED CONTEXT

### Azure SaaS guidance

Microsoft Azure Architecture Center documents multitenant approaches, deployment stamps, tenant mapping, isolation and pricing models. Azure resources/subscriptions/resource groups, Entra ID, managed identities, Policy and Cost Management support but do not create application tenancy automatically.

### Kubernetes multitenancy

Namespaces, RBAC, NetworkPolicy, quotas/limits, admission and separate clusters/nodes provide layers. Namespace alone is weak for hostile tenants; shared kernel/control plane and cluster-wide objects remain. SaaS tenants often do not map one-to-one to Kubernetes namespaces.

### FinOps Foundation

FinOps Open Cost and Usage Specification (FOCUS) normalizes billing data. Framework emphasizes allocation, anomaly, forecasting, unit economics, commitment and workload optimization. Provider bill tags are inputs; application tenant metering fills shared-resource attribution.

## 5. COMPARISON TABLE

| Model | Isolation | Unit cost | Operations | Best fit |
|---|---|---|---|---|
| Pooled shared | Logical | Lowest potential | One fleet, policy complexity | Many similar tenants |
| Schema per tenant | Metadata/schema | Medium | Migration fleet in DB | Moderate isolation |
| DB per tenant | Data/resource | Higher | Connections/migrations/backups | Regulated/premium |
| Full silo | Strongest dedicated stack | Highest | Fleet sprawl | contractual/custom/high-risk |
| Cell/stamp | Bounded group | Balanced | Repeatable units/placement | scale/blast control |
| Equal cost split | Weak fairness | Simple | Low | genuinely equal usage |
| Usage allocation | Causal | Metering needed | Medium | variable consumption |
| Dedicated charge | Direct | Transparent | Resource sprawl | silo tier |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Tenant equals user—memberships many-to-many.
2. `tenant_id` column completes isolation—every layer/path matters.
3. Client tenant header is authority—validate membership server-side.
4. Database per tenant is full silo—shared layers remain.
5. Namespace is security boundary alone—cluster/kernel/control remain.
6. Rate limit prevents noisy neighbor—payload/concurrency/resources differ.
7. Meter equals bill—rating/contracts/corrections/reconciliation required.
8. Observability metric is billing-grade—loss/duplicates/changes possible.
9. Price equals cost—margin/revenue differ.
10. Shared cost must be hidden—explicit unallocated bucket is more honest.
11. Commit discount always saves—unused commitments waste.
12. Budget should hard-stop every workload—criticality/safety policy matters.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- Tenant boundary = contract+identity+data+isolation+billing.
- Control plane manages lifecycle/placement; data plane serves.
- Propagate authoritative tenant to DB/cache/object/event/log/search.
- Composite tenant keys/FKs; test every bulk/admin/async path.
- Pool efficiency; silo isolation; bridge hybrid; cell bounded blast.
- Global+tenant rate, concurrency, resource and cumulative budgets.
- Weighted fairness can lend idle capacity while preventing starvation.
- Usage event immutable/idempotent/versioned/correctable/reconciled.
- Cost≠price≠revenue; gross margin=(revenue−cost)/revenue.
- Allocate direct first, shared by defensible drivers, reconcile exactly.
- Optimize cost per successful business outcome, not bill alone.
- Offboarding includes active/derived/backups/identity/metering/evidence.

## 8. PRACTICE SET FOR SELF-TEST

1. Model user memberships in three tenants.
2. List tenant context propagation layers.
3. Compare pooled table, DB-per-tenant and cell.
4. Design quota for LLM endpoint.
5. Allocate ₹100,001 among usage50/30/20 with exact paise/rupee policy.
6. Define billing usage event.
7. Compute unit cost ₹750k/3M success.
8. Compute margin revenue₹1.2M,cost₹900k.
9. Explain commitment coverage versus utilization.
10. Outline tenant offboarding.

## 9. CURATED RESOURCES

- Microsoft Azure Architecture Center, *Architectural Approaches for the Deployment and Configuration of Multitenant Solutions* and multitenancy checklists — Azure tenant models, stamps, isolation, identity, cost.
- AWS, *SaaS Tenant Isolation Strategies* and SaaS Lens — silo/pool/bridge, identity and isolation concepts transferable across clouds.
- FinOps Foundation, *FinOps Framework* capabilities and *FOCUS Specification* — allocation, unit economics, anomaly, forecasting, optimization and normalized billing.
- Kubernetes official “Multi-tenancy,” RBAC, Network Policies, Resource Quotas, and Pod Security docs — actual cluster isolation mechanisms/limits.
- Martin Fowler, “Multi-Tenant Architecture” and deployment stamp/cell architecture literature — tenancy patterns and trade-offs.
- NIST SP 800-204A, *Building Secure Microservices-based Applications Using Service-Mesh Architecture* — service identity/policy/telemetry relevant shared platforms.
- J.R. Storment and Mike Fuller, *Cloud FinOps*, 2nd ed., chapters on allocation, rates, rightsizing, commitments, unit economics and culture — practical FinOps operating model.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Cloud/Identity/Networking:** resource hierarchy and access.
2. **Security/Privacy:** tenant isolation, purpose, deletion/audit.
3. **Distributed/Data Systems:** placement, partitioning, quotas and consistency.
4. **Hardware/GPU:** resource drivers for AI cost.

### After

1. **Multitenancy and FinOps advanced:** deepens cells, noisy neighbor, exact allocation/forecasting.
2. **Security, Privacy and Audit:** proves cross-tenant controls.
3. **GPU Inference/LLMOps:** meters token/KV/GPU usage and admits fairly.
4. **SRE:** sets per-tenant/global SLO, capacity and incident blast.

---ANSWER KEY BELOW---

1. User identity plus membership table `(user,tenant,roles,status,validity)`; tenant selected and authorized per request.
2. Gateway/auth context, service, DB key/session, cache, object path, event/job, search/vector, logs/traces/audit, downstream token.
3. Pool efficient/logical; DB dedicated data but fleet overhead; cell groups bounded tenants/repeatable blast/capacity.
4. Input/output/context caps, weighted token rate, concurrent requests/KV bytes, daily spend, global cap, tier weights, 429/reset/usage and safety override.
5. Convert to smallest unit and largest remainder. At rupee integer: 50,001;30,000;20,000 sums100,001 (tie/order policy); preferably allocate paise precisely.
6. Stable ID, tenant, meter/version, quantity/unit, occurrence/ingest, resource/region/tier, source request, correction link, integrity/provenance.
7. ₹0.25/success.
8. (1.2−.9)/1.2=25%.
9. Coverage fraction eligible use under commitments; utilization fraction purchased commitment consumed; high coverage can coexist with waste.
10. Suspend/drain, authenticate export, retention/hold, revoke federation/users/secrets/jobs/webhooks, delete active/derived/index/cache, expire backups/keys, finalize billing/audit and release resources/domain.
