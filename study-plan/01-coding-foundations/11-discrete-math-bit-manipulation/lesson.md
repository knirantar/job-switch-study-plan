# Discrete Mathematics and Bit Manipulation from Scratch

Parent subject: `01-coding-foundations`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why software engineers need discrete mathematics

Software works with distinct states: a request is authorized or denied, a bit is zero or one, a graph contains a path or does not, and a collection contains an integer number of records. **Discrete mathematics** studies such countable structures. It supplies the language behind conditions, sets, functions, graphs, probability, modular arithmetic, and algorithm proofs.

This lesson is not an abstract mathematics detour. It explains why a binary search over a million items takes about 20 steps, why `(hash & (capacity-1))` works only for power-of-two capacity, why XOR can identify an unpaired value, why `a && (b || c)` cannot be casually rearranged, and why integer overflow invalidates seemingly obvious formulas.

### Propositions and logic

A **proposition** is a statement that is either true or false. Logical negation `¬P` reverses truth; conjunction `P ∧ Q` requires both; disjunction `P ∨ Q` requires at least one; implication `P → Q` is false only when P is true and Q is false.

In code, `&&`, `||`, and `!` approximate these operations, with the additional operational fact that Java short-circuits evaluation. De Morgan's laws are essential:

- `!(P && Q)` equals `!P || !Q`.
- `!(P || Q)` equals `!P && !Q`.

If access requires `verified && !frozen`, denial is `!verified || frozen`. Writing `!verified && frozen` denies only accounts that satisfy both, creating an authorization vulnerability.

### Sets, mappings, and counting

A **set** is a collection of distinct elements. A **subset** contains only elements from another set. **Union** combines elements; **intersection** retains common elements; **difference** removes members. A **Cartesian product** pairs every element of one set with every element of another.

A **function** maps every element in a domain to exactly one value in a codomain. An **injective** mapping never maps different inputs to the same output; a **surjective** mapping reaches every codomain value; a **bijection** is both. Hash functions are not injective over arbitrary keys because a finite hash range cannot uniquely encode infinitely many possible inputs. The **pigeonhole principle** guarantees collisions.

Counting rules quantify possibilities. If a four-digit PIN allows 10 digits independently, there are `10^4 = 10,000` combinations. If repetition is forbidden, there are `10×9×8×7 = 5,040`. A subset of n independent flags has `2^n` possible combinations. This explains why brute-force enumeration becomes infeasible quickly: 50 boolean choices yield `2^50 ≈ 1.126 quadrillion` subsets.

### Powers, logarithms, and growth

Exponentiation repeats multiplication. `2^10=1024`; `2^20=1,048,576`; `2^30≈1.074 billion`. A logarithm asks for the exponent: `log₂(1,048,576)=20`. Algorithms that halve input each step take logarithmic steps. Algorithms that enumerate subsets take exponential steps.

Logarithm bases differ only by a constant factor in asymptotic analysis, but exact capacity calculations need a base. A balanced binary tree with height h holds at most `2^(h+1)-1` nodes when root height is zero.

### Integers, divisibility, and modular arithmetic

Integer `a` divides `b` if `b = ak` for some integer k. A **prime** has exactly two positive divisors, 1 and itself. The **greatest common divisor** (GCD) is the largest positive integer dividing both numbers.

Modular arithmetic treats numbers with the same remainder as congruent. `17 mod 5 = 2`, so 17 is congruent to 2 modulo 5. It powers circular buffers, sharding, clocks, checksums, and cryptography. Java's `%` is remainder, and negative operands can produce negative results: `-1 % 8 == -1`. Use `Math.floorMod(-1,8) == 7` when a non-negative modular index is required.

### Binary representation

A **bit** is a binary digit. Eight bits form a byte. In positional binary, bit position k has weight `2^k`. Decimal 13 is binary `1101` because `8+4+1=13`.

Java signed integers use **two's-complement** representation. An `int` has 32 bits; its highest bit carries negative sign semantics, giving range `-2^31` through `2^31-1`. Negation is conceptually invert bits and add one. `-1` is all ones.

Bit operators work position by position:

- AND `&`: one only when both bits are one.
- OR `|`: one when either bit is one.
- XOR `^`: one when bits differ.
- NOT `~`: invert every bit.
- left shift `<<`: shift left, filling zeros.
- signed right shift `>>`: preserve sign.
- unsigned right shift `>>>`: fill zeros.

Bit manipulation is appropriate for compact flags, protocols, hashing, encoding, and certain algorithm problems. It is not automatically faster or clearer than named fields.

### Proof methods

A **counterexample** disproves a universal claim. “Every prime is odd” is disproved by 2. **Direct proof** derives a conclusion from assumptions. **Proof by contradiction** assumes the opposite and derives impossibility. **Mathematical induction** proves a base case and an inductive step. Loop invariants are an operational form of induction.

Senior interviews value proof habits more than formal notation: state what remains true, show progress, cover boundaries, and give a counterexample to an unsafe shortcut.

## 2. CORE MECHANICS

### 2.1 Truth tables and authorization rules

Suppose a request is allowed when `(employee OR contractedClinician) AND consentActive`.

| employee | contractor | consent | allowed |
|---|---|---|---|
| false | false | true | false |
| true | false | true | true |
| false | true | true | true |
| true | false | false | false |

Parentheses are part of the policy. `employee || contractor && consent` uses Java precedence as `employee || (contractor && consent)`, accidentally allowing employees without consent. Encode policy with named predicates and tests for every meaningful row.

### 2.2 Set operations in code

Given entitlements `A={READ,EXPORT}` and resource permissions `B={READ,WRITE}`, intersection is `{READ}`, union is `{READ,EXPORT,WRITE}`, and A−B is `{EXPORT}`. A request requiring `{READ,WRITE}` is allowed only if the granted set is a superset.

Java's `EnumSet` compactly represents enum members and supports `retainAll`, `addAll`, and `removeAll`. Avoid mutating the original when computing a derived set unless the contract permits it.

### 2.3 Counting and the pigeonhole principle

With 1,000,001 records assigned to 1,000 shards, some shard receives at least `ceil(1,000,001/1,000)=1,001` records. This does not prove distribution is balanced; it proves a minimum worst bucket occupancy.

For a 32-bit hash, there are `2^32` outputs. Collisions become likely far before 4.29 billion items because of the birthday effect: around `sqrt(2^32)=65,536` randomly hashed items gives a substantial collision probability. Therefore hash equality is never proof of key equality.

### 2.4 GCD and modular cycles

Euclid's algorithm uses `gcd(a,b)=gcd(b,a mod b)`:

`gcd(252,105)` → `gcd(105,42)` → `gcd(42,21)` → `gcd(21,0)` = 21.

A circular buffer of capacity 8 advances index with `(index+1) % 8` or, because 8 is a power of two, `(index+1) & 7`. The mask shortcut is invalid for capacity 10. Use `%`/`floorMod` unless the power-of-two invariant is explicit and tested.

### 2.5 Converting binary and testing bits

Decimal 45 decomposes into 32+8+4+1, so binary is `101101`. To test bit k: `(value & (1 << k)) != 0`. For 45 and k=3, mask 8, result 8: set. To set it: `value | mask`; clear it: `value & ~mask`; toggle it: `value ^ mask`.

Use `1L << k` for a long bitset. `1 << 40` does not shift an int by 40 as a novice expects; Java masks int shift distance to five bits, effectively shifting by 8.

### 2.6 XOR properties

XOR is associative and commutative; `x^x=0`; `x^0=x`. If every integer appears twice except one, XORing all values leaves the unique value. For `[42,17,9,17,9]`, pairs cancel and result is 42.

This requires the exact multiplicity assumption. If values can appear three times, or two values are unique, the method needs modification. XOR does not “remove duplicates” generally.

### 2.7 Power of two and bit count

A positive power of two has one set bit. Subtracting one turns that bit off and all lower bits on. Thus `n > 0 && (n & (n-1)) == 0` tests powers of two. For 16 (`10000`), 15 is `01111`, AND is zero. Zero must be excluded because it also yields zero.

Brian Kernighan's bit-count loop repeatedly clears the lowest set bit: `n &= n-1`. For 44 (`101100`), it produces `101000`, `100000`, `000000`: three iterations, one per set bit.

### 2.8 Signed shifts and overflow

For `-8`, `-8 >> 1` is `-4` because sign bits are filled. `-8 >>> 1` becomes a large positive int because a zero enters the high bit. Shifts are not a universally safe replacement for division: signed rounding behavior differs for negative odd values.

Left shift can discard high bits silently. `1 << 31` is `Integer.MIN_VALUE`, not positive 2,147,483,648. Promote to long: `1L << 31`.

### 2.9 Probability basics for engineering

Probability ranges from 0 to 1. For independent events A and B, `P(A and B)=P(A)P(B)`. If each zone independently fails with probability 0.001 over a period, simultaneous failure probability is 0.000001 under that strong independence assumption. Shared power, networking, deployment, and software defects violate independence, so multiplying probabilities without checking correlation can dangerously overstate resilience.

Expected value is a weighted average. If 1% of requests cost 500 ms and 99% cost 10 ms, mean latency is `0.01×500 + 0.99×10 = 14.9 ms`, which hides the 500 ms tail. Percentiles are needed for user experience.

## 3. WORKED PROBLEMS

### Problem 1 — De Morgan's law (easy)

Negate “token valid AND scope present.”

**Solution.** `!(valid && scope)` equals `!valid || !scope`. A request is denied if either condition is missing. `!valid && !scope` is too weak because it denies only when both fail.

**Trap:** changing AND to AND during negation.

### Problem 2 — Capacity halvings (easy)

How many halvings reduce 1,048,576 candidates to one?

**Solution.** Since 1,048,576 is `2^20`, exactly 20 halvings. This is the operational meaning of `log₂ n`.

**Trap:** using natural log as the exact number of halvings.

### Problem 3 — Circular retry slot (easy)

Map attempt −1 into an eight-slot array.

**Solution.** Java `-1 % 8` is −1, an invalid index. `Math.floorMod(-1,8)` returns 7. If inputs are known non-negative, ordinary remainder suffices.

**Trap:** assuming Java remainder is always non-negative.

### Problem 4 — Permission intersection (medium)

User has `{READ,EXPORT}`; resource allows `{READ,WRITE}`; action requires `{READ}`. Decide access and derive effective permissions.

**Solution.** Effective permissions are intersection `{READ}`. Required set is a subset of effective permissions, so allow READ. Deny EXPORT even though the user claims it, because the resource does not grant it.

**Trap:** using union for effective authorization.

### Problem 5 — Unique event code (medium)

Find the unpaired code in `[503,200,429,503,429]`.

**Solution.** XOR all: equal 503 values cancel, equal 429 values cancel, zero XOR 200 is 200. Time O(n), space O(1).

**Trap:** applying the method without the “all others occur exactly twice” invariant.

### Problem 6 — Bitmask flags (medium)

Bits 0, 2, and 5 represent READ, EXPORT, and ADMIN. Encode READ+EXPORT and test ADMIN.

**Solution.** Mask is `(1<<0)|(1<<2)=1+4=5`, binary `000101`. ADMIN mask is `1<<5=32`; `5 & 32` is zero, so absent. To add ADMIN use `5|32=37`.

**Trap:** treating bit positions as their masks—for example using 5 instead of `1<<5`.

### Problem 7 — Hash collision reasoning (hard)

Can a 32-bit hash uniquely identify 10 billion events?

**Solution.** No. There are only 4,294,967,296 hash outputs, fewer than events, so pigeonhole principle guarantees collisions. Even at much lower counts collisions are probabilistically plausible. Store/compare the real key; use a cryptographic digest only according to an explicit collision-risk model, not as mathematical uniqueness.

**Trap:** confusing a well-distributed hash with an injective mapping.

### Problem 8 — Subset explosion (hard)

A placement optimizer considers every subset of 60 nodes at one microsecond per subset. How long?

**Solution.** `2^60 = 1,152,921,504,606,846,976` subsets. At one million subsets/second, seconds are about `1.153×10^12`, or about 36,558 years using 31,557,600 seconds/year. Brute force is infeasible.

**Trap:** hearing “one microsecond” and ignoring exponential count.

### Problem 9 — Independence fallacy (hard)

Two zones each have 0.1% outage probability. Is dual failure necessarily one in a million?

**Solution.** Only if failures are independent. Shared regional control planes, software releases, credentials, and dependencies create correlation. Model common-cause failures separately and test them. Multiplying marginal probabilities without independence evidence is invalid.

**Trap:** assuming distinct zones imply statistical independence.

## 4. REAL-WORLD / APPLIED CONTEXT

### Java HashMap capacity

OpenJDK's `HashMap` uses power-of-two table sizes, enabling bucket selection with a mask and spreading high hash bits. This is why the mathematical invariant “capacity is a power of two” matters. It also handles collisions by comparing keys and can treeify heavily populated bins; a hash code alone never establishes equality.

### Protocol and permission masks

Unix file permissions encode read/write/execute flags compactly. Network protocols use bit fields because wire space and fixed layouts matter. In ordinary domain code, an `EnumSet<Permission>` is often clearer and safer; bit-level representation should be encapsulated behind named operations.

### Consistent hashing and modular placement

Simple `hash(key) mod N` changes placement for most keys when N changes. Consistent hashing maps keys and nodes onto a ring to reduce movement during membership changes. Both rely on modular/circular reasoning, but the distributed algorithm adds virtual nodes, balance, and replication considerations.

## 5. COMPARISON TABLE

| Technique | Exact property | Typical cost | Use | Main hazard |
|---|---|---:|---|---|
| Boolean fields | Named independent states | Usually bytes/object overhead | Domain readability | Many fields and serialization overhead |
| Bitmask | Up to 32 flags in `int`, 64 in `long` | O(1) bit ops | Protocols/compact flags | Magic numbers, limited width |
| `EnumSet` | Type-safe enum set, bit-vector implementation | O(1) common operations | Java domain permissions | Mutable unless copied/wrapped |
| `% capacity` | General remainder | O(1) | Circular index for any positive capacity | Negative result for negative dividend |
| `floorMod` | Non-negative modulo for positive modulus | O(1) | Negative-capable circular indexes | Slightly more explicit cost/intent |
| `& (capacity-1)` | Modulo only for non-negative/power-of-two context | O(1) | Proven power-of-two hot path | Wrong for other capacities |
| exhaustive subsets | Examines all `2^n` choices | Exponential | Small n / proof baseline | Explodes: n=60 is ~1.15e18 |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Negating without De Morgan.** The authorization rule becomes too permissive.
2. **Confusing XOR and exponentiation.** In Java, `2 ^ 10` is bitwise XOR (8), not 1024.
3. **Using `%` as mathematical modulo for negatives.** Use `floorMod` for non-negative indices.
4. **Power-of-two test accepts zero.** Include `n > 0`.
5. **Shifting an int for a long mask.** Use `1L << bit` for bits above 31.
6. **Assuming hash means unique.** Collisions are unavoidable in a finite hash space.
7. **Assuming independent failures.** Shared dependencies introduce correlation.
8. **Using bit tricks without a contract.** XOR uniqueness requires exact multiplicities.
9. **Forgetting overflow.** Powers and counts exceed 32-bit ranges quickly.
10. **Premature bitmasking.** Clear named types often outperform cleverness in maintainability.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- De Morgan: `!(A&&B)=!A||!B`; `!(A||B)=!A&&!B`.
- `2^10=1024`, `2^20≈1.05M`, `2^30≈1.07B`.
- Halving repeatedly → log₂n; enumerating subsets → 2ⁿ.
- Java `%` can be negative; `floorMod` gives non-negative result for positive modulus.
- Set/test/clear/toggle bit k: `x|mask`, `x&mask`, `x&~mask`, `x^mask`.
- XOR: `x^x=0`, `x^0=x`.
- Power of two: `n>0 && (n&(n-1))==0`.
- `>>` sign-fills; `>>>` zero-fills.
- Hash equality does not imply key equality.
- Probability multiplication requires independence.

## 8. PRACTICE SET FOR SELF-TEST

1. Negate `isInternal || hasSignedConsent`.
2. Convert decimal 58 to binary.
3. Convert binary `101011` to decimal.
4. Compute `floorMod(-17, 8)`.
5. Determine whether 64 and 70 are powers of two using the bit test.
6. Count set bits in decimal 58.
7. How many subsets exist for 25 feature flags?
8. At least how many items occupy one bucket when 10,003 items enter 100 buckets?
9. Explain why `(hash & 9)` is not equivalent to `hash % 10`.
10. A 1% event costs ₹10,000 and a 99% event costs ₹20. Compute expected cost, then explain what it does not tell you.

## 9. CURATED RESOURCES

- Kenneth Rosen, *Discrete Mathematics and Its Applications*, 8th ed., Chapters 1, 2, 4, 5, 6, and 8 — logic, sets, number theory, induction, counting, and recurrence foundations.
- Susanna S. Epp, *Discrete Mathematics with Applications*, 5th ed., Chapters 1–5 — especially accessible proof and counterexample development.
- Henry S. Warren Jr., *Hacker's Delight*, 2nd ed., Chapters 2 and 5 — canonical bit identities, population count, and boundary-aware implementation.
- Java Language Specification, Java SE 21, Sections 4.2.1, 15.19, 15.22, and 15.23–24 — authoritative integer ranges, shifts, bitwise, and short-circuit semantics.
- Java SE API docs for `Math.floorMod`, `Integer.bitCount`, and `EnumSet` — production-safe library semantics.
- Thomas H. Cormen et al., *Introduction to Algorithms*, 4th ed., Chapters 3 and 30.3 — growth functions and modular arithmetic in algorithmic context.
- OpenJDK `java.util.HashMap` source and class documentation — real power-of-two capacity, collision, equality, and tree-bin behavior.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Programming Logic and Debugging:** provides expressions, types, tests, and overflow awareness.
2. **Recursion, Searching, and Sorting:** motivates logarithms, induction, powers of two, and order.

### After

1. **Complexity Analysis:** turns growth functions and counting into asymptotic bounds.
2. **Hashing and Sets:** applies set algebra, finite hash ranges, and collision reasoning.
3. **Trees, Heaps, and Tries:** uses binary representation, logarithmic height, and induction.
4. **Graphs:** extends discrete relations and set operations to connectivity.
5. **Java Concurrency Basics:** uses boolean logic and bit/atomic state while adding memory-order constraints.

---ANSWER KEY BELOW---

1. `!isInternal && !hasSignedConsent`.
2. `111010` (32+16+8+2).
3. 43.
4. 7.
5. 64: yes; 70: no.
6. Four.
7. `2^25 = 33,554,432`.
8. `ceil(10,003/100)=101`.
9. Masking implements modulo only with mask `2^k-1`; 9 (`1001`) selects two non-contiguous bits.
10. `0.01×10000 + 0.99×20 = ₹119.80`; it does not describe tail loss, variance, correlation, or risk tolerance.
