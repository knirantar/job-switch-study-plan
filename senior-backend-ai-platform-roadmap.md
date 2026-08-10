# Senior Backend + AI Platform/MLOps Engineer: 12-Week Switch Plan

Prepared for Nirantar Kulkarni | 12 weeks | 12 hours/week | India/remote | product, healthcare, fintech, and services

## 1. Role thesis and gap analysis

The strongest positioning is not “three unrelated roles.” It is: **Senior backend engineer who builds and operates production AI platforms.** This preserves five years of Java/Spring credibility while making Azure ML, AKS, Terraform, identity, networking, and production troubleshooting the differentiator.

Current postings validate this overlap. Senior backend roles repeatedly ask for service ownership, PostgreSQL, Kafka/queues, Kubernetes, observability, reliability, and architectural judgment. Senior AI-platform roles add Python APIs, Terraform/Helm, model serving, lifecycle/evaluation, GPU awareness, governance, and SLOs. Senior titles also expect design leadership and end-to-end ownership, not just tool familiarity.

### Evidence-based assessment

| Area | Assessment | Evidence / action |
|---|---|---|
| Java/Spring service development | Strong | 4+ years, REST, JPA, PostgreSQL, RabbitMQ, tests. Refresh Java 17/21 concurrency, performance, security, and failure semantics. |
| Production operations | Strong differentiator | Concrete 503, image-pull, RBAC, scaling, network and logging failures. Convert these into STAR stories with scale, diagnosis and prevention. |
| Azure ML / AKS / Terraform | Strong operationally | Good platform surface area; demonstrate architecture decisions, reusable modules, deployment safety, SLOs and cost—not merely “support.” |
| Distributed-system design | Rusty / high priority | Resume names microservices but does not prove consistency, partitioning, idempotency, backpressure, capacity or trade-off reasoning. |
| DSA and coding interviews | Rusty / screening risk | Must restore medium-level problem solving in Java; this is a gate even when unrelated to daily work. |
| Kafka | Genuine hands-on gap | Listed in skills but experience bullets prove RabbitMQ, not Kafka. Build a replayable, partitioned pipeline and learn consumer-group failure behavior. |
| Python engineering | Partial gap | Python is used for orchestration, but resume does not prove packaging, typing, async/concurrency, testing or high-performance API ownership. |
| Databases at scale | Partial gap | PostgreSQL/JPA named; indexing, query plans, transactions, locks, replicas and migrations are not demonstrated. |
| SRE/observability | Partial strength | Troubleshooting is credible; SLI/SLO/error budgets, tracing, alert quality, capacity and disaster recovery are missing. |
| ML fundamentals | Genuine gap for MLOps | Learn evaluation, leakage, drift, calibration, feature/data versioning and train/serve skew. Deep model research is not required. |
| Model/LLM serving | Partial gap | Azure endpoints and RAG are named, but batching, latency/throughput, GPU memory, canaries, evals, prompt/model versioning and cost controls are absent. |
| Senior-level influence | Under-signaled | No design ownership, mentoring, reviews, standards, cross-team decision, migration or roadmap outcomes are shown. Capture true examples. |

### Resume claims to reframe

- `Java 8-21` implies production depth across all versions. Use `Java (production: 11; familiar with 17/21)` unless 17/21 were used materially.
- Kafka, Redis, MongoDB, RAG, FAISS and OpenAI embeddings appear without experience evidence. Move unsupported items to `Exposure` or add a credible project with measurements.
- “Work on,” “contribute to,” “handle,” and “use” hide ownership. Replace them with the component, decision, scale, outcome and your role.
- “50% self-heal improvement” is ambiguous. State the baseline and metric: e.g. `automation success rate rose from 42% to 63%` or `self-healed incidents/month rose 50%`.
- Senior applications need scale. Recover requests/s, endpoint count, deployments/month, models/teams supported, availability, latency, recovery time, cloud cost, incident volume and change-failure rate. Never invent them.

## 2. Topic map and learning order

`Must` means interview- or job-critical for the combined role. `NTH` is useful specialization after the core.

| Major area | Ordered subtopics | Neighborhood |
|---|---|---|
| Coding foundations | 1. Complexity + core structures (Must) → 2. Patterns + concurrency (Must) | hashing, heaps, graphs; sliding window, binary search, thread safety |
| Java/Spring | 3. JVM/concurrency (Must) → 4. Spring/API correctness (Must) | memory model, GC, virtual threads; validation, security, resilience |
| Data | 5. PostgreSQL internals (Must) → 6. transactions/caching (Must) | B-trees, EXPLAIN, MVCC; isolation, locks, Redis, invalidation |
| Distributed systems | 7. failure semantics (Must) → 8. Kafka/eventing (Must) → 9. system design/capacity (Must) | timeouts, retries, idempotency; partitions, offsets, CDC; sharding, availability, backpressure |
| Cloud/platform | 10. containers/Kubernetes (Must) → 11. IaC/CI-CD/security (Must) → 12. SRE/observability (Must) | probes, resources, scheduling; Terraform state, supply chain, identity; SLOs, traces, incidents |
| Python + MLOps | 13. production Python/FastAPI (Must) → 14. ML evaluation/lifecycle (Must) → 15. serving/LLMOps (Must) | typing, async, GIL; leakage, drift, registry; batching, canaries, RAG eval |
| Regulated systems | 16. privacy/security/audit (Must for target industries) | threat modeling, encryption, retention, lineage |
| Advanced platform | 17. GPU/inference optimization (NTH) → 18. multi-tenancy/FinOps (NTH) | CUDA memory, quantization; quotas, isolation, chargeback |

## 3. Depth treatment

### 1. Complexity and core data structures — Must

**Why / failure boundary.** Complexity predicts growth, not stopwatch time. Hash maps buy expected O(1) lookup with memory and collision costs; heaps maintain only the extreme in O(log n); graphs express dependencies. Big-O breaks as a complete model when cache locality, allocation, I/O, skew or adversarial hashes dominate.

**Concrete example.** Deduplicating 10 million 16-byte request IDs with a Java `HashSet` is not 160 MB: object/header/table overhead can push it toward hundreds of MB. A Bloom filter sized by `m=-n ln(p)/(ln2)^2` needs about 95.9 million bits (11.4 MiB) for n=10M and p=1%, with about 7 hashes, but admits false positives.

**Interview problems and worked answers.** (1) Top 100 endpoints from 20M log rows: count with a map, retain 100 entries in a min-heap; O(n log 100), O(u+100). If IDs do not fit memory, partition or use approximate heavy hitters. (2) Detect a dependency cycle: DFS with white/gray/black states; an edge to gray is a cycle, O(V+E). Kahn’s algorithm instead removes zero-indegree nodes; fewer than V removed means a cycle.

**Mistakes.** Memorizing complexity without stating n; sorting O(n log n) when a heap gives O(n log k); ignoring duplicate keys, empty input, overflow and memory.

**Primary sources.** Cormen et al., *Introduction to Algorithms*, 4th ed.; Sedgewick & Wayne, *Algorithms*, 4th ed.; Java `HashMap` and `PriorityQueue` API documentation.

### 2. Coding patterns and safe concurrency — Must

**Why / failure boundary.** Patterns compress search: sliding windows work when adding/removing elements updates a monotonic constraint; binary search works on a monotonic predicate; BFS gives shortest paths only in unweighted graphs. Concurrency fails when shared state lacks an ordering relationship.

**Concrete example.** For rate samples `[120,180,90,210,160,130]` and a 3-second window, sums are 390, 480, 460, 500; maximum is 500. Update in O(1) by adding the new value and subtracting the expired value. For a bounded executor with 32 workers and 1,000 queue slots, overload must reject or shed; an unbounded queue converts overload into latency and heap growth.

**Questions.** (1) Longest substring without repeats: map character→last index; move left to `max(left,last+1)`; O(n). (2) Why can `counter++` lose updates? It is read-modify-write; two threads can read the same value. Use `AtomicLong` or locking; `LongAdder` improves high-contention metrics but `sum()` is not a linearizable snapshot.

**Mistakes.** Applying sliding window to non-monotonic constraints; using parallel streams for blocking I/O; confusing thread safety with atomicity of a multi-step business operation.

**Sources.** Goetz et al., *Java Concurrency in Practice*; JLS §17; Java `java.util.concurrent` package specification.

### 3. JVM performance and concurrency — Must

**Why / failure boundary.** The JVM trades warm-up and managed memory for portability and optimization. The memory model defines visibility/order; collectors reclaim unreachable objects, not “unused business data.” Performance fails through allocation rate, retained heap, blocking, pool starvation, lock contention or long-tail pauses.

**Concrete example.** Little’s Law: at 2,000 requests/s and 100 ms average time, concurrency is 200. If a downstream call takes 500 ms, the same rate needs ~1,000 in-flight operations. A 100-thread pool cannot sustain it without queueing. Virtual threads make blocking cheaper but do not increase database connections or downstream capacity.

**Questions.** (1) `volatile` vs `synchronized`: volatile gives visibility and ordering for reads/writes, not compound atomicity; synchronized adds mutual exclusion and happens-before. (2) CPU is 25% but latency is high: inspect thread dumps, pool queues, downstream latency, locks and GC; CPU headroom does not rule out blocked threads. (3) Size a pool: CPU-bound near cores; blocking workloads use measured wait/service ratio but cap by dependencies.

**Mistakes.** Tuning GC before measuring; treating virtual threads as a rate limiter; benchmarking without JMH warm-up/forks; catching `OutOfMemoryError` as recovery.

**Sources.** JLS §17; OpenJDK JEP 444 (Virtual Threads); OpenJDK JEP 439 (Generational ZGC); Oracle Java Flight Recorder docs; Shipilev, JMH samples.

### 4. Spring Boot and API correctness — Must

**Why / failure boundary.** APIs are contracts across independently deployed systems. Correctness includes validation, authorization, idempotency, compatible evolution and bounded failure. Abstractions break through hidden transactions, N+1 queries, proxy/self-invocation behavior and careless retries.

**Concrete example.** `POST /payments` accepts `Idempotency-Key`; persist `(tenant_id,key)` under a unique constraint with request hash and response. A retry with the same body returns the stored response; a different body returns 409. Use 400 for malformed input, 401 unauthenticated, 403 unauthorized, 409 state conflict, 422 semantically invalid input, 429 throttled.

**Questions.** (1) Prevent duplicate payment on timeout: idempotency record and unique business key; transactionally write payment + outbox. (2) N+1: listing 100 orders followed by 100 customer selects; solve with fetch join/entity graph/batch loading or projections, then verify SQL and cardinality. (3) Retry policy: only transient failures and idempotent operations; exponential backoff with jitter, deadline and attempt cap.

**Mistakes.** Putting `@Transactional` on a private/self-invoked method; retrying 4xx; exposing entities as API models; trusting JWT authentication without resource authorization.

**Sources.** Spring Framework transaction docs; Spring Security reference; RFC 9110 (HTTP semantics); RFC 9457 (Problem Details); OWASP API Security Top 10.

### 5. PostgreSQL indexing and query plans — Must

**Why / failure boundary.** Indexes trade write/storage cost for selective access. Composite B-tree order matters; the planner chooses based on statistics and estimated cost. Indexes fail to help when predicates are unselective, functions prevent matching, data is skewed, or random heap reads cost more than a scan.

**Concrete schema.** `payments(id bigint, tenant_id uuid, status text, created_at timestamptz, amount_cents bigint)`. For `WHERE tenant_id=? AND status='FAILED' ORDER BY created_at DESC LIMIT 50`, use a partial index: `CREATE INDEX ON payments(tenant_id, created_at DESC) WHERE status='FAILED';`. Verify with `EXPLAIN (ANALYZE, BUFFERS)`; compare estimated vs actual rows and buffer hits/reads.

**Questions.** (1) Why is an index ignored? Low selectivity, stale stats, type cast/function, leading-column mismatch or small table. (2) Keyset pagination: `WHERE tenant_id=? AND (created_at,id)<(?,?) ORDER BY created_at DESC,id DESC LIMIT 50`; stable and avoids walking a large OFFSET. (3) Zero-downtime index: `CREATE INDEX CONCURRENTLY`; it takes longer and cannot run inside a transaction block.

**Mistakes.** Indexing every column; using `SELECT *`; trusting estimated cost without actual buffers; missing a deterministic pagination tie-breaker.

**Sources.** PostgreSQL manuals: Indexes, Using EXPLAIN, Planner Statistics, MVCC and `CREATE INDEX`.

### 6. Transactions, locks and caching — Must

**Why / failure boundary.** Transactions protect invariants under concurrency; isolation determines which anomalies are excluded. Caches reduce latency/load but duplicate state and create invalidation races. A database transaction cannot atomically include Kafka or Redis without a protocol.

**Concrete example.** Two withdrawals reading ₹1,000 can both approve ₹700. Use `UPDATE account SET balance=balance-700 WHERE id=? AND balance>=700`; affected rows 1 means success. For cross-system publication, commit domain row and outbox row together; relay outbox to Kafka at least once; consumer deduplicates by event ID.

**Questions.** (1) Lost update prevention: atomic conditional update, optimistic version, or row lock. (2) Cache-aside race: writer commits then deletes cache; a concurrent reader can repopulate stale data. Use versioned values, short TTL, ordered invalidation/CDC, or accept bounded staleness. (3) Serializable failure: retry the whole transaction on serialization error with a cap.

**Mistakes.** Assuming `READ COMMITTED` prevents business races; holding locks during remote calls; using distributed locks without fencing tokens; treating TTL as correctness.

**Sources.** PostgreSQL Transaction Isolation and Explicit Locking docs; Kleppmann, *Designing Data-Intensive Applications*; Redis distributed-lock documentation (including safety caveats).

### 7. Distributed failure semantics — Must

**Why / failure boundary.** Networks can delay, duplicate, reorder or lose messages; timeout means “unknown,” not “failed.” Exactly-once effects require idempotency and atomic state transitions, not a marketing flag.

**Concrete example.** A client deadline is 800 ms. Budget 50 ms ingress, 600 ms dependency, 50 ms response and 100 ms reserve. Three sequential 300 ms retries cannot fit. Exponential waits of 50/100 ms with full jitter reduce synchronization, but attempts share the original deadline. A circuit breaker limits repeated calls; bulkheads isolate resource pools.

**Questions.** (1) Payment timed out: query by idempotency key before retry; never infer failure. (2) At-least-once consumer: store processed event ID and business mutation in one DB transaction. (3) CAP: under a partition, choose whether each operation rejects/waits for consistency or serves potentially stale data; CAP is not a normal-mode latency slogan.

**Mistakes.** Nested retries at every layer; no jitter/deadline; assuming ordering across partitions; calling a DLQ a recovery strategy without replay tooling.

**Sources.** RFC 9110; AWS Builders’ Library, “Timeouts, retries, and backoff with jitter”; Kleppmann, DDIA; Google SRE Book.

### 8. Kafka and event-driven design — Must

**Why / failure boundary.** Kafka is a partitioned replicated log. Partition key controls per-key order and parallelism; consumer groups divide partitions, and offsets represent progress, not business completion. It breaks through skewed keys, slow consumers, oversized messages, unsafe commits and incompatible schemas.

**Concrete example.** At 12,000 events/s and 1,000 events/s sustainable consumption per partition, 12 partitions are the mathematical floor; use headroom, e.g. 18–24, after measuring broker/storage limits. A group can actively use at most one consumer per partition. If average event size is 2 KB, raw ingress is ~24 MB/s before replication; RF=3 writes roughly 72 MB/s across replicas.

**Questions.** (1) Preserve account order: key by account ID; order is only within its partition. (2) Avoid loss: process then commit offset; duplicates remain possible, so dedupe. Kafka transactions can atomically consume and produce Kafka records, not update an arbitrary database. (3) Rebalance storm: check session/max-poll settings, slow processing, GC and membership; use cooperative rebalancing/static membership and separate polling from work carefully.

**Mistakes.** More consumers than partitions; random keys when order matters; auto-commit before processing; treating retention as a queue deletion policy; no schema compatibility plan.

**Sources.** Apache Kafka Design and Consumer Configuration docs; KIP-447; Confluent Schema Registry compatibility docs; Richardson, *Microservices Patterns* (outbox).

### 9. Capacity-driven system design — Must

**Why / failure boundary.** Design converts product constraints into data flow, state ownership and failure behavior. Numbers expose impossible assumptions. Begin with traffic, payload, latency, availability, consistency, retention, privacy and cost.

**Concrete case.** 10M registered users, 1M DAU, 20 requests/user/day → 20M/day ≈231 average RPS. At 10× peak, design for ~2,300 RPS. With 4 KB responses, peak egress is ~9.2 MB/s. Retaining 2 KB/request audit records for 90 days at 20M/day is 3.6 TB raw before indexes/replication.

**Questions.** (1) Design notification service: API writes notification + outbox, Kafka partitions by recipient, channel workers apply provider-specific limits, dedupe keys, retries/DLQ, preference checks, delivery state and SLOs. (2) Hot key: shard the logical key, cache/read-replica for reads, serialize writes or isolate the tenant. (3) Multi-region: define RPO/RTO; active-passive is simpler, active-active requires conflict/ownership strategy.

**Mistakes.** Drawing boxes before requirements; saying “Kafka for scale” without throughput/order; omitting overload and degradation; conflating backup with disaster recovery.

**Sources.** Kleppmann, DDIA; Google SRE Book; Nygard, *Release It!*; AWS and Azure architecture reliability guidance.

### 10. Containers and Kubernetes — Must

**Why / failure boundary.** Containers package processes; Kubernetes reconciles declared state. Requests drive scheduling and HPA utilization; limits constrain runtime. Probes have distinct meanings. Failures arise from bad sizing, slow startup, dependency-coupled probes, rollout capacity, DNS/network policy and node pressure.

**Concrete example.** Six pods each request 500m CPU require 3 cores of schedulable capacity even if idle. If target CPU is 70% and observed average is 140%, HPA’s basic ratio suggests doubling replicas. `startupProbe` protects slow boot; `readinessProbe` removes traffic; `livenessProbe` restarts a stuck process. A liveness check must not fail merely because PostgreSQL is briefly unavailable.

**Questions.** (1) `Pending`: inspect events, requests vs allocatable, taints/tolerations, affinity and PVC zone. (2) `ImagePullBackOff`: image/tag, ACR DNS/private link, managed identity/workload identity, secret and node egress. (3) Zero-downtime rollout: readiness, surge capacity, graceful termination, preStop only if needed, connection draining, PDB and backward-compatible schema.

**Mistakes.** No requests; equal tiny request/limit causing throttling; `latest` tags; secrets in images/env dumps; liveness calling every dependency.

**Sources.** Kubernetes docs: Resource Management, Probes, Deployments, HPA, PDB, Scheduling; OCI Image Specification.

### 11. Terraform, delivery and cloud security — Must

**Why / failure boundary.** IaC makes infrastructure reviewable and repeatable; state maps configuration to real resources. Delivery must promote immutable artifacts and separate build from deploy. Security should prefer short-lived workload identity and least privilege.

**Concrete example.** Build image once as `registry/app@sha256:...`; sign/scan it; deploy that digest through dev→stage→prod. Terraform remote state uses locking and restricted access; plans run on PR, apply on protected branch/environment. Split state by blast radius, not by arbitrary folder size.

**Questions.** (1) Secret leaked into state: rotate it first, restrict state, remove from config/state carefully, adopt Key Vault reference/workload identity. (2) Module change recreates production endpoint: inspect plan, lifecycle and provider semantics; redesign migration rather than blindly applying `prevent_destroy`. (3) Safe DB migration: expand schema, deploy dual-compatible code/backfill, switch reads, contract later.

**Mistakes.** `terraform apply` from laptops; giant state; mutable tags; permanent service-principal secrets; mixing infrastructure rollback with irreversible data rollback.

**Sources.** HashiCorp Terraform State and Module docs; SLSA specification; GitHub Actions security hardening; Azure Workload Identity and Key Vault docs; NIST SSDF.

### 12. SRE and observability — Must

**Why / failure boundary.** Observability lets you ask new questions from telemetry; reliability uses user-visible SLIs and explicit objectives. Average latency hides tails. Alerts should predict user harm and demand action.

**Concrete example.** 99.9% monthly availability permits about 43.2 minutes of unavailability in a 30-day month. A 99.9% SLO with 99.5% actual success consumes error budget at 5× the sustainable rate. Track request rate, errors, duration and saturation; propagate trace IDs across HTTP, Kafka and batch jobs, while controlling high-cardinality labels.

**Questions.** (1) 503 spike: correlate ingress/service/downstream metrics, saturation, recent deploys and traces; distinguish no-ready-pods, overload and dependency failure; mitigate, then prevent. (2) Alert: multi-window burn-rate alerts outperform static CPU alarms for availability SLOs. (3) High latency with normal average: inspect p95/p99, per-tenant/routes, queue time and dependency spans.

**Mistakes.** Logging secrets/PHI; user ID as a metrics label; alerting every exception; SLO defined on pod uptime rather than successful user operations.

**Sources.** Google *Site Reliability Engineering* and *SRE Workbook*; OpenTelemetry specification; Prometheus instrumentation and alerting practices.

### 13. Production Python and FastAPI — Must

**Why / failure boundary.** Python’s ergonomics make orchestration fast, but production quality requires types, environments, tests, cancellation, resource bounds and profiling. `async` improves I/O concurrency only when libraries are non-blocking; CPU work still blocks the event loop and the GIL constrains CPU-bound threads.

**Concrete example.** At 500 RPS and 200 ms downstream time, Little’s Law gives ~100 concurrent calls. An async service can hold them efficiently, but a downstream pool of 20 connections creates queueing. Use timeouts/semaphores and expose queue time. Move heavy CPU inference to native libraries/processes or a model server.

**Questions.** (1) `async def` calls `requests.get`: it blocks the event loop; use an async client or thread offload with bounds. (2) Threads vs processes: threads for blocking I/O and C extensions that release GIL; processes for Python CPU work, with serialization/memory cost. (3) Package service: `pyproject.toml`, locked dependencies, typed domain boundary, pytest, lint/type check, multi-stage image and non-root user.

**Mistakes.** Unbounded `asyncio.gather`; background tasks with no durability; global clients never closed; believing more workers always improve throughput.

**Sources.** Python Language Reference and `asyncio` docs; PEP 8, 484 and 517/518; FastAPI deployment docs; pytest documentation.

### 14. ML fundamentals and lifecycle — Must for MLOps

**Why / failure boundary.** MLOps engineers need to recognize whether a model and its data are valid, reproducible and safe to promote. Accuracy fails under imbalance; random splits leak future/entity information; drift may not imply performance loss, and performance loss may occur without obvious input drift.

**Concrete example.** For 10,000 cases with 100 positives, a model predicting all negative is 99% accurate and useless. If TP=70, FP=30, FN=30, precision=70%, recall=70%, F1=70%. A threshold change trades precision for recall; choose it using business cost and calibration. Split claims by time/patient, not random rows, to prevent leakage.

**Questions.** (1) Offline AUC improves but production worsens: check leakage, train/serve skew, population shift, threshold/calibration, feature freshness and logging. (2) Drift monitor: schema/null/range checks, distribution metrics (PSI/KS cautiously), delayed-label performance and segment analysis. (3) Reproducibility: version code, data snapshot, environment, parameters, features and artifacts; record lineage in registry.

**Mistakes.** Monitoring only model-server health; retraining automatically on any drift; comparing experiments on different splits; treating a registry as artifact storage only.

**Sources.** scikit-learn model evaluation and common pitfalls docs; Sculley et al., “Hidden Technical Debt in Machine Learning Systems”; MLflow Tracking and Model Registry docs; Google Rules of ML.

### 15. Model serving and LLMOps — Must

**Why / failure boundary.** Serving balances latency, throughput, cost and quality. Batching improves accelerator utilization but adds queue delay; autoscaling reacts after load arrives; cold starts and model downloads can dominate. LLM systems add stochastic quality, prompt/model versioning, retrieval and safety.

**Concrete example.** A 7B-parameter model requires about 14 GB just for FP16 weights, roughly 7 GB at 8-bit or 3.5 GB at 4-bit, before KV cache/runtime overhead. If prompt+output averages 2,000 tokens and a model serves 100 tokens/s for one stream, naïve service time is ~20 s; continuous batching changes throughput but not the need for queue/admission control.

**Questions.** (1) Canary model: route 5%, compare error, p95/p99, cost/request and task-quality metrics with guardrails; retain fast rollback and schema compatibility. (2) RAG quality: separate retrieval recall@k/MRR from answer faithfulness/relevance; build a versioned labeled set and inspect slices. (3) 503 during burst: determine capacity vs readiness/cold start/quota; add queue bounds, warm capacity, faster images/models, predictive scaling and graceful shedding.

**Mistakes.** Autoscaling only on CPU for GPU/token workloads; evaluating LLMs with a few anecdotes; logging prompts containing PHI; deploying model and prompt changes without independent versions.

**Sources.** Azure ML managed online endpoint, autoscaling and safe-rollout docs; KServe and NVIDIA Triton docs; MLflow deployment docs; Lewis et al., “Retrieval-Augmented Generation”; NIST AI RMF.

### 16. Security, privacy and auditability — Must for healthcare/fintech

**Why / failure boundary.** Security preserves confidentiality, integrity and availability; regulated systems also require purpose limitation, traceability, retention and defensible access. Network isolation alone does not authorize a user or workload.

**Concrete design.** Use OIDC/workload identity → scoped role → Key Vault; encrypt in transit/at rest; tokenize direct identifiers; separate tenant keys/data boundaries; immutable audit events record actor, action, resource, decision and correlation ID—but not secrets or raw clinical text. Set retention and deletion workflows by data class.

**Questions.** (1) Tenant isolation: tenant context from verified identity, server-side row/filter enforcement, per-tenant quotas and tests; never trust a body/header tenant ID alone. (2) Prompt injection: treat retrieved/tool content as untrusted, constrain tool permissions, validate arguments, isolate data and require confirmation for high-impact actions. (3) Incident: contain, preserve evidence, rotate/revoke, assess scope, notify through policy, remediate and test.

**Mistakes.** PHI/PII in logs and traces; broad managed-identity roles; secrets in Terraform state; unaudited break-glass access; claiming “HIPAA compliant” for a component without system controls.

**Sources.** OWASP ASVS and API Security Top 10; NIST SP 800-53 and AI RMF; Microsoft Azure Well-Architected Security guidance; applicable organization/legal guidance for HIPAA, India DPDP and payment standards.

### 17. GPU and inference optimization — Nice to have

**Why / failure boundary.** GPU serving is constrained by weights, KV cache, memory bandwidth, compute and scheduler. Quantization trades memory/speed for possible quality loss; batching trades latency for throughput.

**Example/questions.** Estimate memory before selecting hardware; benchmark p50/p99 time-to-first-token, inter-token latency, tokens/s and quality on realistic sequence lengths. If OOM occurs, reduce batch/sequence, quantize, use tensor parallelism or a smaller model; verify fragmentation and KV-cache use. Do not compare vendor peak FLOPS to application throughput.

**Sources.** NVIDIA Triton and TensorRT-LLM docs; vLLM paper/docs; CUDA programming guide.

### 18. Multi-tenancy and FinOps — Nice to have

**Why / failure boundary.** Shared platforms improve utilization but create noisy-neighbor, data-isolation and chargeback risks. Unit economics drive sustainable capacity.

**Example/questions.** Attribute compute-seconds, GPU-seconds, tokens, storage and egress by tenant/model/version. Apply quotas, priority classes, admission control and separate pools for strict isolation. A ₹300/hour endpoint at 20% utilization has an effective busy-hour compute cost of ₹1,500 before overhead; consolidation or scale-to-zero may help, subject to cold-start SLO.

**Sources.** Kubernetes multi-tenancy and ResourceQuota docs; FinOps Foundation framework; Azure Cost Management docs.

## 4. Twelve-week sequence (144 hours)

Use six 2-hour sessions weekly: 4h concepts, 4h implementation, 2h interview drills, 2h review/story work. Each week ends with a timed 45-minute coding problem and a 45-minute design explanation recorded aloud.

| Week | 12-hour focus | Exit evidence |
|---|---|---|
| 1 | DSA: arrays/maps, stacks, heaps, complexity; Java 17/21 refresh | 12 problems; explain 4 trade-offs without notes |
| 2 | Trees/graphs, binary search, concurrency/JMM, profiling | 10 problems; JFR/thread-dump diagnosis lab |
| 3 | HTTP/API contracts, Spring transactions/security/resilience/testing | Idempotent payments API with integration tests |
| 4 | PostgreSQL plans/indexes/MVCC/locks; Redis/cache patterns | EXPLAIN report on ≥1M generated payment rows |
| 5 | Distributed failures, outbox, consistency, capacity estimation | Design notification platform; failure matrix |
| 6 | Kafka partitions/groups/offsets/schema/replay | Kafka payment-event service with dedupe and replay |
| 7 | Kubernetes scheduling/resources/probes/HPA/rollouts/networking | Deploy service; deliberately break and diagnose 5 cases |
| 8 | Terraform modules/state; CI/CD; identity, secrets, supply chain | PR plan + signed immutable image + staged deployment |
| 9 | SLI/SLO, OpenTelemetry, alerts, incident response/DR | Dashboard, 2 burn-rate alerts, runbook and postmortem |
| 10 | Python typing/async/FastAPI/testing; ML metrics/leakage/drift | Async inference gateway + evaluation notebook/script |
| 11 | Azure ML serving, canary/shadow, autoscaling, RAG evaluation | Design AI endpoint platform and quality gate |
| 12 | Regulated design, full mocks, resume/stories; NTH GPU/FinOps | 2 coding mocks, 2 design mocks, 6 STAR stories |

Minimum weekly score: coding solution correct in 35 minutes; design covers requirements, numbers, data, APIs, failure, security and operations in 40 minutes; quiz ≥80%. If below, replace the next week’s NTH time with remediation.

## 5. Practice artifacts

### Project A — Regulated payment-event platform

Generate 1,000,000 payment rows with: 100 tenants (Zipf-skewed), 1% duplicate idempotency keys, 2% failures, ₹1–₹200,000 amounts, timestamps over 30 days. Build Spring Boot + PostgreSQL + Kafka services:

1. `POST /payments` with validation, idempotency and optimistic/atomic balance protection.
2. Transactional outbox; publisher can crash after publish but before marking sent.
3. Consumer writes ledger effects exactly once at the database boundary using event-ID dedupe.
4. Kafka key is account ID; demonstrate ordering and a hot-account partition.
5. OpenTelemetry traces and RED metrics; define 99.9% success and p95 <300 ms SLOs.
6. Load test at 250 average and 1,000 peak RPS. Report throughput, p50/p95/p99, errors, pool/queue saturation and DB plans—not fabricated targets.

**Reference solution.** `payment` and `outbox` commit together. Unique `(tenant_id,idempotency_key)` plus request hash controls retries. Relay publishes keyed events with stable `event_id`. Ledger consumer transaction inserts `processed_event(event_id)` and ledger mutation; duplicate unique violation becomes success/no-op. Partition only guarantees per-account order. Bounded pools, deadlines and 429/503 shedding prevent collapse. Audit fields exclude sensitive payloads. Deploy immutable image to Kubernetes with readiness/startup probes, resources, HPA on CPU plus queue/lag signal, PDB and backward-compatible migrations.

### Project B — AI endpoint control plane

**Prompt.** Design a multi-tenant platform for 40 teams, 300 registered models and 60 online deployments. Baseline is 80 RPS; burst is 800 RPS for 10 minutes. p95 gateway overhead <100 ms excluding inference; control-plane availability 99.9%; sensitive healthcare prompts; private networking; canary and rollback; per-team cost allocation.

**Reference answer.** Separate control and data planes. Control API authenticates workload/user, authorizes tenant/project, validates deployment spec and writes desired state/version to durable metadata. Reconciler performs idempotent Azure ML/AKS operations through a work queue with per-resource state machine and retry classification. Data plane uses gateway→policy/routing→endpoint, bounded concurrency and admission control. Registry pins model, image, environment and prompt/config digests. Release uses shadow where safe, then 5/25/100% canary with latency/error/quality/cost gates and instant route rollback. Scale on concurrency/queue or inference metrics, retain warm minimum for the burst SLO. Use managed/workload identity, Key Vault, private endpoints, tenant-scoped audit, content redaction and strict retention. Telemetry includes deployment-state age, reconciliation failure, ready capacity, queue, 429/503, p95/p99, model quality and cost per tenant. DR explicitly states metadata RPO/RTO and recreation process.

### Focused drills with solutions

1. **Kafka lag:** 24 partitions, 12 consumers, each 400 events/s; ingress 6,000/s. Capacity is 4,800/s, so lag grows 1,200/s or 72,000/min. Raise sustainable per-consumer throughput, add consumers up to 24, or reduce ingress; merely increasing `max.poll.records` does not create processing capacity.
2. **Availability composition:** three mandatory serial dependencies each at 99.9% yield approximately `0.999³ = 99.7003%`, before your service. Remove unnecessary synchronous dependencies or improve/fallback; retries do not erase correlated outages.
3. **Cache hit economics:** 4,000 RPS, 90% hit rate means DB sees ~400 RPS (plus fills/writes). At 70% hits it sees ~1,200 RPS—3× more—so alert on hit rate and DB saturation together.
4. **Partition storage:** 20,000 events/s × 1.5 KB × 86,400 s × 7 days ≈18.1 TB raw decimal; replication factor 3 ≈54.4 TB before overhead/compaction. Validate retention and broker throughput.
5. **ML threshold:** TP=180, FP=60, FN=20 gives precision 75%, recall 90%, F1≈81.8%. In clinical screening, quantify the relative cost of 20 misses versus 60 reviews before selecting threshold.

## 6. Resume rewrites and interview narrative

Use these only after replacing brackets with verified facts.

1. **Headline:** `Backend & AI Platform Engineer | Java/Spring Boot, Python, Azure ML, AKS, Terraform | Production Reliability`.
2. **Current-role ownership:** `Built and operated deployment orchestration for [N] Azure ML online/batch endpoints used by [N] teams, automating [provisioning/deployment] with Python/Azure SDK and reducing [lead time/failure rate] from [A] to [B].`
3. **Reliability:** `Diagnosed and remediated production 503s, scaling delays, ACR image-pull and managed-identity/private-network failures; introduced [alert/runbook/design change], improving [availability/MTTR/deployment success] by [verified result].`
4. **Platform architecture:** `Developed reusable AKS/Terraform/GitHub Actions platform components for AI-agent workloads, enforcing managed identity, Key Vault and private networking across [N environments/teams].`
5. **Backend impact:** `Designed Spring Boot/PostgreSQL/RabbitMQ automation services for SAP operations, cutting median incident MTTR by ~90% and response time by 70% across [N incidents/month or workflows]; added [idempotency/tests/observability] to sustain [verified reliability].`

Add a two-project section only if the projects above are genuinely implemented and linkable. Replace a long flat skills inventory with `Production`, `Working knowledge`, and optionally `Exposure`; this raises trust.

### Why I am switching / why this role

“I began in Java backend engineering, building Spring Boot services and event-driven automation for enterprise operations. That work taught me to care about failure handling and measurable outcomes—we reduced MTTR substantially by turning recurring operational work into reliable software. In my current healthcare assignment I moved closer to the platform layer, operating Azure ML endpoints and AKS-based AI workloads and solving real production issues across scaling, identity, private networking and observability. I found that the work I enjoy most is the intersection: designing dependable backend systems and giving teams a secure, repeatable way to deploy AI capabilities. I’m now looking for a senior backend or AI-platform role where I can own those systems end to end—from API and data design through deployment, SLOs and incident learning—while deepening distributed-systems and model-lifecycle engineering.”

### Six stories to prepare

1. A 503/scaling incident: signal → hypotheses → evidence → mitigation → permanent prevention.
2. Image pull/private networking/identity failure across team boundaries.
3. A design trade-off you owned, including rejected alternatives.
4. The 90% MTTR result with baseline, measurement window and your exact contribution.
5. A risky deployment or migration made safe.
6. A disagreement or ambiguous problem where you influenced without authority.

## 7. Primary-source shelf

- Java: JLS §17; OpenJDK JEP 444; Java concurrency APIs; JMH and JFR documentation.
- Backend: Spring Framework/Security docs; RFC 9110; RFC 9457; OWASP API Security Top 10.
- Data: PostgreSQL manuals for indexes, EXPLAIN, MVCC, locks and isolation; Redis docs.
- Messaging: Apache Kafka design/configuration docs and KIPs; schema compatibility docs.
- Platform: Kubernetes official docs; HashiCorp Terraform docs; SLSA; NIST SSDF.
- Reliability: Google SRE Book/Workbook; OpenTelemetry spec; Prometheus best practices.
- ML/MLOps: scikit-learn evaluation/pitfalls; MLflow docs; Sculley et al. (2015); Google Rules of ML.
- Serving: Azure ML managed endpoint and autoscaling docs; KServe; Triton; vLLM.
- Core books: Kleppmann, *Designing Data-Intensive Applications*; Nygard, *Release It!*; Goetz et al., *Java Concurrency in Practice*; Cormen et al., *Introduction to Algorithms*.

## 8. Application strategy

Run two resume variants, not three: **Senior Backend Engineer** (Java/data/distributed systems first, AI platform as differentiator) and **Senior AI Platform/MLOps Engineer** (Azure ML/AKS/Terraform/reliability first, backend as foundation). At five-plus years, apply selectively to Senior roles whose scope matches your ownership, but also to strong SDE-2/Backend Engineer II/Platform Engineer roles; some product companies calibrate Senior at 7–8+ years. Service-company titles are less standardized, so evaluate the work and interview bar, not the title.

Start applications in week 5 rather than waiting until week 12: 8–12 well-matched applications/week, 3 referral conversations/week and one mock interview/week. Track role family, JD gaps, screen outcome, coding/design feedback and story weakness; update the study allocation every Sunday from evidence.
