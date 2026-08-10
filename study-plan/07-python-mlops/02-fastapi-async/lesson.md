# FastAPI, ASGI, and Async Service Engineering

**Parent:** 07 — Python and MLOps  
**Target:** senior backend / AI-platform / MLOps engineering  
**Validated stack:** CPython 3.13.4, FastAPI 0.138.2, Pydantic 2.13.4, Starlette 1.6.0, HTTPX 0.28.1  
**Study time:** 3–4 hours plus the executable API lab

## 1. FOUNDATIONS

FastAPI is an HTTP/API framework built on Starlette’s ASGI toolkit and Pydantic validation/schema generation. Its productivity comes from using Python type annotations as one source for request extraction, validation, dependency resolution and OpenAPI. That convenience does not remove the need to design API semantics, trust boundaries, concurrency limits and lifecycle.

**WSGI** models a synchronous request/response callable and fits traditional blocking applications. **ASGI** generalizes an application as an asynchronous callable receiving a connection scope plus receive/send channels. ASGI supports HTTP, WebSocket and long-lived/asynchronous interactions. An ASGI server such as Uvicorn owns sockets/protocol parsing and invokes the application; FastAPI builds routing/dependencies/schema above Starlette.

An **event loop** schedules cooperative tasks. One task executes Python until it awaits an operation that yields control. Thousands of network waits can overlap on one loop thread, but one blocking database call, sleep, file parse or CPU loop blocks all tasks on that loop. Async increases concurrency for appropriate I/O; it does not create CPU parallelism or automatically reduce latency.

FastAPI path-operation declarations form a boundary contract. Path/query/header/cookie parameters and request body are extracted separately. Pydantic models validate/serialize structured data. Response models constrain output and documentation. Dependencies form a directed graph whose values are cached per request by default. Lifespan owns process-wide resources; yield dependencies own request-scoped resources.

The motivation is a service layer that is explicit and machine-readable. Without it, request parsing is duplicated, schema drifts from code and every handler hand-builds errors. But generated OpenAPI can create false confidence: a type annotation is not business authorization; input validation is not output correctness; documentation is not compatibility; async syntax is not scalability.

Production failure modes include accepting unexpected fields, silently coercing money, leaking validation inputs, using authentication without tenant/resource authorization, holding a database session across a streaming response, firing critical work in an in-process background task, creating unlimited coroutines, retrying beyond client deadlines, multiplying model memory across workers and declaring readiness before dependencies/models are ready.

## 2. CORE MECHANICS

### 2.1 ASGI request lifecycle

For HTTP, the server receives a connection and constructs a scope containing method, path, headers, client/server and ASGI metadata. It calls middleware and routing, reads body events from receive, and sends response start/body events. Middleware order matters: outer middleware sees requests first and responses last.

FastAPI matches a route, solves dependencies, validates parameters/body, invokes a sync or async endpoint, validates/serializes the response and applies exception handlers. Sync path operations/dependencies are normally run in a thread pool so they do not directly block the event loop, but that pool is finite and shared. An async function that calls blocking code is worse because FastAPI assumes it will yield cooperatively.

Use async endpoint when its call chain is async-native. Use sync endpoint for blocking libraries when thread execution and pool capacity are intentional. For CPU-heavy work, a thread pool under traditional CPython is not a general solution; use bounded process/native/worker architecture.

### 2.2 Routing and HTTP semantics

Routes should use nouns/resources and correct methods. GET is safe/read-only and should be idempotent; PUT replaces or sets a known resource idempotently; DELETE is idempotent in desired state; POST generally creates/commands and may need an idempotency key. PATCH applies partial change with explicit merge/JSON patch semantics.

Return status codes as protocol, not decoration: 200 response, 201 created plus Location, 202 durably accepted async operation, 204 no body, 400 malformed semantics, 401 unauthenticated, 403 authenticated but forbidden, 404 absent or intentionally concealed, 409 state/idempotency conflict, 412 failed precondition, 422 validation, 429 admission/rate limit, 503 unavailable, 504 owned gateway/dependency deadline. Document retry behavior.

The lab POST returns 200 because it synchronously calculates a score. A real expensive model request may still be synchronous if it meets bounded latency; a deployment/training operation should usually durably enqueue and return 202 with operation ID rather than pretend an in-process task is durable.

### 2.3 Pydantic v2 input models

Declare required fields, ranges, lengths/patterns, closed enums and cross-field validators. For public/regulated APIs, forbid extra fields when silently ignoring them could hide a client/schema error. Strict mode reduces coercion, but JSON has only number—not Decimal. The lab explicitly accepts an exact decimal string, parses before core validation, rejects JSON floats and then applies finite/range/digits/scale rules.

That boundary was discovered through tests. With a strict Decimal field, string 1250.00 initially returned 422 because Pydantic required an actual Decimal instance after JSON decode. A before-validator solved this deliberately. A second failure showed returning Decimal NaN to later validation produced an error payload containing Decimal NaN that current FastAPI/Starlette could not JSON-encode. Rejecting nonfinite in the before-validator avoided leaking the problematic input into the validation response.

Do not echo raw validation input in custom errors/logs. FastAPI release notes in current versions explicitly warn about leaking information when re-raising validation errors. Normalize safe error codes/locations/messages; preserve details only in restricted evidence.

### 2.4 Output contracts and serialization

A response model validates and filters output. This is a defense against accidentally returning internal attributes, but not against authorizing the wrong object. Distinguish input and output schemas; fields such as password, secret, internal risk explanation and audit metadata must never be on public output.

Decimal JSON serialization commonly becomes string to preserve exactness, as the lab shows risk score 0.125 serialized as "0.125". Decide API representation—decimal string, integer minor unit or JSON number—and encode in schema/examples/consumer tests. Datetimes use timezone-aware UTC and defined precision. Enums should have stable wire values independent of display label.

Avoid returning raw ORM objects/lazy relationships after session closure. Map to explicit DTO. Response validation failure is a server defect and should be visible as 5xx/telemetry, not converted to a client 422.

### 2.5 Dependency injection graph

Depends declares values derived from request/app state or other dependencies. Use it for authentication context, authorization policy, database transaction/session, service client and configuration—not as a hidden global service locator.

Dependencies are cached per request by default: two consumers of the same dependency normally share its result. Disable cache only with a real semantic reason. Dependency order follows graph, not textual intuition. Overrides make tests convenient but can hide wiring errors; retain integration tests with real dependencies.

A dependency with yield behaves like a context manager: setup before endpoint, cleanup later. FastAPI 0.118 changed streaming behavior so cleanup occurs after sending the response, allowing a yielded resource to remain usable during StreamingResponse. Current 0.138.2 behavior must still be tested before relying on session lifetime. Holding a DB transaction for a slow client stream can exhaust pools; prefer materialize/cursor-specific design.

### 2.6 Lifespan

Use lifespan async context manager for process-level initialization and teardown: create HTTP/DB clients, load and verify model, start bounded resources; yield only when ready; close after server stops accepting/draining according to deployment lifecycle. Import-time initialization makes tests, worker spawn, CLI and failure handling brittle.

Each process worker runs its own lifespan. Four workers load four models/connection pools unless architecture shares externally. Initialization must be idempotent and report readiness. Partial initialization cleans already-created resources with an exit stack or structured try/finally.

The lab stores one scorer and a semaphore of four in application state during lifespan. The readiness endpoint checks that state exists. Production readiness should also represent critical local initialization and perhaps shallow dependency ability, but not perform expensive writes or flap on every transient dependency.

### 2.7 Authentication and authorization

Authentication verifies principal; authorization decides action on resource/tenant. API keys are shown only as a lab mechanism and compared to a fixed value; production should use a secret store, constant-time comparison where relevant, rotation, rate limits and preferably workload/user identity standards.

For OAuth2/OIDC JWT, verify signature using trusted issuer/JWKS, algorithm allowlist, issuer, audience, expiry/not-before and token type; handle key rotation/cache. Never merely decode. Map immutable subject/tenant/roles/scopes to domain authorization. A scope claim is not automatically permission for every claim record; enforce ownership/policy in the service/data query.

Return 401 for absent/invalid authentication (and WWW-Authenticate where standard), 403 for known principal lacking permission. Avoid resource enumeration through differentiated errors when threat model requires. Log safe decision metadata/correlation, never token.

### 2.8 Deadlines, timeout and cancellation

Every request has a finite end-to-end budget. Allocate edge, auth, queue, model/dependency and serialization reserve. The lab wraps semaphore acquisition plus scoring in asyncio.timeout(0.250), translating expiry to 504. This gives one bounded operation but not automatic downstream cancellation/rollback.

Propagate remaining deadline to HTTP/database/model calls, choose timeouts shorter than remaining, and cap retries. Timeout cancels the local task; a thread or remote server may continue. If side effect could have committed, mark outcome unknown and reconcile by idempotency key/status.

Catch TimeoutError outside the timeout context as required by asyncio semantics. Preserve cancellation: do not broadly catch and suppress CancelledError-like control. Cleanup in finally/async context. Shield only a tiny must-complete cleanup, since shielding can outlive request budgets.

### 2.9 Backpressure and concurrency limits

Async makes it easy to create more work than dependencies can handle. Use semaphores, bounded queues, connection pool limits, per-tenant admission and server worker/concurrency limits. The lab semaphore caps four concurrent scoring sections. In production, waiting for the semaphore should consume the deadline so overloaded requests fail quickly rather than queue indefinitely.

If 200 requests arrive and model capacity is four concurrent at 100 ms each, ideal service capacity is 40/s. Without admission, the last request waits roughly five seconds even before overhead. A 250-ms contract should admit only around eight–twelve within two or three service waves depending queue policy, rejecting/shed the rest with 429/503.

Fairness matters: one tenant cannot occupy every slot. Partition quotas or weighted scheduling. Report admitted, queued, shed, timeout and useful throughput separately.

### 2.10 Async I/O and blocking work

Async-native clients expose awaitable DNS/connect/pool/read/write and cancellation. Reuse one bounded client/pool; creating HTTP client per request loses connection reuse and adds sockets. Configure connect, pool acquisition, read, write and overall deadlines.

File operations, JSON serialization of huge objects, image/PDF parsing, cryptography and feature code can block/consume CPU. Offload bounded legacy I/O with to_thread, CPU with process/native worker, or redesign as async job. Thread cancellation does not stop underlying blocking call. Avoid nested native threads across many process workers.

Measure event-loop lag, executor queue, pool wait and task count. CPU below 100% does not prove the loop is healthy: one loop thread can be saturated while a multicore pod average looks low.

### 2.11 Database sessions and transactions

Use request-scoped session/transaction only for a bounded unit of work. Do not hold it during remote model calls unless consistency requires and lock duration is accepted. Prefer transaction → outbox/operation state → commit, then async side effect. Configure statement/lock/pool timeouts.

An async endpoint needs an async database driver/session; calling synchronous ORM blocks the event loop unless intentionally moved to a bounded thread. Pool maximum multiplied by workers/pods must fit DB capacity. Cleanup must rollback failed transaction and return connection.

N+1 lazy queries hurt latency. Load required relationships or explicit queries. Tenant authorization should be in query predicate/row policy rather than fetch-then-check when possible, preventing accidental cross-tenant data.

### 2.12 Background tasks and durable work

FastAPI background tasks execute in the application process after response. They are useful for best-effort small actions whose loss on process crash is acceptable. They are not a durable queue and share process resources.

For emails with legal importance, payments, model deployment/training, audit export or long CPU work, persist job/outbox transactionally and process with a durable broker/worker. Return operation ID and status. Make worker effects idempotent, observable and replayable.

Do not pass request-scoped session/resource to background work after dependency cleanup; pass immutable IDs and reacquire resources.

### 2.13 Streaming and WebSockets

Streaming responses yield chunks without buffering everything, reducing memory/first-byte latency. They hold a worker connection and potentially dependencies until client completes. Handle disconnect/cancellation, chunk size, rate/timeout, proxy buffering and resource cleanup. Never stream from a DB transaction indefinitely.

WebSockets are stateful bidirectional connections. Authenticate at handshake and re-evaluate authorization/expiry for long sessions as needed. Bound per-connection queues/message size/rate; slow clients otherwise consume memory. Multi-process/replica broadcast requires external broker, not in-memory list. Deploy drain behavior and reconnect semantics.

Server-Sent Events are unidirectional HTTP streaming and may fit status updates with simpler client/proxy behavior. Choose from protocol needs, not novelty.

### 2.14 Middleware

Middleware is appropriate for correlation, trace context, security headers, trusted proxy handling, compression and metrics. Order affects behavior. CORS is a browser policy, not authentication or network security; configure exact allowed origins/methods/headers/credentials.

Do not trust forwarded client/proto headers from arbitrary internet peers; only from known proxy and server configuration. Request-body middleware can consume streams or buffer unbounded bodies. Enforce server/proxy content-length/body/time limits before expensive Pydantic validation.

Exception middleware should map domain failures to stable safe problem details. It must not turn every defect into 200 or leak stack/inputs. Record correlation and 5xx metric.

### 2.15 OpenAPI and compatibility

FastAPI derives OpenAPI from routes/models/dependencies. Set operation IDs, tags, descriptions, response models/status/errors and security schemes deliberately. Commit generated schema and diff in CI. Client generation amplifies breaking schema changes.

Breaking changes include removing/renaming field, narrowing accepted values unexpectedly, changing optional to required, changing Decimal/date representation, status/error semantics or authorization scope. Add fields compatibly but consumers may reject unknown fields, so contract test. Version only when necessary; prefer additive evolution and deprecation telemetry/window.

OpenAPI cannot express every semantic invariant, idempotency, ordering or conditional authorization. Document and test them separately.

### 2.16 Testing

Test request parsing, success, boundaries, unexpected fields, authn/authz, tenant isolation, error mapping, timeouts, cancellation/resource cleanup, lifespan/readiness, OpenAPI snapshots and concurrency/overload. Use deterministic fake scorer and real integration dependencies where needed.

The lab’s TestClient executes lifespan via context management. It verifies health routes excluded from schema, auth 401, exact decimal contract and float/extra/NaN/pattern 422, threshold output and slow scorer 504. The stack emitted a Starlette deprecation warning that HTTPX-backed TestClient is deprecated in favor of httpx2 in this version. Tests pass, but the warning is actionable dependency-migration evidence rather than something to suppress blindly.

For async internals, use an async test client/ASGI transport supported by pinned stack. Simulate cancellation/disconnect and race. Load test with real server/workers/network—not TestClient throughput.

### 2.17 Deployment and workers

Run behind an ASGI server with explicit host/port, proxy/trusted headers, keep-alive/body/concurrency/graceful timeouts and logging. Development reload is not production. Pin FastAPI because pre-1.0 may have breaking minor changes; FastAPI official version guidance recommends pinning a known working version.

One process generally has one event loop. Multiple workers use cores and isolate crashes but multiply memory, lifespan state, DB/HTTP pools and metrics. Kubernetes often favors one/few workers per pod plus horizontal pods for visibility/failure isolation; benchmark model memory and startup.

Graceful termination: readiness false/traffic drain, stop new requests, wait bounded in-flight/background, close clients/model/telemetry before grace. Long WebSockets/streams need drain/reconnect design.

### 2.18 Observability and SLOs

Measure logical request count/outcome/latency by route template, method, status class, region and bounded model tier. Do not label raw path, user, claim, trace or arbitrary model ID. Track event-loop lag, in-flight, semaphore wait, pool wait, executor/task count, model latency, validation rejection and shed.

Propagate W3C trace context through outgoing HTTP/message. Log safe structured correlation, principal type/tenant pseudonymous bounded context only per privacy policy, release/model digest and error category. Validation payloads may contain PHI and should not be logged.

Readiness/liveness probes are operational signals, not user SLIs. Page on user impact/burn and correctness/security invariants; use runtime metrics for diagnosis.

### 2.19 Security and regulated boundaries

Set body/upload/message size and time limits. Validate MIME by content where important, scan/unpack in sandbox, prevent path traversal/archive bombs. Docs endpoints may reveal attack surface; restrict/disable in production policy while keeping schema artifact available to authorized developers.

Use TLS at edge and backend as required, workload identity, least privilege, tenant-scoped queries, audit decisions and rate limits. Do not include secrets/PHI in URL query/path because proxies/logs retain them. Avoid returning Pydantic validation input or internal exception details.

Dependency versions matter: FastAPI 0.138.2 currently depends on Pydantic 2 and Starlette; transitive security/behavior must be locked/scanned/tested. Promote one container digest and attach SBOM/provenance.

## 3. WORKED PROBLEMS

### Problem 1 — Async handler blocks

**Statement.** An async endpoint calls a synchronous SDK taking 500 ms; 100 concurrent requests arrive on one loop.

**Solution.** The first call blocks the loop, so calls largely serialize toward 50 seconds plus overhead. Use async-native SDK or bounded thread offload; if CPU-heavy, process/native worker. Bound concurrency and propagate deadline. Benchmark actual server.

**Mistake caught:** async declaration implies concurrent internals.

### Problem 2 — Strict Decimal API

**Statement.** Strict Pydantic rejects string "1250.00", but JSON number loses exact decimal intent. Design the boundary.

**Solution.** Specify decimal string on wire. Before-validator accepts only string, parses Decimal, rejects invalid/nonfinite, then Pydantic applies digit/scale/range. Response uses string or minor unit as documented. Reject JSON float with 422. This is the lab contract.

**Mistake caught:** weakening global strictness instead of defining wire semantics.

### Problem 3 — Authentication without authorization

**Statement.** Valid JWT with claims-reader scope requests another tenant’s claim.

**Solution.** Verify JWT issuer/audience/signature/time, derive immutable principal/tenant, then authorize action and resource ownership. Query with tenant predicate/row policy. Return 404/403 per enumeration policy and audit safe decision. Scope alone is insufficient.

**Mistake caught:** authenticated means authorized.

### Problem 4 — Concurrency queue

**Statement.** Model has four slots, 100 ms service, 200 requests arrive; deadline 250 ms.

**Solution.** Capacity 40/s; in 250 ms roughly 10 services can finish ideally (four at 100, four at 200, only two of next wave before deadline in continuous idealization; batch waves mean eight safely, next four finish 300). Admit around eight with reserve, reject/shed remainder rather than queue all. Measure overhead and fairness.

**Mistake caught:** semaphore alone prevents unacceptable queue latency.

### Problem 5 — Timeout after remote write

**Statement.** Dependency times out after possibly creating a model deployment; handler returns 504 and client retries POST.

**Solution.** Use client idempotency key and durable operation record. Timeout means outcome unknown; query/reconcile remote by key before retrying effect. Same key returns same operation/conflict for different payload. Do not treat 504 as definitely failed.

**Mistake caught:** cancellation/timeout rolls back remote side effect.

### Problem 6 — Background task durability

**Statement.** Endpoint returns 202 then uses FastAPI background task for a two-hour training job.

**Solution.** Process restart/deploy loses task and shares API resources. Transactionally persist operation/outbox, publish durable queue, run dedicated worker with leases/checkpoints/idempotency, expose status/cancel and audit. Background task may only nudge publisher if loss-safe.

**Mistake caught:** post-response execution equals durable asynchronous job.

### Problem 7 — Streaming DB dependency

**Statement.** Yield dependency opens transaction; StreamingResponse lasts 20 minutes for a slow client.

**Solution.** Current FastAPI cleanup may occur after response, so transaction/connection remains held and pool exhausts. Materialize bounded result, use short cursor/session chunks with clear consistency, object storage signed download, or async producer decoupled from DB. Enforce stream timeout/disconnect.

**Mistake caught:** dependency cleanup timing is irrelevant to streaming.

### Problem 8 — Worker resource multiplication

**Statement.** Four workers each load 3-GiB model and 25 DB connections on 12-GiB pod; DB allowance 80.

**Solution.** Model pages alone 12 GiB before Python/native memory; connections total 100. Use one/fewer workers, external model server or smaller model; budget DB globally with deployment/pod headroom. Scale pods based on measured RSS/throughput. Worker count is not free CPU.

**Mistake caught:** process state is shared automatically.

### Problem 9 — Schema evolution

**Statement.** Amount changes from decimal string to JSON number and optional currency becomes required.

**Solution.** Both break existing producers/consumers/precision. Keep old representation, add new version/field additively with dual-read/write and contract telemetry; default/derive currency only if semantically safe; publish deprecation window and generated-client tests. Version route only if incompatible semantics cannot coexist.

**Mistake caught:** generated OpenAPI makes changes backward compatible.

## 4. REAL-WORLD / APPLIED CONTEXT

FastAPI 0.138.2 was the latest documented release found for this study date (June 29, 2026 release). Its official version guide advises pinning a known working version and notes pre-1.0 minor versions can break compatibility. This lesson pins exact versions only for the temporary lab; production should lock the entire tested graph.

FastAPI 0.118 changed yield-dependency cleanup to occur after streaming response, illustrating why lifecycle claims must name framework version and be tested. Current release notes also document the move to Pydantic v2-only support in late 2025 and Python 3.9 support removal in 2026.

The executable lab validates five endpoints/contracts with TestClient in about 0.30 seconds locally: health/schema, authentication, strict body, threshold and forced 300-ms scorer timing out at 250 ms. It discovered strict Decimal and NaN error-serialization edges. TestClient emitted a current Starlette warning recommending future httpx2 migration; the lab is valid today but dependency upgrade needs planned verification.

## 5. COMPARISON TABLE

| Handler/work | Event loop behavior | Appropriate use | Failure boundary |
|---|---|---|---|
| async + async I/O | yields cooperatively | network/DB clients supporting async | unlimited tasks/pools, cancellation |
| sync endpoint | FastAPI thread-pool execution | blocking library with bounded pool | pool starvation, GIL CPU |
| async + to_thread | explicit thread offload | isolated legacy blocking call | underlying call continues after cancellation |
| process/external worker | CPU parallel/isolation | feature/PDF/model/training | serialization, memory, job durability |

| Async work pattern | Durability | Response | Use |
|---|---|---|---|
| await in request | client/request lifetime | final result | bounded latency operation |
| FastAPI background task | process-best-effort | response then local task | small loss-tolerant side effect |
| durable queue + worker | broker/store-backed | 202 + operation | long/critical/retriable work |
| stream/WebSocket | connection lifetime | incremental | bounded live data/status |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **FastAPI is automatically fast.** Blocking code, validation and dependencies determine behavior.
2. **Async means CPU parallel.** It overlaps cooperative waits, not Python CPU.
3. **Sync function in async handler is harmless.** It blocks unless explicitly offloaded.
4. **More coroutines are more throughput.** Pools/dependencies saturate; enforce backpressure.
5. **Semaphore alone solves overload.** It can create a long hidden queue; admission/deadline matter.
6. **Pydantic strict Decimal accepts JSON decimal naturally.** JSON has no Decimal; define wire conversion.
7. **Annotations validate business authorization.** They only shape data.
8. **Ignore extra fields by default.** It can hide wrong client/tenant schema; choose deliberately.
9. **Validation errors are safe to log.** Inputs may contain PHI/secrets.
10. **Response model proves correct tenant object.** It filters shape, not authorization.
11. **Decode JWT equals verify.** Validate signature, issuer, audience, time, algorithm and token type.
12. **Scopes replace resource authorization.** Enforce tenant/object policy.
13. **Timeout means remote failed.** Effect may have committed; reconcile/idempotency.
14. **Cancellation undoes a thread/remote call.** It often continues.
15. **BackgroundTasks is a queue.** It is process-local best effort.
16. **Yield dependency always closes before streaming.** Version behavior can retain until response completion.
17. **Health endpoint equals SLO.** It is component probe, not user outcome.
18. **Readiness should perform deep writes every probe.** It can overload/flap dependencies.
19. **One client per request.** It wastes connection pools/sockets; initialize in lifespan.
20. **Import-time model loading is convenient.** It breaks workers/tests/lifecycle/error cleanup.
21. **Workers share memory/pools.** Process state normally multiplies.
22. **CORS authenticates API.** It is browser-origin policy.
23. **Trust forwarded headers.** Only accept from configured proxies.
24. **OpenAPI contains all semantics.** Idempotency, conditional auth and workflows need separate contracts.
25. **TestClient load result is server capacity.** Use real ASGI server/network/workers.
26. **Suppress dependency deprecation warnings.** Treat them as migration work/evidence.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- ASGI server handles protocol; Starlette ASGI; FastAPI route/dependency/OpenAPI; Pydantic validation.
- Async for async I/O; sync endpoint/thread for bounded blocking I/O; process/external worker for CPU/long work.
- Model input: forbid extras as needed, strict + explicit conversions, domain validators, safe errors.
- Response model filters shape; authorization remains separate.
- Dependency graph request-scoped; yield owns cleanup; lifespan owns process resources.
- Authn verifies principal; authz verifies action + exact tenant/resource.
- Deadline includes queue; propagate remaining time; timeout does not prove rollback.
- Bound tasks, semaphore, queue, pool, workers, body and stream.
- Background task is not durable. Critical/long work uses operation + durable queue/worker.
- Commit/diff OpenAPI and contract test semantic/error/idempotency evolution.
- Each worker repeats lifespan/model/pools. Size globally.
- Observe SLO, loop lag, in-flight, semaphore/pool wait, validation, shed and model latency.

## 8. PRACTICE SET FOR SELF-TEST

1. Design exact request/response/error/OpenAPI contract for tenant-scoped claim scoring with decimal amount and idempotency.
2. Given eight model slots at 80 ms and 400 requests burst with 300-ms deadline, derive admission/queue policy.
3. Refactor an async endpoint using synchronous SQL, requests and CPU PDF parser into bounded components.
4. Design OIDC authentication plus tenant/claim authorization and negative tests.
5. Implement transaction/outbox and 202 operation for model deployment; define timeout/retry semantics.
6. Compare request-scoped yield session for JSON, streaming download and WebSocket; define cleanup.
7. Design lifespan initialization failure/cleanup/readiness for DB, HTTP client and 4-GiB model.
8. Calculate worker/pool/model memory for three pods × two workers and DB max; define safe global caps.
9. Evolve a Pydantic/OpenAPI model across three releases without breaking generated clients.
10. Create load/failure test plan covering loop blocking, pool exhaustion, cancellation, slow clients and graceful shutdown.

## 9. CURATED RESOURCES

1. FastAPI official tutorial, *Concurrency and async/await*. Framework-specific async versus blocking execution model.
2. FastAPI official docs, *Dependencies*, *Dependencies with yield* and *Lifespan Events*. Exact dependency caching/cleanup and process resource lifecycle.
3. FastAPI official docs, *Request Body*, *Response Model*, *Handling Errors*, *Security*. Validation/serialization/error/auth mechanisms.
4. FastAPI official docs, *Deployment Concepts*, *Server Workers*, *About FastAPI versions*, and current Release Notes. Worker/resource and version-specific operational behavior.
5. Pydantic v2 documentation, *Models*, *Strict Mode*, *Validators*, *Serialization* and *Decimal*. Exact core validation and wire behavior.
6. Python 3.13 docs, *asyncio*, especially tasks, TaskGroup, timeout, cancellation, synchronization and queues. Runtime mechanics below FastAPI.
7. ASGI 3 specification and HTTP/WebSocket ASGI sub-specification. Scope/receive/send/protocol lifecycle FastAPI implements.
8. Starlette official docs, *Middleware*, *Responses*, *Background Tasks*, *Test Client*. Lower-layer behavior and limitations.
9. Uvicorn official docs, *Settings*, *Deployment*, *Server Behavior*. ASGI process, proxy, concurrency and timeout controls.
10. RFC 9110, *HTTP Semantics*, and RFC 9457, *Problem Details for HTTP APIs*. Canonical method/status and machine-readable error contracts.
11. OpenAPI Specification 3.1. Generated schema semantics/limitations and compatibility review.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Production Python:** supplies object, typing, asyncio, packaging and lifecycle foundations.
2. **API Design:** supplies HTTP/idempotency/version/error semantics.
3. **Cloud Identity:** supplies OIDC, least privilege and tenant authorization.
4. **Metrics/Logs/Traces:** supplies SLO/correlation/runtime observability.

### After

1. **ML Fundamentals:** produces evaluated score/output semantics for the endpoint.
2. **ML Lifecycle:** supplies registry/lineage/deployment operation behind APIs.
3. **Model Serving and LLMOps:** extends batching/GPU/cache/streaming/guardrails.
4. **Regulated Design:** governs patient/financial validation, audit and authorization.

---ANSWER KEY BELOW---

1. Request includes tenant from verified identity, claim ID patterned, amount exact decimal string with finite/range/scale, model tier closed enum and idempotency key header for side-effecting record. Response includes immutable model digest/version, exact score representation, decision/review and correlation—not explanations/PHI. Errors use stable problem code/status; same key+same canonical payload returns same result, different payload 409. Auth query scopes tenant.
2. Eight slots × 12.5/s =100/s. In 300 ms, ideal 30 completions; batch waves finish 8 at 80, 16 at 160, 24 at 240, next at 320. Admit at most 24 minus overhead reserve, perhaps 16–20; per-tenant fair queue and immediate 429/503 for remainder. Semaphore wait consumes deadline; measure real latency.
3. Use async DB driver/session for bounded transaction, reusable async HTTP client with deadlines and semaphore, and move CPU parser to bounded process/external sandbox job. If libraries cannot change, sync endpoint/bounded thread for blocking I/O but not CPU. Split long PDF into 202 operation. Propagate cancellation/idempotency and cap all pools/queues.
4. Verify signature/issuer/audience/algorithm/exp/nbf/type using pinned trusted config/JWKS rotation; derive immutable subject/tenant/scopes. Dependency returns auth context; policy checks score action and claim tenant, enforced in database query. Tests cover missing/expired/wrong issuer/audience/signature, wrong tenant/resource, insufficient scope, enumeration response and audit/no token leakage.
5. Transaction inserts operation keyed by tenant/idempotency plus outbox, commits, returns 202/operation URL. Publisher/worker deliver idempotently and state transition uses expected version. Client timeout retries same key and receives same operation; different canonical payload conflicts. Unknown remote effects reconcile by command ID; cancel is an explicit request/outcome.
6. JSON request session may close after endpoint/response serialization and rollback/commit. Streaming that reads DB retains yielded resource in current versions and risks pool exhaustion; materialize/object-store or short chunk/cursor design. WebSocket lifespan may be hours; never hold one transaction/session—acquire per bounded message/unit and release. Test framework-version cleanup/disconnect.
7. Lifespan creates resources sequentially with AsyncExitStack; validate config, DB/client connectivity, model digest/schema/warmup, semaphore, then set ready and yield. On any failure, close already-created resources and never ready. Shutdown toggles readiness/drains then closes in reverse with time bounds. Each worker repeats, so memory/pools counted.
8. Six worker processes total. If each model 3 GiB plus 0.4 GiB base, raw 20.4 GiB across pods, about 6.8 GiB/pod before headroom. If each pool default 20, total 120 connections. With DB usable 90, cap perhaps 10–12 per worker (60–72) leaving rollout/admin/other headroom. Verify pod memory limit/node and avoid rollout doubling beyond DB/memory.
9. Release 1 adds optional new field and output, server dual-reads old. Release 2 clients migrate with telemetry; server dual-writes/returns compatible representation and warns out-of-band. Release 3 removes only after published window and observed zero old clients, possibly under versioned route if amount representation/required field is incompatible. Diff OpenAPI and test old/new generated clients at every stage.
10. Run real pinned Uvicorn/container. Cases: inject blocking sleep and measure loop lag/unrelated latency; exhaust semaphore/HTTP/DB pools and verify bounded queue/shedding; cancel/disconnect during scorer/transaction and verify cleanup/no duplicate effects; slow stream/WebSocket queue bounds; SIGTERM during mixed requests verifies readiness drain/grace/forced cutoff. Report environment, concurrency, distribution, percentiles, errors/shed, resource/queue and artifacts.
