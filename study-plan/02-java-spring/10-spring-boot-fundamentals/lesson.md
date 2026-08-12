# Spring Boot Fundamentals — Context, Beans, Auto-Configuration and Application Lifecycle

**Parent:** 02 — Java and Spring  
**Level:** prerequisite 5  
**Study time:** 3–4 hours plus concept lab  
**Lab:** `SpringBootConceptLab.java` (dependency-free IoC simulation)

## 1. FOUNDATIONS

### Spring versus Spring Boot

The **Spring Framework** provides an inversion-of-control container, dependency injection, resource abstraction, events, validation, data access, transactions, web frameworks, testing and integrations. **Spring Boot** is an opinionated layer that assembles production-ready Spring applications through starters, auto-configuration, embedded servers, external configuration and operational features. Boot does not replace Spring; it chooses/configures it based on classpath and properties while allowing overrides.

Before Spring, Java enterprise systems often manually constructed object graphs, looked up services through containers, and configured large XML descriptors. Dependency injection separates object creation/wiring from business use. A `ClaimService` declares it needs a `Notifier`; the container supplies one. This improves substitution/testing and centralizes lifecycle/configuration.

A **bean** is an object managed by the Spring `ApplicationContext`. The context is a bean factory plus events, resources, environment and more. **IoC** means framework controls creation/calls; **DI** is the concrete technique of supplying dependencies. A POJO is an ordinary Java object without requiring framework inheritance.

What breaks without these basics: developers put `new` everywhere and bypass proxies/config; confuse `@SpringBootApplication` with magic; create multiple ambiguous beans; inject fields making tests/lifecycle obscure; use profiles for every feature; access configuration before validation; perform work in constructors before application is ready.

### A minimal Boot application

```java
@SpringBootApplication
public class ClaimsApplication {
  public static void main(String[] args) {
    SpringApplication.run(ClaimsApplication.class, args);
  }
}
```

`@SpringBootApplication` combines `@SpringBootConfiguration` (a specialized `@Configuration`), `@EnableAutoConfiguration`, and `@ComponentScan` from its package downward. Place it in a sensible root package. `SpringApplication.run` prepares environment, creates context appropriate to application type, loads bean definitions, refreshes context, starts lifecycle/server and invokes runners. It returns the context; it is not merely “start Tomcat.”

## 2. CORE MECHANICS

### 2.1 Starters and dependency management

Starter dependencies group compatible libraries: web, validation, data-jpa, security, actuator, test. They contain little/no functional code themselves; they select dependencies. Boot's BOM/dependency management aligns versions. Do not specify versions for managed dependencies without reason. A starter can activate auto-configuration by placing classes on classpath.

`spring-boot-starter-web` traditionally brings Spring MVC, Jackson, validation integration and embedded servlet server choice (commonly Tomcat). WebFlux is different reactive stack; adding both can choose MVC by Boot rules unless forced. Inspect dependency tree and conditions.

### 2.2 Component scanning and stereotypes

`@Component` marks a scan candidate; `@Service`, `@Repository`, `@Controller`, `@RestController` are specialized stereotypes carrying semantics/tooling. `@Repository` participates in persistence exception translation when infrastructure configured. Annotation on class creates bean definition if scanning includes it.

Scanning is package-based, not “find everything in project.” A component outside root package is missing unless imported/scanned. Overbroad scanning can accidentally instantiate test/other module beans. Prefer explicit module configuration/import boundaries.

### 2.3 Java configuration and `@Bean`

`@Configuration` class declares `@Bean` factory methods for third-party types or explicit assembly:

```java
@Bean Clock clock() { return Clock.systemUTC(); }
@Bean ClaimService claimService(ClaimRepository repo, Clock clock) {
  return new ClaimService(repo, clock);
}
```

Method parameters are resolved beans. Bean default name is method name; type usually drives injection. Full configuration classes may proxy inter-bean method calls to preserve singleton semantics; `proxyBeanMethods=false` avoids proxy when methods do not directly call one another. Do not call `@Bean` method manually from arbitrary code expecting container behavior.

### 2.4 Constructor injection

Use constructor injection for required dependencies. With one constructor, `@Autowired` is unnecessary. Benefits: dependencies explicit, final fields, object cannot exist invalid, plain unit construction, cycle exposed. Field injection hides requirements, prevents final and encourages framework-only tests. Setter injection can represent optional/reconfigurable dependencies but be deliberate.

The included `MiniContext` demonstrates contract registration and constructor assembly. Real Spring resolves richer metadata, scopes, qualifiers, lifecycle and proxies.

### 2.5 Candidate resolution: primary and qualifier

If two Notifier beans exist, injection by type is ambiguous and startup fails. `@Primary` chooses default; `@Qualifier("sms")` selects semantic bean; bean name can act as fallback qualifier. Prefer custom qualifier annotation for stable meaning. Collections (`List<Notifier>`) inject all candidates in ordered order.

Do not “fix” ambiguity by marking random primary. Define which policy needs which implementation. `@ConditionalOnMissingBean` auto-configuration backs off when application bean exists.

### 2.6 Bean scopes

Default singleton means one bean instance per ApplicationContext, not JVM-wide or thread-safe. Prototype creates each lookup/injection resolution, but injecting prototype into singleton resolves once unless provider/proxy. Web scopes include request/session/application; scope proxy/provider needed when shorter-lived dependency enters singleton.

Singleton services must be stateless or synchronize/thread-confine mutable state. Never store current user/request fields in controller/service singleton. Local variables are per invocation; injected collaborators must be thread-safe according to contract.

### 2.7 Bean lifecycle

Definition → instantiate → populate dependencies → aware callbacks → BeanPostProcessors before initialization → `@PostConstruct`/InitializingBean/custom init → post-process after init (often proxy) → use → `@PreDestroy`/DisposableBean/custom destroy on context close. Constructors should establish object invariants, not start network-heavy work. PostConstruct occurs during startup and failures prevent readiness.

Use `SmartLifecycle` for ordered start/stop, `ApplicationReadyEvent` after startup, `CommandLineRunner`/`ApplicationRunner` for startup tasks cautiously. Runners delaying or failing startup matter. Shutdown grace allows server stop accepting and in-flight completion before bean destruction.

### 2.8 Auto-configuration mechanics

Boot imports auto-configuration classes listed in metadata. Conditions include class present/missing, bean present/missing, property value, web application. Auto-configurations declare beans only when conditions match and usually back off before user beans. It is deterministic conditional configuration, not runtime reflection guessing every request.

Debug condition evaluation with `--debug`, actuator conditions endpoint (secure), or startup report. If DataSource auto-config fails, ask: JDBC classes present? URL/driver properties? custom DataSource? Do not exclude auto-config blindly.

### 2.9 Externalized configuration and precedence

Boot reads properties from packaged `application.properties/yaml`, profile files, external locations, environment variables, system properties, command line and config imports with documented precedence. Higher-precedence sources override. Exact precedence is version-sensitive; consult Boot reference.

Use canonical kebab-case keys `claims.review-threshold`. Environment `CLAIMS_REVIEW_THRESHOLD`. Never commit secrets; load from secret manager/mounted secret with rotation. Config values are strings converted to target types.

### 2.10 `@ConfigurationProperties`

Prefer typed grouped configuration:

```java
@ConfigurationProperties("claims")
public record ClaimsProperties(@Min(1) int maxBatch, Duration timeout) {}
```

Enable scanning/registration and validation (`@Validated`). It provides metadata, relaxed binding and fail-fast. `@Value` suits one simple expression but becomes scattered/stringly typed. Defaults must be explicit. Duration `250ms`, data size units reduce ambiguity.

### 2.11 Profiles and conditions

Profiles activate beans/properties for environments or modes: `@Profile("dev")`, `application-dev.yml`. Avoid `if(prod)` across business code and avoid profile explosion. Production behavior should be default-safe; use properties/feature management for orthogonal features. Never use profiles as authorization/security boundary.

Activate via environment/config, not bake into artifact. Tests declare active profile/dynamic properties. Profile groups can combine but need transparency.

### 2.12 Logging and startup

Boot uses a logging facade and default implementation through starter. Configure levels/pattern/JSON externally. Startup logs show profiles, server port, context failures. Do not disable failure analysis. Avoid logging configuration secrets.

`banner`, lazy initialization and startup metrics exist, but lazy beans move failures to first request and complicate readiness. Prefer eager validation for critical dependencies.

### 2.13 Embedded server and application types

Boot web app embeds servlet container, packages executable JAR and starts it as context bean. No external WAR server required, though WAR deployment possible. Configure port/address/graceful shutdown/threads via properties. Server readiness differs from process liveness.

Non-web command/batch app can set application type none. Reactive app uses reactive context/server. Do not add web starter just for RestClient if it unintentionally starts server; choose dependencies/configuration deliberately.

### 2.14 Actuator essentials

Actuator exposes production endpoints: health, info, metrics, loggers, mappings, conditions, env/configprops (sensitive), thread/heap dump. Expose minimal endpoints, secure authorization, separate management network/port where appropriate. Health contributors distinguish liveness/readiness; liveness should not depend on every remote service and cause restart storms.

Custom health must be fast/bounded. Metrics need low-cardinality tags. Actuator is not automatically public-safe.

### 2.15 DevTools and configuration metadata

DevTools restart/live reload helps local development and should not ship active in production. Configuration processor generates metadata for IDE completion. Annotation processors must be configured in build. Docker Compose/service connections can ease dev/test but production config remains explicit.

### 2.16 Failure modes at startup

Missing bean: scan/package/conditional/type. Ambiguous bean: qualifier/primary/design. Circular dependency: redesign responsibilities; constructor cycles fail and allowing cycles hides architecture. Port in use: configure/stop process. Binding failure: invalid/missing config. Failure to determine driver: datasource properties/dependency. UnsatisfiedLinkError: native mismatch.

Read nested cause and condition report. Do not add `@ComponentScan("com")` or `spring.main.allow-circular-references=true` as reflex.

### 2.17 Testing the context

Plain unit instantiate service. `ApplicationContextRunner` tests auto-config conditions. Slice tests load subset. `@SpringBootTest` loads full context (mock/random/defined web environment). `@MockBean`/newer mock override tools replace bean but overuse hides wiring. One context-load test catches configuration, not application correctness.

### 2.18 Dependency-free lab

```bash
javac SpringBootConceptLab.java && java SpringBootConceptLab
```

It models contract registration, constructor injection and deterministic missing/duplicate failures. It intentionally does not pretend to implement Spring annotations/proxies.

## 3. WORKED PROBLEMS

### Problem 1 — Missing bean (easy)

Service outside root package not found. **Solution:** move under root, import configuration or targeted scan; verify module boundary. **Mistake:** scan entire classpath.

### Problem 2 — Ambiguous bean (easy)

Email and SMS implement Notifier. **Solution:** qualifier at policy injection or primary default with semantic design; inject list if all. **Mistake:** delete one implementation.

### Problem 3 — Field injection (medium)

Why test NPE constructing `new Service()`? **Solution:** hidden field dependency only container fills. Refactor constructor required dependency/final. **Mistake:** use reflection in unit test.

### Problem 4 — Singleton state (medium)

Controller field `currentTenant` set per request. **Solution:** data race/cross-tenant leak. Keep request data local/from authenticated context; singleton stateless. **Mistake:** synchronize field (still semantic cross-request design).

### Problem 5 — Prototype (medium)

Prototype injected into singleton always same. **Solution:** resolved at singleton creation; inject ObjectProvider/proxy or redesign factory. **Mistake:** assuming annotation changes every method call.

### Problem 6 — Config precedence (medium)

Packaged timeout 2s, command line `--claims.timeout=100ms`. **Solution:** command-line higher precedence under usual Boot precedence; effective 100ms. Confirm version/reference. **Mistake:** reading YAML only.

### Problem 7 — Auto-config backoff (hard)

Custom DataSource bean appears and Boot defaults vanish. **Solution:** conditional-on-missing-bean backs off; custom bean owns configuration. Ensure properties/pool/metrics configured. **Mistake:** think Boot randomly failed.

### Problem 8 — Readiness (hard)

Liveness fails when optional downstream unavailable, Kubernetes restarts continuously. **Solution:** liveness only unrecoverable process state; readiness may remove traffic based on critical dependency with bounded checks; optional degraded dependency shouldn't restart. **Mistake:** same health for all probes.

### Problem 9 — Circular dependency (hard)

A constructor needs B and B needs A. **Solution:** identify misplaced responsibilities, extract coordinator/interface/event; do not enable circular references/lazy as default. **Mistake:** annotation workaround rather than architecture.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring Boot 3.x requires modern Java and Jakarta namespaces. Version selection must follow supported Boot release/JDK matrix. A service upgraded from Boot 2 may fail because `javax.*` moved to `jakarta.*`, Hibernate/Jackson/security defaults changed. Use migration guide and managed BOM.

Azure/Kubernetes deployment injects environment/secret/config; Boot relaxed binding maps it. Treat secret change/reload behavior per source/library—some beans do not hot reload. Immutable artifact with environment config supports promotion.

Lab runs on Java SE only to make DI principle visible. Actual Boot behavior must be verified using official test facilities and exact version.

## 5. COMPARISON TABLE

| Choice | Use | Strength | Boundary |
|---|---|---|---|
| component scan | application classes | concise discovery | package coupling/accidental beans |
| `@Bean` | third-party/explicit assembly | visible construction | config verbosity |
| constructor injection | required deps | immutable/testable/fail-fast | exposes cycles (good) |
| setter injection | optional/reconfigurable | flexible | temporarily invalid/mutable |
| field injection | none preferred | terse | hidden/framework-coupled |
| singleton | stateless service | low allocation/shared | thread safety/state leak |
| prototype | new per lookup | mutable instances | singleton injection trap/destruction |
| `@ConfigurationProperties` | grouped config | typed/validated/metadata | registration required |
| `@Value` | isolated simple value | convenient | scattered/stringly expressions |
| profile | environment/mode group | easy activation | combinatorial explosion |
| property condition | feature/integration | granular | config complexity |
| eager init | critical config | fail startup | startup time |
| lazy init | optional/heavy | faster startup | runtime surprise/readiness |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Boot and Spring same—Boot configures/assembles Spring.
2. Starter is code generator—it is dependency grouping/convention.
3. Component scan scans project—package hierarchy only.
4. Singleton is thread-safe—scope gives count, not safety.
5. Field injection easiest therefore best—it hides required contracts.
6. `@Primary` solves design—it only chooses candidate.
7. Profile is security boundary—it is configuration activation.
8. Environment variable always wins everything—use documented precedence/version.
9. Auto-configuration cannot be changed—it backs off/overrides explicitly.
10. Actuator endpoints safe by default for internet—expose/secure minimally.
11. Health equals all dependencies up—liveness/readiness semantics differ.
12. Constructor should call remote services—startup lifecycle/timeouts need explicit phase.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- Spring container manages beans; Boot adds starters/auto-config/server/config/actuator.
- `@SpringBootApplication` = configuration + auto-config + component scan.
- Constructor injection, final required deps; one constructor needs no Autowired.
- Scan from root package; use `@Bean` for explicit/third-party construction.
- Multiple candidates: semantic qualifier/primary/list.
- Singleton per context, not thread-safe; keep services stateless.
- Auto-config is conditional and backs off before user beans.
- Typed validated `@ConfigurationProperties`; secrets external.
- Profiles coarse environment/mode; conditions/properties granular.
- Lifecycle: instantiate → post-process/init/proxy → use → destroy.
- Actuator expose minimally; liveness ≠ readiness.
- Read cause/condition report before excluding auto-config.

## 8. PRACTICE SET FOR SELF-TEST

1. Distinguish Spring Framework and Spring Boot.
2. What three annotations compose `@SpringBootApplication`?
3. Why constructor injection over field injection?
4. What happens with two beans same interface and no qualifier?
5. Is singleton JVM-global/thread-safe?
6. Why might custom DataSource disable Boot DataSource bean?
7. When prefer ConfigurationProperties over Value?
8. Difference liveness/readiness?
9. Why prototype injected into singleton may not be new per call?
10. How diagnose auto-configuration condition?

## 9. CURATED RESOURCES

1. [Spring Boot Reference: Using Spring Boot](https://docs.spring.io/spring-boot/reference/using/index.html) — exact starters/application structure/run behavior.
2. [Spring Boot Auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html) — conditions, backoff and diagnostics.
3. [Spring Boot Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html) — authoritative property sources, precedence and binding.
4. [Spring Framework Core: IoC Container](https://docs.spring.io/spring-framework/reference/core/beans.html) — bean definitions, injection, scopes and lifecycle.
5. [Spring Boot Actuator](https://docs.spring.io/spring-boot/reference/actuator/index.html) — health, endpoints, metrics and security boundary.
6. **Craig Walls, _Spring in Action_, 6th ed., Chapters 1–3** — approachable Boot/DI/config application progression.
7. **Laurentiu Spilca, _Spring Start Here_, Chapters 2–6** — beans, context, wiring and scopes from first principles.
8. [Spring Initializr](https://start.spring.io/) — official project metadata/dependency starter generator; inspect generated build.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java Object Model** — beans are ordinary objects/interfaces.
2. **Collections/Exceptions** — candidate collections and startup failures.
3. **Build/Testing/Debugging** — starters/BOM/plugins and context tests.
4. **Modern Java** — records/config/time and lambdas.

### After

1. **Spring Web, Validation and Configuration** — request handling on Boot context/server.
2. **Spring Data JPA Fundamentals** — repositories/DataSource/JPA auto-config.
3. **Spring Core and Transactions (advanced)** — proxies, scopes/lifecycle and transaction mechanics deeply.
4. **API Design/Security** — production contracts and authorization.
5. **Testing/Resilience** — Boot slices, fault tolerance and load.

---ANSWER KEY BELOW---

1. Spring is framework modules/container; Boot opinionated assembly with starters, auto-config, embedded runtime, external config and operations.
2. SpringBootConfiguration, EnableAutoConfiguration, ComponentScan.
3. Makes required dependencies explicit/final, supports plain construction/tests and fails cycles/missing dependencies early.
4. Unsatisfied/NoUniqueBeanDefinition startup failure; use meaningful qualifier/primary or collection.
5. One per ApplicationContext by default; no automatic thread safety.
6. Auto-config commonly uses ConditionalOnMissingBean and backs off when application supplies one.
7. Grouped related settings needing conversion, validation, defaults and metadata; Value for one isolated simple value.
8. Liveness says process cannot recover and restart may help; readiness says should receive traffic. Remote outage often affects readiness, not liveness.
9. Dependency resolved once while singleton is created; use provider/scoped proxy/factory if genuinely needed.
10. Enable debug condition report, inspect conditions actuator securely, logs and bean definitions/classpath/properties.
