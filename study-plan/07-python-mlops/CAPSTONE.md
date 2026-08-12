# Python and MLOps Capstone — Governed Claims Intelligence Platform

## Objective

Build and defend a production-grade claims-risk and claims-summary platform spanning a typed Python API, leakage-safe training, immutable ML lifecycle, online serving and a retrieval-assisted LLM path. The capstone passes only with executable evidence; a notebook, architecture diagram or dashboard alone is insufficient.

## Prerequisite gate

Complete all ten lessons first. Create an isolated Python environment and package; demonstrate syntax, mutability, collections, functions, exceptions, classes, iterators and context managers; run formatting, typing and unit tests; and load/validate a real CSV-shaped dataset. Calculate mean, variance, probability, a gradient step, confusion-matrix metrics and a train/validation/test split by hand or executable code. Finally, explain tokens, embeddings, attention, transformer inference and retrieval-augmented generation, including one groundedness and one access-control failure. This gate makes the advanced lifecycle depend on Python fluency and ML/GenAI foundations rather than framework recipes.

## Product contract

- A Java claims service calls a Python risk endpoint at 600 RPS peak; availability is 99.9%, p95 ≤150 ms and p99 ≤300 ms.
- A nightly snapshot scores 12 million open claims by 06:00 IST and can restart without duplicate business effects.
- Risk output is advisory routing, never an automatic denial. Every prediction records model/policy identities.
- The LLM summarizes only documents the authenticated analyst may read, cites source/version and cannot execute tools.
- Inputs can contain health and financial data. Raw prompts, claim IDs, email, payment-card data and credentials cannot enter general logs/tracking.
- Candidate gates: test AUC ≥0.90, Brier ≤0.11, TPR gap ≤0.05; serving p95 ≤150 ms at the stated load.
- Each tenant has a token/request quota; overload sheds work before unbounded queues form.

## Required build

1. Package Python using `src/` layout, pinned dependencies, static typing, structured exceptions and tests. Demonstrate process/thread/async choices for CPU and I/O work.
2. Implement FastAPI lifespan initialization, strict Pydantic request/response models, dependency-based auth, request IDs, deadlines and bounded concurrency. Prove cancellation does not leave committed partial work.
3. Create a dated claims dataset with explicit label availability, entity-grouped chronological train/validation/test splits and a baseline. Report confusion matrix, ROC-AUC, PR behavior, Brier/calibration, threshold economics, slices and uncertainty.
4. Produce a run manifest pinning code, data digest/as-of, split IDs, seed, feature schema, environment, artifact digest, metrics, gates and approval. Negative tests cover leakage, mutable aliases, artifact tampering and secret metadata.
5. Express snapshot → validate → features → split → train → evaluate → register as idempotent pipeline components with complete cache keys and transient/permanent retry policy.
6. Register an immutable candidate with signature, intended use, limitations, evaluation report and approval. Resolve aliases to numeric version/digest before deployment.
7. Load, verify and warm the model before readiness. Enforce schema, deadline, bounded queue, quota, version labels and safe errors.
8. Benchmark batch sizes/concurrency with p50/p95/p99, throughput, queue time, CPU/GPU/memory and useful SLO goodput. State exact hardware/runtime/data/method.
9. Build RAG ingestion/retrieval with document tenant/ACL/version metadata. Enforce authorization before context construction and treat retrieved content as untrusted.
10. Version model, system prompt, tools (none for this scenario), embedding/index/reranker and settings. Evaluate task success, citation correctness, groundedness, refusal/privacy, latency and cost on a protected set.
11. Shadow, then canary with sticky routing. Roll back a compatible model/preprocessing/feature/runtime bundle when an injected error or latency gate fails.
12. Monitor service, schema/freshness, scores, slices, token/cost/safety and delayed outcomes. Show why drift triggers investigation rather than automatic promotion.

## Mandatory experiments

1. Run all package/API/metrics/manifest/gateway tests from a clean environment.
2. Inject Decimal NaN, oversized output bounds, unknown fields and malformed auth; prove safe deterministic responses.
3. Add one entity to both train and test; the lifecycle gate must fail.
4. Modify one artifact byte; digest verification must prevent readiness/promotion.
5. Change feature code while data stays fixed; prove the complete cache key misses.
6. Attempt deployment through mutable `champion`; resolve it and record numeric version plus digest.
7. Send twice the admitted peak for five minutes; show bounded queue, intentional 429/503, stable accepted-traffic latency and recovery.
8. Compare batch 1/4/8/16 under the same load; select from measured SLO goodput rather than maximum raw throughput.
9. Include an unauthorized document and a prompt-injection document in retrieval; neither may grant content or authority.
10. Inject email and card-like values in input and generated output; prove redaction/blocking and verify logs contain neither.
11. Release a canary with >1% error for five minutes and ≥5,000 requests; prove automated stop/rollback and versioned evidence.
12. Delay outcome labels by 60 days; build cohort backfill and distinguish leading signals from mature performance.

## Evidence bundle

- Repository commit, dependency locks, build commands and passing test output.
- Dataset/label contract, snapshot digest, split IDs and leakage tests.
- Reproducible run manifest, pipeline graph/cache identities and registry record.
- Evaluation report with actual rows/counts, thresholds, slices, uncertainty and limitations.
- API/signature examples, load-test raw results, capacity calculation and overload traces.
- Prompt/RAG/index versions, ACL and injection tests, evaluation-set results and cost worksheet.
- Shadow/canary routing evidence, alert/rollback timeline and compatibility verification.
- Privacy threat model, access/retention policy and negative log/artifact scans.
- Runbooks for provider outage, quota exhaustion, model corruption, rollback and delayed-label degradation.
- Thirty-minute oral defense explaining trade-offs without relying on slides.

## Mastery gates

- A fresh engineer can reproduce the candidate from immutable inputs or explain a documented tolerance.
- Test data was not used for fitting, thresholding or repeated selection; temporal/entity leakage tests pass.
- Predictive improvement cannot waive latency, fairness, privacy, security or approval gates.
- Registry aliases never serve as final deployment/audit identities.
- Readiness requires verified artifact, compatible schema and completed warmup.
- Queues/concurrency/token budgets are bounded per tenant and overload is observable.
- Benchmark claims name environment/method and report tail latency plus useful throughput.
- Retrieval authorization happens before model context; model output/tool arguments are untrusted.
- Logs/tracking/evaluation artifacts contain no prohibited payloads or credentials.
- Monitoring joins versioned predictions to mature outcomes and does not equate drift with degradation.
- Rollback restores the compatible bundle and verifies business outcomes, not just HTTP health.
- All failures preserve tenant isolation and auditable model/policy identities.

## Rubric (100)

| Area | Points |
|---|---:|
| Python/API engineering and tests | 15 |
| ML evaluation and leakage control | 20 |
| Reproducibility, pipeline and registry governance | 20 |
| Serving performance, capacity and resilience | 20 |
| RAG/LLM evaluation, authorization and safety | 15 |
| Privacy, evidence quality and oral defense | 10 |

Pass at 80+, with every mastery gate mandatory.
