# Kubernetes from Control Loops to Production Operations

**Parent:** 05 — Cloud Platform  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus manifest exercises

## 1. FOUNDATIONS

Kubernetes is an API-driven control system for running containerized workloads across machines. You declare desired state—four replicas of this pod template, reachable through a stable service—and controllers continuously compare it with observed state and act to reduce the difference. This is **reconciliation**. Kubernetes is not a script that starts containers once; it is a set of level-based control loops that tolerate repeated events and partial failure.

The architectural lineage includes Google's Borg and Omega. Kubernetes made many concepts portable and extensible: declarative objects, labels/selectors, pods, controllers, scheduling, service discovery and custom resources. Its power comes with distributed-systems behavior. API writes may be observed asynchronously by controllers; a Pod name/IP is ephemeral; “created” does not mean “ready”; a controller can replace an object; and multiple controllers interact.

The **control plane** stores and reconciles desired state. The API server authenticates, authorizes and admits requests, validates objects and exposes watch APIs. `etcd` stores cluster state and requires strong operational protection. The scheduler binds unscheduled Pods to nodes based on requests, constraints and policies. Controller managers run reconciliation loops. Cloud controller integrations manage provider resources.

A **node** runs `kubelet`, a container runtime through CRI, and networking/service components such as kube-proxy or an eBPF implementation. Kubelet ensures assigned Pod containers/volumes/probes run. Kubernetes does not normally build images; it pulls an immutable image reference from a registry.

A **Pod** is the smallest schedulable unit: one or more containers sharing network namespace/IP/ports and attached volumes. Containers in a Pod communicate over localhost and share fate/scheduling. Put containers together only when they form one tightly coupled instance (application plus a necessary sidecar), not because they belong to one business domain. Scaling a Pod scales all its containers together.

Kubernetes supplies orchestration primitives, not application correctness. It can restart a crashed payment service but cannot know whether a timed-out gateway call charged a card. It can reschedule a Kafka consumer but duplicates still require idempotency. It can store a Secret object but base64 is not encryption. Senior design joins Kubernetes mechanics with transactions, deadlines, identity, supply-chain and capacity constraints.

This lesson targets current upstream behavior visible in Kubernetes v1.35 documentation where version-sensitive. Managed distributions may lag or add features; verify cluster/server version and feature gates before using fields such as in-place Pod resize.

## 2. CORE MECHANICS

### 2.1 API objects, spec/status and reconciliation

Objects have `apiVersion`, `kind`, metadata, desired `spec` and controller-reported `status`. Metadata includes unique UID, `resourceVersion`, generation, labels, annotations, owner references and finalizers. `resourceVersion` supports optimistic API concurrency/watch position; it is not a semantic application version.

Controllers are level-based: they repeatedly drive observed state toward desired state. A Deployment wants four ready Pods; if a node dies, ReplicaSet creates replacements. Events may duplicate or be missed between lists/watches, so controllers must reconcile current truth idempotently rather than depend on exactly one notification.

Use declarative server-side apply/GitOps with field ownership and review. Editing a generated Pod is futile because its owner recreates it. Change the Deployment template. Status is observed, not user-authored desired state.

### 2.2 Pods and lifecycle

A Pod is scheduled once to one node; it is not moved. On failure a controller creates a new Pod with new UID/IP. **Pod phase** (`Pending`, `Running`, `Succeeded`, `Failed`, `Unknown`) is coarse and not an application health model. Container states include Waiting/Running/Terminated with reasons; restart count matters.

Init containers run sequentially before app containers and are good for finite setup, not dependency polling loops that can deadlock rollout. Sidecars share lifecycle/resources/network. Native sidecar semantics are version-sensitive; verify. Ephemeral containers support debugging and are not restarted like regular containers.

`emptyDir` begins with Pod and disappears with it. A memory-backed `emptyDir` counts against memory, and current Kubernetes docs warn an unbounded tmpfs can consume up to the Pod/container memory limit (or node if no limit). Set `sizeLimit`, while recognizing enforcement/accounting details and memory limit still matter.

### 2.3 Workload controllers

**Deployment** manages interchangeable stateless Pods through ReplicaSets and rolling updates. **StatefulSet** provides stable ordinal identity, ordered operations and per-Pod volume claims; it does not make software distributed/consistent automatically. **DaemonSet** places Pod on selected nodes (agents/device plugins). **Job** runs finite work to completion; **CronJob** creates Jobs on schedule and can miss/duplicate around controller failures, so task is idempotent. Kubernetes documentation does not promise exactly-once cron execution.

For a 90-minute training job, a Job with checkpointing, backoff limit, active deadline and stable operation identity is more appropriate than a Deployment. For a web API, Deployment. For Kafka brokers/databases, StatefulSet is only one layer; use a proven operator/managed service and understand quorum/storage/fencing.

### 2.4 Labels, selectors and ownership

Labels identify/query objects and power selectors for Services, Deployments, PDBs, NetworkPolicies and topology. Selector mistakes are dangerous: a Service selecting no Pods causes outage; selecting another tenant/app leaks traffic; overlapping Deployment selectors can fight. Deployment selector must match template labels and is effectively immutable for safe operation.

Use recommended application labels and separate identity (`name`, `instance`, `component`) from mutable version. Annotations hold non-identifying metadata such as checksums/tool ownership, not secrets. Owner references drive garbage collection; finalizers delay deletion until cleanup controller completes. A stuck finalizer can leave object Terminating—investigate owner/controller before removing it manually.

### 2.5 Scheduling, requests and limits

Scheduler places Pods based primarily on **requests**, not live usage. Current docs state sum of requests must fit node allocatable even if actual usage is low. CPU `500m` is half a CPU; memory `768Mi` is binary mebibytes. Requests reserve scheduling capacity/drive QoS and HPA utilization denominator; limits are runtime ceilings.

CPU limit is enforced by throttling, not Pod termination. Memory is incompressible; exceeding cgroup limit can OOM-kill a container. Using more than request on a pressured node increases eviction risk. Limit without request may cause request to default to limit when no admission default intervenes, reducing scheduling density unexpectedly.

Pod requests/limits sum regular containers (init-container scheduling has max/specific rules). Sidecar resource is not free. Ephemeral-storage requests/limits cover writable layers/logs/`emptyDir` as accounted; node disk/inode pressure causes eviction. Memory-backed `emptyDir` counts as memory.

QoS classes: **Guaranteed** when every relevant container has equal CPU/memory request=limit; **Burstable** when at least one request/limit but not Guaranteed; **BestEffort** when none. QoS influences eviction priority but is not an availability guarantee. PriorityClass affects scheduling/preemption; careless high priority can evict critical workloads or make drains impossible.

Kubernetes v1.35 documentation marks in-place container resource resize stable; older clusters require replacement Pods and provider/runtime support may vary. VPA recommendations/restarts can conflict with HPA when both use CPU; design ownership.

### 2.6 Resource sizing example

Four API Pods each request 500m/768Mi and limit 2 CPU/1Gi. Scheduler reserves 2 CPU and 3 GiB memory total; allowed maxima aggregate to 8 CPU/4 GiB, which node may not have simultaneously if limits are overcommitted. At 20 HPA replicas: 10 requested CPU, 15 GiB requested memory; maxima 40 CPU/20 GiB.

If safe tested capacity is 350 RPS/Pod and peak 4,000 with 25% headroom, normal need 15 Pods—not four. HPA minimum must cover immediate peak/failure capacity because scale-up has measurement, scheduling, image-pull and startup delay. Autoscaling is not instant capacity.

For Java, 1Gi memory limit and `MaxRAMPercentage=70` leaves about 307Mi for nonheap/native before other details; load/soak measure RSS. CPU limit 2 can throttle burst even if node idle above quota. Monitor `container_cpu_cfs_throttled_seconds_total`/runtime equivalents and cgroup metrics.

### 2.7 Probes

**Startup probe** suppresses liveness/readiness failure evaluation until startup succeeds; ideal for slow JVM/model loading. In manifest, period 5 × failureThreshold 24 allows roughly 120 seconds before startup failure (plus timeout/scheduling details). **Readiness** controls whether Pod endpoint is ready for Service traffic. **Liveness** restarts a container when local unrecoverable state persists.

Do not make liveness call database/identity/Kafka. Dependency outage would restart all Pods, add cold load and not repair dependency. Liveness checks local event-loop/progress. Readiness may account for inability to serve the path, with hysteresis and cheap checks. An overloaded liveness endpoint sharing saturated pool can cause cascade; reserve capacity and choose thresholds from measurements.

HTTP, TCP, exec and gRPC probes have different semantics. `timeoutSeconds`, initial/period/failure/success thresholds matter. A TCP connect proves listener, not business readiness. Exec forks/processes and may be expensive. Probes originate from kubelet/network context; secure endpoint without requiring unavailable external auth.

### 2.8 Termination and graceful shutdown

Deletion sets termination grace, endpoint readiness is updated, kubelet runs `preStop` (if configured) then sends TERM to PID 1, waits remaining grace, then KILL. Exact ordering/concurrent control-plane propagation creates races: traffic may still arrive briefly. Application stops accepting, drains within budget and makes work idempotent.

The example uses 45-second grace and a five-second preStop sleep to allow endpoint propagation. This assumes runtime image has `/bin/sh`; distroless would fail the hook. Prefer application readiness/drain endpoint or exec available binary where appropriate, and test actual load balancer behavior. `preStop` time counts inside grace.

Do not set huge grace without considering rollout/drain. For workers, release/expire leases and checkpoint; forced termination remains possible. PDB affects voluntary eviction, not direct Pod deletion, rollout controller or node crash.

### 2.9 Deployments and rolling updates

Deployment rolling strategy `maxUnavailable:0,maxSurge:1` for replicas=4 may run up to five Pods and aims to keep four available during healthy rollout. It needs spare cluster/downstream capacity. New readiness gates promotion to available; `minReadySeconds` can require stable readiness. `progressDeadlineSeconds` defaults to 600 per current docs and marks stalled rollout but does not automatically roll back.

Rolling update allows old/new versions coexist. API/event/database compatibility must be expand–contract. A bad readiness probe can send traffic early; a probe that never succeeds stalls and leaves surge capacity consumed. `revisionHistoryLimit` supports rollout history but image digest/config/data changes may make rollback unsafe.

Canary/blue-green require traffic routing and metrics beyond basic Deployment. Avoid deploying mutable tags: Pods started at different times can run different bytes. Pin digest and record provenance.

### 2.10 Services, DNS and traffic

A Service selects Pods and provides stable virtual IP/DNS. ClusterIP is internal; NodePort exposes on nodes; LoadBalancer asks integration for external load balancer. Headless Service returns endpoints for direct discovery/stateful use. Ingress API routes HTTP(S) through an Ingress controller; Gateway API offers richer roles/routes but controller support varies.

`port` is Service port; `targetPort` points to container port/name. Named ports reduce numeric mismatch. EndpointSlices scale endpoint representation. Readiness removes endpoints, but clients keep existing connections and control-plane/LB propagation takes time.

Service load balancing does not guarantee session affinity, exactly-once calls or cross-zone optimality. Client DNS caching, keepalive and HTTP/2 can imbalance. Source/destination IP behavior varies by kube-proxy/eBPF/cloud settings. Measure.

### 2.11 NetworkPolicy

NetworkPolicy is enforced only if the cluster networking implementation supports it. A policy selecting a Pod for Ingress/Egress isolates it for that direction; allowed traffic is additive across policies. The sample policy selects app and declares both directions with no allow rules: default deny. Therefore it is intentionally not a complete deployable connectivity policy until environment-specific DNS, ingress-controller and database/API egress rules are added.

Default deny then explicit allow is safer. Remember DNS egress, monitoring/telemetry and control-plane/cloud metadata. Avoid broad `0.0.0.0/0` egress for sensitive services. NetworkPolicy works at network identity (pods/namespaces/IP blocks) and does not replace TLS/workload identity/application authorization. Existing connections and implementation behavior should be tested.

### 2.12 ConfigMaps and Secrets

ConfigMap stores nonconfidential configuration. Secret stores confidential bytes but is base64-encoded, not automatically encrypted at rest. Secure etcd encryption, RBAC, audit, node access and backups. Anyone able to create a Pod under an identity that can mount a Secret may extract it even without direct Secret GET—current Kubernetes security guidance highlights this privilege path.

Mount projected/CSI secrets rather than environment variables when rotation is needed; processes often read env only at startup and env leaks via diagnostics. Use external secret manager with workload identity when appropriate. Never commit Secret YAML plaintext/base64. Avoid `list` permission on Secrets because list returns content.

ConfigMap/Secret volume updates are eventually projected, but `subPath` mounts do not receive updates in normal documented behavior; application must reload safely. Immutable config plus rollout checksum gives auditability. A config change can break all replicas—canary it.

### 2.13 ServiceAccounts, RBAC and cloud workload identity

ServiceAccount is namespaced workload identity. Default ServiceAccount has minimal discovery permissions in a normal RBAC cluster but its credential is mounted by default unless disabled. Sample sets `automountServiceAccountToken:false` because API access is not needed. If needed, create dedicated SA and Role with exact verbs/resources/resourceNames where feasible, then RoleBinding.

Avoid ClusterRoleBinding and wildcard verbs/resources. Kubernetes permissions to create Pods can become permission to use their service accounts/mount accessible secrets. `impersonate`, `bind`, `escalate`, node/proxy and exec permissions are powerful.

Modern projected ServiceAccount tokens are short-lived, audience-bound and rotated. Long-lived Secret tokens are discouraged. For Azure/AWS/GCP APIs, federate workload identity from ServiceAccount/OIDC rather than store cloud client secret. Check audience, subject namespace/name and least-privilege cloud role.

### 2.14 Pod security

Pod Security Standards define Privileged, Baseline and Restricted profiles; enforce via Pod Security Admission namespace labels or policy engine. PodSecurityPolicy was removed in Kubernetes v1.25—do not recommend it.

Restricted-aligned workload uses non-root numeric user, `allowPrivilegeEscalation:false`, drops all capabilities, RuntimeDefault/Localhost seccomp, and avoids host namespaces/paths/privileged. Read-only root filesystem is an additional good practice though application needs declared writable volumes. The sample meets these application-side controls.

Admission should require trusted registries/digests/signatures/provenance, resource bounds, probe policy and restricted security settings. Policy changes can block urgent deploys; version/test/audit exemptions. Node/kubelet/runtime and control plane security remain cluster-owner duties.

### 2.15 Persistent storage

PersistentVolume (PV) represents storage; PersistentVolumeClaim requests it; StorageClass drives dynamic provisioning. Access modes describe how volume may be mounted, not necessarily application concurrency semantics. `ReadWriteOnce` means one node, potentially multiple Pods on that node; `ReadWriteOncePod` provides one-Pod restriction when supported.

Volume topology constrains scheduling: zonal disk cannot attach in another zone. `WaitForFirstConsumer` delays provisioning until scheduler knows topology. StatefulSet volumeClaimTemplates create per-ordinal PVCs; scaling down/deleting may retain PVCs according to policy. Snapshots are not application-consistent unless coordinated; test restores.

Ephemeral containers/pods and persistent volumes have separate lifecycles. A database operator needs replication, quorum, backups, anti-affinity, disruption and fencing beyond PVC.

### 2.16 Topology, affinity, taints and disruption

Node selectors/affinity constrain placement. Pod anti-affinity can spread replicas but is scheduler-expensive at scale; topologySpreadConstraints directly limit skew. Sample requires max skew 1 across zones with `DoNotSchedule`. If only one zone/node label available, Pods may remain Pending—availability constraint requires actual capacity in every domain.

Taints repel Pods; tolerations permit but do not force placement. Use dedicated GPU/regulated nodes with taints plus affinity, but toleration alone is not isolation. RuntimeClass can select sandbox/runtime overhead.

PDB limits simultaneous **voluntary** disruptions through Eviction API. It cannot prevent node crash and does not constrain Deployment rolling updates; current docs explicitly note direct deletion/deployment deletion bypass. Four replicas/maxUnavailable1 allows one voluntary eviction if health/intended counts permit. `AlwaysAllow` unhealthy eviction avoids a broken Pod blocking drain, as current docs recommend in many cases.

PDB too strict (`minAvailable:100%`) can block node maintenance. PDB plus topology plus capacity plus rollout strategy must be feasible. Quorum services calculate safe disruption from membership, not generic percentage.

### 2.17 Horizontal, vertical and node autoscaling

HPA periodically adjusts replica target from metrics. CPU utilization target is usage/request; missing or inflated requests distort it. Sample target 60% with min 4/max 20 and five-minute scale-down stabilization. If request is 500m and average use 400m, utilization 80%; desired replicas roughly current×80/60 before algorithm tolerances/missing metrics.

HPA reacts after load. For sharp bursts use sufficient minimum, predictive/scheduled scaling where justified, queues/admission and fast startup. Max must respect database/provider capacity. Scaling Pods may require node autoscaler to provision nodes, adding minutes and image pulls.

VPA recommends/changes requests, sometimes restarting Pods depending mode/version. HPA on CPU + VPA changing CPU request creates feedback; use compatible modes/custom external metrics. Node autoscaler provisions cluster capacity based on Pending Pods/requests; it cannot fix Pods blocked by impossible affinity/PVC/quota.

For Kafka/GPU jobs, scale on lag/oldest age and sink/GPU capacity, not only CPU. Multiple replicas cannot split one hot partition/job.

### 2.18 Namespaces, quotas and multi-tenancy

Namespaces scope names, RBAC, quotas and policies; they are not hard security boundaries against cluster-admin/node compromise. ResourceQuota caps aggregate requests/limits/object counts; LimitRange defaults/bounds individual resources. Without quotas one tenant can consume nodes/PVCs/Services.

Strong multi-tenancy may require separate clusters/accounts/subscriptions, dedicated nodes and network/identity/data controls. Healthcare/fintech production, dev and untrusted training code should not share broad credentials. Audit Kubernetes API, exec/port-forward/secret access, admission exemptions and workload identity.

### 2.19 Troubleshooting sequence

Start from desired object downward:

1. `kubectl get deployment,rs,pods -o wide`; inspect generation/status/conditions.
2. `kubectl describe pod` events: scheduling, pull, mount, probe, eviction.
3. Container status: waiting/terminated reason, exit, restart, last state; `logs --previous`.
4. Pending: requests vs allocatable, taints/tolerations, affinity/spread, PVC, quota.
5. CrashLoop: command/config/permissions/dependency, OOM, probes, signal.
6. Service: selector labels, EndpointSlices/readiness, ports, DNS/network policy/LB.
7. Node: conditions/pressure/runtime/kubelet/CNI/CSI, but avoid broad node access.
8. Compare exact image digest/config/RBAC/admission and recent events/rollout.

Events expire and are not an audit log. Export metrics/logs/traces/audit to durable systems. Avoid `kubectl exec` as routine repair; use ephemeral debug containers under audited RBAC and fix declaratively.

## 3. WORKED PROBLEMS

### Problem 1 — Requests versus limits

**Statement.** Ten Pods request 500m/768Mi and limit 2 CPU/1Gi. What does scheduler reserve and what may runtime allow?

**Solution.** Scheduler accounts 5 CPU and 7.5 GiB requested memory (7680Mi). Aggregate limits are 20 CPU and 10 GiB, which may exceed node allocatable via overcommit. CPU above quota throttles; memory limit crossing can OOM kill. Node pressure can evict Pods using above requests according to priority/QoS.

**Mistake caught.** Scheduling on limits/live averages only.

### Problem 2 — HPA CPU math

**Statement.** Four replicas request 500m each, average use 400m, target 60%.

**Solution.** Utilization 80%. Simplified desired `ceil(4×80/60)=ceil(5.333)=6`, subject to HPA tolerance, missing/unready metrics and behavior policies. If requests were incorrectly 100m, reported utilization 400% and scaling signal is distorted.

**Mistake caught.** CPU target as percentage of limit/node.

### Problem 3 — Probe cascade

**Statement.** Liveness checks database; DB slows 20 seconds; all Pods restart.

**Solution.** Remove dependency from liveness; check local progress. Readiness may fail/degrade DB-dependent path with thresholds. Startup probe protects cold init. Reserve health endpoint resources. Restarts add cold connections/cache load and cannot fix DB. Test outage with graceful shedding.

**Mistake caught.** Deepest possible liveness equals best health.

### Problem 4 — Rolling capacity

**Statement.** Four replicas, `maxUnavailable=0,maxSurge=1`, each requests 2Gi; cluster has only 1Gi spare.

**Solution.** Fifth Pod cannot schedule, so rollout stalls while old four stay available; progress deadline eventually marks failure. Add schedulable surge headroom or choose a strategy accepting temporary unavailability (`maxUnavailable=1`) only if capacity/SLO permits. HPA/PDB do not conjure node memory.

**Mistake caught.** Assuming zero-downtime rollout without spare cluster capacity.

### Problem 5 — PDB misconception

**Statement.** Four replicas/PDB maxUnavailable1. Two nodes crash.

**Solution.** PDB cannot prevent involuntary node failures; both Pods can disappear. Controller schedules replacements if zones/nodes/capacity allow. PDB constrains voluntary Eviction API operations and counts involuntary unavailability when deciding further voluntary eviction.

**Mistake caught.** Calling PDB an availability guarantee.

### Problem 6 — NetworkPolicy outage

**Statement.** Apply egress default deny; app cannot resolve DNS or reach PostgreSQL.

**Solution.** NetworkPolicy is working. Add narrow DNS egress to cluster DNS namespace/pods/ports UDP/TCP 53 as implementation requires, and PostgreSQL egress to selected namespace/pods or controlled CIDR/port 5432. Add explicit ingress from gateway. Test CNI enforcement and deny unauthorized paths.

**Mistake caught.** Default deny without dependency inventory.

### Problem 7 — Secret permissions

**Statement.** Developer cannot GET Secret but can create Pods using privileged ServiceAccount in namespace.

**Solution.** They can create a Pod that mounts/prints Secret available to that SA, effectively reading it. Restrict Pod creation/use of service accounts, separate namespaces, least RBAC, admission and external workload identity; audit exec/logs. Direct Secret verb analysis alone is insufficient.

**Mistake caught.** Treating RBAC verbs independently of privilege escalation paths.

### Problem 8 — Zone spread Pending

**Statement.** Four replicas require `maxSkew:1, DoNotSchedule` across zone label, but only zone A has suitable nodes.

**Solution.** Scheduler cannot satisfy spread as intended; Pods remain Pending rather than concentrate. Provide capacity/labels in other zones, relax to ScheduleAnyway if risk accepted, or alter constraints. Do not delete constraint blindly; it encoded zone failure intent.

**Mistake caught.** Reading Pending as need for more replicas instead of impossible topology.

### Problem 9 — Stateful storage failover

**Statement.** Stateful Pod with zonal RWO disk dies with its zone; scheduler tries another zone.

**Solution.** Disk may not attach cross-zone, so Pod remains Pending. StatefulSet stable identity/PVC is not cross-zone replication. Use application/data-service replication across zones, appropriate storage class/topology and tested failover/backups. RWO describes mounting access, not replicated availability.

**Mistake caught.** Assuming PVC makes data highly available.

## 4. REAL-WORLD / APPLIED CONTEXT

**Kubernetes v1.35 resources.** Current upstream docs say scheduler uses requests, CPU limits throttle rather than terminate, memory limits can lead to kill, memory-backed `emptyDir` counts as memory, and in-place container resize is stable in v1.35. Managed clusters may run older versions; gate manifests/operations accordingly.

**Disruption behavior.** Upstream docs explicitly say PDBs govern voluntary Eviction API behavior, not all disruptions, and Deployment rolling updates are controlled by their own strategy. A five-replica example with four required permits one voluntary disruption. This prevents the common claim that a PDB blocks rollout or node crash.

**Hardened Java API manifest.** `workload.yaml` defines four replicas, immutable-reference syntax, requests/limits, three probes, 45-second grace, restricted security context, zone spread, PDB, HPA, Service and default-deny policy. It intentionally uses a placeholder registry digest and no allow NetworkPolicy; replace with a signed real digest and environment-specific least-privilege flows before deployment.

## 5. COMPARISON TABLE

| Controller | Identity/lifecycle | Scaling | Best fit | Key trap |
|---|---|---|---|---|
| Deployment | interchangeable Pods | replicas/HPA | stateless API/worker | rolling coexistence compatibility |
| StatefulSet | stable ordinal/PVC association | ordered replicas | stateful clustered member | not automatic replication/quorum |
| DaemonSet | one per eligible node | node count | agents/device plugins | broad host privilege |
| Job | finite completion | parallelism/completions | batch/migration | retries duplicate side effects |
| CronJob | schedules Jobs | per schedule | recurring task | missed/duplicate starts; idempotency |

| Probe | Failure action | Should test | Must not imply |
|---|---|---|---|
| Startup | delays other probes/restarts on threshold | startup completed enough | dependencies always healthy |
| Readiness | removes endpoint | can serve traffic/path now | restart will help |
| Liveness | restarts container | local unrecoverable/progress failure | every downstream reachable |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Kubernetes moves Pods.** It creates replacements with new identity/IP.
2. **Running phase means ready.** Readiness and app SLI are separate.
3. **Requests are minimum runtime allocation.** They drive scheduling/shares; actual can vary to limits/contention.
4. **CPU limit kills.** It throttles; memory pressure/limit can kill/evict.
5. **HPA percent is limit utilization.** Resource HPA CPU utilization uses request denominator.
6. **Autoscaling replaces baseline headroom.** Metrics/node/image/startup lag behind bursts/failures.
7. **Liveness checks dependencies.** It can restart fleet and amplify outage.
8. **PDB prevents all downtime.** It governs voluntary eviction only and not Deployment rollout.
9. **PDB 100% is safest.** It can block maintenance indefinitely.
10. **StatefulSet makes database HA.** Stable names/PVCs do not provide consensus/replication/backups.
11. **RWO means one Pod.** It commonly means one node; use RWOP where supported/appropriate.
12. **Service sends only to Pods by name.** Selectors/EndpointSlices/readiness govern; labels can misroute.
13. **NetworkPolicy always works.** CNI must enforce; default deny needs explicit DNS/dependencies.
14. **Secret is encrypted because base64.** Configure etcd encryption/RBAC/external manager.
15. **No Secret GET means no secret access.** Pod creation/SA use can mount/exfiltrate.
16. **Namespace is hard tenant boundary.** Nodes/control-plane/cluster-admin/shared policies remain.
17. **PodSecurityPolicy is current.** Removed v1.25; use Pod Security Admission/policy engines.
18. **Mutable image tag is okay with pull policy.** Replicas can run different bytes; use digest.
19. **kubectl exec repair is durable.** Controller replaces drift; fix declaration/image.
20. **More replicas fix hot partition/DB bottleneck.** Shared bottleneck and ordering cap remain.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Desired spec → API/etcd → scheduler/controllers → kubelet/runtime; reconciliation is repeated/idempotent.
- Pod is schedulable shared network/volume unit; replacement gets new UID/IP.
- Deployment stateless; StatefulSet stable identity/PVC; Job finite; CronJob can duplicate/miss.
- Scheduler uses requests; CPU limits throttle; memory limits can OOM; ephemeral storage can evict.
- Startup protects slow boot; readiness controls endpoints; liveness only restart-helpful local failure.
- Rollout needs surge/available capacity and old/new schema/API compatibility.
- PDB only voluntary eviction, not node crash/direct delete/Deployment rollout.
- Service selector + readiness → EndpointSlices; port ≠ targetPort; IPs ephemeral.
- Default deny NetworkPolicy plus explicit DNS/ingress/egress; requires enforcing CNI.
- Secret base64 ≠ encryption; Pod-create/SA permissions can imply extraction.
- Dedicated SA, short projected token only if needed, least RBAC/cloud workload federation.
- Restricted: non-root, no escalation, drop ALL, RuntimeDefault seccomp, no host privilege.
- HPA resource utilization uses requests; min handles sudden load, max protects downstream.
- PVC/storage topology ≠ replicated HA; test snapshots/restores/fencing.
- Troubleshoot owner→Pod events/status→logs previous→Service endpoints/network→node.

## 8. PRACTICE SET FOR SELF-TEST

1. Calculate requested/limited CPU and memory for 18 replicas at 750m/1Gi requests and 2CPU/2Gi limits.
2. Six replicas use 600m each against 400m request; HPA target 75%. Estimate desired replicas.
3. Design startup/readiness/liveness for a service loading a 90-second model and calling a policy DB.
4. Choose rolling parameters for 10 replicas when cluster can host only two surge Pods and SLO permits one unavailable.
5. Explain PDB behavior during one unhealthy Pod, node drain and direct Pod delete.
6. Write the dependency inventory needed before turning on egress default deny for a Spring API.
7. Design least-privilege SA/RBAC for a controller that only gets/lists/watches ConfigMaps named by label in one namespace; state RBAC limitation.
8. Diagnose Pending Pod with PVC, GPU request, taint, zone affinity and quota systematically.
9. Design GPU training Job termination/checkpoint/idempotency and queue-based autoscaling boundaries.
10. Explain why four Pods evenly spread across zones can still share a single failure domain.

## 9. CURATED RESOURCES

1. Kubernetes Docs, [Cluster Architecture](https://kubernetes.io/docs/concepts/architecture/). Authoritative control-plane/node component responsibilities and object flow.
2. Kubernetes Docs, [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/). Current request/limit scheduling, cgroups, tmpfs and v1.35 resize semantics.
3. Kubernetes Docs, [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) and [Probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/). Exact states, restart, termination and probe behavior.
4. Kubernetes Docs, [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/). ReplicaSet ownership, rolling math, progress and rollback behavior.
5. Kubernetes Docs, [Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/). Voluntary/involuntary distinction and PDB boundaries.
6. Kubernetes Docs, [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/). Control algorithm, request denominator, missing metrics and behavior policies.
7. Kubernetes Docs, [Services, Load Balancing, and Networking](https://kubernetes.io/docs/concepts/services-networking/). Service/EndpointSlice/DNS/Ingress/Gateway and NetworkPolicy mechanics.
8. Kubernetes Docs, [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/) and [Secrets good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/). Current restricted controls and identity/secret escalation boundaries.
9. Burns et al., “Borg, Omega, and Kubernetes,” ACM Queue 2016. Historical control/scheduling lineage and lessons.
10. Hightower, Burns and Beda, *Kubernetes: Up & Running*, 3rd ed., chapters 2–12. Cohesive operational walkthrough supplementing exact upstream references.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Containers.** Pods orchestrate image/runtime, cgroup, signal, filesystem and security primitives.
2. **Capacity-Driven Design.** Requests, replica minima, topology and HPA limits derive from measured capacity/failures.
3. **Failure Semantics.** Probes, termination, retries and rescheduling cannot erase ambiguous side effects.
4. **Data Migrations.** Rolling old/new Pods require expand–contract schemas/events.

### After

1. **Terraform and IaC.** Clusters, node pools, identities, networks and managed dependencies become declarative.
2. **CI/CD Supply Chain.** Signed image digests and manifests flow through policy-gated rollout.
3. **Cloud Identity and Networking.** Workload federation, private endpoints, DNS, ingress/egress and zones surround Pods.
4. **SRE/Observability.** Kubernetes/controller/probe/resource signals integrate with service SLIs and incident response.

---ANSWER KEY BELOW---

1. Requests: `18×0.75=13.5 CPU`, `18 Gi`. Limits: `36 CPU`, `36 Gi`. Scheduler needs requests plus system/DaemonSet headroom; node cannot necessarily supply all aggregate limits simultaneously.
2. Utilization per Pod `600/400=150%`. Simplified desired `ceil(6×150/75)=12`, subject to tolerance, metric readiness and scale policies/max. Verify downstream capacity and that CPU request is correct.
3. Startup `/startup` or local readiness with period 5/failure ≥24 for measured 90s plus margin; liveness local event-loop/process progress only and begins after startup; readiness verifies model loaded and ability to serve, may incorporate bounded policy-path status without restarting on DB outage. Shed/fail closed policy requests safely.
4. `maxSurge:2,maxUnavailable:1`; ensure minimum nine available satisfies the SLO and the cluster has capacity for twelve Pods during rollout. Set readiness/minReady/progress/grace and confirm old/new compatibility. Integer values avoid percentage-rounding surprises; verify downstream connection load from twelve Pods.
5. Unhealthy Pod counts unavailable, so PDB may block further healthy eviction unless `unhealthyPodEvictionPolicy:AlwaysAllow` allows unhealthy removal. Drain uses Eviction API and respects budget; direct delete bypasses PDB. Involuntary failure cannot be prevented but counts against allowed voluntary action.
6. Cluster DNS UDP/TCP, ingress controller/gateway, PostgreSQL/private endpoint, Kafka, Redis, identity/token endpoints, observability collector, secret manager/KMS, object registry/storage, time/CA/OCSP if required, provider metadata explicitly denied or workload identity path, health/admin paths. Resolve selectors/CIDRs and fail behavior.
7. Namespaced Role with get/list/watch on core `configmaps`, RoleBinding to dedicated SA. RBAC cannot restrict list/watch by label selector; `resourceNames` generally helps named get but list/watch require field-selector constraints clients may not enforce as policy. Split namespace/controller or admission/custom authorization for stronger boundary.
8. Describe Pod events first: quota admission, extended `nvidia.com/gpu` allocatable/device plugin, matching labeled zone nodes, taint toleration, node affinity, PVC Pending/storage class/zone binding and requests/allocatable. Check each constraint intersection; autoscaler cannot solve unavailable GPU type/volume topology/quota.
9. Job carries operation ID, checkpoint to durable object store atomically/versioned, handles TERM within grace, retries resume checkpoint and dedupe final registration. Active deadline/backoff/TTL, GPU request/limit, taint/affinity and per-tenant quota. Scale workers/nodes from queue age with max GPUs/budget and artifact/data bandwidth; cancellation state remains durable.
10. They may share one database/Kafka/identity provider, same image/config bug, cloud account quota, region/control plane, CNI/DNS, deployment pipeline/operator credential or tenant hot key. Topology spread covers node/zone placement only.
