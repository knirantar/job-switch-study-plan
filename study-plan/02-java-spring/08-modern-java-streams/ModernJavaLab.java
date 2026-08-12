import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.*;
import java.util.stream.Collectors;

public final class ModernJavaLab {
    record Claim(String id, String tenant, long amountPaise, boolean approved) {}

    static List<String> highValueApprovedIds(List<Claim> claims, long threshold) {
        return claims.stream()
                .filter(Claim::approved)
                .filter(claim -> claim.amountPaise() >= threshold)
                .sorted(Comparator.comparingLong(Claim::amountPaise).reversed().thenComparing(Claim::id))
                .map(Claim::id)
                .toList();
    }

    static Map<String, Long> approvedPaiseByTenant(List<Claim> claims) {
        return claims.stream().filter(Claim::approved)
                .collect(Collectors.groupingBy(Claim::tenant, TreeMap::new, Collectors.summingLong(Claim::amountPaise)));
    }

    static Optional<Claim> findById(List<Claim> claims, String id) {
        return claims.stream().filter(c -> c.id().equals(id)).findFirst();
    }

    public static void main(String[] args) {
        List<Claim> claims = List.of(
                new Claim("C1", "T1", 50_000, true),
                new Claim("C2", "T2", 800_000, true),
                new Claim("C3", "T1", 900_000, false),
                new Claim("C4", "T1", 800_000, true));
        check(highValueApprovedIds(claims, 500_000).equals(List.of("C2", "C4")), "pipeline ordering");
        check(approvedPaiseByTenant(claims).equals(Map.of("T1", 850_000L, "T2", 800_000L)), "grouping reduction");
        check(findById(claims, "missing").isEmpty(), "optional absence");
        AtomicInteger calls = new AtomicInteger();
        String value = Optional.of("cached").orElseGet(() -> { calls.incrementAndGet(); return "loaded"; });
        check(value.equals("cached") && calls.get() == 0, "lazy fallback");
        Instant event = Instant.parse("2026-08-12T04:30:00Z");
        ZonedDateTime india = event.atZone(ZoneId.of("Asia/Kolkata"));
        check(india.toLocalTime().equals(LocalTime.of(10, 0)), "timezone conversion");
        System.out.println("All modern-Java/streams checks passed.");
    }

    private static void check(boolean condition, String name) { if (!condition) throw new AssertionError(name); }
}
