# Cloud Platform Capstone — Regulated Model-Inference Release Platform

## Objective

Design and demonstrate an Azure platform that releases a Java inference API and Python model worker to AKS for healthcare and fintech tenants. An evaluator must be able to trace one production pod back to reviewed source, immutable image digest, provenance, Terraform plan, workload identity and permitted network flows. The deliverable is executable evidence and recovery practice, not a diagram alone.

## Prerequisite gate

Complete all nine lessons first. Navigate Linux, inspect processes/files/permissions, connect commands safely and diagnose a failed service; create a Git repository, branch, commit, merge and repair a conflict without losing history; explain compute/storage/network/IAM and shared responsibility; and draw a cloud request path through DNS, routing, subnets, security controls, load balancing and private endpoints. Run the prerequisite shell and policy labs from a clean checkout. Kubernetes, Terraform and CI/CD work begins only after these operating-system, version-control and cloud-network foundations are reproducible.

## Workload and constraints

- 18 million API requests/day; measured peak factor 6; payload p50 2 KiB and p99 48 KiB.
- 40 inference pods at normal peak, each requesting 750 millicores and 1.5 GiB; survive one of three zones without waiting for scale-out.
- Four model-worker pods each request one GPU; a fifth canary GPU is allowed for no more than 45 minutes per release.
- API availability SLO 99.95%; production rollout must abort on a 5-minute 1% error-rate burn threshold or any tenant-isolation invariant failure.
- Patient identifiers and financial account data must not enter images, CI logs, Terraform state, Kubernetes manifests, provenance or flow-log labels.
- Production has no public Kubernetes API administration, no public PaaS data endpoints and no stored cloud credential in CI.
- RPO 0 for Terraform state and deployed release metadata; regional platform RTO 60 minutes. State restore and DNS/failover require rehearsal.
- Use current prices from the chosen Azure India region and record the date/SKU. Do not present forecast pricing as an invoice.

## Required architecture

1. Build minimal non-root multi-stage images with read-only root filesystems, dropped Linux capabilities, health probes and graceful shutdown.
2. Use an AKS Deployment with resource requests/limits, topology spread or anti-affinity, PodDisruptionBudget, autoscaling rationale, NetworkPolicy and immutable image digest.
3. Provision network, AKS dependencies, identities, DNS and private endpoints with Terraform. Use remote Azure Blob state, native locking, Entra/OIDC authentication, versioning/recovery controls and separate state boundaries.
4. Separate untrusted PR CI from trusted build and protected production deployment. Pin third-party actions, build once, publish SBOM/provenance and promote the same digest.
5. Federate the exact protected deployment workflow to a narrowly scoped Azure principal. Use distinct AKS workload identities for API and worker; neither may assign roles.
6. Place edge, application, private endpoints and data in intentional segments. Document every allowed source/destination/protocol/port and deny every unrequired flow.
7. Resolve each PaaS hostname privately from AKS and the DR path. Public network access is disabled only after caller/DNS tests pass.
8. Correlate source SHA, image digest, attestation, Kubernetes rollout revision and runtime telemetry without logging tokens or regulated payloads.

## Capacity evidence

Calculate average and forecast peak requests/second, bandwidth at p50 and p99 scenarios, normal/zone-loss pod placement, total CPU/memory requests, GPU rollout capacity, subnet/IP headroom, NAT port/egress assumptions, registry pull demand and log volume. Label each number as requirement, measurement, forecast, assumption or derivation. Run a load test and report environment, duration, concurrency, dataset, percentiles, error/shed rate and limitations; do not generalize laptop numbers to Azure.

## Mandatory executable evidence

1. Compile/test both applications and scan dependencies/images with recorded tool/database versions.
2. Build the same Dockerfile twice with pinned inputs; explain any digest difference and make the build reproducible where feasible.
3. Prove the container runs as non-root, cannot write root filesystem, receives termination and exposes only the intended port.
4. Validate manifests offline and server-side against a disposable compatible cluster; run policy tests for digest pin, probes, resources, security context and forbidden privilege.
5. Run `terraform fmt`, `validate`, saved plan and policy checks. A production plan with destroy/replace, public IP, wildcard role or public PaaS access must require explicit recovery/security evidence or fail.
6. Change a Terraform resource address using a `moved` block and prove plan shows no remote replacement. Import one pre-existing disposable resource and reconcile to a no-unexpected-change plan.
7. Generate provenance/SBOM for an image and verify subject digest plus expected issuer/repository/workflow identity before admission.
8. Demonstrate an altered artifact/digest, wrong signer identity and mutable tag are rejected.
9. From the API identity, prove required secret/data operation succeeds while write, unrelated tenant resource and role assignment fail.
10. Test flow matrix: edge→API allowed; API→required PaaS allowed; ingress→database denied; worker→API-admin denied; internet→private endpoint denied.
11. Verify private DNS from workload and DR/hybrid test point; deliberately break zone link/forwarding and diagnose it in the documented sequence.
12. Execute canary, failed-probe rollout, drain/zone disruption and rollback/roll-forward with backward-compatible database migration.

## Failure and recovery drills

- Kill a pod during a 60-second in-flight request and record graceful termination versus dropped request.
- Remove one zone's schedulable nodes and prove remaining capacity meets the stated invariant or sheds predictably.
- Exhaust a test subnet/IP budget and show monitoring plus expansion/runbook response.
- Block registry/private DNS/Key Vault separately and distinguish scheduling, resolution, network and authorization symptoms.
- Interrupt Terraform after a disposable remote create; inspect remote state/lineage/lock and reconcile without blind recreation or force unlock.
- Revoke the deployment federation/role and prove production deploy fails closed while running service remains healthy.
- Route a private-endpoint response asymmetrically through a stateful firewall and use effective routes/logs to locate it.
- Restore state/DNS/configuration from protected evidence and measure RPO/RTO; record gaps rather than declaring success.

## Deliverables

1. Threat model, trust boundaries, data classification and abuse cases.
2. Architecture, DNS resolution and packet-flow diagrams with failure domains.
3. Versioned application, Docker, Kubernetes and Terraform source.
4. CI workflows, action/dependency pins, SBOM, provenance and verification policy.
5. RBAC matrix and network-flow matrix with positive/negative automated tests.
6. Capacity/cost worksheet and load-test report with reproducible method.
7. Captured plans, test outputs, digests, rollout histories and failure-drill evidence.
8. Operational runbooks for credential compromise, DNS/network failure, rollout, state recovery and regional DR.
9. Audit-evidence index with retention/access controls and no regulated payloads.
10. A 25-minute oral defense followed by a 15-minute incident scenario.

## Mastery gates

- Production runs the exact verified digest; no rebuild or mutable tag crosses environments.
- A PR/fork cannot obtain production token, mutate trusted cache or execute on a privileged persistent runner.
- Every workload has a distinct identity with smallest actions and scope; negative tests prove forbidden access.
- Reachability and authorization are tested independently; “private” is never used as proof of permission.
- Private endpoint, public-access setting, DNS and hybrid/DR resolution are all explicit and tested.
- Kubernetes availability claims account for requests, limits, placement, disruptions, probes and zone-loss capacity.
- Terraform state is encrypted/access-controlled/versioned/recoverable; address refactors/imports show no unintended replacement.
- Rollback includes data/schema compatibility, not only an old image.
- Every metric and price has method/date/environment; every assumption is labeled.
- Security evidence contains neither credentials nor healthcare/financial payloads.

## Rubric (100)

| Area | Points |
|---|---:|
| Containers and Kubernetes runtime correctness | 18 |
| Terraform state, policy and safe change | 18 |
| CI/CD provenance and immutable promotion | 18 |
| Identity least privilege and federation | 16 |
| Network segmentation, private DNS and egress | 16 |
| Capacity, resilience and recovery evidence | 10 |
| Privacy, reproducibility and oral defense | 4 |

Pass at 80+, with every mastery gate mandatory.
