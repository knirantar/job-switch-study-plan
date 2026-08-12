# Production Operations Foundations from Scratch

Parent subject: `06-sre-observability`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Software is not finished when it compiles

A production service is software plus configuration, infrastructure, dependencies, data, deployment mechanisms, observability, security, people, and procedures operating over time. **Operations** is the discipline of running that socio-technical system safely: releasing change, detecting failure, responding, maintaining capacity, protecting data, and learning.

Traditional development and operations teams were often separated by handoffs. DevOps emerged as a cultural and technical movement emphasizing shared ownership, automation, small changes, feedback, and collaboration. Site Reliability Engineering (SRE), developed at Google, applies software engineering to operations and manages reliability through measurable objectives, automation, and bounded operational work.

Neither term means “developers run random shell commands in production.” Mature operation reduces privileged manual action, makes desired state reproducible, and records evidence. Human judgment remains essential for novel incidents and risk decisions.

### Service, environment, and dependency

A **service** is a capability with an owner, interface, users, state, dependencies, and lifecycle. A **production environment** serves real business workloads/data. Development, test, staging, and pre-production environments support changes but never perfectly reproduce production scale, traffic, data, identity, and failure. “Works in staging” is evidence, not proof.

A **dependency** is anything required for an operation: database, DNS, identity provider, queue, model registry, cloud control plane, certificate, human approval, or third-party API. Maintain a service catalog describing owners, on-call, criticality, data classification, endpoints, dependencies, dashboards, runbooks, repositories, deployments, and SLOs.

### Ownership and on-call

Every production component needs an accountable team. Ownership includes code, alerts, runbooks, capacity, security response, upgrades, costs, data lifecycle, and decommissioning. A rotating **on-call** engineer responds to urgent service issues during an assigned period. Escalation brings deeper expertise/authority when impact or duration exceeds the responder's scope.

On-call health is a system quality signal. Frequent non-actionable pages, missing access, unclear ownership, and repetitive toil cause fatigue and unsafe decisions. Page only for urgent actionable conditions; send tickets/dashboards for work that can wait.

### Changes and releases

Change is a major incident trigger, yet freezing all change prevents security fixes and improvement. Safe delivery reduces change size, automates validation, separates deployment from feature exposure, rolls out gradually, observes, and supports rollback or roll-forward.

A **build artifact** is immutable deployable output identified by digest. A **deployment** places it in an environment. A **release** exposes behavior to users, sometimes through feature flags. Separating these allows dark deployment and controlled activation. Configuration is also change and needs versioning, review, validation, provenance, and rollback.

Common rollout strategies:

- rolling: replace subsets incrementally;
- canary: send a small representative share to new version and compare;
- blue/green: maintain old/new environments and switch traffic;
- feature flag: activate behavior independently by cohort;
- shadow: copy traffic without using new response, with privacy/side-effect controls.

No strategy eliminates compatibility requirements. During rolling/canary, old and new code coexist and share schema/messages. Database migrations often use expand–migrate–contract.

### Configuration and secrets

Configuration changes service behavior without source modification: endpoints, timeouts, feature flags, resource limits, and policy. Defaults should be safe and validated. Dynamic configuration needs version, author, target scope, staged rollout, audit, and failure behavior. A malformed global timeout can cause an outage faster than code deployment.

Secrets are credentials or keys, not general config. Store them in managed secret/key systems, grant workload identity, rotate, prevent logging, and handle expiry. A secret manager outage/rotation can be a dependency incident; cache/lifetime behavior must be explicit.

### Runbooks and playbooks

A **runbook** is a tested procedure for a known operational task or symptom. It states purpose, preconditions, authorization, safety checks, exact scope, commands/actions, expected output, rollback, verification, escalation, and evidence. A **playbook** often coordinates a broader scenario such as ransomware response or regional failover.

Runbooks decay. Exercise them, make commands read-only first, avoid unresolved variables/wildcards for destructive actions, and automate repeated safe steps. A document saying “restart the service” without diagnosis, impact, and verification is not an operational runbook.

### Incidents and severity

An **incident** is an unplanned interruption or reduction in service quality, security, or data correctness requiring coordinated response. Severity reflects user/business impact and urgency, not engineer difficulty. Define criteria: affected users/tenants, critical workflows, error/latency, data loss/corruption, security/privacy, financial/regulatory exposure, and duration.

Incident response prioritizes safety and impact reduction: declare, assign roles, establish communication, gather timeline, mitigate, verify, and then investigate/fix. Preserve forensic evidence in security incidents. Do not wait for certainty before declaring; severity can be adjusted.

### Toil and automation

Google defines **toil** as manual, repetitive, automatable, tactical work with no enduring value that scales linearly with service growth. Not all operational work is toil: designing recovery, capacity experiments, and incident learning create durable value. Track repetitive pages, manual releases, access grants, and cleanup; eliminate causes or automate with guardrails.

Automation amplifies both correctness and mistakes. Start with read-only reporting, dry runs, scoped targets, idempotency, rate limits, approvals for high-risk actions, audit, rollback, and tests. “One-click delete all stale resources” needs classification/retention/legal-hold checks.

### Production access

Use least privilege, individual federated identity, MFA, just-in-time elevation, approved break-glass paths, session/audit logs, and separation of duties for high-impact actions. Avoid shared accounts and standing admin credentials. Break-glass access must be available when normal identity is down, protected, tested, monitored, and reviewed after use.

Read-only observation should be broadly safe enough for responders; mutation should be narrower. Production data access follows purpose limitation and masking. A developer's need to debug does not authorize downloading sensitive patient or payment data.

### Operational evidence

Evidence includes deployment event/digest, config version, audit record, metric/log/trace, ticket, incident timeline, backup result, restore test, and capacity experiment. Evidence must have timestamps, identity, scope, integrity/retention, and correlation. Dashboards that cannot identify deployment/config changes slow diagnosis.

## 2. CORE MECHANICS

### 2.1 Build a service inventory

For `claims-api`, record:

- owner: Claims Platform; on-call/escalation;
- critical user journeys: submit/status/cancel claim;
- data: PHI, financial amount, retention;
- runtime: region, cluster, namespace, artifact digest;
- dependencies: gateway, identity, PostgreSQL, Kafka, object storage;
- SLO/dashboard/alerts/logs/traces;
- deployment pipeline/repository/IaC;
- runbooks: elevated errors, DB pool, Kafka lag, rollback, secret rotation;
- RPO/RTO and last recovery exercise.

Automate catalog synchronization from deployment/IaC where possible, but ownership and journey meaning need human governance.

### 2.2 Define environments and promotion

Development permits fast iteration with synthetic data. Test runs automated functional/integration/security checks. Staging rehearses production-like deployment/config and migrations. Production receives an already built immutable artifact by digest, never a rebuild from branch.

Promotion gates include tests, vulnerability/policy, schema compatibility, change approval proportional to risk, canary, and telemetry. Emergency change has faster path but still identity, review where possible, immutable artifact, audit, verification, and follow-up.

### 2.3 Make a change plan

For JVM upgrade:

1. State purpose/risk/affected services.
2. Verify dependency/framework support and release notes.
3. Build once with pinned inputs; record digest/SBOM.
4. Benchmark CPU/memory/GC/startup under representative load.
5. Test rollback compatibility and persistent data.
6. Canary one fault domain/low percentage.
7. Compare error, latency, resource, business correctness.
8. Expand with hold points; stop conditions explicit.
9. Verify full rollout and observe long enough for delayed effects.
10. Record outcome and remove old version after rollback window.

### 2.4 Canary arithmetic

At 20,000 rps, a 1% canary receives 200 rps. If a rare defect occurs once per 100,000 requests, expected canary occurrence is 0.002/s, about one every 500 seconds (8.3 minutes). A five-minute canary has expected 0.6 occurrences and may miss it. Choose volume/duration from detectable effect and statistical confidence, not a ritual percentage.

For zero baseline errors, one canary error may be meaningful; for noisy metrics, use rate/confidence and matched cohorts. Include tenant/geography/request diversity while preventing high-risk users from first exposure where appropriate.

### 2.5 Configuration validation

Represent config with schema, types, ranges, cross-field constraints, and safe defaults. Example: connect timeout 50–5000 ms; request deadline 100–10,000 ms; connect timeout must be below request deadline; retry count 0–3; pool max × max replicas ≤ DB budget. Validate in CI and admission, then canary dynamic changes.

Unknown fields should fail or warn according to evolution policy; silently ignored misspellings create false confidence.

### 2.6 Write an actionable runbook

Alert: DB pool wait p99 >100 ms for 10 minutes and user latency burns SLO.

Runbook begins with impact/dashboard link and safe queries: verify scope/version, pool active/idle/wait, DB sessions/CPU/locks/slow queries, recent scaling/deploy/config. Decision tree distinguishes leaked connections, DB saturation, lock blocking, dependency latency, and replica storm. Mitigations include stop rollout, reduce admission, kill only verified blocker with authorization, tune/restart only with impact, and scale within DB budget. Exit requires user SLI recovery and no data correctness issue.

### 2.7 Handoff an on-call shift

Handoff includes active incidents, degraded dependencies, risky changes, temporary mitigations/expiry, silences, capacity concerns, scheduled jobs/releases, vendor cases, access issues, and named next actions. It should be durable and time-stamped, not only a chat call.

### 2.8 Conduct a production readiness review

Before launch, verify ownership/on-call, architecture/dependencies/failure modes, SLOs/alerts, dashboards/correlation, load and failure tests, capacity/quotas, secure identity/data, deployment/rollback, schema compatibility, runbooks, backups/restores, DR, cost, compliance, and decommission plan. Risks can be accepted by accountable owners with expiry; a checklist cannot transfer accountability.

### 2.9 Handle a stuck deployment

Do not immediately rerun repeatedly. Determine control-plane status, desired/current replicas, failing step, image/artifact availability, admission policy, capacity/quota, readiness, migration lock, and whether old version still serves. Repeated retries can create concurrent migrations or exhaust rate limits. Stop, preserve IDs/logs, choose rollback/roll-forward based on state.

### 2.10 Decommission safely

Prove no callers via inventory, traffic logs, dependency scans, and staged deny/observation. Define data retention/export/deletion/legal hold; revoke routes, DNS, identities, secrets, jobs, monitors, backups according to policy; drain and archive evidence; remove infrastructure via reviewed IaC; verify costs and vulnerability surface disappear. Deleting compute alone leaves orphaned data/credentials.

## 3. WORKED PROBLEMS

### Problem 1 — Deployment versus release (easy)

Version 2 runs with feature flag off. Deployed or released?

**Solution.** Deployed, but feature not released to users. This separation supports validation and controlled exposure.

**Trap:** using terms interchangeably and losing rollback/flag reasoning.

### Problem 2 — Page or ticket (easy)

Certificate expires in 25 days; automation healthy. Page now?

**Solution.** Usually ticket/warning with escalation thresholds, not wake someone. Page if renewal/deployment fails and remaining time crosses urgent action window or active handshakes fail.

**Trap:** paging every future risk regardless urgency.

### Problem 3 — Immutable artifact (easy)

Why not rebuild `main` for production after staging passed?

**Solution.** Source/dependencies/environment may change; promote exact tested digest with provenance. Branch is mutable.

**Trap:** treating same source ref as same bytes.

### Problem 4 — Canary volume (medium)

Service 5,000 rps, 2% canary, defect 1 per 50,000 requests. Expected time to one defect?

**Solution.** Canary 100 rps; event rate 100/50,000=.002/s; expected 500 s≈8.33 minutes. Detection probability varies; one expected event is not high confidence.

**Trap:** running a fixed two-minute canary.

### Problem 5 — Config outage (medium)

Global pool size changes from 10 to 100 across 50 replicas; DB budget 800.

**Solution.** Potential demand jumps 500→5,000, 6.25× budget. Reject via cross-field/admission policy; canary config; coordinate replicas/pool/proxy; roll back safely if applied.

**Trap:** treating configuration as lower-risk than code.

### Problem 6 — Runbook mutation (medium)

Runbook says `kubectl delete pod -l app=claims`. What is missing?

**Solution.** Context/cluster/namespace resolution, reason/diagnosis, exact matched targets preview, impact/PDB/capacity, authorization, rate/batch, expected recreation, verification, and escalation. Broad selector deletion can create outage.

**Trap:** command list mistaken for procedure.

### Problem 7 — Shared production account (hard)

Team uses one admin login “for speed.” Risks and replacement?

**Solution.** No individual attribution/revocation, broad standing privilege, credential sharing/theft, weak MFA/audit. Use federation, individual identities, JIT scoped roles, approvals, break-glass, session logs.

**Trap:** compensating only with password rotation.

### Problem 8 — Staging confidence (hard)

All staging tests pass. Why can production still fail?

**Solution.** Scale, data distribution, concurrency, traffic mix, quotas, network topology, identities, external dependencies, caches, and failure states differ. Canary/load/failure tests and observability close some gap, never all.

**Trap:** demanding an identical full production copy as complete proof.

### Problem 9 — Incident versus bug (hard)

Model returns wrong clinical eligibility for 2% requests but API latency/errors normal. Incident?

**Solution.** Yes—data/business correctness and potential patient/regulatory impact. Stop/contain model, route safe fallback/human review, identify decisions, notify privacy/safety stakeholders, preserve lineage/evidence, correct/reconcile. Technical uptime is not service correctness.

**Trap:** declaring healthy because 2xx and latency are normal.

## 4. REAL-WORLD / APPLIED CONTEXT

### Google SRE

Google formalized error budgets, toil limits, production readiness, incident response, and automation. The central idea is not copying organizational titles; it is aligning reliability with product objectives and using engineering to reduce repetitive operational load.

### Kubernetes reconciliation

Kubernetes controllers continuously reconcile desired and observed state. Deployments implement rolling behavior; probes control restart/admission; events/status expose control-plane decisions. Operators still own safe manifests, capacity, compatibility, observability, and application shutdown.

### Model platform operations

An ML platform release includes code, container, model artifact, feature definitions, thresholds, prompt/RAG index, and policy. Rollback of code alone may not restore behavior. Record a release manifest linking every immutable component and evaluate business/safety metrics during canary.

## 5. COMPARISON TABLE

| Strategy | Extra capacity | Exposure | Rollback | Key risk |
|---|---:|---|---|---|
| Rolling | Usually modest surge | Incremental instances | Roll old version forward/back | Mixed-version compatibility |
| Canary | Small initial new capacity | Controlled traffic share | Route back | Unrepresentative/low volume |
| Blue/green | Near 2× app capacity | Switchable | Fast traffic switch | Shared DB/state still changes |
| Feature flag | Little infra | Cohort/behavior | Disable flag | Flag/config debt, code paths coexist |
| Shadow | Duplicate compute/downstream | Response not served | Stop copy | Side effects/privacy/cost |
| Manual runbook | Human flexibility | Task-specific | Procedure-dependent | Error, inconsistency, toil |
| Automation | Repeatable/fast | Scalable | Must be designed | Amplifies bad assumptions |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Operations begins after launch.** Ownership, SLO, recovery, capacity, and security are design inputs.
2. **DevOps is a tooling team.** It emphasizes shared outcomes and feedback, not one silo.
3. **Deployment equals release.** Feature exposure can be independent.
4. **Rollback always restores state.** Schema/data/external effects may be irreversible; roll-forward/reconcile can be safer.
5. **Staging proves production.** It reduces risk but cannot reproduce all conditions.
6. **Every alert should page.** Page only urgent actionable user-risk conditions.
7. **Runbook is a command list.** It needs conditions, safety, verification, rollback, escalation.
8. **Automation is always safer.** It increases blast radius without guards.
9. **Config changes are harmless.** They can propagate globally and bypass build tests.
10. **Shared admin improves response.** It destroys attribution and increases compromise scope.
11. **2xx means service correct.** Data/business/model correctness are user outcomes.
12. **Decommission means stop compute.** Data, DNS, secrets, backup, monitoring, and cost remain.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Production service = code + config + infra + data + dependencies + people/process.
- Catalog owner, journey, data, dependencies, SLO, runbooks, deploy, recovery.
- Build once; promote immutable digest.
- Deployment places version; release exposes behavior.
- Small staged change + stop conditions + telemetry + rollback/roll-forward.
- Config is code-like change; secrets are separate protected credentials.
- Page urgent/actionable; ticket nonurgent.
- Runbook: preconditions → read-only evidence → scoped action → verify → rollback/escalate.
- Use individual federation, JIT privilege, break-glass and audit.
- Track toil and automate with dry-run, scope, idempotency, rate limit, audit.
- Correctness/security incidents exist even with healthy latency.

## 8. PRACTICE SET FOR SELF-TEST

1. Define service ownership fields for a model inference endpoint.
2. Distinguish deployment, release, and feature flag.
3. At 12,000 rps and .5% canary, how many requests/minute reach canary?
4. A defect occurs 1/200,000 requests; estimate expected canary detection time from question 3.
5. List eight production readiness categories.
6. Turn “restart database” into a safe runbook outline.
7. Classify weekly manual certificate renewal as toil or not, with reasoning.
8. State emergency change evidence requirements.
9. Explain why rollback after destructive DB migration may fail.
10. Outline safe service decommission.

## 9. CURATED RESOURCES

- Betsy Beyer et al., *Site Reliability Engineering*, Chapters 1, 3, 5, 6, 7, 8, 10, 11, and 14 — SRE principles, risk, objectives, toil, automation, release engineering, and on-call.
- Betsy Beyer et al., *The Site Reliability Workbook*, Chapters 2, 3, 8, 9, 11, and 18 — implementation of SLOs, monitoring, incident response, on-call, and production readiness.
- Nicole Forsgren, Jez Humble, and Gene Kim, *Accelerate*, Chapters 2–7 — research-backed delivery performance, architecture, lean practices, and culture.
- Jez Humble and David Farley, *Continuous Delivery*, Chapters 1–5 and 10–11 — deployment pipeline, configuration, automated testing, and infrastructure/environment management.
- ITIL 4 Foundation sections on service management, incident, change enablement, and continual improvement — operational governance vocabulary useful in service companies.
- NIST SP 800-53 Rev. 5 controls for access, audit, configuration, contingency, and incident response — regulated operational control requirements.
- Kubernetes official documentation, “Deployments,” “Configure Liveness, Readiness and Startup Probes,” and “Pod Lifecycle” — concrete rollout and shutdown mechanisms.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Linux/Cloud/Kubernetes:** supplies the runtime and control mechanisms operations manages.
2. **Git/CI-CD:** supplies immutable change identity, review, and delivery.
3. **Distributed Failure Semantics:** supplies ambiguity, deadlines, and dependency behavior.

### After

1. **Reliability, Availability, and Failure Basics:** quantifies the outcomes production operation protects.
2. **Monitoring and Alerting:** creates feedback and actionable detection.
3. **SLIs/SLOs/Error Budgets:** aligns reliability thresholds with users/business.
4. **Incident Response:** formalizes coordinated mitigation/evidence/learning.
5. **Capacity and DR:** rehearses overload and recovery.

---ANSWER KEY BELOW---

1. Team/on-call, users/journey, endpoint/model manifest, data classification, dependencies, SLO/alerts/dashboard, deploy/rollback, runbooks, capacity, RPO/RTO, cost (appropriate subset).
2. Deployment runs artifact; release exposes behavior; flag controls exposure independently within deployed code.
3. 60 rps ×60=3,600/minute.
4. 200,000/60≈3,333 s≈55.6 minutes expected.
5. Ownership, architecture/dependencies, SLO/alerts, observability, capacity/load/failure, security/data, deployment/compatibility, backup/DR/runbooks/cost/compliance (any eight).
6. Impact/preconditions/auth, inspect topology/replication/transactions/backups, determine cause and safe target, controlled failover/restart, verify data/clients/SLO, rollback/escalation/evidence.
7. Repetitive, manual, automatable, tactical and scales: toil; automate renewal/deployment verification while retaining exception handling.
8. Individual identity, reason/ticket, exact artifact/config, risk/approval proportional to urgency, tests possible, audit, verification, rollback/roll-forward and retrospective follow-up.
9. Old code/schema may be incompatible and deleted/transformed data cannot be recreated; use expand-contract/backups/reconciliation.
10. Prove no callers, handle retention/legal hold/export/delete, revoke routes/identity/secrets/jobs, remove monitors/backups per policy/IaC, verify cost/security disappearance and archive evidence.
