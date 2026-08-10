# Production Python

**Parent:** 07 — Python and MLOps  
**Target:** senior backend / AI-platform / MLOps engineering  
**Validated runtime:** CPython 3.13.4  
**Study time:** 3–4 hours plus the package lab

## 1. FOUNDATIONS

Python optimizes for readable expression, dynamic composition and a broad ecosystem. Production Python is not “Java without braces.” Its object/reference model, runtime typing, interpreter, import system and packaging create different strengths and failure modes.

Every Python object has **identity**, **type** and **value**. A name is a binding to an object, not a box containing a copied value. If two names bind the same list, mutation through one is visible through the other. Equality asks whether values compare equal; identity asks whether references designate the same object. Identity is appropriate for a singleton such as None, not for strings or numbers whose reuse/interning is implementation-dependent.

A **mutable** object can change in place: list, dictionary, set and most class instances. An **immutable** object cannot: integer, string, bytes and the tuple container. A tuple containing a mutable list cannot change which list it references, but the referenced list can mutate. Hash keys need stable equality/hash behavior, so a list cannot be a dictionary key.

Python is dynamically typed: values have runtime types, while annotations do not automatically validate or convert. **Duck typing** depends on supported behavior instead of inheritance. Static type checkers analyze annotations before execution; structural protocols express a required interface. An annotation improves tooling and design, but untrusted JSON, CSV, environment variables and model outputs still need runtime validation.

CPython is the dominant implementation. CPython 3.13 normally uses reference counting plus a cyclic collector. Immediate object destruction is an implementation behavior, not a portable resource contract; context managers own file, socket, lock and transaction lifetimes. Traditional CPython uses a Global Interpreter Lock so one thread executes Python bytecode at a time. Blocking I/O and native extensions can release execution, and Python concurrency is evolving, so every performance claim must name runtime, build and library.

Python grew from a scripting language into a backend/data/ML platform. Production use therefore needs reproducible packages, explicit configuration, tests, observability, deadlines, bounded concurrency, graceful lifecycle and artifact provenance. Quality comes from explicit boundaries and evidence, not merely adding enterprise ceremony.

Without these foundations, teams share mutable defaults between requests, compare strings by identity, use binary floats for money, swallow failures, wait for garbage collection to close sockets, materialize entire datasets, block an event loop, fork unsafe runtime state, load untrusted pickle and deploy floating dependencies.

## 2. CORE MECHANICS

### 2.1 Names, references and argument passing

Python passes object references by assignment. A function can mutate a mutable argument, but rebinding its local name does not change the caller’s binding:

~~~python
def change(values: list[int]) -> None:
    values.append(3)    # caller observes this mutation
    values = [99]       # only the local name is rebound

x = [1, 2]
change(x)
assert x == [1, 2, 3]
~~~

Document ownership. Prefer immutable boundary objects or returned new values unless in-place mutation is intentional and measured. A shallow list/dictionary copy duplicates only the outer container; nested values remain shared. Deep copy can be expensive and semantically wrong for sockets, model handles and objects whose identity represents external state.

### 2.2 Defaults and closure binding

Default argument expressions are evaluated once when a function is defined. A default empty list is therefore shared across calls. Use a None sentinel and construct inside, or an immutable default. Dataclasses use a default factory for per-instance mutable containers.

Late-bound closures look names up when invoked. Three lambdas created in a loop may all read the final loop value. Bind intentionally with a default parameter or factory. The rule is about name lookup time, not a lambda-specific defect.

### 2.3 Collections and complexity

Lists are dynamic arrays: indexing and amortized append are O(1), front insertion/deletion O(n). A deque provides O(1) append/pop at both ends. Dictionary/set hash lookup is average O(1), but hashing, collisions, memory and key design matter. Modern dictionaries preserve insertion order; sets promise membership, not meaningful order.

Choose by semantics. Converting claims to a set loses multiplicity. Building a dictionary by claim ID overwrites duplicate keys unless rejected. For large homogeneous numeric data, Python object/list overhead is far greater than raw values; NumPy uses contiguous typed buffers and is covered later.

### 2.4 Iterables, iterators and generators

An iterable can produce an iterator. An iterator is one-shot and raises StopIteration when exhausted. A generator function yields lazily and retains its execution frame between requests. The lab’s processor reads nothing until next is called, then consumes exactly one row. This supports bounded-memory streaming.

Laziness moves failure to iteration time. A generator may validate successfully on construction and fail at row 40,000. Generators can also retain locals/resources. If a caller stops early, explicit context ownership is still needed. A list comprehension is often clearer for small bounded data; a generator expression is better when the pipeline remains lazy end to end.

### 2.5 Function signatures and dependency boundaries

Use positional-only parameters when parameter names are not public API and keyword-only parameters when meaning must be explicit. The lab’s scorer requires keyword arguments for claim ID and amount, avoiding accidental exchange of same-shaped values.

Functions are first-class dependencies. A protocol object or callable can be passed without a framework. Separate pure parsing/transformation from I/O. Avoid mutable module globals and hidden singleton clients.

Decorators execute wrapping logic at definition/import. Preserve metadata with functools.wraps. Retry decorators must consider idempotency, remaining deadline and exception class; retrying every exception can duplicate payments or conceal programming bugs.

### 2.6 Classes, dataclasses and protocols

Favor composition over deep inheritance. Dataclasses generate initialization, representation and comparison. Frozen prevents normal assignment but is not a security control or deep immutability. Slots removes the usual per-instance dictionary, catches accidental attributes and may reduce memory, with inheritance/introspection trade-offs.

Use class methods for alternate constructors, properties for cheap attribute-like calculations/validation, and static methods only for logically namespaced functions. Structural Protocol types describe behavior without forcing inheritance. The test scorer satisfies the lab protocol by method shape. Static analysis can check this; runtime does not automatically enforce the annotation.

### 2.7 Static types and runtime validation

Use precise contracts. Iterable input accepts streams; Iterator output communicates laziness. Prefer domain objects over nested dictionaries of Any. Any disables checking downstream, whereas object requires narrowing.

Useful constructs include unions, generics, TypedDict for dictionary shape, Literal or Enum for closed choices, NewType for static ID distinctions and Protocol for behavior. None of them validates network input automatically. Parse unknown data, verify shape, finite numeric values, range and domain invariants, then construct trusted objects.

### 2.8 Numeric correctness

Binary floating point cannot exactly represent most decimal fractions; 0.1 plus 0.2 is not exactly 0.3. Float is appropriate for scientific/ML computation with tolerance analysis. For financial decimal rules, use integer minor units or Decimal.

Construct Decimal from strings, define scale and rounding. The lab quantizes 1250.235 to 1250.24 using round-half-even. Validate finite values before ordering: the initial test run exposed that Decimal NaN can survive quantization and a range comparison raises InvalidOperation. Parsing as a numeric type does not guarantee an ordinary finite number.

### 2.9 Exceptions and error taxonomy

Catch only exceptions that can be handled and at the narrowest scope. Translate low-level parsing failure into a domain error while preserving the cause:

~~~python
try:
    amount = Decimal(raw)
except InvalidOperation as error:
    raise ValueError("amount must be decimal") from error
~~~

Bare re-raise preserves traceback. Do not catch BaseException normally because it includes process/user control exceptions. Never swallow Exception and return a plausible success. Cleanup belongs in a context manager or finally; returning from finally can suppress an exception.

Separate expected validation/conflict/not-found, transient dependency, permanent dependency, outcome-unknown and programming defects. A timeout after a remote commit requires idempotency/reconciliation, not blind retry. Keep secrets and regulated values out of error messages.

### 2.10 Context managers and resource ownership

With invokes enter and exit even when the body raises. Use it for files, locks, database transactions, temporary directories and spans. An exit method returning true suppresses the exception, so do that only when suppression is the explicit contract. ExitStack manages a dynamic number of resources.

Closing eventually is not a timeout. Configure connection/read/transaction deadlines. Async resources use async with. Do not depend on destructor timing for correctness or portability.

### 2.11 Memory and garbage collection

Reference counting often reclaims objects immediately in CPython; cycles require cyclic GC. Production “leaks” may be retained references, unbounded cache, worker queues, fragmentation, native allocation or allocator RSS not returned to the OS. Diagnose with representative workload, RSS/native metrics, tracemalloc and heap/allocation profiles.

Generators reduce container retention but keep frames and captured objects. An unlimited least-recently-used cache is explicitly unbounded. Weak references serve specialized cache/observer designs and do not replace ownership.

### 2.12 Modules, imports and layout

A module executes top-level code on first import per interpreter and is cached. Avoid network calls, thread creation, model loading and process-wide configuration at import time. Put initialization in an application factory/lifecycle. Circular imports often reveal tangled ownership; extract contracts or invert dependencies.

Protect multiprocessing entry points with the main-module guard. Do not edit the interpreter search path in production. A source layout places code under src/package and tests separately; it prevents repository-root imports from masking packaging errors. The lab uses source layout and PYTHONPATH only for a dependency-free local run. CI should build/install the distribution in a clean environment.

### 2.13 Packaging and reproducibility

The project file standardizes build backend and metadata. A source distribution contains source/build information; a wheel is a built distribution. Library metadata expresses compatible dependency ranges; a deployed application needs a fully resolved lock/constraints/hashes strategy for Python version, OS/architecture and native wheels.

Build in isolated CI, test the installed wheel, generate SBOM/provenance and promote the same artifact. Do not install unpinned packages at service startup. Validate ABI, libc, CPU/GPU library and accelerator compatibility. Defend against dependency confusion through controlled indexes, namespaces and authentication.

### 2.14 Configuration and secrets

Centralize configuration precedence and typed parsing. Fail startup on missing/invalid required values. The string “false” is truthy if treated as an arbitrary nonempty string; parse booleans explicitly.

Prefer workload identity and secret-manager/file injection. Secrets do not belong in source, image, arguments, logs or exceptions. Environment variables can leak through process inspection, children and dumps; evaluate platform threat model. Design rotation and safe diagnostic rendering.

### 2.15 Logging, metrics and traces

Libraries use logging APIs and should not configure global handlers. The process boundary configures structured UTC events. Record stable event, service/version, correlation, safe error category and immutable release/model identity; omit tokens, raw patient/account fields and model inputs.

Measure logical outcomes separately from attempts, duration distributions, queue/pool saturation and Python runtime health. Context variables carry task-local context through asyncio better than thread locals, but processes and messages need explicit propagation.

### 2.16 Testing

Unit tests cover pure behavior and boundaries; integration tests exercise real database/broker; contract tests protect schemas; property tests explore invariants; load/failure tests prove operation. Inject time, randomness, UUID and I/O for determinism. Coverage percentage is not assertion quality.

The lab tests decimal rounding, missing/NaN/range input, frozen value behavior, generator laziness, exact threshold and invalid model output. The NaN regression demonstrates why edge cases are first-class evidence.

### 2.17 Threads, processes and the GIL

Threads share memory and work well for blocking I/O; synchronization and thread-safe clients are required. Under traditional CPython, pure Python bytecode threads do not run in parallel across cores. Native libraries may release the lock, so benchmark.

Processes give CPU parallelism/isolation but require serialization, importable worker functions, safe start method and memory/IPC design. Do not casually pass sockets, model handles or CUDA state. Forking a multithreaded or accelerator-initialized process can be unsafe.

Modern Python includes multiple-interpreter and free-threaded evolution. Library compatibility/build mode must be proven. The GIL does not make compound domain operations logically atomic; use locks, queues or isolated ownership.

### 2.18 Async boundaries

Asyncio is cooperative concurrency: a task runs until await. It helps many concurrent I/O operations, not CPU acceleration. A synchronous HTTP/database call, time.sleep or CPU-heavy PDF/feature code blocks the event loop. Use async-native libraries or bounded executor/process offload.

Cancellation is a request delivered at await points, not transactional rollback. Clean up in finally/async context and reconcile external effects. Bound tasks with queues/semaphores and structured lifetimes. Unlimited task creation merely moves overload into memory and downstream pools.

### 2.19 Security boundaries

Never evaluate untrusted code. Pickle deserialization can execute code and is unsafe for untrusted model artifacts. Use constrained formats/schemas plus signature/provenance where possible and isolate custom code as executable software. Parameterize SQL. Validate paths/root containment. Use safe YAML parsing.

Invoke subprocess using an argument list, shell disabled, explicit environment/directory, timeout and output bound. Python introspection is not a sandbox. Execute untrusted plugins/models in a restricted process/container/VM with identity, network and resource policy.

### 2.20 Service lifecycle

Startup validates configuration, initializes bounded pools, loads/checks model artifact and only then becomes ready. Liveness means the process can progress; readiness means it may receive traffic. Shutdown stops admission, drains within grace, cancels/reconciles work, flushes bounded telemetry and closes resources.

Workers multiply model memory and connections. Four workers each loading 2.5 GiB need at least 10 GiB just for model pages and can open four times each pool default. Select process count from measured RSS, CPU and useful throughput plus global downstream budgets.

## 3. WORKED PROBLEMS

### Problem 1 — Shared mutable default

**Statement.** A function with a default empty list returns [1] on the first call and [1,2] on the next. Explain and repair its ownership contract.

**Solution.** The default expression ran once at definition, so both calls mutate one list. Use None and create a new list inside. If a caller-supplied list is allowed, specify whether it is mutated; otherwise copy/return a new collection. Use a dataclass default factory for per-instance state.

**Mistake caught:** assuming defaults evaluate per call.

### Problem 2 — Identity versus equality

**Statement.** A status comparison by identity passes for a literal and fails for a parsed READY string.

**Solution.** Interning can make literal objects identical but is not the equality contract. Compare by value. Use identity for None or deliberately shared sentinels.

**Mistake caught:** depending on interpreter interning.

### Problem 3 — Decimal NaN

**Statement.** Decimal NaN is quantized then range-compared. Why did the lab initially raise InvalidOperation?

**Solution.** NaN can remain a Decimal special value but ordered comparison is invalid. Check is_finite before range and normalize all invalid input to the documented domain error. Test NaN and both infinities.

**Mistake caught:** successful construction means finite numeric value.

### Problem 4 — Streaming 10 million rows

**Statement.** Each row averages 400 serialized bytes and code materializes all rows before scoring.

**Solution.** Serialized minimum is 4 GB decimal; Python dictionaries, strings and pointers multiply heap. Stream iterator through validation into bounded scoring/output batches, checkpoint only after durable idempotent output, and quarantine invalid rows with safe reason. Ensure downstream does not convert back to a list.

**Mistake caught:** serialized bytes equal Python heap and lazy producer implies lazy pipeline.

### Problem 5 — Swallowed exception

**Statement.** Worker catches every Exception, returns None and marks the job complete.

**Solution.** It turns malformed rows, transient outage, programming defects and outcome-unknown timeouts into silent data loss. Quarantine known invalid input; bounded-retry known transient errors; reconcile unknown effects; otherwise fail and preserve safe traceback/context.

**Mistake caught:** treating suppression as resilience.

### Problem 6 — Mixed I/O and CPU

**Statement.** One hundred HTTPS calls wait 100 ms; then each item needs 200 ms pure-Python CPU on eight cores.

**Solution.** Bounded asyncio/threads overlap network wait: ideal concurrency 20 gives roughly 0.5 seconds plus overhead/rate limits. CPU totals 20 CPU-seconds; traditional GIL threads do not parallelize Python bytecode, so a process pool could approach at least 2.5 seconds plus serialization/imbalance. A vectorized native implementation may differ; benchmark.

**Mistake caught:** one executor fits every stage.

### Problem 7 — Async blocking

**Statement.** An async handler calls synchronous HTTP with 30-second timeout and time.sleep(1).

**Solution.** Both block the loop. Use an async HTTP client and asyncio sleep, or bounded thread offload for legacy blocking code. Propagate a shorter remaining deadline and cap concurrency. Long work may require an asynchronous job API.

**Mistake caught:** async syntax makes blocking code nonblocking.

### Problem 8 — Wheel differs from source

**Statement.** Repository tests pass but installed wheel lacks a subpackage/template.

**Solution.** Tests imported the working tree and packaging discovery/data omitted artifacts. Use source layout, isolated build, inspect/install wheel into clean environment and run tests/smoke against installed distribution. Verify contents and SBOM.

**Mistake caught:** source tests prove shipped artifact.

### Problem 9 — Worker multiplication

**Statement.** Four workers each load a 2.5-GiB model and open 32 DB connections on an 8-GiB node; DB permits 100.

**Solution.** Models alone total 10 GiB before interpreter/native overhead and 128 connections exceed DB. Reduce workers/model footprint or use a separate/shared model server; globally allocate DB connections with admin/rollout headroom. Measure actual memory sharing and throughput rather than assuming copy-on-write.

**Mistake caught:** process-local defaults do not consume global resources.

## 4. REAL-WORLD / APPLIED CONTEXT

CPython’s official data model specifies identity, type, value and mutability. It documents reference counting plus cyclic collection as CPython behavior while allowing other implementations to delay collection. This is why context managers, not destructor timing, own production resources.

The standard concurrent.futures package presents one Future interface over thread and process executors. Official documentation states that process-pool inputs/results must be picklable and the main module importable. Threads versus processes remain workload/runtime decisions, not style preferences.

The included claim-batch package uses source layout and project metadata with no runtime dependency. On CPython 3.13.4, compileall and six unit tests pass. Concrete data proves 1250.235 becomes 1250.24 by half-even rounding, a score exactly 0.80 triggers review, rows are consumed lazily, and a score 1.01 fails closed. The first run exposed and fixed the NaN boundary. These are correctness results, not performance benchmarks. Because build dependencies were not downloaded, wheel construction itself has not been claimed as verified.

## 5. COMPARISON TABLE

| Concurrency choice | Best fit | Sharing/isolation | Main cost/failure |
|---|---|---|---|
| Synchronous | simple bounded work | one stack | waits idly on I/O |
| Threads | blocking I/O, native code releasing GIL | shared memory | races, stack/context, CPU bytecode limit |
| Asyncio | many async I/O operations | cooperative tasks on loop | one blocking call stalls loop |
| Processes | pure-Python CPU or isolation | serialization/IPC | startup, memory, pickle/import constraints |
| Vector/native/GPU | numeric parallel work | library-owned buffers | copy/ABI/native crash/oversubscription |

| Construct | Mutation | Use | Boundary |
|---|---|---|---|
| list | mutable | ordered dynamic values | front insert O(n), shared alias/default |
| tuple | immutable references | fixed record or hash key | contained mutable object may change |
| dictionary | mutable | key lookup/mapping | duplicate overwrite and memory |
| set | mutable | uniqueness/membership | no multiplicity/order contract |
| generator | stateful one-shot | streaming pipeline | lazy exceptions, exhaustion/resource retention |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Names store copied values.** They bind references; in-place mutation can be shared.
2. **Identity means equality.** Compare values; reserve identity for None/custom sentinels.
3. **Mutable default is new per call.** It is created once; use sentinel/factory.
4. **Tuple is deeply immutable.** Referenced mutable members can change.
5. **Shallow copy isolates nested data.** Inner references remain shared.
6. **Annotations validate JSON.** They do not enforce runtime shape/range.
7. **Any is a safe flexible type.** It disables checking; narrow at boundaries.
8. **Float exactly represents money.** Use defined Decimal/minor-unit rules.
9. **Parsed Decimal is finite.** NaN/infinity need explicit rejection.
10. **Generator is reusable.** It is one-shot and can fail during iteration.
11. **GC closes resources promptly everywhere.** Use context management.
12. **Catching every exception is robust.** It hides defects and data loss.
13. **Return in finally is harmless.** It can suppress exceptions/results.
14. **Frozen dataclass is deep immutability/security.** It prevents normal assignment only.
15. **Imports merely declare symbols.** Module top-level code executes.
16. **Repository tests test the wheel.** Working-tree imports can hide packaging omissions.
17. **Dependency range is a deployment lock.** Application needs a resolved reproducible environment.
18. **GIL makes compound logic safe.** Domain races remain; synchronize explicitly.
19. **Threads never run work in parallel.** Native extensions may release the GIL; runtime evolves.
20. **Async definition makes blocking calls async.** Blocking code stalls the event loop.
21. **Cancellation rolls back effects.** External effects need idempotency/reconciliation.
22. **Unlimited tasks increase throughput.** They exhaust memory, pools and dependencies.
23. **Pickle is safe model data.** Loading untrusted pickle can execute code.
24. **Environment variables are secret by nature.** They can leak through process/tooling.
25. **More workers always improve capacity.** Memory/connections/models multiply.
26. **Local timing is production capacity.** Record environment/data/concurrency/bottleneck.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Names bind objects; equality compares value; identity compares object.
- Mutable: list/dict/set. Immutable: integer/string/bytes and tuple references.
- Defaults evaluate once; use None or a factory for per-call/instance mutable state.
- Iterators are one-shot; generators are lazy and can fail during iteration.
- Type precisely, use Protocol for behavior, validate unknown data at runtime.
- Decimal from string; define rounding/scale; reject nonfinite.
- Catch narrowly, chain causes, never swallow; own cleanup with context managers.
- Package with project metadata and source layout; build isolated wheel, test installed artifact, lock and attest.
- Threads for blocking I/O; processes for pure Python CPU; asyncio for cooperative async I/O; benchmark native code.
- Bound timeouts, retries, tasks, pools, queues, workers and memory.
- No untrusted eval/pickle or shell concatenation; parameterize SQL and sanitize telemetry.
- Startup validates/loads then ready; shutdown stops admission, drains and closes.

## 8. PRACTICE SET FOR SELF-TEST

1. Predict aliasing after a shallow copy of a dictionary containing a list of claim dictionaries; provide an ownership-safe design.
2. Repair a dataclass with a shared tags list when equality, hashing and concurrent readers matter.
3. Design static types and runtime validation for claim ID, decimal amount, currency, optional diagnosis and closed status.
4. Stream a 50-GB CSV through validation, scoring and durable output with bounded memory/checkpoints.
5. Classify retry/error handling for malformed row, HTTP 429, timeout after remote commit, model bug and task cancellation.
6. Choose async, threads, processes and vectorization for 10,000 API calls plus NumPy and pure-Python feature stages.
7. Diagnose an asyncio service whose p99 jumps whenever PDF parsing starts.
8. Design a reproducible wheel/container pipeline with native ML dependencies and offline artifact promotion.
9. Threat-model loading a downloaded pickle model and propose a safer model artifact contract.
10. Size model workers and DB pools on a 16-GiB node when model RSS is 3 GiB, base worker 400 MiB, DB maximum 120 and 30 connections reserved.

## 9. CURATED RESOURCES

1. Python 3.13 Language Reference, *Data Model*. Authoritative identity/type/value, mutability, classes, generators and implementation boundaries.
2. Python 3.13 Library Reference, *typing*, plus the Typing Specification. Protocols, generics, narrowing and static/runtime separation.
3. PEP 484, *Type Hints*; PEP 544, *Protocols*; PEP 585, built-in generics. Exact design/rationale of modern contracts.
4. Python Library Reference, *decimal*. Context, signals, special values, quantization and rounding behavior.
5. Python Library Reference, *contextlib*, *exceptions*, *logging*, *tracemalloc* and *gc*. Exact operational/resource mechanics.
6. Python Library Reference, *asyncio*, *threading*, *multiprocessing*, *concurrent.futures* and *contextvars*. Version-specific concurrency APIs.
7. Python Packaging User Guide, *Packaging Python Projects*, project-file specification and reproducible environments. Current build/distribution guidance.
8. PEP 517, PEP 518 and PEP 621. Isolated build backend/frontend and standardized project metadata.
9. Brett Slatkin, *Effective Python*, 3rd edition, sections on functions, generators, classes, concurrency, robustness and testing. Focused production trade-offs.
10. David Beazley and Brian K. Jones, *Python Cookbook*, 3rd edition, Chapters 1, 4, 7, 8, 12 and 14. Deeper collection, iterator, class, concurrency and test recipes; check changes in current Python.
11. OWASP, *Deserialization Cheat Sheet*. Threat model and mitigations for pickle-like executable deserialization.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java and JVM:** useful contrast for reference semantics, runtime typing, GC and threading.
2. **Coding Foundations:** complexity, collections and error reasoning transfer directly.
3. **Containers and CI/CD:** packaging/runtime artifact needs reproducible delivery and lifecycle.
4. **Metrics, Logs and Traces:** makes Python process behavior operable.

### After

1. **FastAPI and Async:** applies typing, asyncio, context and lifecycle to HTTP.
2. **ML Fundamentals:** builds numeric/data work on reliable Python boundaries.
3. **ML Lifecycle:** extends packages, testing and reproducibility to data/models.
4. **Model Serving and LLMOps:** uses concurrency, memory, security and lifecycle under serving load.

---ANSWER KEY BELOW---

1. The outer dictionary copy is distinct but the claims list and inner claim dictionaries are shared. Appending through either appears in both; changing the inner ID appears in both. Parse into immutable Claim objects in a tuple, rebuild domain data at ownership boundaries, or make an explicit domain-aware copy. Avoid blindly deep-copying handles/models.
2. Use a default factory for a mutable list, or preferably an immutable tuple for read sharing. If the object is a hash key, freeze it and ensure every field has stable equality/hash. Publish a new immutable instance for updates rather than mutating shared readers.
3. Use a ClaimId value object or NewType plus regex/length validation; Decimal from string with finite/range/scale and currency-specific rounding; Enum/Literal plus runtime membership for currency/status; diagnosis string or None with code-system validation. Boundary schema parses, domain constructor enforces invariants.
4. Open with context; iterate CSV rows; validate; batch to bounded/vectorized scorer; write idempotently; checkpoint source offset and output version only after durable commit. Quarantine invalid rows with safe reason and fail systemic schema/model errors. Cap workers/queues and record counts/checksums.
5. Malformed row is permanent quarantine. 429 is bounded retry honoring Retry-After/deadline/jitter. Timeout after possible commit is outcome unknown and needs idempotency lookup/reconciliation. Model bug fails fast/quarantines version, not generic retry. Cancellation propagates after cleanup; reconcile effects.
6. Async or bounded threads for I/O according to client support/rate limits. NumPy may use native threads/release GIL, so avoid nested oversubscription and measure. Pure-Python CPU uses processes/interpreters or vectorized rewrite. Bound queues and account for serialization/memory.
7. PDF parser blocks/consumes CPU on event loop. Confirm with loop-lag and trace. Isolate in bounded process pool or external worker with file/page/time/memory limits; use async job API for long work and sandbox untrusted parser. Thread offload only when measured suitable.
8. Pin Python base by digest; resolve platform-specific transitive packages/hashes from controlled index; isolated-build target wheels; test native imports and installed wheel; produce SBOM/provenance/signature; build nonroot container and promote exact digest. Mirror artifacts and validate ABI/architecture.
9. Pickle load can execute arbitrary code. Do not load untrusted pickle. Prefer constrained operator/data format plus schema, signed provenance/digest and registry admission. Convert custom models in secretless network-restricted sandbox, scan, version/shape-check and canary. Treat custom code as software.
10. Usable DB connections are 90. Raw memory permits floor(16/3.4)=4 workers but leaves no OS/native/headroom. With 25% node reserve, 12 GiB permits three workers (10.2 GiB) and 1.8 GiB within planned usable space; validate RSS. Ninety/three is 30 each maximum, but rollout/other consumers require lower, perhaps 20–25. Benchmark and consider a separate model server.
