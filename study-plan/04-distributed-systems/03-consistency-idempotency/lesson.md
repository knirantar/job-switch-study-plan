# Consistency and Idempotency

**Parent:** 04 — Distributed Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus executable exercises

## 1. FOUNDATIONS

When data has one copy, a successful write followed by a read seems simple. Once copies exist—database replicas, caches, Kafka projections, regional services—different clients can observe different histories. **Consistency** is not one switch; it is a contract describing which histories are allowed. **Idempotency** makes repeated delivery of one logical request converge on one intended effect. Together they let applications survive delay, retry, duplication and partial failure without pretending the network is reliable.

A **history** is a set of operation invocations and responses ordered by real time and program order. A consistency model constrains how that concurrent history may appear. **Linearizability** says each operation takes effect atomically at some instant between invocation and response and respects real-time order: if write W completes before read R begins, R cannot return a state preceding W. It is a property of operations on an object/system, not the same as transaction isolation.

**Serializability** says concurrent transactions have an effect equivalent to some serial ordering. Plain serializability need not respect external real time. **Strict serializability** combines serializability with real-time ordering and is often called external consistency in database contexts. PostgreSQL Serializable provides serializable transaction histories, while systems such as Spanner explicitly target external consistency using bounded clock uncertainty and consensus.

Weaker models serve other goals. **Sequential consistency** preserves each process's program order but not necessarily real time across processes. **Causal consistency** preserves cause-before-effect: if B was created after reading A, nobody observes B without the causally prior A (within the model). **Eventual consistency** says that if updates stop and communication continues, replicas eventually converge; it gives no useful bound by itself and says little about what a user observes before convergence.

Session guarantees make weak replication usable: **read-your-writes** ensures a client sees its prior writes; **monotonic reads** prevent it from moving backward; **monotonic writes** preserve its write order; **writes-follow-reads** preserves causal dependence. Routing one user to a sufficiently caught-up replica or carrying a version token can implement these. “Usually sticky sessions” is not a guarantee during failover.

Replication exists for availability, latency, throughput and disaster recovery. It also creates conflicts. A leader can serialize writes but may be unavailable during partition/failover. Multi-leader/leaderless designs may accept writes in separated regions and reconcile later, so application semantics must define merge or rejection. A timestamp alone rarely captures causality reliably because physical clocks can skew.

Idempotency derives from algebra: applying operation `f` twice has the same effect as once, `f(f(x))=f(x)`. Setting status to `CANCELLED` can be idempotent; incrementing balance is not unless it is tied to a unique operation ID whose duplicate is ignored. An HTTP method labelled idempotent does not guarantee every downstream side effect is. The unit is a logical operation with identity, parameters, scope, durable result and retention.

## 2. CORE MECHANICS

### 2.1 Linearizability through examples

Register starts 0. Client A writes 1 and receives success at 10:00:00.100. Client B starts a read at 10:00:00.200. Returning 0 violates linearizability because write completed before read began. If B's read overlapped the write, returning 0 or 1 may both be legal because the linearization point can fall before or after.

Linearizability is compositional: if each independent object is linearizable, the system of objects is linearizable for single-object operations. It does not give an atomic transaction across two objects. A linearizable balance and linearizable ledger independently can still disagree if updated separately.

Consensus protocols such as Raft/Paxos commonly replicate an ordered log to implement linearizable state machines when clients contact the valid leader/quorum and reads use an appropriate protocol. A stale follower read may intentionally weaken the guarantee for latency/availability.

### 2.2 Serializability versus linearizability

Two transactions each update multiple rows. Serializability constrains transaction interleaving. Linearizability constrains real-time behavior of operations. A database can serialize T2 before T1 even if their execution overlapped; that is fine. If T1 fully committed before T2 began, strict serializability requires T1 before T2.

Snapshot isolation prevents many anomalies but permits write skew. Serializable databases may abort. A globally replicated key-value store can offer linearizable single-key reads/writes yet lack multi-key transactions. Always state object/transaction scope.

### 2.3 CAP precisely

Gilbert and Lynch formalized CAP for an asynchronous network. Their **consistency** is atomic/linearizable register behavior. Their **availability** requires every request to a nonfailed node eventually receive a response. Under a network partition, a replicated service cannot guarantee both: if both sides answer writes/reads, they can disagree; if one side refuses/waits to preserve one-copy semantics, availability in the theorem's sense is lost.

CAP is not “choose any two” as a permanent product label. Partition tolerance is the network fault condition; during normal communication systems can provide strong consistency and availability. During partition, choice can vary by operation/data: reject balance transfer but allow browsing cached catalog. CAP says nothing directly about latency when there is no partition, durability, transaction isolation or data loss after correlated failures. PACELC extends intuition: if Partition, Availability vs Consistency; Else, Latency vs Consistency—but it too is a lens, not a full design.

### 2.4 Leader, quorum and leaderless replication

Single-leader systems route writes through one authority and replicate followers. Benefits: simple conflict order and strong reads through leader/quorum. Costs: leader failover, cross-region write latency and stale follower reads.

Leaderless systems send to multiple replicas. With N replicas, write acknowledgements W and reads R, `W+R>N` creates overlap between a read and the latest acknowledged write quorum; `W>N/2` makes write quorums overlap. For N=3, R=2, W=2 satisfies both. This arithmetic alone does **not** prove linearizability: sloppy quorums, concurrent writes, failed writes, clock conflict resolution, read repair timing and node replacement matter. `ConsistencyLab.quorumOverlap` intentionally checks only the overlap condition.

If N=5, R=3, W=3, a write/read each contact three, so at least one overlaps. Latency is roughly the Wth/Rth fastest response (with tail/coordination effects); availability declines as required responses rise. Define whether failed/timed-out writes might later appear.

### 2.5 Versions, logical clocks and conflicts

A scalar version under one leader orders updates. Lamport clocks establish: if event A happened-before B, then timestamp(A)<timestamp(B); the converse is not guaranteed. **Vector clocks/version vectors** track a counter per replica and can detect concurrency. Clock `{A:2,B:1}` and `{A:1,B:2}` are concurrent because each is ahead on one component; the lab proves it.

Vector metadata grows with participants and does not resolve conflicts; it tells you they are concurrent. Resolution must be domain-aware. A shopping cart can merge set additions (with deletion semantics designed). Two payments cannot be “merged” by choosing a larger amount. Last-write-wins uses a total order, commonly timestamp, and silently discards one update; physical clock skew makes it especially dangerous. Preserve siblings and reconcile, designate one authority, or use a CRDT whose merge matches the domain.

### 2.6 CRDTs

A Conflict-free Replicated Data Type has operations/state that merge deterministically under specified algebraic properties such as associativity, commutativity and idempotence. A grow-only set unions elements; a G-counter maintains per-replica increments and merges component-wise maxima, then sums. A PN-counter combines positive/negative counters.

CRDT does not mean every business invariant survives. Two replicas can each decrement the last inventory item if independent availability is allowed. Escrow/bounded-counter designs allocate rights so local changes cannot exceed assigned capacity, but rebalancing rights requires coordination. Use CRDTs for data whose merge semantics are valid—likes, observed sets, collaborative state—not as a slogan to avoid transactions.

### 2.7 Read repair, anti-entropy and hinted handoff

Leaderless systems reconcile divergent replicas. **Read repair** updates stale replicas discovered during a read. **Anti-entropy** compares replica data (often using Merkle trees) in background. **Hinted handoff** stores a write temporarily for an unavailable target. These improve convergence but do not make every read current. Repair rates, tombstone retention and node replacement determine whether deleted values can resurrect.

Tombstones must live long enough for all replicas/repair paths to learn deletion; removing them too soon while an old replica returns can resurrect data. Long retention consumes storage and conflicts with privacy deletion. Regulated systems need explicit erase propagation/audit and may use encryption-key destruction or authoritative deletion workflows rather than relying on eventual cleanup alone.

### 2.8 Idempotency-key protocol

For `POST /payments`, client creates stable random key scoped by authenticated tenant and operation endpoint. Server calculates canonical request fingerprint and transactionally inserts:

```text
(tenant_id, key) UNIQUE
request_hash, operation_id, state, response_code/body_ref,
created_at, expires_at, lease_owner, lease_until
```

First request owns execution. Same key + same fingerprint returns stored result or in-progress status. Same key + different fingerprint returns conflict. Crash recovery uses lease/status and reconciliation. Store result atomically with business effect where possible.

Canonicalization must be stable: raw JSON byte hash treats field order/whitespace as different; a parsed canonical schema or explicit relevant fields is safer. Never use unauthenticated global keys that let one tenant infer/replay another's result. Do not store secret/card/PHI response bodies unnecessarily.

Retention equals retry horizon. If key records expire in 24 hours, contract must state behavior after 24 hours. A provider may retain its key longer/shorter than you; propagate stable derived identity and reconcile.

### 2.9 Idempotent consumers and inbox/outbox

Kafka delivers at least once around an external DB. Consumer opens transaction, inserts `(consumer_name,event_id)` UNIQUE, applies business mutation, commits, then advances offset. Duplicate insertion signals already applied. Alternatively make business mutation itself conditional on unique operation identity. A separate inbox row and effect must be in the same database transaction; otherwise crash can record “processed” without effect or effect without marker.

Dedupe storage grows: at 10,000 events/s for seven days, 6.048 billion IDs. Use retention aligned with source replay, partitioned tables, compact identity representation or business-level permanent identity. Bloom filters cannot be sole correctness dedupe because false positives would drop legitimate effects.

### 2.10 Commutativity and natural idempotency

Some operations become retry-safe through structure:

- `PUT /resource/{id}` replacing with same representation is idempotent.
- `INSERT ... ON CONFLICT DO NOTHING` under a unique logical ID dedupes.
- `max(current,versionedValue)` is idempotent if version ordering/meaning is sound.
- Set union is commutative/idempotent.

Increment, append email, charge card and “allocate next number” are not naturally idempotent. Wrap them in operation identity or use a ledger entry with unique transfer ID. Commutativity lets reorder; idempotency lets repeat. Addition commutes but repeating addition changes result.

### 2.11 Distributed transactions and two-phase commit

Two-phase commit (2PC) uses a coordinator. Participants prepare (durably promise they can commit), then coordinator decides commit/abort. It provides atomic commitment under its assumptions but can block participants in prepared state if outcome/coordinator is unavailable; recovery logs and presumed-abort/commit details matter. It is not consensus by itself and does not make unreliable external APIs transactional.

XA can coordinate supported resource managers but increases coupling, latency and operational complexity. Use when atomicity across a small controlled set is essential and infrastructure genuinely supports it. Do not put a human task/email/payment gateway into 2PC.

### 2.12 Sagas and compensations

A **saga** is a sequence of local transactions with messages and compensating actions. Choreography reacts to events; orchestration has a coordinator state machine. The included payment saga shows reservation, authorization and completion, with unknown/compensation-pending states.

Compensation is not rollback. Releasing inventory after reservation is a new action that can fail. Refunding a captured payment is observable and may incur fees; it does not erase the original charge. Every step and compensation needs idempotency key, durable state, retry policy and reconciliation. State-machine transitions use optimistic version/unique command IDs so duplicate/reordered messages cannot move backward.

An authorization timeout is unknown; compensating inventory immediately may be correct, but sending another authorization under a new key can double charge. Query provider using same identity before deciding.

### 2.13 TCC and reservations

Try-Confirm/Cancel reserves capacity then confirms or cancels. It is useful for inventory/funds where resources can be held with expiry. Reservations need unique operation, quantity, status, expiry and fencing/version. Expiry races with confirm: confirmation must atomically verify reservation is active/unexpired under authoritative clock/transaction. A sweeper's cancellation is idempotent. Holds reduce availability and can be abused; enforce tenant quotas.

### 2.14 Fencing and leases

A lease grants temporary ownership, but a paused owner can resume after expiry. Give each grant monotonically increasing **fencing token**; protected resource stores greatest token and rejects lower ones. Token 45 accepted means stale owner 44 cannot write. The resource—not lock service—must enforce it.

Fencing handles stale owners, not duplicate business operations; pair it with operation identity. Clock-based lease expiration requires explicit assumptions. Consensus-backed sequence/DB row version often supplies tokens more safely than client wall clock.

### 2.15 Consistency by domain

Do not choose one consistency level for a whole company. Payment ledger and authorization decisions usually require strongly ordered, invariant-preserving authority. Product catalog and model documentation may tolerate bounded stale reads. Model artifact bytes can be immutable/content-addressed and globally cached. A mutable “current approved model” pointer may require linearizable promotion and read-your-writes. Analytics can be eventually consistent with freshness timestamp.

In healthcare, eligibility/consent/authorization staleness can create safety/privacy harm. Define maximum age and fail posture. Multi-region availability does not justify stale permission. Minimize replicated PHI and audit who observed which version.

### 2.16 Verification and observability

Consistency bugs are histories, so final-state unit tests are insufficient. Use deterministic simulations/model checking for state machines; Jepsen-style fault testing records invocation/completion histories and checks models such as linearizability. Inject partitions, clock skew, process pause, failover and response loss.

Record version/read source, staleness/replication lag, conflict/merge counts, idempotency hit/conflict/in-progress/expiry, saga state age, compensation failures and reconciliation mismatch. Avoid logging sensitive request hashes/payloads if they can leak data. An SLO can state “99.99% of catalog reads ≤30 s stale,” while payment correctness is an invariant, not a percentile allowed to fail 0.01%.

## 3. WORKED PROBLEMS

### Problem 1 — Linearizability history

**Statement.** W(1) completes at t=100; R starts t=120 and returns 0. Is history linearizable?

**Solution.** No. Real-time order requires W's linearization before R because W completed before R began. Register after W is 1, so R cannot return 0. If intervals overlapped, the read might linearize before W and return 0 legally.

**Mistake caught.** Treating eventual later convergence as linearizability.

### Problem 2 — Quorum math

**Statement.** N=5 replicas. Evaluate R=3,W=3 and R=1,W=3.

**Solution.** For 3/3, `R+W=6>5` and `2W=6>5`, so read/write and write/write quorums overlap. For 1/3, `1+3=4≤5`, so a read may avoid latest write quorum. Even 3/3 is not proof of linearizability without handling concurrency, sloppy quorums, failed writes and conflict resolution.

**Mistake caught.** Stopping at `R+W>N` and declaring correctness.

### Problem 3 — Vector clocks

**Statement.** Compare `{A:2,B:1}` and `{A:1,B:2}`.

**Solution.** First is greater on A and smaller on B, so neither component-wise dominates; they are concurrent. Preserve siblings or apply domain merge. `{A:3,B:2}` dominates both and can represent a causally later resolved update.

**Mistake caught.** Sorting by sum (both total 3) or wall timestamp.

### Problem 4 — Idempotent payment

**Statement.** Same key arrives twice concurrently with amount ₹1,250; a third request reuses it for ₹1,500.

**Solution.** Unique `(tenant,key)` lets one insert/own. Second has same canonical hash and waits/returns same operation/result. Third hash differs and receives 409 conflict; it never changes original. Store 125000 minor units, not float. Payment/key/outbox commit atomically.

**Mistake caught.** Treating any same key as permission to return unrelated success.

### Problem 5 — Dedupe retention

**Statement.** Consumer processes 10,000 events/s and retains every 16-byte ID plus estimated 40 bytes row/index overhead for seven days. Rough logical bytes?

**Solution.** Events `10000×604800=6,048,000,000`. At 56 bytes each, `338,688,000,000` bytes ≈338.7 GB decimal before page/allocator/WAL/replication. Measure actual DB size. Consider partitioned retention/business unique keys; ensure seven days covers replay.

**Mistake caught.** Ignoring index/row overhead or deleting before source retention.

### Problem 6 — Saga unknown payment

**Statement.** Inventory reserved; authorization call times out.

**Solution.** Move saga to `AUTHORIZATION_UNKNOWN`, persist attempt/provider key. Query provider/status and retry only same key. If confirmed captured, continue; if definitively rejected/not-created per provider contract, compensate inventory; if unresolved, keep reconciliation and alert. Do not issue a new authorization or assume no charge.

**Mistake caught.** Treating timeout as rejection and immediately retrying with new identity.

### Problem 7 — Lease split-brain

**Statement.** Worker with fencing token 44 pauses beyond lease; token 45 owner writes; 44 resumes.

**Solution.** Protected storage remembers 45 and rejects any mutation tagged 44. Compare-delete lock release prevents deleting owner 45's lease but cannot stop 44's external write; fencing can if resource enforces monotonic token. Operation identity separately dedupes repeated logical action.

**Mistake caught.** Assuming lease TTL proves only one live worker.

### Problem 8 — CAP product decision

**Statement.** Network partitions two regions. One holds current consent revocation; the other receives data-export request.

**Solution.** Serving stale authorization risks privacy violation. Reject/defer export in partitioned region or route to a quorum/current authority; preserve consistency for this operation, sacrificing theorem availability. A public catalog browse might serve bounded stale data instead. CAP choice is per operation and business harm.

**Mistake caught.** Labeling entire platform AP/CP without domain semantics.

### Problem 9 — Concurrent inventory

**Statement.** Two regions each see one item and accept a sale during partition.

**Solution.** Eventual merge cannot undo oversell invariant. Options: one consensus/leader authority and reject unavailable region; preallocate escrow rights (region A one, B zero) so local acceptance cannot exceed rights; or accept oversell and compensate if product explicitly allows it. Last-write-wins loses a sale but not its external effects.

**Mistake caught.** Using CRDT/LWW to claim arbitrary invariants converge correctly.

## 4. REAL-WORLD / APPLIED CONTEXT

**Amazon Dynamo.** The 2007 Dynamo paper prioritizes availability for an internal key-value service using consistent hashing, sloppy quorums, hinted handoff, versioning and application-assisted conflict resolution. Its shopping-cart semantics tolerate merging far better than a money ledger. The value is the explicit business-driven trade-off, not copying every mechanism.

**Google Spanner.** The 2012 Spanner paper provides externally consistent transactions using Paxos replication and TrueTime intervals. It reported clock uncertainty generally below 10 ms in its environment and waits out uncertainty to preserve timestamp order. That is a system-specific architecture/measurement, not evidence that NTP timestamps make an ordinary database globally linearizable.

**Payment workflow.** One PostgreSQL authority enforces idempotency/ledger transaction; outbox sends saga commands/events. Inventory and gateway are local authorities. Orchestrator stores versioned state and unknown outcomes; commands/compensations carry saga+step IDs. A reconciliation job compares provider settlements, ledger and saga terminal states.

`ConsistencyLab.java` executes vector-clock comparison, quorum-overlap arithmetic, duplicate ledger suppression and compensation state. It deliberately does not simulate a network or claim those arithmetic checks prove a deployed store's consistency.

## 5. COMPARISON TABLE

| Model | Required observation | Typical use | Cost/failure trade-off |
|---|---|---|---|
| Linearizable | real-time single-copy behavior | leader election, balance/current pointer | coordination latency/unavailability during partition |
| Serializable | transactions equivalent to serial order | multi-row invariants | abort/retry; not necessarily real-time |
| Strict serializable | serializable + real-time | global financial/metadata authority | stronger coordination/latency |
| Causal | causes visible before effects | collaboration/social/session flows | metadata/routing; concurrent writes remain |
| Read-your-writes | session sees own writes | user profile/config UX | session token/stickiness/catch-up wait |
| Eventual | convergence after updates stop | derived catalog/analytics | unbounded intermediate staleness/conflicts |

| Workflow mechanism | Atomic scope | Failure behavior | Best fit |
|---|---|---|---|
| Local ACID tx | one database/resource manager | rollback/serialization retry | invariants colocated in DB |
| 2PC/XA | supported participants | prepared blocking/coordinator recovery | small controlled atomic set |
| Saga | sequence of local tx | intermediate states, compensation failure | long/cross-service business process |
| TCC | explicit reservation/confirm/cancel | held capacity/expiry races | inventory/funds reservations |
| Idempotent at-least-once | each sink effect by operation ID | duplicates tolerated, dedupe storage | messaging/external retry |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Consistency means replicas identical now.”** Name the formal/session model and scope.
2. **Linearizability equals serializability.** One respects operation real time; the other orders transaction effects.
3. **CAP means choose two all the time.** Trade-off is under partition and uses strict definitions.
4. **A timeout is a partition proof.** It is local failure suspicion; slow overload and lost response look similar.
5. **`R+W>N` guarantees linearizability.** Concurrent/sloppy/failed writes and resolution protocols still matter.
6. **Last-write-wins resolves business conflicts.** It discards one write, possibly using skewed clocks.
7. **Vector clocks resolve conflicts.** They detect causal dominance/concurrency; domain logic resolves.
8. **CRDT preserves every invariant.** Mergeable data is not equivalent to bounded inventory or money safety.
9. **Idempotent HTTP method makes downstream safe.** Email/charge/increment still needs logical identity.
10. **Store key after effect.** Crash between effect and key allows duplicate; make them atomic where possible.
11. **Same key, different request returns old success.** It must conflict to prevent accidental/malicious key reuse.
12. **Dedupe forever is free.** High-rate identity storage needs retention/capacity tied to replay horizon.
13. **Bloom filter for correctness dedupe.** False positives drop legitimate events.
14. **Saga compensation is rollback.** It is a new fallible observable action.
15. **Lease prevents stale owner.** Paused owner resumes; protected resource needs fencing.
16. **Eventual consent/authorization is harmless.** Stale permission can violate safety/privacy; fail posture is domain-specific.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Linearizable: atomic point + real-time order. Serializable: serial-equivalent transactions. Strict = both.
- Eventual consistency promises convergence after updates/communication, not bounded freshness.
- Session guarantees: read-your-writes, monotonic reads/writes, writes-follow-reads.
- CAP: under partition cannot guarantee Gilbert-Lynch linearizability and every-node availability.
- Quorum overlap: `R+W>N`, write overlap `2W>N`; necessary arithmetic, not full proof.
- Vector clock: component-wise dominance = causal order; mixed greater/less = concurrent.
- Idempotency record: scoped key UNIQUE + canonical request hash + durable state/result + retry-horizon retention.
- Consumer: event-ID marker and business effect in one sink transaction; offset afterward.
- Commutative ≠ idempotent: addition reorders safely but duplicate addition changes result.
- 2PC provides atomic commitment for supported resources; saga provides local transactions + fallible compensations.
- Timeout after side-effect request = unknown; query/retry same identity.
- Lease + unique release token is insufficient for stale writer; resource enforces fencing.
- Correctness invariant is not a percentile SLO.

## 8. PRACTICE SET FOR SELF-TEST

1. Construct a legal linearizable ordering for two overlapping writes and a read; then give one impossible history.
2. For N=7, find two R/W pairs satisfying read/write and write/write overlap; discuss latency/availability differences.
3. Compare vector clocks `{A:4,B:2,C:0}`, `{A:4,B:1,C:3}` and `{A:5,B:2,C:3}`.
4. Design idempotency storage and response semantics for `POST /model-promotions`, including key reuse with different model digest.
5. At 25,000 events/s and 14-day replay horizon, calculate event IDs retained; explain capacity beyond count.
6. Design read-your-writes when writes go to leader region and reads normally use local replica.
7. Decide consistency for payment ledger, product catalog, approved-model pointer and analytics dashboard.
8. Build a saga for appointment booking plus payment deposit, including timeout-unknown and failed compensation.
9. Explain why two available regions cannot both accept the last inventory item during partition while guaranteeing no oversell, unless rights were preallocated.
10. Design a test history that distinguishes a stale follower read from a linearizable service.

## 9. CURATED RESOURCES

1. Herlihy and Wing, “Linearizability: A Correctness Condition for Concurrent Objects,” TOPLAS 1990. Formal histories, real-time order and compositionality.
2. Gilbert and Lynch, “Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services,” SIGACT News 2002. Precise CAP definitions/proof rather than “choose two.”
3. Lamport, “Time, Clocks, and the Ordering of Events in a Distributed System,” CACM 1978. Happened-before relation and logical clocks.
4. DeCandia et al., “Dynamo: Amazon's Highly Available Key-value Store,” SOSP 2007. Sloppy quorums, hinted handoff, versioning and business-driven eventual consistency.
5. Corbett et al., “Spanner: Google's Globally-Distributed Database,” OSDI 2012. External consistency, Paxos and TrueTime uncertainty/commit wait.
6. Shapiro et al., “Conflict-Free Replicated Data Types,” SSS 2011. Formal convergence conditions and CRDT families.
7. Gray and Lamport, “Consensus on Transaction Commit,” TODS 2006. Relationship between classic 2PC blocking and Paxos Commit.
8. Garcia-Molina and Salem, “Sagas,” SIGMOD 1987. Original long-lived transaction/compensation model.
9. Kleppmann, *Designing Data-Intensive Applications*, Chapters 5, 7, 8 and 9. Replication, isolation, failure and consistency integration with concrete systems.
10. Bailis et al., “Highly Available Transactions: Virtues and Limitations,” VLDB 2014. Which transactional guarantees are achievable under high availability and where coordination is needed.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Failure Semantics.** Timeouts and partitions create ambiguity that consistency and idempotency contracts resolve.
2. **Kafka and Eventing.** At-least-once delivery, per-partition order and outbox supply concrete duplicate/reordering cases.
3. **Transactions and Locking.** Local ACID boundaries are the building blocks for dedupe, outbox and saga steps.

### After

1. **Capacity-Driven System Design.** Stronger quorum/coordination and replay retention have quantitative latency/capacity costs.
2. **Cloud Data Services.** Managed databases expose selectable read/write consistency, regional replication and failover.
3. **SRE and Testing.** History checking, reconciliation, lag and invariant alerts operationalize guarantees.
4. **Regulated Design.** Consent, deletion, audit and financial correctness constrain where eventual consistency is acceptable.

---ANSWER KEY BELOW---

1. Example legal: W1 and W2 overlap, W2 returns, read begins after both and returns W1; linearize W2 then W1 if response intervals allow. Impossible: W1 completes, then read begins and returns pre-W1 value. Draw invocation/response intervals and respect nonoverlap real time.
2. Examples R=4,W=4 (`8>7`, `8>7`) balanced; R=1,W=7 (`8>7`, `14>7`) fast reads but writes require all seven and are fragile. R=6,W=2 also satisfies (`8>7`,`4≤7` fails write/write), so it is not acceptable if overlapping writes required; check both inequalities.
3. First vs second: concurrent (first greater B, second greater C). Third `{5,2,3}` dominates both, so both happened-before it or were incorporated. Equality/missing component treated as zero under the model.
4. Unique tenant+key, canonical hash including endpoint/model digest/target/config, operation ID/state/version/result, timestamps/lease/expiry. Same key/same digest returns current/result; same key/different digest is 409. Persist promotion intent/outbox atomically and use same identity downstream.
5. `25000×14×86400 = 30,240,000,000` IDs. Capacity includes ID/row/index/page/WAL/replication/backups, partition maintenance and lookup throughput; align retention with Kafka replay and permanent business IDs where needed.
6. Return a commit/version token; subsequent reads send minimum token. Route to leader or wait/select a replica whose applied position ≥ token, with deadline/fallback. Sticky routing alone fails on rebalance; bounded stale response must expose inability if token not reached.
7. Ledger: serializable/strict durable authority. Catalog: bounded eventual plus version/freshness. Approved-model pointer: linearizable promotion and read-your-writes/current version. Analytics: eventual with as-of/lag metadata. Exact choice follows harm/SLO.
8. Reserve appointment under saga ID; authorize deposit same provider key; timeout → PAYMENT_UNKNOWN and status reconciliation; success confirms booking; rejection cancels reservation. If cancellation fails, COMPENSATION_PENDING with retries/alert; every command/compensation idempotent and state-version guarded.
9. During partition neither side can know whether other accepted. If both must answer success, both can sell it; if no oversell, at least one side must reject/wait/route or hold zero preallocated rights. Escrow coordinates rights before partition.
10. Complete write v2 through authority, then begin read on tested endpoint. A follower returning v1 violates linearizability because operations do not overlap. Record invocation/completion times and nemesis/failover; repeat histories and verify no later read regresses after observing v2.
