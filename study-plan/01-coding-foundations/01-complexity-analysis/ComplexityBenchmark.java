import java.util.*;

public final class ComplexityBenchmark {
    static volatile long sink;

    static long timeLinear(int[] a, int repetitions) {
        long start = System.nanoTime();
        long sum = 0;
        for (int r = 0; r < repetitions; r++)
            for (int value : a) sum += value;
        sink = sum;
        return System.nanoTime() - start;
    }

    static long timeBinarySearch(int[] a, int repetitions) {
        long start = System.nanoTime();
        long sum = 0;
        for (int r = 0; r < repetitions; r++)
            sum += Arrays.binarySearch(a, a.length - 1);
        sink = sum;
        return System.nanoTime() - start;
    }

    static long timeQuadratic(int n) {
        long start = System.nanoTime();
        long sum = 0;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) sum += (i ^ j) & 1;
        sink = sum;
        return System.nanoTime() - start;
    }

    public static void main(String[] args) {
        for (int warm = 0; warm < 5; warm++) {
            timeLinear(java.util.stream.IntStream.range(0, 1_000_000).toArray(), 10);
            timeQuadratic(2_000);
        }
        System.out.println("JDK=" + System.getProperty("java.version") + ", OS=" + System.getProperty("os.name") + ", arch=" + System.getProperty("os.arch"));
        for (int n : new int[]{100_000, 1_000_000, 10_000_000}) {
            int[] a = java.util.stream.IntStream.range(0, n).toArray();
            long linear = timeLinear(a, 20);
            long binary = timeBinarySearch(a, 2_000_000);
            System.out.printf(Locale.ROOT, "n=%d linear-scan=%.3f ms/scan binary-search=%.1f ns/search%n",
                    n, linear / 20.0 / 1_000_000.0, binary / 2_000_000.0);
        }
        for (int n : new int[]{2_000, 4_000, 8_000}) {
            long quadratic = timeQuadratic(n);
            System.out.printf(Locale.ROOT, "n=%d quadratic=%.3f ms%n", n, quadratic / 1_000_000.0);
        }
        System.out.println("sink=" + sink);
    }
}
