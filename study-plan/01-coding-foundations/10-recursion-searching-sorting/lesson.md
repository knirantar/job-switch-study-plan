# Recursion, Searching, and Sorting from Scratch

Parent subject: `01-coding-foundations`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why these three ideas belong together

Searching asks where an item is. Sorting arranges items so later work becomes easier. Recursion solves a problem by solving smaller instances of the same problem. Together they form a bridge from basic loops to algorithmic reasoning: binary search relies on order and repeatedly discards half of a search range; merge sort recursively divides data and merges ordered results; quicksort partitions data and recursively processes the parts.

Humans have sorted and indexed information for centuries because organization reduces future retrieval cost. A phone book sorted by surname supports directed search; an unsorted pile requires inspection one entry at a time. Computer science formalized these trade-offs as data volumes grew. Without reliable searching and sorting, database indexes, log processing, scheduling, ranking, and deduplication would repeatedly scan entire datasets.

### Sequence, order, key, and comparator

A **sequence** is an ordered collection whose elements have positions. Sorting changes the sequence so it obeys an ordering relation. A **key** is the property used for ordering, such as a transaction timestamp. A **comparator** decides whether one element is less than, equal to, or greater than another.

A valid comparator must be consistent enough to define order. **Antisymmetry** means if `a < b`, then `b > a`. **Transitivity** means if `a < b` and `b < c`, then `a < c`. A comparator based on `a - b` can overflow: comparing `Integer.MAX_VALUE` to `-1` produces an incorrect sign. Java code should use `Integer.compare(a, b)`.

A sort is **stable** when equal-key elements retain their original relative order. Given claims `(A,100)`, `(B,50)`, `(C,100)`, stable sorting by amount produces B, A, C; A remains before C. Stability matters when applying multiple sort keys or preserving event arrival order.

An algorithm is **in-place** when it uses only small auxiliary storage relative to input, though definitions sometimes permit a recursion stack. An **adaptive** sort benefits from existing order. A comparison sort learns order only through comparisons; such general algorithms have an Ω(n log n) worst-case comparison lower bound.

### Searching

**Linear search** examines elements until it finds a match or exhausts input. It needs no ordering and works on streams. In the worst case it performs `n` comparisons.

**Binary search** requires sorted data and random access. It maintains a candidate interval, compares the middle element, and discards the impossible half. With one million elements it needs at most about 20 halving steps because `2^20 = 1,048,576`. This speed is purchased with a prerequisite: maintaining sorted order or a suitable index.

### Recursion and the call stack

A recursive function calls itself on a smaller problem. It needs a **base case**, which answers a smallest instance without recursion, and a **recursive case**, which reduces the problem. Each active call has a **stack frame** containing parameters, local variables, and a return location. Frames use finite memory; too much depth causes Java `StackOverflowError`.

For factorial, `5! = 5 × 4 × 3 × 2 × 1 = 120`. A recursive definition is `factorial(n) = n × factorial(n-1)`, with `factorial(0)=1`. The base case is not an optimization: without it the computation never terminates normally. In production Java, a loop is safer for simple linear recursion because Java does not guarantee tail-call elimination.

### Correctness through invariants and induction

Iterative algorithms use loop invariants. Recursive correctness is commonly argued by induction: prove the base case, assume the smaller call is correct, then show the current call combines it into a correct answer. Binary search maintains the invariant: if the target exists, it is within `[low, high]`. Sorting algorithms maintain order properties during insertion, selection, partitioning, or merging.

## 2. CORE MECHANICS

### 2.1 Linear search

```java
static int linearSearch(String[] ids, String target) {
    for (int i = 0; i < ids.length; i++) {
        if (java.util.Objects.equals(ids[i], target)) return i;
    }
    return -1;
}
```

For `['TX-91','TX-14','TX-87','TX-22']` and target `TX-87`, comparisons occur at indices 0, 1, then 2, so the result is 2. The best case takes one comparison; worst case takes four. Empty input returns −1. Decide explicitly whether null elements and a null target are valid; `Objects.equals` treats two nulls as equal.

### 2.2 Binary search and safe midpoint arithmetic

```java
static int binarySearch(long[] sorted, long target) {
    int low = 0, high = sorted.length - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (sorted[mid] < target) low = mid + 1;
        else if (sorted[mid] > target) high = mid - 1;
        else return mid;
    }
    return -1;
}
```

For `[4,11,19,28,37,49,63,78]`, target 49: range 0–7 gives mid 3 (28), so low becomes 4; range 4–7 gives mid 5 (49), return 5. `low + (high-low)/2` avoids the overflow risk of `(low+high)/2`.

Duplicates require a contract. “Find any match” is above. For the first occurrence, store the match and continue left, or use a **lower bound**: the first index whose value is at least the target.

```java
static int lowerBound(int[] a, int target) {
    int low = 0, high = a.length; // half-open [low, high)
    while (low < high) {
        int mid = low + (high - low) / 2;
        if (a[mid] < target) low = mid + 1;
        else high = mid;
    }
    return low;
}
```

For `[2,5,5,5,9]` and 5, this returns 1. For 7, it returns insertion position 4. For 10, it returns length 5. Half-open intervals make “not present but insertion point exists” natural.

### 2.3 Recursion mechanics

```java
static long factorial(int n) {
    if (n < 0) throw new IllegalArgumentException();
    if (n <= 1) return 1;
    return Math.multiplyExact(n, factorial(n - 1));
}
```

`factorial(4)` creates frames for 4, 3, 2, 1. The last returns 1; results unwind as 2, 6, 24. `20!` fits in `long`; `21!` does not and `multiplyExact` detects overflow. The depth is O(n). A recursive traversal of a balanced tree has O(log n) depth, while a degenerate chain has O(n).

### 2.4 Insertion sort

Insertion sort grows a sorted prefix. For each position, save its value, shift larger prefix values right, and insert it.

For `[37,11,28,4]`: start `[37]`; insert 11 → `[11,37,28,4]`; insert 28 → `[11,28,37,4]`; insert 4 → `[4,11,28,37]`. The invariant is that indices `0..i-1` are sorted before iteration `i`.

It is stable if equal elements are not moved past each other, in-place, O(n²) worst case, and O(n) on already sorted data with the standard condition. It performs well for small or nearly sorted ranges; production hybrid sorts use insertion sort for small partitions.

### 2.5 Selection sort

Selection sort repeatedly finds the minimum remaining value and swaps it into position. For `[37,11,28,4]`, minimum 4 swaps with 37 → `[4,11,28,37]`; the remaining suffix is already ordered. It always makes roughly `n(n-1)/2` comparisons but at most `n-1` swaps. It is usually unstable. Its low write count can matter on storage where writes are expensive, but it is rarely a default library choice.

### 2.6 Merge sort

Merge sort splits until subarrays contain one element, then merges sorted halves. Merge `[4,37]` and `[11,28]`: compare 4/11 → 4; 37/11 → 11; 37/28 → 28; append 37, producing `[4,11,28,37]`.

Each level processes n elements and there are log₂n levels, so time is O(n log n). Conventional array merge sort uses O(n) auxiliary memory and is stable. Linked-list merge sort can relink nodes with small auxiliary storage.

### 2.7 Quicksort and partitioning

Quicksort selects a pivot, partitions smaller/equal/larger regions, then recursively sorts partitions. For `[37,11,28,4]` using 28 as pivot, a valid partition is `[11,4] [28] [37]`. Expected time is O(n log n); repeatedly poor pivots cause O(n²) and O(n) recursion depth. Randomization or introspective fallback mitigates this.

Partition boundaries are a rich source of bugs. State the precise scheme—Lomuto, Hoare, or three-way—and do not mix their return semantics. Three-way partitioning is valuable with many duplicates.

### 2.8 Java library behavior

Use library sorts in production unless an algorithm implementation is the task. `Arrays.sort(int[])` sorts primitive arrays with an implementation optimized for primitives; `Arrays.sort(Object[])` is stable. `List.sort` is stable by contract. Comparator chains express multiple keys:

```java
claims.sort(java.util.Comparator
    .comparingLong(Claim::amountPaise)
    .thenComparing(Claim::submittedAt)
    .thenComparing(Claim::id));
```

Explicit tie-breakers make pagination deterministic. Sorting only by a non-unique timestamp can move records between pages.

## 3. WORKED PROBLEMS

### Problem 1 — Linear incident lookup (easy)

Find `INC-1048` in `[INC-1002, INC-1048, INC-1031]`.

**Solution.** Compare index 0: no. Index 1: yes, return 1. Time is O(n) worst case, O(1) extra space. No preprocessing is justified for a one-off scan of three unsorted items.

**Trap:** applying binary search to unsorted data.

### Problem 2 — Binary search trace (easy)

Find 63 in `[4,11,19,28,37,49,63,78]`.

**Solution.** low 0, high 7, mid 3 → 28 < 63, low 4. Mid 5 → 49 < 63, low 6. Mid 6 → 63, return 6. Three comparisons.

**Trap:** updating `low=mid`, which can stop progress.

### Problem 3 — First eligible timestamp (medium)

For sorted epoch seconds `[100,120,120,120,180,240]`, find the first timestamp at least 120.

**Solution.** Use lower bound over `[0,6)`. Mid 3 is 120, high 3. Mid 1 is 120, high 1. Mid 0 is 100, low 1. Return 1. This solves both equality and insertion position.

**Trap:** returning the first equal value encountered, which may be index 3.

### Problem 4 — Recursive directory size (medium)

A tree has root files 10 MB and 5 MB, child A with 20 MB, and child B with 7 MB plus child C with 8 MB. Compute recursively.

**Solution.** Define size(node) as local bytes plus the sizes of children. Leaves: A=20, C=8. B=7+8=15. Root=10+5+20+15=50 MB. Base case is a node with no child directories. Each node is visited once.

**Trap:** omitting local files on non-leaf directories.

### Problem 5 — Insertion-sort trace (medium)

Sort `[45,12,12,90,3]` stably.

**Solution.** Insert 12 into `[45]` → `[12a,45,...]`; insert second 12 by shifting only values strictly greater, yielding `[12a,12b,45,...]`; insert 90 unchanged; insert 3 by shifting 90,45,12b,12a → `[3,12a,12b,45,90]`. Stability is preserved.

**Trap:** shifting on `>=`, which reverses equal elements.

### Problem 6 — Choose a sort (medium)

Sort 50 million fixed-width audit records on disk with only 1 GB free RAM.

**Solution.** An in-memory comparison sort is unsuitable. Use external merge sort: read chunks that fit memory, sort each run, write runs, then k-way merge streams. If each record is 100 bytes, data is about 5 GB before overhead; perhaps create ten 500 MB runs, leaving working memory for objects/buffers. The merge is sequential I/O friendly.

**Trap:** choosing quicksort based only on average CPU complexity.

### Problem 7 — Comparator overflow (hard)

Explain the result risk in `(a,b) -> a.priority() - b.priority()` for priorities `Integer.MAX_VALUE` and `-10`.

**Solution.** Mathematical difference is 2,147,483,657, beyond int max, so it wraps negative and incorrectly reports the maximum value as smaller. Use `Comparator.comparingInt(Item::priority)` or `Integer.compare`.

**Trap:** believing subtraction is always a valid three-way comparison.

### Problem 8 — Recursion explosion (hard)

Why is naive Fibonacci slow, and how do you fix it?

**Solution.** `fib(n)=fib(n-1)+fib(n-2)` recomputes overlapping subproblems; its call count grows exponentially (approximately φⁿ). Memoization stores each result for O(n) time and O(n) space; an iterative two-variable solution uses O(n) time and O(1) auxiliary space. For `fib(50)`, naive recursion entails billions of calls, while iteration performs 49 additions.

**Trap:** assuming recursion itself implies logarithmic or linear time.

### Problem 9 — Deterministic database pagination (hard)

Ten claims can share the same `created_at`. Why is `ORDER BY created_at LIMIT 20` unsafe for page boundaries?

**Solution.** Equal timestamps have unspecified relative order, so executions may move records across pages. Sort by a unique total order such as `ORDER BY created_at, claim_id`. For keyset pagination request rows after `(last_created_at,last_claim_id)` with the matching composite predicate and index.

**Trap:** treating a non-unique sort key as deterministic.

## 4. REAL-WORLD / APPLIED CONTEXT

### Database B-trees and directed search

PostgreSQL B-tree indexes keep keys ordered and support equality and range queries. A tree index reduces the number of pages examined compared with scanning all table pages, though real cost includes caching and I/O. Binary search is not literally the whole B-tree algorithm, but its central idea—use order to eliminate large regions—carries directly.

### TimSort in production runtimes

Tim Peters designed TimSort for Python by exploiting existing ordered runs and merging them. Java's object sorting uses a stable, adaptive merge-derived implementation. Real datasets commonly contain partial order; adaptiveness makes the best behavior materially better than treating input as random. Python documents sort stability, enabling multi-pass sorts.

### External merge sort in data platforms

MapReduce-style systems sort intermediate key/value data before grouping. When input exceeds memory, sorted runs are spilled and merged. Sorting 5 GB of audit records with 1 GB RAM is therefore a storage/I/O design, not just a choice between classroom in-memory algorithms.

## 5. COMPARISON TABLE

| Algorithm | Best | Average | Worst | Extra space | Stable | Practical use |
|---|---:|---:|---:|---:|---|---|
| Linear search | O(1) | O(n) | O(n) | O(1) | n/a | Unsorted or one-pass data |
| Binary search | O(1) | O(log n) | O(log n) | O(1) iterative | n/a | Sorted random-access data |
| Insertion sort | O(n) | O(n²) | O(n²) | O(1) | Yes | Small/nearly sorted ranges |
| Selection sort | O(n²) | O(n²) | O(n²) | O(1) | Usually no | Teaching; unusually expensive writes |
| Merge sort | O(n log n) | O(n log n) | O(n log n) | O(n) arrays | Yes | Stability, external sorting |
| Quicksort | O(n log n) | O(n log n) | O(n²) | O(log n) expected stack | Usually no | Fast in-memory primitive sorting |
| Heap sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No | Bounded memory and worst-case guarantee |

For one million ordered items, binary search needs at most about 20 comparisons; linear search may need one million. Sorting first costs O(n log n), so it pays off when enough searches follow or ordering has other value.

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Binary search on unsorted input.** It may return plausible wrong results; sortedness is a precondition.
2. **Unclear interval convention.** Mixing `[low,high]` with `[low,high)` creates missed elements or infinite loops.
3. **Unsafe midpoint.** `(low+high)/2` can overflow; use `low+(high-low)/2`.
4. **Missing recursive base case.** Calls continue until stack exhaustion.
5. **No progress toward base case.** Calling with the same `n` is equivalent to an infinite loop.
6. **Equating recursion with efficiency.** Naive Fibonacci is exponential.
7. **Assuming quicksort is always O(n log n).** Bad pivots cause quadratic behavior.
8. **Ignoring stability.** Equal-key records can change semantic order.
9. **Comparator subtraction.** Overflow violates comparator ordering.
10. **Reimplementing library sort in production.** Standard libraries are optimized and tested; custom code needs a strong reason.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the preceding sections.

- Linear search: unordered, O(n), streaming-friendly.
- Binary search: sorted + random access, O(log n), define exact contract.
- Closed range loop: `low <= high`; half-open lower bound: `low < high`.
- Recursive algorithm: base case + smaller recursive case + combination.
- Java has no guaranteed tail-call optimization.
- Stable sort preserves equal-key order.
- Insertion: small/nearly sorted. Merge: stable O(n log n), O(n) array space. Quick: expected fast, worst O(n²).
- Comparator: use `Integer.compare`, not subtraction.
- Deterministic pagination needs a unique tie-breaker.

## 8. PRACTICE SET FOR SELF-TEST

1. Trace binary search for 19 in `[4,11,19,28,37,49,63,78]`.
2. What does lower bound return for 6 in `[2,5,5,9]`?
3. Trace recursive `gcd(48,18)` using Euclid's `gcd(a,b)=gcd(b,a%b)`.
4. Stable-sort `(A,3),(B,1),(C,3),(D,2)` by the number.
5. Give insertion sort's comparisons/moves behavior on an already sorted array.
6. Choose an approach for finding one ID in an unsorted stream that cannot fit memory.
7. Explain why recursive traversal of a million-node linked list is unsafe in Java.
8. Give a deterministic ordering for claims with amount and creation time duplicates.
9. Calculate the largest number of binary-search comparisons needed for 10 million elements.
10. Identify the defect: `while (low < high) { mid=(low+high)/2; if(a[mid]<x) low=mid; else high=mid; }`.

## 9. CURATED RESOURCES

- Cormen, Leiserson, Rivest, and Stein, *Introduction to Algorithms*, 4th ed., Chapters 2, 4, 7, and 12.1 — rigorous insertion/merge sorting, divide-and-conquer recurrences, quicksort, and binary-search-tree context.
- Robert Sedgewick and Kevin Wayne, *Algorithms*, 4th ed., Sections 2.1–2.3 — implementations, cost models, stability, and practical sorting trade-offs.
- Jon Bentley, *Programming Pearls*, 2nd ed., Columns 4 and 5 — binary search correctness and disciplined program verification.
- Java SE 21 API, `java.util.Arrays`, `java.util.Collections`, and `java.util.Comparator` — authoritative stability, overload, and comparator contracts.
- Tim Peters, `listsort.txt` in the CPython source tree — primary design notes for TimSort's adaptive run merging.
- Donald Knuth, *The Art of Computer Programming, Volume 3: Sorting and Searching*, 2nd ed. — canonical deep treatment and historical foundations.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Programming Logic and Debugging:** supplies loops, contracts, traces, and invariants.
2. **Java Language and Object Model:** supplies arrays, methods, call behavior, and comparators.

### After

1. **Discrete Math and Bit Manipulation:** explains logarithms, powers of two, and boolean identities used here.
2. **Complexity Analysis:** formally derives O(log n), O(n log n), and recursive costs.
3. **Arrays and Strings:** applies binary-search and ordering patterns to indexed data.
4. **Trees, Heaps, and Tries:** generalizes ordered search and recursive traversal.

---ANSWER KEY BELOW---

1. Mid 3→28, high 2; mid 1→11, low 2; mid 2→19, result 2.
2. Index 3, the insertion point before 9.
3. `(48,18)→(18,12)→(12,6)→(6,0)`, answer 6.
4. B, D, A, C; A remains before C.
5. Approximately n−1 key comparisons, no shifts, O(n) time in the adaptive implementation.
6. Linear scan; retain only the match/current state.
7. O(n) frames can overflow the finite stack; iterate instead.
8. For example `(amount, created_at, claim_id)` where claim ID is unique.
9. `ceil(log2(10,000,000)) = 24` interval halvings/comparisons in the usual bound.
10. When `mid==low` and `a[mid]<x`, the range does not shrink; set `low=mid+1` and use safe midpoint arithmetic.
