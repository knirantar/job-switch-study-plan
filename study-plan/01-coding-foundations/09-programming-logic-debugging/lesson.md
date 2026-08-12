# Programming Logic and Debugging from Scratch

Parent subject: `01-coding-foundations`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### What a program really is

A program is a precise sequence of instructions that transforms input and state into output and new state. That sounds elementary, but it explains most interview failures: a candidate begins writing Java before deciding exactly what information exists, what must change, and what must remain true.

Consider a payment API receiving three settled amounts in paise: `129900`, `49900`, and `25000`. Its job is to compute the total. The **input** is the sequence of integers; the **output** is `204800`; the changing **state** is a running total. An **algorithm** is the language-independent recipe. Source code is one encoding of that recipe.

Early computers were programmed by wiring hardware or entering machine instructions. Assembly languages attached names to machine operations, and higher-level languages made control flow and data representation readable by people. The enduring motivation is abstraction: humans should reason about “add this transaction to the total,” not processor opcodes. Without a precise algorithm, however, a higher-level language merely lets us express ambiguity faster.

### Values, types, variables, expressions, and statements

A **value** is a piece of data such as `42`, `true`, or `"paid"`. A **type** defines a set of possible values and permitted operations. Java's `int` is a signed 32-bit integer ranging from −2,147,483,648 to 2,147,483,647. `long` is signed 64-bit. `boolean` holds `true` or `false`. A **variable** is a named storage location whose current value may change. An **expression** produces a value: `pricePaise * quantity` is an expression. A **statement** performs an action: `total += amount;` is a statement.

Types prevent nonsensical operations and make representation limits visible. A daily payment total may overflow `int`: 100,000 payments of ₹50,000 equal 500,000,000,000 paise, far above `int`. Use `long` for counts and integral minor currency units; use `BigDecimal` when decimal arithmetic and specified rounding are required. Binary floating-point `double` cannot exactly represent most decimal fractions, so it is a poor default for money.

### Control flow

By default, statements execute from top to bottom. A **branch** chooses a path using a condition. A **loop** repeats a block. A **function** or Java method names a reusable transformation and creates a boundary with parameters, a result, and local state.

Every branch and loop should be derived from a requirement. “Reject an empty batch” becomes a precondition check. “Process each transaction exactly once” becomes an iteration invariant plus deduplication. Code without explicit conditions tends to mishandle boundaries: empty input, one element, the maximum value, duplicates, and invalid data.

### Problem decomposition and contracts

**Decomposition** splits a large responsibility into smaller ones. A reconciliation job might: parse records, validate fields, normalize identifiers, calculate totals, compare ledgers, and report mismatches. Each part can become a method with a **contract**: preconditions the caller must satisfy, postconditions guaranteed on success, and defined failure behavior.

For `sumNonNegative(long[] amounts)`, a reasonable contract is: the array reference must not be null; each amount must be non-negative; the exact mathematical sum must fit in a `long`; on success the method returns that sum; invalid input causes `IllegalArgumentException`; arithmetic overflow causes `ArithmeticException`. The contract removes guesswork for both implementation and testing.

### Correctness: invariants and traces

An **invariant** is a statement that remains true at a defined point. For a running sum loop, before iteration `i`, `total` equals the sum of elements at indices `0` through `i-1`. It is true initially because the empty prefix sums to zero. Processing `amounts[i]` preserves it. When `i == amounts.length`, it proves that `total` is the full sum.

A **trace** is a table of state over time. For `[129900, 49900, 25000]`:

| Before index | Current value | Total before | Total after |
|---:|---:|---:|---:|
| 0 | 129900 | 0 | 129900 |
| 1 | 49900 | 129900 | 179800 |
| 2 | 25000 | 179800 | 204800 |

Tracing exposes off-by-one errors and mistaken update order. In an interview, a 20-second trace is often more convincing than “I think it works.”

### Errors and debugging

A **compile-time error** violates language rules, such as assigning a `String` to an `int`. A **runtime exception** occurs during execution, such as indexing beyond an array. A **logic error** produces a valid but wrong result. A **failure** is externally observable incorrect behavior; its cause may be code, configuration, data, load, or dependency behavior.

Debugging is controlled hypothesis testing:

1. Reproduce the failure with the smallest deterministic input.
2. State expected and actual results precisely.
3. Localize the earliest point where state diverges.
4. Form one falsifiable hypothesis.
5. inspect or instrument only what tests that hypothesis.
6. Fix the cause, add a regression test, and remove accidental diagnostic noise.

Random edits are not debugging. They destroy evidence and may hide the defect.

## 2. CORE MECHANICS

### 2.1 The edit–compile–run loop

Save Java source in a file matching its public class name. The JDK compiler translates source into JVM bytecode; the `java` launcher loads and executes it.

```java
public final class InvoiceTotal {
    public static void main(String[] args) {
        long[] paise = {129_900L, 49_900L, 25_000L};
        System.out.println(sumNonNegative(paise));
    }

    static long sumNonNegative(long[] amounts) {
        if (amounts == null) throw new IllegalArgumentException("amounts is null");
        long total = 0;
        for (long amount : amounts) {
            if (amount < 0) throw new IllegalArgumentException("negative amount");
            total = Math.addExact(total, amount);
        }
        return total;
    }
}
```

Compile with `javac InvoiceTotal.java`; run with `java InvoiceTotal`. The result is `204800`. Underscores improve numeric readability and do not alter values. `L` makes the literals `long`. `Math.addExact` detects overflow rather than silently wrapping.

Boundary cases: an empty array returns zero; null is rejected; a negative amount is rejected; `{Long.MAX_VALUE, 1}` throws rather than returning `Long.MIN_VALUE`.

### 2.2 Conditions and truth tables

Boolean operators combine conditions: `&&` means both, `||` means either, and `!` negates. Java short-circuits from left to right. Therefore `user != null && user.active()` safely avoids calling a method on null.

For a transfer allowed only when KYC is verified and the account is not frozen:

| verified | frozen | `verified && !frozen` |
|---|---|---|
| false | false | false |
| false | true | false |
| true | false | true |
| true | true | false |

Be careful with De Morgan's laws: `!(A && B)` equals `!A || !B`; it does not equal `!A && !B`.

### 2.3 Loops, bounds, and termination

A loop needs initialization, a continuation condition, progress, and termination. To visit every array element once, valid indices are `0` through `length - 1`, so the condition is `i < length`.

```java
int failures = 0;
for (int i = 0; i < statusCodes.length; i++) {
    if (statusCodes[i] >= 500) failures++;
}
```

With `{200, 503, 429, 500}`, indices 0, 1, 2, 3 are visited and the answer is 2. Using `i <= length` attempts index 4 and throws. An empty array performs zero iterations. A `while` loop is preferable when progress is event-driven rather than a simple count, but its update must still guarantee termination.

### 2.4 Functions, scope, and side effects

A **pure function** depends only on arguments and changes no externally visible state. Pure transformations are easy to test. A **side effect** changes state outside the method, such as writing a database, mutating an argument, or logging.

```java
static int cappedRetryDelay(int attempt) {
    if (attempt < 0) throw new IllegalArgumentException();
    return Math.min(30_000, 250 * (1 << Math.min(attempt, 16)));
}
```

Attempts 0, 1, 2 produce 250, 500, 1000 milliseconds. The cap prevents unbounded delay. In real retry code, avoid the shift entirely for very large attempts because integer shifts have modulo behavior; a clearer production implementation uses `long`, checks the cap before multiplication, and adds jitter.

Local variables exist only within their **scope**, normally the surrounding braces. Narrow scope reduces the number of places that can change state.

### 2.5 Input validation and failure policy

Validation belongs at trust boundaries. Distinguish malformed input from a legitimate empty result. A missing patient identifier is invalid; a search with no matches is valid and should generally return an empty collection.

Fail fast when continuing would violate an invariant. Do not catch `Exception` merely to return a default: converting a database timeout into an empty list can falsely tell a clinician that no medication exists. Either handle a specific, expected failure or propagate it with context.

### 2.6 Debuggers, logs, and tests

A breakpoint pauses execution. **Step over** runs the current line, **step into** enters a called method, and **step out** completes the current method. A watch expression displays selected state. Conditional breakpoints, such as `transactionId.equals("TX-10482")`, avoid stopping for thousands of irrelevant records.

Logs should record structured identifiers, decisions, and durations—not secrets. For a payment, log a tokenized transaction ID and status, never a PAN or CVV. A regression test is lasting evidence:

```java
assert sumNonNegative(new long[]{129_900, 49_900, 25_000}) == 204_800;
try {
    sumNonNegative(new long[]{Long.MAX_VALUE, 1});
    throw new AssertionError("overflow not detected");
} catch (ArithmeticException expected) { }
```

Java assertions are disabled unless run with `-ea`; production test frameworks such as JUnit do not rely on that flag.

## 3. WORKED PROBLEMS

### Problem 1 — Count failed requests (easy)

Given HTTP status codes `[200, 201, 503, 404, 500, 429, 502]`, count server failures (`500–599`).

**Solution.** Initialize `count = 0`. Visit each value. Only 503, 500, and 502 satisfy `code >= 500 && code <= 599`, so the result is 3. The invariant is: before index `i`, count equals the number of 5xx codes in the processed prefix. Time is linear; extra space is constant.

**Trap:** counting every code `>= 400`, which includes client errors.

### Problem 2 — Safe invoice total (easy)

Sum `[4_999_900, 12_500_000, 875_000]` paise and reject negatives.

**Solution.** Validate each item before addition and use `Math.addExact`. Totals are 4,999,900; 17,499,900; 18,374,900 paise (₹183,749). Empty input returns zero by the additive identity.

**Trap:** using `int` because each individual number fits; the aggregate may not.

### Problem 3 — Classify latency (easy)

Classify 85 ms as `FAST` (≤100), `ACCEPTABLE` (101–300), or `SLOW` (>300).

**Solution.** Test boundaries in ascending order: `if (ms <= 100) FAST; else if (ms <= 300) ACCEPTABLE; else SLOW`. 85 is `FAST`; exactly 100 is also `FAST`, 101 is `ACCEPTABLE`, 300 is `ACCEPTABLE`, and 301 is `SLOW`.

**Trap:** overlapping or missing boundary values.

### Problem 4 — Validate a retry loop (medium)

The code `while (attempt <= maxAttempts) { call(); attempt++; }` starts at zero and receives `maxAttempts = 3`. How many calls occur, and how should “at most three total attempts” be expressed?

**Solution.** It calls at attempts 0, 1, 2, and 3: four calls. For three total attempts use `attempt < maxAttempts`. If the variable instead means “three retries after the first call,” four calls are correct—but rename it `maxRetries` and document the semantics.

**Trap:** confusing attempts with retries.

### Problem 5 — First divergence debugging (medium)

Expected cumulative balances for deltas `[1000, -250, -300]` are `[1000, 750, 450]`; actual values are `[1000, 1250, 1550]`. Localize the likely defect.

**Solution.** State first diverges at index 1: expected `1000 + (-250) = 750`, actual `1250` implies subtraction of the signed delta, `balance -= delta`, or use of `abs(delta)`. Inspect the single update statement and add a regression containing both signs.

**Trap:** investigating the final element first instead of the earliest divergence.

### Problem 6 — Short-circuit null safety (medium)

Why does `account != null && account.isActive()` work while `account.isActive() && account != null` can fail?

**Solution.** `&&` evaluates left to right and stops once false is known. In the first expression a null account makes the left operand false, so the method call is skipped. In the second expression the dereference occurs first and throws `NullPointerException`.

**Trap:** treating boolean algebra as if evaluation order had no runtime effects.

### Problem 7 — Overflow in capacity calculation (hard)

A service handles 75,000 events/second for 86,400 seconds. Calculate daily events safely.

**Solution.** Mathematical result: `75,000 × 86,400 = 6,480,000,000`, exceeding `int`. Write `75_000L * 86_400`, producing a `long`. If both operands were `int`, overflow would occur before assignment to a long. `long daily = 75_000 * 86_400;` is therefore wrong.

**Trap:** assuming the destination type changes the arithmetic type.

### Problem 8 — Define a medication lookup contract (hard)

Design failure semantics for `findActiveMedications(patientId)`.

**Solution.** Preconditions: non-null, syntactically valid authorized patient ID. Successful postcondition: immutable list of active medication records; no matches returns an empty list. Invalid ID causes a validation error; absent authorization causes forbidden/not-found according to enumeration policy; dependency timeout is an unavailable error, never an empty list. Audit access without recording clinical content. This preserves the distinction between “known none” and “unknown because the system failed.”

**Trap:** swallowing all exceptions and returning empty.

### Problem 9 — Prove a maximum scan (hard)

Find the maximum of `[17, 42, 9, 42, -3]` and state a loop invariant.

**Solution.** Reject empty input or represent absence explicitly. Initialize `max = 17`. Process 42 → 42; 9 → 42; 42 → 42; −3 → 42. Invariant: after processing index `i`, `max` is the largest value in indices 0 through `i`. Initialization, preservation via `max = Math.max(max, a[i])`, and termination prove correctness. Time is O(n), extra space O(1).

**Trap:** initializing max to zero, which fails for an all-negative array.

## 4. REAL-WORLD / APPLIED CONTEXT

### Money and overflow

Payment systems often store integer minor units because equality and addition are exact. Stripe's API represents many amounts as integer minor currency units; Java's exact arithmetic methods help detect range violations. At 75,000 transactions per second, even a count reaches 6.48 billion per day, demonstrating why aggregates need 64-bit representation even when per-request values fit in 32 bits.

### Kubernetes control loops

Kubernetes controllers repeatedly observe actual state and act toward desired state. Conceptually this is a loop with an invariant and idempotent action, not a one-time script. If desired replicas are 5 and observed ready replicas are 3, the controller schedules work, then observes again. This “reconciliation loop” is the same input-state-output reasoning used in elementary loops, applied to a distributed system where observations can become stale.

### Scientific debugging in production

Google's Site Reliability Engineering literature emphasizes monitoring, incident response, and blameless learning. A useful incident investigation still begins with the first known divergence, a timeline, and falsifiable hypotheses. Structured request IDs let engineers trace one failing request among millions; indiscriminate logging produces cost, privacy risk, and noise.

## 5. COMPARISON TABLE

| Technique | Cost / behavior | Use when | Avoid when |
|---|---|---|---|
| `if/else` | Evaluates selected branch | Mutually exclusive business rules | Many evolving type cases better modeled polymorphically |
| `for` loop | Explicit bounded iteration | Index or count controls progress | Termination depends on external events |
| enhanced `for` | Visits each element; hides index | Every element is needed | Index, neighbor, or in-place position is required |
| `while` | Repeats while condition holds | Attempts, parsing, state machines | Progress cannot be clearly proved |
| debugger | Exact process state; pauses execution | Reproducible local/staging defect | Pausing production or timing-sensitive concurrency |
| structured log | Historical, searchable evidence | Production paths and correlation | Secret data or per-item hot-loop noise |
| unit test | Repeatable executable claim | Stable input/output and regression | As sole evidence for cross-system behavior |
| `int` | 32-bit, about ±2.147 billion | Small bounded indices/counts | High-volume aggregates or money totals |
| `long` | 64-bit, about ±9.22 quintillion | timestamps, counters, minor units | Arbitrary precision or decimal fractions |
| `BigDecimal` | Arbitrary-precision decimal; explicit rounding | Financial decimal rules | Extremely hot approximate numerical computation |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Coding before defining the contract.** Returning `null` for both “not found” and “dependency failed” erases meaning. Define outcomes first.
2. **Using `<= length`.** For a four-element array, index 4 is invalid. Use `i < length`.
3. **Initializing a maximum to zero.** Input `[-9, -2]` incorrectly yields zero. Initialize from the first element after handling emptiness.
4. **Assuming `long x = intA * intB` is safe.** Multiplication occurs as `int`. Promote an operand: `(long) intA * intB`.
5. **Using `double` for exact currency.** `0.1 + 0.2` is not exactly `0.3` in binary floating point. Use minor units or `BigDecimal` with a rounding policy.
6. **Catching everything.** `catch (Exception) { return List.of(); }` converts unknown failure into false business truth.
7. **Changing several lines during debugging.** The apparent fix cannot identify which hypothesis was correct. Change one causal factor and retain a regression test.
8. **Logging sensitive payloads.** Debug convenience does not override privacy. Log safe identifiers, outcomes, and timings.
9. **Treating example success as proof.** One normal input says little about empty, single, duplicate, maximum, and invalid cases.

## 7. CHEAT SHEET — REVIEW ONLY

This is review only, not a substitute for the sections above.

- Start with inputs, outputs, constraints, state, failure behavior.
- Expression produces a value; statement performs an action.
- Valid array indices: `0..length-1`.
- Loop proof: initialization, invariant preservation, termination.
- Test empty, one, boundary, duplicate, invalid, and overflow cases.
- `int`: signed 32-bit; `long`: signed 64-bit.
- Promote before arithmetic; use `Math.addExact` when overflow is invalid.
- Debug: reproduce → expected/actual → first divergence → hypothesis → evidence → regression.
- Empty result and failed lookup are different outcomes.
- Never log credentials, tokens, PAN/CVV, or sensitive clinical payloads.

## 8. PRACTICE SET FOR SELF-TEST

1. Trace `total` for `[15, -4, 8, -2]` and give the invariant.
2. State the valid indices and iteration count for an array of length zero and length five.
3. Evaluate `isAdmin || isVerified && !isFrozen` for false, true, true; explain precedence.
4. Fix the overflow bug in `long bytes = 4_000_000 * 2_000;`.
5. Write a contract for `withdraw(account, amount)` including invalid and insufficient-fund cases.
6. A loop starts `i=1`, continues while `i<100`, and doubles `i`. List its values and prove termination.
7. Expected sorted count is 8, actual is 7 only when the final item matches. Identify the likely boundary defect.
8. Choose `int`, `long`, integer minor units, or `BigDecimal` for: array index, nanosecond timestamp, INR ledger posting, and compound-interest calculation rounded monthly.
9. Explain why returning an empty feature vector after a feature-store timeout can be dangerous.
10. Describe a minimal regression test for a null account in a boolean authorization expression.

## 9. CURATED RESOURCES

- Brian W. Kernighan and Dennis M. Ritchie, *The C Programming Language*, 2nd ed., Chapter 1 — canonical explanation of variables, control flow, functions, and the edit–compile loop, transferable across languages.
- Robert Sedgewick and Kevin Wayne, *Algorithms*, 4th ed., Section 1.1 “Basic Programming Model” — connects code, data types, arrays, methods, and empirical execution.
- Java Language Specification, Java SE 21, Chapters 4, 14, and 15 — authoritative type, statement, and expression semantics, including numeric promotion and short-circuiting.
- Java API docs, `java.lang.Math` (`addExact`, `multiplyExact`) — exact overflow behavior rather than folklore.
- David J. Agans, *Debugging: The 9 Indispensable Rules for Finding Even the Most Elusive Software and Hardware Problems* — a disciplined evidence-driven debugging method.
- Steve McConnell, *Code Complete*, 2nd ed., Chapters 5–8 and 22–23 — design in construction, defensive programming, control structures, and debugging.
- Google, *Site Reliability Engineering*, Chapter 12 “Effective Troubleshooting” — production-scale hypothesis formation and localization.

## 10. RELATED TOPICS BRIDGE

### Immediately before

1. **None:** this is the entry point and assumes no algorithm knowledge.
2. **Java language and object model (Parent 02):** may be studied in parallel when syntax feels unfamiliar; this lesson focuses on reasoning rather than the full Java model.

### Immediately after

1. **Recursion, Searching and Sorting:** builds control flow into foundational algorithms and introduces call-stack reasoning.
2. **Discrete Math and Bit Manipulation:** supplies boolean, modular, logarithmic, and binary tools used in analysis.
3. **Complexity Analysis:** quantifies how the algorithms introduced here grow with input size.
4. **Arrays and Strings:** applies contracts, loops, bounds, traces, and tests to the most common interview representation.

---ANSWER KEY BELOW---

1. Totals: 0 → 15 → 11 → 19 → 17; before index `i`, total equals the processed-prefix sum.
2. Length zero has no valid index and zero iterations; length five has 0–4 and five iterations.
3. `&&` binds tighter: false OR (true AND false) = false.
4. `long bytes = 4_000_000L * 2_000;`, yielding 8,000,000,000.
5. Require existing authorized account and positive representable amount; atomically debit and return receipt on sufficient funds; validation error for invalid amount, not-found/forbidden per policy, domain rejection for insufficient funds, and unavailable for dependency failure.
6. Values 1, 2, 4, 8, 16, 32, 64; doubling makes positive progress and the next value 128 fails the bound.
7. Likely `i < length - 1` instead of `i < length`, skipping the final element.
8. `int`; `long`; integer minor units (usually `long`); `BigDecimal` with explicit scale/rounding.
9. It confuses unavailable data with real zero values, producing silently incorrect model decisions.
10. Pass null and assert denial/defined validation rather than `NullPointerException`; also test active and inactive non-null accounts.
