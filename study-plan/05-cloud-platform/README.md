# Parent 05 — Cloud Platform

This parent moves from container primitives through orchestration and declarative
infrastructure into secure delivery, identity, and networking.

No Linux, Git, cloud, or platform background is assumed.

## Phase A — Prerequisites

1. [Linux, Shell, Files, and Processes](06-linux-shell-process-filesystem/lesson.md) — command execution, filesystem, permissions, users, processes, signals, services, logs, packages and resource diagnosis.
2. [Git and Collaborative Version Control](07-git-version-control-collaboration/lesson.md) — repositories, commits, branches, merges, rebases, remotes, pull requests, recovery and release history.
3. [Cloud Computing Foundations](08-cloud-computing-foundations/lesson.md) — regions/zones, service models, shared responsibility, compute/storage/database/network/identity, elasticity and cost.
4. [Cloud Networking, DNS, TLS, and Load Balancing](09-cloud-networking-dns-tls-load-balancing/lesson.md) — virtual networks, subnets, routes, filtering, private connectivity, name resolution, certificates, gateways and resilient traffic flow.

## Phase B — Existing advanced sequence

5. [Containers](01-containers/lesson.md) — complete; includes a compilable Java service, hardened multi-stage Dockerfile, and passing static policy verifier.
6. [Kubernetes](02-kubernetes/lesson.md) — complete; includes a six-object hardened workload manifest and passing offline syntax/policy validation.
7. [Terraform and IaC](03-terraform-iac/lesson.md) — complete; includes typed configuration, state/backends, safe refactoring/import, policy and a validated offline plan lab.
8. [CI/CD Supply Chain](04-cicd-supply-chain/lesson.md) — complete; includes pipeline trust boundaries, OIDC, provenance/SBOM, rollout safety, a parsed two-job workflow, and a passing tamper-rejection lab.
9. [Cloud Identity and Networking](05-cloud-identity-networking/lesson.md) — complete; includes Azure RBAC/workload identity, CIDR/routing/NSGs, Private Link/DNS, and six passing deny-by-default policy tests.

After all nine lessons, complete the [Cloud Platform Capstone](CAPSTONE.md), including its mandatory failure drills and mastery gates.
