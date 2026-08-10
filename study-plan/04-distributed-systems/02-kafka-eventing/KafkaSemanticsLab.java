import java.nio.charset.StandardCharsets;
import java.util.*;

public final class KafkaSemanticsLab {
  record Event(String id, String aggregateId, long version, int bytes) {}

  static int partition(String key, int partitions) {
    if (partitions <= 0) throw new IllegalArgumentException();
    // Stable educational hash, not Kafka's production partitioner implementation.
    int h = 0;
    for (byte b : key.getBytes(StandardCharsets.UTF_8)) h = 31 * h + Byte.toUnsignedInt(b);
    return Math.floorMod(h, partitions);
  }

  static long backlog(long arrivalPerSecond, long servicePerSecond, long seconds) {
    return Math.max(0, Math.multiplyExact(arrivalPerSecond - servicePerSecond, seconds));
  }

  static long retentionBytes(long eventsPerSecond, long averageBytes, long seconds,
                             int replicationFactor, double overheadFactor) {
    double raw = (double)eventsPerSecond * averageBytes * seconds * replicationFactor * overheadFactor;
    if (raw > Long.MAX_VALUE) throw new ArithmeticException();
    return (long)Math.ceil(raw);
  }

  static final class IdempotentSink {
    private final Set<String> appliedIds = new HashSet<>();
    private final Map<String, Long> versions = new HashMap<>();
    boolean apply(Event e) {
      if (!appliedIds.add(e.id)) return false;
      long current = versions.getOrDefault(e.aggregateId, 0L);
      if (e.version != current + 1) {
        appliedIds.remove(e.id); // quarantine/retry; don't mark applied
        return false;
      }
      versions.put(e.aggregateId, e.version);
      return true;
    }
  }

  public static void main(String[] args) {
    if (partition("payment-42", 12) != partition("payment-42", 12)) throw new AssertionError();
    if (backlog(2_000, 1_500, 3_600) != 1_800_000) throw new AssertionError();
    long bytes = retentionBytes(10_000, 800, 86_400, 3, 1.20);
    if (bytes != 2_488_320_000_000L) throw new AssertionError(bytes);
    IdempotentSink sink = new IdempotentSink();
    Event v1 = new Event("e1", "p7", 1, 500);
    if (!sink.apply(v1) || sink.apply(v1)) throw new AssertionError("duplicate");
    if (sink.apply(new Event("e3", "p7", 3, 500))) throw new AssertionError("gap");
    if (!sink.apply(new Event("e2", "p7", 2, 500))) throw new AssertionError("v2");
    System.out.println("Partition, capacity, dedupe, and sequence checks passed.");
  }
}
