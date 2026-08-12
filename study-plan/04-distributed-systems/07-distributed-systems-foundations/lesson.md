# Distributed Systems Foundations from Scratch

Parent subject: `04-distributed-systems`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### What makes a system distributed

A **distributed system** is a collection of independent computing nodes that communicate and coordinate to provide a service or maintain shared state. Nodes do not share one perfectly synchronized memory or clock. Messages take time and can fail. Nodes can crash, pause, restart, or become partitioned while others continue.

Distribution is chosen for scale, geographic latency, availability, fault isolation, organizational autonomy, specialized hardware, and data locality. It also introduces failure modes absent from one process. A single process is either reachable and running from its own perspective; across a network, one node cannot always tell whether another crashed, the path failed, or the response is merely slow.

Leslie Lamport famously captured the surprise: a distributed system is one in which a machine you did not know existed can make your own unusable. The point is dependency, not cynicism. Design must expose membership, failure assumptions, ownership, and recovery.

### Nodes, state, messages, and protocols

A **node** is an independently failing participant: process, VM, host, database server, broker, or controller depending on the model. **State** is information that influences future behavior. **Local state** belongs to one node; **replicated state** has copies; **durable state** survives defined failures.

Nodes exchange **messages** according to a protocol—a state machine specifying valid inputs, outputs, transitions, timeouts, and errors. The network is asynchronous in the general model: there is no known fixed upper bound on message delay or relative node speed. Real systems introduce practical bounds and failure detectors, but pauses and congestion can violate optimistic expectations.

### Partial failure and failure detectors

In a partial failure, some components/pathways fail while others work. A timeout provides suspicion, not proof. Node A timing out B cannot distinguish B crashed, the A→B request was lost, B processed it and response was lost, the path is delayed, or A itself paused.

A **failure detector** estimates whether nodes are alive, often through heartbeats and timeouts. Aggressive timeouts detect real failures faster but falsely suspect slow nodes; relaxed timeouts delay failover. No perfect failure detector exists in a fully asynchronous system with crash failures because silence is ambiguous.

**Fail-stop** models assume a failed node halts detectably. **Crash-stop** halts permanently but detection is external. **Crash-recovery** nodes can restart with durable state. **Byzantine** nodes may behave arbitrarily or maliciously, including sending conflicting messages. Most backend/cloud designs assume crash/recovery plus network faults, not Byzantine behavior; using Byzantine algorithms without the threat requirement adds high cost.

### Time and clocks

A physical clock attempts to track real time but drifts and is synchronized imperfectly with protocols such as NTP. Wall clocks can jump backward/forward due to corrections. Use a monotonic clock for elapsed durations and deadlines. Use UTC instants for event timestamps and retain domain time-zone context where needed.

Clock timestamps do not perfectly order close distributed events. A **happens-before** relation, introduced by Lamport, captures causal order:

1. earlier action in one process happens before later action there;
2. sending a message happens before receiving it;
3. relation is transitive.

Events without causal order are **concurrent**. A **Lamport clock** assigns counters that respect causality: if A happens before B, timestamp(A) < timestamp(B), but the converse is not guaranteed. **Vector clocks** can detect concurrency by tracking per-participant components but grow with membership.

### Replication

Replication stores state on multiple nodes to improve availability, read scale, geographic locality, or durability. It creates the problem of keeping copies coherent.

In **leader-based replication**, one leader orders writes and followers copy them. Synchronous replication waits for selected replicas before acknowledgment, increasing durability at latency/availability cost. Asynchronous replication acknowledges before followers catch up, lowering latency but allowing acknowledged-data loss during failover depending on system rules.

**Multi-leader** accepts writes at multiple leaders and must resolve conflicts. **Leaderless** systems send reads/writes to multiple replicas and reconcile versions. Quorum notation often uses N replicas, W write acknowledgments, R read responses. `W + R > N` creates an overlap under simplified assumptions, but does not by itself guarantee linearizability: sloppy quorums, concurrent writes, clock/version resolution, failures, and repair matter.

### Partitioning/sharding

Partitioning splits a dataset across nodes. **Range partitioning** groups adjacent keys, supporting range scans but risking hot ranges. **Hash partitioning** spreads keys more evenly but destroys natural range locality. A **directory** maps keys to partitions flexibly but is itself state to maintain. Consistent hashing reduces key movement when membership changes.

The partition key determines scalability and correctness boundaries. Hashing by tenant may isolate tenants but a giant tenant becomes hot. Hashing by patient distributes one tenant but cross-patient queries fan out. Repartitioning large live datasets needs routing/versioning, dual read/write or migration protocols, validation, and rollback.

### Consistency models

A consistency model tells clients what values/ordering they may observe.

- **Linearizability:** each operation appears atomic at some point between invocation and response, respecting real-time order.
- **Sequential consistency:** all operations appear in one order consistent with each process's program order, but not necessarily real-time order.
- **Causal consistency:** causally related writes are observed in order; concurrent writes may be seen differently.
- **Eventual consistency:** if updates stop, replicas converge eventually; it says little about interim values or conflict semantics.
- **Read-your-writes:** a client sees its own completed writes.
- **Monotonic reads:** a client does not move backward to older versions.

Consistency is not binary. Specify per operation: balance authorization may require strongly ordered ledger state; a profile avatar can tolerate eventual propagation.

### Availability, partitions, and CAP

The CAP theorem concerns a read/write register in the presence of a network partition: a system cannot simultaneously guarantee both linearizable consistency and availability for every request when partitioned. Here **availability** means every request to a non-failing node eventually receives a non-error response, not “five nines.”

During partition, a CP-oriented system may reject/delay operations that cannot safely coordinate; an AP-oriented system accepts operations and later reconciles, so clients may observe divergent state. Without a partition, systems still trade latency, consistency, durability, and throughput. “Choose two of three” is an oversimplification; partition tolerance is not optional for a networked system, and choices can be per operation.

PACELC extends the discussion: if Partition, trade Availability vs Consistency; Else, trade Latency vs Consistency. It is a heuristic vocabulary, not a complete design.

### Consensus and coordination

**Consensus** lets nodes agree on one value/order despite failures under stated assumptions. Raft and Paxos are crash-fault consensus families. A leader commonly proposes log entries and commits when a majority acknowledges according to the protocol. Consensus powers replicated metadata, membership, leader election, and configuration state.

A majority quorum in 3 nodes is 2 and tolerates 1 unavailable node for progress. In 5 nodes, majority 3 and progress tolerates 2. Adding a fourth node does not improve majority fault tolerance beyond one (`floor((N-1)/2)`); odd voting groups are common. Consensus does not make arbitrary application workflows transactional; it provides an ordered replicated state machine substrate.

The FLP result shows deterministic consensus cannot guarantee termination in a fully asynchronous system with even one crash failure. Practical algorithms use timing assumptions/randomness and may temporarily stop making progress to preserve safety.

### Safety and liveness

A **safety property** says something bad never happens: two different values are not both committed for one log index; an account never spends the same funds twice. A **liveness property** says something good eventually happens: a valid request eventually completes; a new leader is eventually elected.

Distributed algorithms commonly preserve safety during uncertainty by sacrificing liveness. A minority partition should not elect/write conflicting authoritative state. Interview answers should state both: “What invariant must never break?” and “Under what assumptions does progress resume?”

## 2. CORE MECHANICS

### 2.1 Model one interaction under failure

Client C sends `CreatePayment(K)` to server S. Enumerate cut points:

1. before request send: no server effect;
2. request lost: no server effect;
3. server receives, crashes before commit: no committed effect;
4. commits, crashes before response: effect occurred, client uncertain;
5. response lost: effect occurred, client uncertain;
6. response received: client knows acknowledged outcome, subject to contract.

Idempotency key K and status reconciliation turn ambiguous retry into a safe protocol. A transport timeout alone cannot identify the cut point.

### 2.2 Use monotonic time

```java
long start = System.nanoTime();
// work
long elapsedNanos = System.nanoTime() - start;
```

`nanoTime` is for elapsed intervals, not epoch timestamps, and only differences in the same running JVM are meaningful. `currentTimeMillis` can change with wall-clock corrections. Distributed deadlines should be conveyed according to protocol/library semantics, accounting for clock uncertainty; many systems propagate remaining duration locally.

### 2.3 Lamport clock example

Processes A and B start counters 0. A local event → A=1. A sends message timestamp 2 after increment. B currently 5 receives it and sets `B=max(5,2)+1=6`. B's receive is causally after the send. If another event C has Lamport timestamp 4, that number alone does not prove C causally precedes B=6.

For total ordering, combine logical timestamp with stable node ID, but the arbitrary tie-break gives order, not causality.

### 2.4 Leader replication acknowledgment

Three replicas A leader, B/C followers. If leader acknowledges after local write only, A can fail before replication and the acknowledged write may disappear after B election. If it waits for one follower (majority total two) and protocol ensures committed entries survive elections, one node failure retains the entry. Latency now includes follower round trip and disk policy.

Clarify “write complete”: accepted in memory, WAL appended, fsynced locally, replicated, committed by consensus, visible to reads, or externally reconciled are different boundaries.

### 2.5 Quorum arithmetic

For N=3, W=2, R=2, every read and write quorum overlap in at least one replica. But a stale overlapping replica, concurrent versions, or non-authoritative conflict resolution can still return stale data. Quorum math is necessary within some designs, not a universal consistency proof.

Availability under independent replica reachability p can be calculated with a binomial model. If p=.99, probability at least 2 of 3 are reachable is `3×.99²×.01 + .99³ = .999702` (99.9702%). Real failures are correlated, so this is optimistic.

### 2.6 Detect and handle split brain

If two sides of a partition both believe they are leader, conflicting writes can occur. Avoid through majority leases/consensus terms and fencing. A **fencing token** is a monotonically increasing epoch attached to operations; storage rejects stale epochs. Merely expiring a lock is unsafe because the old holder may resume after pause and continue acting.

Example: worker A gets token 41 then pauses; lease expires and B gets 42. Storage accepts B's writes and later rejects A's token 41. Without fencing, both can write.

### 2.7 Partition keys and hotspots

One billion events/day averages `1e9/86400≈11,574/s`, but peak may be 10×. With 100 hash partitions average peak is ~1,157/s, assuming even keys. If one tenant produces 30% of traffic and tenant is the key, one partition sees ~34,722/s at peak—30× average—while others idle. Salt/subpartition giant tenants, choose finer keys, or isolate them, while preserving required ordering.

### 2.8 Consistent hashing movement

Simple modulo with N nodes remaps most keys when N changes because `hash mod N` changes. An ideal consistent-hash ring adding one node to N moves roughly `1/(N+1)` of keys; adding an eleventh moves about 9.1%, subject to vnode distribution. Virtual nodes improve balance and heterogeneous weighting but expand routing metadata.

### 2.9 Read repair and anti-entropy

In leaderless designs, a read that receives multiple versions can select/merge the newest according to version metadata and write it back—read repair. Background anti-entropy compares replicas (often with tree/hash summaries) and repairs divergence. Last-write-wins using physical timestamps can lose valid writes under clock skew; version vectors or domain merges preserve more causality at complexity cost.

### 2.10 Design by invariant and operation

For each operation document:

1. state/invariant: ledger entries balance per currency;
2. partition key/authority: account or ledger shard;
3. consistency: linearizable conditional debit;
4. failure outcome: accepted/rejected/unknown;
5. retry identity: stable command ID;
6. replication acknowledgment/durability;
7. recovery/reconciliation;
8. latency/availability behavior during partition.

Do not label a whole platform “strongly consistent.” A metadata store, cache, object store, event log, and feature store can expose different models.

## 3. WORKED PROBLEMS

### Problem 1 — Majority size (easy)

Give majority for 3, 4, 5, and 7 voting nodes and crash unavailability tolerated for progress.

**Solution.** Majorities 2,3,3,4. Tolerated unavailable while retaining majority: 1,1,2,3. General crash tolerance `floor((N-1)/2)`.

**Trap:** believing four nodes tolerate two failures.

### Problem 2 — Timeout meaning (easy)

Client times out after sending a transfer. Did it fail?

**Solution.** Unknown. It may not have arrived, may have failed pre-commit, or may have committed with lost response. Reconcile by idempotency/status; do not infer outcome from timeout.

**Trap:** equating no response with no effect.

### Problem 3 — Clock use (easy)

Choose wall or monotonic clock for measuring a 250 ms operation.

**Solution.** Monotonic elapsed clock. Wall clock is for civil/epoch timestamps and can jump.

**Trap:** subtracting distributed wall timestamps as precise latency.

### Problem 4 — Replication lag (medium)

User updates profile via leader, then reads an async follower and sees old data. Is this necessarily a bug?

**Solution.** It is allowed under eventual consistency unless read-your-writes was promised. Provide leader/session-sticky read, version token with minimum-version wait, or synchronous replication according to requirement.

**Trap:** saying eventual consistency means all reads are eventually current enough without a bound.

### Problem 5 — Quorum overlap (medium)

For N=5, list W/R pairs satisfying `W+R>N`.

**Solution.** Examples (1,5), (2,4), (3,3), (4,2), (5,1). They trade write/read availability and latency. Overlap alone is not a complete linearizability proof.

**Trap:** claiming any listed pair guarantees strong consistency in any database.

### Problem 6 — CAP decision (medium)

During partition, should a ledger debit be accepted independently in both regions?

**Solution.** Usually no if it can overspend the same balance. Route/coordinate through an authoritative quorum and reject/defer where authority unavailable, preserving safety. Alternative escrow partitions preallocate spendable rights, but that is a different invariant/protocol.

**Trap:** selecting AP because “availability is important” without conflict semantics.

### Problem 7 — Hot partition (hard)

Peak 100,000 events/s, 50 partitions, one customer is 20% and customer is key. Load?

**Solution.** Average 2,000/s, but hot customer's partition receives at least 20,000/s plus other keys, about 10× average. Adding evenly hashed partitions does not split that key. Change key/subpartition or isolate customer while preserving ordering requirements.

**Trap:** dividing total by partitions and stopping.

### Problem 8 — Lease without fencing (hard)

Worker A's 30-second lease expires during a 60-second GC pause; B acquires it. What breaks?

**Solution.** A can resume and act concurrently with B. Add monotonically increasing fencing token enforced by the resource; make operations idempotent and bounded. Lease expiry only changes coordinator belief.

**Trap:** treating time-based lock expiration as revoking an old process.

### Problem 9 — FLP interpretation (hard)

Does FLP say consensus is impossible in production?

**Solution.** It says no deterministic algorithm guarantees termination in a fully asynchronous system with one possible crash while always preserving consensus properties. Practical algorithms make timing/randomness assumptions and may pause progress during uncertainty while preserving safety.

**Trap:** using FLP to claim Raft/Paxos cannot work.

## 4. REAL-WORLD / APPLIED CONTEXT

### Raft in etcd

etcd uses Raft to replicate an ordered log among members and provide strongly consistent metadata operations. Kubernetes depends on etcd for cluster state. A three-member cluster tolerates one member failure for quorum; stretching members across high-latency/failure-correlated locations changes commit latency and availability.

### Dynamo-style systems

Amazon's Dynamo paper described consistent hashing, preference lists, sloppy quorums, hinted handoff, vector clocks, and anti-entropy to prioritize availability for a shopping-cart workload. These mechanisms show why `R+W>N` slogans omit conflict and failure details.

### Google Spanner

Spanner combines synchronous replication/consensus with TrueTime clock uncertainty to provide externally consistent transactions across regions. It does not assume perfectly synchronized clocks; it exposes uncertainty bounds and may wait to ensure ordering, explicitly paying latency for semantics.

## 5. COMPARISON TABLE

| Model/approach | Guarantee | Strength | Cost/limitation |
|---|---|---|---|
| Linearizable | Real-time single-copy behavior | Simple critical-state reasoning | Coordination/latency, may reject under partition |
| Sequential | One program-order-respecting sequence | Strong global ordering abstraction | Can violate real-time observation |
| Causal | Preserves happens-before | Collaborative/event relationships | Metadata/session routing complexity |
| Eventual | Converges after writes stop | Availability/local latency | Interim staleness/conflict unspecified |
| Leader replication | One write authority | Clear order/conflicts | Failover and leader bottleneck |
| Multi-leader | Multiple write locations | Disconnected/geo writes | Conflict resolution |
| Leaderless/quorum | Multiple replicas contacted | Tunable read/write trade-off | Repair/version/conflict complexity |
| Range partition | Ordered locality | Range scans | Hot sequential ranges/rebalance |
| Hash partition | Load distribution | Point access/scale | Scatter range queries, hot keys remain |
| Consensus quorum | Ordered fault-tolerant state | Safety under crash/partition assumptions | Majority required, latency, operational care |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Timeout identifies a crashed node.** It only creates suspicion.
2. **Wall clocks give exact distributed order.** Skew and corrections invalidate that assumption.
3. **Replication equals backup.** Bad writes/deletes replicate.
4. **Three replicas mean three failures tolerated.** Majority progress tolerates one.
5. **W+R>N guarantees linearizability universally.** Versioning, sloppy quorums, concurrency, and protocol matter.
6. **Eventual consistency means “a few seconds.”** It provides no universal bound.
7. **CAP means choose any two all the time.** The theorem addresses consistency/availability during partition under precise definitions.
8. **Consensus makes all application data strongly consistent.** Only operations routed through the consensus-backed state/protocol gain its semantics.
9. **Lease expiry stops old holder.** Fencing at the resource is required.
10. **More shards fix hot keys.** One indivisible key still maps to one partition.
11. **Async replication has no data-loss risk after ack.** Failover can lose unreplicated acknowledged writes.
12. **Safety and availability are the same.** Safety forbids bad states; liveness concerns progress.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Distributed = independent nodes + messages + no shared perfect clock/fate.
- Timeout means unknown/suspected, not “did not happen.”
- Monotonic clock for duration; wall/UTC for event instants.
- Happens-before captures causality; Lamport values do not prove converse.
- Replication adds copies and coordination/conflict problems.
- Partitioning splits data; hot key survives more partitions.
- Linearizable respects real time; eventual promises convergence only after updates stop.
- CAP: under partition, cannot guarantee both linearizable C and every-request availability.
- Majority = floor(N/2)+1; crash progress tolerance=floor((N−1)/2).
- Consensus preserves safety and may stop progress during uncertainty.
- Lease requires fencing token enforced by resource.
- Design per invariant and operation, not one platform-wide adjective.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain four interpretations of a timed-out write.
2. Compute majority and failure tolerance for 9 nodes.
3. With N=5, W=2, what minimum R creates overlap?
4. Distinguish read-your-writes from monotonic reads.
5. Calculate average events/s for 2.592 billion events/day.
6. Explain why hashing by tenant does not balance one tenant with 40% load.
7. Give a safe behavior for inventory decrement during loss of quorum.
8. Describe how fencing token 102 protects against stale token 101.
9. Explain one difference between Lamport and vector clocks.
10. State CAP availability in theorem terms, not uptime percentage.

## 9. CURATED RESOURCES

- Leslie Lamport, “Time, Clocks, and the Ordering of Events in a Distributed System,” 1978 — primary happens-before and logical-clock formulation.
- Nancy Lynch, *Distributed Algorithms*, Chapters 1–3 and 12 — rigorous models, failures, clocks, and consensus foundations.
- Martin Kleppmann, *Designing Data-Intensive Applications*, Chapters 5, 6, 8, and 9 — replication, partitioning, network faults, clocks, and consistency.
- Seth Gilbert and Nancy Lynch, “Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services,” 2002 — formal CAP proof and definitions.
- Michael Fischer, Nancy Lynch, and Michael Paterson, “Impossibility of Distributed Consensus with One Faulty Process,” 1985 — the FLP result in its actual model.
- Diego Ongaro and John Ousterhout, “In Search of an Understandable Consensus Algorithm (Raft),” 2014 — leader election, log replication, and safety.
- Giuseppe DeCandia et al., “Dynamo: Amazon's Highly Available Key-value Store,” 2007 — consistent hashing, sloppy quorums, vector clocks, hinted handoff, and anti-entropy.
- James C. Corbett et al., “Spanner: Google's Globally-Distributed Database,” 2012 — consensus, TrueTime uncertainty, and external consistency at global scale.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Computer Networking:** supplies asynchronous transport, delay, loss, partitions, and reachability.
2. **Client–Server, RPC, and Messaging:** supplies protocol, delivery, deadline, and idempotency boundaries.
3. **Transactions and Locking:** supplies local atomicity/isolation, contrasted with cross-node state.

### After

1. **Failure Semantics:** implements practical suspicion, deadlines, retry, backoff, breaker, and overload behavior.
2. **Kafka and Eventing:** applies partitioning, replication, ordering, offsets, and consumer coordination.
3. **Consistency and Idempotency:** deepens linearizability, sagas, deduplication, and cross-service workflows.
4. **Capacity-Driven Design:** quantifies replication, quorum, failure headroom, fan-out, and partitions.
5. **Kubernetes and SRE:** applies reconciliation, leases, control planes, availability, and recovery.

---ANSWER KEY BELOW---

1. Request not sent/lost; received but failed pre-commit; committed but response lost; response delayed beyond timeout (among variants).
2. Majority 5; progress tolerates 4 unavailable crash-stop members under protocol assumptions.
3. R=4 because W+R>5.
4. RYW ensures a session sees its writes; monotonic reads ensures it never later observes a version older than one already seen.
5. `2.592e9/86400=30,000/s`.
6. All that tenant's keyed events share a partition; split/salt/isolate the key if ordering permits.
7. Reject/defer where authoritative quorum unavailable, or consume preallocated escrow rights under a proven protocol; never independently oversell.
8. Storage remembers highest epoch and rejects operations labeled 101 after accepting/learning 102.
9. Lamport clocks order causal events but cannot detect concurrency; vector components can identify incomparable concurrent histories at metadata cost.
10. Every request to a non-failing node eventually receives a non-error response despite partition.
