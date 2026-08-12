import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Objects;

public final class BuildTestingDebuggingLab {
    static final class ClaimService {
        private final Clock clock;
        ClaimService(Clock clock) { this.clock = Objects.requireNonNull(clock); }
        boolean expired(Instant deadline) { return !Instant.now(clock).isBefore(deadline); }
        int retryDelayMillis(int attempt) {
            if (attempt < 0 || attempt > 10) throw new IllegalArgumentException("attempt 0..10");
            return Math.multiplyExact(100, 1 << attempt);
        }
    }

    public static void main(String[] args) {
        Clock fixed = Clock.fixed(Instant.parse("2026-08-12T10:00:00Z"), ZoneOffset.UTC);
        ClaimService service = new ClaimService(fixed);
        equal(false, service.expired(Instant.parse("2026-08-12T10:00:01Z")), "future deadline");
        equal(true, service.expired(Instant.parse("2026-08-12T10:00:00Z")), "inclusive expiry boundary");
        equal(800, service.retryDelayMillis(3), "backoff");
        expect(IllegalArgumentException.class, () -> service.retryDelayMillis(11), "invalid attempt");
        System.out.println("4 deterministic tests passed.");
    }

    static void equal(Object expected, Object actual, String name) {
        if (!Objects.equals(expected, actual)) throw new AssertionError(name + ": expected=" + expected + " actual=" + actual);
    }
    static void expect(Class<? extends Throwable> type, Runnable action, String name) {
        try { action.run(); }
        catch (Throwable error) { if (type.isInstance(error)) return; throw new AssertionError(name + ": wrong exception", error); }
        throw new AssertionError(name + ": exception missing");
    }
}
