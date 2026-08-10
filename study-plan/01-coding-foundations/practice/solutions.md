# Worked Solutions

## Diagnostic

1. O(n): total pointer movement is n, not n per outer iteration. State O(1) space if only indices.
2. Hash map value→earliest index; check complement before insert. Expected O(n)/O(n).
3. `ArrayDeque<Character>` stack; reject mismatch/empty and leftover openings. O(n)/O(n).
4. BFS, marking visited on enqueue; O(V+E)/O(V).
5. Increment is read-modify-write. Volatile makes reads/writes visible but two threads can read the same old value. Use `AtomicInteger`, `LongAdder` for metrics, or locking for a broader invariant.

## Level 1

1. Maintain `write`; copy nonzeroes, then fill suffix. Each item read once: O(n)/O(1).
2. Count the smaller array in a map. Scan the other; emit and decrement when count >0. O(n+m) expected and O(min(n,m)) space.
3. Push into `in`. For dequeue, if `out` empty, move all `in→out`, then pop. Each element is pushed/popped a constant number of times: amortized O(1), worst individual dequeue O(n).
4. `height(node)=node==null?0:1+max(height(left),height(right))`; O(n), stack O(h). A skewed million-node tree risks stack overflow; use iterative traversal.
5. Build undirected adjacency, include all vertices even with no edges, and start BFS/DFS at every unvisited vertex. O(V+E).

## Level 2

6. Map char→last index. `left=max(left,last+1)`; update best with `right-left+1`. O(n)/O(character set).
7. Prefix frequency starts `{0:1}`. At each sum `s`, add count of `s-k`, then increment `s`. For the given input, four subarrays sum to 7. O(n)/O(n).
8. Frequency map then min-heap size k. O(n+u log k)/O(u+k). State tie rule.
9. Convert prerequisites to edges `auth→api`, `auth→billing`, `api→web`; Kahn may return `auth,api,billing,web`. O(V+E).
10. Search `[max(weights)=10,sum=55]`. `can(capacity)` greedily starts a new day before exceeding capacity. First feasible value is 15. O(n log 46)/O(1).
11. Sort by start, extend current end while next start ≤ current end; otherwise emit current. O(n log n), with sorting auxiliary space implementation-dependent.
12. Map key→node plus doubly linked recency list. `get` moves to front; full `put` evicts tail. Expected O(1) operations, O(capacity).

## Level 3

13. Count only 5xx per endpoint in a map; retain top 100 in a min-heap: O(n+u log 100), O(u). If cardinality/data does not fit, hash-partition records, aggregate partitions, then merge local top candidates; for approximate streaming use a heavy-hitters sketch with an explicit error bound.
14. DFS states plus `parent`. On edge `u→v` where v is GRAY, walk parents from u back to v, reverse and close the cycle. O(V+E), O(V).
15. Arrival exceeds service by 400/s, so any finite queue eventually fills. Use bounded queue sized from acceptable wait, e.g. 600 slots ≈1 second at service capacity, bounded executor/semaphore, reject with 429/503 or durable admission, propagate deadlines and report queue depth, rejection rate, wait time and downstream saturation. More threads do not create downstream capacity.
16. `ConcurrentHashMap.putIfAbsent(requestId, IN_PROGRESS)` elects one local owner; carefully define completion/expiry and memory bounds. Across instances, use a database unique constraint/conditional write or durable idempotency record. A distributed lock without a durable result and fencing is not enough.

