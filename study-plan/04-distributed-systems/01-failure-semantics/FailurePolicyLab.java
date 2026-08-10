import java.util.Set;

public final class FailurePolicyLab {
  enum State { CLOSED, OPEN, HALF_OPEN }
  record Budget(long totalMs, long elapsedMs, long reserveMs) {
    long remainingMs() { return Math.max(0, totalMs - elapsedMs - reserveMs); }
  }

  static long maxLeafAttempts(int attemptsPerLayer, int retryingLayers) {
    if (attemptsPerLayer < 1 || retryingLayers < 0) throw new IllegalArgumentException();
    long result = 1;
    for (int i=0; i<retryingLayers; i++) result = Math.multiplyExact(result, attemptsPerLayer);
    return result;
  }

  // Full jitter in [0, cap], with deterministic randomUnit in [0,1] for tests.
  static long fullJitterMs(int retry, long baseMs, long maximumMs, double randomUnit) {
    if (retry < 0 || baseMs <= 0 || maximumMs < baseMs || randomUnit < 0 || randomUnit > 1)
      throw new IllegalArgumentException();
    long exponential = baseMs << Math.min(retry, 20);
    long cap = Math.min(maximumMs, exponential);
    return (long)Math.floor(randomUnit * (cap + 1));
  }

  static boolean retryable(String method, int status, boolean hasIdempotencyKey) {
    boolean safeMethod = Set.of("GET", "HEAD", "OPTIONS").contains(method);
    boolean transientStatus = status == 429 || status == 502 || status == 503 || status == 504;
    return transientStatus && (safeMethod || hasIdempotencyKey);
  }

  static State after(State state, boolean success, int consecutiveFailures,
                     int threshold, boolean openIntervalElapsed) {
    if (state == State.OPEN) return openIntervalElapsed ? State.HALF_OPEN : State.OPEN;
    if (state == State.HALF_OPEN) return success ? State.CLOSED : State.OPEN;
    return !success && consecutiveFailures >= threshold ? State.OPEN : State.CLOSED;
  }

  public static void main(String[] args) {
    if (new Budget(800, 215, 85).remainingMs() != 500) throw new AssertionError();
    if (maxLeafAttempts(4, 3) != 64) throw new AssertionError();
    if (fullJitterMs(3, 25, 1000, 0.5) != 100) throw new AssertionError();
    if (!retryable("GET", 503, false) || retryable("POST", 503, false)
        || !retryable("POST", 503, true) || retryable("GET", 400, false)) throw new AssertionError();
    if (after(State.CLOSED, false, 5, 5, false) != State.OPEN) throw new AssertionError();
    if (after(State.OPEN, false, 5, 5, true) != State.HALF_OPEN) throw new AssertionError();
    if (after(State.HALF_OPEN, true, 0, 5, false) != State.CLOSED) throw new AssertionError();
    System.out.println("Deadline, retry, jitter, and breaker checks passed.");
  }
}
