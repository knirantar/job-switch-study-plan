# Parent 01 — Coding Foundations

## Outcome

You should be able to turn an unfamiliar problem into a correct Java solution, justify time/space complexity, test edge cases, and communicate trade-offs. This parent is a screening gate: system-design strength cannot compensate for repeatedly failing coding rounds.

## Prerequisites

- Java syntax, methods, classes and generics at a basic level
- A JDK (17 or newer is preferred)
- Paper/notebook for traces and invariants

## Child sequence

| # | Child topic | Exit criterion |
|---|---|---|
| 1 | [Complexity Analysis](01-complexity-analysis/lesson.md) | Derive—not guess—time and auxiliary space |
| 2 | [Arrays and Strings](02-arrays-and-strings/lesson.md) | Manipulate contiguous data and indices safely |
| 3 | [Hashing and Sets](03-hashing-and-sets/lesson.md) | Use lookup/counting/deduplication with correct key semantics |
| 4 | [Linked Lists, Stacks and Queues](04-linked-lists-stacks-queues/lesson.md) | Select structures by operations and preserve invariants |
| 5 | [Trees, Heaps and Tries](05-trees-heaps-tries/lesson.md) | Traverse hierarchies and solve top-k/ordered-prefix problems |
| 6 | [Graphs](06-graphs/lesson.md) | Model relationships; use BFS/DFS/topological ordering |
| 7 | [Problem-Solving Patterns](07-problem-solving-patterns/lesson.md) | Recognize two-pointer, window, binary-search and interval patterns |
| 8 | [Java Concurrency Basics](08-java-concurrency-basics/lesson.md) | Explain races, visibility, atomicity and bounded execution |
| — | [Practice set](practice/problems.md) | ≥80% correct; medium problems ≤35 minutes |
| — | [Integrated capstone](CAPSTONE.md) | ≥80/100 and successful oral defense |

## Four-week micro-plan (24 hours)

- Week A (6h): complexity, arrays, strings; 8 drills.
- Week B (6h): hashing, linked structures, stacks/queues; 8 drills.
- Week C (6h): trees, heaps, graphs; 8 drills.
- Week D (6h): patterns, concurrency, two timed mocks and error review.

If fitting this into the original roadmap, do Weeks A+B during roadmap week 1 and Weeks C+D during week 2.

## Parent completion gate

Coding Foundations is complete only after all eight child exit tests, two consecutive timed-medium successes, the practice diagnostic at 80% or higher, and the integrated capstone at 80/100 or higher. Keep failed cases in the mistake log and repeat them after 1, 3, 7 and 14 days.

## Interview answer template

1. Restate inputs, output and constraints.
2. Ask about null/empty input, duplicates, ordering, range and mutability.
3. Give a simple baseline and its complexity.
4. Identify repeated work or an invariant.
5. Propose the optimized structure/pattern.
6. Walk one normal and one edge case.
7. Code in small, named steps.
8. Test; then state time and **auxiliary** space precisely.
