# Collections, Generics and Exceptions — Building Type-Safe Java APIs

**Parent:** 02 — Java and Spring  
**Level:** prerequisite 2  
**Study time:** 3–4 hours plus lab  
**Lab:** `CollectionsGenericsLab.java`

## 1. FOUNDATIONS

Arrays store a fixed number of one component type. Real applications need collections that grow, enforce uniqueness, map keys to values, preserve ordering or prioritize work. The Java Collections Framework supplies interfaces, implementations and algorithms with consistent contracts. Choosing a collection is an algorithmic and semantic decision: a `List` says order/duplicates matter; a `Set` says uniqueness; a `Map` associates keys and values; a `Queue` models processing order.

**Generics** parameterize types: `List<Claim>` means a list whose element API is Claim. Before generics, collections returned Object and callers cast at runtime. Generics move many errors to compilation, document relationships and enable reusable algorithms. Java generics mostly use **type erasure**: type parameters guide compilation, while runtime representations generally do not retain `List<String>` versus `List<Integer>`. This explains restrictions such as `new T()` and `instanceof List<String>`.

An **exception** is an object representing abnormal completion. It unwinds stack frames until caught or terminates the thread. Exceptions separate the happy-path return from failure details, but poor use hides control flow, loses context or catches failures that cannot be handled. Checked exceptions must be declared/caught; unchecked `RuntimeException` does not. The distinction is compiler enforcement, not severity.

Without these foundations, Spring code becomes raw maps, unsafe casts, generic `catch(Exception)`, null-heavy repository returns, mutable shared lists and incorrect JPA entity collections. Interviews repeatedly test collection complexity, hash/equality, wildcard variance, exception hierarchy and resource handling.

## 2. CORE MECHANICS

### 2.1 Iterable, Collection and iteration

`Iterable<T>` exposes `iterator()`, enabling enhanced `for`. `Collection<T>` adds size, add/remove/contains and bulk operations. `Iterator` has `hasNext`, `next`, optional `remove`. Structural modification during fail-fast iteration usually throws `ConcurrentModificationException`; this is bug detection, not a concurrency guarantee. Use iterator's remove, `removeIf`, collect a result, or a suitable concurrent collection.

Immutable factory collections (`List.of`, `Set.of`, `Map.of`) reject null and mutation. `Collections.unmodifiableList(original)` is a read-only view: changes through `original` remain visible. `List.copyOf` makes an unmodifiable shallow copy. Shallow means element objects may mutate.

### 2.2 List implementations

`ArrayList` is a resizable array: O(1) indexed get, amortized O(1) append, O(n) middle insert/remove/search. Growth occasionally copies the backing array. Pre-size when a large known count avoids copies, but not speculative huge memory.

`LinkedList` is doubly linked and implements List/Deque. Indexed access is O(n); node allocation and poor locality make it rarely faster for application lists. Even insertion at a known logical index requires traversal unless an iterator is already positioned. Prefer `ArrayDeque` for stacks/queues.

`subList` is usually a backed view with coupled structural modification hazards; copy it when independent lifetime is required. `Arrays.asList(array)` is fixed-size backed by the array: `set` works, `add` fails.

### 2.3 Set implementations

`HashSet` uses hash structure: expected O(1) add/contains/remove with sound hashes and distribution, no iteration-order contract. `LinkedHashSet` adds insertion/access ordering overhead. `TreeSet` uses a balanced sorted tree: O(log n), order by comparator/natural comparison.

Set uniqueness follows `equals` for hash sets and comparison result (`compare==0`) for sorted sets. A comparator inconsistent with equals can make TreeSet consider unequal objects duplicates. Mutable keys break both hashing and sorting invariants.

### 2.4 Map implementations and APIs

`HashMap` offers expected O(1), allows one null key/null values (avoid ambiguity). `LinkedHashMap` preserves insertion or access order and can implement bounded LRU-like behavior. `TreeMap` gives O(log n) sorted keys. `EnumMap` is compact/fast for one enum key type. `ConcurrentHashMap` supports concurrent operations but not null and individual method thread safety does not make a multi-step check-then-act atomic.

Use `getOrDefault`, `computeIfAbsent`, `merge`, `replaceAll`. `computeIfAbsent` mapping functions should be short and avoid recursive map mutation. `containsKey` distinguishes absent from mapped null. Iterate `entrySet` when both key/value are needed.

### 2.5 Queue, Deque and PriorityQueue

Queue pairs come in exception/sentinel forms: `add/remove/element` throw, `offer/poll/peek` return false/null. `ArrayDeque` is the standard stack/queue: `addLast/removeFirst` for FIFO, `push/pop` for stack. It disallows null, preventing ambiguity with empty `poll`.

`PriorityQueue` is a heap: O(log n) offer/poll, O(1) peek; iteration is not sorted. It is not stable for equal priorities. Use a sequence tie-breaker if FIFO among equals matters. It is not thread-safe; `PriorityBlockingQueue` has different blocking/unbounded implications.

### 2.6 Comparable and Comparator

`Comparable<T>.compareTo` defines natural order. `Comparator<T>` externalizes alternate order. Build comparators with `comparing`, `thenComparing`, primitive variants, `nullsFirst/Last`, `reversed`. Avoid subtraction (`a.age-b.age`) because overflow; use `Integer.compare`.

Comparator must be antisymmetric/transitive and consistent enough for sorting. `reversed()` reverses the whole comparator built so far; place carefully. Sorting objects with TimSort requires comparator contract—violations can throw “comparison method violates its general contract.”

### 2.7 Generic classes and methods

`class Box<T> { T value; }`; `static <T> T first(List<T> values)`. Type parameter scope begins at declaration. Use meaningful names for domain types, conventional T/E/K/V/R for small generic roles. Bounds: `<T extends Comparable<? super T>>` means T can compare to T or a supertype.

Generics are invariant: `List<Integer>` is not subtype of `List<Number>`, because otherwise a Double could be added to an Integer list. Arrays are covariant (`Integer[]` is Number[]) but enforce at runtime, enabling `ArrayStoreException`; generic invariance is safer.

### 2.8 Wildcards and PECS

`? extends Number` is an unknown subtype producing Numbers; you cannot safely add an Integer because actual list may be Double. `? super Integer` is an unknown supertype consuming Integers; reads are only Object. **PECS**: Producer Extends, Consumer Super.

The lab sums `List<? extends Number>` and writes defaults into `List<? super Integer>`. No wildcard is needed when exact type relationship should be preserved through input/output—use a named type parameter.

### 2.9 Erasure and generic restrictions

After erasure, overloaded methods `m(List<String>)` and `m(List<Integer>)` clash. You cannot create `new T[10]`, test `x instanceof List<String>`, use primitive type argument (`List<int>`), instantiate T directly or create static fields of class type parameter. Generic varargs can cause heap pollution; `@SafeVarargs` asserts safety and must not conceal unsafe writes.

Runtime frameworks recover some generic information from declarations/reflection (`Field.getGenericType`, Spring `ResolvableType`) but an ordinary `new ArrayList<String>()` object does not intrinsically carry all parameter information for arbitrary runtime tests.

### 2.10 Exception hierarchy

`Throwable` branches to `Error` and `Exception`. Errors such as OutOfMemoryError generally are not recoverable business conditions. RuntimeException is unchecked. Checked examples include IOException/SQLException (though Spring translates database exceptions to unchecked hierarchy).

Catch the most specific exception you can handle. Multiple catch clauses go specific before broad; multi-catch `catch (IOException | SQLException e)`. Never swallow. Preserve the cause when translating: `throw new ClaimImportException("file="+id, e)`. Include safe context, not secrets/PHI.

### 2.11 Checked versus unchecked design

Checked exceptions suit recoverable conditions callers are expected to handle and where API callers benefit from compiler visibility. Unchecked suit programming errors, invariant violations and failures that many layers cannot locally recover from. This is design judgment, not “checked bad.”

Do not return magic null/false for richly diagnosable failure. Do not use exceptions for normal loop control. Domain validation may aggregate field errors; a missing optional result may use Optional; infrastructure failure should preserve diagnostic cause and retry classification.

### 2.12 Try/catch/finally and try-with-resources

`finally` runs on normal/exceptional exit except abrupt process/JVM failures, but `return` in finally overrides earlier return/exception—never do it. Try-with-resources closes reverse declaration order and preserves close failures as suppressed. Resource variables can be effectively final in modern Java.

In Spring, exception type affects transaction rollback defaults: unchecked rolls back by default; checked does not unless configured. This is why exception translation/design affects data correctness.

### 2.13 Custom exceptions and boundaries

Name domain meaning: `DuplicateClaimException`, `InsufficientFundsException`. Include stable identifiers and machine-readable error code; avoid exposing internals to HTTP clients. At a boundary, map domain failures to Problem Details/status centrally. Retrying depends on category: validation is permanent, timeout/deadlock may be transient, unknown remote effect requires idempotency/status lookup.

### 2.14 Optional basics

`Optional<T>` represents maybe-one value. Create with `of`, `ofNullable`, `empty`; consume via `map`, `flatMap`, `filter`, `orElseGet`, `orElseThrow`. `orElse(expensive())` evaluates eagerly; `orElseGet` lazily. Avoid `isPresent/get` as null-check in disguise. Do not generally use Optional for JPA entity fields, serialization DTO fields or parameters; it is strongest as a return type.

### 2.15 Lab execution

```bash
javac CollectionsGenericsLab.java
java CollectionsGenericsLab
```

It verifies generic grouping, PECS, ordering/uniqueness, comparator selection, Map.merge and exception cause preservation.

## 3. WORKED PROBLEMS

### Problem 1 — Pick a collection (easy)

Need unique claim IDs preserving arrival order. **Solution:** `LinkedHashSet<String>`; HashSet loses order, List permits duplicates. **Mistake:** choosing by familiarity only.

### Problem 2 — Complexity (easy)

One million membership queries over 100k IDs: ArrayList versus HashSet. **Solution:** list worst/average scan O(100k) each; hash expected O(1) each after O(n) build. Measure memory/hash quality. **Mistake:** ignoring query frequency.

### Problem 3 — Priority iteration (medium)

Why printing PriorityQueue does not show sorted order? **Solution:** only head is guaranteed; repeatedly poll a copy for priority order. **Mistake:** assuming heap array is fully sorted.

### Problem 4 — PECS (medium)

Write method copying Integers into `List<Number>`. **Solution:** source `List<? extends Integer>` (or List<Integer>), destination `List<? super Integer>`. **Mistake:** using `List<Number>` source and rejecting Integer list.

### Problem 5 — Invariance (medium)

Why can't List<Integer> assign to List<Number>? **Solution:** then caller could add Double, violating actual Integer list. **Mistake:** extrapolating array covariance.

### Problem 6 — Concurrent map (medium)

`if(!map.containsKey(k)) map.put(k,v)` races. **Solution:** `putIfAbsent`/`computeIfAbsent` with safe mapping; individual operations do not make compound sequence atomic. **Mistake:** equating thread-safe container with atomic workflow.

### Problem 7 — Exception translation (hard)

Repository catches SQLException and throws new RuntimeException("failed"). **Solution:** preserve cause and safe context/category, preferably Spring translation/domain boundary; classify transient/constraint failures. **Mistake:** destroying diagnostics.

### Problem 8 — Comparator overflow (hard)

Comparator `(a,b)->a.score-b.score`. **Solution:** subtraction can overflow and violate order; `Comparator.comparingInt(Item::score)`. **Mistake:** treating comparator result magnitude as difference.

### Problem 9 — Optional eagerness (hard)

`cache.find(id).orElse(repository.load(id))` queries DB on cache hit. **Solution:** `orElseGet(() -> repository.load(id))`. **Mistake:** assuming orElse is lazy.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring Data repositories return collections, Optional or pages; their semantics should match absence/cardinality. Returning `Optional<List<T>>` usually duplicates meanings—empty list already represents no elements. JPA entity collections are managed wrappers; replacing them can disrupt dirty checking/orphan removal, and exposing mutable collection fields breaks aggregate control.

Spring translates JDBC/JPA exceptions into `DataAccessException` unchecked hierarchy, enabling technology-neutral handling while retaining cause. A unique-constraint failure should not become HTTP 500 blindly; map known domain conflicts at a boundary.

The dependency-free lab runs on OpenJDK 25. Collection complexity is contractual/asymptotic; exact throughput depends on data, JVM, hashes and hardware.

## 5. COMPARISON TABLE

| Type | Order | Core cost | Null | Use |
|---|---|---|---|---|
| ArrayList | index/insertion | get O(1), middle O(n) | yes | default list |
| LinkedList | insertion | index O(n) | yes | rare iterator-position operations |
| ArrayDeque | FIFO/LIFO | ends amortized O(1) | no | queue/stack |
| HashSet | unspecified | expected O(1) | one null | uniqueness |
| LinkedHashSet | insertion | expected O(1) | one null | ordered uniqueness |
| TreeSet | sorted | O(log n) | comparator-dependent | ranges/sorted uniqueness |
| HashMap | unspecified | expected O(1) | allows null | lookup |
| TreeMap | sorted keys | O(log n) | comparator-dependent | ordered/range map |
| ConcurrentHashMap | unspecified | concurrent expected O(1) | no | shared concurrent lookup |
| checked exception | compile declaration | explicit caller contract | n/a | expected recoverable condition |
| unchecked exception | no declaration required | propagates freely | n/a | invariant/program/infrastructure boundary |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. LinkedList insert always O(1)—finding position is O(n).
2. HashMap always O(1)—expected, depends on hashing/collisions/resizing.
3. PriorityQueue iteration sorted—only peek/poll head guarantee.
4. Unmodifiable view is immutable copy—backing collection/objects may change.
5. `ConcurrentHashMap` makes workflows atomic—compound operations still need atomic API/design.
6. List<Integer> is List<Number>—generics are invariant.
7. `? extends T` permits adding T—it is primarily a producer.
8. Generics fully exist runtime—erasure removes much parameterization.
9. Catch Exception improves resilience—it can swallow programmer/cancellation/system signals.
10. Logging and rethrowing everywhere helps—it duplicates noise; log at owning boundary.
11. Optional.get is normal—prefer combinators/orElseThrow.
12. Exception message can contain full request—avoid sensitive data.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the lesson.

- List = ordered/duplicates; Set = unique; Map = key→value; Deque = queue/stack.
- Default: ArrayList, HashSet/Map, ArrayDeque; Tree* for order/ranges.
- Hash keys need stable equals/hashCode; sorted keys need stable comparator.
- PECS: producer extends, consumer super.
- Generics invariant and erased; no `List<int>`, `new T()`, `instanceof List<String>`.
- Catch specific, preserve cause, add safe context, do not swallow.
- Checked is compiler-enforced; unchecked is not “unimportant.”
- Try-with-resources closes reverse order and preserves suppressed failures.
- Optional return for maybe-one; `orElseGet` is lazy.
- Concurrent collection operation ≠ atomic multi-step business effect.

## 8. PRACTICE SET FOR SELF-TEST

1. Choose a collection for FIFO work with no nulls.
2. Explain HashMap expected complexity and two degradation causes.
3. Why must hashed keys be immutable in equality fields?
4. Write a method that sums `List<Integer>` and `List<Long>` via wildcard.
5. What can be added/read from `List<? super Integer>`?
6. Why do two overloads differing only as List<String>/List<Integer> clash?
7. When is a checked exception defensible?
8. How do you preserve an original exception during translation?
9. Difference between `orElse` and `orElseGet`?
10. How should duplicate payment key be represented across repository/API layers?

## 9. CURATED RESOURCES

1. **Java SE 25 API, `java.util` package** — authoritative contracts for every collection/utility.
2. **Java Language Specification, Chapters 4.5, 8.4, 11** — parameterized types, generic methods and exception rules.
3. **Joshua Bloch, _Effective Java_, Items 26–33, 45–48, 69–77** — generics, streams/collections and exception design.
4. [Java Tutorials: Collections Framework](https://dev.java/learn/api/collections-framework/) — official conceptual path and examples.
5. [Optional API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Optional.html) — exact eager/lazy and combinator contracts.
6. [ConcurrentHashMap API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html) — atomic operations and concurrency guarantees.
7. **Maurice Naftalin & Philip Wadler, _Java Generics and Collections_, Chapters 1–8** — deepest treatment of subtyping/wildcards beyond this lesson.
8. **Cay Horstmann, _Core Java Volume I_, Chapters 7 and 9** — exceptions and collections in application code.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Java Language and Object Model** — supplies classes, equality and interfaces.
2. **Complexity Analysis** — explains collection performance choices.
3. **Hashing and Sets** — provides algorithmic foundations for hash collections.

### After

1. **Modern Java and Streams** — processes collections with functional APIs.
2. **Build, Testing and Debugging** — tests exceptional/collection behavior.
3. **Spring Web Fundamentals** — maps collection/exception/Optional contracts at HTTP boundaries.
4. **Spring Data JPA** — uses entity collections, repository generics and exception translation.
5. **Concurrency** — adds visibility/atomicity and concurrent collections.

---ANSWER KEY BELOW---

1. `ArrayDeque`, using offer/addLast and poll/removeFirst.
2. Expected O(1) with distributed stable hashes and capacity; poor collisions/adversarial hashes and resizing/load/cache behavior degrade it.
3. Mutation changes hash/bucket or comparison position, making lookup/removal incorrect.
4. `long sum(List<? extends Number> xs) { ... n.longValue(); }`.
5. Add Integer (and null technically); read only as Object without capture/cast.
6. Erasure makes both signatures `method(List)`, so bytecode signatures collide.
7. When callers are reasonably expected to recover and compile-time acknowledgment improves the API, e.g. a domain operation requiring explicit alternative handling.
8. Pass it as cause: `new DomainException("safe context", original)`; retain category/metadata.
9. `orElse` evaluates fallback eagerly; `orElseGet` invokes supplier only when empty.
10. Repository detects unique/idempotency conflict and returns/throws typed domain outcome; service compares request fingerprint; API maps semantic conflict to stable status/problem without leaking internals.
