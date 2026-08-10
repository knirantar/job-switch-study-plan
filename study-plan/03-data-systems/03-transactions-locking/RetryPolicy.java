import java.time.Duration;
import java.util.Set;
import java.util.function.LongUnaryOperator;

public final class RetryPolicy {
  private static final Set<String> RETRYABLE = Set.of("40001", "40P01");

  static boolean retryable(String sqlState) { return RETRYABLE.contains(sqlState); }

  // Exponential cap plus deterministic "jitter" input for a testable example.
  static long delayMillis(int attempt, long jitterMillis) {
    if (attempt < 1 || jitterMillis < 0) throw new IllegalArgumentException();
    long exponential = 25L << Math.min(attempt - 1, 6); // 25..1600 ms
    return Math.min(2000, exponential) + Math.min(jitterMillis, 24);
  }

  static long execute(int maxAttempts, LongUnaryOperator transaction) {
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
      long result = transaction.applyAsLong(attempt);
      if (result >= 0) return result;
    }
    throw new IllegalStateException("retry budget exhausted");
  }

  public static void main(String[] args) {
    if (!retryable("40001") || !retryable("40P01") || retryable("23505"))
      throw new AssertionError("SQLSTATE classification");
    if (delayMillis(1, 7) != 32 || delayMillis(8, 100) != 1624)
      throw new AssertionError("backoff");
    long value = execute(4, attempt -> attempt < 3 ? -1 : 42);
    if (value != 42) throw new AssertionError("whole-unit retry");
    System.out.println("Retry policy checks passed.");
  }
}
