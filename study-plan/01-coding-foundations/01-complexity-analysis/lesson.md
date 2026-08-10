# Complexity Analysis — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `01-complexity-analysis`  
**Expected study time:** 2–4 hours for the first pass, plus practice and spaced review

## 1. FOUNDATIONS

### 1.1 The problem complexity analysis solves

Suppose two services both return the correct answer for 1,000 payment records. One checks every payment against every other payment; the other records previously seen transaction IDs in a hash table. On the sample, both may finish quickly. At 10 million records, the first attempts roughly 100 trillion pair checks, while the second performs roughly 10 million insertions/lookups. Correctness alone cannot tell us whether software will survive production scale. Complexity analysis gives us a machine-independent language for describing how resource demand grows as the input grows.

Before modern asymptotic analysis, programmers could time implementations, but a timing binds the conclusion to a processor, compiler, input distribution, runtime state and dataset size. Timing is still essential, but it answers “how fast was this implementation in this experiment?” Complexity answers a different question: “how does the amount of work or storage grow?” We need both.

The mathematical roots go back to the study of computability and resource-bounded computation. Donald Knuth popularized careful analysis of algorithms; the asymptotic notation itself was introduced in mathematics by Paul Bachmann and Edmund Landau and adapted into computer science. The motivation remains practical: compare algorithms without being distracted by constants that change across hardware, then measure the surviving candidates in the real environment.

Without this discipline, three failures are common. First, a solution works in development and collapses at production scale. Second, engineers optimize a harmless constant while missing a catastrophic growth rate. Third, teams make vague claims such as “hash maps are faster” without defining the operation, input size, worst case or memory cost.

### 1.2 Input size and the cost model

An **algorithm** is a finite, unambiguous procedure that transforms input into output. **Input size** is a variable describing how much input the algorithm receives. It is traditionally called `n`, but that name is not sacred. For a graph, use `V` vertices and `E` edges. For multiplying an `m × k` matrix by a `k × n` matrix, all three dimensions matter. For a string algorithm, `n` might mean Unicode code points rather than Java `char` values; define it.

A **cost model** decides which primitive operations count. In the RAM model used for interviews, arithmetic on machine-sized values, comparison, assignment and indexed array access are treated as constant time. This is an abstraction. Adding two arbitrary-precision 10-million-digit integers is not constant time. Reading a remote object is not comparable to reading an array cell. State exceptions when they matter.

**Time complexity** measures growth in the number of operations. **Space complexity** measures memory growth. **Auxiliary space** means extra working memory created by the algorithm, normally excluding the input and sometimes excluding the required output. Always state your convention. A recursive algorithm consumes call-stack space even if it allocates no explicit collection.

### 1.3 Asymptotic notation

Let `f(n)` be the actual work and `g(n)` a simpler growth function.

- `f(n) ∈ O(g(n))` means that beyond some input size, `f(n)` is at most a constant multiple of `g(n)`. Big-O is an asymptotic upper bound.
- `f(n) ∈ Ω(g(n))` means it is at least a constant multiple: a lower bound.
- `f(n) ∈ Θ(g(n))` means both: a tight asymptotic bound.

Formally, `f(n) ∈ O(g(n))` if there are positive constants `c` and `n₀` such that `0 ≤ f(n) ≤ c·g(n)` for every `n ≥ n₀`. For `f(n)=3n²+8n+20`, choose a sufficiently large `n`; `n²` eventually dominates. Therefore `f(n) ∈ Θ(n²)`. Saying only `O(n³)` is technically an upper bound but uninformative; interviewers expect the tightest useful bound.

Big-O does **not** automatically mean worst case. Worst, average, expected, best and amortized describe which executions are being analyzed; O/Ω/Θ describe bounds. We often say “O(n) worst-case time” as shorthand, but the dimensions are separate.

### 1.4 Cases, probability and amortization

**Worst-case complexity** is the maximum cost among inputs of size `n`. Linear search is Θ(n) worst case when the value is absent or last. **Best case** is Θ(1) when the first item matches. **Average case** requires a probability distribution over inputs; it cannot be asserted without one. **Expected complexity** averages over algorithmic randomness or an explicitly assumed distribution. Hash-table lookup is commonly expected O(1), but collision patterns and implementation defenses matter.

**Amortized analysis** spreads the cost of occasional expensive operations over a sequence, without assuming random inputs. A resizable array might double capacity. Appends usually write one element; a resize copies all existing elements. Across appending `n` elements, copied elements form a geometric series `1+2+4+...<2n`, so total work is O(n) and amortized append is O(1). It does not mean every append is constant time.

### 1.5 Common growth classes

For intuition, take `n=1,000,000`:

| Growth | Approximate operation count | Typical source |
|---|---:|---|
| O(1) | 1 | array index, stack top |
| O(log₂ n) | about 20 | binary search, balanced-tree height |
| O(n) | 1,000,000 | scan |
| O(n log₂ n) | about 20,000,000 | comparison sort |
| O(n²) | 1,000,000,000,000 | all pairs |
| O(2ⁿ) | impossibly large | naïve subset recursion |
| O(n!) | even faster explosion | enumerate all permutations |

These are growth counts, not timings. A comparison may cost far more than an integer addition. Nevertheless, growth dominates at sufficient scale.

### 1.6 Why complexity is not performance

Asymptotically better does not guarantee faster for every `n`. Constants, cache locality, branch prediction, allocation, JIT compilation, garbage collection, network I/O and data skew matter. A linear scan of a tiny contiguous array may beat a hash lookup. An O(n log n) library sort written in optimized runtime code may beat a theoretically O(n) method with huge allocation at modest sizes. Complexity narrows designs; profiling and benchmarking validate implementations.

On the JVM, a naïve loop benchmark is easily optimized away, polluted by warm-up, or distorted by dead-code elimination. OpenJDK’s Java Microbenchmark Harness (JMH) exists to manage warm-up, forks, measurement and result consumption. The small benchmark included beside this file is intentionally an illustrative local experiment, not a publication-quality JMH result.

## 2. CORE MECHANICS

### 2.1 Constant time

O(1) means the operation count is bounded independently of input size, not that it takes one CPU cycle.

```java
int last = values[values.length - 1];
```

The address is computed from base plus index offset. Whether the array has 10 or 10 million elements, one indexed access is performed. Boundary behavior matters: for an empty array, this throws. Checking emptiness is also O(1).

### 2.2 Sequential statements add

If one pass handles 4 million records and a second pass handles them again, the count resembles `4n + 7n + 12 = 11n+12`, which is Θ(n). We add sequential blocks and retain the dominant term.

```java
for (Payment p : payments) validate(p); // n
for (Payment p : payments) persist(p);  // n
```

This is Θ(n), not Θ(n²), because the loops are sequential, not nested. Operationally, two expensive remote operations per record can still be slow; complexity does not erase constants.

### 2.3 Independent nested loops multiply

```java
for (int i = 0; i < n; i++)
    for (int j = 0; j < n; j++) compare(i, j);
```

There are `n` inner iterations for each of `n` outer iterations: exactly `n²` comparisons. At `n=8,000`, that is 64 million iterations. Our local Java 25 run measured 78.990 ms for the included arithmetic body. At `n=4,000`, 16 million iterations took 21.789 ms. Doubling `n` multiplied operations by four and measured time by about 3.63; measurement noise and CPU effects explain why the timing ratio is not exactly four.

### 2.4 Dependent loop bounds require summation

```java
for (int i = 0; i < n; i++)
    for (int j = i; j < n; j++) work();
```

The inner counts are `n, n-1, ..., 1`. Their sum is `n(n+1)/2`, which is `(n²+n)/2`, hence Θ(n²). A triangular loop is still quadratic even though it performs about half as many iterations as a full square.

By contrast:

```java
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++) work();
```

performs `0+1+...+(n-1)=n(n-1)/2`, also Θ(n²). Edge case `n=0` performs zero work; asymptotic analysis concerns growth.

### 2.5 Geometric progress creates logarithms

```java
for (int size = 1; size < n; size *= 2) work();
```

After `k` iterations, `size=2ᵏ`. The loop stops when `2ᵏ ≥ n`, so `k=ceil(log₂ n)`. For `n=1,000,000`, about 20 iterations suffice. The logarithm base is omitted in Big-O because changing bases multiplies by a constant.

Boundary traps include integer overflow (`size *= 2` can become negative) and `n≤1`. Production code may use `size <= n/2` or a wider type.

### 2.6 Two pointers can make nested-looking code linear

```java
int right = 0;
for (int left = 0; left < n; left++) {
    while (right < n && acceptable(left, right)) right++;
}
```

It is wrong to multiply mechanically. `left` advances `n` times. If `right` never moves backward, it also advances at most `n` times over the entire execution. Total pointer movements are at most `2n`, so the traversal is O(n), assuming `acceptable` is O(1). This is an aggregate argument.

If `right` resets to `left` on every outer iteration, the analysis changes and may become quadratic. The monotonic invariant is the deciding fact.

### 2.7 Library-call costs are part of your algorithm

```java
for (String s : records) {
    Arrays.sort(s.toCharArray());
}
```

If there are `n` strings of average length `m`, conversion is O(m), sorting is O(m log m), and repeating gives O(n·m log m). Saying “one loop, O(n)” ignores the loop body.

Similarly, `list.contains(x)` is linear for an `ArrayList`; calling it for every element of another n-element list is O(n²). `HashSet.contains` is expected O(1), so building a set O(n) and probing n times is expected O(n), with additional memory.

### 2.8 Recursion: draw the call structure

For:

```text
T(n) = T(n-1) + O(1)
```

there are n levels, so time Θ(n), stack Θ(n).

Binary search has `T(n)=T(n/2)+O(1)=Θ(log n)`. Recursive stack is Θ(log n); iterative binary search uses Θ(1) auxiliary space.

Merge sort has two half-size calls plus linear merging:

```text
T(n)=2T(n/2)+cn
```

At each level, all merges total `cn`; there are `log₂ n` levels, so Θ(n log n). Typical array merge sort needs Θ(n) auxiliary storage and Θ(log n) call stack; be precise about implementation.

Naïve Fibonacci has `T(n)=T(n-1)+T(n-2)+O(1)`, exponential growth, and Θ(n) maximum stack depth. Total calls and simultaneous stack depth are different quantities.

### 2.9 Amortized dynamic-array growth

Starting at capacity 1 and doubling, appending 16 items triggers copies of 1, 2, 4 and 8 elements: 15 total copies plus 16 writes. For `n=2ᵏ`, total copies are `1+2+...+n/2=n-1`. Across n appends, fewer than 2n writes/copies occur, so amortized O(1).

Worst-case one append remains O(n). A latency-sensitive system may pre-size the array or avoid a resize on a critical path.

### 2.10 Space analysis and hidden storage

Iterating an array with two integers uses O(1) auxiliary space. Copying it uses O(n). A recursion of depth h uses O(h) stack. A breadth-first traversal of a binary tree can hold O(w) nodes where w is maximum width; in the worst case w=O(n). DFS stack is O(h), which is O(log n) for balanced trees but O(n) for a chain.

Views and slices need semantic care. A view may be O(1) to create but retain a large backing store; a copy is O(k) time and space. Java `String.substring` behavior changed historically, so analyze the actual target JDK rather than repeating folklore.

### 2.11 Multiple input dimensions

Comparing every user in list A (`m`) to every user in list B (`n`) is Θ(mn), not automatically O(n²). Merging two sorted arrays is Θ(m+n). Graph traversal with adjacency lists is Θ(V+E). For a dense directed graph, E may be Θ(V²), but preserving `V+E` communicates the representation and works for sparse inputs.

### 2.12 Lower bounds and choosing the right target

If an unsorted array may contain the target anywhere, any correct worst-case membership algorithm must inspect all n elements: Ω(n). Sorting first costs Ω(n log n) in the comparison model, so it is wasteful for one lookup but useful for many lookups or ordered queries. Comparison-based sorting has an Ω(n log n) lower bound in the general case; counting sort escapes it by using assumptions about a bounded integer range.

## 3. WORKED PROBLEMS

### Problem 1 — Count an exact loop

**Statement.** A cleanup job runs:

```java
for (int i = 0; i < n; i++)
    for (int j = i; j < n; j++) deleteCandidate(i, j);
```

Derive a tight time bound and count calls for `n=5`.

**Solution.** When `i=0`, j has 5 values. Then 4, 3, 2 and 1. Total `5+4+3+2+1=15`. Generally the sum is `n(n+1)/2`. Expand: `0.5n²+0.5n`; the quadratic term dominates, so Θ(n²). If `deleteCandidate` is not O(1), multiply by its cost.

**Mistake caught.** Saying `5²=25` because two loops exist. The final class is quadratic, but the exact count reflects dependent bounds.

### Problem 2 — Sequential versus nested database preparation

**Statement.** A batch validates n claims, hashes each in Θ(k) where k is average payload bytes, and then sorts all claims by timestamp. What is the time complexity?

**Solution.** Validation is Θ(n) if constant per claim. Hashing all payloads is Θ(nk). Comparison sorting is Θ(n log n), assuming timestamp comparisons are constant. Sequential costs add: Θ(n + nk + n log n)=Θ(nk+n log n). We cannot discard either `nk` or `n log n` without knowing how k grows. If k is bounded by a fixed maximum, this simplifies to Θ(n log n).

**Mistake caught.** Collapsing every problem to one variable or multiplying sequential phases.

### Problem 3 — Binary search iterations

**Statement.** A sorted array contains 10,000,000 model IDs. How many iterations can iterative binary search require, and what are time and space bounds?

**Solution.** Each comparison halves the remaining range. `ceil(log₂ 10,000,000)` is 24 because `2²³=8,388,608` and `2²⁴=16,777,216`. Thus at most about 24 range reductions/comparisons, depending on exact loop convention. Time Θ(log n), auxiliary space Θ(1). A recursive implementation has Θ(log n) stack.

**Mistake caught.** Claiming O(1) because 24 is small. It grows logarithmically; for this concrete n it happens to be 24.

### Problem 4 — ArrayList append amortization

**Statement.** A dynamic array begins with capacity 1 and doubles when full. Count element copies while appending 1,024 elements and derive amortized complexity.

**Solution.** Resizes copy capacities `1+2+4+...+512`. This geometric sum is `1024-1=1,023` copied elements. There are also 1,024 writes of new elements. Total relevant element operations are below 2,048, or fewer than 2 per append on average. Therefore n appends take Θ(n), amortized Θ(1) per append. The append that triggers the 512→1024 resize is Θ(512), so worst-case individual append is Θ(n).

**Mistake caught.** Calling append worst-case O(1), or calling every append O(n).

### Problem 5 — A nested while loop that is linear

**Statement.** Analyze removal of duplicates from a sorted array:

```java
int write = 0;
for (int read = 0; read < n; read++) {
    while (read + 1 < n && a[read] == a[read + 1]) read++;
    a[write++] = a[read];
}
```

**Solution.** Although a while loop appears inside a for loop, `read` never decreases. Both the `for` update and while body advance the same pointer. Across the whole execution, it advances from 0 to n, at most n steps; writes are at most n. Time Θ(n), auxiliary space Θ(1). For an all-equal array, the while performs n−1 advances and the outer body once. For all distinct values, while never advances and the outer loop executes n times. Both are linear.

**Mistake caught.** Mechanically multiplying loop counts.

### Problem 6 — Top 100 failing endpoints

**Statement.** From 20 million request records containing endpoint and status, return the 100 endpoints with the most 5xx responses. Let u be distinct endpoints.

**Solution.** Scan records. For each 5xx, increment its endpoint in a hash map: expected Θ(n) time and Θ(u) memory. Iterate u frequency entries while maintaining a min-heap of size at most 100. Each offer/poll is O(log 100), so Θ(u log 100), effectively linear in u but write the exact expression. Total expected Θ(n+u log 100), space Θ(u+100). Sorting all u counts would cost Θ(u log u). If u counts do not fit memory, hash-partition records, aggregate each partition, and merge partition candidates; approximate heavy-hitter algorithms are another trade-off with explicit error.

**Mistake caught.** Sorting 20 million raw records or calling heap traversal sorted.

### Problem 7 — Graph traversal

**Statement.** A deployment graph has V services and E dependency edges stored as adjacency lists. Analyze DFS cycle detection, including stack space.

**Solution.** Each vertex changes state a constant number of times. Each adjacency entry is examined once for a directed graph, so Θ(V+E) time. State and parent arrays use Θ(V). Recursive call depth can reach V in a chain, so auxiliary space is Θ(V). In a dense graph E approaches V²; in a sparse service graph it may be close to V. If stored as an adjacency matrix, scanning all possible neighbors makes traversal Θ(V²) even when few edges exist.

**Mistake caught.** Saying simply O(n), omitting E and representation.

### Problem 8 — Naïve Fibonacci versus memoization

**Statement.** Compare recursive `fib(n)=fib(n-1)+fib(n-2)` with a memoized implementation.

**Solution.** The naïve recursion branches and recomputes values. Its recurrence is `T(n)=T(n-1)+T(n-2)+O(1)`, growing Θ(φⁿ), often loosely written O(2ⁿ), where φ≈1.618. Maximum call depth is n, so stack Θ(n), not exponential. Memoization computes each state 0..n once; each does constant work, so Θ(n) time and Θ(n) memo plus stack. Bottom-up iteration is Θ(n) time and can retain only two previous values, Θ(1) auxiliary space.

For `n=50`, naïve recursion entails tens of billions of calls; iterative computation performs about 49 additions.

**Mistake caught.** Equating total calls with simultaneous memory, or saying memoization is O(1) because map lookup is expected O(1) while ignoring n states.

### Problem 9 — Many queries change the best design

**Statement.** You receive an unsorted list of 1 million transaction IDs and then q membership queries. Compare scanning per query, sorting once plus binary search, and building a hash set.

**Solution.** Scanning costs Θ(qn), O(1) extra space. Sorting costs Θ(n log n) once and Θ(q log n) queries, with sorting space implementation-dependent. Hash construction is expected Θ(n), queries expected Θ(q), and memory Θ(n). For one query, scanning may be simplest and can beat construction constants. For 1 million queries, scanning is infeasible; sorting enables ordered/range operations, while hashing usually gives faster exact membership at higher memory and without ordering. The requirement, not a slogan, selects the design.

**Mistake caught.** Declaring hash tables universally best without query count, ordering needs or memory budget.

## 4. REAL-WORLD / APPLIED CONTEXT

### 4.1 Java collection contracts

Java’s `PriorityQueue` official API documents O(log n) for enqueue/dequeue, O(n) for `contains(Object)` and `remove(Object)`, and O(1) for `peek`, `element` and `size`. This matters in production: using `contains` inside a loop over n items turns a seemingly heap-based design into O(n²). Also, iterating a priority queue is not guaranteed to be sorted; ordered extraction requires repeated `poll` at O(n log n) or copying and sorting.

Oracle’s collection guidance distinguishes `HashSet` expected constant-time operations from `TreeSet` logarithmic operations, while noting `HashSet` iteration is proportional to entries plus table capacity. Over-sizing a `HashSet` can therefore hurt iteration even when membership remains expected O(1).

### 4.2 Local measured dataset

`ComplexityBenchmark.java` beside this document was run on 2026-08-09 with Java 25 on macOS ARM64. After five warm-up rounds, it reported:

| Input | Linear integer scan | Repeated binary search |
|---:|---:|---:|
| 100,000 | 0.150 ms/scan | 27.0 ns/search |
| 1,000,000 | 1.315 ms/scan | 30.0 ns/search |
| 10,000,000 | 16.117 ms/scan | 37.7 ns/search |

Quadratic arithmetic loops took 5.447 ms at n=2,000, 21.789 ms at n=4,000 and 78.990 ms at n=8,000. The important observation is the growth shape, not transferability of nanoseconds. The benchmark uses a volatile sink and warm-up but not JMH forks/statistical reporting. CPU frequency, thermal state and JIT decisions can change numbers. Re-run with:

```bash
javac ComplexityBenchmark.java
java ComplexityBenchmark
```

For trustworthy JVM microbenchmarks, use OpenJDK JMH.

### 4.3 Database and distributed-system cost

Complexity analysis extends beyond in-memory algorithms. A nested-loop join can approach O(mn) comparisons; an indexed lookup may reduce the search component toward O(log n), though database cost includes pages, selectivity and I/O. Kafka partition processing is O(number of records processed), but per-key skew makes aggregate `n` misleading: one hot partition can dominate wall time. Senior engineers name the controlling dimension—rows, pages, events, partitions, payload bytes or network round trips—rather than writing O(n) without a model.

## 5. COMPARISON TABLE

| Goal / approach | Build cost | Per-operation cost | Extra space | Concrete scale at n=1,000,000 | Use when |
|---|---:|---:|---:|---:|---|
| Linear scan | none | Θ(n) | O(1) | up to 1,000,000 comparisons/query | few queries, unsorted data, minimal memory |
| Sort + binary search | Θ(n log n) | Θ(log n) | depends on sort | ~20 comparisons/query after sort | many queries plus ordering/ranges |
| Hash set | expected Θ(n) | expected O(1) | Θ(n) | ~1,000,000 stored keys | many exact-membership queries, memory available |
| Balanced tree | Θ(n log n) incremental | Θ(log n) | Θ(n) | ~20 tree levels | ordered queries and dynamic updates |
| Full sort for top-k | Θ(n log n) | — | sort-dependent | ~20M comparison scale | need all items ordered |
| Size-k heap for top-k | Θ(n log k) | — | Θ(k) | k=100 → ~6.64 levels per update | only k extremes needed |
| Recursive DFS | Θ(V+E) | — | O(height), worst O(V) | chain of 1M risks stack failure | concise, bounded depth |
| Iterative DFS/BFS | Θ(V+E) | — | O(V) worst | explicit heap storage | adversarial depth; BFS for unweighted shortest paths |
| Memoized Fibonacci | Θ(n) | — | Θ(n) | 1M states stored | need cached states/reconstruction |
| Bottom-up rolling Fibonacci | Θ(n) | — | Θ(1) | two prior values | need only final value |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Big-O means worst case.”** `HashMap.get` may be discussed as expected O(1); the O notation is a bound, while “expected” identifies the case. State both.
2. **“Two loops means O(n²).”** Two sequential scans are O(n); monotonic two pointers are O(n); only count actual total iterations.
3. **Ignoring the body.** Calling O(n) `contains` inside an n loop is O(n²), not O(n).
4. **Dropping variables prematurely.** Θ(mn) does not become Θ(n²) unless m and n are linked.
5. **Confusing total recursion calls with stack.** Naïve Fibonacci has exponential time but linear maximum depth.
6. **Calling amortized O(1) a worst-case guarantee.** Dynamic-array resize is individually O(n).
7. **Forgetting output size.** Returning every pair among n items inherently creates Θ(n²) output; no algorithm can run asymptotically faster than writing its output.
8. **Treating hashes as magic.** Expected O(1) lookup costs memory and depends on hashing/collisions; ordered/range queries remain poor.
9. **Assuming lower asymptotic growth wins at tiny n.** `1000n` loses to `n²` until n exceeds roughly 1000. Measure relevant sizes.
10. **Benchmarking JVM code with one timestamp.** Warm-up, dead-code elimination and GC invalidate naïve conclusions. Use JMH for serious claims.
11. **Ignoring integer overflow.** `mid=(low+high)/2` and doubling loops can overflow; use `low+(high-low)/2` and guarded growth.
12. **Saying “space O(1)” for recursion.** Call frames count. Tail-call optimization is not guaranteed by Java.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the sections above.

- Define variables first: n, m, V, E, payload length k.
- Sequential phases add; nested independent repetitions multiply.
- `1+2+...+n = n(n+1)/2 = Θ(n²)`.
- Halving/doubling: Θ(log n).
- Monotonic pointer total movement often proves Θ(n).
- Sort: generally Θ(n log n) comparison time.
- Hash lookup: expected O(1); tree lookup: O(log n); scan: O(n).
- Heap top-k: O(n log k), O(k).
- BFS/DFS adjacency list: O(V+E); matrix: O(V²).
- Recurrence: one half → log n; two halves + linear merge → n log n.
- Recursion space = maximum depth.
- Dynamic-array append: amortized O(1), worst single append O(n).
- Say average/expected/amortized/worst separately from O/Θ.
- Big-O predicts growth; benchmarks measure implementations.

## 8. PRACTICE SET FOR SELF-TEST

Do these without viewing the answer key. For each, write the variables, tight time, auxiliary space and one boundary condition.

1. A loop runs `for (i=n; i>0; i/=3)`. What is its time complexity, and what happens when n=0?
2. Analyze `for i=0..n-1; for j=0..m-1`. Do not assume m=n.
3. An algorithm creates every length-3 combination from n distinct IDs. Derive the output count and time lower bound.
4. A recursive tree algorithm visits each node once but concatenates immutable strings of length proportional to depth at every node. Is O(n) always valid? Analyze a chain.
5. You must answer 10 membership queries over an unsorted array of 50 integers, then discard it. Compare scan versus building a set.
6. A service processes 12,000 events distributed across 24 partitions, but one partition holds 6,000 events. If each partition is processed sequentially and 24 workers run in parallel, what dimension controls completion time?
7. Give time and space for merge sort on an array and explain why time is not O(log n).
8. A size-n loop calls `PriorityQueue.contains`. Give complexity using the Java API contract.
9. A BFS runs on a graph with 1 million vertices and 2 million directed edges in adjacency lists. Give asymptotic time/space and a concrete upper-scale count of adjacency entries examined.
10. Explain the flaw in: “Binary search is O(1) because a 64-bit key needs at most 64 comparisons.”

## 9. CURATED RESOURCES

1. **Cormen, Leiserson, Rivest and Stein, *Introduction to Algorithms*, 4th edition, Chapters 2–4 and 11.** Adds formal asymptotic definitions, recurrence methods, probabilistic analysis and hashing beyond this interview-oriented treatment.
2. **Sedgewick and Wayne, *Algorithms*, 4th edition, §1.4 Analysis of Algorithms.** Adds the doubling-ratio experimental method that connects mathematical models to measured running time.
3. **Robert Sedgewick and Kevin Wayne, Princeton Algorithms, Part I, lecture “Analysis of Algorithms.”** Adds visual growth models and empirical order-of-growth experiments.
4. **Donald E. Knuth, *The Art of Computer Programming*, Volume 1, §1.2.11 and related analysis sections.** Adds historically influential, precise treatment of algorithm analysis and mathematical tools.
5. **Thomas H. Cormen et al., “The Master Theorem” treatment in CLRS Chapter 4.** Adds a systematic method for many divide-and-conquer recurrences; learn after recursion trees.
6. **Oracle Java SE 21 API: `java.util.PriorityQueue`.** Adds exact implementation complexity contracts—logarithmic enqueue/dequeue, linear object search, constant head access—that should govern Java code reviews.
7. **Oracle Java Collections Framework Overview and implementation tutorials.** Adds official distinctions between resizable-array, hash-table, tree, linked and concurrent implementations, including operational caveats.
8. **OpenJDK, Java Microbenchmark Harness (JMH) project and `jmh-samples`.** Adds correct JVM benchmark structure for warm-up, forks, modes, state and avoiding dead-code elimination.
9. **Jon Bentley, *Programming Pearls*, 2nd edition, Chapters 1–5.** Adds concrete examples where reformulating the problem changes both complexity and implementation simplicity.
10. **Jeff Erickson, *Algorithms*, Chapter 0 and recursion chapters (freely available textbook).** Adds detailed recurrence-tree reasoning and proof techniques.

## 10. RELATED TOPICS BRIDGE

### Immediately before

1. **Basic Java syntax and execution model.** You need to recognize loops, method calls, arrays, objects and recursion before you can count their operations.
2. **Elementary algebra and logarithms.** Sums, powers and logarithms are the language used to derive triangular loops and halving behavior.
3. **Problem constraints and requirements.** Complexity only becomes actionable after identifying input dimensions, latency limits, memory budget and operation mix.

### Immediately after

1. **Arrays and Strings.** This is the first place to apply indexing, scan, copy and nested-loop analysis to real Java solutions.
2. **Hashing and Sets.** Complexity explains why trading O(n) memory for expected O(1) membership can remove repeated linear scans.
3. **Trees, Heaps and Graphs.** Their height, edges and frontier sizes introduce multi-variable and logarithmic analysis.
4. **Problem-Solving Patterns.** Sliding windows, two pointers and binary search depend on proving a monotonic invariant and total pointer movement.
5. **Benchmarking and profiling.** After asymptotic screening, JMH and profilers determine constants and real bottlenecks on the JVM.

---ANSWER KEY BELOW---

1. Θ(log₃ n) for positive n because division by 3 reaches zero logarithmically; for n=0 the loop executes zero times. Guard against a negative-input interpretation.
2. Θ(nm) time and O(1) auxiliary space if the body and loop variables are constant-space.
3. `C(n,3)=n(n-1)(n-2)/6=Θ(n³)` outputs, so any explicit-output algorithm is Ω(n³) time and output space Θ(n³).
4. No. In a chain, depths are 1..n and immutable concatenation can copy Θ(depth) characters at each node; sum is Θ(n²). A mutable builder/backtracking strategy may reduce copying depending on required output.
5. Scanning is at most 500 comparisons and O(1) space; building a set is expected O(50) plus 10 lookups but has allocation/hash overhead. For these tiny, disposable inputs, scanning is defensible; measure if it is hot code.
6. The maximum per-partition load controls parallel completion. The hot partition requires processing 6,000 sequential events even though average is 500; asymptotic total O(n) hides skew and wall-clock critical path.
7. Θ(n log n) time: log n levels, Θ(n) total merging each level. Typical array implementation uses Θ(n) auxiliary array plus Θ(log n) stack. It is not O(log n) because each level processes all n elements.
8. `PriorityQueue.contains(Object)` is O(n); called n times gives O(n²).
9. Θ(V+E) time and Θ(V) visited/queue worst-case space. About 2 million directed adjacency entries are examined, plus vertex handling.
10. It treats the universe size as a fixed constant instead of the collection size and conflates key bit width with search steps. For arrays up to a fixed 64-bit addressable maximum, one can make a theoretical constant-universe argument, but algorithm analysis uses scalable n; binary search is Θ(log n), and a 64-bit key’s value width does not determine array length.
