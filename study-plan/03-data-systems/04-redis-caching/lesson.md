# Redis and Caching

**Parent:** 03 — Data Systems  
**Target:** senior backend / AI-platform / MLOps engineering  
**Study time:** 3–4 hours plus executable exercises

## 1. FOUNDATIONS

A cache stores a reusable result closer to or cheaper for its consumer than the authoritative source. If a PostgreSQL lookup takes 12 ms and a local memory lookup takes 50 microseconds, caching can remove repeated database work. But the cache is a **derived copy**. Once two copies exist, they can disagree. The hard question is not how to call `GET`; it is how stale the copy may be, how it is invalidated, what happens on cache failure, and whether the source can survive misses.

Caching exploits **locality**. Temporal locality means something recently used is likely to be used again. Spatial locality means nearby data is likely to be used. A workload with a skewed popularity distribution—often approximated by a Zipf distribution—can achieve a high hit rate with a cache much smaller than the complete dataset. A uniformly random one-time scan cannot. A **hit** returns a usable cached value. A **miss** consults the source. Hit ratio is `hits/(hits+misses)`, but a global 95% can conceal a 20% hit rate on the expensive tenant or a miss storm at one key.

The expected latency arithmetic is simple but incomplete. With 95% hits at 1 ms and 5% misses at 25 ms, the weighted mean is `0.95×1 + 0.05×25 = 2.2 ms`, excluding cache lookup on the miss path if it precedes the database. Tail latency, serialization, network queues and correlated misses matter more than this average. If 10,000 requests/second have a 5% miss rate, the source sees about 500 reads/second. If a hot key expires and 5,000 waiting requests all reload it, the brief **stampede** can exceed the source capacity even though the long-run miss ratio is excellent.

Redis is an in-memory data-structure server commonly used as a remote shared cache. Remote is important: an application-local cache avoids a network hop and isolates failures, but every process has its own stale copy and memory footprint. Redis centralizes cache state and supports atomic commands, TTLs, counters, sets, sorted sets, streams and scripts, but adds a network dependency and finite-memory behavior. Redis is often fast; no fixed microsecond number is universal. Measure command latency on the actual topology, payloads, TLS, pipelining and load.

A **TTL** (time to live) makes an entry expire after a duration. TTL bounds how long an entry can remain without refresh, but it does not guarantee freshness until expiry, nor does it guarantee an expiration event occurs at the exact millisecond the TTL reaches zero. Redis documentation explains passive expiration on access plus active background sampling. A **maximum staleness** requirement is a product correctness statement; a TTL is only one mechanism toward it.

Caching grew from CPU and storage hierarchies, but distributed application caching adds partial failure. The cache may be down while the database is healthy; the database may commit while invalidation is lost; a replica may be stale; an object may exceed expected size; one key may consume a shard's command capacity. Senior design starts by classifying data: authoritative or reconstructible, security-sensitive or public, mutation rate, tolerated staleness, access skew, and source fallback capacity.

## 2. CORE MECHANICS

### 2.1 Cache-aside

In **cache-aside** (lazy loading), the application reads cache, loads the database on miss, then populates cache:

```text
value = cache.get(key)
if value exists: return value
value = database.read(key)
cache.set(key, serialize(value), ttl)
return value
```

It is simple and fills only demanded data. Failure cases matter. Multiple misses can stampede. A database update between the read and cache set can let a slow loader write stale data after invalidation. Prevent regression with versioned values and compare/set logic, short TTLs where acceptable, or an invalidation protocol ordered through a durable change stream. Cache “not found” briefly to stop penetration, but distinguish absence from cache failure.

On write, common cache-aside ordering is commit database, then delete cache. Deleting first creates this race: writer deletes; reader misses and reads old uncommitted/previous database value; reader caches it; writer commits, leaving stale cache. Commit-then-delete has a smaller but real failure window if deletion is lost. An outbox/change-data-capture invalidator plus TTL and monitoring improves recovery. There is no magical order that atomically spans independent database and Redis without a broader protocol.

### 2.2 Read-through, write-through, write-behind

A **read-through** cache/library loads the source automatically; it centralizes loader behavior but hides expensive misses if poorly instrumented. **Write-through** writes the cache layer and authoritative store synchronously, keeping reads warm but adding latency and coupling. **Write-behind** acknowledges cache writes then persists asynchronously, improving latency/batching but risking loss/reordering and turning Redis into part of the system of record. For payments or clinical records, do not casually use write-behind. Define recovery, durability and audit guarantees first.

### 2.3 TTL selection and jitter

TTL trades freshness, hit ratio and source load. If product data may be stale for five minutes, `EX 300` is an upper refresh interval only when writes/invalidation semantics support it. Apply **jitter** so one million keys created together do not all expire at exactly five minutes. A uniform 300–360 second TTL spreads expected expirations across 61 integer-second buckets; under uniform hashing, one million entries average about 16,393 expirations per bucket rather than a synchronized million. Real distributions vary.

Boundary conditions: Redis expiration has millisecond resolution, but an expired key may be removed on access or background work. `TTL` returns special negative values for missing/no-expiry keys; clients must interpret their Redis-version semantics. Never use expiration notification timing as a reliable scheduler. `CacheLab.java` checks expiry exactly at the boundary and deterministic 300–360 second jitter.

### 2.4 Stampede protection

**Request coalescing/single-flight** lets one process load a missing key while peers await the same result. It must have a timeout and propagate neither an infinite hang nor an unbounded queue. Across instances, a short lease can coordinate reloads, but lock failure should degrade deliberately.

**Stale-while-revalidate** stores fresh and stale deadlines. Before fresh deadline, serve normally. Between fresh and stale deadlines, serve the old value while one worker refreshes. After stale deadline, block/fail according to safety. This is suitable for a product catalog but potentially unsafe for authorization or a revoked clinical consent. The data classification determines whether stale serving is permitted.

**Probabilistic early refresh** spreads refresh before expiry. The exact algorithm should be documented and tested; do not add random TTL alone and claim stampede is solved. A hot single key can still have thousands of simultaneous readers when it expires.

### 2.5 Cache penetration and negative caching

Penetration means repeated requests for keys that do not exist bypass the cache. Cache a typed negative result, e.g. `NOT_FOUND(version=...)`, for a short TTL such as 30 seconds. That changes creation visibility: if a patient is created immediately afterward, readers may see the negative until invalidation/expiry. Never encode absent as an empty object indistinguishable from a real empty record. Bloom filters can reject definitely absent keys with no false negatives under their construction assumptions, but false positives still hit the database and deletion/update semantics add complexity.

### 2.6 Hot keys and sharding

A hot key concentrates requests on one Redis shard because a key hashes to one slot. Adding shards does not split one key. Remedies include local near-cache with bounded staleness, replicating read-only value under multiple derived keys, client-side caching/invalidation, or redesigning the aggregate. Counter sharding distributes increments across N keys but reads must sum them and become temporarily inconsistent.

Redis Cluster hash tags `{...}` force related keys into one slot, enabling multi-key operations/scripts but can create a hot slot. Multi-tenant key names must include tenant scope and avoid sensitive raw identifiers when logs/metrics expose keys. Example: `patient:{tenant-42}:7` co-locates a tenant; that may be useful or dangerously imbalanced.

### 2.7 Memory accounting and eviction

`maxmemory` bounds cache dataset memory, and `maxmemory-policy` decides what happens when writes exceed it. Redis current documentation lists `noeviction`, all-keys and volatile families including approximate LRU/LFU/random/TTL-based choices. **Volatile** policies consider only expiring keys; if none qualify, writes can fail. Mixing persistent coordination data and evictable cache data in one instance creates ambiguous policy—separate workloads when possible.

Redis approximate LRU samples candidates rather than maintaining exact global LRU, saving metadata/CPU. LFU favors frequently used keys and can resist scans better, but adaptation/decay must match workload. `allkeys-lru` is a reasonable baseline for pure cache with recency locality; benchmark trace replay rather than choosing by slogan.

Memory is not payload bytes alone. Keys, object headers, allocator fragmentation, expiration metadata, client buffers, replication and AOF buffers matter. Redis says replication/persistence buffer memory represented by `mem_not_counted_for_evict` is excluded from the eviction comparison, so leave headroom. Use `MEMORY USAGE`, `INFO memory`, fragmentation ratios and representative serialized objects. A 1 KiB JSON value does not mean one million keys fit safely in exactly 1 GiB.

### 2.8 Data structures and atomicity

Strings store serialized objects and counters. Hashes store fields, sets membership, sorted sets score ordering, HyperLogLog approximate cardinality, and streams append entries. Choose based on operations and memory measurements, not semantic resemblance alone.

Individual Redis commands are atomic relative to other commands. A sequence `GET`, calculate, `SET` is not. Use `INCR`, conditional `SET NX/XX`, transactions (`WATCH`/`MULTI`/`EXEC`), or a Lua/function operation when atomic composition is required. The supplied fixed-window limiter uses one Lua invocation to increment and set expiry only on the first count. It still has algorithmic limitations: requests can burst across a window boundary, and a single key may become hot.

Pipelining batches network round trips but does not make commands one transaction. Transactions queue commands and execute them without interleaving, but Redis does not provide database-style rollback for runtime command errors. Scripts run atomically and block the server's command processing while executing, so keep them bounded and deterministic with respect to provided inputs/Redis state.

### 2.9 Serialization, schema versioning and compression

Cache keys and values form a schema. Include namespace and semantic version: `model-summary:v3:{tenant}:{modelId}`. Deploy readers capable of old/new formats during rolling changes or bump namespace and accept cold misses. Store source version/updated time in the value so late refreshes cannot overwrite newer content. Compression lowers bytes but consumes CPU and may amplify latency for small objects; measure thresholds.

Never cache secrets or protected health information merely because Redis is “internal.” Apply TLS/auth/network isolation, least privilege, encryption requirements, tenant separation, retention and audit policy. Cache dumps, AOF, replicas and support tooling expand exposure. Avoid secrets/PHI in key names because keys appear in diagnostics.

### 2.10 Failure behavior and source protection

Decide **fail open** (bypass cache) versus **fail closed** by data. If Redis fails and every request immediately hits PostgreSQL, the cache outage becomes a database outage. Bound fallback with circuit breakers, concurrency limits, timeouts, load shedding and stale serving only where permitted. Prewarm carefully: a fleet restart that scans millions of database rows can itself cause failure.

Use separate timeouts for connection acquisition and command execution. Retry only safe operations with a small budget; automated retries multiply load. A rate limiter stored in unavailable Redis needs an explicit product/security posture: deny, allow with local emergency limits, or degrade by endpoint. “High availability” does not answer this policy question.

### 2.11 Replication and persistence limits

Redis replication is asynchronous by default. Redis documentation states `WAIT` can request acknowledged replica copies but does not make the deployment a strongly consistent CP system, and acknowledged writes may still be lost during failover depending on persistence/configuration. Treat a disposable cache differently from sessions, quotas or locks. If data cannot be reconstructed, Redis is not “just a cache”; specify RDB/AOF, replication, restore and consistency requirements accordingly.

Keyspace notifications are Pub/Sub and fire-and-forget: disconnected consumers miss events. Expiration events occur when Redis deletes the key, not at the theoretical TTL instant, and cluster notifications are node-specific. Therefore they are observability hints, not a durable invalidation log. Use an outbox/CDC/Kafka stream for durable invalidation where needed.

### 2.12 Distributed locks and fencing

For a single Redis instance, acquire a lease with `SET resource unique-token NX PX 30000`. Release with compare-and-delete Lua so an expired former owner cannot delete a successor's lock. But a lease can expire while a paused client continues work. Two actors can then affect an external resource.

A **fencing token** is a monotonically increasing number returned on each successful ownership grant. The protected storage rejects operations with a token lower than the greatest already accepted. This makes a stale owner harmless if the resource enforces fencing. Redis's distributed-lock documentation now explicitly advises fencing for consistency-critical work and notes wall-clock/TTL hazards. For financial or clinical correctness, prefer database constraints/transactions or a consensus-backed coordinator with fencing rather than assuming a cache lease is a universal mutex.

### 2.13 Measuring success

Measure per cache/tenant/key class: requests, hits, misses, negative hits, stale serves, loader latency/errors, coalesced waiters, evictions, expirations, memory/fragmentation, command latency, connections and source fallback. Track **byte hit ratio** as well as request hit ratio: caching many tiny hits while repeatedly missing 20 MB model artifacts may save requests but not bandwidth. Test failure by disabling cache, adding latency, restarting nodes and creating hot-key/expiry waves.

## 3. WORKED PROBLEMS

### Problem 1 — Capacity arithmetic

**Statement.** A service has 8,000 reads/s. Cache hit rate is 92%. Cache access is 0.8 ms and database load after a miss adds 18 ms. Estimate source QPS and mean path latency.

**Solution.** Miss fraction is 0.08, so source load is `8000×0.08=640 reads/s`. Every request pays 0.8 ms; misses add 18 ms: `0.8 + 0.08×18 = 2.24 ms`. This is a mean model; it omits queuing and tail effects. Verify whether the database can handle a transient 8,000/s when cache is down.

**Mistake caught.** Applying the database latency only to total requests but forgetting the cache lookup on misses.

### Problem 2 — Cache-aside stale fill

**Statement.** Reader misses and reads DB version 7. Writer commits version 8 and deletes cache. Slow reader then sets version 7.

**Solution.** The invalidation occurred before the stale fill, so stale v7 survives until TTL. Store source version and use atomic compare logic that refuses to replace a higher version, or order refreshes through durable change versioning. TTL bounds residual damage; a second delete can narrow but not prove elimination of all races. `CacheLab.java` demonstrates rejecting late version 8→7 regression.

**Mistake caught.** Claiming “write DB then delete cache” eliminates every race.

### Problem 3 — TTL wave

**Statement.** One million product keys are written during deployment with exactly 300-second TTL; database capacity is 20,000 reads/s.

**Solution.** A synchronized expiry can create up to demand-scale reloads near one instant. Add deterministic/random jitter, e.g. 300–360 seconds, request coalescing per key and bounded stale-while-revalidate where catalog staleness is safe. Prewarm gradually. Uniformly distributing one million expirations over 61 second buckets averages ~16,393/s, below 20,000 only before normal traffic/skew, so retain headroom and load test.

**Mistake caught.** Treating average distribution as a guaranteed maximum.

### Problem 4 — Negative cache

**Statement.** Bots request 50,000 random nonexistent model IDs/s; each DB miss costs 4 ms.

**Solution.** Validate input/authorization before lookup, rate-limit abusive callers, and negative-cache legitimate absence for perhaps 30 seconds keyed by tenant+ID. A repeated absent key then hits cache; uniformly new random IDs will not, so negative caching alone fails. A Bloom filter or existence index can help, with monitored false positives and update process.

**Mistake caught.** Caching “null” indefinitely, hiding a subsequently created model.

### Problem 5 — Eviction policy

**Statement.** A pure cache has a long-tail catalog plus occasional scans. Choose between allkeys-LRU, allkeys-LFU and noeviction.

**Solution.** Start from trace replay. LRU may let a scan displace genuinely popular entries; LFU can preserve frequent entries, with adaptation trade-offs. `noeviction` turns memory pressure into write errors and is poor for reconstructible cache unless failure is intentionally handled. Set maxmemory with buffer/headroom, observe `evicted_keys`, hit rate and source load, then compare policies under the same trace.

**Mistake caught.** Declaring LFU universally superior without workload or decay behavior.

### Problem 6 — Hot model metadata key

**Statement.** One model configuration receives 120,000 GET/s; adding Redis shards does not help.

**Solution.** One key maps to one shard. Add a small local cache with version/invalidation and maximum staleness; optionally replicate immutable/versioned value across derived keys and spread readers. Keep authorization outside unsafe stale data. Measure one-node command/network capacity. Sharding unrelated keys increases cluster capacity but not this key's single-shard path.

**Mistake caught.** Assuming horizontal shard count divides a single key automatically.

### Problem 7 — Fixed-window limiter

**Statement.** Permit 100 requests per tenant per 60 seconds. Why must increment and first expiry be atomic?

**Solution.** If `INCR` succeeds and process crashes before `EXPIRE`, the limiter key persists forever. Lua atomically increments and sets `PEXPIRE 60000` when result is 1, as in `redis-lab.txt`. Reject count >100. Document boundary burst: 100 requests at 12:00:59.9 and 100 at 12:01:00.1 pass in 0.2 seconds. Sliding window/token bucket may better match policy.

**Mistake caught.** Calling two individually atomic commands an atomic compound operation.

### Problem 8 — Protected-health-data cache

**Statement.** Cache patient summaries for five minutes to cut DB latency.

**Solution.** First determine legal/security authorization and staleness requirements, especially consent/revocation. Use tenant-scoped opaque keys, encryption/TLS/auth/network controls, minimum fields, audit and deletion workflows; ensure replicas/backups/AOF meet policy. Invalidate from durable changes and choose fail-closed for authorization data. A performance benefit does not authorize storage of PHI in a new system.

**Mistake caught.** Treating a TTL as deletion/audit compliance.

### Problem 9 — Expired lease owner

**Statement.** Worker A holds a 30-second Redis lease, pauses for 45 seconds; worker B acquires and writes. A resumes.

**Solution.** Mutual exclusion has already failed in real time. Unique compare-delete prevents A from deleting B's lease but does not prevent A's stale write. Grant increasing fencing tokens; protected storage accepts token 102 from B and rejects A's older 101. If target cannot enforce fencing, do not use the lease for correctness-critical mutation.

**Mistake caught.** Believing lease ownership lasts while the process is alive.

## 4. REAL-WORLD / APPLIED CONTEXT

**Redis eviction.** Current Redis Open Source documentation says eviction begins when dataset memory crosses `maxmemory`; LRU is approximated via sampling rather than exact global tracking. It also exposes `mem_not_counted_for_evict` because replication/AOF buffers need headroom. This directly informs capacity alerts: memory below maxmemory does not prove the host cannot OOM from excluded buffers, clients or allocator overhead.

**Spring service cache-aside.** A product service may use Caffeine locally for 10-second near-cache and Redis for five-minute shared cache. PostgreSQL remains authoritative. An outbox emits versioned product changes; consumers evict both layers. On Redis failure, a bulkhead caps database fallback. This hierarchy saves two network paths on hot data but adds two invalidation surfaces, so metrics identify L1 versus L2 hit/staleness.

**ML feature/config serving.** Immutable model manifests work well with content/version-addressed keys because new versions never overwrite old values: `manifest:v1:sha256`. A small mutable “current model” pointer is harder; cache it briefly or invalidate durably and include generation. Never cache a large model artifact as millions of base64 strings without measuring memory amplification; object storage/CDN plus local disk is usually the better artifact hierarchy.

The included CLI lab provides exact `SET EX NX`, memory inspection, atomic limiter and safe compare-delete commands. The Java lab validates expiry boundary, 300–360 second jitter and version monotonicity without needing Redis. Actual server memory and latency must be recorded from your environment.

## 5. COMPARISON TABLE

| Pattern | Read path | Write/freshness behavior | Best use | Main failure |
|---|---|---|---|---|
| Cache-aside | app cache→DB→fill | DB then invalidate/expire | general read-heavy data | race/lost invalidation, stampede |
| Read-through | cache loads source | provider-defined | centralized loader | hidden miss cost/coupling |
| Write-through | synchronous cache+store | warm after success | strong operational integration | added write latency/dual-system failure |
| Write-behind | cache acknowledges, async store | eventually durable | loss-tolerant aggregation | loss/reordering; cache becomes authority |
| Refresh-ahead | background before expiry | bounded by scheduler | predictable hot keys | refresh unused data/failure waves |
| Stale-while-revalidate | serve stale during refresh | explicit stale window | catalog/config where stale safe | unsafe for authorization/revocation |

| Placement | Typical latency relationship | Consistency/memory | Use when |
|---|---|---|---|
| In-process | no network; fastest path | per-instance copies/staleness | very hot small data |
| Shared Redis | network hop | centralized finite memory | cross-instance reuse/atomic operations |
| CDN/edge | near user | invalidation across edges | public/static responses/artifacts |
| Database | authoritative path | durable constraints/transactions | truth or low reuse |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **“Redis is always sub-millisecond.”** TLS, network, payload, queuing and commands determine latency; measure percentiles.
2. **“95% hit rate means safe.”** A synchronized miss wave can overload the source; segment and failure-test.
3. **“TTL guarantees fresh data.”** A value can be stale immediately after source update; TTL only bounds refresh under assumptions.
4. **“Expiry event fires exactly on time.”** Redis removes passively/actively; notifications happen on deletion and are not a scheduler.
5. **“Pub/Sub invalidation is durable.”** Disconnected consumers lose keyspace notifications.
6. **Delete-before-commit.** A reader can refill old data between delete and source commit.
7. **Unversioned slow fill.** An old loader can overwrite a newer cached value.
8. **No TTL jitter.** Bulk-created keys create synchronized expiration and database load.
9. **Unlimited fallback.** Cache outage redirects the whole workload to the database and causes cascading failure.
10. **One shard fixes hot keys.** One key still belongs to one shard.
11. **Payload-size capacity math.** Redis memory includes keys, metadata, allocator, expires and buffers.
12. **Pipelining equals transaction.** It reduces round trips; commands can have different atomicity semantics.
13. **`SET NX PX` is a permanent mutex.** Pause/partition/clock effects can outlive lease; use fencing or stronger coordination.
14. **Compare-delete solves stale owner writes.** It protects release only, not the external resource.
15. **Caching authorization/PHI like catalog data.** Staleness and exposure have much higher consequences.

## 7. CHEAT SHEET — REVIEW ONLY, NOT A SUBSTITUTE FOR THE SECTIONS ABOVE

- Source QPS = request QPS × miss fraction; test cache-down QPS too.
- Cache-aside: get → source on miss → version-aware fill; writes commit source then invalidate with durable repair.
- TTL is freshness/capacity trade-off; add jitter; notifications are not precise/durable.
- Stampede: single-flight, bounded stale-while-revalidate, early refresh, source bulkhead.
- Negative cache typed absence briefly; random unique penetration needs validation/rate limit/filtering.
- Hot key is one-shard problem; use local cache/versioning or deliberate replication.
- Set `maxmemory`, leave headroom, choose eviction from trace; inspect `MEMORY USAGE` and `INFO`.
- Atomic single command ≠ atomic multi-command; use native operation, transaction or bounded Lua.
- Namespace/version keys and values; include source generation to prevent regression.
- Cache outage policy: explicit fail-open/closed, timeouts, circuit breaker, load shed.
- Keyspace notifications are fire-and-forget; use durable change log when required.
- Lease: unique token + compare-delete; correctness-critical external work also needs fencing.

## 8. PRACTICE SET FOR SELF-TEST

1. At 25,000 reads/s, 97.5% hits, 0.6 ms cache time and 14 ms added miss load, calculate source QPS and weighted mean path time.
2. Draw the exact interleaving where commit-then-delete loses the delete and state how TTL plus outbox repair bounds it.
3. Design TTLs and stampede protection for 600,000 exchange-rate keys where values update every minute and may be 10 seconds stale.
4. Choose an eviction policy for a mixed instance containing cache keys with TTL and non-expiring job coordination keys; identify the better architecture.
5. Explain why `GET counter; SET counter+1` loses increments and give two atomic alternatives.
6. Design a cache key/value schema for healthcare eligibility that prevents cross-tenant leakage and late-version regression.
7. A Redis failover loses an acknowledged rate-limit increment. Explain why `WAIT 1` is not a strong-consistency proof and define a safety posture.
8. Design a single-flight loader with timeout, stale window and behavior when the loader fails.
9. Given a 32 GiB host and observed 4 GiB replication/AOF buffers plus 3 GiB process/fragmentation headroom, propose a starting maxmemory and state why it is not final.
10. Explain fencing tokens with owners 44 and 45 and a storage service that has already accepted token 45.

## 9. CURATED RESOURCES

1. Redis Documentation, [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/). Current maxmemory behavior, complete policy list, approximate LRU and operational metrics.
2. Redis Documentation, [Keys and values: expiration](https://redis.io/docs/latest/develop/using-commands/keyspace/). Exact TTL precision/persistence semantics and command examples.
3. Redis Documentation, [`EXPIRE`](https://redis.io/docs/latest/commands/expire/). Passive/active expiration and replication behavior beyond simple TTL use.
4. Redis Documentation, [Keyspace notifications](https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/). Fire-and-forget, delayed expiry events and cluster node scope.
5. Redis Documentation, [Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/). Asynchronous replication and why `WAIT` does not provide CP guarantees.
6. Redis Documentation, [Distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/). Canonical lease algorithm, safety/liveness claims, fencing and clock disclaimer.
7. Redis Documentation, [Pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/). Round-trip batching, throughput effects and distinction from atomicity.
8. Nishtala et al., “Scaling Memcache at Facebook,” NSDI 2013. Real multi-region cache architecture, leases, stale sets and operational trade-offs.
9. Fan et al., “MemC3: Compact and Concurrent MemCache with Dumber Caching and Smarter Hashing,” NSDI 2013. Hash table/eviction design and measured cache-system engineering.
10. Kleppmann, “How to do distributed locking,” 2016. Critical analysis of leases and fencing; read alongside Redis's official response/disclaimer.

## 10. RELATED TOPICS BRIDGE

### Before

1. **PostgreSQL Modeling.** The authoritative schema and version determine what a derived entry represents.
2. **Indexes and Query Plans.** Optimize and capacity-test the source before masking it with cache.
3. **Transactions and Locking.** Cache invalidation is outside the database transaction; idempotency and ordering address the gap.

### After

1. **Data Migrations.** Key/schema versions and rolling compatibility keep cached encodings safe during deployment.
2. **Distributed Consistency.** Replication, leases and stale reads connect to quorums, consensus and fencing.
3. **Kafka and Messaging.** Durable change streams repair/drive invalidation more reliably than Pub/Sub notifications.
4. **SRE/Observability.** Hit/miss segmentation, hot keys, memory, evictions and fallback load require SLOs and runbooks.

---ANSWER KEY BELOW---

1. Miss fraction 0.025; source `25000×0.025=625/s`. Mean `0.6 + 0.025×14 = 0.95 ms`, excluding client/queue/serialization and tail effects.
2. DB commit succeeds; process/network fails before Redis delete; old cache remains. An outbox in the commit emits versioned invalidation until acknowledged, while TTL limits residual duration if consumer is unavailable; monitor invalidation lag.
3. Use source-versioned values, TTL around the permitted 10 seconds with jitter (for example 7–10 seconds only if source/update timing proves bound), durable update invalidation, per-key single-flight and stale serving no later than the explicit 10-second safety deadline. Load-test synchronized minute updates.
4. Volatile eviction risks write failures if only non-expiring keys remain and mixes reconstructible with coordination state. Separate instances/policies: pure cache with allkeys-LRU/LFU selected by trace and coordination store with explicit durability/noeviction/capacity—or move coordination to appropriate durable system.
5. Both clients can read 10 and write 11, losing one. Use `INCR`/`INCRBY`, or `WATCH` plus `MULTI/EXEC` retry; a bounded Lua script is another option.
6. Key `eligibility:v3:{opaqueTenant}:{opaquePatient}:{policyVersion}` with authorization before lookup; value includes source generation, decision, evaluated-at/expires-at and no unnecessary PHI. Atomic compare prevents lower generation replacing higher; durable invalidation and fail-closed policy handle revocation.
7. Redis docs state WAIT confirms replica acknowledgements but failover/persistence can still lose writes; it does not make CP. For security quota choose deny or conservative local emergency budget on uncertainty, or use a stronger authoritative service—explicitly product-approved.
8. Keep one in-flight future per key; followers wait only to deadline. Fresh returns immediately; stale-safe window serves old while leader refreshes; loader error clears flight and serves stale only within policy, otherwise fails/load-sheds. Bound waiters and emit metrics.
9. A cautious arithmetic start is at most `32-4-3=25 GiB`, with additional OS/safety reserve likely making maxmemory lower (for example 22–24 GiB). Measure peak excluded buffers, allocator RSS, client buffers, fork/persistence behavior and container limit before finalizing.
10. Storage remembers maximum 45. Owner 44 resumes after its lease and sends a write tagged 44; storage rejects `44<45`. Owner 45's operations may proceed. Enforcement by the protected resource—not merely lock service—provides stale-owner safety.
