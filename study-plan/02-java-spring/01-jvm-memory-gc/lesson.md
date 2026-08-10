# JVM Memory and Garbage Collection — Complete Study Resource

**Parent:** `02-java-spring`  
**Child:** `01-jvm-memory-gc`  
**Primary baseline:** HotSpot JDK 21 semantics/docs; version-specific differences are identified

## 1. FOUNDATIONS

### Why a managed runtime exists

Java source does not execute directly as source. `javac` compiles it to JVM **bytecode**, a platform-neutral instruction format stored in class files. A Java Virtual Machine loads, verifies and executes bytecode, initially interpreting and then compiling frequently executed paths to native machine code through **just-in-time (JIT) compilation**. This indirection enables portability, runtime optimization, security checks and automatic memory management.

In manual-memory languages, programmers allocate and explicitly free storage. A premature free creates use-after-free; forgetting to free creates leaks. Java’s **garbage collector (GC)** identifies objects no longer reachable by the running program and reclaims their heap memory. GC prevents many memory-safety bugs, but not every memory problem. A map that retains obsolete entries is reachable and therefore not garbage. Native/direct memory can exhaust outside heap. Large allocation rates create CPU and pause pressure even when nothing leaks.

### Runtime memory areas

The **heap** stores ordinary objects and arrays and is shared among threads. Each thread owns a **Java stack** made of **frames** for active method calls; a frame holds local variables, operand-stack state and return information. Deep recursion can throw `StackOverflowError` even when heap is plentiful.

The **method area** is a specification concept for class metadata, method code and related structures. HotSpot stores class metadata in native **Metaspace**, introduced after PermGen removal. Loading unbounded classes/class loaders can exhaust Metaspace. The **code cache** holds JIT-compiled native code. **Direct buffers**, JNI allocations, thread stacks and JVM internal structures consume native/process memory outside Java heap.

**Resident set size (RSS)** is operating-system physical memory attributed to the process. It is not equivalent to used heap. A container can be OOM-killed because RSS exceeds its limit even when heap has headroom.

### Reachability, not “scope,” determines collection

GC begins from **roots**: active thread stacks, static references, JNI handles and JVM internals. It traces references to mark reachable objects. Unreachable cycles are collectible because tracing does not use reference counts. A local variable going textually out of scope may become unreachable, but the JIT controls precise liveness; `System.gc()` is only a request and does not guarantee immediate reclamation.

Object states are often described as strongly, softly, weakly or phantom reachable. A **strong reference** prevents collection. A **WeakReference** does not keep its referent alive and is useful for canonical mappings with carefully understood semantics. Soft references have GC-dependent retention and are usually a poor cache-sizing policy. Phantom references plus `ReferenceQueue` support post-mortem cleanup coordination; `Cleaner` is safer than finalization but deterministic resource management should use `try-with-resources`.

### GC goals conflict

**Throughput** is application work time divided by total time. **Pause time** is when application (**mutator**) threads are stopped for GC phases. **Latency** is user-operation duration, often p95/p99 rather than average. **Footprint** is memory consumption. Collectors trade CPU, memory and pauses; no collector maximizes all simultaneously.

Oracle’s JDK 21 guide says G1 is selected by default on most server-class configurations, while ergonomics are platform-dependent. Do not repeat defaults without naming JDK/vendor/container environment. JDK 21 also introduced Generational ZGC as an option; later JDK 23 made ZGC’s generational mode default when ZGC is selected. Flags and behavior change across releases.

## 2. CORE MECHANICS

### 2.1 Allocation and TLABs

Most objects allocate in the young generation using a pointer bump: reserve consecutive space and advance a pointer. **Thread-local allocation buffers (TLABs)** give threads private allocation regions, reducing contention. Allocation can be cheap, but initialization, cache traffic and eventual collection still cost resources. Escape analysis may eliminate an allocation or scalar-replace an object, but this is an optimization, not a Java-language guarantee.

Large objects may receive special treatment. In G1, an object occupying at least half a region is **humongous** and uses contiguous humongous regions; many awkward sizes can fragment capacity. G1 region size is selected ergonomically, generally targeting roughly 2,048 regions within documented bounds.

### 2.2 Generational hypothesis

Most newly allocated objects die young: request DTOs, temporary strings and iterator state. Generational collectors divide heap logically into young and old areas. Young collections reclaim frequent short-lived garbage; survivors age and may be **promoted**. References from old to young require **remembered sets/card tables** so young collection need not scan all old objects.

Promotion is not evidence of a leak. Objects survive due to real lifetime, collection timing or references. A too-small young area can increase collection frequency/promotion, but manually sizing generations before measuring can worsen behavior.

### 2.3 Mark, sweep, compact and copy

**Marking** traces reachable objects. **Sweeping** makes unmarked space reusable but may leave fragmentation. **Compaction** moves live objects together, updating references and creating contiguous free space. **Copying/evacuation** moves live objects from selected regions to new regions, making old regions wholly reclaimable. Movement requires stop-the-world or barriers/concurrent protocols to keep references correct.

A **write barrier** is runtime code around reference stores that records information for GC. A **load barrier** participates when references are read. Barriers add mutator overhead in exchange for concurrent/region/generational collection.

### 2.4 Stop-the-world, parallel and concurrent

**Stop-the-world (STW)** pauses application threads. **Parallel GC work** uses several GC threads during a pause. **Concurrent work** runs GC alongside application threads, consuming CPU and requiring barriers. “Concurrent collector” does not mean zero pauses. Safepoints coordinate operations requiring a consistent JVM state; application time-to-safepoint can matter separately from GC phase duration.

### 2.5 Serial and Parallel collectors

Serial GC uses one GC thread and suits small heaps/constrained machines; Oracle guidance cites small datasets around up to approximately 100 MB as a broad use case, not a hard threshold. Enable with `-XX:+UseSerialGC`.

Parallel GC prioritizes throughput and uses multiple GC threads, generally with stop-the-world collections. Enable `-XX:+UseParallelGC`. It can suit batch workloads where aggregate throughput matters more than low tail pauses.

### 2.6 G1

G1 partitions heap into equal-sized regions assigned roles dynamically. Young collections evacuate selected young regions. Concurrent marking estimates live data in old regions. **Mixed collections** collect young plus selected old regions with reclaimable garbage, choosing a **collection set** to work toward a pause-time goal.

`-XX:MaxGCPauseMillis` is a soft goal, not SLA. Setting it unrealistically low can increase collection overhead or reduce throughput. G1 uses remembered sets and adaptive heuristics; start with defaults, adequate heap and GC logs before changing low-level knobs.

### 2.7 ZGC

ZGC performs most work concurrently and targets very low pauses at large heap scales. JEP 439’s Generational ZGC goals included pauses not exceeding 1 ms, heaps from hundreds of MB to multiple TB and minimal manual configuration. These are design goals/benchmark claims, not a guarantee for every application or total request latency. Concurrent collectors need CPU and headroom to reclaim faster than allocation; otherwise **allocation stalls** or failure can occur.

In JDK 21, generational ZGC was enabled using `-XX:+UseZGC -XX:+ZGenerational`; later releases changed mode defaults. Always inspect `java -version` and current `java` option docs.

### 2.8 Heap sizing

`-Xms` controls initial heap, `-Xmx` maximum. Used heap, committed heap and maximum differ. Setting Xms=Xmx can reduce resizing variability and, with pre-touch, startup commits pages—but increases startup/committed footprint. In containers, leave memory for Metaspace, code cache, direct buffers, thread stacks, native libraries and OS. Setting heap equal to container limit invites OOM kill.

The **live set** is memory remaining reachable after collection. Maximum heap must exceed live set plus allocation/evacuation headroom. If live set is 3.5 GB in a 4 GB heap, GC cannot create sufficient breathing room even if it runs constantly.

### 2.9 OutOfMemoryError varieties

Messages point to different exhausted resources:

- `Java heap space`: heap allocation cannot be satisfied;
- `GC overhead limit exceeded`: little reclaimed despite excessive GC under relevant collector policy;
- `Metaspace`: class metadata/native Metaspace cap exhausted;
- `Direct buffer memory`: direct-buffer limit/allocation pressure;
- `unable to create native thread`: OS/native memory/thread limits;
- array size/request-related messages: impossible/oversized allocation.

Do not increase Xmx before identifying which resource and why. A container SIGKILL may produce no Java OOME or heap dump.

### 2.10 Memory leaks in managed code

A Java leak is unwanted retention. Common patterns: unbounded static cache, listener never deregistered, `ThreadLocal` value retained by pool thread, class-loader leak, queue backlog, metrics labels creating unbounded maps, and response/request objects captured by long-lived tasks.

Heap analysis uses **shallow size** (object itself) and **retained size** (memory that becomes unreachable if object is removed). A **dominator** lies on every root-to-object path; dominator trees reveal retaining owners. Compare post-GC live set over time, histograms and heap dumps—not one rising sawtooth before GC.

### 2.11 Diagnostics

Enable unified GC logging, for example JDK 21:

```bash
java -Xms512m -Xmx512m -Xlog:gc*,safepoint:file=gc.log:time,uptime,level,tags App
```

Use `jcmd <pid> GC.heap_info`, `GC.class_histogram`, `VM.native_memory summary` (when Native Memory Tracking enabled), `JFR.start`, and heap dumps such as `-XX:+HeapDumpOnOutOfMemoryError`. Histograms show counts/shallow bytes, not complete retention. Heap dumps can pause applications and contain secrets/PHI; secure storage and access.

JFR records allocation, GC, safepoint, lock and I/O events with designed low overhead, but configure/measure for your workload. JDK Mission Control analyzes recordings.

### 2.12 Finalization and resources

Finalization is deprecated for removal and unpredictable. GC manages memory, not prompt release of sockets/files/DB connections. Use `AutoCloseable` and try-with-resources. `Cleaner` is fallback safety, not deterministic lifecycle. A leaked connection may exhaust a pool while heap looks normal.

## 3. WORKED PROBLEMS

### Problem 1 — Reachability cycle

**Statement.** A references B, B references A, and no root reaches either. Are they collectible?

**Solution.** Yes. Tracing starts from roots; neither object is marked. Reference counting alone would fail, but tracing GC reclaims the unreachable cycle.

**Mistake caught.** Believing any mutual reference prevents Java collection.

### Problem 2 — Static cache leak

**Statement.** `static Map<String,byte[]> cache` gains 10,000 unique 100 KB values/hour without eviction.

**Solution.** Raw payload grows about 1,000,000 KB/hour≈976.6 MiB/hour, excluding keys/map overhead. Entries remain strongly reachable from static root. GC cannot reclaim them. Add bounded size/weight, expiry, invalidation and metrics; decide whether cache miss reload is safe.

**Mistake caught.** Increasing Xmx treats symptom and extends time to failure.

### Problem 3 — Allocation rate

**Statement.** Service allocates 2 MB/request at 500 RPS; estimate allocation rate.

**Solution.** 1,000 MB/s decimal≈0.93 GiB/s. Even if objects die within request, collector must process roughly this churn. Measure allocation profile, remove unnecessary copies/boxing, and select/sizing based on pause/throughput evidence.

**Mistake caught.** “No leak means memory is fine.” Allocation rate can dominate CPU/GC.

### Problem 4 — Container heap

**Statement.** Pod limit4 GiB; engineer sets `-Xmx4g`. Why unsafe?

**Solution.** Heap is only part of RSS. Metaspace, code cache, direct buffers, thread stacks, native libraries and JVM structures need memory. RSS can exceed4 GiB and kernel kills process without heap OOME. Budget nonheap/native from measurements and leave safety headroom.

**Mistake caught.** Equating Xmx with total process memory.

### Problem 5 — Sawtooth diagnosis

**Statement.** Used heap rises 1→3 GB then drops to1.1 GB repeatedly; is it a leak?

**Solution.** This is normal allocation/reclamation shape if post-GC floor remains stable. Track post-GC live set over comparable load/time. A steadily rising floor, increasing dominator retention and eventual pressure suggests leak.

**Mistake caught.** Alerting on pre-GC used heap alone.

### Problem 6 — Stack overflow

**Statement.** Recursive DFS on one-million-node chain fails despite 8 GB free heap.

**Solution.** Each call consumes thread-stack frame; stack is separate and bounded. Convert to explicit heap-based stack/iterative DFS or bound depth. Increasing `-Xss` multiplies native reservation per thread and is not the first fix.

**Mistake caught.** Treating every memory failure as heap/GC.

### Problem 7 — G1 pause goal

**Statement.** Set `MaxGCPauseMillis=10`; does it guarantee p99<10 ms?

**Solution.** No. It is a collector heuristic goal, GC pauses are only one latency component, and some events/full collections/safepoint delays may exceed it. Measure end-to-end p99 and GC/safepoint correlation.

**Mistake caught.** Converting a soft tuning target into SLA.

### Problem 8 — Weak cache

**Statement.** Can WeakHashMap be a reliable cache of model metadata?

**Solution.** Keys can disappear whenever no strong key reference remains, based on nondeterministic GC timing. It cannot guarantee TTL/hit rate. Use explicit bounded cache with policy. Weak maps suit associations whose lifetime follows externally referenced keys.

**Mistake caught.** Treating weak references as predictable eviction.

### Problem 9 — Metaspace growth

**Statement.** Application repeatedly creates class loaders for redeployed plugins and retains one plugin thread.

**Solution.** Thread/context/objects can retain class loader, keeping all loaded class metadata alive. Heap dump/class-loader stats show loader retention; stop threads, close resources and remove references. Raising Metaspace cap only postpones.

**Mistake caught.** Looking only for large byte arrays in heap.

## 4. REAL-WORLD / APPLIED CONTEXT

### Current collector guidance

Oracle’s JDK 21 GC tuning guide documents Serial, Parallel, G1 and ZGC and identifies G1 as default on server-class machines. It recommends beginning with ergonomics rather than premature detailed tuning. JEP 439 reports a Cassandra benchmark where Generational ZGC used one quarter heap and achieved four times throughput versus non-generational ZGC while retaining sub-millisecond pauses; that is a cited workload result, not a universal expectation.

### Duplicate strings

JEP 192’s motivation reported measurements in some large applications where roughly 25% of live heap was String objects and about half were duplicates. G1 string deduplication can share backing storage, but it adds processing and applies under specific collector/flag/version behavior. First find real duplicate retention.

### Reproducible lab

`JvmMemoryLab.java` generates short-lived allocation, deliberate retained cache entries, a direct buffer and a weak reference. Run with a small heap and logs:

```bash
javac JvmMemoryLab.java
java -Xms64m -Xmx64m -Xlog:gc*,safepoint JvmMemoryLab
```

Weak-reference clearing output is intentionally nondeterministic; deterministic checks must not require GC timing. Inspect collector selected with `-Xlog:gc`/`-XX:+PrintCommandLineFlags` as appropriate to the JDK.

## 5. COMPARISON TABLE

| Collector | Primary goal/style | Typical strength | Trade-off/boundary | Enable (JDK 21 HotSpot) |
|---|---|---|---|---|
| Serial | single-thread STW | small heaps/simple footprint | cannot exploit multiple GC cores | `-XX:+UseSerialGC` |
| Parallel | parallel STW, throughput | batch throughput | longer tail pauses | `-XX:+UseParallelGC` |
| G1 | regional, mostly concurrent | balanced throughput/pause, default server | barriers/remembered sets; pause goal soft | `-XX:+UseG1GC` |
| ZGC | highly concurrent | very low GC pauses, large heaps | CPU/memory headroom; version-sensitive mode | `-XX:+UseZGC` plus JDK21 generational flag if desired |

| Memory | Managed by | Failure/diagnostic |
|---|---|---|
| heap | GC | heap OOME, heap dump/histogram |
| thread stack | per thread/JVM/OS | StackOverflowError/native thread failure |
| Metaspace | JVM class unloading | Metaspace OOME, class-loader stats |
| direct/native | libraries/JVM/OS | direct OOME or RSS kill; NMT/native tools |
| code cache | JIT | compilation/code-cache logs |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **GC prevents leaks.** Reachable unwanted objects are not garbage.
2. **Heap equals process memory.** Native areas and stacks contribute RSS.
3. **Object leaves scope, so collected immediately.** Liveness/collection timing are unspecified.
4. **`System.gc()` guarantees cleanup.** It is a request and may be disabled/handled differently.
5. **All OOME means raise Xmx.** Identify message/resource first.
6. **Used heap rise means leak.** Inspect post-GC floor and dominators.
7. **Pause target is SLA.** It is a soft heuristic and not total latency.
8. **ZGC guarantees every request under1 ms.** Design pause goals do not include application/downstream latency and need headroom.
9. **Recursive memory is heap only.** Calls consume thread stack.
10. **Soft/weak references are production cache policy.** Eviction timing is GC-driven.
11. **Finalizer closes resources promptly.** Use try-with-resources.
12. **Tune flags before profiling.** Defaults plus evidence first.
13. **Heap dump is harmless.** It can pause, consume disk and expose secrets/PHI.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full resource.

- Heap objects; per-thread stacks; Metaspace/native/code cache/direct memory outside heap.
- GC traces from roots; unreachable cycles collect.
- Leak = unwanted reachable retention.
- Young/old exploit “most objects die young”; promotion is not automatically leak.
- STW pauses mutators; parallel GC uses many GC threads; concurrent GC overlaps.
- JDK21 server default generally G1; verify actual vendor/config.
- Xmx is not container RSS budget.
- Allocation rate, live set and headroom matter.
- Track post-GC floor, allocation rate, pause p95/p99, CPU and RSS.
- Use GC logs, JFR/JMC, jcmd, heap dump/dominator analysis and NMT.
- Deterministic resources use try-with-resources, not GC.
- Collector/flags are version-sensitive.

## 8. PRACTICE SET FOR SELF-TEST

1. Classify `static`, local, object field, direct buffer and recursive frame storage.
2. Estimate raw allocation rate for 40 KB/request at 8,000 RPS.
3. A post-GC live set rises 50 MB/hour. List evidence needed before calling it leak.
4. Explain how ThreadLocal leaks occur in application-server pools.
5. Pod limit2 GiB, heap1.5 GiB, 500 threads at1 MiB stack reservation: discuss risk.
6. Compare workload fit for nightly batch versus latency-sensitive gateway across collectors.
7. Explain why an old-to-young remembered set exists.
8. Diagnose `unable to create native thread` with heap only40% used.
9. Design safe heap-dump handling for healthcare production.
10. Explain why benchmark claims from JEP 439 cannot be applied directly to your service.

## 9. CURATED RESOURCES

1. **Oracle, HotSpot VM Garbage Collection Tuning Guide, JDK 21.** Definitive collector concepts, ergonomics, G1/ZGC operations and tuning workflow for baseline version.
2. **Oracle, JDK 21 Troubleshooting Guide, memory leaks and JFR chapters.** Exact diagnostic workflow and tools.
3. **OpenJDK JEP 439, “Generational ZGC.”** Design goals, barriers and published workload evidence for JDK 21 feature.
4. **OpenJDK JEP 474, “ZGC: Generational Mode by Default.”** Later-version transition needed for correct flag/default reasoning.
5. **OpenJDK JEP 192, “String Deduplication in G1.”** Concrete duplicate-string motivation and implementation boundary.
6. **OpenJDK JEP 254, “Compact Strings.”** Modern String storage optimization context.
7. **Jones, Hosking & Moss, *The Garbage Collection Handbook*, 2nd ed.** Formal tracing, generational, concurrent and real-time collector theory.
8. **Shipilev, “JVM Anatomy Quarks” series.** Focused experiments on allocation, object layout, TLABs and runtime details.
9. **OpenJDK JOL and JMH.** Measures object layout and performance without relying on folklore.
10. **Eclipse Memory Analyzer documentation, dominator tree/leak suspects.** Practical retained-size heap analysis.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java Concurrency Basics.** Threads/stacks/shared heap and happens-before frame runtime behavior.
2. **Complexity and Data Structures.** Object count/layout and allocation patterns arise from chosen structures.

### After

1. **Advanced Concurrency and Virtual Threads.** Thread-stack/native cost, pinning and pool sizing depend on JVM memory/runtime.
2. **Spring Core and Transactions.** Bean lifetimes/proxies/caches create retention and allocation patterns.
3. **Observability/SRE.** GC logs, JFR, RSS, pauses and allocation become operational signals.
4. **Containers/Kubernetes.** Memory limits, OOM kill and requests/limits interact with JVM ergonomics.

---ANSWER KEY BELOW---

1. Static reference itself is class-associated/root path; referenced object usually heap. Local/reference and frames are stack-frame data while referenced object heap. Object fields are within heap object. Direct buffer payload native/direct with wrapper heap. Recursive frames thread stack.
2. 40 KB×8,000=320,000 KB/s≈312.5 MiB/s binary if KB=1024 bytes; state unit convention. Significant churn even if short-lived.
3. Normalize load; confirm full/mixed/post-GC comparability; capture GC logs, class histograms over time, heap dumps/dominator paths, allocation profile and cache/queue/cardinality metrics. Rule out legitimate warm-up/cache growth.
4. Pool threads live long. ThreadLocalMap values remain reachable from thread when code forgets `remove`, possibly retaining request/class-loader graphs. Use try/finally remove and avoid inappropriate ThreadLocal state.
5. 500×1 MiB≈500 MiB potential native stack reservation plus1.5 GiB heap already equals2 GiB before Metaspace/code/direct/JVM. Strong OOM-kill/native-thread risk; measure actual commitment, reduce threads/stack/heap and leave headroom.
6. Parallel GC may favor batch throughput with acceptable pauses; G1 balanced default; ZGC for strict low GC-pause needs with CPU/headroom. Measure representative allocation/live set and end-to-end goals.
7. Young collection must find old objects pointing to young without scanning all old heap. Write barriers/cards record potential cross-generation references.
8. Check OS/container PID/thread limits, native memory/RSS, stack size, runaway thread creation and ulimit/cgroup constraints. Heap utilization does not diagnose native thread capacity.
9. Restrict trigger/access, encrypt storage, isolate destination capacity, redact operational handling, short retention, audit access, avoid public tickets, obtain incident/privacy approval and securely delete; dumps may contain PHI/secrets.
10. It compares specific Cassandra benchmark/configurations and collectors. Your allocation, live set, CPU, heap, latency and JDK differ. Reproduce representative load with controlled A/B, logs/JFR and application SLOs.
