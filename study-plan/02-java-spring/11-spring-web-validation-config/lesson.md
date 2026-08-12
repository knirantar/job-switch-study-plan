# Spring Web, Validation and Configuration — Building a Correct Boot HTTP Boundary

**Parent:** 02 — Java and Spring  
**Level:** prerequisite 6  
**Study time:** 3–4 hours plus boundary lab  
**Lab:** `WebBoundaryLab.java`

## 1. FOUNDATIONS

An HTTP API boundary translates bytes, headers, paths and authenticated context into domain commands, then translates outcomes into status, headers and representation. Spring MVC implements the Servlet stack; Spring WebFlux implements reactive nonblocking stack. Spring Boot configures one based on dependencies. This lesson starts with MVC because it matches most Spring Boot enterprise services and your Java/Spring background.

A request does not call a controller “directly.” Embedded servlet server accepts connection, filters run, `DispatcherServlet` dispatches through handler mappings/adapters, argument resolvers create parameters, conversion/deserialization/validation occur, controller/service executes, return-value handlers and message converters serialize, exception resolvers map failures, filters complete. Security uses a filter chain before MVC authorization/interceptors.

**Serialization** maps object to bytes (usually JSON); **deserialization** maps bytes to object. **Binding** maps path/query/form/config fields. **Validation** checks syntactic/structural constraints. **Business validation** checks domain/current state and usually belongs in service/domain. A DTO is a boundary contract, not a JPA entity.

Skipping these basics causes common interview and production errors: accepting entities in controllers, confusing `@RequestParam`/`@PathVariable`/`@RequestBody`, missing `@Valid`, returning 200 for everything, using GET for mutation, leaking stack traces, validation only client-side, profile/config uncertainty, CORS confused with auth, and controller unit tests that never exercise JSON.

## 2. CORE MECHANICS

### 2.1 HTTP message anatomy

Request: method, target/path/query, protocol, headers, optional body. Response: status, headers, optional body. HTTP is stateless at protocol semantics; cookies/tokens/session add application state. Content negotiation uses `Content-Type` for sent representation and `Accept` for desired response.

JSON is text with objects/arrays/string/number/boolean/null. Java long decimal money representation must have explicit schema; JSON number may lose precision in JavaScript, so large IDs should be strings. Dates use ISO-8601 with offset/instant contract.

### 2.2 DispatcherServlet pipeline

`DispatcherServlet` is front controller. HandlerMapping finds controller method from route conditions; HandlerAdapter invokes; argument resolvers handle annotated parameters; HttpMessageConverter handles body; validation may run; return-value handler creates response; HandlerExceptionResolver maps exceptions. Interceptors wrap handler execution but are not replacement for servlet security/filter for all dispatch types.

Knowing layers diagnoses: 404 no handler; 405 path exists wrong method; 415 request Content-Type unsupported; 406 cannot produce Accept; 400 binding/deserialization; validation; 500 unhandled.

### 2.3 Controllers and route mapping

`@RestController` combines Controller + ResponseBody. `@RequestMapping("/claims")` class prefix; `@GetMapping`, `@PostMapping`, etc. Method mapping can constrain consumes/produces/headers/params. Avoid ambiguous overlapping mappings.

Use nouns/resources and HTTP semantics. Controller should orchestrate boundary: parse/validate/auth context → service command → response. Keep transactions/business rules out. Return DTO/ResponseEntity as needed, not persistence entity.

### 2.4 Argument sources

`@PathVariable` identifies resource (`/claims/{id}`); `@RequestParam` filter/page (`?status=OPEN`); `@RequestHeader`; `@CookieValue`; `@RequestBody` JSON; `Principal`/authentication from security; `@ModelAttribute` binds form/query object. Be explicit when parameter-name compiler metadata may differ.

Do not take tenant/user authorization from body. Path variables require type conversion; invalid UUID maps 400. Missing required parameter 400. Optional query can use Optional sparingly/defaultValue/null contract.

### 2.5 Request and response DTOs

Use records/classes tailored per operation. Create DTO excludes server-generated ID/status; update DTO models allowed fields; response provides stable contract. Separate input/output to prevent mass assignment and accidental sensitive serialization. Jackson supports records/constructors/accessors depending configuration.

Do not expose entity lazy relations, bidirectional cycles, internal columns or password hashes. Mapping can be manual/MapStruct. Version DTO fields deliberately and test JSON snapshots/contracts.

### 2.6 Jackson essentials

ObjectMapper modules handle Java time, naming, unknown fields, enums, polymorphism. Boot configures defaults/version. Decide unknown-property policy: reject catches client mistakes/security mass assignment; tolerant readers support evolution. Never enable unsafe polymorphic default typing for untrusted JSON.

`@JsonProperty`, `@JsonIgnore`, `@JsonFormat` affect contract; excessive entity annotations couple persistence/API. Enum unknown value needs evolution strategy. BigDecimal scale serialization and null/absent differences matter. Validate maximum body/nesting/string size to prevent resource exhaustion.

### 2.7 Bean Validation

Jakarta Validation annotations: `@NotNull`, `@NotBlank`, `@Size`, `@Min/@Max`, `@Positive`, `@Pattern`, `@Email`, `@Past`, `@Valid` nested. Put on DTO component/field with correct target. `@Valid @RequestBody` triggers object graph validation; missing `@Valid` often means annotations ignored at MVC boundary.

`@Validated` enables groups/method validation integration. Groups can become complex; operation-specific DTOs often clearer. Custom constraint consists annotation + validator; validators should be thread-safe and not perform slow DB calls. Class-level validator checks cross-field structural rule.

Validation messages are user-safe/localizable; error response should expose stable field/code, not depend solely on text. The lab aggregates three violations rather than fail first.

### 2.8 Structural versus business validation

DTO: amount positive, currency format, required ID. Service/domain: claim exists, belongs to tenant, state permits approve, duplicate key, policy threshold. Database: unique/check/foreign-key final invariant under concurrency. Repeat critical validation at authoritative layer; controller-only checks race/bypass via batch/message.

Do not query repository from annotation validator for uniqueness—race still exists and hidden I/O. Check for friendly response then rely on unique constraint/idempotency handling.

### 2.9 Response status and headers

Typical: 200 successful retrieval/update with body; 201 create plus `Location`; 202 accepted async not completed; 204 successful no body; 400 malformed/validation; 401 unauthenticated; 403 authenticated unauthorized; 404 absent (sometimes conceal); 409 state/conflict/duplicate semantic; 412 precondition failed; 415/406 media; 422 sometimes semantically invalid; 429 rate; 500 unexpected; 503 unavailable; 504 gateway timeout.

Do not cargo-cult. Document semantics. POST is not inherently non-idempotent; idempotency key can make create safe. PUT is defined idempotent for full replacement semantics; PATCH partial and format-specific.

### 2.10 Central exception handling

`@RestControllerAdvice` with `@ExceptionHandler` maps typed failures. Spring Framework supports RFC 9457 Problem Details (`ProblemDetail`, `ErrorResponse`). Include stable type/title/status/detail/instance, correlation and validation extensions. Do not expose SQL, class names, stack, token or PHI.

Order mappings specific before fallback. Log unexpected once with trace; expected validation/conflict often no error stack. Preserve cause internally. Mapping domain exception to status belongs boundary, not service depending on HTTP.

### 2.11 Filters versus interceptors versus advice

Filter sees raw servlet request/response around whole chain, appropriate correlation, security chain, CORS, body limits (careful wrapping). HandlerInterceptor knows selected MVC handler and pre/post/completion. ControllerAdvice handles MVC exceptions/binding. A filter exception before DispatcherServlet may not reach controller advice; map at filter or delegate to resolver.

Security annotations/interceptors are defense-in-depth; primary authentication/authorization filter/method security. ThreadLocal request context must be cleared; async dispatch changes thread.

### 2.12 CORS and CSRF basics

CORS is browser policy controlling cross-origin script reads/requests; it does not stop curl/server attackers and is not authorization. Configure exact origins/methods/headers/credentials; wildcard with credentials invalid/unsafe. Preflight OPTIONS needs security handling.

CSRF exploits browser automatically attached credentials (cookies). Stateless bearer tokens not automatically attached in same way, but storage/architecture matters. Spring Security CSRF defaults suit browser sessions; disabling requires threat reasoning, not “REST.” XSS can steal tokens/act as user; output encoding/CSP/frontend controls matter.

### 2.13 Multipart/file handling

Validate size, type by content not name, filename/path traversal, malware policy, archive bombs. Stream to controlled storage, not whole memory. Generate server filename; quarantine/scan; authorization. Limits at proxy/server/Boot/controller. Never trust `Content-Type` alone.

### 2.14 Configuration for web boundaries

Typed properties for pagination max, body/file sizes, allowed origins, timeouts. Validate at startup. Environment-specific origins/secrets external. Never put wildcard dev CORS in production profile accidentally. Server forward headers only from trusted proxies or attackers spoof scheme/IP.

Configure graceful shutdown, compression only after security/performance review (secrets + compression side channels), request encoding UTF-8, error inclusion disabled in prod.

### 2.15 MVC testing

Plain controller unit only Java decisions. `@WebMvcTest` + MockMvc exercises mappings, converters, validation, advice, selected security. Test request JSON/status/headers/body and malformed JSON/content type/unknown fields/authorization. `@SpringBootTest(webEnvironment=RANDOM_PORT)` exercises server/network stack using client.

MockMvc does not prove proxy/load balancer/TLS. Contract/OpenAPI tests and end-to-end complement. Avoid assertions only `isOk`; verify schema/business fields.

### 2.16 OpenAPI and documentation

OpenAPI describes paths, operations, schemas, security, errors. Generate from code/annotations or contract-first; both can drift without tests. Examples must be realistic but non-sensitive. Document idempotency, pagination, time/timezone, money and errors—not only fields.

Do not expose Swagger UI publicly without auth/environment decision. OpenAPI is contract, not authorization implementation.

### 2.17 Lab

```bash
javac WebBoundaryLab.java && java WebBoundaryLab
```

It tests aggregated structural violations, safe problem representation and query-limit exact boundary without Spring dependencies.

### 2.18 Interview request walkthrough

Practice narrating one POST end to end: server accepts bytes; security/CORS/correlation filters run; DispatcherServlet finds the `@PostMapping`; converter selects JSON and Jackson constructs request DTO; Bean Validation rejects structural errors; controller obtains trusted principal and calls service; service authorizes tenant and applies transaction/domain rules; repository persists; controller returns 201 with Location; converter serializes response; tracing/logging closes. On any failure, name which layer owns translation and whether the transaction started. This walkthrough exposes missing assumptions far better than reciting annotations.

## 3. WORKED PROBLEMS

### Problem 1 — Annotation source (easy)

`GET /claims/C1?detail=true`: bind values. **Solution:** `@PathVariable String id`, `@RequestParam(defaultValue="false") boolean detail`. **Mistake:** RequestBody on GET.

### Problem 2 — Missing Valid (easy)

DTO NotBlank ignored. **Solution:** add validation starter and `@Valid @RequestBody`; verify constraint placement and MVC test. **Mistake:** manually call validator in controller.

### Problem 3 — Create response (medium)

Claim created synchronously ID C1. **Solution:** 201, Location `/claims/C1`, response DTO. **Mistake:** 200 and entity.

### Problem 4 — Media errors (medium)

JSON endpoint receives text/plain. **Solution:** 415 Unsupported Media Type; Accept impossible response gives 406. **Mistake:** both 400.

### Problem 5 — Uniqueness (medium)

Controller `exists` then save races. **Solution:** DB unique `(tenant,externalId)`, catch/translate conflict; optional precheck only UX. **Mistake:** validation annotation with DB query.

### Problem 6 — Entity exposure (medium)

Returning User entity exposes passwordHash/lazy roles. **Solution:** response DTO allowlist; map explicitly; serialization tests. **Mistake:** JsonIgnore one field and assume future fields safe.

### Problem 7 — Filter failure (hard)

Auth filter throws before controller; advice not invoked. **Solution:** security authentication entry point/access denied handler or catch/delegate configured resolver at filter; consistent Problem Details. **Mistake:** assume ControllerAdvice catches all JVM exceptions.

### Problem 8 — CORS (hard)

API CORS allows only company web, attacker uses curl. **Solution:** curl unaffected; authentication/object authorization required. CORS protects browsers from cross-origin script, not API. **Mistake:** CORS as firewall.

### Problem 9 — Large body (hard)

100MB JSON OOM before validation. **Solution:** enforce proxy/server multipart/request limits and streaming where possible before deserialization; bounded fields/nesting; return 413. **Mistake:** `@Size` after full object allocation only.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring MVC uses Jackson HttpMessageConverter under Boot. Exact unknown-property/date/error defaults change by version/configuration; inspect ObjectMapper and contract tests. Spring Framework 6 uses Jakarta packages and ProblemDetail support.

Healthcare/fintech APIs require tenant-derived authorization, exact money/time, idempotency and safe audit. A structurally valid claim can still be unauthorized or invalid state; validation is layered.

The Java SE lab validates boundary logic only. Full MVC evidence requires a Boot build and MockMvc/server tests, described in curated docs and later testing lesson.

## 5. COMPARISON TABLE

| Mechanism | Input/role | Use | Boundary |
|---|---|---|---|
| PathVariable | resource identity | `/claims/{id}` | encoding/type |
| RequestParam | filters/options/page | query | size/default/repetition |
| RequestBody | structured payload | create/update | media/size/deserialization |
| Filter | raw chain/all dispatch | auth/correlation/CORS | before MVC/advice |
| Interceptor | selected handler | handler policy/timing | not all responses/security alone |
| ControllerAdvice | MVC mapping | consistent errors | pre-MVC filter errors |
| DTO validation | structure | required/range/format | races/domain/auth |
| service/domain | state/policy | transitions/ownership | DB concurrency invariant |
| DB constraint | authoritative data invariant | unique/FK/check | friendly context mapping |
| MockMvc | in-context simulated request | mapping/JSON/validation/advice | real socket/proxy |
| random-port test | actual embedded server | HTTP stack | external ingress/TLS |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Controller is business layer—it is translation/orchestration boundary.
2. Entity equals API DTO—causes coupling/leaks/lazy cycles.
3. Validation annotation automatically runs—needs integration and `@Valid`/method validation.
4. Bean Validation ensures uniqueness—it cannot beat DB race.
5. 401 means forbidden—401 unauthenticated, 403 authenticated denied.
6. CORS secures API—it is browser cross-origin policy.
7. CSRF irrelevant to REST—depends on automatic credentials/browser architecture.
8. ControllerAdvice catches filters—many failures happen before DispatcherServlet.
9. JSON number safe for all IDs—JavaScript precision can lose large integers.
10. Return stack trace helps client—it leaks internals/data.
11. GET body works everywhere—it has poor/intermediary semantics; use query/resource design.
12. `isOk` sufficient test—assert headers/schema/body/errors/security.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- Server/filter/security → DispatcherServlet → mapping/arguments/converter/validation → controller → converter/error resolver.
- RestController JSON body; mappings declare method/path/consumes/produces.
- Path identity, query options, body command; authenticated tenant server-derived.
- Boundary DTOs, never entity; explicit allowlist mapping.
- `@Valid` nested; DTO structure, domain state, DB constraint under concurrency.
- 201+Location create, 202 async, 204 no body; 401 authn, 403 authz, 409 conflict.
- RestControllerAdvice + ProblemDetail; safe stable error codes.
- Filter before MVC; advice may not catch it.
- CORS ≠ auth; CSRF depends on browser credentials.
- Bound body/file/query/page before expensive work.
- MockMvc boundary tests; real server/proxy tests separately.

## 8. PRACTICE SET FOR SELF-TEST

1. Difference PathVariable, RequestParam, RequestBody?
2. What produces 415 versus 406?
3. Why separate request/response DTO/entity?
4. How trigger nested validation?
5. Where enforce unique external claim ID safely?
6. Map unauthenticated versus unauthorized status.
7. Why doesn't CORS stop curl?
8. Where map authentication filter errors?
9. Design safe validation Problem Details fields.
10. What tests prove JSON mapping and validation?

## 9. CURATED RESOURCES

1. [Spring Framework Web MVC](https://docs.spring.io/spring-framework/reference/web/webmvc.html) — authoritative DispatcherServlet, controllers and processing pipeline.
2. [Spring MVC Annotated Controllers](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html) — exact mappings, arguments and return values.
3. [Spring Validation](https://docs.spring.io/spring-framework/reference/core/validation/beanvalidation.html) — Bean Validation integration/method validation.
4. [Spring MVC Error Responses](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html) — ProblemDetail/ErrorResponse/advice mechanics.
5. [Jackson Databind Documentation](https://github.com/FasterXML/jackson-databind) — object mapping configuration/security/version notes.
6. [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) — methods, status and content negotiation source.
7. [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457) — standard error representation.
8. [Spring Boot Testing Spring MVC](https://docs.spring.io/spring-framework/reference/testing/mockmvc.html) — MockMvc setup/request/assertion behavior.
9. [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html) — boundary threats beyond validation.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Spring Boot Fundamentals** — context/server/auto-config foundation.
2. **Java Records/Exceptions** — DTOs and error translation.
3. **Build/Testing** — validation dependencies and MockMvc.
4. **HTTP basics** — protocol semantics drive mappings/status.

### After

1. **Spring Data JPA Fundamentals** — service persists boundary commands safely.
2. **Spring Core/Transactions advanced** — proxy transaction/service boundaries.
3. **API Design and Security advanced** — idempotency/versioning/auth/abuse.
4. **Testing/Resilience** — contracts, retry/timeouts/faults.
5. **Observability** — trace/log/metrics around request pipeline.

---ANSWER KEY BELOW---

1. PathVariable extracts route identity, RequestParam query/filter/option, RequestBody deserializes payload via message converter.
2. 415 means request representation Content-Type unsupported; 406 means server cannot produce representation acceptable by Accept.
3. Prevent mass assignment/data leaks/lazy cycles, decouple persistence from public contract and tailor operation fields.
4. `@Valid` on request/root property plus `@Valid` on nested property/record component as needed and validation implementation configured.
5. Authoritative composite unique database constraint; service precheck optional UX; translate constraint/idempotency conflict.
6. 401 when credentials missing/invalid; 403 when authenticated principal lacks permission.
7. CORS is enforced by web browsers for scripts; arbitrary HTTP clients are not constrained.
8. Spring Security entry point/access-denied handler or filter catches and delegates to configured resolver; not ordinary controller advice assumption.
9. Stable type, title, HTTP status, safe detail/instance/correlation, violations with field+stable code+safe message; no stack/SQL/payload.
10. MVC slice/MockMvc tests exercise routes, converters, validation and advice; random-port tests actual embedded HTTP; contract tests schema.
