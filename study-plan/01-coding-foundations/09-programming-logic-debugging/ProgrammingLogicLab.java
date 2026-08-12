import java.util.Arrays;

/** Run: javac ProgrammingLogicLab.java && java -ea ProgrammingLogicLab */
public final class ProgrammingLogicLab {
    static long sumNonNegative(long[] amounts) {
        if (amounts == null) throw new IllegalArgumentException("amounts is null");
        long total = 0;
        for (long amount : amounts) {
            if (amount < 0) throw new IllegalArgumentException("negative amount: " + amount);
            total = Math.addExact(total, amount);
        }
        return total;
    }

    static int countServerFailures(int[] codes) {
        if (codes == null) throw new IllegalArgumentException("codes is null");
        int failures = 0;
        for (int code : codes) if (code >= 500 && code <= 599) failures++;
        return failures;
    }

    static int maximum(int[] values) {
        if (values == null || values.length == 0) {
            throw new IllegalArgumentException("values must be non-empty");
        }
        int max = values[0];
        for (int i = 1; i < values.length; i++) max = Math.max(max, values[i]);
        return max;
    }

    public static void main(String[] args) {
        assert sumNonNegative(new long[]{129_900, 49_900, 25_000}) == 204_800;
        assert sumNonNegative(new long[]{}) == 0;
        assert countServerFailures(new int[]{200, 201, 503, 404, 500, 429, 502}) == 3;
        assert maximum(new int[]{17, 42, 9, 42, -3}) == 42;
        assert maximum(new int[]{-9, -2, -40}) == -2;
        expect(IllegalArgumentException.class, () -> sumNonNegative(new long[]{1, -1}));
        expect(ArithmeticException.class, () -> sumNonNegative(new long[]{Long.MAX_VALUE, 1}));
        System.out.println("PASS: " + Arrays.toString(new long[]{204_800, 0, 3, 42, -2}));
    }

    static void expect(Class<? extends Throwable> type, Runnable action) {
        try {
            action.run();
            throw new AssertionError("Expected " + type.getSimpleName());
        } catch (Throwable actual) {
            if (!type.isInstance(actual)) throw actual;
        }
    }
}
