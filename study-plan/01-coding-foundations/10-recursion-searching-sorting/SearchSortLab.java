import java.util.Arrays;

/** Run: javac SearchSortLab.java && java -ea SearchSortLab */
public final class SearchSortLab {
    static int binarySearch(long[] a, long target) {
        int low = 0, high = a.length - 1;
        while (low <= high) {
            int mid = low + (high - low) / 2;
            if (a[mid] < target) low = mid + 1;
            else if (a[mid] > target) high = mid - 1;
            else return mid;
        }
        return -1;
    }

    static int lowerBound(int[] a, int target) {
        int low = 0, high = a.length;
        while (low < high) {
            int mid = low + (high - low) / 2;
            if (a[mid] < target) low = mid + 1;
            else high = mid;
        }
        return low;
    }

    static void stableInsertionSort(Record[] a) {
        for (int i = 1; i < a.length; i++) {
            Record current = a[i];
            int j = i - 1;
            while (j >= 0 && a[j].key() > current.key()) {
                a[j + 1] = a[j--];
            }
            a[j + 1] = current;
        }
    }

    static long factorial(int n) {
        if (n < 0) throw new IllegalArgumentException();
        if (n <= 1) return 1;
        return Math.multiplyExact(n, factorial(n - 1));
    }

    record Record(String id, int key) {}

    public static void main(String[] args) {
        long[] sorted = {4, 11, 19, 28, 37, 49, 63, 78};
        assert binarySearch(sorted, 49) == 5;
        assert binarySearch(sorted, 50) == -1;
        assert binarySearch(new long[0], 1) == -1;
        assert lowerBound(new int[]{2, 5, 5, 5, 9}, 5) == 1;
        assert lowerBound(new int[]{2, 5, 5, 5, 9}, 7) == 4;
        assert lowerBound(new int[]{2, 5, 5, 5, 9}, 10) == 5;
        Record[] records = {new Record("A", 3), new Record("B", 1),
                new Record("C", 3), new Record("D", 2)};
        stableInsertionSort(records);
        assert Arrays.stream(records).map(Record::id).toList().equals(
                java.util.List.of("B", "D", "A", "C"));
        assert factorial(20) == 2_432_902_008_176_640_000L;
        expect(ArithmeticException.class, () -> factorial(21));
        System.out.println("PASS: search, bounds, stable sort, recursion, overflow");
    }

    static void expect(Class<? extends Throwable> type, Runnable action) {
        try { action.run(); throw new AssertionError("expected " + type); }
        catch (Throwable actual) { if (!type.isInstance(actual)) throw actual; }
    }
}
