# Linked Lists, Stacks and Queues — Complete Study Resource

**Parent:** `01-coding-foundations`  
**Child:** `04-linked-lists-stacks-queues`  
**Expected study time:** 2–4 hours plus coding practice

## 1. FOUNDATIONS

### Why restricted structures exist

An array gives indexed access, but many problems do not need arbitrary access. A parser needs “the most recently opened delimiter.” A request scheduler needs “the oldest waiting task.” An undo feature needs “the most recent action.” Encoding those policies directly into data structures reduces both implementation cost and the number of illegal operations.

A **linked list** stores elements in nodes connected by references rather than one contiguous block. A singly linked node contains a value and a `next` reference. A doubly linked node adds `previous`. The first node is the **head**; the last is the **tail**. A list segment ending in `null` is **acyclic**; if a next-reference reaches an earlier node, it contains a **cycle**.

A **stack** is last-in, first-out (LIFO): push adds to the top, pop removes the top, peek observes it. A **queue** is usually first-in, first-out (FIFO): enqueue at the tail and dequeue at the head. A **deque** (double-ended queue) supports insertion and removal at both ends. A **priority queue** is not FIFO; it removes by priority and belongs with heaps.

These abstractions are ancient in concept—queues model waiting lines and stacks model piled objects. In computing, stacks became fundamental to expression evaluation, subroutine calls and compiler parsing; queues underpin scheduling, breadth-first search and messaging. Linked lists enabled dynamic collections when contiguous reallocation was expensive or impossible.

### What breaks without the right abstraction

Using an `ArrayList` as a queue by repeatedly removing index 0 shifts remaining references and makes n removals O(n²). Using recursion as an unbounded stack can overflow. Using an unbounded production queue turns overload into growing latency and memory. Losing one temporary reference during linked-list reversal discards the unprocessed suffix. A queue can be thread-safe yet still violate business correctness if task effects are not idempotent.

### Memory reality

Textbook notation calls node insertion O(1), but a node carries object header, value/reference fields, alignment and allocation/GC cost. Nodes are scattered, reducing cache locality. An `int[]` stores 4-byte primitive payloads contiguously; a linked representation can consume many times more memory per value on a typical 64-bit JVM. Exact bytes depend on object layout and compressed references; measure with OpenJDK JOL.

Java’s recommended general-purpose stack/deque implementation is `ArrayDeque`, not legacy `Stack`. `ArrayDeque` is resizable, unsynchronized, disallows null, and supplies amortized constant-time operations at both ends. `LinkedList` implements List and Deque but usually pays node overhead and locality costs.

## 2. CORE MECHANICS

### 2.1 Singly linked traversal and insertion

To traverse, start at head and follow next until null. Time O(n), space O(1). Finding index i is O(i), unlike array O(1).

Insertion after a known node requires linking the new node to the old successor before linking the node to the new one:

```java
Node inserted = new Node(9);
inserted.next = current.next;
current.next = inserted;
```

This is O(1) after the node is known. Searching for the insertion position remains O(n). Deleting the node after current is `current.next=current.next.next`, after validating it exists. Removing a known node itself from a singly list normally requires its predecessor; the “copy successor into this node” interview trick fails for the tail and changes node identity.

### 2.2 Dummy/sentinel nodes

A dummy head is a temporary node before the real head. It makes insertion/removal at the first position use the same logic as middle positions. It is not a domain value and is returned via `dummy.next`.

Merging sorted lists uses dummy and tail. Compare current values, attach the smaller node, advance it, and advance tail. When either list ends, attach the remaining suffix. Choosing from the first list on equality preserves cross-list stability. O(m+n), O(1) auxiliary space when nodes are reused.

### 2.3 Reversal invariant

Before each reversal iteration:

- `previous` heads the fully reversed processed prefix.
- `current` heads the untouched suffix.
- together they contain every original node exactly once.

Save `next=current.next` **before** overwriting `current.next`. Then point current backward, advance previous and current. For `1→2→3→null`, states become `1→null | 2→3`, then `2→1 | 3`, then `3→2→1 | null`. O(n)/O(1). Recursive reversal is O(n) time/O(n) call stack and risks deep-stack failure.

### 2.4 Fast and slow pointers

For the middle, slow advances one node and fast two. When fast reaches the end, slow is near the middle. For even lengths, explicitly define whether the lower or upper middle is returned.

Floyd cycle detection also uses speeds 1 and 2. If a cycle exists, fast eventually laps slow; if fast reaches null, none exists. To find entry after a meeting, reset one pointer to head and advance both one step; they meet at entry. The algebra follows from distances: if μ is distance to entry and λ cycle length, the meeting distance satisfies a multiple-of-λ relation, making head-to-entry equal to the remaining cycle offset modulo λ. Time O(n), space O(1), compare node identity, not values.

### 2.5 Stack mechanics

`ArrayDeque.push/pop/peek` use the front. Bracket validation pushes opening delimiters. A closing delimiter must find a matching top; a close on empty fails; leftover opens at end fail. Non-delimiter behavior must be specified—ignore, reject, or tokenize first.

Expression evaluation uses an operator stack and an operand stack. Precedence and associativity determine when to pop. Recursive function calls use the JVM call stack: local variables, return point and execution state. An iterative explicit stack can control memory and avoid `StackOverflowError` on adversarial depth.

### 2.6 Min stack

To return minimum in O(1), store each pushed value with the minimum at that depth. Push 5→(5,5), 2→(2,2), another 2→(2,2), 7→(7,2). Popping 7 and one 2 still leaves minimum 2. A separate min stack also works but must handle duplicate minima by pushing duplicates or counts.

### 2.7 Queue mechanics and circular buffers

With an array-backed circular queue, head and tail wrap modulo capacity. Track size or reserve one empty slot to distinguish full from empty. For capacity 5, indices can progress 3,4,0,1 without moving existing elements. Enqueue/dequeue are O(1). Fixed capacity provides backpressure but requires a defined full policy.

`ArrayDeque` grows dynamically and hides ring mechanics. `ArrayBlockingQueue` is bounded and thread-safe for producers/consumers. `ConcurrentLinkedQueue` is unbounded and nonblocking; that does not make unbounded growth safe.

### 2.8 Queue using two stacks

Push new values to `in`. On dequeue, if `out` is empty, move every item from in to out, reversing order; pop out. A transfer can cost O(n), but each element is pushed into and popped from each stack at most once, so a sequence of operations costs O(number of operations): amortized O(1). Worst-case one dequeue remains O(n).

### 2.9 Monotonic stacks

A monotonic stack keeps values/indices in increasing or decreasing order. For next-greater element, keep unresolved indices with decreasing values. When a larger value arrives, pop smaller indices and set their answer. Each index pushes and pops once, so O(n), even though a while loop is nested.

For temperatures `[73,74,75,71,69,72,76,73]`, index 0 resolves when 74 arrives (1 day); indices 4 and 3 resolve when 72 arrives; 2 resolves at 76 after 4 days. Store indices because distance matters.

### 2.10 Monotonic deque for window maximum

The deque holds indices of candidates in decreasing value order. Before inserting index i:

1. Remove front indices `<=i-k` because expired.
2. Remove back indices whose value is `<=current`; they can never beat current in any future shared window.
3. Add i. Front is maximum.

For `[1,3,-1,-3,5,3,6,7]`, k=3, results are `[3,3,5,5,6,7]`. Each index enters/exits once: O(n), O(k).

### 2.11 Production queues and Little’s Law

A queue does not create capacity. If arrivals are 1,000 tasks/s and downstream sustains 600/s, backlog grows 400/s. A 40,000-task buffer merely delays exhaustion by about 100 seconds, while wait time rises. Little’s Law `L=λW`: at 600 tasks/s and 2-second average wait/service system time, roughly 1,200 tasks are in flight.

Bound queues from acceptable waiting time and service rate, propagate deadlines, expose depth/age/rejection metrics, and reject, shed, degrade or durably admit according to the product. FIFO can cause head-of-line blocking when one slow task delays smaller work; priority/fair queues help but introduce starvation and tenant-isolation concerns.

## 3. WORKED PROBLEMS

### Problem 1 — Reverse a list

**Statement.** Reverse `10→20→30→40` in place.

**Solution.** Initialize previous null/current 10. Save successor before rewiring each node. After four iterations previous heads `40→30→20→10`, current null. O(n)/O(1). Empty returns null; singleton returns itself.

**Mistake caught.** Overwriting `current.next` before saving it loses nodes 20 onward.

### Problem 2 — Merge sorted incident IDs

**Statement.** Merge `1→4→7` and `2→3→8` by reusing nodes.

**Solution.** Dummy tail chooses 1,2,3,4,7; first list ends and remainder 8 attaches. Result `1→2→3→4→7→8`. O(m+n)/O(1). If inputs must remain intact, allocate copies and space becomes O(m+n).

**Mistake caught.** Claiming O(1) space while creating a new node for every result.

### Problem 3 — Remove nth from end

**Statement.** Remove the second node from end of `5→7→9→11→13`.

**Solution.** Use dummy before head. Advance fast n=2 edges; then move fast and slow together until fast.next is null. Slow is predecessor of 11; bypass it. Result `5→7→9→13`. O(length)/O(1). Validate n positive and not larger than length.

**Mistake caught.** Without dummy, removing head needs an error-prone special case.

### Problem 4 — Cycle entry

**Statement.** `1→2→3→4→5` has tail pointing to node 3. Return entry.

**Solution.** Floyd pointers meet within cycle. Reset slow to head; advance both one. Their first identity-equal node is 3. O(n)/O(1). Repeated values elsewhere do not matter.

**Mistake caught.** Comparing values and falsely reporting a cycle when equal values occur in distinct nodes.

### Problem 5 — Validate delimiters

**Statement.** Validate `payment({items:[1,2]})` and `([)]`.

**Solution.** Push `(`, `{`, `[`, then close in reverse; first string succeeds and stack ends empty. In `([)]`, `)` sees `[` on top and fails. O(n)/O(n) worst-case stack.

**Mistake caught.** Counting opening/closing quantities without checking nesting order.

### Problem 6 — Queue from two stacks

**Statement.** Execute add 1, add 2, remove, add 3, remove, remove.

**Solution.** After first removes trigger transfer, out has 1 above 2; remove gives 1. Add 3 stays in in. Next out gives 2. Only when out empty transfer 3; final gives 3. FIFO preserved. Amortized O(1), worst single transfer O(n).

**Mistake caught.** Transferring on every enqueue destroys the amortized simplicity or ordering.

### Problem 7 — Sliding-window maximum

**Statement.** Return maxima for `[1,3,-1,-3,5,3,6,7]`, k=3.

**Solution.** Maintain decreasing candidate indices. At index 1, value 3 removes index 0. First window front is 3. Value 5 later removes -3,-1,3 candidates as dominated. Produced maxima `[3,3,5,5,6,7]`. O(n)/O(k).

**Mistake caught.** Storing values rather than indices makes expiry ambiguous with duplicates.

### Problem 8 — Largest rectangle in histogram

**Statement.** Heights `[2,1,5,6,2,3]`; find maximum area.

**Solution.** Maintain increasing indices. When a lower height arrives, pop height h; right boundary is current index exclusive, left boundary is new stack top+1, width is `i-left`. At height 2 (index 4), pop 6 giving width1 area6; pop5 giving left2,width2,area10. Append a zero sentinel iteration to flush remaining bars. Maximum 10. O(n)/O(n).

**Mistake caught.** Using width 1 for every bar or failing to flush increasing suffix.

### Problem 9 — Bounded dispatcher

**Statement.** Arrival 1,000/s, service 600/s, maximum acceptable queue wait 2 seconds. Design admission.

**Solution.** At sustainable service, a rough queue ceiling is 600×2=1,200 waiting tasks, adjusted from measured service distribution and in-flight workers. Because overload is permanent in the stated interval, the queue will fill after roughly `1200/(1000-600)=3` seconds from empty. Then reject/throttle or durably redirect 400/s; adding memory cannot solve it. Track oldest age, depth, service latency, rejection and downstream saturation.

**Mistake caught.** Choosing an unbounded queue or merely increasing worker threads beyond downstream capacity.

## 4. REAL-WORLD / APPLIED CONTEXT

### JVM execution and parsing

Every Java thread has a call stack; recursive graph/list code can throw `StackOverflowError` at depth far below available heap. Compiler/parser algorithms use explicit stacks for delimiter nesting and expression grammar. `ArrayDeque` is the official general-purpose recommendation for stack/queue use over `Stack` and often `LinkedList`.

### Executors and backpressure

Java `ThreadPoolExecutor` combines workers, a `BlockingQueue`, and rejection policy. An unbounded `LinkedBlockingQueue` tends to keep the pool near core size while backlog grows; a bounded queue forces an explicit overload decision. `CallerRunsPolicy` slows the submitting thread and can create feedback, but is dangerous if the caller must remain responsive or holds locks. Production choice depends on request deadlines and ownership.

### Messaging systems

Kafka partitions are durable ordered logs rather than in-memory FIFO queues, but consumers still face backlog/lag. Ordering is per partition, not global. RabbitMQ supports queueing and acknowledgements; redelivery makes effects at least once unless consumers deduplicate. Queue structure explains order and backlog, while distributed systems add persistence, replication, failures and consumer coordination.

The accompanying `LinearStructuresLab.java` compiles and verifies list reversal/merge/cycle entry, delimiter stacks, monotonic deque, two-stack queue and duplicate-safe min stack.

## 5. COMPARISON TABLE

| Structure | Access/search | End operations | Middle insertion | Memory/locality | Use |
|---|---:|---:|---:|---|---|
| `int[]` | index O(1), search O(n) | fixed | shift O(n) | compact, excellent locality | fixed primitive sequence |
| `ArrayList` | index O(1) | append amortized O(1) | shift O(n) | contiguous references | general random-access list |
| singly linked list | O(n) | head O(1), tail O(1) only if tracked | O(1) after predecessor known | node overhead, poor locality | node splicing/identity cases |
| doubly linked list | O(n) | O(1) with ends | O(1) at known node | more links | LRU order/removal |
| `ArrayDeque` | no indexed contract | amortized O(1) both ends | unsupported | array locality | stack/queue/deque |
| `ArrayBlockingQueue` | queue semantics | O(1), may block | unsupported | fixed capacity | bounded producer/consumer |
| `PriorityQueue` | head O(1), search O(n) | offer/poll O(log n) | heap-managed | array heap | priority, not FIFO |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **O(1) insertion means list is always faster.** Finding predecessor is O(n), and allocation/locality may dominate.
2. **Losing the suffix during reversal.** Save next before rewiring.
3. **Comparing cycle values.** Cycle algorithms rely on node identity.
4. **Recursive reversal is O(1) space.** It consumes O(n) stack.
5. **Using Java `Stack`.** Prefer `Deque`/`ArrayDeque` for modern LIFO code.
6. **Balanced bracket counts imply validity.** `([)]` has equal counts but wrong order.
7. **Queue with two stacks is worst-case O(1).** It is amortized O(1); one transfer is O(n).
8. **Storing values in a monotonic window deque.** Indices are needed for expiry and duplicates.
9. **Unbounded queue absorbs bursts safely.** Sustained overload grows latency/memory without limit.
10. **Thread-safe queue makes task effects safe.** Business effects need idempotency/transactions.
11. **FIFO always means fair.** Large slow head work can block small work; tenants can monopolize.
12. **Priority fixes latency without cost.** It can starve low priority and requires stable policy.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the preceding material.

- Singly list: index/search O(n); splice after known predecessor O(1).
- Dummy head removes head special cases.
- Reverse invariant: previous reversed, current untouched; save next first.
- Floyd: slow1/fast2; reset one to head to find cycle entry.
- Stack=LIFO; queue=FIFO; deque=both ends; priority queue≠FIFO.
- Prefer `ArrayDeque` for ordinary Java stack/deque.
- Two-stack queue: amortized O(1), worst transfer O(n).
- Monotonic stack/deque: each index pushes/pops once → O(n).
- Window deque stores indices; expire front, remove dominated back.
- Bound production queues from wait budget/capacity; overload needs rejection/throttling/durable admission.

## 8. PRACTICE SET FOR SELF-TEST

1. Reverse nodes from positions 3 through 6 in `1→2→3→4→5→6→7` in one pass.
2. Determine the upper and lower middle of lists with 5 and 6 nodes using slow/fast initialization choices.
3. Check whether `1→2→3→2→1` is a palindrome in O(n) time/O(1) auxiliary space while restoring the list.
4. Evaluate postfix tokens `2 7 + 3 * 4 -` using a stack.
5. Give next greater values for `[2,1,2,4,3]`.
6. Design a circular buffer of capacity 4 and trace enqueue A,B,C,D, dequeue twice, enqueue E,F.
7. For a bounded queue capacity 10,000, arrival 2,500/s and service 2,000/s, calculate fill time from empty and explain steady-state behavior.
8. Explain why a lock-free unbounded queue can still crash a service.
9. Design a deque algorithm for shortest subarray sum at least K when negative numbers exist; state the prefix-sum invariant.
10. Compare at-least-once message redelivery with an in-memory queue retry and state the consumer requirement.

## 9. CURATED RESOURCES

1. **Oracle Java SE API, `ArrayDeque`, `Deque`, `LinkedList`, `BlockingQueue`, `ThreadPoolExecutor`.** Exact Java operation, null, capacity, blocking and rejection contracts.
2. **Cormen et al., *Introduction to Algorithms*, 4th ed., Chapter 10 “Elementary Data Structures.”** Formal stacks, queues, linked lists and pointer invariants.
3. **Sedgewick & Wayne, *Algorithms*, 4th ed., §1.3 “Bags, Queues, and Stacks.”** Java implementations and expression-evaluation applications.
4. **Robert Sedgewick, “Implementing Quicksort Programs,” linked/stack context, and classic algorithm texts.** Adds careful invariant-driven implementation habits.
5. **Michael and Scott, “Simple, Fast, and Practical Non-Blocking and Blocking Concurrent Queue Algorithms” (1996).** Foundation for concurrent queue algorithm reasoning.
6. **Java Concurrency in Practice, Goetz et al., Chapters 5, 6 and 8.** Production blocking queues, task execution, saturation and pool configuration.
7. **Little, “A Proof for the Queuing Formula: L=λW” (1961).** Formal basis for relating throughput, time and in-flight work.
8. **Apache Kafka design documentation and RabbitMQ Consumer Acknowledgements guide.** Extends local queue intuition to durable logs, acknowledgements and redelivery.
9. **OpenJDK JOL.** Measures actual linked-node versus array memory layout on the target JVM.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Complexity Analysis.** Required for amortized two-stack queues and aggregate monotonic-stack proofs.
2. **Arrays and Strings.** Array-backed deques and index windows contrast with node linkage.
3. **Hashing and Sets.** Hash map plus doubly linked list forms O(1) LRU; sets track visited nodes.

### After

1. **Trees, Heaps and Tries.** Trees generalize node links; heaps specialize priority queues.
2. **Graphs.** BFS uses a queue, DFS an explicit/implicit stack, and visited sets prevent revisits.
3. **Java Concurrency Basics.** Blocking/concurrent queues require visibility, atomicity, interruption and cancellation.
4. **Kafka and Eventing.** Queue order, backlog and consumers become durable distributed-system concerns.
5. **Capacity and SRE.** Queue depth/age, Little’s Law and overload become operational signals and SLO design.

---ANSWER KEY BELOW---

1. Use dummy; move `before` to node2. Reverse exactly four nodes using standard local reversal, connect `before.next` to new segment head6 and old segment head3 to node7. Result `1→2→6→5→4→3→7`, O(n)/O(1).
2. Slow=head, fast=head yields upper middle for six (node4) and node3 for five; slow=head, fast=head.next yields lower middle for six (node3) and node3 for five, under the usual loop `while(fast!=null&&fast.next!=null)`.
3. Find middle, reverse second half, compare corresponding values, then reverse again and reconnect. O(n)/O(1). Restoration is part of the contract.
4. Push 2,7; `+`→9; push3; `*`→27; push4; `-`→23. Answer 23. Reject insufficient operands or leftover stack.
5. Maintain decreasing indices. Answers `[4,2,4,-1,-1]`.
6. After A–D buffer full. Dequeues return A,B; wrapped enqueues E,F occupy freed slots. Logical queue C,D,E,F. Track size or reserved slot to distinguish full/empty.
7. Net growth 500/s; 10,000 fills in 20 seconds. After that, 500/s must be rejected, throttled or durably redirected; otherwise latency/memory cannot remain bounded.
8. Lock freedom addresses thread progress, not capacity. Producers can outrun consumers until queued nodes exhaust heap; payload retention and GC can kill the process.
9. Build long prefix sums. Maintain deque of indices with increasing prefix values; while current−front≥K, update answer/pop front; while back prefix≥current, pop dominated back; add current. O(n)/O(n).
10. Durable broker may redeliver after consumer effect succeeds but acknowledgement is lost. Consumer must be idempotent/deduplicate or atomically coordinate effect and progress. In-memory retry disappears on process loss and has different durability guarantees.
