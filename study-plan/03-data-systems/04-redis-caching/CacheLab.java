import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

public final class CacheLab {
  record Entry(String value, long expiresAt, long sourceVersion) {}
  static final class Cache {
    private final Map<String, Entry> data = new ConcurrentHashMap<>();
    Optional<String> get(String key, long now) {
      Entry e = data.get(key);
      if (e == null) return Optional.empty();
      if (e.expiresAt <= now) { data.remove(key, e); return Optional.empty(); }
      return Optional.of(e.value);
    }
    void put(String key, String value, long version, long now, long ttl) {
      data.compute(key, (k, old) -> old != null && old.sourceVersion > version
          ? old : new Entry(value, Math.addExact(now, ttl), version));
    }
    void invalidate(String key) { data.remove(key); }
  }

  // Stable pseudo-random jitter in [0, spread], useful for deterministic tests.
  static long ttlWithJitter(long base, long spread, String key) {
    if (base <= 0 || spread < 0) throw new IllegalArgumentException();
    return base + Math.floorMod(key.hashCode(), spread + 1);
  }

  public static void main(String[] args) {
    Cache cache = new Cache();
    cache.put("patient:42", "v1", 1, 1_000, 100);
    if (!cache.get("patient:42", 1_099).orElseThrow().equals("v1")) throw new AssertionError();
    if (cache.get("patient:42", 1_100).isPresent()) throw new AssertionError("expiry boundary");
    cache.put("model:m1", "new", 9, 2_000, 100);
    cache.put("model:m1", "stale", 8, 2_001, 100); // late fill cannot regress version
    if (!cache.get("model:m1", 2_050).orElseThrow().equals("new")) throw new AssertionError();
    long ttl = ttlWithJitter(300, 60, "tenant:42");
    if (ttl < 300 || ttl > 360) throw new AssertionError();
    System.out.println("TTL boundary, jitter, and version-order checks passed.");
  }
}
