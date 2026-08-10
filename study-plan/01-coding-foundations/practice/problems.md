# Coding Foundations Practice Set

Do not open `solutions.md` until you have written: approach, invariant, complexity, code and tests.

## Diagnostic (60 minutes, no notes)

1. Analyze: an outer loop runs n times; an inner pointer advances from 0 to n once total. Give time and explain.
2. Return indices of two numbers summing to target, including duplicates.
3. Validate brackets `()[]{}`.
4. Find shortest number of edges between two nodes in an unweighted graph.
5. Explain why `volatile int count; count++` is unsafe.

Score 1 point each for correct result, invariant/reason and complexity. Below 10/15: follow every lesson. 10–12: still follow order but shorten easy drills. 13+: focus on timed communication and edge cases.

## Level 1 — Foundation

1. **Stable compaction.** Input `[0,4,0,0,7,2,0]`; move zeroes to end in place while retaining nonzero order. Expected `[4,7,2,0,0,0,0]`.
2. **Frequency intersection.** Inputs `[4,9,5,4]` and `[9,4,9,8,4]`; return multiset intersection `[4,4,9]` in any order.
3. **Queue simulation.** Implement a queue with two stacks and prove amortized O(1).
4. **Tree height.** Return height in nodes; define empty height as 0. Include skewed tree risk.
5. **Components.** For edges `A-B, B-C, D-E` and vertex `F`, answer 3 components: `{A,B,C}`, `{D,E}`, `{F}`.

## Level 2 — Interview medium

6. **Longest unique substring.** Input `pwwkew`; answer 3 (`wke`). O(n) required.
7. **Subarray sum k.** Input `[3,4,7,2,-3,1,4,2]`, k=7; answer 4. Negative values disallow the usual positive-only window.
8. **Top k frequency.** Input `[1,1,1,2,2,3,3,3,3,4]`, k=2; answer `{3,1}`.
9. **Deployment order.** Dependencies `api→auth`, `billing→auth`, `web→api`, where arrow means “depends on.” Return a valid dependency-first order or explain the edge reversal you use.
10. **Minimum capacity.** Weights `[1,2,3,4,5,6,7,8,9,10]`, D=5; minimum ship capacity is 15. Solve by binary search on answer.
11. **Merge intervals.** `[[1,3],[2,6],[8,10],[10,12],[15,18]]`; if touching merges, output `[[1,6],[8,12],[15,18]]`.
12. **LRU cache.** Capacity 2: `put(1,A), put(2,B), get(1), put(3,C), get(2)`; last result is miss because key 2 was least recently used.

## Level 3 — Backend-flavored

13. **Top endpoints.** Process 20 million `(endpoint,status)` records and return the 100 endpoints with most 5xx responses. Give in-memory and data-too-large approaches.
14. **Dependency cycle.** Return the actual cycle path, not just boolean, from a directed service graph.
15. **Bounded dispatcher.** Design Java execution for 1,000 tasks/s when downstream sustains only 600/s. Explain queue bound, rejection behavior, deadlines and metrics.
16. **Concurrent deduplication.** Multiple threads receive the same request ID. Exactly one may begin local work. Give a single-JVM design, then explain why it does not solve multi-instance dedupe.

## Required oral prompts

- Compare array, linked list, heap, hash map and balanced tree by operations and memory.
- Explain BFS versus DFS and one case where BFS is wrong.
- Explain expected, amortized and worst-case complexity using one example each.
- Explain atomicity versus visibility using `counter++`.

