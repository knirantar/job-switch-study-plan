# Failure-injection drills

Run these only in a local/staging system whose data and dependencies are disposable.

1. Add 350 ms latency to dependency B while the user deadline is 500 ms. Verify the
   caller propagates the remaining deadline and does not start work after expiry.
2. Return HTTP 503 for exactly 10% of 10,000 GETs. Compare no retry, one immediate
   retry, and one full-jitter retry. Record original QPS, attempt QPS, success rate,
   p50/p95/p99, in-flight count and dependency CPU.
3. Drop the response after the server commits a POST. Verify the client reports an
   unknown outcome, retries only with the same idempotency key, and obtains the same
   resource rather than creating a duplicate.
4. Restrict the dependency to 40 concurrent requests; send 400 simultaneous calls.
   Compare unbounded queueing with a 100-slot bounded queue and deadline-aware load
   shedding. Record useful completions after clients have timed out.
5. Kill 50% of replicas at 70% normal utilization. Confirm traffic does not simply
   overload survivors; exercise degradation and upstream shedding.
6. Open the circuit for one dependency, then recover it. Limit half-open probes so a
   recovering instance is not hit by the entire fleet at once.
