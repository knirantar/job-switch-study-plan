# Trees, Heaps and Tries — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `05-trees-heaps-tries`  
**Expected study time:** 2–4 hours plus implementation

## 1. FOUNDATIONS

### Hierarchy and partial order

Linear structures give each element at most one next position. Many domains branch: directories contain files/directories, an organization contains teams, a query plan contains child operators, and an index divides key ranges. A **tree** models hierarchy as **nodes** joined by **edges** with one distinguished **root** and no cycles. Every non-root node has one parent; nodes with no children are **leaves**. A node’s **depth** is edges from root; its **height** is the longest downward edge path to a leaf. Some texts count nodes instead of edges—state the convention.

A **binary tree** gives each node at most left and right children. It is not automatically ordered. A **binary search tree (BST)** adds an invariant: every key in a node’s left subtree is less than the node and every key in the right is greater, under a declared duplicate policy. This global subtree rule—not merely comparison with immediate children—enables ordered search.

A **balanced search tree** limits height to O(log n). AVL and red-black trees maintain different balance conditions during updates. Without balancing, inserting sorted values 1,2,3,… into a plain BST creates a chain of height n, degrading search/insert/delete from O(log n) to O(n). Java `TreeMap`/`TreeSet` use a red-black tree implementation and provide O(log n) basic ordered operations.

A **heap** is a different partial order. In a min-heap every parent is no greater than its children, so only the minimum is guaranteed at the root. The rest is not globally sorted. A **priority queue** uses a heap to insert tasks and remove the current extreme efficiently.

A **trie** (prefix tree) stores keys along root-to-node paths, usually one symbol per edge. Shared prefixes are physically shared: `care`, `card` and `cat` share `ca`. Lookup depends on key length rather than number of stored keys, but nodes/child maps can consume large memory.

### Motivation and history

Tree structures date through mathematical genealogy and classification, becoming central in early computing for search and syntax. Balanced trees such as AVL (1962) and red-black trees (1970s) solved pathological height under dynamic updates. Heaps, introduced with heapsort by J. W. J. Williams in 1964, offered compact priority management. Tries were named by Edward Fredkin from “retrieval” and support dictionaries and prefix matching.

Without correct distinctions, candidates claim heap search is logarithmic, validate only local BST relationships, recurse into stack overflow, or use a 26-child trie for arbitrary Unicode and enormous sparse memory. Production systems also care about persistence, concurrency, page layout and cache behavior beyond textbook costs.

## 2. CORE MECHANICS

### 2.1 Structural classifications

A **full** binary tree has every node with 0 or 2 children. A **complete** tree fills every level except possibly the last, which fills left-to-right; array heaps use this shape. A **perfect** tree has all internal nodes with 2 children and all leaves at one depth; with height h in edges, it has `2^(h+1)-1` nodes. A **balanced** tree informally keeps height logarithmic, but exact definitions depend on the structure.

For a complete tree stored zero-based in an array, parent of i is `(i-1)/2`; children are `2i+1` and `2i+2` if within size. No node pointers are required.

### 2.2 Traversals

Depth-first traversals differ by when the node is processed:

- preorder: node, left, right—copying/serialization and prefix structure;
- inorder: left, node, right—sorted keys for a valid BST;
- postorder: left, right, node—child results before parent, deletion/size computation.

Level-order traversal is BFS with a queue and visits by depth. All visit n nodes: O(n). Recursive DFS stack is O(h), which is O(log n) balanced and O(n) skewed. BFS queue is O(w), maximum width, worst O(n).

Iterative inorder pushes the entire left spine, pops one node, then explores its right. Its invariant: stack contains ancestors whose left subtree is complete but whose node is not yet emitted.

### 2.3 BST search and validation

Search compares target to current and chooses one subtree: O(h). Validation passes an allowed interval down the tree. At node 5, left descendants inherit upper 5; a node 6 deep inside the left subtree violates it even if it is greater than its immediate parent 3. Use long bounds for int keys so `Integer.MIN_VALUE/MAX_VALUE` remain legal values. Strict bounds reject duplicates; a duplicate policy changes inequalities and must be consistent.

### 2.4 BST deletion

Deletion has three cases. Leaf: remove it. One child: replace node link with child. Two children: replace key/value with inorder successor (minimum in right subtree) or predecessor, then delete that source node, which has at most one child. O(h). If nodes carry identity or external references, copying a key may violate semantics; transplant nodes carefully.

Balanced-tree rotation/recoloring details are beyond ordinary BST interviews but you should know why library ordered maps stay logarithmic.

### 2.5 Lowest common ancestor

In a general binary tree, recurse. If root is null/p/q, return it. If left and right both return non-null, root is the split point; otherwise propagate the non-null side. O(n)/O(h). This assumes both targets exist if the specification does; otherwise add presence validation.

In a BST, compare both target keys with current. If both smaller go left; both larger go right; otherwise current is split. O(h).

### 2.6 Tree serialization

Values alone do not preserve shape. Preorder with null markers uniquely records a binary tree. For `5` with left `3` and no right, encoding can be `5,3,#,#,#,`. Deserialization consumes tokens recursively in the same grammar. O(n) time/output. Production formats need escaping/length framing, validation, depth limits and versioning; comma splitting is only a controlled integer demonstration.

### 2.7 Heap mechanics

In a min-heap, insertion appends at end then **sifts up** while smaller than parent: O(log n). Removing minimum swaps/moves last value to root, shrinks size and **sifts down** with smaller child: O(log n). Peek is O(1). Searching/removing an arbitrary value is O(n) because heap order cannot choose one branch.

Building a heap bottom-up from n values is O(n), not O(n log n): most nodes are near leaves and move little. Repeated insertion is O(n log n). Heap sort builds heap O(n), then performs n O(log n) removals: O(n log n), in-place for array implementation, not stable.

Java `PriorityQueue` is a min-heap by natural/comparator order. Its iterator is not sorted. Use repeated `poll` (destructive) or copy and sort when ordered output is required.

### 2.8 Top-k

To keep k largest from n streaming values, maintain a min-heap of size k. Until full, insert. Later, if x exceeds root (smallest retained), replace root. At completion heap contains k largest but not ordered. O(n log k), O(k).

For `[5,1,9,3,12,7]`, k=3: heap evolves to `{1,5,9}`, 3 replaces1→`{3,5,9}`, 12 replaces3→`{5,9,12}`, 7 replaces5→`{7,9,12}`. Sort retained output descending if required, adding O(k log k).

When k is near n and all results need sorting, full sort may be simpler/faster. Quickselect gives expected O(n) selection but mutates input and does not fully order top k.

### 2.9 Trie operations

Insert follows/creates an edge for each symbol and marks terminal. Lookup succeeds only if the path exists **and terminal is true**; otherwise a prefix such as `cat` would incorrectly count as stored when only `cater` exists. Prefix lookup needs only the path.

For key length L symbols, operation time O(L), independent of number of keys under assumed child lookup. Space is O(total created prefix nodes). A fixed 26-pointer array makes child access O(1) but allocates 26 references per node; a map saves sparse slots but adds hashing/object overhead. Compressed radix trees merge single-child paths; ternary search tries trade branching memory for comparisons.

Unicode requires defining symbol unit and normalization. `é` can be one code point or `e` plus combining accent; visually equal text may follow different trie paths unless normalized. Case folding and locale rules also matter.

### 2.10 Augmented trees

Nodes can store subtree size, sum, max or interval endpoint. An order-statistic tree finds kth key/rank in O(log n) when balanced and sizes are correctly maintained. Interval trees prune overlap searches using maximum endpoint. The augmentation update must be preserved across insertion, deletion and rotations; stale metadata silently corrupts answers.

## 3. WORKED PROBLEMS

### Problem 1 — Traversals

**Statement.** Root 5 has left 3 (children 2,4) and right 8. Give traversals.

**Solution.** Preorder `5,3,2,4,8`; inorder `2,3,4,5,8`; postorder `2,4,3,8,5`; level order `5,3,8,2,4`. Each O(5); DFS stack height 3 nodes.

**Mistake caught.** Calling any binary-tree inorder sorted without first proving BST validity.

### Problem 2 — Deep BST violation

**Statement.** Root 5, left child 3 whose right child is 6, right child 8. Valid?

**Solution.** No. Although 6>3, it is in the entire left subtree of 5 and must be <5. Bounds at 6 are `(3,5)`, which it violates. O(n)/O(h).

**Mistake caught.** Comparing only parent-child pairs.

### Problem 3 — Delete two-child BST node

**Statement.** Delete 5 from BST keys `{2,3,4,5,7,8,9}` where 5 is root.

**Solution.** Choose successor: minimum in right subtree, e.g. 7. Replace/transplant 5 with 7, then delete original 7 position, which has no left child. Inorder remains `2,3,4,7,8,9`. O(h). Exact links depend on shape.

**Mistake caught.** Removing root and attaching both subtrees arbitrarily, breaking order.

### Problem 4 — Lowest common ancestor

**Statement.** In the first tree, find LCA of nodes 2 and 4.

**Solution.** Node3 receives non-null from both children, so returns itself. Root5 receives node3 from left and null right, propagates3. Answer node3. O(n)/O(h).

**Mistake caught.** Matching values when duplicate-valued distinct nodes are allowed; use identity under node-reference problem.

### Problem 5 — Maximum path sum

**Statement.** For root `-10`, children 9 and 20, with 20’s children 15 and 7, find maximum path sum.

**Solution.** Postorder gain from child is `max(0, child value + one best child gain)`. At20, through-path is 15+20+7=42; upward gain is 20+15=35. Root through is -10+9+35=34. Global maximum remains42. O(n)/O(h).

**Mistake caught.** Returning a path that branches upward; parent can receive only one child branch.

### Problem 6 — Top three values

**Statement.** Return top3 from `[5,1,9,3,12,7]`.

**Solution.** Maintain min-heap size3 as traced above; retained `{7,9,12}`, ordered output `[12,9,7]`. O(n log3), O(3), plus O(3 log3) output sort.

**Mistake caught.** Assuming heap iteration is sorted or using max-heap of all n and O(n) memory.

### Problem 7 — Merge k sorted streams

**Statement.** Merge `[1,7,20]`, `[2,3,18]`, `[5,6,9]`.

**Solution.** Put first item of each stream in min-heap with stream/index. Poll1, push7; poll2,push3; poll3,push18; poll5,push6; continue →`1,2,3,5,6,7,9,18,20`. N=9,k=3: O(N log k), O(k).

**Mistake caught.** Loading/sorting all N values O(N log N) when streaming constraints matter.

### Problem 8 — Trie semantics

**Statement.** Insert `care`, `card`, `cat`. Evaluate contains(`car`), prefix(`car`), contains(`care`).

**Solution.** Path c-a-r exists, so prefix true; its node terminal is false, so contains car false. Care path ends terminal true. Each lookup O(L).

**Mistake caught.** Treating every prefix node as a complete key.

### Problem 9 — Serialize shape

**Statement.** Show why preorder values `1,2,3` are ambiguous and fix it.

**Solution.** Root1-left2-left3 and root1-left2-right3 share preorder values. Add null markers: first `1,2,3,#,#,#,#`; second `1,2,#,3,#,#,#`. Grammar preserves shape. O(n) tokens including null positions.

**Mistake caught.** Serializing only values and claiming reversible structure.

## 4. REAL-WORLD / APPLIED CONTEXT

### Java ordered maps and priority queues

`TreeMap` supplies guaranteed O(log n) `containsKey`, `get`, `put` and `remove` under its API contract and supports navigation such as floor/ceiling/ranges. `PriorityQueue` documents O(log n) offer/poll, O(1) peek and O(n) contains/remove-by-object. Those exact distinctions prevent hidden quadratic code.

### Database indexes

PostgreSQL B-tree indexes are multiway, page-oriented balanced trees, not binary trees. They support equality and ordered/range queries while minimizing storage-page I/O through high fan-out. If a node/page holds hundreds of child pointers, a billion-row index can have only a few levels. Real performance also depends on selectivity, heap access, caching and write amplification; use `EXPLAIN (ANALYZE, BUFFERS)`.

### Scheduling and routing

Schedulers use priority queues for earliest deadline/next event, but changing priorities may require indexed heaps or reinsertion/versioning. Routers/autocomplete use compressed prefix structures for longest-prefix match. Production tries often compress paths and store byte prefixes to control memory.

The accompanying Java lab compiles and checks iterative inorder, global-bound BST validation, identity LCA, top-k ordering, Unicode code-point trie semantics and serialization round-trip.

## 5. COMPARISON TABLE

| Structure | Search | Insert/delete | Ordered/range | Key advantage | Main cost |
|---|---:|---:|---|---|---|
| plain BST | O(h), worst O(n) | O(h) | yes | simple order | can skew |
| balanced BST | O(log n) | O(log n) | yes | predictable dynamic order | rotations/metadata |
| hash map | expected O(1) | expected O(1) amortized | no | exact association | memory/no ranges |
| sorted array | O(log n) | O(n) | yes | locality/compact | expensive updates |
| min-heap | min O(1), arbitrary O(n) | O(log n) | only extreme | top-k/scheduling | not globally sorted |
| trie | O(L) | O(L) | prefix/lexical traversal | prefix sharing | node memory/normalization |
| radix tree | O(L) | O(L) | prefixes | compresses chains | complex splits/merges |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Binary tree equals BST.** Ordering is an additional global invariant.
2. **Local BST validation.** Descendant bounds matter.
3. **BST always O(log n).** Unbalanced height can be n.
4. **Recursive DFS O(1) space.** Stack is O(h).
5. **Heap is sorted.** Only parent/extreme guarantee; arbitrary search O(n).
6. **Heap build O(n log n).** Bottom-up heapify is O(n).
7. **PriorityQueue iteration sorted.** Java does not guarantee it.
8. **Top-k always max-heap.** A min-heap of size k bounds memory and exposes replacement threshold.
9. **Trie lookup O(1).** It is O(key length), with child-operation assumptions.
10. **Prefix means word.** Terminal marker distinguishes complete keys.
11. **`char` trie handles Unicode characters.** It stores UTF-16 units; define code points/normalization.
12. **Serialization values preserve shape.** Null markers or equivalent structure are required.
13. **LCA answer valid if one target absent.** Problem contract must specify/existence must be checked.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the complete sections.

- Tree: connected acyclic hierarchy; h controls DFS/search space.
- DFS preorder=NLR, inorder=LNR, postorder=LRN; BFS uses queue.
- BST invariant is global; validate with propagated bounds.
- Balanced BST operations O(log n); plain BST worst O(n).
- Two-child delete uses successor/predecessor then deletes source.
- Heap: peek extreme O(1), offer/poll O(log n), arbitrary search O(n).
- Bottom-up heapify O(n).
- Top-k largest: min-heap size k, O(n log k)/O(k).
- Trie operation O(L); terminal distinguishes key from prefix.
- DFS stack O(h), BFS queue O(width).
- Serialization must encode null/shape and validate hostile depth/input.

## 8. PRACTICE SET FOR SELF-TEST

1. Give all traversals for root10, left5(children2,7), right15(left12).
2. Determine whether preorder `[8,5,1,7,10,12]` can describe a BST and reconstruct it.
3. Find kth smallest in a BST using O(h+k) time and O(h) space.
4. Explain heap states when inserting `8,3,10,1,6` into a min-heap.
5. Find median of stream `5,15,1,3` using two heaps after every insertion.
6. Calculate top-100 complexity for 50M events with 2M distinct keys after counting.
7. Design trie deletion so deleting `car` does not remove `card`.
8. Explain why NFC normalization matters for trie keys `é` and `e`+combining acute.
9. Analyze BFS memory for a perfect binary tree with 1,048,575 nodes.
10. State protections required when deserializing an untrusted recursive tree encoding.

## 9. CURATED RESOURCES

1. **Cormen et al., *Introduction to Algorithms*, 4th ed., Chapters 6, 12, 13 and 14.** Heaps, BSTs, red-black balancing and augmentation.
2. **Sedgewick & Wayne, *Algorithms*, 4th ed., §§2.4, 3.2–3.3 and 5.2.** Java heaps, search trees and tries.
3. **Oracle Java SE API, `TreeMap`, `TreeSet`, `PriorityQueue`.** Exact performance and iteration/ordering contracts.
4. **Adelson-Velsky and Landis, “An algorithm for the organization of information” (1962).** Original AVL balancing motivation.
5. **Williams, “Algorithm 232: Heapsort” (1964).** Original heap-based sorting presentation.
6. **Fredkin, “Trie Memory” (1960).** Early trie formulation and naming.
7. **PostgreSQL documentation, Chapter 11 “Indexes,” B-tree sections.** Connects ordered trees to page-based production indexing.
8. **Unicode Standard Annex #15, Unicode Normalization Forms.** Exact normalization requirements for text keys.
9. **Okasaki, *Purely Functional Data Structures*, tree/heap chapters.** Adds persistence and structural sharing beyond mutable Java implementations.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Complexity Analysis.** Height, width and log bounds determine tree/heap performance.
2. **Linked Lists, Stacks and Queues.** Tree nodes generalize links; traversals use stacks/queues.
3. **Hashing and Sets.** Hashes are the unordered alternative; visited sets support traversals.

### After

1. **Graphs.** Trees are a restricted graph; graph traversal adds cycles, components and multiple paths.
2. **Problem-Solving Patterns.** Recursive decomposition, heap top-k and binary-search-tree order recur in interviews.
3. **Database Indexes.** B-trees translate ordered search into page-aware persistent structures.
4. **Schedulers and Kafka.** Heaps prioritize time; partitioned logs add distributed ordering/failure.

---ANSWER KEY BELOW---

1. Preorder `10,5,2,7,15,12`; inorder `2,5,7,10,12,15`; postorder `2,7,5,12,15,10`; level order `10,5,15,2,7,12`.
2. Yes: 8 root; 5 left with 1 left/7 right; 10 right with 12 right. Validate preorder with bounds/stack, not arbitrary insertion alone.
3. Iterative inorder; after popping k nodes return kth. O(h+k) assuming early stop, O(h). Validate k range.
4. `[8]`; insert3 sift→`[3,8]`; 10→`[3,8,10]`; 1 sifts past8 and3→`[1,3,10,8]`; 6→`[1,3,10,8,6]`.
5. Max-heap lower/min-heap upper: medians 5;10;5;4. Rebalance size difference≤1 and lower max≤upper min.
6. Counting expected O(50M), O(2M) map. Heap selection O(2M log100), O(100) extra; total expected O(50M+2M log100).
7. Unmark terminal at car. Recursively remove a node only if nonterminal and childless; shared path to card remains.
8. They can render alike but have different code-point sequences, producing different paths. Normalize both to a documented form such as NFC before insert/query.
9. Perfect tree has last level `(n+1)/2=524,288` nodes; BFS queue is Θ(n) and may hold roughly that many references near the last level.
10. Bound input bytes, token count, numeric range and maximum depth/nodes; reject malformed/trailing/missing tokens; avoid recursive stack overflow; authenticate/authorize format use and version it.
