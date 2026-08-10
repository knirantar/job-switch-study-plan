# Java Concurrency Basics — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `08-java-concurrency-basics`  
**Expected study time:** 2–4 hours plus experiments

## 1. FOUNDATIONS

### Why concurrency exists

A backend waits for databases, networks and disks while also serving independent requests. A single sequential execution would leave CPU idle during waits and let one slow request block every other request. **Concurrency** lets multiple tasks make progress during overlapping time. **Parallelism** means work literally executes simultaneously on multiple cores. A single-core system can be concurrent by interleaving tasks without parallel execution.

A **process** is an operating-system resource container with memory and handles. A **thread** is an execution path within a process; Java threads share heap objects but have separate stacks and program counters. Sharing enables efficient communication, but interleavings make correctness nonlocal.

The history runs from time-sharing and operating-system scheduling through multiprocessor machines and server thread pools. Java originally exposed platform threads closely mapped to OS threads and supplied `synchronized`, `wait/notify` and `java.util.concurrent`. Modern Java also offers virtual threads for cheap blocking-style concurrency, covered deeply later. Virtual threads change cost, not the laws of shared-state correctness or downstream capacity.

### The three properties

**Atomicity** means an operation appears indivisible. **Visibility** means one thread’s write becomes observable by another. **Ordering** means observations respect specified constraints rather than arbitrary compiler/CPU reordering.

`counter++` is not atomic: read counter, add one, write. Two threads can both read 10 and both write 11, losing one increment. Declaring counter `volatile` makes individual reads/writes visible and ordered, but does not combine the three steps atomically.

A **data race** occurs when threads access the same variable concurrently, at least one access is a write, and accesses lack required synchronization ordering. A **race condition** is a broader result dependent on timing; even individually thread-safe calls can form an unsafe check-then-act sequence.

### Java Memory Model

The Java Memory Model (JMM), specified primarily in JLS Chapter 17, defines legal inter-thread observations. A **happens-before** relationship guarantees visibility and ordering: actions before releasing a monitor happen-before actions after another thread acquires it; a volatile write happens-before a later read of that variable; actions before starting a thread happen-before its actions; thread actions happen-before a successful join returns.

Without happens-before, a thread may see stale values and reasoning from source-code order is invalid. “It worked in my test” is no proof because timing, JIT optimization and hardware differ.

### Safety, liveness and performance

**Safety** means nothing bad happens: balances never go negative. **Liveness** means something good eventually happens: tasks do not deadlock/starve forever. **Progress** terms include blocking, lock-free and wait-free guarantees. A design can be safe but unusable because one global lock serializes all work; it can be fast but incorrect.

**Deadlock** is a cycle of threads waiting for resources. **Starvation** means a thread repeatedly fails to obtain resources. **Livelock** means threads keep reacting but make no progress. **Contention** is competition for shared resources. **Backpressure** limits producers when consumers/capacity cannot keep up.

## 2. CORE MECHANICS

### 2.1 Thread lifecycle and task abstraction

Java threads move through NEW, RUNNABLE, BLOCKED, WAITING, TIMED_WAITING and TERMINATED states. `Thread.State` is diagnostic, not a complete scheduler truth. Prefer submitting `Runnable`/`Callable` tasks to an executor rather than manually creating a thread per small task. `Callable<T>` returns a value and may throw; `Future<T>` represents eventual result/cancellation.

Never assume start order equals execution/completion order. `thread.start()` starts asynchronously; calling `run()` directly is an ordinary method call. `join()` waits and establishes happens-before for completed actions.

### 2.2 Intrinsic locks and synchronized

Every Java object has a monitor. A synchronized instance method locks `this`; static synchronized locks the `Class` object; block form locks an explicit object. Only code using the same lock coordinates.

```java
synchronized boolean withdraw(long amount) {
  if (balance < amount) return false;
  balance -= amount;
  return true;
}
```

The check and update share one critical section, preserving nonnegative balance. Synchronizing only getter/setter separately does not protect a compound check-then-update performed outside.

Keep critical sections small but complete. Do not call slow/unknown network code while holding a lock: it increases contention and can deadlock through callbacks. Monitor release occurs even when an exception exits the synchronized block.

### 2.3 Volatile

Use volatile for a variable whose reads/writes are individually sufficient and whose invariant does not combine it with other mutable state—shutdown flag is classic:

```java
private volatile boolean stopped;
while (!stopped) doOneUnit();
```

Volatile does not make `x++`, “if absent then insert,” or coupled fields atomic. Publishing an immutable object through a volatile reference can safely expose its fully constructed state, provided no unsafe later mutation.

### 2.4 Atomics and CAS

`AtomicInteger/Long/Reference` support atomic read-modify-write via compare-and-set (CAS). CAS changes value only if it still equals expected, retrying on contention. It avoids blocking for simple independent state.

`LongAdder` spreads updates across cells under contention and combines them for `sum()`. It is excellent for metrics but sum is not a linearizable snapshot for transactions. Atomic classes do not automatically protect invariants spanning multiple variables.

The **ABA problem** occurs when CAS observes A again after A→B→A and cannot detect intervening change. Version stamps/tagged references address relevant cases.

### 2.5 Explicit locks and conditions

`ReentrantLock` supports interruptible/timed acquisition, fairness option and multiple `Condition`s. Always unlock in `finally`. Fair locks reduce barging but may reduce throughput; fairness does not guarantee application-level fairness.

Conditions replace raw `wait/notify` for explicit locks. Wait in a loop, not `if`, because wakeups can be spurious and another thread may consume the condition before reacquisition:

```java
lock.lock();
try { while (queue.isEmpty()) notEmpty.await(); ... }
finally { lock.unlock(); }
```

Prefer higher-level blocking queues, semaphores, latches and concurrent collections over hand-written condition protocols.

### 2.6 Deadlock and lock ordering

Coffman conditions: mutual exclusion, hold-and-wait, no preemption and circular wait. Break one to prevent deadlock. For transfers between accounts, acquire locks in globally sorted account-ID order regardless of transfer direction. Equal IDs need identity/tie handling. Never use mutable ordering keys.

Timed `tryLock` can detect/avoid indefinite wait but requires rollback and retry policy; timeouts do not prove absence of deadlock.

### 2.7 Concurrent collections

`ConcurrentHashMap` permits scalable concurrent access and atomic operations such as `putIfAbsent`, `compute`, `merge`. Iterators are weakly consistent rather than global snapshots. `CopyOnWriteArrayList` makes every mutation copy the backing array—excellent for small, rarely modified listener lists; disastrous for frequent writes/large lists. `BlockingQueue` coordinates producers/consumers and can bound capacity.

Collections.synchronized wrappers serialize operations, but iteration and compound sequences require external synchronization per documentation.

### 2.8 Executors and queueing

A thread pool separates task submission from execution. Core/max threads, work queue, keep-alive and rejection policy interact. An unbounded queue often prevents growth beyond core threads and converts overload into latency/memory. A bounded queue plus explicit rejection makes saturation observable.

At 1,000 tasks/s arrival and 600/s service, backlog grows 400/s. A 20,000-task queue fills in 50 seconds. More threads help only if service capacity is limited by available concurrency rather than CPU/downstream quota.

Little’s Law: concurrency `L=λW`. At 2,000 requests/s and average 100 ms, about 200 in flight. If dependency latency becomes 500 ms at same arrivals, about 1,000 in flight. Bound concurrency around downstream capacity; an executor is not a rate limiter by itself.

### 2.9 Interruption and cancellation

Interruption is cooperative cancellation. Blocking methods may throw `InterruptedException` and clear interrupt status. Either propagate it or restore status with `Thread.currentThread().interrupt()` when unable to throw. Swallowing interruption prevents shutdown/deadlines.

`Future.cancel(true)` requests interruption; it cannot force arbitrary code to stop. Tasks must use interruptible operations or check status and release resources. Cancellation also needs business semantics: an HTTP timeout does not imply a downstream payment failed.

### 2.10 Semaphores, latches and barriers

A `Semaphore` controls permits, useful for bounding concurrent calls to a dependency. Always release in `finally` only after successful acquire. It bounds concurrency, not rate per second.

`CountDownLatch` lets threads wait for one-time events. `CyclicBarrier` coordinates repeated phases. `CompletableFuture` composes asynchronous stages, but default common-pool use and exception/cancellation behavior must be explicit; blocking stages should use suitable executors.

### 2.11 Thread confinement and immutability

The easiest shared-state bug is no shared mutation. Local variables/objects confined to one thread need no synchronization. Immutable objects can be safely shared after safe publication. Defensive copies prevent callers from mutating internal collections. Database transactions/message ownership can serialize business state outside JVM locks and work across service instances.

### 2.12 Testing and diagnosis

Concurrency tests are probabilistic unless they use specialized harnesses. OpenJDK jcstress explores JMM outcomes; JMH benchmarks performance. Thread dumps show BLOCKED/WAITING stacks and owned monitors; Java Flight Recorder profiles locks and thread activity. A unit test with sleeps is fragile and cannot prove race absence. Use latches/barriers to arrange interleavings, repeat stress, and assert invariants.

## 3. WORKED PROBLEMS

### Problem 1 — Lost increment

**Statement.** Two threads each increment shared int 100,000 times. Expected 200,000; why can result be lower?

**Solution.** `++` decomposes read/add/write. Interleaving both reads x, both calculate x+1, both write x+1 loses one. Use `AtomicInteger.incrementAndGet`, synchronized critical section, or LongAdder for approximate metric aggregation. Volatile alone fails.

**Mistake caught.** Believing one source statement is atomic.

### Problem 2 — Safe withdrawal

**Statement.** Balance ₹1,000; two threads withdraw ₹700. Prevent negative balance.

**Solution.** Lock around check and decrement on same account. First succeeds, leaves300; second observes300 and fails. Separately synchronized `getBalance` and `setBalance` still allow both checks. For multiple JVMs use atomic database conditional update/transaction, not JVM monitor.

**Mistake caught.** Thread-safe accessors do not create an atomic business operation.

### Problem 3 — Volatile stop flag

**Statement.** Worker loops until another thread requests stop.

**Solution.** Volatile boolean makes write visible to later reads and supplies ordering. Each iteration reads it. If work blocks indefinitely, flag alone cannot wake it; use interruption/close/resource timeout too.

**Mistake caught.** Nonvolatile flag may be cached/hoisted, or assuming volatile interrupts blocking I/O.

### Problem 4 — Transfer deadlock

**Statement.** T1 transfers A→B locking A then B; T2 B→A locking B then A.

**Solution.** T1 can hold A waiting B while T2 holds B waiting A. Order all account locks by immutable unique ID. Both acquire min ID then max, eliminating circular wait. Release reverse via nested synchronized exit.

**Mistake caught.** Ordering by transfer direction.

### Problem 5 — Atomic map initialization

**Statement.** Multiple threads initialize a per-tenant client once.

**Solution.** `computeIfAbsent` coordinates map update per API semantics; function must not recursively update same mapping and should avoid slow side effects whose retry/exception semantics are unsafe. Resource construction may occur again after failure/removal. Across pods it is not globally once.

**Mistake caught.** `if(!contains) put` race or claiming distributed singleton.

### Problem 6 — Pool saturation

**Statement.** Arrival1,000/s, service600/s, queue20,000.

**Solution.** Net400/s fills in50s. After saturation reject/throttle/durable-queue at least400/s or reduce arrival/increase actual downstream capacity. Unbounded queue only postpones failure and raises latency.

**Mistake caught.** Calling backlog a transient burst without duration/capacity math.

### Problem 7 — Interrupted task

**Statement.** A method catches `InterruptedException` but cannot declare it.

**Solution.** Perform necessary cleanup, restore interrupt with `Thread.currentThread().interrupt()`, and return/throw application cancellation. Do not continue normal long work. If method owns policy, convert to domain exception while preserving cause/status as appropriate.

**Mistake caught.** Empty catch clears cancellation request.

### Problem 8 — Concurrent metrics

**Statement.** 64 threads increment request counter; exact transactional snapshot is not needed.

**Solution.** `LongAdder` reduces hot CAS contention by striped cells; `sum()` combines them. For an exact linearizable sequence number, use `AtomicLong`; for durable/global IDs, neither suffices across processes.

**Mistake caught.** Using LongAdder for unique IDs or balance invariants.

### Problem 9 — Bound downstream concurrency

**Statement.** Service may run 500 virtual/platform tasks, but DB pool has 30 connections and must leave5 for admin/background work.

**Solution.** Limit this workload to at most25 permits or appropriately partition pool; acquire before operation, release finally, observe wait/deadline. More threads do not create connections. Consider transaction duration and global load across pods: 10 pods×25=250 potential DB calls.

**Mistake caught.** Sizing per-pod without multiplying deployment replicas.

## 4. REAL-WORLD / APPLIED CONTEXT

### Spring singleton beans

Spring singleton scope creates one bean per application context, commonly serving many request threads. Mutable fields are shared and require synchronization or redesign. Stateless services with immutable dependencies are easier. Request scope does not solve cross-request durable business state.

### Connection pools

HikariCP and similar pools bound concurrent database connections. Executor/virtual-thread concurrency above pool capacity waits. At 100 requests/s holding a connection 200 ms, Little’s Law suggests ~20 busy connections average, before variance/headroom. Long transactions and downstream calls while holding a connection amplify contention.

### Production diagnostics

`jcmd <pid> Thread.print`, thread dumps and JFR can reveal lock owners, blocked stacks and pool starvation. A deadlock detector can report monitor cycles, but logical deadlocks across queues/futures may not appear as monitor deadlock. Metrics need active count, queue depth/age, rejection, task latency and dependency saturation.

The compiled lab verifies 800,000 atomic increments, one-winner synchronized withdrawal, global lock ordering and bounded executor execution.

## 5. COMPARISON TABLE

| Mechanism | Guarantees/use | Blocking | Best use | Major boundary |
|---|---|---|---|---|
| `volatile` | visibility/order for variable | no | flags, immutable publication | no compound atomicity |
| `synchronized` | mutual exclusion + happens-before | yes | multi-step invariant | same lock required |
| `AtomicLong` | linearizable single-value RMW | retry/CAS | counters/sequence in one JVM | contention/multi-field |
| `LongAdder` | scalable accumulation | internal contention handling | metrics | sum not transactional snapshot |
| `ReentrantLock` | timed/interruptible lock, conditions | yes | advanced lock policy | must unlock finally |
| `ConcurrentHashMap` | concurrent map atomic operations | mostly nonblocking reads | shared lookup/update | compound external state |
| `BlockingQueue` | producer/consumer coordination | optionally | bounded work handoff | queue not capacity creation |
| `Semaphore` | concurrent permit bound | yes | dependency bulkhead | not rate/durable/global by default |
| immutability/confinement | eliminates shared mutation | no | default design | publication/object graph |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **One line is atomic.** `counter++` is multiple operations.
2. **Volatile counter fixes increment.** Visibility is not compound atomicity.
3. **Thread-safe components make workflow atomic.** Multiple calls can interleave.
4. **Different locks protect same field.** Coordination requires same lock/protocol.
5. **Synchronize every getter/setter.** Broader invariant may still race.
6. **Hold lock during remote I/O.** Contention/deadlock/latency explode.
7. **Unbounded executor queue is safe.** Overload becomes memory and latency.
8. **More threads increase throughput.** CPU/downstream bottlenecks cap service.
9. **Semaphore is rate limiter.** It limits concurrent in-flight, not starts per second.
10. **Swallow interruption.** Shutdown/cancellation breaks.
11. **ConcurrentHashMap is distributed.** It is local process memory.
12. **LongAdder supplies exact sequence.** It is an accumulator.
13. **Sleep-based test proves safety.** Timing tests miss interleavings.
14. **Virtual threads remove races/backpressure.** They reduce thread cost only.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the complete sections.

- Concurrency overlaps; parallelism executes simultaneously.
- Atomicity, visibility, ordering are distinct.
- `++` is read-modify-write; volatile does not make it atomic.
- Happens-before: monitor release/acquire, volatile write/read, start, join.
- Lock whole invariant with same lock; avoid remote calls inside.
- Atomics for single-value state; LongAdder for contended metrics.
- Global lock order prevents common transfer deadlock.
- Bounded queue + rejection exposes saturation.
- `L=λW`; multiply per-pod concurrency by replicas.
- Interruption is cooperative; propagate or restore.
- Prefer immutability, confinement and high-level concurrent utilities.
- jcstress for JMM outcomes, JMH for performance, JFR/thread dumps for diagnosis.

## 8. PRACTICE SET FOR SELF-TEST

1. Give an interleaving that loses one update for x=5 under two `x++` operations.
2. Determine whether `volatile List` makes mutations to ordinary ArrayList thread-safe.
3. Design a thread-safe bounded inventory decrement for one JVM and then multiple pods.
4. Explain safe publication of an immutable configuration object after reload.
5. Diagnose two threads both WAITING on futures submitted to the same single-thread executor.
6. Arrival800/s, average task time250 ms: estimate in-flight concurrency; then size impact across6 pods.
7. Compare AtomicLong and LongAdder for request metrics and invoice numbering.
8. Design cancellation handling for a task blocked on queue take.
9. Explain why CopyOnWriteArrayList suits 20 listeners read millions of times but not 1M-item frequent writes.
10. List evidence to gather for high latency with CPU25% and no obvious errors.

## 9. CURATED RESOURCES

1. **Java Language Specification, Chapter 17 “Threads and Locks.”** Authoritative JMM, synchronization, happens-before and allowed observations.
2. **Goetz et al., *Java Concurrency in Practice*, Chapters 1–10 and 14–16.** Core safety, liveness, task execution and memory-model reasoning.
3. **Oracle Java SE API, `java.util.concurrent` package summary and individual classes.** Exact executor, atomic, lock, queue and cancellation contracts.
4. **Herlihy & Shavit, *The Art of Multiprocessor Programming*, revised edition.** Linearizability, progress guarantees and concurrent algorithms.
5. **OpenJDK jcstress project and samples.** Empirical JMM outcome testing beyond ordinary unit tests.
6. **OpenJDK JMH project.** Correct concurrency/performance microbenchmark methodology.
7. **OpenJDK JEP 444, “Virtual Threads.”** Establishes what virtual threads change and explicitly what they do not.
8. **Little, “A Proof for the Queuing Formula: L=λW” (1961).** Formal capacity relationship.
9. **Oracle JDK Flight Recorder documentation.** Production lock/thread profiling and low-overhead event analysis.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Complexity and Problem Patterns.** Aggregate reasoning and invariants extend to interleavings/contention.
2. **Stacks/Queues.** Executors and blocking queues build on work handoff/backlog.
3. **Hashing.** Concurrent maps add atomicity semantics to local lookup.

### After

1. **JVM Memory, GC and Advanced Concurrency.** Deepens JMM, thread dumps, virtual threads, pools and performance.
2. **Spring Transactions.** Business atomicity moves into database transactions and proxy boundaries.
3. **Distributed Failure Semantics.** JVM locks stop at process boundaries; idempotency/consensus/transactions handle multiple nodes.
4. **SRE Capacity and Observability.** Pool queues, saturation, contention and cancellation become production signals.

---ANSWER KEY BELOW---

1. T1 reads5; T2 reads5; T1 writes6; T2 writes6. Final6 instead of7.
2. No. Volatile only governs reference reads/writes; ArrayList internal state mutations still race. Use confinement, immutability/copy, lock or appropriate concurrent structure.
3. One JVM: synchronized/lock around check+decrement or AtomicInteger CAS loop. Multiple pods: database atomic `UPDATE ... SET qty=qty-? WHERE qty>=?`, transaction/row version, check affected rows; JVM lock alone fails.
4. Fully construct immutable object, then assign to volatile/AtomicReference; readers take one reference snapshot. Do not mutate reachable components afterward; make defensive immutable copies.
5. Executor’s only worker runs task A waiting future B, but B is queued behind A and cannot run: thread-starvation deadlock. Avoid blocking dependency inside same bounded executor, compose differently or provide capacity/structure.
6. `L=800×0.25=200` average in flight globally for stated arrival. If 800/s is per pod, 200 each and1,200 across6; if global load-balanced, ~33.3 each. Clarify scope.
7. LongAdder for high-contention approximate metric snapshots; AtomicLong for local linearizable invoice sequence, though durable/global invoice numbering needs database/central protocol.
8. `take()` throws InterruptedException. Clean up, propagate or restore status and exit; shutdownNow requests interrupt. Do not swallow and retry forever unless policy explicitly says so.
9. Reads iterate immutable snapshot without locking; each of rare 20-listener changes copies tiny array. Copying one million references on frequent writes is O(n) allocation per write and untenable.
10. Thread dumps/states, executor active/queue/oldest age, connection pools, dependency latency and traces, lock/JFR events, GC pauses, I/O waits, per-route/tenant p95/p99, recent deploy/config and timeout/retry behavior.
