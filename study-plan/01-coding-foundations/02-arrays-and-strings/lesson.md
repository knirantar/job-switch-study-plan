# Arrays and Strings — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `02-arrays-and-strings`  
**Expected study time:** 2–4 hours, plus implementation and spaced review

## 1. FOUNDATIONS

### Why arrays exist

Programs constantly need to store sequences: hourly request counts, model latency samples, payment amounts, bytes read from a network socket, or characters in an identifier. Keeping each value in an unrelated variable makes it impossible to write one general loop. An **array** stores a fixed number of elements of one declared type and associates each with an integer **index**.

The central implementation idea is contiguous indexed storage. Conceptually, if the first element starts at address `base` and every element occupies `width` bytes, element `i` is at `base + i × width`. This arithmetic is why random access is O(1): finding index 900,000 does not require walking through the first 899,999 elements. Hardware caches also favor contiguous scanning because nearby elements arrive in cache lines together.

The trade-off is structural rigidity. A Java array has a fixed length. Inserting at the front requires shifting existing elements or allocating another array. A resizable array such as `ArrayList` hides reallocation and copying, but it cannot repeal those costs. Linked structures make some insertions cheap but sacrifice locality and O(1) indexed access.

Java arrays are objects. `new int[5]` creates five zero-initialized primitive slots. `new Payment[5]` creates five `null` reference slots; it does not construct five payments. `a.length` is a field, not a method. Indices range from 0 through `length-1`; any other index throws `ArrayIndexOutOfBoundsException`. This checked boundary prevents silent memory corruption common in lower-level languages, but an incorrect algorithm still fails at runtime.

### Why strings require separate care

A **string** is a sequence of text elements, but “character” is ambiguous. Java `String` stores UTF-16 code units. A Java `char` is one 16-bit code unit, not necessarily one Unicode character. Many common characters use one code unit, while supplementary code points such as 😀 use a surrogate pair. Human-perceived grapheme clusters can contain multiple code points—for example a base letter plus combining mark or a family emoji sequence. Therefore:

- `s.length()` counts UTF-16 code units.
- `s.codePointCount(0, s.length())` counts Unicode code points.
- Neither necessarily counts user-perceived characters.

String is **immutable**: after construction, its sequence cannot change. Immutability allows safe sharing, stable hashing and string pooling. Operations that appear to modify a string create a new string. Repeated concatenation in a loop can repeatedly copy an ever-growing prefix; use `StringBuilder` for incremental construction.

### Vocabulary used throughout

An **element** is a stored value. A **subarray** is a contiguous interval of an array; a **subsequence** preserves order but may skip elements. A **substring** is a contiguous portion of a string. A **prefix** starts at index 0; a **suffix** ends at the final index. **In-place** usually means O(1) auxiliary storage while mutating the input, but clarify whether a few variables are allowed. **Stable** means equal or retained items preserve relative order. A **sentinel** is a distinguished value used to mark a condition; sentinels are unsafe when the value can legitimately occur in input.

An **invariant** is a statement that remains true at a chosen point in every loop iteration. Invariants are the main technique for reasoning about index-heavy code. Rather than hoping that pointer movements work, state what every region means: processed prefix, active window, unprocessed suffix, or final output.

### What breaks without disciplined indexing

Array bugs often look small but create production failures: an off-by-one drops the last payment, an integer overflow corrupts a midpoint, a forward merge overwrites unread input, a UTF-16 assumption splits an emoji, or a quadratic concatenation causes latency and garbage collection. Senior-level work requires both algorithmic correctness and contract clarity: null behavior, mutation, Unicode semantics, integer range, stability and memory ownership.

## 2. CORE MECHANICS

### 2.1 Index ranges and boundary conventions

Two conventions dominate. A closed interval `[left,right]` includes both ends and has length `right-left+1`. A half-open interval `[left,right)` includes left but excludes right and has length `right-left`. Java collections and strings commonly use half-open ranges because empty ranges are natural (`left==right`) and adjacent ranges compose without overlap: `[0,k)` followed by `[k,n)`.

For a 6-element array, valid whole-array forms are `[0,5]` closed and `[0,6)` half-open. Mixing formulas creates off-by-one errors. Write the convention next to binary search or window code.

### 2.2 Traversal

Use an enhanced for loop when only values matter:

```java
long sum = 0;
for (int latency : latencies) sum += latency;
```

Use an indexed loop when position, neighbors or mutation matter. Accumulate `int` values into `long` when totals can overflow. One million values of 100,000 sum to 100 billion, far above `Integer.MAX_VALUE` (2,147,483,647).

Reverse traversal starts at `length-1` and continues while `i>=0`. With an unsigned index in other languages, this pattern can underflow; Java `int` avoids unsigned underflow but the empty-array start becomes -1 and safely skips.

### 2.3 Read and write pointers: stable compaction

To move zeroes to the end while preserving nonzero order, maintain this invariant before reading index `read`: `a[0..write)` contains exactly the nonzero values from `a[0..read)`, in original order.

For `[0,5,0,3,8]`:

1. read 0: zero; prefix empty.
2. read 1: write 5 at index 0; prefix `[5]`.
3. read 2: zero.
4. read 3: write 3 at index 1; prefix `[5,3]`.
5. read 4: write 8 at index 2; prefix `[5,3,8]`.
6. Fill indices 3 and 4 with zero.

Time O(n), auxiliary space O(1), stable. A swap-based version can reduce writes when nonzeroes are already placed, but must still preserve order if stability is required.

### 2.4 Two-ended pointers

Reversing swaps the outside pair and shrinks inward. The invariant is that elements outside `[left,right]` are already in final reversed positions.

```java
while (left < right) {
    int tmp = a[left]; a[left++] = a[right]; a[right--] = tmp;
}
```

Odd-length arrays leave the center untouched; empty and singleton arrays perform no swaps. Two pointers also solve sorted pair-sum: if `a[left]+a[right]` is too small, no pair using that left and a smaller right can reach target, so advance left. This reasoning depends on sorting.

### 2.5 Prefix and suffix accumulation

A prefix array stores cumulative information. Define `prefix[0]=0` and `prefix[i+1]=prefix[i]+a[i]`. Then the sum of half-open interval `[left,right)` is `prefix[right]-prefix[left]`.

For `[12,7,5,20]`, prefix is `[0,12,19,24,44]`; sum indices `[1,4)` is `44-12=32`. Building costs O(n) time/O(n) space; each later range query is O(1). For one query, a direct scan may be simpler. For one million queries, preprocessing is decisive.

Product-except-self uses a prefix product in the output and a rolling suffix. For `[1,2,3,4]`, the forward output becomes `[1,1,2,6]`. Moving backward with suffix values 1,4,12,24 gives `[24,12,8,6]`. It avoids division and correctly handles zeroes. Integer multiplication can overflow; production code may require `long`, `BigInteger`, checked arithmetic or domain constraints.

### 2.6 Sliding windows

A **window** is a contiguous range whose state is updated when boundaries move. Fixed-size window sums avoid recomputing all k elements. For request counts `[120,180,90,210,160,130]` and k=3, the first sum is 390. Add 210 and subtract 120 →480; add 160/subtract 180 →460; add 130/subtract 90 →500. O(n), not O(nk).

Variable windows require a monotonic validity rule. Longest substring without repeated symbols tracks last positions. When a repeated symbol at `right` was last at p within the current window, move `left` to `p+1`; never move left backward. Each boundary advances at most n times.

The standard “shrink while sum too large” method fails with negative numbers because expanding can decrease the sum and shrinking can increase it. Prefix sums plus hashing are then often appropriate.

### 2.7 Rotation by reversal

Rotating `[1,2,3,4,5,6,7]` right by 3 should yield `[5,6,7,1,2,3,4]`. Reverse all → `[7,6,5,4,3,2,1]`; reverse first 3 → `[5,6,7,4,3,2,1]`; reverse remainder → result. Normalize `k` using `Math.floorMod(k,n)` so values larger than n and negative rotations have defined behavior. Empty input must return before modulus by zero. Time O(n), space O(1).

Alternatives are an O(n) copy, repeated one-step shift O(nk), or cycle replacement O(n)/O(1) with trickier correctness.

### 2.8 Merging sorted arrays

If the first array has spare capacity at the end, merge backward. With `a=[1,3,7,_,_,_]` and `b=[2,6,8]`, compare 7 and 8, write 8 at the last slot; compare 7 and 6, write 7; continue. Writing from the front would overwrite unread values in `a`. The loop can stop once `b` is exhausted because leftover `a` values are already placed. O(m+n) time/O(1) auxiliary space.

### 2.9 Strings, builders and Unicode

This loop is potentially quadratic:

```java
String result = "";
for (String token : tokens) result += token;
```

Each immutable concatenation may copy the accumulated prefix. If n one-character tokens are appended, copied lengths resemble `1+2+...+n=O(n²)`. `StringBuilder` maintains a growable buffer and makes total append work amortized O(n), followed by one final string creation.

For Unicode code-point processing:

```java
int[] codePoints = text.codePoints().toArray();
```

This allocates O(n) integers but avoids splitting surrogate pairs. For user-visible grapheme clusters, code points are still insufficient; use a Unicode text boundary implementation such as `BreakIterator` and specify locale/behavior.

### 2.10 Sorting and binary search prerequisites

Java `Arrays.sort(int[])` provides primitive sorting with implementation/version-specific guarantees; object arrays use stable sorting contracts. Never infer stability without checking the exact API. Binary search requires data sorted according to the same comparator used for searching. Duplicate matches may return any matching index unless you implement lower/upper-bound search.

Use `mid=low+(high-low)/2` to avoid overflow. Decide a closed or half-open search template and prove termination. Empty arrays and values outside the range must return a defined “not found” representation such as -1 or insertion point.

## 3. WORKED PROBLEMS

### Problem 1 — Stable zero compaction

**Statement.** Transform `[0,4,0,0,7,2,0]` in place to move zeroes to the end while preserving nonzero order.

**Solution.** Keep `write=0`. Scan values: 4 writes at 0, 7 at 1, 2 at 2. Now `write=3`; fill positions 3–6 with zero. Result `[4,7,2,0,0,0,0]`. Every element is read once and at most once written during compaction plus suffix fill: O(n), O(1). The invariant states the prefix before write is the final stable nonzero prefix.

**Mistake caught.** Swapping every zero with the last nonzero reverses or scrambles order.

### Problem 2 — Merge sorted telemetry batches

**Statement.** `a=[1,3,7,0,0,0]`, m=3 and `b=[2,6,8]`, n=3. Merge into a.

**Solution.** Start i=2 (7), j=2 (8), write=5. Write 8; then 7; then 6; compare 3 and 2, write 3; write 2. b is exhausted; 1 remains correctly at index 0. Result `[1,2,3,6,7,8]`. O(m+n)/O(1).

**Mistake caught.** Forward writes destroy unread elements in the first array.

### Problem 3 — Product except self with zeroes

**Statement.** Return product of all other positions for `[0,2,0,4]` without division.

**Solution.** Prefix pass stores `[1,0,0,0]`: after the first zero, later prefix products are zero. Backward suffix multiplication also introduces the other zero, producing `[0,0,0,0]`. With exactly one zero, only its position receives the product of nonzero values. With no zero, normal prefix/suffix results apply. O(n) time; O(1) auxiliary space excluding output.

**Mistake caught.** Division fails at zero and may lose integer precision/overflow semantics.

### Problem 4 — Rotate by a large k

**Statement.** Rotate `[1,2,3,4,5,6,7]` right by k=10.

**Solution.** Normalize `10 mod 7=3`. Apply three reversals as described earlier; result `[5,6,7,1,2,3,4]`. O(n)/O(1). For k=-2, `floorMod(-2,7)=5`, equivalent to rotating left by 2.

**Mistake caught.** Performing 10 individual rotations gives O(nk), and `%` with negative values may not express intended rotation.

### Problem 5 — Longest unique Unicode code-point substring

**Statement.** Find the longest substring without repeated Unicode code points in `a😀b😀c`.

**Solution.** Code points are `[a,😀,b,😀,c]`, five symbols although UTF-16 length is seven. Track last index. Window grows through `a😀b` length 3. At second 😀 (index 3), move left from 0 to last😀+1=2. Window `b😀c` again reaches 3. Answer 3 code points. O(p) expected time/O(u) space where p is code points and u distinct code points.

**Mistake caught.** Iterating `char` treats each surrogate half as a separate value and corrupts semantics.

### Problem 6 — Range sums for dashboard queries

**Statement.** Hourly incident counts are `[12,7,5,20,9,11]`. Answer sums for hours `[1,4)` and `[0,6)` efficiently across many queries.

**Solution.** Prefix `[0,12,19,24,44,53,64]`. First result `prefix[4]-prefix[1]=44-12=32`. Whole range `64-0=64`. Preprocess O(n)/O(n); query O(1). Use `long` if cumulative counts can exceed int.

**Mistake caught.** Using `prefix[right]-prefix[left-1]` while mixing inclusive and half-open boundaries.

### Problem 7 — Summarize sorted ID ranges safely

**Statement.** Convert `[0,1,2,4,5,7]` to `["0->2","4->5","7"]`.

**Solution.** At each unprocessed index, record start and advance while the next value equals end+1. Emit one number if start=end, otherwise range. Each index advances once: O(n), output space O(number of ranges). For `long`, checking `end+1` can overflow at `Long.MAX_VALUE`; test `end != Long.MAX_VALUE` first.

**Mistake caught.** Overflow makes `Long.MAX_VALUE+1` wrap to `Long.MIN_VALUE`, falsely joining distant values.

### Problem 8 — Minimum-length positive subarray

**Statement.** For positive request costs `[2,3,1,2,4,3]`, find minimum contiguous length with sum at least 7.

**Solution.** Expand right while adding values. Whenever sum≥7, record window length and remove left until invalid. Windows include `[2,3,1,2]` length 4, `[3,1,2,4]` shrinking to `[4,3]` length 2. Answer 2. Each element enters/leaves once: O(n)/O(1). Positivity is essential: removing a positive always decreases sum and makes monotonic shrinking valid.

**Mistake caught.** Applying the same window unchanged when negative values exist.

### Problem 9 — Set matrix zeroes in place

**Statement.** For matrix `[[1,1,1],[1,0,1],[1,1,1]]`, set an entire row and column to zero when a cell is zero, using O(1) extra space.

**Solution.** Use first row and first column as marker arrays, plus booleans remembering whether they originally contained zero. Scan interior; zero at (1,1) marks row 1 and column 1. Second pass zeroes marked interior, yielding `[[1,0,1],[0,0,0],[1,0,1]]`; finally handle first row/column flags. O(rows×cols), O(1). Empty/ragged matrices require an explicit contract; this approach assumes rectangular nonempty rows.

**Mistake caught.** Zeroing immediately causes newly written zeroes to cascade and erase the whole matrix.

## 4. REAL-WORLD / APPLIED CONTEXT

### Java and memory locality

Primitive `int[]` stores values without per-element boxing. `ArrayList<Integer>` stores references to `Integer` objects (with some cached small integers), adding indirection and often allocation. For 10 million integers, raw payload in `int[]` is about 40 MB because each int is 4 bytes, excluding the small array header/alignment. A boxed representation can require several times that amount depending on compressed references, object layout and value caching. Use Java Object Layout (JOL) on the actual JVM for evidence; do not hard-code an object-size claim across runtimes.

### Network and file parsing

Libraries parse byte arrays and buffers using indices and slices. A zero-copy slice can be O(1) to create but retains the backing buffer; a small long-lived slice may prevent a large buffer from being reclaimed. Netty’s `ByteBuf` exposes reader/writer indices precisely to separate consumed, readable and writable regions. Correct boundary management is both a performance and security concern: length fields must be validated before indexing or allocation.

### Production text handling

Java identifiers and many protocols are ASCII-constrained, where a 128-entry frequency array is fast and clear. User names, clinical notes and international addresses are not. A backend that reverses UTF-16 `char` values can split surrogate pairs. Correct implementation depends on the unit: code unit for protocol internals, code point for many symbol algorithms, grapheme cluster for user-visible editing.

The included `ArraysStringsLab.java` compiles and tests zero compaction, prefix/suffix product, normalized rotation, code-point sliding windows, overflow-safe range summarization and backward merge.

## 5. COMPARISON TABLE

| Requirement | Approach | Time | Extra space | Concrete trade-off |
|---|---|---:|---:|---|
| One range-sum query | direct scan | O(k) | O(1) | no preprocessing |
| Many range-sum queries | prefix sums | O(n) build, O(1) query | O(n) | 1M `long` prefixes ≈8 MB payload |
| Rotate array | copy | O(n) | O(n) | simplest, preserves source if desired |
| Rotate array | three reversals | O(n) | O(1) | mutates; careful k normalization |
| Rotate array | k shifts | O(nk) | O(1) | unacceptable for large k |
| Build text | repeated `String +` loop | potentially O(total²) | many temporaries | readable only for tiny/folded expressions |
| Build text | `StringBuilder` | amortized O(total) | O(total) | correct default for loops |
| Membership, unsorted array | scan | O(n) | O(1) | good for few queries/small data |
| Membership after sort | binary search | O(log n)/query | sort-dependent | ordering/range operations available |
| Stable filter | read/write pointer | O(n) | O(1) | mutates input, preserves retained order |
| Unicode iteration | `char` | O(code units) | O(1) | may split supplementary code points |
| Unicode iteration | `codePoints()` | O(code units) | stream/array dependent | correct code points, not grapheme clusters |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Using `i <= a.length`.** Last valid index is `length-1`; use `< length`.
2. **Confusing subarray and subsequence.** `[2,5]` chosen from `[2,3,5]` is a subsequence but not contiguous.
3. **Integer accumulation overflow.** Summing 1 million large ints into int silently wraps; use long or checked arithmetic.
4. **Forward in-place merge.** It overwrites unread values; fill from the end.
5. **Modulo by zero on empty rotation.** Return before normalizing k.
6. **Repeated immutable concatenation.** It can copy quadratic total text; use a builder.
7. **Treating `char` as Unicode character.** Surrogate pairs break; define code point or grapheme semantics.
8. **Sliding window with non-monotonic data.** Negative values invalidate positive-sum shrinking logic.
9. **Binary search on mismatched ordering.** Data and comparator must agree.
10. **Midpoint overflow.** Prefer `low+(high-low)/2`.
11. **Claiming in-place while returning a full copy.** State mutation and auxiliary-space contract.
12. **Immediate matrix zeroing.** Written zeros contaminate later decisions; record markers first.
13. **Ignoring stability.** Partitioning by swapping can change relative order even when membership is correct.
14. **Assuming rectangular arrays.** Java 2D arrays are arrays of arrays and may be ragged or contain null rows.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the sections above.

- Valid indices: `0..length-1`; half-open whole range `[0,length)`.
- Scan O(n); index O(1); middle insertion/deletion O(n).
- Stable compaction invariant: `[0,write)` is the final retained prefix.
- Prefix: `p[i+1]=p[i]+a[i]`; `[l,r)` sum=`p[r]-p[l]`.
- Sliding window works when boundary changes update state and validity is monotonic.
- Rotation: normalize k; reverse all, first k, remainder.
- Merge into spare tail from right to left.
- Use `StringBuilder` for looped construction.
- Java `char`=UTF-16 code unit; code point and grapheme are different.
- Use long for large sums and guard `MAX_VALUE+1`.
- State mutation, stability, interval convention and Unicode unit.

## 8. PRACTICE SET FOR SELF-TEST

Do not view the answer key until all responses include reasoning, complexity and boundary tests.

1. Remove duplicates from sorted `[1,1,2,2,2,4,7,7]` in place and return the new logical length.
2. Find the maximum sum of any 4 consecutive values in `[14,-2,31,7,9,-12,40,6]`.
3. For prefix `[0,5,3,12,20]`, recover the original array and give sum `[1,4)`.
4. Rotate `[10,20,30,40,50]` right by -2 under the documented floor-mod convention.
5. Explain why the usual minimum-length-positive-window algorithm fails on `[5,-10,20]` for target 15.
6. Return the first and last position of 8 in sorted `[2,4,8,8,8,11,15]` using logarithmic time.
7. Estimate primitive payload bytes for an `int[25_000_000]`, excluding header/alignment, and explain why `ArrayList<Integer>` differs.
8. Determine Java UTF-16 length and code-point count for `A😀B`.
9. Design an O(rows×cols), O(cols) method to compute each matrix row’s prefix sums without mutating input.
10. Given sorted timestamps `[1,2,3,10,11,Long.MAX_VALUE]`, summarize consecutive ranges without overflow.

## 9. CURATED RESOURCES

1. **Oracle Java SE API, `java.util.Arrays`.** Exact contracts for primitive/object sorting, binary search, copying, filling and mismatch operations.
2. **Java Language Specification, Chapter 10 “Arrays.”** Definitive rules for array types, creation, initialization, covariance and runtime store checks.
3. **Oracle Java SE API, `java.lang.String`, `StringBuilder`, and `Character`.** Exact UTF-16, code-point and builder behavior.
4. **Unicode Standard, Chapter 3; Unicode Standard Annex #29, “Unicode Text Segmentation.”** Distinguishes code units, code points and grapheme clusters beyond Java-specific APIs.
5. **Cormen et al., *Introduction to Algorithms*, 4th ed., Chapters 2 and 7.** Adds loop invariants, insertion sort and array partition reasoning.
6. **Sedgewick & Wayne, *Algorithms*, 4th ed., §§1.1, 1.4 and 2.1–2.3.** Connects array algorithms to empirical performance and sorting.
7. **Jon Bentley, *Programming Pearls*, 2nd ed., Columns 2 and 8.** Adds array rotation and maximum-subarray problem reformulation.
8. **Netty 4.x API, `io.netty.buffer.ByteBuf`.** Shows production reader/writer index design, capacity and slicing semantics.
9. **OpenJDK Java Object Layout (JOL).** Provides runtime evidence for arrays, references and boxed object layout on the actual JVM.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Complexity Analysis.** You need growth and auxiliary-space reasoning to compare scanning, copying, prefix preprocessing and nested loops.
2. **Java syntax and primitive/reference types.** Array allocation, default values and method parameter behavior depend on Java’s type model.

### After

1. **Hashing and Sets.** Hashing replaces repeated array scans with expected constant-time membership at an O(n) memory cost.
2. **Problem-Solving Patterns.** Two pointers, windows, prefix sums and binary search become reusable recognition patterns.
3. **Linked Lists, Stacks and Queues.** These contrast contiguous storage with node-based or restricted-access structures.
4. **Database Indexes and Query Plans.** Sorted arrays and binary search provide the conceptual bridge to ordered indexes, while real databases add pages and I/O.

---ANSWER KEY BELOW---

1. Keep write=1 for nonempty input; scan read=1..end and copy when value differs from `a[write-1]`. Result prefix `[1,2,4,7]`, logical length 4. O(n)/O(1). Empty input returns 0.
2. Initial sum `14-2+31+7=50`; slide: 45, 35, 4, 43. Maximum 50. O(n)/O(1).
3. Differences give `[5,-2,9,8]`. Sum `[1,4)`=`20-5=15`.
4. `floorMod(-2,5)=3`; right by 3 gives `[30,40,50,10,20]`, equivalent to left by 2.
5. Whole window sum is 15 and length 3, but removing left 5 produces 10 and appears invalid; the optimal single `[20]` is hidden until the negative is removed. Positivity/monotonicity is absent.
6. Run lower bound for first index ≥8 →2 and upper bound for first index >8 →5; last is 4. O(log n)/O(1).
7. 25,000,000×4=100,000,000 bytes (100 MB decimal, about 95.37 MiB) primitive payload. Boxed list adds reference array and usually Integer object/indirection costs, runtime-dependent.
8. `length()` is 4 UTF-16 code units: A=1, 😀=2, B=1. Code-point count is 3.
9. Allocate `long[rows][cols+1]` or one row at a time; `p[r][c+1]=p[r][c]+matrix[r][c]`. O(rows×cols) time and O(rows×cols) output; O(cols) working space if rows are streamed/emitted.
10. Emit `1->3`, `10->11`, and `9223372036854775807`. Test `end != Long.MAX_VALUE` before comparing next with `end+1`.
