# Coding Foundations Capstone — Production Event Analyzer

## Prerequisite gate

Complete all eleven lessons before starting. From a clean checkout, compile and run a small Java program without an IDE, explain variables/control flow/method calls, debug one malformed input, and write tests for boundary values. Then implement one recursive routine with a stated base case, binary search, one comparison sort, and one bit-mask operation. For each implementation, derive time and auxiliary-space complexity rather than quoting it from memory. This gate ensures the analyzer is built on programming fluency, debugging discipline, recursion/search/sort mechanics and discrete-math/bit foundations—not only memorized data-structure patterns.

## Scenario

Build a Java command-line analyzer for request events. Each event has:

```text
timestampEpochMs,tenantId,requestId,endpoint,status,latencyMs,parentRequestId
```

Generate or load at least 1,000,000 events with 100 tenants, 250 endpoints, 2% 5xx responses, 1% duplicate request IDs, timestamps across 24 hours, and a sparse parent-request graph. Include one tenant producing 35% of traffic and one deliberate dependency cycle.

## Required features

1. Deduplicate by `(tenantId,requestId)` while reporting conflicting duplicate payloads.
2. Return top 100 endpoints by 5xx count with deterministic tie order.
3. Calculate rolling 5-minute maximum request count from minute buckets.
4. Return p50/p95/p99 latency using a documented exact approach; explain why repeated sorting per query is wasteful.
5. Detect and return a cycle path in the parent-request graph.
6. Produce a valid topological order after removing the deliberate cycle.
7. Process tenant summaries concurrently while bounding task submission and preserving deterministic output.
8. Expose time and auxiliary-space analysis for every operation.

## Correctness requirements

- Use immutable composite keys with correct equality/hash semantics.
- Accumulate counts/timestamps in `long` and handle parsing/range failures.
- State Unicode assumptions for tenant/endpoint identifiers.
- Avoid recursion for adversarial graph depth.
- Never rely on `PriorityQueue` iteration for sorted output.
- Concurrency must not mutate unsynchronized shared collections.
- Tests cover empty input, one event, all duplicates, tie counts, disconnected graph, self-loop, long chain, cancellation and queue saturation.

## Target architecture

- Streaming parser validates and emits immutable records.
- Hash map/set performs exact deduplication and counts.
- Arrays/buckets compute time windows.
- Size-100 heap selects top endpoints; final list receives explicit comparator sort.
- Adjacency lists plus iterative three-state DFS detect/reconstruct cycles; Kahn provides topological order.
- Fixed/bounded executor runs independent per-tenant aggregation; results are merged in sorted tenant order.

## Evaluation rubric (100 points)

| Area | Points | Evidence |
|---|---:|---|
| Correctness and edge cases | 25 | automated tests and invariant explanations |
| Complexity and memory | 15 | tight bounds with n,u,V,E and measured heap use |
| Data-structure selection | 15 | explicit alternatives/rejected trade-offs |
| Java quality | 15 | immutable models, clear APIs, no hidden overflow |
| Concurrency safety | 15 | bounded execution, cancellation, deterministic merge |
| Communication | 10 | 15-minute design/code walkthrough |
| Measurement quality | 5 | warm-up/method disclosure; no universal claims from one run |

Passing requires at least 80 overall and no zero in correctness or concurrency safety. After passing, reimplement two selected operations under a 45-minute interview timer without consulting the project.

## Oral defense questions

1. At what event/endpoint cardinality does the exact map stop fitting memory, and what would you change?
2. Why is top-100 `O(n+u log 100)` rather than `O(n log n)`?
3. How would graph semantics change if one request may have several parents?
4. What is still unsafe if each per-tenant aggregator is thread-safe but the final result list is not?
5. How would the design change when events arrive continuously across multiple service instances?
