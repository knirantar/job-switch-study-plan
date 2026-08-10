# CI/CD and the Software Supply Chain

**Parent:** 05 — Cloud Platform  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus the executable integrity lab

## 1. FOUNDATIONS

Continuous integration (CI) is the practice of integrating small changes frequently and automatically checking each integration. Continuous delivery keeps every accepted revision releasable; continuous deployment automatically releases every qualifying revision. These are different promises. A team can run excellent CI yet deploy monthly, or continuously deliver to a production approval gate without continuously deploying.

Before CI, long-lived branches accumulated incompatible changes and integration happened late. Automated builds shortened that feedback loop. Cloud runners, package registries and deployment APIs then turned the pipeline into a privileged production system. That created a second problem: an attacker no longer needs to change application source if they can replace a dependency, workflow action, build runner or artifact between test and deployment. **Software supply-chain security** protects the entire path from source and dependencies through build, provenance, registry and runtime.

A **pipeline** is the ordered/parallel graph of jobs. A **runner** executes a job. A **trigger** is the event and trust context that starts it. An **artifact** is an immutable build output intended for consumption; a **cache** is a disposable performance optimization. A **digest**, such as SHA-256, identifies bytes. A **signature** binds a digest to a key. An **attestation** is a signed claim about a subject—such as who built an image, from which repository and commit. **Provenance** records how an artifact was produced. An **SBOM** inventories software components; it does not prove they are safe.

The governing invariant is **build once, promote the same digest**. If commit `9f31c2a` produces image digest `sha256:ab…`, staging and production consume that digest. Rebuilding a tag for production produces different bytes because timestamps, repositories or toolchains may differ, invalidating prior tests. Tags are mutable pointers; digests identify content.

Without explicit trust boundaries, pull-request text can become shell code, caches can carry executable poison into trusted jobs, broad repository tokens can modify releases, long-lived cloud secrets can be stolen from logs, and an unpinned third-party action can change after review. A pipeline is therefore executable security policy, not merely automation YAML.

## 2. CORE MECHANICS

### 2.1 Model stages and feedback

A practical flow is `lint → compile → unit tests → component/integration tests → package → scan/attest → publish → deploy canary → verify → promote`. Run cheap deterministic checks first. Suppose lint takes 40 seconds and fails 15% of revisions, unit tests take 4 minutes and fail another 10%, and integration tests take 18 minutes. Running lint first avoids approximately `0.15 × (4+18) = 3.3` runner-minutes per revision. Parallelism shortens latency but consumes runners and can hide ordering dependencies; artifact edges must be explicit.

Set a feedback objective. A pull request receiving a reliable failure in 6 minutes encourages small corrections; a flaky 55-minute pipeline encourages batching and bypasses. Track queue time, execution time, failure rate and rerun rate separately. A 12-minute job waiting 38 minutes is a capacity problem, not test optimization.

### 2.2 Trigger trust and event data

Code from a fork is untrusted. On GitHub Actions, `pull_request` is appropriate for testing fork code with restricted permissions. `pull_request_target` runs in the base repository's privileged context; checking out and executing fork code there can expose secrets. Never interpolate untrusted issue titles or branch names directly into a shell script. Pass them through an environment variable and quote it, or avoid shell interpretation.

Separate untrusted build from trusted release. A PR job should compile and test without cloud credentials. A post-merge job on a protected branch may publish. A production deployment should use an environment gate and retrieve the already-built artifact by immutable identity.

### 2.3 Least privilege and ephemeral identity

Declare workflow permissions, starting with `contents: read`, rather than inheriting a broad token. Grant `packages: write`, `attestations: write` or `id-token: write` only to the job that needs it. Job-level permissions are clearer than workflow-wide privilege.

OpenID Connect (OIDC) lets a runner receive a short-lived signed identity token containing claims such as repository, ref, environment and workflow. A cloud identity provider validates the issuer/audience/claims and exchanges it for limited cloud credentials. This removes static client secrets but does not remove authorization design: a loose subject rule such as “any branch in organization” lets an unexpected workflow assume production privilege. Bind the federation rule to the exact repository and protected environment, constrain audience, and give the cloud principal only deployment operations.

### 2.4 Reproducible dependency resolution

Lock direct and transitive dependencies. Maven's version ranges or floating container bases make tomorrow's build resolve different inputs. Commit lock data where the ecosystem supports it; configure trusted repositories; verify checksums/signatures; and update through reviewed automation. A lock file improves repeatability but cannot make a malicious locked package benign.

Pin third-party workflow actions to a reviewed full commit SHA. A tag such as `@v4` is convenient but movable. Renovation tooling can open a diff that updates the SHA with release notes. Also pin the runner image where practical and record compiler/JDK/container builder versions.

### 2.5 Cache versus artifact

A dependency cache may disappear and the build must still work. An artifact is evidence/output and must have an explicit retention and integrity policy. GitHub currently documents a default artifact/log retention of 90 days, configurable from 1–90 days for public repositories and 1–400 days for private repositories. Its cache documentation says inactive entries are removed after seven days and the default repository cache limit is 10 GB. These service values can change; check organization settings.

Key caches with OS, tool version and lock-file hash. Never cache credentials. Treat restored cache content as untrusted because executable compiler plugins or wrapper binaries can be poisoned. Do not use a broad restore prefix for release-critical executable outputs.

### 2.6 Build, digest and immutable promotion

Package exactly once. Calculate SHA-256, publish into a registry that prevents tag overwrite, capture the registry-returned digest, and make downstream jobs reference it. In the lab, the input bytes produce `ef3d93cb314148c335a780c4cc7e2f0e004a57dd826614871c3b28e542773f54`. Appending `tampered` changes the bytes, and verification exits nonzero.

That test proves integrity only when the expected digest arrives through a trusted channel. If an attacker can replace both artifact and `SHA256SUMS`, both agree. A signature or attestation adds authenticated claims; a deployment policy must verify issuer/identity, subject digest and expected source/workflow—not merely “some valid signature exists.”

### 2.7 Provenance, signatures and SBOMs

SLSA provenance describes the builder, build definition, inputs and output subject. GitHub artifact attestations use workflow OIDC identity to sign provenance containing repository, organization, environment, commit and event. Sigstore keyless signing binds a short-lived certificate to an OIDC identity and records/verifies evidence according to its trust model.

Verification should answer: Does the subject digest equal the artifact being deployed? Is the certificate/attestation issuer trusted? Does identity match the approved repository/workflow? Is the source commit protected? Does policy require an SBOM and vulnerability threshold? Signing a compromised artifact faithfully proves that a compromised builder signed it; harden and isolate builders as well.

An SBOM in SPDX or CycloneDX format enables inventory and incident queries such as “which deployed services contain Log4j version X?” CVE scanning is time-dependent: a clean scan today may become vulnerable tomorrow. Store SBOM/provenance, continuously rescan registry contents, and combine CVSS with exploitability, reachability and business exposure.

### 2.8 Testing layers and gates

Unit tests isolate logic; component tests exercise a service boundary; integration tests use real infrastructure contracts; end-to-end tests verify a critical journey; performance tests measure capacity; security checks include SAST, dependency, secret and container scans. More tests are not automatically safer. A flaky gate that fails 5% independently has only `0.95^10 ≈ 59.9%` probability that ten runs all pass, incentivizing blind reruns.

Quality gates need ownership, thresholds and exception expiry. Fail on newly introduced critical exploitable vulnerabilities, not an unactionable count detached from context. Record waivers with approver, rationale, scope and expiry. Never use `continue-on-error` for a claimed mandatory control.

### 2.9 Deployment strategies and rollback

A rolling update replaces batches; blue/green switches traffic between complete environments; a canary exposes a small percentage before expansion. For 100 pods, a 5% canary means five pods, but traffic distribution—not pod count—determines actual exposure. Compare error rate, latency and business signals against baseline with adequate sample size.

Rollback is code plus data. An old binary may not understand a destructive schema migration. Use expand–migrate–contract: add backward-compatible schema, deploy compatible code, migrate data, then remove old shape in a later release. Roll forward may be safer after irreversible side effects such as emails or payments. Make deployment idempotent and serialize production via a concurrency group; do not cancel an in-progress migration halfway.

### 2.10 Secrets, logs and runners

Secrets may leak through command tracing, process arguments, test reports, artifacts or base64 (which is encoding, not encryption). Prefer OIDC and secret-manager references, scope secrets to environments, mask output, rotate on suspected exposure and test logs/artifacts for leakage. A secret supplied to malicious code is already lost even if redacted in logs.

Hosted ephemeral runners reduce persistence. Self-hosted runners are necessary for some private networks or specialized hardware but need isolation, one-job ephemerality, patched images, restricted egress and no credential residue. Never run public-fork code on a persistent privileged internal runner.

### 2.11 Failure handling and observability

Use timeouts, bounded retries with jitter only for transient idempotent operations, and fail closed on policy uncertainty. Preserve test reports, digests, provenance, deployment ID and logs with privacy-aware retention. Measure deployment frequency, lead time, change failure rate and recovery time, but do not game them. Correlate release digest with runtime telemetry so an incident responder can identify exactly what is running.

## 3. WORKED PROBLEMS

### Problem 1 — Optimize feedback order

**Statement.** Checks have `(duration, failure probability)`: formatting `(1 min, .20)`, unit `(5, .10)`, integration `(20, .05)`. Choose a sequential order minimizing expected time until a failure or success.

**Solution.** A useful ordering score is failure probability per minute: `.20`, `.02`, `.0025`, so format, unit, integration. Expected consumed time is `1 + .80×5 + (.80×.90)×20 = 19.4` minutes. Reverse order costs `20 + .95×5 + (.95×.90)×1 = 25.605` minutes. Savings are 6.205 minutes/revision under the stated independent rates. In real pipelines, validate rates and dependencies before using the heuristic.

**Mistake caught:** ordering by prestige or duration alone.

### Problem 2 — Protect a forked pull request

**Statement.** A workflow uses `pull_request_target`, checks out the contributor's SHA and runs `./mvnw test` with a package token. Assess and redesign.

**Solution.** The base-context workflow executes attacker-controlled wrapper/plugin code while privileged. Use `pull_request` with read-only contents, no secrets, and test the merge ref. After protected merge, a separate `push` workflow builds/publishes. If privileged labeling is needed, a base-only workflow must never execute or source fork content.

**Mistake caught:** assuming reviewed YAML makes checked-out code safe.

### Problem 3 — Build once

**Statement.** Staging tests image `service:1.8.0`; production rebuilds the same tag. Explain the broken claim.

**Solution.** The tag does not prove byte equality. Dependencies, base image and timestamps can change. Capture staging's registry digest, e.g. `service@sha256:4c…`, verify provenance for that digest, and promote/deploy precisely it. A production rebuild is a new artifact requiring new tests.

**Mistake caught:** treating a tag as content identity.

### Problem 4 — Checksum threat model

**Statement.** An artifact and adjacent checksum both come from a compromised bucket. Does `sha256sum --check` establish authenticity?

**Solution.** No. The attacker replaces both consistently. A checksum detects accidental/tampered bytes only when expected digest is trusted. Verify a signed attestation against an approved issuer and workflow identity, then require its subject digest to equal the downloaded bytes.

**Mistake caught:** confusing integrity comparison with authentication.

### Problem 5 — OIDC authorization

**Statement.** Azure trusts OIDC tokens from `repo:acme/*` for Contributor on a subscription. Improve it.

**Solution.** Restrict subject to the exact deployment repository and protected `production` environment, validate audience, use a dedicated application/federated credential, and scope an Azure role to the target resource group with only deployment actions. Give only the deploy job `id-token: write`. Audit token exchanges and protect environment reviewers.

**Mistake caught:** replacing a static secret while retaining excessive privilege.

### Problem 6 — Flaky tests

**Statement.** Eight independent end-to-end tests each fail spuriously 3% of the time. What is clean-run probability, and what action is justified?

**Solution.** `0.97^8 ≈ 0.7837`, so about 21.6% of runs have at least one spurious failure. Blind retry hides real defects. Quarantine with an owner/expiry, collect failure diagnostics, fix nondeterministic clocks/data/isolation, and keep a smaller deterministic release gate.

**Mistake caught:** interpreting rerun-green as proof the first failure was harmless.

### Problem 7 — Database rollback

**Statement.** Release B renames `customer.ssn` to `tax_id`; 10% canary fails and binary A is redeployed.

**Solution.** A may still query `ssn`, so binary rollback fails. First add nullable `tax_id` while preserving `ssn`; deploy dual-read/write compatible code; backfill and validate counts/checksums; switch reads; only later remove `ssn`. Each stage has a separately tested rollback/roll-forward plan.

**Mistake caught:** treating deployment rollback as container-only.

### Problem 8 — Poisoned cache

**Statement.** A privileged release restores `maven-${branch}-` fallback containing compiler plugins produced by an untrusted workflow.

**Solution.** Cache keys and writers cross a trust boundary. Do not let untrusted triggers populate cache scope consumed by release; use lock-hash exact keys, trusted-trigger writes or restore-only behavior, and verify dependencies. Cache absence must only affect speed.

**Mistake caught:** assuming a platform cache is trusted because it is internal.

### Problem 9 — Canary evidence

**Statement.** Baseline has 10,000 requests and 0.20% errors; canary has 100 requests and one error. Automatically roll back because 1% is five times baseline?

**Solution.** The point estimate is worse, but one event is insufficient for a stable rate comparison. Check severity (one fatal payment error can be decisive), confidence/sample plan, traffic comparability and guardrails. Continue within a bounded exposure if safe, or stop immediately for high-severity invariant violations. Never use ratio alone without counts.

**Mistake caught:** ignoring sample size and event severity.

## 4. REAL-WORLD / APPLIED CONTEXT

GitHub Actions demonstrates an identity-aware supply chain: artifact attestations can bind repository, organization, environment, commit and triggering event to a subject digest. Consumers verify the attestation and expected identity. This is stronger than accepting an artifact merely because it appeared in a registry.

Sigstore Cosign supports keyless verification using OIDC identities. A secure admission rule checks both issuer and identity pattern plus image digest. “Signature valid” alone accepts an unintended signer.

The included `pipeline.example.yml` separates build and protected deployment, declares least privilege, uses immutable commit pins for foundational actions, names artifacts by commit SHA, verifies a checksum and requests OIDC only in deployment. It is an instructional example: replace reviewed action SHAs and cloud login with versions validated in your organization. The executable lab accepted SHA-256 `ef3d…773f54` for its fixed sample and rejected modified bytes on macOS using `shasum`; that is a functional test, not a performance benchmark or provenance proof.

## 5. COMPARISON TABLE

| Choice | Guarantee/cost | Use |
|---|---|---|
| Tag | Human-friendly mutable pointer | Discovery only; resolve to digest for deployment |
| SHA-256 digest | Detects byte mismatch given trusted expected value | Artifact identity/integrity |
| Signature | Digest bound to key | Authenticity when key/identity policy is sound |
| Provenance attestation | Signed build/source/input claims | Admission and audit |
| SBOM | Component inventory, no safety proof | CVE/license/incident queries |

| Deployment | Extra capacity | Failure exposure | Best fit |
|---|---:|---:|---|
| Rolling, max surge 25% on 100 pods | up to 25 pods | gradual but mixed versions | routine compatible stateless releases |
| Blue/green | near 100% duplicate app capacity | switch can be rapid; DB shared | fast traffic rollback |
| 5% canary | about 5/100 pods only if traffic aligns | bounded initial traffic | metric-driven risky change |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Green means safe.”** Tests cover asserted behavior; they do not prove absence. Add runtime guardrails and recovery.
2. **Rebuilding per environment.** This changes the tested subject. Promote one digest.
3. **Using `latest`.** It is mutable and destroys traceability. Deploy digest.
4. **Broad workflow permissions.** A compromised step inherits them. Default read-only; elevate per job.
5. **Static cloud secret by habit.** It leaks and persists. Use narrowly bound short-lived OIDC credentials.
6. **Loose OIDC subject.** Any branch/workflow may deploy. Bind repository, protected environment/audience.
7. **Tag-pinned third-party actions.** Tags move. Pin a reviewed full commit and automate reviewable upgrades.
8. **Trusting caches.** Restored compiler inputs can execute. Isolate writers and verify dependencies.
9. **Putting secrets in caches/artifacts.** Retention broadens exposure. Never persist them there.
10. **Checksum equals signature.** Replacing data and checksum defeats it. Authenticate expected digest/provenance.
11. **SBOM equals vulnerability-free.** It is inventory. Rescan and assess exploitability/reachability.
12. **Scanning only at build.** Disclosures occur later. Continuously rescan deployed inventory.
13. **Blind retry.** It normalizes flakiness and duplicate side effects. Retry only transient idempotent operations.
14. **`continue-on-error` on security gate.** The control becomes reporting. Fail or record governed waiver.
15. **Persistent public-fork runner.** Attacker code can pivot. Use isolated ephemeral unprivileged runners.
16. **Canceling production indiscriminately.** Half-applied migrations can corrupt assumptions. Serialize and make steps resumable.
17. **Rollback means old image.** Data/API compatibility may be irreversible. Use expand–migrate–contract.
18. **Canary pod count equals traffic.** Load balancing/skew differ. Measure actual requests and cohorts.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

`untrusted PR → no secrets/read-only → tests`; `protected merge → build once → digest → SBOM + provenance → registry`; `approved environment → OIDC → verify identity + digest → canary → telemetry → promote`.

- Artifact: retained output. Cache: disposable acceleration.
- Pin dependencies, actions and toolchains; tags are not immutable identities.
- Default token permissions to read-only; grant OIDC only to deployment.
- Verify bytes, subject digest, issuer and builder/source identity.
- Deploy same digest through every environment.
- Database safety: expand, compatible deploy, migrate/verify, contract later.
- Track queue/execution time, flake rate, lead time, failure rate and recovery.

## 8. PRACTICE SET FOR SELF-TEST

1. Design trust-separated workflows for public forks, protected main and production Azure deployment.
2. Calculate expected time for checks A `(2m,.25)`, B `(8m,.10)`, C `(30m,.04)` in optimal sequential order.
3. Explain exactly why signing `service:latest` is insufficient and write the verification decision.
4. A release token has repository write, package write and subscription Owner. Produce minimum privilege boundaries.
5. Design a safe cache key/write policy for Maven builds across PR, main and release.
6. A canary receives 200 of 50,000 requests and has two errors versus baseline 50. Decide what more is needed.
7. Provide expand–migrate–contract steps changing `amount FLOAT` to integer `amount_minor`.
8. List evidence retained for a healthcare production deployment without retaining patient data.
9. Threat-model a self-hosted GPU runner building ML images from external pull requests.
10. Distinguish digest, signature, provenance and SBOM in one verification chain.

## 9. CURATED RESOURCES

1. Jez Humble and David Farley, *Continuous Delivery*, Chapters 5, 6 and 10. Canonical deployment-pipeline, testing and deployment design rationale.
2. Nicole Forsgren, Jez Humble and Gene Kim, *Accelerate*, Chapters 4–7. Empirical delivery-performance capabilities and careful metric interpretation.
3. GitHub Docs, [Security for GitHub Actions](https://docs.github.com/en/actions/how-tos/secure-your-work). Current official permission, OIDC and supply-chain hardening entry point.
4. GitHub Docs, [OpenID Connect reference](https://docs.github.com/en/actions/reference/security/oidc). Exact claims used to constrain federation.
5. GitHub Docs, [Artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations). GitHub's provenance subject and identity model.
6. GitHub Docs, [Dependency caching reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching). Cache matching, trust scopes, poisoning controls and current limits.
7. SLSA, *Supply-chain Levels for Software Artifacts specification*. Provenance model and increasing build-integrity requirements.
8. Sigstore Docs, [Verifying Signatures](https://docs.sigstore.dev/cosign/verifying/verify/). Exact Cosign key/keyless verification mechanisms.
9. NIST SP 800-218, *Secure Software Development Framework (SSDF) Version 1.1*. Organization-level secure development practices and evidence.
10. in-toto authors, *in-toto: Providing farm-to-table guarantees for bits and bytes*. Original layout/link metadata model behind end-to-end supply-chain verification.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Containers:** image layers, registries and digests are the release artifact substrate.
2. **Kubernetes:** rollout, probes and immutable image references determine runtime promotion.
3. **Terraform:** reviewed plans and OIDC-based apply jobs are infrastructure delivery.
4. **Testing in Spring:** unit/integration/contract suites become pipeline evidence.

### After

1. **Cloud Identity and Networking:** federation claims, roles, private runners and egress become concrete controls.
2. **SRE and Observability:** release markers, SLOs and incident signals govern canary decisions.
3. **MLOps Pipelines:** model/data lineage, registry stages and evaluation extend artifact provenance.
4. **Regulated Systems:** approvals, traceability, retention and separation of duties become audit controls.

---ANSWER KEY BELOW---

1. PR: `pull_request`, read-only, no secrets, hosted isolated runner. Main: protected `push`, build once, tests/scans, publish digest/provenance. Production: environment approval, digest download/verification, job-only OIDC restricted to repository/environment, scoped Azure role, serialized canary and telemetry gate.
2. Failure/minute scores: A `.125`, B `.0125`, C `.00133`; order A–B–C. Expected duration `2 + .75×8 + .75×.90×30 = 28.25` minutes.
3. `latest` can point to different bytes after signing. Resolve/publish immutable digest; verify signature/attestation subject equals that digest, trusted issuer and expected repository/workflow identity; deploy digest.
4. Build gets contents read and package write only if publishing; deploy gets contents read plus OIDC. Federated Azure principal gets only required operations at target resource group, not Owner. Release metadata mutation is a separate narrowly privileged job.
5. Key OS/JDK/Maven plus dependency-file hash. PR can read trusted base cache but cannot populate trusted main/release scope; trusted main writes. No secrets or produced release binaries; cache miss must rebuild successfully.
6. Baseline error rate is `50/50,000 = .1%`; canary is `2/200 = 1%`, but only two events. Inspect severity, confidence/sample target, cohort/route comparability and time-window effects; stop immediately for invariant/severe errors, otherwise continue bounded sampling.
7. Add nullable integer `amount_minor`; deploy code dual-writing and reading new-with-old fallback; backfill using documented rounding with reconciliation; enforce non-null and switch reads; later stop old write and drop FLOAT only after compatibility window/backup.
8. Commit, reviewed workflow SHA, artifact digest, provenance, SBOM, scan/policy results, approvers, OIDC principal/claims reference, deployment ID/timestamps, manifest digest, redacted logs, verification/canary results and rollback outcome—no payloads, PHI or secrets.
9. External code can exploit kernel/container/runtime/GPU drivers, steal network credentials, poison caches and persist. Do not run it on internal persistent runner; use ephemeral isolated pool, no secrets, read-only source, restricted egress, patched immutable image, resource limits and teardown/forensics.
10. SHA-256 identifies exact bytes; signature authenticates a digest to a key/identity; provenance attests builder/source/process with that subject digest; SBOM lists included components. Verify bytes→digest, attestation/signature issuer+identity+subject, then SBOM/policy and deployment authorization.
