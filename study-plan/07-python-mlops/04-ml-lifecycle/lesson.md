# ML Lifecycle: From Reproducible Experiment to Governed Production Model

**Parent:** 07 — Python and MLOps  
**Target level:** Senior Backend / AI Platform / MLOps Engineer  
**Study time:** 3–4 hours plus the executable lab  
**Lab:** [`lab/`](lab/) — a dependency-free run-manifest validator with six tests

## 1. FOUNDATIONS

### Why an ML lifecycle exists

A conventional release is mostly a function of source code and configuration. An ML release is a function of at least **code, data, features, parameters, environment and randomness**. If any one changes, the produced model can change even though `train.py` has not. That extra state is why a notebook that once reported AUC 0.918 is not yet a production asset.

The lifecycle is the controlled path from a business decision to data, experiment, validated artifact, deployment, observation, retirement and—when justified—retraining. It answers four questions:

1. **Can we reproduce it?** Identify the exact source commit, input snapshot, environment, split and seed.
2. **Should we release it?** Prove predictive, operational, fairness, privacy and security gates on data not used for fitting or tuning.
3. **Can we operate it?** Package a typed contract, deploy gradually, observe inputs/outputs/outcomes and roll back.
4. **Can we explain it later?** Preserve lineage and approval evidence for an incident, audit or adverse decision.

Without this discipline, a mutable `latest.csv` can silently alter training; a feature calculated with tomorrow's information can inflate offline metrics; an engineer can tune repeatedly against the test set; an unpinned library update can change predictions; or a model can remain technically healthy while real-world outcomes deteriorate.

The field grew from reproducible scientific computing, software configuration management and continuous delivery. Hidden Technical Debt in Machine Learning Systems (Sculley et al., 2015) described feedback loops, undeclared consumers and data dependencies that ordinary code review misses. ML Test Score (Breck et al., 2017) converted many of those risks into tests. MLOps applies DevOps ideas, but **CI** now validates code, data and models; **continuous training (CT)** may build candidates; and **continuous delivery/deployment (CD)** promotes only approved, immutable artifacts.

### Vocabulary, in context

An **experiment** groups comparable investigations. A **run** is one execution with parameters, metrics, artifacts and provenance. An **artifact** is an output such as weights, tokenizer, preprocessing graph, evaluation report or container. **Metadata** describes artifacts and executions; **lineage** connects an output to every material input and transformation. A **data asset/snapshot** is a named, versioned dataset. A **feature** is a model input derived from raw observations, while a **feature store** coordinates definitions and retrieval for offline training and online inference.

A **pipeline** is a directed acyclic graph (DAG) of components with typed inputs and outputs. An **orchestrator** schedules those components and manages retries, caching and state. A **model signature** declares input/output names, types and shapes. A **registry** catalogs immutable model versions and governance metadata. A mutable **alias** such as `champion` points to a version; version 17 itself must not change.

**Training-serving skew** means feature computation or dependencies differ between fitting and inference. **Data leakage** means training or selection receives information unavailable at prediction time. A **point-in-time correct join** chooses, for each historical entity event, only feature records whose event timestamps were available then. **Concept drift** means the relationship `P(y|x)` changes; **covariate drift** means `P(x)` changes. Neither automatically proves the other.

A **champion** is the incumbent production model; a **challenger** is evaluated against it. **Shadowing** sends production inputs to a candidate without using its answer. A **canary** serves a small traffic fraction and can affect users. **Rollback** restores a known-good deployment; **roll-forward** fixes by releasing a new immutable version. **Delayed labels** occur when ground truth arrives later—for example, chargeback status after 60 days.

### The senior-engineer mental model

Treat a model as a release bundle, not a single pickle:

```text
decision contract
  -> immutable data + labels + time semantics
  -> feature/preprocessing code
  -> training run + environment
  -> artifact + signature + evaluation report
  -> registry version + approval evidence
  -> serving image/config
  -> prediction and outcome telemetry
```

Every arrow needs an identity, owner and compatibility rule. Reproducibility is not “same seed”; it is enough captured state to explain or recreate the result within a declared tolerance. Exact bitwise reproduction may be impossible on nondeterministic GPU kernels, so the contract might require AUC within ±0.002 and identical schema rather than identical bytes.

## 2. CORE MECHANICS

### 2.1 Begin with a decision contract

Write what decision the model supports, at what time, for whom, with what cost of errors and human override. For claims triage, suppose a score above 0.60 routes a claim to manual review; it does not deny payment. Capacity is 8,000 reviews/day, false negatives have estimated mean loss ₹18,000, and false positives cost ₹220 of analyst time. Those numbers determine threshold and monitoring. “Maximize AUC” does not.

Define the prediction timestamp. If the model scores when a claim is submitted, a settlement amount recorded 14 days later is forbidden even if it exists in the warehouse during training. Define label maturity: evaluate July fraud outcomes only after the investigation window closes.

### 2.2 Version data by content and time

A path alone is weak provenance. `claims/latest.parquet` is mutable. Record an immutable URI or version plus a content digest, schema and extraction/as-of timestamp. The lab manifest pins `snapshot_date=2026-07-31`, a 64-hex SHA-256, and `as_of=2026-07-31T23:59:59Z`.

SHA-256 detects changed bytes; it does not prove semantic correctness or authenticity. Access control, signed manifests and trusted ingestion are still required. Large datasets are normally identified by a versioned table snapshot plus a manifest of object digests rather than hashing terabytes in each training job.

Boundary cases include deleted upstream snapshots, non-deterministic SQL without stable ordering, schema-compatible but semantically changed columns, late-arriving events and corrected labels. Retention must cover the audit/retraining window. Do not log row-level regulated data to a broadly readable tracking server.

### 2.3 Make historical features point-in-time correct

For an entity row `(claim=C1009, event_time=2026-07-10 09:00)`, join the newest feature record with `feature_time <= event_time` and, if relevant, `created_time <= training_cutoff`. A feature record with event time July 9 but ingested July 12 was not available to a July 10 online decision unless the production system can backfill time travel.

Example feature history:

| claim | feature time | known at | prior claims |
|---|---:|---:|---:|
| C1009 | Jul 1 00:00 | Jul 1 00:10 | 2 |
| C1009 | Jul 10 08:30 | Jul 12 03:00 | 5 |

At Jul 10 09:00, the safe value is 2, not 5. Feast calls this a point-in-time join. Offline and online transformations should share definitions, but offline batch storage and low-latency online storage can remain different physical systems.

### 2.4 Separate train, validation and test responsibilities

Fit parameters on **train**. Choose hyperparameters, features and threshold on **validation**. Open **test** once for a final unbiased estimate. If you inspect test AUC after every change, test has become validation.

The lab records entity IDs and enforces disjoint splits. For time-dependent healthcare or fintech data, prefer chronological splits and consider grouping by patient, account or merchant so the same entity cannot leak across partitions. A random row split can put one patient's January visit in train and February visit in test.

A seed controls supported pseudorandom operations; it does not neutralize data races, unordered sets, parallel reductions, GPU nondeterminism or library-version differences. Record framework/runtime/container and hardware-relevant settings. Report uncertainty: 0.918 AUC on 200 examples is much less certain than on 200,000.

### 2.5 Track runs and compare like with like

Log parameters (learning rate 0.03, max depth 6), metrics with dataset/split context, source commit, environment, dataset identities and artifacts. MLflow organizes executions as runs within experiments. A metric named simply `auc=0.918` is ambiguous: which split, time window, label definition and confidence interval?

Tracking is an evidence store, not a dumping ground. Never log access tokens, patient identifiers or unrestricted sample rows. Apply authentication, least privilege, retention and artifact scanning. Parent-child runs are useful for a tuning job: the parent records search policy; each child records one trial.

### 2.6 Construct pipelines as idempotent components

A practical DAG might be:

```text
snapshot -> validate data -> build features -> split -> train
                                                |       |
                                                +-> evaluate -> register candidate
```

Each component has a contract: versioned code/image, typed inputs, declared outputs and deterministic cache key where possible. **Idempotent** means retrying with the same inputs does not create inconsistent side effects. Write output to a run-scoped temporary location, validate it, then atomically publish an immutable URI.

Cache only when the key covers every behavior-changing input. If feature code changed but the cache key includes only dataset URI, reusing old features is wrong. Never cache a nondeterministic or external-state-dependent step without representing that state. Retries need classification: retry transient 503/timeouts with bounded exponential backoff; do not repeatedly retry a schema violation.

### 2.7 Evaluate with explicit release gates

The running candidate has test AUC 0.918, Brier score 0.094 and TPR gap 0.041. Gates require AUC ≥0.90, Brier ≤0.11 and gap ≤0.05, so all pass. Direction matters: larger AUC is better; smaller Brier and disparity gap are better.

Gates should cover:

- predictive performance against a baseline and incumbent;
- slice performance for clinically/business-relevant cohorts;
- calibration and threshold outcomes at expected prevalence;
- schema, missingness, range and leakage checks;
- inference latency, memory and artifact size;
- privacy, dependency, license and model-artifact security;
- required human and model-risk approval.

A fairness threshold alone cannot establish fairness. Group definitions, sample size, uncertainty and the decision's context matter. In regulated decisions, preserve the exact evaluation report and approval ticket.

### 2.8 Package a complete, safe model contract

The package includes preprocessing, weights, signature, dependencies and examples. The sample signature has `age: int64[18,100]`, `prior_claims: int64[0,50]`, and `amount: float64[0,1000000]`. Enforce compatible types and ranges both before training and at serving.

Python pickle can execute code while loading; treat untrusted serialized models as executable. Prefer safer formats where suitable, scan dependencies, isolate loading and allow only trusted registries. ONNX improves portability for supported operators but does not guarantee numeric identity across runtimes. A container digest captures filesystem bytes, not external feature-service behavior.

### 2.9 Register immutable versions; move aliases deliberately

Registration creates a durable model version linked to its run. The lab accepts `models:/claims-risk/17` and rejects `models:/claims-risk/production`. Why? An audit or deployment manifest must resolve to immutable version 17. A human-facing `champion` alias is operationally useful, but because it can move independently, resolve it once during promotion and record the resulting version and digest.

Do not overwrite version 17. Publish version 18. Store signature, owner, intended use, limitations, evaluation window and approvals. Registry status is not a substitute for deployment status: a registered model may never be released, and one model version may back multiple environment-specific deployments.

### 2.10 Keep CI, CT and CD separate

**CI** on a pull request runs unit tests, schema/contract tests, small deterministic training tests and security scans. It should not silently promote a model. **CT** is a scheduled or event-driven pipeline that produces a candidate when enough mature data exists or drift plus business evidence justifies retraining. **CD** packages and promotes an already evaluated artifact through environments.

Separation prevents a data arrival from immediately changing customer decisions. A typical policy is: CT trains model 18; automated gates pass; model-risk review approves ticket MRM-4821; CD shadows it; an operator promotes 5%, then 25%, then 100%, with automated rollback conditions.

### 2.11 Deploy progressively and compare safely

Offline validation cannot reproduce every production dependency. Shadowing checks latency, errors and prediction divergence without user impact, but cannot measure treatment outcomes because the candidate does not control decisions. Canarying exposes a small cohort and needs routing consistency: one account should not oscillate between variants. A/B testing estimates causal product impact if assignment, sample size and guardrails are sound. Champion-challenger commonly runs a candidate alongside the incumbent for comparative evidence.

Suppose 5% canary traffic is 50 requests/s, error rate rises from 0.2% to 1.4%, and the alert requires more than 1.0% for five minutes with at least 5,000 requests. After five minutes there are 15,000 canary requests and about 210 failures versus an expected 30 at baseline; rollback is justified. Preserve request correlation and version labels.

### 2.12 Monitor the whole decision loop

Infrastructure signals—availability, p95 latency, CPU, memory—are necessary but insufficient. Also monitor schema violations, missingness, feature freshness, distribution shifts, score distribution, calibration and performance once labels mature. Join predictions to outcomes using privacy-preserving identifiers and record model version, feature version, timestamp and decision.

Population Stability Index is often used for drift: `PSI = Σ(actual_i - expected_i) ln(actual_i/expected_i)`. If expected bins are `[0.50,0.30,0.20]` and actual `[0.35,0.35,0.30]`, PSI is approximately `(-.15 ln .7)+(.05 ln 1.1667)+(.10 ln 1.5)=0.1017`. It signals a distribution difference, not degradation or causality. Zero bins need smoothing and fixed bin definitions.

Labels delayed 60 days mean today's AUC is unknowable. Use leading indicators carefully, then backfill cohort performance by prediction date when labels mature. Retraining should be triggered by evidence and policy, not drift alone. An upstream change can be fixed without retraining; conversely, stable inputs can hide concept drift.

### 2.13 Roll back all compatible state

Rollback is not merely changing a model URI. Version 16 may expect feature schema 4 while production now emits schema 5. Preserve a compatible bundle: model, preprocessing, feature views, container, runtime configuration and routing. Test rollback before incidents. If predictions create irreversible downstream actions, rollback stops new harm but cannot undo previous decisions; reconciliation and human review are part of the runbook.

### 2.14 Use the executable manifest lab

Run:

```bash
cd lab
python3 -m unittest -v test_validate_manifest.py
python3 validate_manifest.py run-manifest.json
```

The six tests verify the accepted reference plus rejection of split leakage, mutable aliases, failed gates, secret-bearing metadata and tampered artifact bytes. `model.json` hashes to `2df46e7e8e3ac1a63f23c23aea744eced44eb2d96c6350b645ce30692d7e1d30`. This is intentionally a compact policy example, not a replacement for signed attestations, registry RBAC or full schema validation.

## 3. WORKED PROBLEMS

### Problem 1 — Reproduce an unexplained winner (easy)

Run A and run B both say `code=v2`, `data=claims/latest`, AUC 0.918 and 0.887. What evidence is missing?

**Solution.** “v2” and “latest” are mutable labels. Capture the 40-character source commit; dataset snapshot/version and digest; feature-code version; train/validation/test entity IDs; seed; hyperparameters; dependency/container digest; hardware and deterministic settings; label cutoff; and metric implementation. Re-run both from immutable inputs. If exact reproduction is not promised, compare against a documented tolerance. The first task is provenance, not choosing A.

**Mistake caught:** assuming a seed or notebook filename makes an experiment reproducible.

### Problem 2 — Detect temporal leakage (easy)

A claim is scored July 10 at 09:00. A feature says five prior claims with event time July 10 at 08:30 but ingestion time July 12. May training use five?

**Solution.** No, not for a system that only knows ingested records at scoring. Point-in-time correctness requires both event time before prediction and availability time before the simulated training cutoff. Use the previous known value, two. Otherwise offline evaluation sees knowledge production lacked.

**Mistake caught:** checking event time while ignoring ingestion/creation time.

### Problem 3 — Repair entity leakage (medium)

A 100,000-row patient dataset is randomly split 80/10/10. It contains 31,000 patients with multiple visits. Test AUC is 0.94 but drops to 0.79 on new patients. Design the split.

**Solution.** Group by patient ID so no patient crosses partitions. If predicting future visits, also split chronologically: train on visits through March, validate April, test May, using mature labels. Freeze IDs and record them. The fall suggests the row split let the model exploit patient-specific history rather than generalize.

**Mistake caught:** treating correlated rows as independent samples.

### Problem 4 — Calculate release gates (medium)

Candidate metrics are AUC 0.918, Brier 0.094, TPR gap 0.041, p95 82 ms. Gates are AUC ≥0.90, Brier ≤0.11, gap ≤0.05 and p95 ≤75 ms. Release?

**Solution.** Predictive, calibration and fairness gates pass: `0.918≥0.90`, `0.094≤0.11`, `0.041≤0.05`. Latency fails because 82>75 ms. Do not average gates or waive latency because AUC is strong. Profile preprocessing/model, optimize or change the SLO after a capacity/risk decision, then rerun the unchanged benchmark protocol.

**Mistake caught:** collapsing independent safety and operational constraints into one score.

### Problem 5 — Build a correct cache key (medium)

Feature materialization depends on dataset digest D, SQL commit C, feature parameters P and runtime image I. The orchestrator keys cache only on D. What should change?

**Solution.** Use a canonical serialization of `{D,C,P,I,component-version}` and hash it. Include external reference data versions too. A changed SQL commit with unchanged D must miss the cache. Secrets should not be placed in the key; represent behavior-relevant secret/config versions without values. Disable caching for unrepresented mutable external state.

**Mistake caught:** confusing the input dataset with the complete function input.

### Problem 6 — Resolve an alias safely (medium)

CD configuration says `models:/claims-risk@champion`. During rollout another operator moves `champion` from 17 to 18. Which version is running?

**Solution.** It depends on when each replica resolves the alias, which can yield a mixed fleet. At promotion start, resolve alias to numeric version 17, verify its digest and approval, and write that immutable identity into the deployment revision. Alias movement can initiate a new promotion but must not mutate an in-flight one.

**Mistake caught:** treating a convenient registry pointer as immutable provenance.

### Problem 7 — Interpret PSI (hard)

Expected score-bin shares are `[.50,.30,.20]`; current shares are `[.35,.35,.30]`. Compute PSI and decide whether to retrain.

**Solution.** Terms are `-.15 ln(.35/.50)=.05350`, `.05 ln(.35/.30)=.00771`, and `.10 ln(.30/.20)=.04055`; total ≈0.10176. It establishes a shift under these bins. It does not show accuracy fell, identify cause, or prove retraining helps. Check data quality, slice/source changes and mature-label performance; retrain only under an approved policy with a valid candidate.

**Mistake caught:** interpreting a drift statistic as a production-performance metric.

### Problem 8 — Design a canary decision (hard)

A 5% canary receives 50 rps. Its five-minute error rate is 1.4%; incumbent baseline is 0.2%; rollback threshold is >1.0% for five minutes and ≥5,000 observations. Act and quantify.

**Solution.** Five minutes yields `50×300=15,000` requests, above minimum. Approximately 210 canary errors occurred; baseline expectation is 30. Both duration and rate rules are met, so stop expansion and route to the known-good compatible bundle. Preserve logs and version dimensions, investigate, and do not reuse the failed artifact under the same version.

**Mistake caught:** comparing percentages without checking sample count or policy duration.

### Problem 9 — Handle delayed outcomes and rollback (hard)

Fraud labels mature after 60 days. Model 18 shows stable latency and input distributions for two weeks, but average review volume rose 35%. Should it remain and should CT retrain?

**Solution.** Review-volume increase is an immediate business guardrail even though AUC is unavailable. Verify traffic/prevalence, threshold, feature freshness and score-distribution changes. If the approved capacity bound is exceeded, rollback or adjust only through controlled policy; do not wait 60 days. Do not automatically retrain: no mature evidence shows a learned relationship changed, and a threshold/config or data pipeline fault may be responsible. Create prediction cohorts and evaluate model 18 after labels mature.

**Mistake caught:** equating healthy infrastructure—or any drift—with healthy decision quality.

## 4. REAL-WORLD / APPLIED CONTEXT

### MLflow tracking and registry

MLflow Tracking records runs, parameters, metrics, code versions and artifacts. Its registry creates named model versions and supports mutable aliases. Official examples load a numeric URI such as `models:/name/17` or an alias such as `models:/name@champion`. The operational pattern in this lesson uses aliases for discovery/promotion intent but numeric versions plus artifact digests for audit and deployment identity. MLflow model packages can carry signatures, input examples and dependency files. Those improve reproducibility; they do not prove the dependencies are safe.

### Azure Machine Learning assets and registries

Azure ML CLI/SDK v2 supports models sourced from local paths, datastore paths, job outputs, MLflow `runs:/...`, workspace assets such as `azureml:name:version`, and registry version URIs. That makes an Azure ML job output a traceable registration source. In a healthcare/fintech platform, grant training jobs read access to approved data assets, grant promotion automation read access only to approved model versions, and keep production identities away from raw training data unless inference requires it.

### Feast and Kubeflow Pipelines

Feast's historical retrieval is designed around point-in-time correct feature joins, addressing one major source of leakage while online retrieval serves current feature values. Kubeflow Pipelines models workflows as components and tasks; caching can reuse task results when inputs are considered unchanged. This improves cost and iteration time only when component identities and complete inputs participate in the cache decision. Neither product removes the need to define label time, governance gates or rollback compatibility.

### Measured local lab evidence

On this workspace's CPython runtime, the stdlib test suite runs six cases: one valid manifest and five adversarial mutations. It verifies an actual 92-byte model file with SHA-256. These are correctness fixtures, not throughput benchmarks; filesystem, CPU and runtime differ across environments, so no latency claim is generalized.

## 5. COMPARISON TABLE

| Choice | Concrete property/cost | Use when | Failure boundary |
|---|---|---|---|
| Mutable alias `@champion` | One registry update redirects future resolution | Human-friendly promotion pointer | Mixed versions if resolved during rollout |
| Numeric version `/17` + digest | Stable identity; 64-hex SHA-256 detects byte change | Deployment, audit, rollback | Digest does not prove trust or semantics |
| Random row split | Simple and balanced | Independent, exchangeable rows | Leaks entities/time in longitudinal data |
| Grouped chronological split | Preserves entity and future boundary | Claims, patients, accounts, time series | May expose seasonal shift and reduce sample size—that is useful realism |
| Shadow | Candidate affects 0% of decisions | Interface, latency, divergence checks | Cannot measure treatment outcome |
| 5% canary | Candidate affects ~5% of routed population | Controlled production validation | Users can be harmed; needs guardrails and sticky routing |
| A/B test | Randomized variants estimate causal product effect | Product outcome comparison | Requires power, clean assignment and ethical approval |
| Scheduled CT | Predictable compute and review cadence | Stable label/data arrival | May retrain unnecessarily or too late |
| Event/drift-triggered CT | Faster response to qualified change | Reliable triggers and mature evidence | Drift false alarms; feedback loops |
| Pickle | Native Python object fidelity | Trusted, isolated same-ecosystem workflows | Loading untrusted bytes may execute code |
| ONNX | Portable graph for supported operators | Cross-runtime serving and optimization | Unsupported/custom ops and numeric differences |
| Container image | Packages OS/runtime/dependencies | Reproducible serving environment | Does not capture external data/service state |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Same seed means reproducible.”** Parallel GPU kernels and changed dependencies can differ. Record all state and define bitwise or metric-tolerance expectations.
2. **“Versioned filename means immutable data.”** `v3.csv` can be overwritten. Use controlled immutable storage and content/snapshot identity.
3. **“A registry alias is a version.”** `champion` can move. Resolve and record version 17 plus digest.
4. **“High offline AUC authorizes release.”** A candidate with 82 ms p95 fails a 75 ms contract; privacy, slices and calibration are separate gates.
5. **“No train/test row overlap means no leakage.”** The same patient across rows or future-derived features still leak.
6. **“Feature stores automatically prevent skew.”** A point-in-time API helps, but wrong timestamps, definitions or online freshness still break correctness.
7. **“Drift means retrain.”** PSI 0.102 indicates distribution shift, not root cause or performance loss.
8. **“Healthy endpoint means healthy model.”** HTTP 200 and 40 ms latency reveal nothing about delayed fraud outcomes.
9. **“Rollback just changes model weights.”** Old weights may be incompatible with new preprocessing/schema.
10. **“Experiment trackers are safe notebooks.”** Logging claim IDs or tokens expands the breach surface. Store minimal metadata under RBAC and retention.
11. **“Retry every failed pipeline step.”** Retrying a deterministic schema error wastes money; classify permanent versus transient failure.
12. **“Retraining is deployment.”** CT creates a candidate. Approval and progressive CD determine whether it affects decisions.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; this is not a substitute for the foundations, mechanics and problems above.

- Reproducible run = code SHA + data identity/time + features + split IDs + seed + parameters + environment + artifacts.
- Train fits; validation chooses; test estimates once.
- Historical feature: `feature_time <= event_time` and availability must match production reality.
- Cache key covers every behavior-changing input.
- Gate directions: AUC `>=`; Brier/latency/disparity `<=`.
- Registry version is immutable; alias is movable.
- CI tests; CT builds candidates; CD promotes approved artifacts.
- Shadow: no decision impact. Canary: limited impact. A/B: randomized outcome comparison.
- Monitor service + data + scores + mature outcomes + slices + business guardrails.
- Drift is evidence to investigate, not an automatic retrain command.
- Roll back model + preprocessing + feature/schema + runtime/config.
- Never log secrets or row-level regulated identifiers to experiment metadata.

## 8. PRACTICE SET FOR SELF-TEST

Do not read the answer key until all ten are attempted.

1. A manifest records Git branch `main`, `data/latest`, seed 42 and AUC 0.91. Name six missing identities needed for defensible reproduction.
2. An account is scored at 12:00. A feature event happened 11:40 but was ingested 12:10. Which value must an offline join use, and why?
3. Candidate metrics are AUC .899, Brier .081 and TPR gap .03; gates are .90, .10 and .05 respectively. Is it promotable?
4. Explain why using test results to choose max depth among 4, 6 and 8 invalidates the test estimate.
5. A canary receives 20 rps for ten minutes at 1.2% errors. The policy requires >1% for five minutes and 10,000 requests. Does the sample requirement pass, and about how many errors occurred?
6. Expected feature bins are `[.25,.50,.25]`; actual is identical. Compute PSI.
7. Give a cache-key input that teams often omit when dataset bytes remain unchanged but feature results change.
8. Explain the safe relationship between `champion` and numeric version 23 in a deployment record.
9. Fraud outcomes mature in 45 days. Name three immediate signals and two delayed signals to monitor.
10. Model 22 expects `age` as integer years; a new pipeline emits decimal months. Why can rolling back only model weights fail?

## 9. CURATED RESOURCES

1. [MLflow Tracking official documentation](https://mlflow.org/docs/latest/ml/tracking/) — exact run/experiment, parameter, metric, artifact and model concepts used in the evidence model.
2. [MLflow Model Registry Workflows](https://www.mlflow.org/docs/latest/ml/model-registry/workflow/) — numeric model versions, tags and mutable aliases, including `@champion` behavior.
3. [MLflow Models official documentation](https://mlflow.org/docs/latest/ml/model/) — packaging, signatures, input examples and dependency metadata beyond the compact lab.
4. [Azure Machine Learning: Work with registered models](https://learn.microsoft.com/en-us/azure/machine-learning/how-to-manage-models?view=azureml-api-2) — exact Azure CLI/SDK v2 paths for job, datastore, MLflow and registry assets.
5. [Feast: Point-in-time joins](https://docs.feast.dev/getting-started/concepts/point-in-time-joins) — precise historical feature-retrieval semantics that prevent future leakage.
6. [Kubeflow Pipelines: Caching](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/caching/) — how task reuse works and where incomplete inputs create stale results.
7. **D. Sculley et al., “Hidden Technical Debt in Machine Learning Systems,” NeurIPS 2015** — canonical account of feedback loops, data dependencies, glue code and undeclared consumers.
8. **Eric Breck et al., “The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction,” IEEE Big Data 2017** — concrete tests across data, model, infrastructure and monitoring.
9. **NIST AI Risk Management Framework 1.0 (2023), Govern/Map/Measure/Manage** — governance and risk vocabulary for high-impact or regulated use beyond predictive metrics.
10. **Chip Huyen, _Designing Machine Learning Systems_ (O'Reilly, 2022), Chapters 4–10** — end-to-end treatment of training data, feature engineering, evaluation, deployment, monitoring and continual learning.

## 10. RELATED TOPICS BRIDGE

### Immediately before

1. **ML Fundamentals** — metrics, calibration, leakage and generalization are needed to design meaningful lifecycle gates.
2. **Production Python** — packaging, dependency management, testing and concurrency make pipeline components reliable.
3. **Data Modeling and SQL** — immutable snapshots, temporal joins and data contracts depend on sound data semantics.

### Immediately after

1. **Model Serving and LLMOps** — consumes the immutable model contract and adds inference topology, batching, safety and LLM-specific evaluation.
2. **Observability and SLOs** — turns service, data and outcome signals into alerts and error-budget decisions.
3. **Security, Privacy and Compliance** — deepens artifact trust, data minimization, approval evidence and regulated decision controls.
4. **System Design** — integrates registry, orchestrator, feature platform, serving plane and monitoring under scale/failure constraints.

---ANSWER KEY BELOW---

1. Full commit SHA; immutable dataset version/digest and as-of time; feature-code/version; frozen split identities; hyperparameters; environment/container digest; framework/hardware determinism settings; label definition/cutoff; metric implementation. Any six defensible identities earn credit.
2. Use the most recent value known before 12:00, not the 11:40 event ingested at 12:10. Production could not observe it at prediction time.
3. No. AUC .899 is below .90 even though Brier and TPR gap pass. Gates are conjunctive unless policy explicitly says otherwise.
4. Repeated choices optimize against test noise, making test part of model selection. Choose depth on validation, then evaluate the selected model once on untouched test data.
5. `20×600=12,000`, so the minimum passes; `.012×12,000=144` errors approximately. The duration/rate rule also needs confirmation from the time series.
6. Zero: every term is `(actual-expected) ln(actual/expected)=0`.
7. Feature transformation/SQL commit, parameters, runtime image or external reference-data version; any behavior-changing omitted input is valid.
8. `champion` may point to 23 at approval time, but CD resolves it once and records immutable numeric version 23 and its artifact digest in the deployment revision.
9. Immediate: latency/errors, schema/missingness, feature freshness, score distribution, review volume. Delayed: discrimination/calibration, false-positive/negative rates, slice performance or realized fraud loss after labels mature.
10. Preprocessing/schema semantics changed: decimal months interpreted as years yields invalid inputs/predictions. Roll back the compatible preprocessing/feature contract and runtime configuration with the model.
