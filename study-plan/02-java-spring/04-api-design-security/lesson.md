# API Design and Security — Complete Study Resource

**Parent:** `02-java-spring`  
**Child:** `04-api-design-security`  
**Standards baseline:** RFC 9110, RFC 9457, OAuth/OIDC specifications, OWASP API Security Top 10 2023

## 1. FOUNDATIONS

### An API is a long-lived contract

An application programming interface lets independently deployed clients and servers coordinate. The difficult part is not mapping JSON to a Java object; it is preserving semantics under retries, partial failures, concurrent updates, unauthorized callers and evolving versions. A method signature can change with one compilation. A public API can have thousands of clients, cached responses and intermediaries that cannot upgrade together.

HTTP is an application protocol with standardized **methods**, **status codes**, representation metadata, caching and conditional requests. REST is an architectural style emphasizing resources, representations, stateless interactions, uniform interface and cacheability; not every useful HTTP API is perfectly RESTful. Use HTTP semantics rather than treating every endpoint as remote procedure `POST /doThing`.

A **resource** is a conceptual entity identified by URI; a **representation** is its current serialized form. `/payments/123` identifies a payment; JSON is one representation. A **safe** method is intended to be read-only from the client’s requested semantics, though logging/accounting may occur. An **idempotent** method has the same intended effect after one or several identical requests. RFC 9110 defines GET/HEAD/OPTIONS/TRACE as safe and PUT/DELETE plus safe methods as idempotent; POST and PATCH are not inherently idempotent.

### Security model

**Authentication** establishes identity. **Authorization** decides whether that identity may perform an action on a particular resource. **OAuth 2.0** is an authorization framework; **OpenID Connect (OIDC)** adds identity/authentication claims on OAuth. A **JWT** is a token format, not automatically an authentication system. Signature validation without issuer, audience, algorithm, time and authorization checks is insufficient.

**Least privilege** grants only necessary actions/resources. **Defense in depth** layers controls. **Tenant isolation** prevents data/action crossing tenant boundaries. **BOLA** (broken object-level authorization) occurs when a caller changes an ID and accesses another object because the API checks authentication but not ownership/tenant/policy. OWASP ranks broken object authorization prominently because opaque IDs are not access control.

### What breaks without contracts

A timed-out POST is retried and charges twice. Offset pagination duplicates/misses rows during inserts. A controller trusts `tenantId` from JSON and leaks another customer’s record. Error bodies expose stack traces and PHI. An API fetches arbitrary callback URLs and reaches cloud metadata through SSRF. An unbounded `pageSize=10000000` exhausts heap/database. Contract design must include failure, security and limits from the start.

## 2. CORE MECHANICS

### 2.1 Resource and URI design

Use stable nouns: `/v1/payments/{paymentId}`, subresources `/payments/{id}/refunds`. Avoid leaking database topology or verbs when HTTP method expresses action. Domain commands that are not CRUD can be modeled as resources (`POST /payment-cancellations`) or explicit action endpoints when clearer; consistency matters more than dogma.

Do not encode authorization assumptions in guess-resistant IDs. UUIDs reduce enumeration but a caller must still be authorized for the located object. Normalize/validate path segments and let framework route decoding prevent traversal/confusion.

### 2.2 Methods and status codes

Typical semantics:

- `GET /payments/123`: 200 with representation; 404 if not found/hidden.
- `POST /payments`: 201 Created with `Location`; 202 Accepted if asynchronous and status resource available.
- `PUT /profiles/123`: replace/create known URI, idempotent.
- `PATCH`: partial change; define media type/operation semantics and concurrency.
- `DELETE`: idempotent intended effect; repeated call may return 204 or 404 consistently.

Useful statuses: 400 malformed syntax/general invalid request; 401 missing/invalid authentication (with challenge as applicable); 403 authenticated but forbidden; 404 absent or intentionally concealed; 409 state/version/idempotency conflict; 412 conditional precondition failed; 415 unsupported media type; 422 semantically invalid content; 429 throttled; 500 unexpected server fault; 502/503/504 upstream/availability/gateway timing distinctions.

Do not return 200 with `{success:false}` for ordinary HTTP failures; intermediaries/metrics/clients misinterpret it.

### 2.3 Validation

Validate at boundaries: maximum body bytes before parsing, content type, schema/types, required fields, length/range/format, cross-field domain rules. Syntactic validity (`amount` integer) differs from semantic (`amount>0`, supported currency) and business state (`account active`). Database constraints remain final concurrent defense.

Reject unknown fields for strict safety where silent typos are dangerous, or tolerate for forward compatibility—document choice. Normalize only with domain rules; never silently truncate monetary amount/name.

### 2.4 Problem Details

RFC 9457 defines `application/problem+json` with `type`, `title`, `status`, `detail`, `instance` and extensions. `type` identifies problem class and should have stable documented semantics; `instance` identifies this occurrence. Example:

```json
{"type":"https://api.example.com/problems/idempotency-conflict","title":"Idempotency key conflicts with original request","status":409,"detail":"The key was previously used with a different request payload.","instance":"/problems/01J...","correlationId":"6f7..."}
```

Do not put stack traces, SQL, secrets, internal hostnames or raw PHI into detail. Validation extensions can list safe field pointers. Log internal exception with correlation ID under access controls.

### 2.5 Idempotency

Network timeout means unknown outcome. For non-idempotent POST, accept client `Idempotency-Key` within tenant/principal scope. Atomically insert `(scope,key)` with canonical request hash, state, response/status/resource and expiry. Same key/same hash returns original or in-progress semantics; same key/different hash returns409. Concurrent first requests need unique constraint/conditional write, not in-memory check.

Canonical hashing must be stable: preferably hash normalized domain command or exact accepted bytes with documented behavior, not unordered map serialization. Retention must cover client retry horizon; expiry permits eventual reuse and must be documented. Idempotency prevents duplicate server effect for that scope, not arbitrary external side effects unless they receive same key/protocol.

### 2.6 Optimistic concurrency

Lost updates occur when two clients read version7 then both update. Return `ETag`; require `If-Match: "v7"`. Update conditionally; stale request returns412. Database implementation can use version column:

```sql
UPDATE account SET email=?, version=version+1 WHERE id=? AND version=7;
```

Affected0 means conflict/not found. PATCH without precondition can overwrite concurrent fields depending semantics.

### 2.7 Pagination

Offset `LIMIT 50 OFFSET 1000000` may scan/discard many rows and shifts under inserts/deletes. Keyset/cursor pagination uses deterministic sort, e.g. `(created_at DESC,id DESC)` and next predicate `(created_at,id)<(cursorCreated,cursorId)`. Composite tie-breaker is mandatory.

Cursor should be opaque, validated/signed if tampering matters, bound to filters/tenant and expire/version as needed. Base64 alone is encoding, not integrity. Page size maximum protects resources. Returning total count can be expensive/stale; make optional/estimated where appropriate.

### 2.8 Versioning and compatibility

Prefer additive changes: optional response fields, tolerant clients, new enum handling strategy. Removing/renaming/changing meaning is breaking. Adding required request field breaks old clients. New enum values can break exhaustive client switches. Version via URI/header/media type according to organization; maintain deprecation/sunset communication and telemetry of client use.

OpenAPI documents syntax but cannot fully encode business authorization, idempotency or consistency. Contract tests and consumer-driven tests supplement.

### 2.9 Caching and conditional requests

HTTP caching uses `Cache-Control`, validators `ETag`/`Last-Modified`, and `Vary`. Personalized/sensitive responses generally need `private` or `no-store` as policy demands. Missing `Vary: Authorization`/tenant dimension in shared caches can leak data; many systems avoid caching authenticated responses at shared layer.

GET side effects violate retry/cache/prefetch expectations. Never put secrets in URLs: they leak to logs/history/referrers.

### 2.10 Authentication/token validation

For bearer JWT access token validate cryptographic signature using trusted keys, allowed algorithm (never accept token-selected `none`), issuer, audience, expiry/not-before with bounded clock skew, token type/use, and required scopes/claims. Key rotation uses JWKS caching with safe refresh; unknown `kid` must not trigger unbounded attacker-controlled fetches.

Do not use ID token as API access token unless architecture explicitly specifies it. Do not log tokens. Prefer short-lived tokens; revocation/introspection/session strategy depends threat model.

### 2.11 Authorization layers

Check function-level permission **and** object/tenant relation. Repository queries can include tenant predicate from authenticated context: `WHERE tenant_id=:trustedTenant AND id=:id`. Never trust tenant from body/header unless verified against identity. Admin overrides must be explicit/audited.

Field-level authorization prevents returning sensitive fields. Mass assignment occurs when request binds arbitrary entity properties such as `role=ADMIN`; use request DTO allowlists, not persistence entities.

### 2.12 CSRF, CORS and browser context

CSRF exploits credentials automatically attached by browser (notably cookies). Use same-site cookies, CSRF tokens and method/content protections. A bearer token explicitly added by JS changes CSRF profile but increases XSS/token storage concerns.

CORS is browser read/access policy, not authentication or server-to-server firewall. `Access-Control-Allow-Origin:*` with credentials is invalid/insecure configuration. Allow exact trusted origins/methods/headers and understand preflight caching.

### 2.13 SSRF and outbound calls

Webhook/image-import URL features can let attackers request `169.254.169.254`, localhost, private networks or internal control planes. Prefer allowlisted destinations/schemes, DNS/IP resolution validation at connect time, block private/link-local/loopback ranges, prevent redirect bypass, restrict egress at network layer, use dedicated fetch service, cap bytes/time and do not return raw internal response.

DNS rebinding means validate every resolved/connected address, not string once.

### 2.14 Resource consumption and abuse

Bound request bytes, JSON depth, array length, decompressed size, page size, query complexity, concurrency, timeouts and response bytes. Rate limit by authenticated subject/tenant/business flow plus IP as supplemental. Return429 with useful retry policy where appropriate. Expensive endpoints need cost-aware quotas; bots can distribute across IPs.

Sensitive business flows (signup, reservation, claims, password reset) need anti-automation and fraud controls beyond generic RPS.

### 2.15 Logging and observability

Record method, route template (not raw high-cardinality path), status, latency, principal/tenant pseudonymous IDs where permitted, correlation/trace ID and decision reason. Never log passwords, bearer tokens, card data or raw PHI. Audit logs need tamper resistance, retention and access control; application logs are not automatically compliant audit trails.

## 3. WORKED PROBLEMS

### Problem 1 — Create payment

**Statement.** Design synchronous create response.

**Solution.** `POST /v1/payments` with validated DTO and idempotency key. On new success return201, `Location:/v1/payments/p_123`, representation. Same key/hash returns original201/body; conflicting hash409 Problem Detail. Atomic DB key prevents races.

**Mistake caught.** Retrying POST creates a second payment.

### Problem 2 — Async model deployment

**Statement.** Deployment takes20 minutes.

**Solution.** POST deployment request returns202 and `Location` to operation `/operations/op1`; operation exposes pending/running/succeeded/failed, progress and result link. Idempotency covers submission. Avoid holding HTTP open20 minutes.

**Mistake caught.** Returning201 before resource exists or timing out uncertain work.

### Problem 3 — Object authorization

**Statement.** User changes `/payments/p1` to `/payments/p2` and sees another tenant.

**Solution.** Resolve trusted tenant/subject from authentication, query by `(tenant,id)`, enforce owner/admin permission, optionally return404 to conceal. Random IDs do not replace check. Test horizontal/vertical access.

**Mistake caught.** Authentication-only security.

### Problem 4 — Lost update

**Statement.** Two admins edit model configuration version12.

**Solution.** GET returns `ETag:"12"`; clients PUT/PATCH with If-Match. First conditional update increments13; second version12 gets412 and refetches/merges. Do not silently last-write-wins unless intentional.

**Mistake caught.** Assuming transaction isolates human edit cycles.

### Problem 5 — Pagination under inserts

**Statement.** New payments arrive while client pages by offset.

**Solution.** Sort created_at desc,id desc and use opaque cursor of last tuple/filter snapshot. Next query uses strict `<`. This avoids duplicate/skip from rows inserted before offset, though updates to sort keys/snapshot semantics require policy.

**Mistake caught.** Timestamp alone duplicates when ties.

### Problem 6 — JWT validation

**Statement.** Token signature valid but `aud` is another API.

**Solution.** Reject. Signature only proves issuer/key signed claims; audience restricts intended recipient. Also verify issuer, allowed alg, time, token type/scopes.

**Mistake caught.** Signature-valid means authorized.

### Problem 7 — Webhook SSRF

**Statement.** User configures callback `http://169.254.169.254/...`.

**Solution.** Reject non-allowlisted scheme/destination; resolve and block link-local/private/loopback, validate redirects/re-resolution, enforce egress firewall/proxy, cap response/time. Prefer destination registration/verification.

**Mistake caught.** Regex only on hostname before DNS/redirect.

### Problem 8 — Error disclosure

**Statement.** SQL exception returned with query and patient ID.

**Solution.** Return generic500 RFC9457 instance/correlation; internal secured log contains sanitized diagnostic, not unnecessary PHI. Alert and map known conflicts to safe4xx. Review retention/access.

**Mistake caught.** Helpful client errors expose internals/sensitive data.

### Problem 9 — Resource exhaustion

**Statement.** `pageSize=10,000,000` and deeply nested JSON.

**Solution.** Gateway/server body/decompression/depth limits; schema max items/page≤e.g.200 based on measurement; DB statement/deadline; concurrency/rate quota; return400/413/422/429 appropriately. Do not allocate before validation.

**Mistake caught.** Relying only on authentication to prevent abuse.

## 4. REAL-WORLD / APPLIED CONTEXT

### Standards

RFC 9110 defines method/status/cache semantics and idempotence. RFC 9457, which obsoletes RFC7807, standardizes machine-readable problems. OWASP API Security Top10 2023 emphasizes authorization, resource consumption, sensitive flows and SSRF. These are contracts/threat categories, not framework settings.

### Payment idempotency

Payment providers commonly expose idempotency keys because retries across unknown outcomes are unavoidable. A robust server persists original result, scopes keys and rejects body mismatch. The accompanying Java lab demonstrates same key/same command replay versus409 conflict; real implementation requires durable unique storage.

### Cursor performance

For PostgreSQL query `ORDER BY created_at DESC,id DESC LIMIT 50`, matching index `(tenant_id,created_at DESC,id DESC)` supports keyset traversal. `OFFSET 1,000,000` must locate/discard a million candidates; exact timing depends plan/cache. Verify with `EXPLAIN (ANALYZE,BUFFERS)`.

## 5. COMPARISON TABLE

| Concern | Approach | Strength | Boundary |
|---|---|---|---|
| pagination | offset | random page/simple | shifts; deep scan |
| pagination | cursor/keyset | stable efficient next page | no easy arbitrary page; cursor policy |
| update | last-write-wins | simple | silent lost update |
| update | ETag/If-Match | explicit conflict | client merge/retry |
| auth | opaque ID | reduces enumeration | no authorization |
| auth | object policy + tenant query | enforces access | must cover every path/field |
| POST retry | no idempotency | minimal state | duplicate effects |
| POST retry | durable idempotency | safe repeat within scope/window | storage/canonical hash/state |
| error | custom ad hoc | quick | inconsistent clients |
| error | RFC9457 | standard machine shape | still must define safe domain types |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **POST is automatically idempotent.** It is not; design key/state.
2. **UUID secures object.** Authorization still required.
3. **401 and403 interchangeable.** Authentication versus permission semantics differ.
4. **200 with error body.** Breaks HTTP tooling/metrics.
5. **Base64 cursor is secure.** It is reversible encoding; sign/encrypt if needed.
6. **JWT signature enough.** Validate issuer/audience/time/type/scopes.
7. **CORS protects API.** It constrains browsers, not arbitrary clients.
8. **CSRF irrelevant to APIs.** Cookie-authenticated browser APIs remain exposed.
9. **Validation only annotations.** Body/decompression/depth/business/DB constraints needed.
10. **Rate limit only IP.** Distributed bots/shared NAT and tenant fairness require richer keys.
11. **Allow arbitrary webhook URL.** SSRF/internal metadata risk.
12. **OpenAPI proves compatibility/security.** Semantics/policies require tests/review.
13. **Log full request for debugging.** Tokens/PHI/secrets leak.
14. **Retry every 5xx.** Operation/idempotency/deadline determine safety.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the complete resource.

- API contract includes retry, concurrency, compatibility, security and limits.
- GET safe; PUT/DELETE idempotent semantics; POST/PATCH not inherently.
- 201 create,202 async,401 unauthenticated,403 forbidden,409 state conflict,412 precondition,422 semantic,429 throttle.
- RFC9457 errors; no internals/PHI.
- Idempotency: scoped key + canonical request hash + atomic durable result.
- ETag/If-Match prevents lost update.
- Cursor uses deterministic composite sort/tie-breaker; Base64 not integrity.
- Authenticate then function/object/tenant/field authorize.
- JWT: alg/signature/iss/aud/exp/nbf/type/scope.
- Bound bytes/depth/page/query/time/concurrency.
- SSRF: allowlist, resolve/connect validation, redirect and egress control.
- Logs/audits redact and restrict.

## 8. PRACTICE SET FOR SELF-TEST

1. Choose statuses for malformed JSON, unsupported currency, insufficient balance, unauthenticated and throttled.
2. Design idempotency schema for tenant-scoped claim submission.
3. Explain DELETE retry semantics when first returns204 and second404.
4. Build keyset predicate for ascending `(priority,id)` after `(7,900)`.
5. Design ETag update for model endpoint autoscale config.
6. List JWT checks for an Azure/OIDC-issued access token consumed by your API.
7. Threat-model URL import endpoint with redirects and DNS rebinding.
8. Design object and field authorization for doctor viewing patient record.
9. Identify breaking versus additive changes: optional response field, required request field, new enum, removed field.
10. Design safe 503 response/retry guidance for idempotent GET versus payment POST.

## 9. CURATED RESOURCES

1. **RFC 9110, HTTP Semantics.** Authoritative methods, status, idempotence, conditional requests and caching.
2. **RFC 9457, Problem Details for HTTP APIs.** Standard error shape/type/instance/extensions; replaces RFC7807.
3. **RFC 6749 OAuth2, RFC6750 Bearer Token Usage, RFC7519 JWT.** Token framework/transport/format foundations.
4. **OpenID Connect Core 1.0.** Authentication/ID-token and issuer/audience/nonce semantics.
5. **OAuth 2.0 Security Best Current Practice (RFC 9700).** Modern security corrections beyond original OAuth2 patterns.
6. **OWASP API Security Top 10 2023.** Concrete authorization, consumption, sensitive-flow and SSRF threat cases.
7. **OWASP ASVS 5.x, authentication/access-control/API sections.** Testable security requirements beyond risk list.
8. **OpenAPI Specification 3.1.** Exact contract syntax and JSON Schema integration.
9. **Spring Security Reference, servlet OAuth2 resource server/method security/CSRF/CORS.** Framework implementation with correct filter/context model.
10. **PostgreSQL documentation, indexes and EXPLAIN.** Evidence-driven keyset/conditional-update implementation.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Spring Core/Transactions.** Controller-to-service boundary, proxies and constraints implement API effects.
2. **Concurrency/Failure Basics.** Retries/timeouts/concurrent updates motivate idempotency and conditions.

### After

1. **Testing and Resilience.** Contract/security/error/retry behavior needs automated and failure tests.
2. **PostgreSQL Modeling/Indexes.** Durable idempotency, tenants, ETags and keyset require schema/index design.
3. **Distributed Failure Semantics.** API timeout becomes unknown remote outcome.
4. **Regulated Security/Privacy.** Healthcare/fintech add audit, retention, consent and data classification.

---ANSWER KEY BELOW---

1. Malformed JSON400; unsupported well-formed currency422 (or documented400); insufficient balance409 or domain403 depending semantics—RFC9457 defines type; unauthenticated401; throttled429 with policy/Retry-After where appropriate.
2. Unique `(tenant_id,key)`, request_hash, status/in_progress owner/version, resource/result/response status/body, created/expiry timestamps. Atomic insert; same hash replay, different409; retention covers retries.
3. DELETE’s intended final state remains absent, so effect idempotent even if response differs. Document204 repeated or404; clients should treat both according contract.
4. `WHERE (priority,id)>(7,900) ORDER BY priority ASC,id ASC LIMIT :n`, with matching tenant/filter/index and cursor bound to them.
5. GET returns version ETag. PUT/PATCH sends If-Match. DB conditional version update increments; zero rows→412. Return new ETag.
6. TLS; allowed alg/signature using trusted JWKS; issuer; audience; exp/nbf/iat policy/skew; token type/use; scopes/roles; tenant claim provenance; key rotation/cache; reject unknown/malformed and never log token.
7. Schemes, credentials/ports, allowlist, DNS resolving private/link-local/loopback, rebinding between validation/connect, redirects to forbidden host, response size/decompression/time, internal response disclosure, egress proxy/firewall and audit/rate.
8. Authenticated clinician; organization/tenant membership; treatment relationship/purpose/consent/break-glass policy; patient object check; field masking for specially sensitive data; audit decision/access; server-derived context, not request tenant.
9. Optional response field usually additive if clients tolerate unknown; required request field breaking; new enum can break exhaustive clients and needs compatibility plan; removed response field breaking.
10. GET can retry with bounded exponential jitter under original deadline/Retry-After. Payment POST only retry with same idempotency key and status reconciliation; 503 must not claim no effect unless server knows request not accepted.
