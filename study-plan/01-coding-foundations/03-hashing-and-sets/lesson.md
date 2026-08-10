# Hashing and Sets — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `03-hashing-and-sets`  
**Expected study time:** 2–4 hours plus implementation and review

## 1. FOUNDATIONS

### The lookup problem

Given ten million processed request IDs, a service needs to decide whether an arriving ID has already been handled. Scanning all ten million values for every request is O(n) per decision. Keeping the values sorted enables O(log n) lookup but insertion into an array remains O(n), and maintaining order may be unnecessary. A **hash table** aims to convert a key directly into a small candidate location, making lookup, insertion and deletion expected O(1).

Hashing exists because direct addressing is usually impossible. If every possible 128-bit request ID had its own slot, the table would require `2^128` positions. A **hash function** maps the enormous key universe into a finite integer range. The table converts that hash into a **bucket index**. Different keys must sometimes map to the same bucket—the pigeonhole principle guarantees **collisions**—so a real design must store and compare colliding keys.

The idea predates modern programming languages. Hash tables emerged in 1950s computing as engineers sought faster symbol-table and dictionary lookup. The same abstraction now appears in compilers, caches, database hash joins, deduplication, routing, storage systems and interview algorithms.

Without sound hashing, correctness and performance both break. A poor key implementation can make an inserted value “disappear.” A collision attack can turn expected constant-time work into long chains. An oversized table wastes memory and slows iteration. A probabilistic filter treated as an exact set can incorrectly reject legitimate work. Senior engineers distinguish the mathematical abstraction, the concrete implementation, and the business correctness boundary.

### Terminology

A **map** associates each unique key with at most one value. A **set** stores unique elements and can be viewed as a map from element to a dummy marker. A **multiset** or bag tracks multiplicity, usually with a map from element to count. A **bucket** is a table position holding zero or more entries. **Capacity** is the bucket-array size; **size** is the number of entries. The **load factor** `α=size/capacity` measures density. **Rehashing/resizing** allocates a new bucket array and redistributes entries.

**Separate chaining** stores colliding entries in a per-bucket structure. **Open addressing** stores all entries in the table and probes alternative slots; linear probing, quadratic probing and double hashing define probe sequences. A **tombstone** marks a deleted open-addressed slot so searches are not broken. Java `HashMap` uses buckets with linked nodes and, under qualifying collision conditions, tree bins rather than textbook open addressing.

The **hash contract** in Java is: if `a.equals(b)` is true, `a.hashCode()==b.hashCode()` must also be true. Unequal objects may have equal hashes. Hash codes do not prove identity and are not cryptographic signatures. A **cryptographic hash** such as SHA-256 targets preimage and collision resistance; ordinary table hashing targets speed and distribution. Do not use `Object.hashCode()` for security, persistence identity or cross-process partition stability unless the exact contract guarantees it.

### Expected versus worst-case behavior

With reasonably distributed keys and controlled load, lookup examines a small number of entries and is expected O(1). Resizing makes insertion amortized O(1). The worst case can be O(n) if all keys collide, though Java implementations may treeify sufficiently large, eligible bins and improve those bin operations toward O(log n). This is an implementation detail with thresholds and comparability conditions, not permission to use pathological hashes.

Space is O(n) but overhead exceeds key/value payload: bucket array, references, entry objects, alignment and load-factor slack all matter. Measure with Java Object Layout or a heap profiler on the actual JDK.

## 2. CORE MECHANICS

### 2.1 From key to bucket

Suppose capacity is 16 and a mixed hash is 37. A simple index is `37 mod 16=5`; power-of-two tables can use bit masking after spreading high bits. If another key also selects bucket 5, equality checks distinguish it. Hash is a filter: equal hash narrows candidates, then `equals` decides the key.

For strings, Java computes a polynomial-style hash over UTF-16 code units under its documented formula. The exact integer may overflow; Java integer overflow wraps by two’s-complement arithmetic. Never infer security from a 32-bit hash: there are only about 4.29 billion possible values and infinitely many strings.

### 2.2 Equality and immutable keys

Consider a mutable key `(tenantId,requestId)` inserted into a map. If `requestId` changes and participates in `hashCode`, lookup computes a different bucket. The entry remains physically in its old bucket but can no longer be found normally. Prefer immutable records:

```java
record RequestKey(UUID tenantId, String requestId) {}
```

Java records generate component-based equality/hash code. Components themselves must have stable equality. An array component still uses array identity unless wrapped or compared deliberately.

### 2.3 Capacity, load factor and resizing

At capacity 16 and load factor 0.75, a resize is triggered around 12 entries. Lower load reduces collisions but uses more buckets. Higher load saves bucket memory but increases candidate work. Resizing is O(n) for that operation; across many insertions, geometric growth gives amortized O(1).

Pre-sizing can reduce resizes when n is known, but absurd over-sizing wastes memory and can affect iteration. Official `HashSet` documentation notes iteration is proportional to size plus backing capacity. Choose evidence-based sizing; do not copy a “double expected size” rule blindly across JDK versions and constructors.

### 2.4 Set operations

Membership, deduplication and intersection are natural set tasks. To intersect sets A and B, build a set from the smaller and probe values from the larger: expected O(|A|+|B|), O(min(|A|,|B|)) additional storage. If duplicates matter, a set is wrong; use counts.

For multiset intersection `[4,9,5,4]` and `[9,4,9,8,4]`, counts from the smaller are `{4:2,9:1,5:1}`. Scan the other: emit 9 and reduce to zero; emit 4 twice; extra 9 has no remaining count. Result has `[9,4,4]` in scan order.

### 2.5 Counting and grouping

Frequency maps turn values into counts:

```java
counts.merge(endpoint, 1L, Long::sum);
```

Use a wide count type if events can exceed `Integer.MAX_VALUE`. Grouping maps a derived canonical key to a list. For lowercase English anagrams, a 26-count vector avoids sorting, but a safe map key must implement content equality. `int[]` does not; encode the vector or wrap it. For general Unicode, sorting code points costs O(m log m) per word and has defined code-point rather than locale-collation semantics.

### 2.6 Complement lookup: Two Sum

At value x, seek `target-x` among earlier values. Check before insertion to avoid using the same index. For `[3,3]`, target 6: at index 0 seek 3, absent, insert `3→0`; at index 1 seek 3, find index 0. O(n) expected/O(n).

Subtraction can overflow int. Compute in long and only convert when within int range. The checked lab implementation demonstrates this boundary.

### 2.7 Prefix sums plus hashing

For subarray sum k, let prefix `P[j]` be sum before/through a position according to a fixed convention. A subarray ends at current position with sum k whenever an earlier prefix equals `currentPrefix-k`. Store frequencies because multiple earlier prefixes create multiple subarrays.

For `[3,4,7,2,-3,1,4,2]`, k=7, start with frequency `{0:1}`. At prefix 7, prior prefix 0 contributes `[3,4]`; at 14, prior 7 contributes `[7]`; later prefixes find two more, total 4. Use long prefixes/counts. Initial zero prefix is essential for subarrays starting at index 0.

### 2.8 Ordering variants

`HashMap` provides no iteration-order guarantee. `LinkedHashMap` maintains insertion order or optional access order; that supports an LRU cache by moving accessed entries and evicting the eldest. `TreeMap` orders by key with O(log n) operations and supports floor/ceiling/range queries. A comparator inconsistent with equals can produce surprising map/set semantics.

An LRU cache is not automatically thread-safe, distributed, durable or bounded by bytes. Entry count may poorly approximate memory. `LinkedHashMap`’s convenient implementation is appropriate for a single-JVM, lock-protected use case; production caches need concurrency, expiry, metrics and failure semantics.

### 2.9 Concurrent maps and atomic compound operations

`ConcurrentHashMap` supports concurrent access, but a sequence `if (!map.containsKey(k)) map.put(k,v)` is not atomic. Use `putIfAbsent`, `computeIfAbsent`, `compute` or an external protocol depending on semantics. Mapping functions should be short and must obey documented recursion/exception behavior.

Single-process atomicity does not deduplicate across pods. A database unique constraint or conditional write can establish one durable business winner. In-memory maps still need expiry/bounds or they leak memory.

### 2.10 Bloom filters

A Bloom filter uses m bits and k hash-derived positions. Insert sets all positions; lookup returning “definitely absent” is exact because any missing bit proves non-insertion. “Might be present” can be a false positive. Standard sizing is:

`m = -n ln(p)/(ln 2)^2`, `k = (m/n) ln 2`.

For n=10,000,000 and target false-positive p=1%, m≈95,850,584 bits≈11.43 MiB and k≈6.64, typically 7 hashes. An exact Java `HashSet` would use far more than raw key payload. A Bloom filter cannot enumerate keys and ordinary forms cannot safely delete. It is a front filter, not the source of truth.

### 2.11 Hashing for partitioning

Systems hash keys to partitions, but `hash % partitionCount` remaps most keys when the count changes. Consistent hashing or rendezvous hashing reduces remapping. Stable partitioning also requires a stable byte encoding and hash algorithm across languages. Java’s process-local object hash behavior is not a cross-system data contract.

Hot keys remain hot: hashing one customer with 40% of traffic assigns 40% to one partition. Salting can split load but complicates ordering and aggregation.

## 3. WORKED PROBLEMS

### Problem 1 — Two Sum with duplicates and overflow

**Statement.** Return two distinct indices summing to target for `[3,3]`, target 6, and explain int overflow handling.

**Solution.** Maintain earlier value→index. At index 0 no complement; insert 3→0. At index 1 complement is 3 and earlier index 0 exists, so return `(0,1)`. Check before insert ensures distinct indices. Compute `(long)target-value`; otherwise `Integer.MIN_VALUE-1` wraps. Expected O(n)/O(n).

**Mistake caught.** Inserting and then finding the same element, or using a set when indices are required.

### Problem 2 — Multiset intersection

**Statement.** Intersect `[4,9,5,4]` with `[9,4,9,8,4]`, retaining duplicate multiplicity.

**Solution.** Count smaller array. Emit a probed value only when remaining count is positive, then decrement/remove. Output `[9,4,4]` in second-array scan order. Expected O(n+m), O(min(n,m)).

**Mistake caught.** `HashSet` returns only `{4,9}` and loses multiplicity.

### Problem 3 — First unique event type

**Statement.** For `PAY,AUTH,PAY,CAPTURE,AUTH,REFUND`, return the first type occurring once.

**Solution.** First pass counts. Second pass preserves original order and returns CAPTURE, not REFUND. Expected O(n)/O(u). A `LinkedHashMap` can combine order and counts, but two simple passes are often clearer.

**Mistake caught.** Iterating `HashMap` and assuming encounter order.

### Problem 4 — Group anagrams

**Statement.** Group `eat, tea, tan, ate, nat, bat`.

**Solution.** Canonical sorted-code-point keys: aet→`eat,tea,ate`; ant→`tan,nat`; abt→`bat`. If each word length is m, total O(n·m log m), O(total text) output/storage. For only lowercase a–z, a 26-count key makes canonicalization O(m).

**Mistake caught.** Using mutable `int[]` directly as a map key; arrays use identity equality.

### Problem 5 — Count subarrays summing to 7

**Statement.** Count subarrays in `[3,4,7,2,-3,1,4,2]` with sum 7.

**Solution.** Keep prefix-frequency map beginning `{0:1}`. At each prefix p, add frequency of p−7, then increment p. This yields 4. Negative values prevent the usual positive sliding-window method. Expected O(n)/O(n).

**Mistake caught.** Storing only a set of prefix values loses multiple starts; omitting zero prefix loses ranges from index 0.

### Problem 6 — LRU trace

**Statement.** Capacity 2: `put(1,A), put(2,B), get(1), put(3,C), get(2)`.

**Solution.** After first puts, recency oldest→newest is 1,2. `get(1)` makes 2,1. `put(3)` evicts 2, leaving 1,3. Final get(2) misses. Hash map finds nodes expected O(1); linked order updates O(1). Space O(capacity).

**Mistake caught.** Evicting insertion-oldest rather than access-oldest.

### Problem 7 — Bloom filter sizing

**Statement.** Size a Bloom filter for 10M IDs at 1% false positives.

**Solution.** Substitute n=10,000,000, p=.01. `-n ln p/(ln2)^2≈95.85M bits`; divide by 8 and 1,048,576≈11.43 MiB. `k≈6.64`, choose 7. Insert and query use 7 bit positions. A positive result must be verified in exact storage; a negative can skip expensive lookup.

**Mistake caught.** Calling positive membership certain or comparing only against raw key bytes while ignoring exact-set overhead.

### Problem 8 — Top 100 endpoints

**Statement.** From 20M logs, return 100 endpoints with most 5xx responses.

**Solution.** Count endpoint only for 5xx: expected O(n), O(u). Maintain min-heap size 100 over u counts: O(u log 100), O(100) beyond map. Total expected O(n+u log100), O(u). Define deterministic tie ordering if output stability matters.

**Mistake caught.** Sorting raw logs or assuming heap iteration is ordered.

### Problem 9 — Cross-pod idempotency

**Statement.** Five service pods may receive the same `(tenant,idempotencyKey)`. Exactly one payment creation may commit.

**Solution.** A local concurrent set is insufficient because each pod has its own memory. Put a unique database constraint on `(tenant_id,idempotency_key)`. In one transaction, insert an idempotency row containing request hash/state and create payment; one insert wins, duplicates read the stored result. A retry with same key but different request hash returns conflict. Hashing can accelerate lookup, but database uniqueness establishes durable correctness.

**Mistake caught.** Treating `ConcurrentHashMap` or a probabilistic filter as a distributed exactly-once guarantee.

## 4. REAL-WORLD / APPLIED CONTEXT

### Java HashMap/HashSet

The Java SE API specifies expected constant-time `get` and `put` for `HashMap` assuming proper hash distribution, and notes iteration cost is proportional to capacity plus size. Default load factor is 0.75 in standard constructors. These contracts explain why an unnecessarily enormous capacity can hurt full iteration even when lookup is fast.

The included `HashingSetsLab.java` compiles and verifies duplicates, overflow-conscious complement lookup, multiset counts, prefix-frequency counting, Unicode anagram grouping, access-order LRU and Bloom-filter no-false-negative behavior for inserted values.

### Database hash joins

PostgreSQL can build a hash table for one join input and probe it with the other. Conceptually, build cost is O(n), probe O(m) expected, but real execution depends on memory, batches, skew and disk spilling. `EXPLAIN (ANALYZE, BUFFERS)` is required; asymptotic reasoning alone cannot predict page I/O or planner choice.

### Cassandra/Dynamo-style membership and partitioning

Storage engines use Bloom filters to avoid unnecessary disk reads when an SSTable definitely lacks a key. Distributed key-value systems hash partition keys to place data. These applications show two different roles: probabilistic membership reduces expensive I/O; partition hashing distributes ownership. Neither provides cryptographic integrity, and skew/capacity changes require explicit design.

## 5. COMPARISON TABLE

| Structure | Lookup | Insert/delete | Order/range | Extra characteristics | Best fit |
|---|---:|---:|---|---|---|
| Array scan | O(n) | middle O(n) | index order | minimal overhead, locality | few queries/small data |
| Sorted array | O(log n) | O(n) | excellent | compact, immutable batches | many reads, few writes |
| HashMap/HashSet | expected O(1) | expected amortized O(1) | none guaranteed | O(n) memory, key contract | exact membership/association |
| LinkedHashMap | expected O(1) | expected amortized O(1) | insertion/access order | extra links | ordered map, local LRU |
| TreeMap/TreeSet | O(log n) | O(log n) | sorted/range/floor | comparator correctness | dynamic ordered queries |
| Bloom filter | O(k hashes) | O(k hashes) | none/enumeration impossible | false positives, no false negatives under correct implementation | prefilter expensive exact lookup |
| BitSet direct domain | O(1) | O(1) | numeric bit order | universe-sized bits | dense bounded integer domain |

For 10M keys and 1% target Bloom false positives, the mathematical bit payload is about 11.43 MiB. A direct bitset for every 32-bit unsigned value needs 2³² bits=512 MiB, independent of how few keys are present.

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Equal objects with different hashes.** Violates map/set contract; equal keys may occupy/search different buckets.
2. **Mutable key fields.** Mutation after insertion changes lookup hash/equality and makes entries effectively unreachable.
3. **Arrays as content keys.** `new int[]{1,2}` does not equal another such array; use wrapper/canonical representation.
4. **Hash means unique.** Collisions are unavoidable; compare actual keys.
5. **Hash means secure.** Ordinary hash codes lack cryptographic properties and may be predictable.
6. **HashMap is ordered.** Iteration order is unspecified; use LinkedHashMap or TreeMap for an explicit contract.
7. **Set for multiset.** Duplicates disappear; store counts.
8. **Non-atomic check-then-put.** Concurrent threads can both pass; use atomic map operation or durable conditional write.
9. **Local dedupe across pods.** Memory is process-local; use shared durable uniqueness.
10. **Bloom positive is certain.** It means “possibly present”; verify in exact store.
11. **Unlimited dedupe map.** It becomes a memory leak; define TTL, maximum size and replay horizon.
12. **Ignoring load/capacity.** Too small resizes; too large wastes memory and can slow iteration.
13. **Counting in int forever.** High-volume counts/prefix sums overflow; use long and define overflow behavior.
14. **Hash partitioning removes skew.** One hot key remains one hot partition unless the key model changes.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the sections above.

- Hash narrows bucket; equality confirms key.
- Equal ⇒ same hash; same hash ⇏ equal.
- Prefer immutable keys; records help but component semantics still matter.
- Hash map/set: expected O(1), amortized insertion, O(n) space.
- Tree map/set: O(log n), sorted/range queries.
- LinkedHashMap: insertion or access order.
- Multiset = map value→count.
- Prefix-frequency: initialize zero prefix; store counts, not only membership.
- Concurrent map compound actions require atomic APIs.
- Cross-pod correctness needs durable conditional uniqueness.
- Bloom: negative definite, positive possible; `m=-n ln p/(ln2)^2`.
- Hashing does not guarantee security, stable cross-language partitions or balanced hot keys.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain why a Java key whose `equals` uses email but `hashCode` uses database ID is invalid; give a failing scenario.
2. Return the longest consecutive integer sequence in `[100,4,200,1,3,2,2]` in expected O(n).
3. Count pairs summing to 10 in `[1,9,1,9,5,5]`, counting index pairs.
4. Design a lowercase-English anagram key and analyze its time/space for 500,000 words of average length 12.
5. A Bloom filter holds 1M keys with 10 bits/key and optimal k. Approximate k and false-positive rate.
6. Compare `HashSet`, `TreeSet` and `LinkedHashSet` for 2M IDs when sorted export is required once daily but membership runs continuously.
7. Explain why `computeIfAbsent` does not make a cache distributed or protect against a process crash during value creation.
8. For prefix sums `[1,-1,1,-1]`, count zero-sum subarrays using frequencies.
9. A 32-partition topic uses `customerId` as key; one customer produces 45% of events. Explain why adding consumers cannot solve the maximum throughput after 32 consumers.
10. Specify safe idempotency-record fields and behavior for same key/same body, same key/different body, and in-progress retry.

## 9. CURATED RESOURCES

1. **Oracle Java SE API, `HashMap`, `HashSet`, `LinkedHashMap`, `TreeMap`, `ConcurrentHashMap`.** Exact complexity, ordering, null, synchronization and atomic-operation contracts.
2. **Java Language Specification and `Object.equals/hashCode` API contract.** Definitive equality requirements underlying all hashed collections.
3. **Cormen et al., *Introduction to Algorithms*, 4th ed., Chapter 11 “Hash Tables.”** Formal direct addressing, chaining, universal hashing and open addressing analysis.
4. **Sedgewick & Wayne, *Algorithms*, 4th ed., §3.4 “Hash Tables.”** Practical separate-chaining and linear-probing implementations with empirical trade-offs.
5. **Burton H. Bloom, “Space/Time Trade-offs in Hash Coding with Allowable Errors” (1970).** Original Bloom-filter construction and probabilistic motivation.
6. **Broder and Mitzenmacher, “Network Applications of Bloom Filters: A Survey.”** Adds real networking uses and false-positive design analysis.
7. **PostgreSQL documentation, `EXPLAIN` and planner join strategies.** Connects in-memory hash reasoning to hash joins, batching and measured plans.
8. **Amazon Dynamo paper, DeCandia et al., “Dynamo: Amazon’s Highly Available Key-value Store.”** Adds consistent hashing, virtual nodes and production distributed-key placement.
9. **Java Object Layout (OpenJDK JOL).** Measures actual bucket, reference and object overhead instead of assuming payload-only memory.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Complexity Analysis.** Expected, amortized and worst-case distinctions are essential to honest hash-table claims.
2. **Arrays and Strings.** Bucket arrays and canonical string keys rely on indexing, content and Unicode semantics.

### After

1. **Trees, Heaps and Tries.** These supply ordered, top-k and prefix alternatives when hashing cannot satisfy the query.
2. **Problem-Solving Patterns.** Complement lookup and prefix-frequency maps recur across array problems.
3. **Concurrency Basics.** Atomic map operations, visibility and compound invariants matter under multiple threads.
4. **Kafka Partitioning and Distributed Systems.** Stable hashing, skew and rebalancing become cross-node architecture concerns.
5. **Caching and Redis.** Hash maps motivate cache structure, while production caching adds eviction, consistency and remote failure.

---ANSWER KEY BELOW---

1. Equal emails can produce unequal ID-based hashes, so lookup with an equal email key searches another bucket and misses. Hash must derive from the same equality-significant fields; immutable normalized email may be the key.
2. Put values in a set. Start only when `x-1` is absent, then advance while present. Sequence 1,2,3,4 has length 4. Expected O(n)/O(n); duplicates do not extend length. Guard integer boundaries.
3. Process counts of earlier values. Each 1 sees prior 9 count and vice versa; final count is 2×2 for 1/9 plus `C(2,2)=1` for 5/5, total 5. Expected O(n)/O(u).
4. Use 26 integer counts encoded in an immutable content-equality key. Counting is O(total characters)=about 6M character visits; key construction has fixed 26 cost per word and groups/output require O(total words/text) storage.
5. Optimal `k≈(m/n)ln2=10×.693≈6.93`, use 7. False-positive `p≈(1-e^{-kn/m})^k≈(1-e^{-.7})^7≈0.0082`, about 0.82%.
6. HashSet is best for continuous membership; daily sorted export can copy and sort O(n log n). TreeSet pays O(log n) continuously to keep order. LinkedHashSet preserves insertion, not sorted order. Choose from measured workload; likely HashSet plus daily sort.
7. It coordinates only within one map/JVM under its API semantics. Other instances compute independently; a crash loses state and may leave external side effects. Durable shared state/idempotency is separate.
8. Prefixes: start frequency `{0:1}`. Running prefixes 1,0,1,0 contribute 0+1+1+2=4 zero-sum subarrays.
9. One partition carries at least 45% and is consumed sequentially by one group member. More than one consumer cannot share that partition concurrently; throughput is bounded by the hot partition. Re-key/salt with ordering trade-offs or isolate the customer.
10. Store tenant, key, request hash, status, resource/result reference or response, timestamps/expiry and optionally owner/version. Same hash returns stored/in-progress semantics; different hash returns conflict; in-progress retry polls/returns accepted or safely resumes under lease/state-machine rules.
