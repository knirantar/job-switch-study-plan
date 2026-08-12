# Java Build Tools, Testing and Debugging — From Source to Reproducible Evidence

**Parent:** 02 — Java and Spring  
**Level:** prerequisite 4  
**Study time:** 3–4 hours plus lab  
**Lab:** `BuildTestingDebuggingLab.java`

## 1. FOUNDATIONS

A professional Java application is not “a folder that works in IntelliJ.” It needs a reproducible build defining source layout, Java release, dependencies, compilation, tests, packaging and publication. Maven and Gradle automate this graph. An IDE consumes the build model; it must not be the only source of truth.

A **dependency** is external code identified by coordinates/version. A **repository** stores artifacts. A **transitive dependency** is required by another dependency. A **scope/configuration** controls when it is available (compile, runtime, test). A **lock/checksum/SBOM** supports reproducibility and supply-chain evidence. Version ranges and mutable snapshots make builds time-dependent.

Testing provides evidence at different boundaries. A **unit test** isolates a small behavior; **integration test** exercises real component collaboration (database/network/framework); **contract test** checks consumer/provider assumptions; **end-to-end** covers deployed flow. Debugging forms and tests hypotheses using stack traces, breakpoints, logs, dumps and profilers. Logging random values until a bug disappears is not diagnosis.

Interviews expect the practical basics: Maven lifecycle, dependency conflicts, JUnit assertions/lifecycle, Mockito trade-offs, Spring test slices, reading stack traces, deterministic time, test pyramid, mocking limits and CI behavior.

## 2. CORE MECHANICS

### 2.1 Standard project layout

Maven/Gradle convention: `src/main/java`, `src/main/resources`, `src/test/java`, `src/test/resources`. Package paths mirror names. Build output (`target/`, `build/`) is generated and ignored. `pom.xml` is Maven Project Object Model; `build.gradle(.kts)` is Gradle build. Wrapper (`mvnw`, `gradlew`) pins launcher version for developer/CI.

Separate main/test classpaths. Test helpers should not leak into production artifact. Resource loading uses classpath, not assumed working directory. Multi-module builds define boundaries but add coordination; use for real ownership/dependency separation, not one module per package.

### 2.2 Maven lifecycle

Important phases: validate, compile, test, package, verify, install, deploy. Invoking `mvn verify` runs earlier phases. `clean` is separate lifecycle and deletes output. Surefire runs unit tests; Failsafe conventionally integration tests during integration-test/verify. `install` puts artifact in local repository; it does not deploy application.

Coordinates: groupId/artifactId/version; packaging often jar. DependencyManagement controls versions but does not necessarily add dependencies. Spring Boot parent/BOM supplies compatible dependency versions. PluginManagement similarly configures defaults without execution unless plugin used.

### 2.3 Gradle fundamentals

Gradle tasks form a graph; common Java tasks `classes`, `test`, `check`, `build`. Configurations include `implementation`, `api` (java-library), `runtimeOnly`, `testImplementation`. `implementation` hides dependencies from consumer compile classpath, reducing coupling. Gradle daemon/cache improve speed; tasks must declare inputs/outputs to cache safely.

Use wrapper and version catalogs/platform/BOM. Avoid dynamic versions (`1.+`, latest.release). Build scripts are code: review plugins and repositories.

### 2.4 Dependency resolution

Maven generally selects nearest definition in dependency tree; dependencyManagement makes selection explicit. Gradle has conflict resolution rules (commonly newest unless constrained). Inspect `mvn dependency:tree` or `gradle dependencies/dependencyInsight`. Symptoms include NoSuchMethodError (compiled against different version than runtime), ClassNotFoundException, duplicate logging bindings.

Exclude only with understanding; upgrading/downgrading can violate library compatibility. Directly declare dependencies your code uses, not rely on accidental transitives. Keep one logging facade/backend combination appropriate to runtime.

### 2.5 Compiler/JDK compatibility

Pin toolchain/release. `--release 21` controls language/API target better than source/target alone. Running Java 25 does not mean artifact can use Java 25 APIs if production is 21. Bytecode compiled for newer release fails older JVM with UnsupportedClassVersionError.

Enable useful compiler warnings, annotation processing deliberately, encoding UTF-8. Lombok reduces boilerplate but changes compilation/IDE and can obscure interview fundamentals; understand generated code.

### 2.6 Packaging and executable JARs

Ordinary JAR contains classes/resources/manifest. Spring Boot plugin repackages executable archive with dependencies and launcher. Fat/uber JAR merges dependencies and can conflict in service metadata/signatures; use supported plugin. Layered containers separate dependencies/application for cache.

Never put secrets in resources/application files inside JAR—they are readable. Record artifact digest, source commit, dependency/SBOM and build provenance.

### 2.7 JUnit 5 basics

JUnit Jupiter uses `@Test`, lifecycle `@BeforeEach/@AfterEach`, `@BeforeAll/@AfterAll`, parameterized tests, nested tests, tags. Assertions: `assertEquals`, `assertTrue`, `assertThrows`, `assertAll`, timeout (understand thread semantics). Test name states behavior/condition.

Arrange–Act–Assert: set inputs/dependencies, invoke one behavior, assert observable outcome. One test may assert multiple facets of one behavior. Avoid tests coupled to private implementation. The included lab uses a dependency-free mini harness so it compiles anywhere; production should use JUnit.

### 2.8 Test doubles and Mockito

Dummy fills parameter; stub returns prepared result; spy records while real-ish behavior; mock verifies interactions; fake is working simplified implementation. Mockito creates mocks/stubs/verifications. Prefer state/outcome tests. Verify interactions when the interaction is the contract (audit event, payment gateway once).

Over-mocking produces tests that pass while integration fails and mirror implementation. Do not mock value objects/collections/JDK trivially. Avoid deep stubs. `verifyNoMoreInteractions` globally makes refactors brittle. For repository SQL/JPA semantics, use real database integration (Testcontainers), not mocked EntityManager.

### 2.9 Deterministic tests

Inject `Clock`, random generator/seed, IDs and executor/scheduler. Do not `Thread.sleep` hoping async work finishes; use latches/futures/eventually with deadline. Freeze locale/time zone or specify explicitly. Isolate filesystem via temp directories and network via controlled server/fake. Clean database state transactionally or with explicit fixtures.

The lab fixes clock at `2026-08-12T10:00Z`, making exact expiry boundary reproducible. It checks future, equality boundary, backoff and invalid input.

### 2.10 Unit versus integration versus slice

Unit tests run fast and locate logic. Integration tests validate serialization, framework configuration, SQL, transactions and network contracts. Spring `@WebMvcTest` loads MVC slice; `@DataJpaTest` JPA slice; `@SpringBootTest` broader context. Do not label an H2 repository test proof of PostgreSQL locking/types; use target database for fidelity.

Test pyramid is heuristic: many focused tests, fewer expensive broad tests. Modern services may use “test trophy” with strong integration emphasis. Optimize feedback and risk coverage, not a shape.

### 2.11 Test coverage, mutation and quality

Line/branch coverage shows executed code, not asserted correctness. 100% can be meaningless. Mutation testing changes code to see whether tests fail, revealing weak assertions, but costs time and equivalent mutants. Property-based testing generates values around invariants. Contract testing prevents API/schema drift.

Prioritize domain boundaries, negative paths, concurrency, serialization, database constraints, security and recovery. Test exact threshold equality and just below/above.

### 2.12 Reading stack traces

Read exception type/message, first application frame, causal chain (`Caused by`), suppressed exceptions. Top frame is throw location, not always root cause. Repeated wrapper layers require deepest relevant cause plus context. `NullPointerException` enhanced message identifies null expression. Preserve original trace; do not log only `e.getMessage()`.

For a failed startup, find final “APPLICATION FAILED” and root cause, not first warning. Classpath errors often show NoClassDefFoundError caused by initialization failure, which differs from ClassNotFoundException.

### 2.13 Debugger fundamentals

Breakpoints pause at line; conditional breakpoint limits cases; watch expressions inspect without mutation; step over/into/out; evaluate cautiously because methods can cause side effects. Inspect threads and lock ownership for hangs. Do not alter production state with remote debugger casually; security/performance risk.

Understand optimized/JIT code may not map perfectly; local variable absent after optimization. Reproduce under controlled environment where possible.

### 2.14 Logging for diagnosis

Structured logs include event, safe IDs, trace/request, release, outcome, duration/error category—not concatenated sensitive payload. Levels: ERROR requires attention/failure, WARN abnormal recoverable, INFO lifecycle/business-safe, DEBUG diagnosis, TRACE very detailed. Do not log same exception at every layer.

Parameter placeholders avoid eager string building. SLF4J is facade; Logback/Log4j2 implementations. Protect against log injection and secrets. Correlate metrics/traces; logs alone cannot reveal aggregate saturation.

### 2.15 JVM diagnostic tools primer

`jcmd <pid> VM.version`, `Thread.print`, `GC.heap_info`; `jstack` thread dump; `jmap`/heap dumps with caution; Java Flight Recorder/JDK Mission Control for low-overhead profiling; `jfr` tool; `jdeps`, `javap`. CPU profiling answers where time; allocation profiling where objects; thread dump blocking/deadlock; heap histogram/retained graph memory.

Do not take huge heap dump to full production disk or expose PHI/secrets. Use access, encryption and retention. Three thread dumps spaced apart reveal persistent stacks better than one.

### 2.16 CI basics

CI starts clean, uses wrapper/toolchain, restores safe caches, compiles/tests/scans/packages once, publishes immutable artifact. Do not rebuild separately for prod. Fail on test/format/security gates according to policy. Flaky tests are defects—quarantine briefly with owner/deadline, fix root cause.

Tests must not depend on execution order or developer machine. Parallel test execution exposes shared statics/ports/files/database collisions. Record test reports and versions.

### 2.17 Lab commands

```bash
javac BuildTestingDebuggingLab.java
java BuildTestingDebuggingLab
```

For a Maven project, equivalent routine is `./mvnw verify`; Gradle `./gradlew build`.

## 3. WORKED PROBLEMS

### Problem 1 — Maven phase (easy)

Need compile, unit/integration checks and package verification. Command? **Solution:** `./mvnw verify` (plus clean when justified). Verify includes prior phases. **Mistake:** only `mvn test` and assuming package/integration verification.

### Problem 2 — Runtime mismatch (easy)

UnsupportedClassVersionError on Java 17. **Solution:** artifact compiled newer; run supported newer JVM or compile `--release 17` without newer APIs, align CI/prod toolchains. **Mistake:** treating as corrupt JAR.

### Problem 3 — NoSuchMethodError (medium)

Compilation passes, runtime fails calling library method. **Solution:** runtime resolved incompatible older/different JAR. Inspect dependency tree/classpath, BOM, exclusions, container layers. **Mistake:** debugging source logic first.

### Problem 4 — Flaky clock test (medium)

Test sets deadline now+5ms and sleeps. **Solution:** inject fixed/mutable Clock and assert exact before/equal/after boundaries; no real sleep. **Mistake:** increasing sleep.

### Problem 5 — Mock repository (medium)

Mocked save test proves unique constraint? **Solution:** no; mock only proves configured call. Use real target DB integration and concurrent/constraint test. **Mistake:** equating interaction with persistence semantics.

### Problem 6 — Stack trace (medium)

Controller exception wraps service wraps SQL unique violation. Root response? **Solution:** inspect cause; map known duplicate domain conflict centrally, preserve trace internally, safe Problem Details externally. **Mistake:** expose SQL or return generic 500 without classification.

### Problem 7 — Deadlock diagnosis (hard)

App hangs, CPU low. **Solution:** capture multiple thread dumps/JFR, identify threads BLOCKED and lock cycle/connection wait; correlate pool metrics; fix lock order/boundaries, not add threads blindly. **Mistake:** heap dump for every hang.

### Problem 8 — Coverage (hard)

100% line coverage but mutation survives changing `>=` to `>`. **Solution:** missing equality-boundary assertion; add threshold test. Coverage executed line but not semantic edge. **Mistake:** quality = coverage number.

### Problem 9 — CI artifact (hard)

Prod Docker stage recompiles source after CI tests. **Solution:** promote the exact tested JAR/image digest; rebuild breaks provenance and may resolve different dependencies. **Mistake:** assuming same commit means same bytes.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring Boot Maven/Gradle plugins package executable applications and generate build info/layers. Dependency BOM compatibility matters: overriding one Jackson/Netty/Hibernate component can break a tested stack. Use dependency tree and Boot release notes.

Testcontainers starts real PostgreSQL/Kafka/etc in containers for integration fidelity; pin images and design cleanup/reuse. It improves confidence but is slower and still not full production topology.

OpenJDK 25 compiled and executed four deterministic checks in the lab. The custom harness is intentionally transparent; JUnit remains the production standard.

## 5. COMPARISON TABLE

| Tool/test | Strength | Use | Boundary |
|---|---|---|---|
| Maven | declarative lifecycle/convention | standard enterprise builds | XML/less flexible graph |
| Gradle | flexible incremental task graph | complex/multi-language builds | script complexity/cache correctness |
| unit test | fast/local diagnosis | pure domain behavior | framework/DB not proven |
| slice test | focused Spring config | MVC/JPA boundary | partial context |
| integration test | real collaborators | SQL/serialization/framework | slower/environment |
| E2E | deployed flow | critical journey | slow/flaky/root cause |
| mock | controlled interaction | outbound contract/rare path | implementation coupling |
| fake | realistic behavior | in-memory deterministic collaborator | semantic drift |
| logs | discrete context | known event diagnosis | aggregation/cardinality |
| thread dump | stacks/locks | hang/deadlock | momentary sample |
| JFR | time/allocation/locks | production-capable profiling | analysis expertise/storage |
| heap dump | retained object graph | memory leak | size/sensitive data/pause |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. IDE build equals CI build—use wrapper/build source of truth.
2. `mvn install` deploys service—it installs artifact locally.
3. clean always required—it discards useful incremental output; CI clean workspace may suffice.
4. latest/dynamic dependencies convenient—they destroy reproducibility.
5. Unit mocks prove database behavior—they cannot.
6. 100% coverage proves correctness—it measures execution, not assertions.
7. Sleep fixes async tests—it creates slow flakiness.
8. Mock every dependency—tests implementation, not behavior.
9. Catch/log only message—loses stack/cause.
10. First stack frame always root—read caused-by and application boundary.
11. Debug logging safe in prod—may expose data/overload storage.
12. Rebuild for deployment is harmless—exact tested artifact must be promoted.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- Standard layout main/test java/resources; generated output ignored.
- Maven `verify`; Gradle `build`; use wrapper and pinned toolchain.
- Dependency tree explains runtime conflicts; BOM aligns versions.
- Unit logic; slice framework boundary; integration real dependency; E2E journey.
- AAA, behavior-focused assertions, exact boundaries and negative cases.
- Mock interaction contracts sparingly; real DB for SQL/transaction proof.
- Inject Clock/random/IDs/executors; no arbitrary sleeps/order dependence.
- Read exception type, first application frame, cause chain, suppressed failures.
- Thread dump hang; JFR CPU/allocation/locks; heap dump retained memory.
- Promote exact tested artifact digest; never rebuild in deployment.

## 8. PRACTICE SET FOR SELF-TEST

1. What does Maven `verify` do relative to `test`?
2. Difference dependencyManagement and dependencies?
3. Why use `--release`/toolchain?
4. Choose test level for PostgreSQL unique/concurrent behavior.
5. What makes a time-based test deterministic?
6. When should interaction verification be used?
7. Diagnose NoSuchMethodError after successful compile.
8. Which artifact helps a low-CPU hang?
9. Why can heap dumps be security incidents?
10. What does “build once, promote” protect?

## 9. CURATED RESOURCES

1. [Apache Maven Introduction to Lifecycle](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html) — exact phases/goals/lifecycle behavior.
2. [Gradle Java Plugin](https://docs.gradle.org/current/userguide/java_plugin.html) — authoritative tasks/configurations/layout.
3. [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/) — annotations, assertions, parameterized and extension model.
4. [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org.mockito/org/mockito/Mockito.html) — exact stubbing/verification guidance and warnings.
5. [Spring Boot Testing](https://docs.spring.io/spring-boot/reference/testing/index.html) — official context/slice facilities.
6. [Testcontainers for Java](https://java.testcontainers.org/) — real dependency integration patterns and lifecycle.
7. [JDK Troubleshooting Guide](https://docs.oracle.com/en/java/javase/25/troubleshoot/) — official dumps, JFR and diagnostic commands.
8. **Gerard Meszaros, _xUnit Test Patterns_, Chapters 1–5 and Test Double taxonomy** — rigorous test design vocabulary.
9. **Michael Feathers, _Working Effectively with Legacy Code_, Chapters 1–10** — seams and safe test introduction.
10. **Joshua Bloch, _Effective Java_, Items 78–82** — concurrency testing/diagnosis context bridging later lessons.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java language/object model** — code/build/runtime vocabulary.
2. **Collections/generics/exceptions** — assertions and failure design.
3. **Modern Java/streams** — deterministic time/pipeline testing.

### After

1. **Spring Boot Fundamentals** — build plugins, starters and context tests.
2. **Spring Web** — MVC slice/serialization/error tests.
3. **Spring Data JPA** — real DB integration/transaction tests.
4. **JVM Memory/GC** — uses JFR/jcmd/heap diagnostics deeply.
5. **Testing and Resilience** — advances into contracts, mutation, load and fault injection.

---ANSWER KEY BELOW---

1. Verify runs earlier phases including compile/test/package and verification/integration conventions; test stops earlier.
2. dependencyManagement selects/configures versions for dependencies when used; dependencies actually adds them to project classpaths.
3. It aligns language/API/bytecode with target JDK and prevents accidental use of newer APIs despite newer build JVM.
4. Integration test against actual PostgreSQL (often Testcontainers), including database constraint and concurrent transactions.
5. Inject controlled Clock/scheduler/random/IDs and assert events/deadlines without real sleep.
6. When an outbound interaction itself is observable contract: one payment call, audit publication, no call on validation failure.
7. Runtime classpath resolved incompatible version; inspect dependency tree, BOM/exclusions and actual packaged classes.
8. Multiple thread dumps and/or JFR; inspect blocked/waiting stacks, locks and pools.
9. They may contain entire object graph including credentials, PHI, tokens and customer data; also large/pause/disk risk.
10. Provenance: production bytes are exactly those tested/scanned/signed, immune to dependency/build-environment drift.
