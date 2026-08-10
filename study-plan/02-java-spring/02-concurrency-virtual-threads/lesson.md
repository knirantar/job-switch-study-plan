# Advanced Concurrency and Virtual Threads — Complete Study Resource

**Parent:** `02-java-spring`  
**Child:** `02-concurrency-virtual-threads`  
**Baseline:** Java 21 stable virtual threads; preview APIs are labeled explicitly

## 1. FOUNDATIONS

### From correctness to scalable execution

Concurrency basics establish safety: happens-before, locks, atomics and cancellation. Advanced concurrency asks how to express thousands of dependent tasks without exhausting threads, queues, memory or downstream capacity. A service can be race-free and still fail because every request blocks a 200-thread pool while waiting on a 30-connection database pool.

Traditional Java **platform threads** are scheduled by the operating system and normally correspond closely to OS threads. They are powerful but relatively expensive in native stack/reservation and scheduling resources. The common server solution was a bounded thread pool plus callbacks/futures for high concurrency. This controls resources but can entangle logical task count with thread count and make stack traces/control flow hard to follow.

Java 21 finalized **virtual threads** through JEP 444. A virtual thread is a `Thread` scheduled by the JVM rather than permanently tied to one OS thread. The JVM mounts it on a platform **carrier thread** while it runs and can unmount it during supported blocking operations, freeing the carrier to run another virtual thread. The programming model remains blocking, sequential code with ordinary stack traces and `ThreadLocal` support.

Virtual threads target **scale (throughput under blocking concurrency)**, not faster execution of one task. They do not create CPU cores, database connections, API quota, heap or network bandwidth. They make “thread per task/request” feasible; they do not justify “unbounded admission.”

### Vocabulary

A **task** is a unit of work; a **thread** executes tasks. An **executor** accepts tasks and decides how/where to run them. A **thread pool** reuses a bounded number of worker threads. A **work-stealing pool** gives workers local queues and lets idle workers steal, useful for fork/join CPU work. **Fan-out** launches several independent child operations; **fan-in** combines results.

A virtual thread is **mounted** when executing on a carrier and **unmounted/parked** when suspended without occupying it. **Pinning** means a virtual thread cannot unmount during a blocking operation, temporarily occupying the carrier. Pinning is a scalability issue, not automatically a correctness failure.

**Structured concurrency** treats a group of related child tasks as a lexical unit whose lifetime, cancellation and errors are joined before scope exits. As of Java 21 its API was preview and changed in later releases; use the concept confidently but check the target JDK API before production code.

## 2. CORE MECHANICS

### 2.1 Platform thread pools

For CPU-bound independent tasks, worker count near available processors is a starting point; excess runnable threads add context switching. For blocking tasks, the classic estimate is `threads ≈ cores × targetUtilization × (1 + wait/compute)`, but it is only a measurement-based model and must be capped by dependencies and memory.

Example: 8 cores, task computes 10 ms and waits 90 ms; wait/compute=9, theoretical high-utilization pool around80 threads. But if database allows30 concurrent calls, 80 can only queue at the pool/DB. Measure service time, queueing and actual bottleneck.

`ThreadPoolExecutor` parameters interact: core/max, queue and rejection. An unbounded queue usually means max threads are never reached after core. `SynchronousQueue` hands off directly and can grow toward max. Bounded queues expose overload. Named thread factories, uncaught exception handling and metrics improve operability.

### 2.2 ForkJoinPool and parallel streams

Fork/join recursively splits CPU work and uses work stealing. Small tasks are not free; choose thresholds. Blocking within the common pool can starve unrelated work unless managed/compensated. Parallel streams use the common pool by default and hide executor/resource policy, so avoid them for blocking remote calls and latency-critical code without strong evidence.

Associative, stateless operations suit parallel reduction. Mutable shared accumulation introduces contention/races. Speedup is limited by serial fraction (Amdahl’s law): if 10% is inherently serial, infinite processors cap speedup at10×; with8 processors, `1/(0.1+0.9/8)≈4.71×` ideal before overhead.

### 2.3 CompletableFuture

`CompletableFuture` models a value/completion graph. `thenApply` transforms a result; `thenCompose` flattens an asynchronous dependent future; `thenCombine` joins independent results. `allOf` signals completion but does not return typed results. Async variants schedule on an executor; non-async continuations may run in the completing thread.

Always define executor for blocking work. Handle exceptional completion with `handle`, `exceptionally` or `whenComplete` according to whether recovery changes the value. `orTimeout` completes the future exceptionally; it does not necessarily stop underlying remote work. Cancellation/deadline propagation must reach HTTP/client operations.

Calling `join/get` inside the same small executor needed by child tasks can create thread-starvation deadlock. Compose stages or separate execution resources.

### 2.4 Creating virtual threads

Stable Java 21 APIs include:

```java
Thread.startVirtualThread(task);
try (ExecutorService e = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<Result> f = e.submit(callable);
}
```

The per-task executor creates a new virtual thread for each task and is not a traditional fixed-size pool. Pooling virtual threads defeats their cheap-per-task model and can preserve ThreadLocal leakage assumptions. Limit scarce operations with semaphores/rate limiters/connection pools, not by pooling virtual threads merely to cap count.

### 2.5 Parking, mounting and pinning

Supported JDK blocking operations such as socket I/O and `Thread.sleep` can park a virtual thread and release its carrier. Historically, blocking while holding a `synchronized` monitor could pin; JDK implementation evolved, including work to reduce pinning in newer releases. For Java 21 baseline, avoid long/blocking operations inside `synchronized` and measure pinning through JFR or `-Djdk.tracePinnedThreads=full` where supported. Native/foreign calls may also pin or otherwise occupy carriers.

Do not replace every synchronized block preemptively. Short CPU-only critical sections are fine. Fix observed long pinning by moving blocking work outside the monitor, reducing scope, or using an appropriate lock/protocol.

### 2.6 ThreadLocal and context

Virtual threads support ThreadLocal, but millions of virtual threads each copying large context can consume memory. Thread pools historically risk ThreadLocal leakage across tasks; virtual per-task lifetime reduces reuse leakage but large values still live for task duration. Avoid using ThreadLocal as hidden global dependency.

Logging/security context needs deliberate propagation. `InheritableThreadLocal` snapshot semantics and executor scheduling can surprise. **Scoped values** provide immutable bounded context in newer Java releases but were preview across several releases; check target version.

### 2.7 Structured concurrency concept

Unstructured fan-out can orphan tasks: parent times out while children keep running; one failure does not cancel siblings; exceptions disappear. Structured concurrency creates a scope, forks child tasks, joins, applies policy (e.g., shutdown on failure/success), then exits only after cleanup.

For a product page fetching price, inventory and recommendation, all required children share the request deadline. If inventory fails and page cannot proceed, cancel siblings. Preview class names/methods vary across JDKs; do not paste Java 21 preview code into Java 25 without checking JEP/API.

### 2.8 Bulkheads and admission

With virtual threads, 100,000 tasks can cheaply wait, but a queue of user requests still represents latency, payload memory and expiring work. Use a semaphore around downstream calls, a bounded request ingress, deadlines and rejection. If 10 pods each allow25 database operations, global potential is250; compare with DB maximum and other workloads.

A semaphore bounds concurrency, not rate. If operations take100 ms, 25 permits theoretically support about250 operations/s absent other overhead (`25/0.1`). If they slow to500 ms, about50/s. Adaptive concurrency must use robust measurements and stability controls.

### 2.9 Cancellation and deadlines

Timeouts should form one end-to-end deadline rather than a fresh timeout at every layer. If request has800 ms, child calls share remaining budget. `Future.cancel(true)` interrupts cooperative Java blocking, but remote side may have already committed. Use idempotency and status lookup for business effects.

On interruption, propagate or restore status. Virtual threads make cancellation cheap but not automatic. Ensure semaphores, locks, transactions and connections release in finally/try-with-resources.

### 2.10 Backpressure versus blocking

Blocking a virtual thread is cheap in carrier terms, but not proof that producer rate is safe. At arrival1,000/s and service800/s, waiting tasks grow200/s. After five minutes,60,000 tasks may retain request/context objects and already exceed client deadlines. Reject/throttle/durable queue based on policy.

Reactive streams formalize demand signals and can be appropriate for streaming pipelines; virtual threads simplify request/response blocking code. They are alternatives at some layers, complementary at others. Choose from semantics/tooling, not fashion.

### 2.11 Diagnostics

JFR records virtual-thread events, pinning and thread dumps in supported versions. `jcmd <pid> Thread.dump_to_file` can produce thread dumps suitable for large virtual-thread populations depending on JDK. Traditional platform thread dumps with millions of logical threads need tooling-aware formats.

Measure task rate, active/downstream concurrency, semaphore wait, executor queue (for platform pools), carrier CPU, pin duration/count, deadline cancellations, connection-pool wait, heap/RSS and p95/p99 end-to-end latency.

## 3. WORKED PROBLEMS

### Problem 1 — CPU pool sizing

**Statement.** Eight cores execute pure CPU tasks with no waits. Should pool use800 threads?

**Solution.** No. Around8 workers is baseline; perhaps adjust for measured runtime/other work. 800 runnable platform/virtual threads contend for8 cores and add scheduling/cache overhead. Virtual threads do not accelerate CPU tasks.

**Mistake caught.** Cheap virtual threads mean cheap CPU parallelism.

### Problem 2 — Blocking estimate

**Statement.** Eight cores, 10 ms CPU and90 ms wait per task.

**Solution.** Wait/compute9; classical estimate at full target utilization `8×(1+9)=80`. Then cap against downstream/service/memory and measure. Virtual threads remove need to tie logical concurrency to80 carriers, but downstream still caps useful concurrency.

**Mistake caught.** Treating formula as guaranteed optimum.

### Problem 3 — CompletableFuture deadlock

**Statement.** A single-thread executor runs task A; A submits B to same executor then calls `get`.

**Solution.** Only worker is blocked in A; B waits queued forever. Compose without blocking, run B before wait on another suitable executor, or redesign scope. Increasing pool may mask but not robustly solve nested blocking.

**Mistake caught.** Futures automatically prevent blocking deadlock.

### Problem 4 — Fan-out deadline

**Statement.** Request has800 ms remaining; price typically100 ms, inventory150 ms, recommendations700 ms, all independent.

**Solution.** Start concurrently under shared deadline. Required price/inventory failures cancel scope; recommendations may be optional and omitted on timeout. Do not allocate800 ms sequentially to each (2.4s total). End-to-end cancellation reaches clients and operations are idempotent/read-only as appropriate.

**Mistake caught.** New full timeout per child/layer.

### Problem 5 — Virtual threads and DB pool

**Statement.** 50,000 virtual requests, DB pool30.

**Solution.** At most30 execute DB calls; others wait and retain state. Protect ingress/deadlines and often a bulkhead ≤pool capacity with reserved headroom. Measure pool wait. Creating more virtual threads cannot exceed DB throughput.

**Mistake caught.** Equating runnable task capacity with resource capacity.

### Problem 6 — Pinning

**Statement.** Virtual thread enters synchronized cache method and performs2-second HTTP call.

**Solution.** Under Java21 pinning behavior this can occupy carrier while blocking and serialize monitor users. Move HTTP outside critical section; lock only state transition or use concurrent single-flight design. Confirm with JFR/pinned-thread tracing before wholesale rewrites.

**Mistake caught.** All blocking unmounts under every context/version.

### Problem 7 — Amdahl speedup

**Statement.** 20% of job serial, 80% parallel, 8 processors. Ideal speedup?

**Solution.** `1/(0.2+0.8/8)=1/0.3≈3.33×`, before overhead. Infinite processors cap at5×.

**Mistake caught.** Expecting8× from8 cores regardless of serial work.

### Problem 8 — Global bulkhead

**Statement.** Twelve pods each use semaphore20 against DB max180, with30 connections reserved elsewhere.

**Solution.** Workload can demand240, but safe share is150. Static equal budget is floor(150/12)=12 per pod with6 spare, not20. Autoscaling changes replica count; use coordinated/pool-level constraints and conservative dynamic config.

**Mistake caught.** Per-pod bounds without replica multiplication.

### Problem 9 — Timeout side effect

**Statement.** Payment call times out after client sends request. Can virtual thread cancellation mark payment failed?

**Solution.** No. Timeout means outcome unknown; remote may commit. Retry only with idempotency key, query status, and reconcile. Thread cancellation controls local waiting, not distributed transaction outcome.

**Mistake caught.** Conflating execution cancellation with business rollback.

## 4. REAL-WORLD / APPLIED CONTEXT

### JEP 444 goals

JEP 444 states virtual threads aim to let thread-per-request server applications scale with near-optimal hardware utilization and preserve observability/debugging. It explicitly does not aim to remove the thread model or make data processing faster. The JEP demonstrates scale scenarios; benchmark on your JDK/client libraries because blocking integration and pinning evolve.

### Spring Boot request handling

Modern Spring Boot versions can use virtual threads when running on compatible Java/Spring configuration, but application dependencies must behave correctly: DB pools remain bounded, ThreadLocal usage grows per logical thread, schedulers/lifecycle semantics change, and pinned/native blocking can limit carriers. Verify exact Boot version properties and test load; this document does not claim a universal switch.

### Lab

`VirtualThreadsLab.java` creates500 virtual-thread tasks but uses a semaphore limiting simulated downstream concurrency to12; it also validates `CompletableFuture` fan-in and cooperative cancellation. It uses stable Java APIs and compiles on the workspace JDK25 while remaining conceptually Java21-compatible.

## 5. COMPARISON TABLE

| Model | Strength | Cost/control | Good fit | Boundary |
|---|---|---|---|---|
| fixed platform pool | explicit bounded workers | queue/sizing complexity | CPU tasks, legacy blocking bound | pool starvation/queueing |
| fork/join | work stealing | split threshold/common pool | recursive CPU parallelism | blocking tasks |
| CompletableFuture | composition graph | hidden execution/cancellation complexity | async fan-out/integration | blocking joins/executor choice |
| virtual thread per task | simple blocking code at high concurrency | many logical tasks/context | I/O-heavy request/task workloads | CPU/downstream/admission still bounded |
| reactive streams | demand/backpressure, async pipeline | conceptual/debug complexity | streaming/event pipelines | library/context integration |
| structured concurrency | bounded child lifetime/error policy | preview API version-sensitive | related request fan-out | target JDK maturity |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Virtual threads make code run faster.** They improve concurrency scale for blocking workloads, not single-task CPU.
2. **Pool virtual threads.** Use per-task; bound scarce resource separately.
3. **Unbounded tasks are safe.** Payload/deadline/downstream limits remain.
4. **Every blocking call unmounts.** Native/monitor/version behavior can pin/occupy carriers.
5. **More carriers equals more DB capacity.** Pools/quotas dominate.
6. **CompletableFuture uses intended executor automatically.** Async/default stages may use common pool.
7. **Timeout cancels remote effect.** Local completion and business outcome differ.
8. **Parallel stream for remote calls.** Common pool/blocking/resource policy is hidden.
9. **ThreadLocal is free.** Per-virtual-thread context can multiply memory.
10. **Structured concurrency API is stable across JDK21–25.** Concept stable; preview API evolved.
11. **Semaphore is global/rate limit.** It is local concurrent permit count unless coordinated.
12. **Ignore interruption.** Cancellation leaks tasks/resources.
13. **Per-pod safe means globally safe.** Multiply replicas.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full resource.

- Platform thread≈OS scheduled; virtual thread=JVM scheduled, mounted on carrier.
- Virtual threads improve blocking concurrency, not CPU speed/resource capacity.
- Use virtual-thread-per-task executor; do not pool them for scarcity.
- Bound DB/API with semaphore/pool/rate/admission and global replica math.
- CompletableFuture: apply=transform, compose=flatten dependency, combine=independent fan-in.
- Specify executors; avoid blocking child waits inside same small pool.
- Shared deadline, propagated cancellation, idempotent effects.
- Pinning is measured carrier occupation; avoid long blocking under monitor on affected JDK.
- Structured concurrency ties child lifetime/errors to parent; API preview/version-sensitive.
- Observe semaphore/pool waits, cancellations, pinning, carrier CPU, p99 and RSS.

## 8. PRACTICE SET FOR SELF-TEST

1. Compute Amdahl speedup for5% serial on16 processors.
2. At2,000 RPS and400 ms service time, estimate in-flight tasks; state what virtual threads change.
3. Design fan-out for required profile/orders and optional recommendations under600 ms deadline.
4. Explain `thenApply` versus `thenCompose` with a future-returning function.
5. Diagnose common-pool starvation caused by blocking parallel stream.
6. 20 pods×15 DB permits, database safe global180: redesign budget.
7. Explain why placing semaphore acquire after obtaining DB connection is ineffective.
8. Describe how to detect virtual-thread pinning and what evidence justifies code change.
9. Compare reactive backpressure with simply parking many virtual threads.
10. Give cancellation-safe resource acquisition pseudocode for semaphore and HTTP call.

## 9. CURATED RESOURCES

1. **OpenJDK JEP 444, “Virtual Threads.”** Stable Java21 design, goals, scheduling, ThreadLocal and observability rationale.
2. **Oracle Java 21 Core Libraries guide, Virtual Threads chapter.** Official usage, scheduling and adoption guidance.
3. **Oracle Java SE API, `Executors`, `ExecutorService`, `CompletableFuture`, `ForkJoinPool`, `Semaphore`.** Exact stable API semantics.
4. **Goetz et al., *Java Concurrency in Practice*, Chapters 6–10.** Executor design, cancellation, sizing and liveness foundation.
5. **OpenJDK structured-concurrency JEPs beginning JEP 428 and target-release successors.** Concept and preview evolution; select exact JEP for deployed JDK.
6. **OpenJDK scoped-values JEPs beginning JEP 429 and successors.** Bounded immutable context alternative and version status.
7. **Amdahl, “Validity of the Single Processor Approach…” (1967).** Formal serial-fraction speedup limit.
8. **Little, “A Proof for the Queuing Formula: L=λW” (1961).** In-flight capacity reasoning.
9. **Oracle JFR/JDK Mission Control docs for virtual threads.** Production diagnostics for pinning and thread behavior.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java Concurrency Basics.** JMM, locks, interruption and executors remain valid for virtual threads.
2. **JVM Memory/GC.** Platform stacks, heap context and allocation determine scale/footprint.

### After

1. **Spring Core and Transactions.** Thread-bound transaction/security context and blocking request handling meet virtual execution.
2. **Testing and Resilience.** Timeouts, cancellation, bulkheads and deterministic concurrency tests become application policy.
3. **Database Pools and SRE Capacity.** Virtual-thread scale must be reconciled with connections, queue wait and SLOs.
4. **Distributed Failure Semantics.** Local cancellation cannot decide remote outcomes.

---ANSWER KEY BELOW---

1. `1/(.05+.95/16)=1/.109375≈9.14×`; infinite processor cap20×.
2. `L=2000×0.4=800` average in flight. Virtual threads can represent blocked tasks cheaply; they do not reduce service time or add downstream capacity.
3. Start all concurrently under one scope/deadline. Profile/orders failure fails request and cancels siblings; recommendations can time out/fail to empty fallback. Propagate remaining deadline and ensure cleanup/observability.
4. `thenApply(x -> completedFuture(y))` yields nested `CompletableFuture<CompletableFuture<Y>>`; `thenCompose` flattens to `CompletableFuture<Y>` and sequences async dependency.
5. Common pool workers block on remote calls, leaving insufficient workers for other stages. Use virtual threads or dedicated bounded blocking executor/client, avoid blocking parallel stream, inspect pool/thread dumps.
6. Demand300>safe180. Equal static maximum9 per pod (180 total), preferably lower for headroom/other workload and responsive to replica changes; coordinate at DB/proxy/global layer.
7. Connection is already consumed while waiting for permit, so bulkhead does not protect pool and can deadlock/starve. Acquire workload permit before scarce connection/call, with deadline and finally release.
8. Use JFR virtual-thread/pinned events and supported trace flag/thread dumps; correlate duration/count with carrier starvation and latency under representative load. Change long blocking monitor/native regions, not every short synchronized block.
9. Reactive demand prevents upstream emission beyond requested capacity; parked virtual threads merely make waiting cheaper and can still accumulate unbounded work. Admission/bounds are still needed; models can coexist.
10. Track `acquired=false`; acquire with remaining deadline/interruption; set true; perform timeout-aware HTTP call; finally if acquired release. Propagate/restore interrupt, close response, and treat timeout outcome according to idempotency/status semantics.
