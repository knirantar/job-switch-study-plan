# Problem-Solving Patterns — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `07-problem-solving-patterns`  
**Expected study time:** 2–4 hours plus timed practice

## 1. FOUNDATIONS

### Patterns are compressed proofs

Interview problems appear diverse, but many share a mathematical structure. A **problem-solving pattern** is a reusable combination of state, invariant and boundary movement. Two pointers work because order lets one comparison eliminate many candidates. A sliding window works because validity changes monotonically as boundaries move. Dynamic programming works because different decision paths revisit the same state. The pattern is not a keyword lookup; it is a proof about discarded possibilities.

Before patterns, candidates often solve each problem from scratch or memorize code templates. Memorization breaks when the problem changes: negative numbers invalidate a positive sliding window, duplicates alter binary-search boundaries, and a greedy coin choice fails for denominations 1,3,4. The correct workflow is:

1. define input/output and constraints;
2. give a correct baseline;
3. identify repeated work or search structure;
4. state the invariant/monotonic predicate/state;
5. prove boundary movement does not discard a valid optimum;
6. code and test counterexamples.

### Terminology

An **invariant** remains true at a specified program point. A **monotonic predicate** changes only once across an ordered search domain—false then true, or true then false. An **optimal substructure** means an optimal solution can be built from optimal subproblem solutions. **Overlapping subproblems** means the same state recurs. **State** is the minimum information needed to determine future choices. A **transition** moves between states. A **greedy choice** makes an irrevocable locally best decision; it requires an exchange/cut/stays-ahead proof, not intuition.

**Backtracking** explores a decision tree and undoes choices. **Pruning** stops branches proven unable to lead to a valid/better answer. **Memoization** caches top-down recursion. **Tabulation** computes bottom-up. An **interval** needs endpoint semantics: closed `[start,end]` versus half-open `[start,end)` changes whether touching intervals overlap.

## 2. CORE MECHANICS

### 2.1 Two pointers on sorted data

For sorted pair sum, start at extremes. If sum is below target, every pair using the current smallest value with an index no larger than right is no greater, so only increasing left can help. If too large, decrease right. Each pointer moves at most n: O(n)/O(1).

For `[1,2,4,7,11]`, target9: 1+11=12, move right; 1+7=8, move left; 2+7=9. Overflow-safe code sums into long. Without sorting, the elimination proof fails; use hashing or sort while preserving original-index needs.

Fast/slow read-write pointers compact arrays. Opposite pointers reverse or partition. The unifying condition is monotonic progress plus an invariant describing processed regions.

### 2.2 Fixed sliding window

When every candidate is a contiguous range of fixed length k and aggregate can be updated, compute first window then add incoming/subtract outgoing. For `[14,-2,31,7,9,-12,40,6]`, k=4, sums are 50,45,35,4,43; max50. O(n)/O(1) instead of O(nk). Validate `1≤k≤n` or define empty behavior.

Not every aggregate has a simple inverse: a maximum cannot be updated by subtraction when the outgoing value was maximum. Use a monotonic deque to maintain candidates in O(n).

### 2.3 Variable sliding window

For longest substring without repeats, state is last positions or a frequency map. Expand right. When invalid, advance left until valid. Both boundaries never retreat, so O(n).

For minimum-length subarray with sum≥K and all values positive, expand adds positive amount and shrink removes positive amount; validity is monotonic. With `[5,-10,20]`, K=15, this logic can miss single `[20]`: negative values break monotonicity. Use prefix sums plus a monotonic deque for the general shortest-at-least-K problem.

### 2.4 Prefix sums and frequency maps

Prefix sums convert a range aggregate into difference: `sum[l,r)=P[r]-P[l]`. Count subarrays with sum k by storing frequencies of previous prefixes `P[r]-k`. Initialize prefix0 frequency1. Negative values are fine. Use long.

For `[3,4,7,2,-3,1,4,2]`, k7, frequency counting yields four ranges. A set is insufficient because repeated prefix values represent different starting indices.

Two-dimensional prefix sums answer rectangle sums: `S(r2,c2)-S(r1,c2)-S(r2,c1)+S(r1,c1)` under half-open coordinates, applying inclusion-exclusion.

### 2.5 Binary search on indices

Classic binary search locates target. More reusable are **lower bound** (first index with value≥target) and **upper bound** (first index with value>target). Equal range is `[lower,upper)`. Use half-open `[low,high)`:

```text
while low < high:
  mid = low + (high-low)/2
  if a[mid] < target: low=mid+1
  else: high=mid
```

At termination low is first location that could satisfy ≥target, possibly n. The invariant is all indices before low are known too small and all indices at/after high are known candidates.

### 2.6 Binary search on answer

Sometimes the answer is numeric and a feasibility predicate is monotonic. Shipping weights within D days: capacity below some threshold fails; every larger capacity succeeds. Search capacity `[maxWeight,sumWeights]`, greedily count required days. For weights1..10,D5, minimum15. Complexity O(n log(sum-max)).

Proof obligations: bound contains answer, `can(x)` truly monotonic, arithmetic cannot overflow, and update returns first feasible rather than any feasible.

### 2.7 Intervals and sweep lines

Merge intervals by sorting starts and maintaining current union. Under closed/touching-merges semantics, merge when `next.start≤current.end`. For `[1,3],[2,6],[8,10],[10,12]`, result `[1,6],[8,12]`. If half-open booking intervals, `[8,10)` and `[10,12)` do not overlap.

For concurrent meetings, sort starts/ends or create events. Tie ordering matters: under half-open intervals, process end before start at same time. A min-heap of active end times returns room count and supports assignment.

### 2.8 Monotonic stack/deque

Next-greater element keeps unresolved decreasing indices. A larger arrival resolves all smaller tops. Each index enters/exits once: O(n). Histogram largest rectangle and daily temperatures are variants.

Window maximum deque keeps indices with decreasing values, expires old front and removes dominated back. Dominated means a newer value is at least as large and expires later, so older can never win.

### 2.9 Backtracking

Backtracking has: choices, constraints, completion, choose→recurse→undo. For unique subsets of sorted `[1,2,2]`, at a recursion depth skip `a[i]` when `i>start && a[i]==a[i-1]`. This prevents duplicate sibling choices but allows choosing the second 2 after the first along a deeper path. Six subsets result: `[],[1],[1,2],[1,2,2],[2],[2,2]`.

Complexity often matches output size—subsets O(2^n), permutations O(n·n!). Pruning helps instances, not necessarily worst-case class.

### 2.10 Dynamic programming

Write DP in five parts: state meaning, transition, base, computation order, answer. Coin change minimum with coins `[1,3,4]`, amount6:

`dp[x]=1+min(dp[x-coin])`. Initialize `dp[0]=0`, others impossible. Results lead `dp[6]=2` via3+3, while greedy largest-first chooses4+1+1=3 coins. O(amount×coins), O(amount).

For 0/1 knapsack, iterate capacity downward in one-dimensional DP so an item is used once. Upward iteration changes it into unbounded reuse. Computation order is part of correctness.

### 2.11 Greedy reasoning

Greedy interval scheduling selects compatible interval with earliest finish; an exchange proof shows replacing an optimal solution’s first interval with the earliest-finishing one does not reduce remaining opportunity. Greedy coin selection is not universally correct. Minimum spanning-tree algorithms are greedy because cut properties justify safe edges.

When no proof/counterexample confidence exists, formulate DP or exhaustive baseline first.

### 2.12 Pattern combinations

Real questions combine techniques: sort + two pointers; prefix sums + hash map; binary search + greedy feasibility; heap + hashing for top-k; graph BFS + bitmask state; backtracking + memoization. Complexity must include every phase and state dimension.

## 3. WORKED PROBLEMS

### Problem 1 — Sorted pair sum

**Statement.** Find pair summing9 in `[1,2,4,7,11]`.

**Solution.** Extremes 12 too high→right; 8 too low→left; 9 match indices1,3. O(n)/O(1). The sorted order proves movements safe.

**Mistake caught.** Applying pointer elimination to unsorted values.

### Problem 2 — Longest unique substring

**Statement.** For `pwwkew`, return length.

**Solution.** Window p,w length2; second w moves left past first w; window wke reaches3; final w moves left accordingly. Answer3 (`wke` or `kew`). O(n) expected/O(character set).

**Mistake caught.** Moving left to `previous+1` without max can move it backward.

### Problem 3 — Subarray sum with negatives

**Statement.** Count sum7 ranges in `[3,4,7,2,-3,1,4,2]`.

**Solution.** Maintain prefix frequencies beginning0→1; for each prefix p add count p−7 then record p. Answer4, O(n)/O(n).

**Mistake caught.** Positive-only window or a set instead of frequencies.

### Problem 4 — First/last duplicate

**Statement.** Find range of8 in `[2,4,8,8,8,11,15]`.

**Solution.** Lower bound≥8 returns2; upper bound>8 returns5; range `[2,5)` and last4. Two O(log n) searches.

**Mistake caught.** Returning arbitrary binary-search match then scanning linearly.

### Problem 5 — Ship capacity

**Statement.** Weights1..10,D5.

**Solution.** Bounds10..55. Feasibility greedily fills each day without exceeding capacity. Binary search narrows to15; capacity14 needs >5 days,15 fits. O(n log46)/O(1).

**Mistake caught.** Binary searching without monotonic proof or using average ceiling as guaranteed answer.

### Problem 6 — Merge bookings

**Statement.** Closed intervals `[1,3],[2,6],[8,10],[10,12],[15,18]`; touching merges.

**Solution.** Sort (already). Merge first two→1,6; 8 starts new; 10≤10 merges→8,12; 15 new. Output `[1,6],[8,12],[15,18]`. O(n log n).

**Mistake caught.** Failing to state touching endpoint semantics.

### Problem 7 — Coin change counterexample

**Statement.** Minimum coins for6 with `[1,3,4]`.

**Solution.** Greedy4+1+1 uses3. DP finds3+3 uses2. State dp[x] minimum; base0; impossible sentinel; transition over coins. O(18) updates conceptually, O(amount×3).

**Mistake caught.** Assuming largest denomination greedy always works.

### Problem 8 — Unique subsets

**Statement.** Enumerate unique subsets of `[1,2,2]`.

**Solution.** Sort, backtrack, skip equal sibling at same depth. Produce six subsets listed earlier. O(number of generated elements), conventionally O(n2^n), path O(n) excluding output.

**Mistake caught.** Global duplicate skip prevents valid `[2,2]`; no skip produces duplicates.

### Problem 9 — Meeting rooms

**Statement.** Half-open meetings `[0,30),[5,10),[10,20),[25,35)`; minimum rooms.

**Solution.** At5 two active. At10 first short meeting ends before next starts, reuse its room; `[0,30)` plus `[10,20)` still two. At25 `[10,20)` ended, but `[0,30)` and `[25,35)` two. Maximum2. End-before-start tie rule is essential. O(n log n).

**Mistake caught.** Treating touching half-open intervals as overlap.

## 4. REAL-WORLD / APPLIED CONTEXT

### Capacity configuration

Binary search on answer appears in shard sizing, batch capacity and concurrency-limit exploration when a deterministic feasibility simulation is monotonic. Production performance tests are noisy, so binary search over measured latency is unsafe unless the experiment controls noise and the predicate is reliably monotonic.

### Time windows and telemetry

Monitoring systems compute rolling rates/maxima/quantiles. Simple sums use fixed windows; maxima use deques; distributed event-time windows add late data, watermarks and state retention. The array pattern is the foundation, not the complete streaming guarantee.

### Scheduling

Calendar and compute scheduling use intervals, sweep lines and heaps. Kubernetes scheduling is far richer—constraints, resources and priorities—but interval overlap and priority structures remain subproblems. Always distinguish half-open time ranges to make back-to-back reservations reusable.

The compiled `PatternsLab.java` verifies overflow-aware two pointers, Unicode windowing, prefix frequencies, binary answer search, interval copying/merge, DP and duplicate-aware backtracking.

## 5. COMPARISON TABLE

| Signal | Pattern | Required property | Time | Failure boundary |
|---|---|---|---:|---|
| sorted pair/partition | two pointers | order eliminates candidates | O(n) | unsorted data |
| fixed contiguous aggregate | fixed window | incremental update | O(n) | noninvertible aggregate needs structure |
| variable valid range | sliding window | monotonic validity | O(n) | negatives/nonmonotonic rules |
| many range sums | prefix sums | associative cumulative difference | O(n)+O(1)/query | updates require other structures |
| first feasible numeric answer | binary answer search | monotonic predicate | O(check·log range) | noisy/nonmonotonic check |
| overlapping ranges | sort/sweep/heap | endpoint semantics | O(n log n) | wrong tie rules |
| enumerate candidates | backtracking | finite decision tree/pruning | often exponential | state not restored |
| repeated subproblems | DP | state sufficiency + overlap | states×transitions | missing state/order |
| local irreversible choice | greedy | proof property | often O(n log n) | plausible heuristic without proof |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Pattern by keyword.** “Substring” does not guarantee sliding window; prove monotonicity.
2. **Two pointers on unsorted data.** Elimination becomes invalid.
3. **Window with negative sums.** Shrink/expand effects are nonmonotonic.
4. **Binary search infinite loop.** Interval/update conventions must shrink every iteration.
5. **Any feasible answer returned.** Most tasks require first/minimum feasible boundary.
6. **Interval endpoints unstated.** Touching overlap changes answer.
7. **Backtracking state not undone.** Choices leak across siblings.
8. **Duplicate skip at wrong level.** Removes valid repeated-value combinations.
9. **DP state missing information.** Two histories collapsed despite different futures.
10. **Wrong 1D DP direction.** Converts 0/1 choice into unlimited reuse.
11. **Greedy without proof.** A local best choice can block global optimum.
12. **Ignoring output cost.** Enumerating 2^n subsets cannot be polynomial.
13. **Forgetting preprocessing.** “Binary search O(log n)” omits sort O(n log n).

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full resource.

- Start baseline, invariant, proof; do not template-match blindly.
- Two pointers: monotonic movement and safe candidate elimination.
- Fixed window: add incoming/remove outgoing.
- Variable window: validity must support monotonic shrink/expand.
- Prefix range `[l,r)=P[r]-P[l]`; count with prefix frequencies.
- Lower bound=first ≥x; upper=first >x.
- Answer search requires monotonic `can(x)` and valid bounds.
- Intervals: declare closed/half-open and tie ordering.
- Monotonic structures: each index pushes/pops once.
- Backtracking: choose, recurse, undo; prune with proof.
- DP: state, transition, base, order, answer.
- Greedy requires exchange/cut/stays-ahead proof.

## 8. PRACTICE SET FOR SELF-TEST

1. Find all unique triplets summing0 in `[-1,0,1,2,-1,-4]`.
2. Find longest subarray with at most two distinct values in `[1,2,1,2,3,2,2]`.
3. Count subarrays with equal zeroes and ones in `[0,1,0,0,1,1,0]`.
4. Find minimum eating speed for piles `[3,6,7,11]` within8 hours.
5. Merge half-open intervals `[1,3),[3,5),[4,8)` under non-touching semantics.
6. Give largest rectangle area for `[2,1,5,6,2,3]` and pattern.
7. Enumerate unique permutations of `[1,1,2]`.
8. Give 0/1 knapsack value for weights `[2,3,4]`, values `[4,5,7]`, capacity5 and show correct iteration direction.
9. Prove or disprove greedy earliest-start selection for maximum number of meetings.
10. Choose a pattern for shortest subarray sum≥3 in `[2,-1,2]` and explain why ordinary window is unsafe.

## 9. CURATED RESOURCES

1. **Cormen et al., *Introduction to Algorithms*, 4th ed., Chapters 14–16 and 22–23.** Dynamic programming, greedy proofs and amortized/structured algorithms.
2. **Sedgewick & Wayne, *Algorithms*, 4th ed., sorting/searching chapters.** Practical Java patterns and empirical costs.
3. **Jon Bentley, *Programming Pearls*, 2nd ed., Columns 2, 8 and 9.** Problem reformulation, maximum subarray and code tuning.
4. **Skiena, *The Algorithm Design Manual*, 3rd ed., Chapters 1, 8 and problem catalog.** Pattern recognition tied to real problem classes.
5. **Kleinberg & Tardos, *Algorithm Design*, Chapters 4–6.** Strong greedy and DP proof development.
6. **MIT OpenCourseWare 6.006, lectures on binary search, two pointers, DP.** Worked derivations and state design.
7. **Oracle Java API for `Arrays.binarySearch`, `PriorityQueue`, `ArrayDeque`.** Exact library boundaries behind patterns.
8. **Dijkstra, “A Discipline of Programming.”** Invariant-based derivation rather than post-hoc code explanation.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Complexity Analysis.** Patterns are valuable because they change growth and require aggregate proofs.
2. **Arrays/Strings and Hashing.** Windows, prefixes and complement maps use these directly.
3. **Stacks/Queues, Trees/Heaps, Graphs.** Monotonic structures, priority choices and state searches build on them.

### After

1. **Java Concurrency Basics.** Invariants extend from one execution to interleavings and atomic transitions.
2. **Database Algorithms.** Binary search, hashing, sort/merge and DP-like planning become persistent/query operations.
3. **System Design.** Capacity, scheduling and caching reuse patterns under distributed failures.
4. **Interview Mocks.** Pattern knowledge must become timed problem decomposition and communication.

---ANSWER KEY BELOW---

1. Sort `[-4,-1,-1,0,1,2]`; fix each distinct i and two-pointer remainder. Results `[-1,-1,2]`, `[-1,0,1]`. O(n²), excluding output O(1)/sort-dependent.
2. Frequency window; expand, while distinct>2 remove left. Longest `[1,2,1,2]` length4 or suffix `[2,3,2,2]` length4. O(n)/O(2–3).
3. Map 0→-1 and 1→+1. Equal counts mean same prefix balance. Frequencies count pairs; compute running to obtain 9 zero-sum transformed subarrays.
4. Predicate hours=`sum ceil(pile/speed)`≤8, monotonic. Search1..11; minimum4 (hours1+2+2+3=8). O(n log maxPile).
5. Sort; `[1,3)` does not overlap `[3,5)`. `[3,5)` overlaps `[4,8)`→`[3,8)`. Result `[1,3),[3,8)`.
6. Monotonic increasing stack; maximum10 from heights5,6 width2.
7. Sort; at each depth skip unused duplicate when previous equal is unused. Results `[1,1,2],[1,2,1],[2,1,1]`.
8. Best weight2+3 value9. One-dimensional capacity iterates downward 5..weight per item; upward would permit reusing same item.
9. Disprove: meetings `[0,100],[1,2],[2,3],[3,4]`; earliest-start chooses first and gets1, optimum gets3. Earliest-finish is the proven greedy rule.
10. Prefix sums plus increasing monotonic deque; ordinary positive window is unsafe due -1. Whole `[2,-1,2]` sum3 length3 is answer.
