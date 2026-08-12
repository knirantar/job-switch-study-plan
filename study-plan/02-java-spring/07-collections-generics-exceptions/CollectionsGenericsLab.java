import java.util.*;
import java.util.function.Function;

public final class CollectionsGenericsLab {
    record Claim(String id, String tenant, int priority) {}

    static <T, K> Map<K, List<T>> groupBy(List<T> values, Function<? super T, ? extends K> key) {
        Map<K, List<T>> result = new LinkedHashMap<>();
        for (T value : values) result.computeIfAbsent(key.apply(value), ignored -> new ArrayList<>()).add(value);
        return result;
    }

    static long sumNumbers(List<? extends Number> numbers) {
        long sum = 0;
        for (Number n : numbers) sum += n.longValue();
        return sum;
    }

    static void addDefaults(List<? super Integer> target) { target.add(10); target.add(20); }

    static Optional<Claim> highestPriority(List<Claim> claims) {
        return claims.stream().max(Comparator.comparingInt(Claim::priority));
    }

    static int parsePositive(String text) {
        try {
            int value = Integer.parseInt(text);
            if (value <= 0) throw new IllegalArgumentException("must be positive");
            return value;
        } catch (NumberFormatException error) {
            throw new IllegalArgumentException("not an integer: " + text, error);
        }
    }

    public static void main(String[] args) {
        List<Claim> claims = List.of(new Claim("C1", "T1", 2), new Claim("C2", "T2", 5), new Claim("C3", "T1", 3));
        check(groupBy(claims, Claim::tenant).get("T1").size() == 2, "generic grouping");
        check(sumNumbers(List.of(1, 2, 3)) == 6, "producer extends");
        List<Number> target = new ArrayList<>(); addDefaults(target);
        check(target.equals(List.of(10, 20)), "consumer super");
        check(highestPriority(claims).orElseThrow().id().equals("C2"), "comparator");
        Set<String> order = new LinkedHashSet<>(List.of("B", "A", "B"));
        check(new ArrayList<>(order).equals(List.of("B", "A")), "linked set order and uniqueness");
        Map<String, Integer> counts = new HashMap<>(); counts.merge("T1", 1, Integer::sum); counts.merge("T1", 1, Integer::sum);
        check(counts.get("T1") == 2, "map merge");
        try { parsePositive("x"); throw new AssertionError("exception expected"); }
        catch (IllegalArgumentException error) { check(error.getCause() instanceof NumberFormatException, "preserved cause"); }
        System.out.println("All collections/generics/exceptions checks passed.");
    }

    private static void check(boolean condition, String name) { if (!condition) throw new AssertionError(name); }
}
