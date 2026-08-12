# Modern Java: Lambdas, Streams, Optional, Date/Time and Useful Language Features

**Parent:** 02 — Java and Spring  
**Level:** prerequisite 3  
**Study time:** 3–4 hours plus lab  
**Lab:** `ModernJavaLab.java`

## 1. FOUNDATIONS

Java 8 introduced lambdas, method references, streams, Optional and the `java.time` API, changing everyday Java and interview expectations. Later releases added records, sealed classes, switch expressions, text blocks, pattern matching and virtual threads. “Modern Java” does not mean replacing loops/classes with clever one-liners; it means using higher-level immutable transformations and expressive type features where they make correctness clearer.

A **function** maps inputs to output; a **pure function** has no externally visible side effects and produces the same result for the same inputs. Java is not a pure functional language, but functional interfaces and immutable data make collection processing easier to reason about. A **lambda** is an implementation of a target functional interface, not an untyped free-floating function. A **stream** is a lazy pipeline over a data source, not a collection and not necessarily I/O streaming.

Streams exist to describe “what transformation/reduction” while the library controls traversal. This enables composition and sometimes safe parallel execution with concise, type-safe, reusable processing stages. It breaks when pipelines hide side effects, perform database/network calls per element, rely on encounter order accidentally, or allocate enormous intermediate results.

## 2. CORE MECHANICS

### 2.1 Functional interfaces

A functional interface has one abstract method (Object methods do not count) and can be annotated `@FunctionalInterface`. Standard types: `Predicate<T>` returns boolean; `Function<T,R>` transforms; `Consumer<T>` returns void; `Supplier<T>` supplies; `UnaryOperator<T>` maps T→T; `BinaryOperator<T>` combines two T. Primitive specializations (`IntPredicate`, `ToLongFunction`) avoid boxing.

Compose predicates with `and/or/negate`; functions with `andThen/compose`. Use domain-named functions when logic is nontrivial. Throwing checked exceptions do not fit standard interfaces directly; handle at a sensible boundary rather than generic “sneaky throw.”

### 2.2 Lambda syntax, capture and `this`

Forms: `x -> x * 2`, `(a,b) -> a+b`, `x -> { log(x); return parse(x); }`. Captured local variables must be final/effectively final because lambdas can outlive the stack frame; object state referenced by them can still mutate. In a lambda, `this` refers to enclosing instance; in an anonymous class, `this` refers to anonymous instance.

Avoid mutable captured accumulators, especially with parallel streams. `int[] sum={0}; xs.forEach(x -> sum[0]+=x)` is side-effectful and races in parallel; use `mapToInt().sum()`.

### 2.3 Method and constructor references

`Claim::id` references an instance method of arbitrary Claim; `validator::validate` a method on a specific receiver; `ClaimDto::new` a constructor; `Integer::parseInt` static. They are syntax alternatives when the target interface determines signature. If a reference obscures overload selection or intent, use a lambda.

### 2.4 Stream lifecycle and laziness

Create from collections, arrays, `Stream.of`, generators, files (close resource). Intermediate operations (`filter`, `map`, `flatMap`, `sorted`, `distinct`, `limit`, `peek`) are lazy. A terminal operation (`toList`, `collect`, `reduce`, `count`, `findFirst`, `forEach`) consumes once. Reusing a consumed stream throws IllegalStateException.

Short-circuit operations (`anyMatch`, `findFirst`, `limit`) may stop early. Ordering and stateful operations such as sorted/distinct can require buffering. The source must not be structurally interfered with during traversal.

### 2.5 `map`, `flatMap`, filtering and sorting

`map` transforms one element to one result. `flatMap` transforms to zero/many streams and flattens—e.g., orders to line items. `filter` retains matching elements. Sort with explicit comparator and stable tie-breaker for deterministic APIs.

Pipeline in lab filters approved/high-value claims, sorts descending amount then ID, maps IDs and returns unmodifiable encounter-order list via `toList()` (the exact mutability contract differs from `Collectors.toList`, whose implementation/mutability is not guaranteed by specification).

### 2.6 Reduction

`reduce(identity, accumulator)` combines to one value; identity must be neutral and operation associative for parallel correctness. Sum use primitive streams. `collect` performs mutable reduction using supplier/accumulator/combiner; built-in collectors cover lists, sets, joining, grouping, partitioning, mapping, counting, summing, averaging and summary statistics.

`toMap` needs a merge function if duplicate keys possible. Omitting it throws IllegalStateException. Do not silently keep first/last unless business rule says so.

### 2.7 Grouping and downstream collectors

`groupingBy(Claim::tenant, summingLong(Claim::amountPaise))` yields per-tenant totals. Specify map supplier (`TreeMap::new`) when deterministic sorted keys required. Nested grouping can become unreadable and memory-heavy; a database aggregation may be the correct execution engine for millions of rows.

`partitioningBy` always creates boolean groups. `collectingAndThen` finishes/transforms. Modern `teeing` computes two collectors in one pass. Understand the types rather than memorizing chains.

### 2.8 Optional correctly

Optional represents present/absent return. `map` transforms present value; `flatMap` avoids nested Optional; `filter` may empty; `or` gives alternate Optional; `orElseGet` lazy; `orElseThrow` explicit. Optional is itself a value object and should never be null.

Avoid Optional fields in JPA entities/DTO serialization without deliberate support. Avoid parameters—overload or nullable annotation/validation is often clearer. Never use `get` without proof. `Optional<List<T>>` usually duplicates empty meanings.

### 2.9 Parallel streams

Parallel streams split work through common ForkJoinPool by default. They help for large, CPU-bound, splittable, side-effect-free operations with enough per-element work. They often hurt small collections, blocking I/O, ordered operations, shared mutable state and server applications sharing common pool.

Measure. A Spring request using `parallelStream()` for blocking database calls can exhaust connections and contaminate common-pool latency. Parallel reduction requires associative accumulator/combiner and correct identity. Floating sum order can change rounding.

### 2.10 `java.time`

Legacy `Date/Calendar` APIs are mutable/confusing. `Instant` is a UTC timeline point; `LocalDate` date without zone; `LocalTime`; `LocalDateTime` no offset/zone and therefore not a unique instant; `OffsetDateTime` includes offset; `ZonedDateTime` includes region rules; `Duration` time-based; `Period` date-based.

Store event timestamps as Instant (or DB timestamptz with understood driver semantics), retain source zone when business meaning needs it. India UTC+05:30 is stable currently; zones like America/New_York have daylight transitions. Adding 24 hours differs from adding one calendar day across DST. Inject `Clock` for deterministic tests.

### 2.11 Records and pattern matching refresher

Records are ideal immutable DTO/value carriers; compact constructor validates/copies. Pattern `if (obj instanceof Claim claim)` combines test/cast. Pattern switch over sealed hierarchy can be exhaustive. Null handling in switch is explicit; do not assume default catches it. Use features supported by your production JDK and configured compiler release.

### 2.12 Text blocks and switch expressions

Text blocks `"""..."""` improve JSON/SQL test fixtures but indentation/newlines matter; still parameterize SQL—text blocks do not prevent injection. Switch expression uses `->` without fall-through and `yield` for block result. Classic switch fall-through remains a common bug unless intentional/documented.

### 2.13 Immutability and defensive transformations

Stream pipeline is not automatically pure: mapping can mutate inputs and collectors can return mutable objects. Prefer immutable input/value objects and return `List.copyOf`/`toList` where contract is unmodifiable. For mutable elements, deep-copy/domain design remains.

### 2.14 Performance and debugging

Streams add abstraction, lambda objects/inlining behavior and boxing. HotSpot often optimizes, but a primitive loop may be clearer/faster in hotspots. Profile before rewriting. Debug by naming predicates/functions, unit-testing stages and using debugger; `peek` is primarily for observing/debugging and should not drive required side effects.

### 2.15 Lab

```bash
javac ModernJavaLab.java && java ModernJavaLab
```

It verifies pipeline ordering, grouped totals, Optional absence/lazy fallback and Instant→Asia/Kolkata conversion.

### 2.16 Interview reasoning: translate pipelines back to mechanics

Interviewers often ask for a stream solution and then probe its cost. Be able to translate each stage: `filter` and `map` are normally one traversal and lazy; `sorted` materializes/buffers and costs O(n log n); `distinct` keeps seen state (usually hashing); `limit` can short-circuit; `groupingBy` retains groups proportional to distinct keys/elements. A pipeline is not automatically O(n) because it reads left to right.

Also explain encounter order. Lists produce ordered streams; HashSet order is unspecified. `findFirst` preserves encounter-order semantics and can constrain parallelism; `findAny` permits any element and may scale better. `forEach` on parallel stream does not preserve order; `forEachOrdered` does with coordination cost. Deterministic API output needs explicit sorting/tie-breaks, not incidental map/set order.

Checked exceptions are another probe. A mapping function that calls an API throwing IOException cannot be passed directly to ordinary Function. Good answers move I/O to a boundary, return a typed result, or wrap while preserving cause/category; they do not catch and return null. Streams are strongest for in-memory transformations, not as a disguise for imperative failure-heavy workflows.

Finally, distinguish stream parallelism from asynchronous composition. `parallelStream` blocks caller until terminal result and uses data parallelism; `CompletableFuture` composes asynchronous tasks; virtual threads provide cheap blocking concurrency. Choose according to dependency/resource model, deadline and pool limits.

When a collector result is wrong, verify its supplier creates independent containers, accumulator mutates only its container, combiner merges without losing entries, and declared characteristics are truthful. A collector that works sequentially can fail in parallel because its combiner was never exercised. Test empty, singleton, duplicate-key and partitioned inputs explicitly.

## 3. WORKED PROBLEMS

### Problem 1 — Target type (easy)

Can `var f = x -> x+1;` compile? **Solution:** no target functional-interface type; use `IntUnaryOperator f = x -> x+1`. **Mistake:** treating lambdas as standalone dynamically typed values.

### Problem 2 — Laziness (easy)

Create stream with `filter` logging but no terminal operation. Output? **Solution:** none; intermediate pipeline not traversed. **Mistake:** assuming map/filter execute immediately.

### Problem 3 — FlatMap (medium)

List<Order> to all item IDs. **Solution:** `orders.stream().flatMap(o->o.items().stream()).map(Item::id).toList()`. **Mistake:** map yields Stream<List/Stream> nesting.

### Problem 4 — Duplicate key (medium)

Two claims same tenant in `toMap(Claim::tenant, Claim::amount)`. **Solution:** supply merge such as Long::sum if total intended, or reject duplicates deliberately. **Mistake:** assuming map collector groups automatically.

### Problem 5 — Optional fallback (medium)

Why DB called on cache hit with `orElse(load())`? **Solution:** arguments evaluated eagerly; use `orElseGet(this::load)`. **Mistake:** confusing API names with evaluation semantics.

### Problem 6 — Date/time (medium)

Persist `LocalDateTime 2026-11-01 01:30` for New York. Unique? **Solution:** no, DST overlap can represent two instants; persist Instant/offset and zone context. **Mistake:** treating local timestamp as timeline point.

### Problem 7 — Parallel side effect (hard)

`parallel().forEach(result::add)` on ArrayList. **Solution:** data race/corruption; use collect/toList or thread-safe structure with cost, and only parallel if measured. **Mistake:** thread-safe assumption from stream API.

### Problem 8 — Reduce identity (hard)

Parallel product uses identity 0. **Solution:** all products become 0; multiplicative identity is 1, operation associative. **Mistake:** copying sum identity.

### Problem 9 — Database N+1 stream (hard)

`ids.stream().map(repo::findById)` runs 10,000 queries. **Solution:** bulk query/chunking, join/projection, control memory; stream is not batching. **Mistake:** equating fluent syntax with efficient execution.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring controllers/services frequently use streams for DTO mapping and grouping. Keep persistence access outside per-element functions. Hibernate lazy associations traversed in a stream can trigger N+1 and fail outside transaction. MapStruct or explicit mapping may be clearer for complex DTO contracts.

Spring injects `Clock` as a bean to make expiry logic deterministic. Database timestamps, JSON ISO-8601 and user-local display require explicit conversions. Never rely on server default time zone.

The lab uses only Java SE 25 and deterministic inputs. It demonstrates semantics, not claims that streams outperform loops.

## 5. COMPARISON TABLE

| Approach | Strength | Use | Boundary |
|---|---|---|---|
| for-loop | explicit/control/low overhead | mutation, complex state, hotspot | verbose composition |
| sequential stream | declarative lazy pipeline | collection transformations | side effects/debug/boxing |
| parallel stream | easy fork/join | measured CPU-bound bulk | common pool/I/O/order |
| `map` | one→one | DTO/property transform | nested collections |
| `flatMap` | one→many flatten | nested elements/Optional | readability |
| `reduce` | immutable fold | associative scalar | identity/parallel rules |
| `collect` | mutable reduction | grouping/containers | collector complexity |
| Optional | explicit maybe-one return | repository/service lookup | fields/params/serialization |
| Instant | unique UTC point | events/audit | no human zone meaning |
| LocalDateTime | wall-clock components | appointments with zone elsewhere | ambiguous instant |
| ZonedDateTime | region rules | user/business calendar | larger/versioned tz rules |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Stream stores data—it is a one-use computation pipeline.
2. Intermediate operations execute immediately—they are lazy.
3. `peek` is for business side effects—it is observational/debug-oriented.
4. Streams automatically faster—overhead and workload decide.
5. Parallel stream uses a private pool—normally common ForkJoinPool.
6. Parallel helps blocking I/O—it may starve/shared-resource explode.
7. `toMap` handles duplicates—it throws without merge.
8. `Collectors.toList` guarantees ArrayList/mutability—it does not.
9. Optional eliminates null everywhere—it is a focused API return tool.
10. LocalDateTime is UTC—it has no offset/zone.
11. Add 24h equals next local day—DST can differ.
12. Method reference always clearer—overloads/context can obscure intent.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- Predicate test; Function apply; Consumer accept; Supplier get.
- Lambda needs target functional-interface type; captures effectively-final locals.
- stream source → lazy intermediate → one terminal; cannot reuse.
- map one→one; flatMap flatten; filter retain; sorted buffers/order.
- Prefer primitive streams for numeric reductions.
- toMap duplicate requires merge; groupingBy groups.
- Optional: map/flatMap/orElseGet/orElseThrow; avoid get/fields/params.
- Parallel only measured CPU-bound, associative, side-effect-free work.
- Instant timeline; LocalDateTime no zone; ZonedDateTime region rules.
- Inject Clock; never rely on default timezone/current time in tests.

## 8. PRACTICE SET FOR SELF-TEST

1. Name functional interfaces for boolean test, transformation and lazy supply.
2. Why must captured local variables be effectively final?
3. What triggers execution of a stream pipeline?
4. Write grouping of claims by tenant with count.
5. How do you handle duplicate keys in `toMap`?
6. Why is mutable ArrayList accumulation unsafe in parallel?
7. `orElse` versus `orElseGet`?
8. Choose type for an absolute audit timestamp and explain.
9. Why can adding Period.ofDays(1) differ from Duration.ofHours(24)?
10. When is a loop preferable to a stream?

## 9. CURATED RESOURCES

1. [Java Stream API, Java SE 25](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/package-summary.html) — authoritative laziness, non-interference and reduction contracts.
2. [Java `java.util.function` API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/function/package-summary.html) — standard functional-interface signatures/composition.
3. [Java Date-Time tutorial](https://dev.java/learn/date-time/) — official modern temporal model and examples.
4. **Joshua Bloch, _Effective Java_, Items 42–48 and 55** — lambdas, method references, streams, parallel caution and Optional.
5. **Raoul-Gabriel Urma et al., _Modern Java in Action_, 2nd ed., Chapters 2–7** — functional/stream progression and collector mechanics.
6. [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441) — exact exhaustive pattern-switch semantics.
7. [Collectors API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/Collectors.html) — grouping, downstream collectors and duplicate behavior.
8. [Clock API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/time/Clock.html) — injectable time source and test use.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java Language/Object Model** — supplies interfaces, records and methods.
2. **Collections/Generics/Exceptions** — streams operate on typed collections and propagate failures.
3. **Problem-Solving Patterns** — keeps fluent code algorithmically sound.

### After

1. **Build, Testing and Debugging** — tests pipeline/time/error behavior.
2. **Spring Boot Fundamentals** — uses lambdas/configuration and Java time types.
3. **Spring Web** — maps DTOs/Optional/temporal JSON carefully.
4. **Spring Data JPA** — avoids streaming over lazy relations/N+1.
5. **Concurrency/Virtual Threads** — distinguishes data parallelism from request concurrency.

---ANSWER KEY BELOW---

1. Predicate<T>, Function<T,R>, Supplier<T>.
2. Lambda may outlive stack frame and captures a stable value copy; allowing reassignment would produce confusing mutable closure semantics. Referenced objects may still mutate.
3. A terminal operation such as collect, toList, count, reduce or findFirst.
4. `claims.stream().collect(groupingBy(Claim::tenant, counting()))`.
5. Provide explicit merge function matching business semantics, or reject/prevalidate duplicates.
6. ArrayList mutation is unsynchronized and accumulator violates non-interference; collect produces isolated partial results/combination.
7. orElse evaluates fallback eagerly; orElseGet invokes supplier only when absent.
8. Instant: it uniquely identifies a UTC timeline point; retain source zone separately if relevant.
9. Period advances local calendar date through zone rules; 24-hour Duration advances exact elapsed time and can land at different local hour across DST.
10. When mutation/control flow/checked handling is clearer, input is tiny, performance hotspot is measured, or pipeline would hide side effects/I/O.
