# Graphs — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `06-graphs`  
**Expected study time:** 2–4 hours plus implementation

## 1. FOUNDATIONS

### Relationships that do not form a hierarchy

A tree gives each non-root node one parent. Real systems are less tidy: one service depends on several services; users follow each other; roads create cycles; model artifacts are shared by deployments; network routes have costs. A **graph** consists of **vertices** (nodes) and **edges** (relationships). It is the general language for connectivity and dependency.

An edge can be **directed** (`u→v`) or **undirected** (`u—v`). It can carry a **weight** such as latency, distance or price. A **path** is a sequence of adjacent vertices; its length may mean number of edges or sum of weights. A **cycle** returns to an earlier vertex. A **simple graph** excludes self-loops and parallel edges, but software models may allow both. A **DAG** is a directed acyclic graph and supports dependency ordering.

An undirected graph’s **connected component** is a maximal set with paths between every pair. In directed graphs, **strongly connected** means mutual reachability; **weakly connected** ignores direction. A vertex’s **degree** counts incident edges; directed graphs distinguish indegree and outdegree.

Graph theory grew from Euler’s 1736 Königsberg bridges problem, which abstracted landmasses and bridges away from geometry. That abstraction now supports routing, scheduling, compilers, build systems, social networks and distributed-system topology.

### Why modeling is the hardest first step

Algorithms operate on the graph you define, not the business story. “A depends on B” can be encoded `A→B` or `B→A`; both are defensible, but topological output reverses. State edge meaning. Decide whether repeated edges matter, whether weight can be negative, and whether vertices with no edges must be included. Many failures blamed on BFS or topological sort are actually modeling errors.

### Representations

An **adjacency list** stores neighbors for each vertex. Space O(V+E), traversal O(V+E), ideal for sparse graphs. An **adjacency matrix** stores a V×V table: O(V²) space, O(1) edge lookup, neighbor scan O(V), useful for dense/small graphs. An **edge list** stores E edges compactly and suits Kruskal sorting or batch processing but neighbor queries require scanning.

For 1,000,000 vertices and 2,000,000 directed edges, a matrix needs one trillion entries; even one bit each is about 116.4 GiB. An adjacency list stores about two million neighbor IDs plus per-vertex/container overhead. Representation can decide feasibility before algorithm choice.

## 2. CORE MECHANICS

### 2.1 BFS

Breadth-first search explores layers from a source using a FIFO queue. Set source distance 0. When first discovering v from u, set `distance[v]=distance[u]+1` and enqueue. Mark on enqueue, not dequeue, so multiple parents do not enqueue duplicates.

BFS returns shortest **edge count** in an unweighted graph because all distance-d vertices leave the queue before distance d+1. It does not minimize arbitrary weights. Time O(V+E) with adjacency lists and O(V) visited/queue; if only reachable vertices are processed, refine to reachable subgraph.

For edges `0→1,0→2,1→3,2→3,3→4`, distances from0 are `[0,1,1,2,3]`; isolated5 is -1. Parent assigned on first discovery reconstructs a shortest path.

### 2.2 DFS

Depth-first search follows one branch before backtracking, using recursion or explicit stack. It supports components, cycle detection, topological ordering and structural timestamps. O(V+E), O(V) visited plus O(V) worst-case stack. Recursive DFS on a million-node chain can overflow Java’s stack; iterative traversal is safer for hostile depth.

In undirected cycle detection, an edge to visited neighbor is a cycle only when neighbor differs from parent; the edge back to parent is expected. In directed graphs, use three states: WHITE unvisited, GRAY active recursion path, BLACK complete. Edge to GRAY is a directed cycle. Edge to BLACK is not.

### 2.3 Topological ordering

A topological order places every prerequisite before its dependent. It exists iff directed graph is acyclic. Kahn’s algorithm computes indegrees, queues all zero-indegree vertices, removes one and decrements outgoing neighbors. If processed count<V, a cycle prevents completion. O(V+E).

Ordering is usually nonunique. A FIFO ready queue depends on insertion order; a min-heap gives deterministic lexicographically smallest available vertex at O((V+E)logV) worst-case. Determinism improves reproducible builds/tests but costs extra.

If edge means dependent→dependency, reverse edges or reverse output before interpreting as deployment sequence.

### 2.4 Unweighted, 0–1 and weighted shortest paths

Choose by weight constraints:

- unweighted/equal weights: BFS;
- weights only 0 or1: 0–1 BFS with deque, zero edges front and one edges back, O(V+E);
- nonnegative weights: Dijkstra;
- negative weights: Bellman–Ford or DAG relaxation if acyclic;
- all pairs: repeated algorithms, Floyd–Warshall O(V³), or specialized choices.

Dijkstra keeps tentative distances in a min-priority queue. Poll smallest state; skip it if distance is stale because Java `PriorityQueue` lacks decrease-key and improved states are reinserted. Relax edge `(u,v,w)` if `dist[u]+w<dist[v]`. With adjacency lists/binary heap, O((V+E)logV), O(V+E) storage. Negative edges invalidate the greedy proof: a “settled” vertex can later improve.

Guard numeric overflow before adding weights. `Long.MAX_VALUE+w` wraps negative.

### 2.5 Bellman–Ford

Relax all E edges V−1 times; any shortest simple path has at most V−1 edges. If another pass improves a reachable distance, a reachable negative cycle exists. O(VE), O(V). A negative cycle only matters to shortest paths reachable from source and able to affect the queried destination under the exact problem.

### 2.6 Union-find

A disjoint-set union (DSU) maintains components under merges. `find(x)` returns representative; `union(a,b)` joins roots. **Path compression** shortens find paths; **union by size/rank** attaches smaller tree under larger. Amortized cost is O(α(n)), inverse Ackermann, effectively constant for practical n.

DSU solves undirected connectivity, redundant-edge detection and Kruskal MST. It does not directly answer paths, directed reachability or deletions.

### 2.7 Minimum spanning trees

For a connected weighted undirected graph, an MST connects all vertices with V−1 edges and minimum total weight. It is not a shortest-path tree: minimizing total network cost differs from minimizing source-to-node paths.

Kruskal sorts edges by weight O(E log E), adds an edge if DSU roots differ, and stops after V−1. Prim grows from a vertex using a priority queue, commonly O(E log V). Negative weights are fine for MST; directed graphs need different concepts. Disconnected input yields a minimum spanning forest unless failure is required.

### 2.8 Strongly connected components

Kosaraju performs DFS finishing order, reverses graph, then DFS in reverse finishing order: O(V+E), requires reverse adjacency. Tarjan uses discovery indices, low links and an active stack in one DFS: O(V+E). Condensing each SCC into one node produces a DAG, useful for dependency-cycle groups.

### 2.9 Grid graphs

A rows×cols grid implicitly defines vertices. Neighbor directions must be explicit: four-direction excludes diagonals; eight-direction includes them. Avoid constructing adjacency lists when neighbors can be computed. Time O(rows×cols), visited storage O(rows×cols), and BFS queue can be large. Validate ragged arrays and integer multiplication when encoding `r*cols+c`.

### 2.10 Multi-source BFS

Enqueue all sources at distance0 before traversal. This finds distance to nearest source in one pass—for example nearest healthy replica or nearest zero cell. Running BFS separately from k sources costs O(k(V+E)); multi-source costs O(V+E) when all edges unweighted and the objective is nearest source.

### 2.11 Production graph limits

Real graphs may not fit memory, change during traversal, or live behind remote APIs. A traversal that calls another service per neighbor suffers network round trips and inconsistent snapshots. Use batched adjacency access, snapshots/versioning, bounded depth/results and authorization. Graph queries can explode due to high-degree hubs even when depth is small.

## 3. WORKED PROBLEMS

### Problem 1 — Shortest service hops

**Statement.** Edges `api→auth`, `api→catalog`, `auth→token`, `catalog→db`, `token→db`. Find minimum hops api to db.

**Solution.** BFS layers: api distance0; auth/catalog1; token/db2. First discovery of db through catalog gives2, which is minimal in edge count. O(V+E)/O(V).

**Mistake caught.** DFS may first find api-auth-token-db length3 and incorrectly stop.

### Problem 2 — Components including isolates

**Statement.** Undirected edges A-B,B-C,D-E and vertex F. Count components.

**Solution.** Include all six vertices in adjacency, including empty F. Start traversal at unvisited A→{A,B,C}; D→{D,E}; F→{F}. Answer3. O(V+E).

**Mistake caught.** Building vertices only from edges omits isolates.

### Problem 3 — Directed cycle

**Statement.** `A→B,B→C,C→A,C→D`. Detect and return cycle.

**Solution.** DFS A gray→B gray→C gray; edge C→A sees gray, proving active-path cycle. Parent links reconstruct A,B,C,A. D is irrelevant. O(V+E).

**Mistake caught.** Treating any edge to a visited BLACK node as a cycle.

### Problem 4 — Deployment order

**Statement.** `api` depends on `auth`; `billing` depends on auth; `web` depends on api.

**Solution.** Encode prerequisite→dependent: auth→api, auth→billing, api→web. Kahn starts auth; then api/billing become ready; choosing lexical can produce auth,api,billing,web, and web becomes ready after api. Multiple valid orders exist. O(V+E).

**Mistake caught.** Using dependent→prerequisite and reading output without reversal.

### Problem 5 — Dijkstra trace

**Statement.** Edges `0→1(4),0→2(1),2→1(2),1→3(1),2→3(5),3→4(3)`.

**Solution.** Start d0=0. Relax d1=4,d2=1. Poll2; improve d1=3,d3=6. Poll1 at3; improve d3=4. Old state1=4 later is stale and skipped. Poll3=4; d4=7. Distances `[0,3,1,4,7]`. O((V+E)logV).

**Mistake caught.** Marking vertex visited when enqueued prevents later improvement.

### Problem 6 — Negative edge

**Statement.** `S→A(2),S→B(5),B→A(-10)`. Can Dijkstra safely settle A at2?

**Solution.** No. Path S-B-A costs -5, improving A after B. Dijkstra’s nonnegative assumption is violated. Bellman–Ford relaxes edges and finds -5. There is no negative cycle here.

**Mistake caught.** Assuming “no negative cycle” is sufficient for Dijkstra; every edge must be nonnegative.

### Problem 7 — Redundant network edge

**Statement.** Undirected edges `(0,1),(1,2),(2,3),(0,2)`. Identify first edge creating a cycle.

**Solution.** DSU unions first three. For `(0,2)`, both roots already match, so adding it forms cycle. Near O(Eα(V)), O(V).

**Mistake caught.** Using DSU for directed cycle detection where reachability direction matters.

### Problem 8 — Minimum cable cost

**Statement.** Undirected edges AB1, AC4, BC2, BD5, CD3. Find MST.

**Solution.** Sort weights: AB1,BC2,CD3,AC4,BD5. Kruskal accepts AB,BC,CD; now 4 vertices connected with 3 edges, total6. AC would cycle. O(E logE).

**Mistake caught.** Computing shortest paths from A and calling their total an MST.

### Problem 9 — Multi-source failure distance

**Statement.** Grid rows `00100/00000/10001`, where 1 marks healthy node. Find distance of every cell to nearest healthy node using four directions.

**Solution.** Enqueue all four? Actual ones at (0,2),(2,0),(2,4), three sources, each distance0. BFS expands simultaneous layers; each cell’s first visit comes from nearest source. O(15), O(15). Separate BFS per cell would be quadratic-scale.

**Mistake caught.** Enqueuing only one source or permitting diagonals without specification.

## 4. REAL-WORLD / APPLIED CONTEXT

### Build and deployment DAGs

Maven/Gradle, Airflow and CI systems model tasks/dependencies as DAGs. Topological scheduling identifies ready work; cycle diagnostics must return a useful path, not merely “sort failed.” Resource constraints mean ready tasks cannot all necessarily run. Dynamic workflow generation must preserve deterministic IDs and snapshot semantics.

### Network routing

OSPF uses a link-state database and shortest-path-first computation based on Dijkstra. Edge weights represent configured cost, not necessarily physical distance. Real routing adds convergence, equal-cost multipath and changing topology. Complexity explains recomputation; protocol correctness handles distributed state.

### Service and trace graphs

OpenTelemetry traces form directed parent/child span structures, often trees per trace but links can make richer graphs. Service dependency graphs aggregate calls and may contain cycles. High-cardinality graphs require sampling/storage policies; a recursive UI expansion must bound depth and nodes.

The Java lab compiles and verifies BFS unreachable handling, deterministic Kahn ordering, cycle rejection, stale-state Dijkstra with overflow/negative guards and path-compressed union-find.

## 5. COMPARISON TABLE

| Problem | Algorithm | Weight rule | Time | Key boundary |
|---|---|---|---:|---|
| reachability/components | BFS/DFS | irrelevant | O(V+E) | direction/visited |
| shortest edge count | BFS | equal/unweighted | O(V+E) | mark on enqueue |
| shortest 0/1 cost | 0–1 BFS | only 0 or1 | O(V+E) | deque placement |
| single-source shortest | Dijkstra | nonnegative | O((V+E)logV) | stale states/overflow |
| negative weights | Bellman–Ford | any, detect negative cycle | O(VE) | reachable cycle semantics |
| DAG shortest paths | topo relaxation | any in DAG | O(V+E) | acyclicity/order |
| all pairs, dense/small | Floyd–Warshall | handle negatives, no negative cycles for finite shortest | O(V³) | O(V²) space |
| dynamic undirected connectivity | union-find | no paths/deletions | amortized O(α(V)) | not directed reachability |
| minimum spanning network | Kruskal/Prim | undirected | O(ElogE)/O(ElogV) | not shortest paths |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Edge direction unspecified.** Dependency order becomes reversed.
2. **Omitting isolated vertices.** Components/topological counts become wrong.
3. **Marking BFS visited on dequeue.** Duplicates inflate queue and parents become unstable.
4. **DFS first path is shortest.** Only BFS guarantees unweighted shortest paths.
5. **BFS handles weighted edges.** It minimizes edges, not arbitrary sum.
6. **Dijkstra with negative edges.** Greedy settlement fails.
7. **Any directed visited edge is a cycle.** Only edge to active GRAY path proves DFS cycle.
8. **Topological order is unique.** Multiple zero-indegree choices yield many valid orders.
9. **Recursive DFS always safe.** Deep graphs overflow stack.
10. **MST equals shortest-path tree.** Total network cost and source distances differ.
11. **Union-find answers paths/direction.** It only tracks undirected component equivalence under unions.
12. **O(V+E) means cheap remotely.** Per-edge network calls and high-degree hubs dominate.
13. **Distance addition cannot overflow.** Guard long sentinel arithmetic.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full sections.

- Define vertex, edge direction, weight, duplicates, isolates first.
- Adjacency list O(V+E); matrix O(V²).
- BFS queue: unweighted shortest hops; mark on enqueue.
- DFS stack: structure/cycles/components; directed states white/gray/black.
- Topological order iff DAG; Kahn processed<V means cycle.
- Dijkstra nonnegative; skip stale heap states.
- Bellman–Ford handles negative weights/detects reachable negative cycles.
- DSU: undirected incremental connectivity, near-constant amortized.
- MST minimizes total connection cost, not source paths.
- SCC condenses directed cycles into DAG.
- Multi-source BFS enqueues every source at distance0.

## 8. PRACTICE SET FOR SELF-TEST

1. For an undirected graph with V=10M,E=15M, state adjacency-entry count and BFS complexity.
2. Find shortest hops from A to F in edges A-B,A-C,B-D,C-D,D-E,E-F,C-F.
3. Give a valid topological order for prerequisites `db→api`, `auth→api`, `api→web`, `auth→worker` and state whether unique.
4. Detect whether undirected edges 0-1,1-2,2-3,3-1 contain cycle and explain parent handling.
5. Compute shortest distances from S for S-A4,S-B1,B-A2,A-C1,B-C7.
6. Run Bellman–Ford logic on A→B1,B→C-2,C→A0 and determine negative cycle.
7. Explain when 0–1 BFS beats Dijkstra and trace edges 0→1(1),0→2(0),2→1(0).
8. Kruskal on weights AB4,AC1,BC2,BD1,CD5: give MST total.
9. Explain how SCC condensation helps deploy a graph with mutual dependencies.
10. Design protections for a “show dependency graph to depth 5” API against one vertex with 2M neighbors.

## 9. CURATED RESOURCES

1. **Cormen et al., *Introduction to Algorithms*, 4th ed., Chapters 19–24.** Graph representations, BFS/DFS, MST, shortest paths and formal proofs.
2. **Sedgewick & Wayne, *Algorithms*, 4th ed., Chapter 4.** Java graph APIs and practical implementations.
3. **Dijkstra, “A Note on Two Problems in Connexion with Graphs” (1959).** Original shortest-path and spanning-tree formulation.
4. **Bellman, “On a Routing Problem” (1958); Ford’s related work.** Foundations of repeated edge relaxation.
5. **Tarjan, “Depth-First Search and Linear Graph Algorithms” (1972).** SCC and biconnected algorithms with linear analysis.
6. **Tarjan, “Efficiency of a Good But Not Linear Set Union Algorithm” (1975).** Formal union-find amortized analysis.
7. **RFC 2328, OSPF Version 2, shortest-path tree sections.** Production link-state routing use of SPF.
8. **Apache Airflow documentation, DAGs and task dependencies.** Real workflow DAG semantics and scheduling.
9. **OpenTelemetry Trace specification.** Real span parent/link graph semantics.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Trees, Heaps and Tries.** Trees are acyclic graphs; heaps implement Dijkstra/Prim priority queues.
2. **Stacks and Queues.** DFS and BFS depend directly on these frontiers.
3. **Hashing and Sets.** Visited sets and vertex maps support sparse identifiers.

### After

1. **Problem-Solving Patterns.** Graph modeling, state-space BFS and union-find recur in advanced problems.
2. **Distributed Systems.** Dependency, quorum and network-partition graphs add failure/time semantics.
3. **Kafka/Eventing.** Consumer/task DAGs and partition ordering connect graph dependencies to streams.
4. **Airflow and ML Pipelines.** DAG scheduling becomes an operational platform concern.
5. **System Design.** Routing, service topology and workflow orchestration use graph trade-offs at scale.

---ANSWER KEY BELOW---

1. Undirected adjacency lists normally store each edge twice: 30M neighbor entries. BFS O(10M+15M), memory O(V+E) plus representation overhead.
2. BFS finds A-C-F in2 edges, shorter than routes through D/E.
3. Initial db/auth. One valid deterministic order auth,db,api,web,worker or db,auth,api,web,worker depending ready policy; worker can move after auth. Not unique.
4. Yes: during DFS 0→1→2→3, edge3→1 reaches visited neighbor that is not parent2. Cycle1-2-3-1.
5. Distances S0,B1,A3 via B,C4 via A. Dijkstra nonnegative.
6. Cycle total `1-2+0=-1`, negative and reachable from A, so another relaxation remains possible.
7. Weights restricted 0/1; deque yields O(V+E). Process0: put2 front(d0),1 back(d1); process2 improves1 to0 and puts front. Distances 0,0,0.
8. Sort AC1,BD1,BC2,AB4,CD5. Accept AC,BD,BC connecting all four; total4.
9. Each SCC identifies vertices that cannot be topologically separated due to mutual reachability. Condensed SCC nodes form DAG; deploy cycle group together, reject, or redesign it, then order groups.
10. Enforce per-request node/edge/result/byte/time budgets, paginate high-degree adjacency, authorize before expansion, cache/snapshot, return truncation metadata, rate-limit and avoid fetching two million neighbors just to discard them.
