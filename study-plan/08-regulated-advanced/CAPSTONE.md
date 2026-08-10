# Regulated and Advanced Systems Capstone — Multi-Tenant Healthcare/Fintech AI Platform

## Objective

Design, implement and defend a shared platform that routes insurance claims, exchanges authorized clinical evidence, posts approved payments and serves GPU-based model/LLM inference. Prove security/privacy/audit, domain correctness, accelerator capacity and tenant economics together. A diagram or compliance checklist alone does not pass.

## Product and risk contract

- 60 healthcare/insurance tenants; three regulated high-tier tenants receive dedicated stamps, 57 use pooled stamps of at most 20 tenants.
- Peak 1,200 claims requests/s; accepted traffic p95 ≤200 ms. Each pooled stamp must survive one tenant sending 10× contracted work without other tenants exceeding SLO.
- Claim model only recommends straight-through versus human review; it never denies. Risk ≥0.60 or amount ≥₹500,000 goes to review. Missing authority hard-stops.
- Approved claim payments use exact INR, immutable double-entry postings, idempotency and daily processor/bank reconciliation.
- Clinical retrieval is authorization- and consent-scoped before context reaches the LLM; responses cite exact FHIR resource versions.
- GPU model: 7B, 32 layers, 8 KV heads, 128 head dimension, FP16 KV/weights. Derive memory and verify on target hardware.
- Every tenant has request/concurrency/token/storage quotas and an attributed cost report. Allocation conserves every currency unit.
- General logs/tracking contain no patient narrative, claim ID, payment-card value, credential or raw prompt.

## Required design and implementation

1. Create data-flow/threat models covering identity, pooled/dedicated stamps, shared data/cache/queues/GPU, support, training, backups and third parties.
2. Implement trusted tenant context, object/action authorization, composite keys, cache namespaces, retrieval filters and negative cross-tenant tests.
3. Define classification, purpose, consent/authority, retention/deletion/legal hold, encryption/key lifecycle and break-glass workflows.
4. Emit stable audit events for access, consent, model recommendation, override, approval, ledger posting, reconciliation, deployment, quota and admin change. Protect with authenticated append, immutable retention and independently anchored chain heads.
5. Define claim/payment state machines, exact money/currency/rounding, balanced postings, request-fingerprint idempotency, outbox/inbox and UNKNOWN/reconciliation behavior.
6. Exchange clinical data using explicit FHIR profiles, terminology, identity/version/provenance; demonstrate transaction-versus-batch behavior and safe patient matching.
7. Engineer human review: authorized assignment, evidence/limitations, SLA/capacity, double approval, structured override and appeal trail.
8. Derive GPU weight/KV/workspace capacity, then benchmark representative prompt/output distributions, batching, quantization and concurrency on named hardware/runtime.
9. Report TTFT/TPOT/end-to-end percentiles, goodput, queue/copy/compute, memory/utilization/power, error/OOM and quality/slice gates.
10. Implement hierarchical rate/concurrency/work-unit quotas, weighted fair scheduling, priority/minimum shares, bounded queues, overload shedding and tenant quarantine.
11. Create stamp placement/migration and dedicated-tenant policies with region, headroom, quota and blast-radius criteria.
12. Allocate direct/shared/unallocated monthly cost using versioned causal drivers, exact rounding, discount/commitment policy and low/base/high forecast.

## Mandatory experiments

1. Attempt horizontal and vertical cross-tenant API, cache, database, queue, object-store and vector-search access; every path denies and audits safely.
2. Mutate/delete/reorder audit records and rewrite a local chain; prove detection through external signed checkpoint.
3. Put credential, diagnosis, email and card formats into requests, model output and errors; prove prohibited sinks remain clean.
4. Retry one committed ₹2,500 payment after response loss; prove one business effect. Reuse key with ₹2,600; prove conflict.
5. Inject bank timeout/UNKNOWN, later settlement and reconciliation; prove no duplicate debit and balanced append-only correction.
6. Submit failing Observation alongside valid Patient as FHIR batch and transaction; show correct partial versus atomic behavior.
7. Attempt ordinary override of missing-authority hard stop; deny. Override a model review with complete authorized evidence; audit.
8. Calculate FP16 weights/KV for the named 7B GQA model; compare predicted 4,096-token concurrency to measured runtime occupancy and explain difference.
9. Sweep batch/concurrency/precision; reject any throughput winner that violates p95, slice quality or memory safety.
10. Send one pooled tenant 10× load; prove quotas/fair scheduling preserve other tenants and bounded rejection recovers.
11. Fail a stamp and verify routing never crosses tenant/region/model-policy boundaries; recover/reconcile state.
12. Allocate a shared ₹1 example among three equal tenants and a ₹1,000 mixed-driver example; prove exact conservation and repeatability.
13. Forecast a model rollout, inject an untagged 15% cost anomaly, assign owner/root cause and verify normalized savings after repair.
14. Exercise clinical/payment/GPU/security incidents with appropriate containment, evidence, stakeholder escalation and recovery gates.

## Evidence bundle

- Versioned architecture, data-flow/threat/control map and authoritative obligation-to-evidence matrix.
- Passing isolation, policy, ledger/idempotency, FHIR, audit-chain, GPU capacity and cost-allocation tests.
- Raw load/accelerator benchmark data with hardware/software/config/input distribution and repeat statistics.
- Tenant placement, quota/fairness and zone/stamp failure results with per-tier SLOs.
- Immutable model/prompt/FHIR/ledger/audit identities and signed/checkpointed evidence.
- Reconciliation reports, balanced journal samples, UNKNOWN resolution and human-review/override trail.
- Data inventory, consent/access/deletion/break-glass evidence and negative sensitive-data scans.
- Billing-export lineage, allocation version, exact reconciliation, unit economics and low/base/high forecast.
- Incident runbooks/timelines for cross-tenant exposure, duplicate payment, wrong-patient data, GPU OOM and cost runaway.
- Forty-five-minute oral defense: interviewer injects one technical, one domain and one cost failure.

## Mastery gates

- Tenant identity is server-derived and enforced in every stateful/derived path, including failures and support.
- Security/privacy claims distinguish applicable binding requirements, proposals, contracts and guidance.
- Audit history is minimal and tamper-evident against a separately protected checkpoint; review is demonstrated.
- Money is exact/currency-aware; ledger stays balanced; timeouts never imply non-commit; reconciliation closes uncertainty.
- Clinical resources retain identity, version, status, terminology, time and provenance; ambiguous identity fails safely.
- Model advice never silently becomes denial or bypasses consent/authority; humans have capacity and accountable overrides.
- GPU estimates expose all assumptions; measured goodput/quality on exact target—not theoretical FLOPS—drives release.
- No tenant can monopolize queue, connections, storage, GPU compute or KV cache; overload is bounded and observable.
- Dedicated and pooled choices quantify security, reliability, scale, operations and fully loaded cost.
- Allocation conserves exact total, identifies unallocated cost and separates measured facts from policy estimates.
- Optimization cannot weaken isolation, safety, SLO/DR or evidence; savings are normalized and verified.
- Recovery proves tenant/model/policy/data/ledger correctness, not merely healthy processes.

## Rubric (100)

| Area | Points |
|---|---:|
| Security, privacy, tenant isolation and audit evidence | 25 |
| Healthcare/fintech workflow and correctness | 25 |
| GPU inference arithmetic, measurement and reliability | 20 |
| Quotas, fairness, stamps and failure containment | 15 |
| Allocation, unit economics, forecast and optimization | 10 |
| Reproducibility and oral defense | 5 |

Pass at 80+, with every mastery gate mandatory.
