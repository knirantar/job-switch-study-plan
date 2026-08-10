# Containers from First Principles

**Parent:** 05 — Cloud Platform  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus build/run exercises

## 1. FOUNDATIONS

A container is an ordinary operating-system process started with an isolated view of selected kernel resources and optional resource controls. It is not a miniature virtual machine. On Linux, container processes share the host kernel. **Namespaces** change what processes can see—process IDs, mounts, networking, hostname, users and IPC. **Control groups (cgroups)** account for and limit CPU, memory, process count and I/O. Linux capabilities, seccomp, LSMs such as AppArmor/SELinux and filesystem permissions restrict what the process may do.

A virtual machine virtualizes hardware and boots a guest kernel. A container packages userspace files and execution configuration while sharing the host kernel. Containers usually start faster and pack more densely; VMs provide a stronger kernel boundary and can run a different guest OS. In security-sensitive systems, sandboxed runtimes or microVMs combine image workflow with stronger isolation. “Container versus VM” is not binary: cloud platforms frequently run containers inside VMs.

An **image** is an immutable, content-addressed package of filesystem changes and configuration. A **container** is a runtime instance with writable state layered over the image. The Open Container Initiative (OCI), established in 2015, standardizes image, runtime and distribution formats. Current OCI materials describe an image manifest, optional multi-platform index, filesystem layers and image configuration; a runtime turns an unpacked filesystem bundle/config into a running container.

Images solve repeatable packaging: the same application artifact, runtime and libraries can move from build system to registry to test/prod. They do not make the build automatically reproducible, the software patched, configuration secure or behavior identical across CPU architectures and kernels. Mutable tags, network downloads, timestamps, nondeterministic compilers and unpinned dependencies can produce different bits from the same Dockerfile.

Docker popularized the workflow, but the ecosystem is layered. BuildKit/build tools construct OCI images. Registries distribute blobs/manifests. A high-level engine or Kubernetes CRI implementation manages containers. `containerd`/CRI-O manage lifecycle and images; an OCI runtime such as `runc` creates the namespaced/cgrouped process. Avoid equating “container” with one vendor CLI.

Containers exist to make deployment units explicit and disposable. Configuration and durable state live outside the image. A process should tolerate termination, start from declared inputs, emit observable signals and never assume its writable layer survives rescheduling. This operational contract matters more than “it works with `docker run`.”

## 2. CORE MECHANICS

### 2.1 Linux namespaces

Namespaces isolate identifiers/views:

- PID: process sees its own PID tree; first process is PID 1 inside namespace.
- mount: independent mount table/root filesystem view.
- network: interfaces, routes, ports and firewall namespace.
- UTS: hostname/domain name.
- IPC: System V IPC/POSIX message queues.
- user: maps container UIDs/GIDs to different host IDs.
- cgroup/time namespaces cover other scoped views.

Isolation is selective. A process can still consume shared kernel resources unless cgroups/limits apply. `/proc` shows namespace-scoped processes when mounted appropriately, but the host can see container processes. A kernel vulnerability can cross the boundary; keep host/runtime patched and reduce privileges.

### 2.2 cgroups v2 and resource accounting

cgroups organize processes hierarchically and expose controllers. In cgroup v2, `memory.max` is a hard memory boundary, `memory.current` current charged usage, `cpu.max` quota/period, `cpu.stat` includes throttling data, and `pids.max` bounds process creation (subject to runtime/platform).

Docker documentation states containers have no resource constraints by default and may use host resources. `docker run --memory=768m --cpus=1.5 --pids-limit=256 ...` applies limits. Its CPU example maps 1.5 CPUs to a 100,000 µs period and 150,000 µs quota. CPU quota is a ceiling, not a reservation; CPU shares/weight affects competition rather than guaranteed capacity.

Memory accounting includes more than JVM heap: metaspace, code cache, thread stacks, direct buffers, native libraries, allocator and often page cache. In a 1 GiB container, `-Xmx1g` leaves no room and invites cgroup OOM kill. Start with measured headroom; the example uses `MaxRAMPercentage=70`, but 70% is an explicit starting policy, not universal. Observe RSS, cgroup events and post-GC live set.

An in-process Java `OutOfMemoryError` differs from kernel/cgroup OOM kill. In the latter, process may vanish with exit code 137 (128+SIGKILL 9) conventionally, but inspect runtime/OOM events rather than relying only on code. CPU throttling can raise latency without high node CPU; inspect throttled periods/time.

### 2.3 Image manifests, layers and digests

An OCI manifest references configuration and ordered compressed layer blobs by digest. The configuration contains rootfs diff IDs, environment, entrypoint/command, user, working directory and platform metadata. A multi-platform image index points to manifests for combinations such as linux/amd64 and linux/arm64.

Layers are filesystem change archives. Each Dockerfile instruction can create metadata/layer effects. Runtime combines layers through a union/overlay filesystem and adds a writable layer. Content-addressing deduplicates shared blobs and verifies bytes. A digest pins content; a tag such as `21-jre` is a mutable name.

Deleting a secret in a later layer does not remove it from the earlier blob. Never `COPY secret` then `RUN rm secret`. Use BuildKit secret mounts, dependency credentials scoped to one build instruction, clean context and verify image history/layers. If a secret entered an image/registry, rotate it; deleting a tag may not erase distributed blobs/caches immediately.

### 2.4 Build context and cache

The **build context** is the file tree available to `COPY`/`ADD`. A broad `COPY . .` can send `.git`, credentials, build artifacts and huge datasets to the builder. `.dockerignore` reduces leakage/transfer/cache invalidation. The included Dockerfile copies only `HelloServer.java`; its ignore file excludes class/log/study content.

Build cache reuses steps when inputs/instruction metadata match. Put stable dependency resolution before frequently changing source where tool supports it. For Maven, copy `pom.xml`, resolve dependencies, then source; avoid caching credentials. Package manager operations that need a current index should be in one `RUN`, and caches should be cleaned when they add no runtime value.

Cache improves speed, not proof of reproducibility. Run clean builds periodically and record provenance/SBOM. Network dependency disappearance can break a rebuild unless artifacts are mirrored/pinned.

### 2.5 Multi-stage builds

Build tools expand attack surface and image size. Multi-stage Dockerfiles use multiple `FROM` stages; copy only the compiled artifact into the runtime stage. The supplied example compiles with JDK 21 and runs on a JRE image. The compiler and source do not enter the final image.

For production, pin both base stages to reviewed digests. The example intentionally uses readable tags because a digest must be resolved/updated in your registry/CI; a fake or stale digest would make it unbuildable. CI should resolve approved tag, create a reviewable digest update and continuously rebuild for security fixes. Pinning gives repeatable input; updating gives patch freshness—you need both automation and approval.

Smaller is not automatically safer. A minimal/distroless image reduces packages and shell, but debugging changes and missing CA certificates/time-zone/native libraries can break applications. Choose the smallest trusted maintained base that supports runtime requirements. Vulnerability count alone ignores exploitability/reachability and kernel/shared-host risk.

### 2.6 Dockerfile execution forms

`ENTRYPOINT ["java","-jar","/app/app.jar"]` is exec/JSON form: runtime starts Java directly as PID 1. Shell form `ENTRYPOINT java -jar ...` often starts `/bin/sh -c`, which can alter signal forwarding/argument behavior. Use exec form unless shell expansion is intentionally required.

`ENTRYPOINT` defines executable; `CMD` supplies defaults/arguments and can be overridden. Do not bake secrets into `ENV` or `ARG`; image config/history may expose them. `EXPOSE 8080` documents intended port but does not publish it. At runtime `-p 127.0.0.1:8080:8080` maps host loopback port; binding `0.0.0.0` exposes on host interfaces subject to firewall.

Use `COPY` for files; `ADD` has extra URL/tar semantics that can surprise. Set explicit `WORKDIR`. Use labels for source/revision/licenses where supply-chain tooling expects them.

### 2.7 PID 1, signals and shutdown

PID 1 has special Linux behavior. It must reap orphaned zombie children and handle/forward signals appropriately. A single Java process using exec form normally receives SIGTERM directly; the example registers a shutdown hook and stops its HTTP server with a five-second delay. Test it: send TERM, confirm readiness is removed by orchestrator first, in-flight work drains and exit occurs before grace deadline.

Applications spawning child processes may need a tiny init such as `--init`/tini to reap/forward. Shell wrapper scripts should end with `exec "$@"`. SIGKILL cannot be caught; after grace period runtime may force kill. Therefore durable progress/state must not depend solely on shutdown hook.

Exit code conventions: 0 success; nonzero application failure; `128+signal` commonly reports signal termination (143 for TERM, 137 for KILL). Runtime/orchestrator status provides stronger evidence. Crash loops require backoff; a liveness probe that kills slow startup can perpetuate failure.

### 2.8 Users, capabilities and rootless operation

Container UID 0 is root inside its user namespace/context and may map to host root if user namespaces are absent. It is not harmless. Run numeric non-root (`10001:10001` in example) so identity is stable even if `/etc/passwd` differs. Files copied at build must be readable/writable as required; avoid `chmod 777`.

Drop all capabilities and add only required ones. A web service on 8080 does not need `NET_BIND_SERVICE`. Use `no-new-privileges`, read-only root filesystem, writable tmpfs/volume for explicit paths, seccomp default/stricter profile and AppArmor/SELinux. Avoid privileged mode, host PID/network, Docker socket and broad device mounts: they can effectively grant host control.

Rootless engines/user namespaces reduce host privilege impact but have networking/storage/cgroup limitations depending on platform. They complement, not replace, application authorization and image trust.

### 2.9 Seccomp and kernel attack surface

Seccomp filters syscalls. Docker's default profile blocks selected dangerous calls while allowing common workloads. Denying every unfamiliar syscall without test can break JVM/native libraries. Generate from observed behavior cautiously, then test startup, traffic, GC, diagnostics and shutdown. Linux capabilities split root powers, but capabilities such as `SYS_ADMIN` are extremely broad.

The shared kernel means base-image package CVEs and host-kernel CVEs are different. Scanning image filesystem won't find every host vulnerability; runtime/host patching and node isolation remain required. For untrusted tenant code/model execution, consider gVisor/Kata/microVMs, separate nodes/accounts and egress restrictions.

### 2.10 Filesystem and persistence

Image layers are read-only; container writable layer is ephemeral and often copy-on-write. Writing high-volume logs/data there can consume node disk and perform poorly. Write logs to stdout/stderr for platform collection, with rotation/backpressure at runtime. Never log secrets/PHI.

Use volumes for durable/shared data and bind mounts for explicit host paths. Volume lifecycle is separate from container; backups/permissions/encryption still needed. Databases in containers are valid when storage, shutdown, fencing, backups and scheduling are engineered; “containers are ephemeral” does not make database processes impossible, but casual local volumes are not production durability.

Read-only root filesystem catches hidden writes. Give writable `/tmp` with size bound; Java may use temp directory, certificate stores or heap dumps. Heap dumps can contain PHI/secrets and be large—store only in controlled encrypted incident workflow.

### 2.11 Networking

Each container network namespace can have virtual interfaces/routes. A bridge commonly connects veth pairs and uses NAT/port publishing for external access. Container DNS resolves service names in engine/orchestrator networks. `localhost` means the same network namespace/container (or pod in Kubernetes), not another container/host.

Publishing port exposes host entry; `EXPOSE` alone does not. Outbound egress is often open by default, enabling data exfiltration/SSRF impact; restrict with network policy/firewalls/proxies. TLS identity and application authorization remain necessary because network isolation is not user authorization.

Connection tracking, ephemeral ports, DNS caching and MTU can cause production-only failures. Container IPs are disposable; use service discovery. Do not hard-code them.

### 2.12 Image identity, registry and supply chain

Pull by digest to guarantee exact bytes. Tags support human channels but are mutable. Sign image digest, attach SBOM/provenance attestations and enforce trusted registry/issuer/identity at admission. A signature proves signer and integrity under trust policy; it does not prove absence of vulnerabilities or malicious source.

Scan OS packages and application dependencies, but prioritize exploitable reachable risk and patch SLA. Rebuild even if app code unchanged to incorporate base updates; immutable images are replaced, not patched manually in a running container. Keep registry retention/replication, access logs and delete policy.

Multi-architecture builds require tests on each platform. Java bytecode is portable, but JNI/native libraries and image base are architecture-specific. Floating-point/model libraries may yield platform differences; ML validation includes output tolerance and performance.

### 2.13 Health, readiness and observability

Docker `HEALTHCHECK` can report status, but orchestrators have their own probes. Liveness asks if restart helps; readiness asks if traffic should be sent; startup protects slow initialization. A deep dependency check as liveness can restart the fleet during database outage. Keep liveness local, readiness path-aware with bounds, and expose dependency degradation separately.

Observe container CPU usage/throttling, memory current/max/events, OOM kills, filesystem/inodes, network, process count, restarts/exit reason, image digest and application SLIs. Inside-container tools may show host values depending on namespace/cgroup/runtime; prefer platform cgroup-aware metrics and test JVM container support.

### 2.14 Debugging method

1. Inspect desired versus actual image digest, command, env (redacted), mounts, user, limits and security options.
2. Inspect runtime state/exit/OOM/health and logs.
3. Compare cgroup CPU/memory/pids/I/O, node pressure and throttling.
4. Reproduce with exact digest/config/architecture.
5. Use ephemeral debug tooling/network namespace rather than permanently shipping shell/curl in production image.
6. Verify DNS, route, TLS certificate/time and egress policy.
7. For startup, run image with overridden entrypoint only in safe environment and inspect filesystem/permissions.

Never `docker exec` and manually repair production as final fix. Capture evidence, update image/config declaratively and redeploy. In regulated systems, debug access is audited and memory/filesystem artifacts are sensitive.

## 3. WORKED PROBLEMS

### Problem 1 — Container versus VM

**Statement.** Run untrusted customer Python plugins alongside a healthcare API. Is a standard container sufficient isolation?

**Solution.** Standard container shares host kernel; untrusted code increases syscall/kernel/escape risk. Use separate account/node and stronger sandbox (microVM/Kata/gVisor depending requirements), no host mounts/socket, strict egress, CPU/memory/pids/time limits, read-only filesystem and ephemeral identity. API itself may use ordinary hardened containers. Validate threat model/compliance.

**Mistake caught.** Calling containers security-equivalent to VMs.

### Problem 2 — JVM memory limit

**Statement.** Pod/container limit 1 GiB; Xmx set 1 GiB; process is OOMKilled despite heap below Xmx.

**Solution.** Limit covers heap plus metaspace, code cache, thread stacks, direct/native buffers, native libraries and charged cache. Reduce Xmx/MaxRAMPercentage after measuring native/nonheap peak, reduce threads/direct buffers, inspect `memory.events`, RSS and NMT. A starting 70% heap leaves ~307 MiB, but prove under load/soak.

**Mistake caught.** Equating container memory with heap.

### Problem 3 — CPU throttling

**Statement.** Service limited to 0.5 CPU has low node CPU but p99 spikes every load burst.

**Solution.** With 100 ms CFS period, 0.5 CPU roughly permits 50 ms quota per period before throttling. Burst can exhaust quota early and wait for next period. Inspect cgroup `cpu.stat` throttled periods/time; raise limit or reduce CPU/request, change workload/replica count. Node average is irrelevant to per-cgroup ceiling.

**Mistake caught.** Adding application timeouts without checking throttle.

### Problem 4 — Secret in layer

**Statement.** Dockerfile copies Maven settings token, builds, then deletes it.

**Solution.** Token remains in earlier layer/build context/cache. Rotate token immediately; purge governed registry/cache per incident process; use BuildKit `RUN --mount=type=secret` so secret is not committed; narrow context and verify layers/SBOM. Multi-stage alone helps final image but build cache/provenance still needs care.

**Mistake caught.** Believing later `rm` erases immutable lower layer.

### Problem 5 — Signal loss

**Statement.** Shell-form entrypoint launches Java; deployments hit SIGKILL after grace and lose in-flight work.

**Solution.** Use exec-form Java or wrapper ending `exec`; register bounded graceful shutdown; orchestrator removes readiness before TERM; stop accepting, finish/cancel within grace, persist durable work before ack. Test TERM. Add tiny init if spawning children. SIGKILL remains possible, so idempotency/recovery is mandatory.

**Mistake caught.** Relying entirely on shutdown hook for durability.

### Problem 6 — Image-size optimization

**Statement.** Build image is 920 MB with JDK, Maven cache and source; target runtime needs one 28 MB JAR.

**Solution.** Multi-stage builder compiles/tests; runtime contains maintained JRE/distroless plus JAR/CA/time-zone needs. `.dockerignore` excludes artifacts. Measure final compressed/unpacked size and cold pull/start. Do not use scratch if Java/native/cert requirements break. Smaller attack surface is benefit, not the only security criterion.

**Mistake caught.** Deleting build files in later layer instead of excluding them from final stage.

### Problem 7 — Non-root write failure

**Statement.** After `USER 10001`, app cannot write `/app/output`.

**Solution.** Images default created/copied files to root ownership. Prefer no runtime writes under `/app`; mount explicit volume/tmpfs and set ownership/security context. If required, `COPY --chown=10001:10001` or create/chown directory during build, then drop user. Do not `chmod 777` or switch back to root.

**Mistake caught.** Treating non-root as a single Dockerfile line without filesystem design.

### Problem 8 — Architecture mismatch

**Statement.** Image built on Apple Silicon fails `exec format error` on amd64 nodes.

**Solution.** Manifest/layer contains arm64 executable but node expects amd64. Build multi-platform image/index for linux/amd64 and linux/arm64, use architecture-appropriate bases, test each, and deploy digest/index supported by registry/runtime. Emulation build may be slower and can hide runtime differences.

**Mistake caught.** Assuming an image tag identifies one universal binary.

### Problem 9 — Root filesystem fills

**Statement.** App writes 3 GB/day logs inside writable layer; node evicts containers.

**Solution.** Emit structured bounded logs to stdout/stderr; configure runtime collection/rotation/backpressure and retention externally. Limit ephemeral storage, alert filesystem/inodes, prevent verbose PHI logs. Durable exports go object storage/volume through explicit pipeline. Deleting current file may not free space if process retains descriptor—restart/fix safely.

**Mistake caught.** Assuming ephemeral means infinite/free.

## 4. REAL-WORLD / APPLIED CONTEXT

**OCI interoperability.** OCI currently publishes runtime, image and distribution specifications. The image spec defines manifest, optional index, layers and configuration; runtime spec defines filesystem bundle lifecycle. This separation permits tools such as BuildKit, containerd and runc to interoperate around standards rather than one monolith.

**Docker resource controls.** Current Docker documentation explicitly says containers have no limits by default. It documents a minimum Docker `--memory` of 6 MiB and maps `--cpus=1.5` to quota 150,000/period 100,000 µs. These are Docker/Linux mechanics; Kubernetes requests/limits add scheduling/QoS semantics in the next lesson.

**Java API image.** The included server uses Java 21 virtual threads, binds `0.0.0.0:8080`, handles `/live`, and installs shutdown hook. Dockerfile separates JDK builder from JRE runtime, copies one JAR, uses numeric non-root and exec entrypoint. Compile/run locally; then build if Docker exists. Record image digest/size/layers/user, startup/RSS and TERM behavior rather than claiming generic performance.

## 5. COMPARISON TABLE

| Isolation unit | Kernel | Startup/density | Boundary | Best use |
|---|---|---|---|---|
| Process | shared, minimal namespace | fastest/highest | weakest | trusted same-service workers |
| Standard container | shared host kernel | fast/high | namespaces/cgroups/LSM | trusted app workloads |
| Sandboxed container | interposed userspace/kernel boundary | moderate | stronger syscall isolation | less-trusted code |
| MicroVM/VM | separate guest kernel | slower/lower density | stronger hardware virtualization | untrusted/multi-tenant/regulatory boundary |

| Runtime image style | Benefit | Cost/risk | Use when |
|---|---|---|---|
| Full distro/JDK | familiar debugging/tools | large attack/transfer surface | diagnostic/build environment |
| Slim JRE | balanced compatibility/size | some tools/packages absent | common Java production |
| Distroless | minimal packages/no shell | debugging/CA/native needs | stable app with ephemeral debug path |
| Scratch | no userspace extras | static-binary/certs/user metadata challenges | truly self-contained static binary |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Container is lightweight VM.”** It shares host kernel and isolates selected views/resources.
2. **No limits by default.** Namespaces do not cap CPU/memory; set/test cgroups.
3. **Xmx equals memory limit.** Native/nonheap/page charges remain.
4. **CPU request/limit means whole dedicated cores.** Quota/weight/scheduler semantics and platform differ.
5. **Tag is immutable.** Pin digest for exact bytes and automate reviewed refresh.
6. **Digest pin means patched forever.** It freezes old vulnerable bytes until updated.
7. **Delete secret later.** Lower image layer/cache retains it.
8. **Multi-stage automatically secure.** Builder credentials/context/provenance and runtime config still matter.
9. **`EXPOSE` publishes port.** It documents; runtime mapping/service publishes.
10. **`localhost` reaches another container.** It reaches same network namespace.
11. **Root inside is harmless.** Without appropriate mapping/restrictions it expands kernel/host impact.
12. **`chmod 777` fixes non-root.** It creates broad write surface; assign exact ownership/path.
13. **Shell-form entrypoint handles signals normally.** Shell may be PID 1 and fail to forward/reap.
14. **Shutdown hook guarantees completion.** SIGKILL/node death bypasses it; durable idempotent recovery required.
15. **Writable layer is durable storage.** It disappears with container and can exhaust node disk.
16. **Small image means secure.** Trust, patching, runtime privileges and app vulnerabilities dominate too.
17. **Signature means safe code.** It proves origin/integrity under policy, not benign behavior.
18. **Debug by modifying live container.** Drift is unreproducible; diagnose then rebuild/deploy declaratively.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Container = process + namespaces + cgroups + security controls; shared kernel.
- OCI image: manifest/index + config + ordered layers; digest identifies content, tag is mutable.
- Runtime writable layer ephemeral; volumes/object stores for declared persistence.
- Limits: memory includes heap+native; CPU quota can throttle; bound PIDs and ephemeral disk.
- Multi-stage: builder tools stay out of runtime; copy exact artifact.
- Narrow context + `.dockerignore`; never bake secrets in layer/ARG/ENV.
- Pin reviewed digest for repeatability; automate patch/digest updates, SBOM, signature/provenance.
- Exec-form ENTRYPOINT; PID 1 handles signals/reaping; test TERM and forced kill recovery.
- Numeric non-root, drop caps, no-new-privileges, read-only root, bounded writable paths.
- Avoid privileged, host namespaces, Docker socket and broad mounts/devices.
- `EXPOSE` documents; `-p` publishes; localhost is current namespace.
- Observe cgroup CPU throttle/memory events/OOM, exit reason, digest, filesystem and app SLIs.
- Untrusted tenant code merits stronger sandbox/failure domain than ordinary app container.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain exact visibility/resource differences provided by PID namespace and memory cgroup.
2. A 2 GiB container runs Java with 1.5 GiB heap, 300 threads at 1 MiB stacks and 400 MiB direct buffers. Show why budget is unsafe before other native memory.
3. Rewrite a single-stage Maven/JDK image into multi-stage runtime and describe cache ordering.
4. Find three ways `COPY . .` can leak or bloat a build and repair with context/ignore/explicit COPY.
5. Describe a TERM→grace→KILL timeline and design an idempotent worker that survives each cut point.
6. Harden `docker run` for a web API using non-root, dropped capabilities, read-only root, tmpfs, pids, memory and CPU limits.
7. Explain tag versus digest, signature, SBOM and provenance—one guarantee and one non-guarantee each.
8. Diagnose exit 137 using runtime status and cgroup evidence; distinguish OOM kill from manual SIGKILL.
9. Design image/runtime boundary for untrusted user model code requiring GPU access.
10. Explain how to debug a distroless image without permanently adding shell/curl.

## 9. CURATED RESOURCES

1. OCI, [Image Specification](https://specs.opencontainers.org/image-spec/). Exact manifest/index/layer/config/content-descriptor model.
2. OCI, [Runtime Specification](https://specs.opencontainers.org/runtime-spec/). Bundle configuration, lifecycle, namespaces/cgroups/hooks contract.
3. OCI, [Distribution Specification](https://specs.opencontainers.org/distribution-spec/). Registry push/pull/content discovery protocol.
4. Docker Docs, [Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/). Current memory/swap/CPU flag semantics and OOM risks.
5. Docker Docs, [Building best practices](https://docs.docker.com/build/building/best-practices/). Multi-stage, context, cache, non-root, pinning and rebuild guidance.
6. Docker Docs, [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/). Exact stage/target/copy mechanics and BuildKit behavior.
7. Linux kernel docs, [Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html). Authoritative controller files, hierarchy and resource semantics.
8. Linux man-pages, `namespaces(7)`, `pid_namespaces(7)`, `user_namespaces(7)`, `capabilities(7)`. Kernel interface and privilege details behind container isolation.
9. NIST SP 800-190, *Application Container Security Guide*. Threats and security controls across images, registries, orchestrators, containers and hosts.
10. Burns et al., “Borg, Omega, and Kubernetes,” ACM Queue 2016. Historical lineage and production container-orchestration principles.

## 10. RELATED TOPICS BRIDGE

### Before

1. **JVM Memory and GC.** Heap/native/RSS behavior must fit cgroup memory rather than host assumptions.
2. **Concurrency and Capacity.** Thread/request/connection counts become cgroup CPU/memory budgets.
3. **Failure Semantics.** SIGTERM/KILL, OOM and network loss require idempotent recovery and deadlines.
4. **Supply-Chain Basics.** Dependency pinning/trust extends to base images and build provenance.

### After

1. **Kubernetes.** Pods, probes, requests/limits, security contexts and volumes orchestrate these primitives.
2. **Terraform/IaC.** Registries, clusters, identities and network boundaries become declarative infrastructure.
3. **CI/CD Supply Chain.** Builds produce signed digests, SBOM/provenance and policy-gated promotion.
4. **Cloud Identity/Networking.** Workload identity, registry access, service networking and egress surround containers.

---ANSWER KEY BELOW---

1. PID namespace changes process-ID/tree visibility and gives an internal PID 1; it does not limit memory. Memory cgroup accounts/limits charged memory and can trigger cgroup OOM; it does not hide host processes. Both plus mount/network/user/security controls form container boundary.
2. Heap 1.5 GiB + stacks roughly 300 MiB + direct 400 MiB = 2.2 GiB before metaspace, code cache, native libraries, GC structures/page charges, already above 2 GiB. Reduce heap/thread stacks/count/direct cap or raise measured limit; load/soak with NMT/RSS/cgroup events.
3. Builder `FROM maven... AS build`, copy pom/lock files and resolve dependencies, then source/test/package; runtime `FROM` maintained JRE/distroless and `COPY --from=build` JAR. Stable dependency layer precedes changing source; secrets via mounts; pin approved digests.
4. It may include `.git` credentials/history, `.env`/keys, target/node_modules/data/logs; makes context huge and invalidates cache on irrelevant changes. Use dedicated context, `.dockerignore`, explicit manifest/source COPY and secret mounts.
5. Orchestrator removes readiness, sends TERM, PID1 forwards/app stops intake and drains until grace; then KILL. Persist/claim work before acknowledgement, use operation IDs/leases/checkpoints; TERM handler accelerates clean stop but crash/KILL requeues/reconciles safely.
6. Example: `--user 10001:10001 --cap-drop=ALL --security-opt=no-new-privileges --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --pids-limit=256 --memory=768m --memory-swap=768m --cpus=1.5 -p 127.0.0.1:8080:8080`; adapt tmp/exposure and seccomp to tested app.
7. Tag is mutable name (non-guarantee: same bytes); digest fixes content (non-guarantee: safe/patched). Signature proves approved signer/integrity under trust (not vulnerability-free). SBOM inventories declared/discovered components (not complete exploitability). Provenance attests build inputs/process at assurance level (not source benignness).
8. Inspect orchestrator/runtime reason/OOMKilled, host kernel logs where authorized, cgroup `memory.events` (`oom`/`oom_kill`), peak/current, app logs and timestamps. Exit 137 only indicates SIGKILL conventionally; manual/runtime forced kill can match without memory event.
9. Put each job in stronger sandbox/microVM and isolated nodes/account; minimal signed image/digest, numeric non-root, read-only filesystem, no host socket/mount, bounded CPU/RAM/pids/time/ephemeral disk, device plugin granting only GPU, restricted network/metadata/credentials, artifact scanning and teardown/audit. GPU driver host boundary remains trusted risk.
10. Use orchestrator ephemeral debug container or separate approved toolbox joined to target pod/network/process namespace as policy allows; inspect external metrics/logs/files through controlled volumes. Keep production image immutable and audit access; reproduce exact digest locally/staging.
