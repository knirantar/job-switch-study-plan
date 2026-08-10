import java.util.*;

public final class ArraysStringsLab {
    public static void moveZeroes(int[] a) {
        int write = 0;
        for (int value : a) if (value != 0) a[write++] = value;
        while (write < a.length) a[write++] = 0;
    }

    public static int[] productExceptSelf(int[] a) {
        int[] answer = new int[a.length];
        int prefix = 1;
        for (int i = 0; i < a.length; i++) {
            answer[i] = prefix;
            prefix *= a[i];
        }
        int suffix = 1;
        for (int i = a.length - 1; i >= 0; i--) {
            answer[i] *= suffix;
            suffix *= a[i];
        }
        return answer;
    }

    public static void rotateRight(int[] a, int k) {
        if (a.length == 0) return;
        k = Math.floorMod(k, a.length);
        reverse(a, 0, a.length - 1);
        reverse(a, 0, k - 1);
        reverse(a, k, a.length - 1);
    }

    private static void reverse(int[] a, int left, int right) {
        while (left < right) {
            int t = a[left]; a[left++] = a[right]; a[right--] = t;
        }
    }

    public static int longestUniqueCodePoints(String s) {
        int[] cp = s.codePoints().toArray();
        Map<Integer, Integer> last = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < cp.length; right++) {
            Integer previous = last.put(cp[right], right);
            if (previous != null) left = Math.max(left, previous + 1);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    public static List<String> summarizeRanges(long[] sorted) {
        List<String> answer = new ArrayList<>();
        for (int i = 0; i < sorted.length; ) {
            long start = sorted[i], end = start;
            while (i + 1 < sorted.length && sorted[i + 1] == end + 1 && end != Long.MAX_VALUE) {
                end = sorted[++i];
            }
            answer.add(start == end ? Long.toString(start) : start + "->" + end);
            i++;
        }
        return answer;
    }

    public static void mergeIntoFirst(int[] a, int m, int[] b, int n) {
        int i = m - 1, j = n - 1, write = m + n - 1;
        while (j >= 0) a[write--] = i >= 0 && a[i] > b[j] ? a[i--] : b[j--];
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        int[] a = {0, 5, 0, 3, 8};
        moveZeroes(a);
        require(Arrays.equals(a, new int[]{5,3,8,0,0}), "moveZeroes");
        require(Arrays.equals(productExceptSelf(new int[]{1,2,3,4}), new int[]{24,12,8,6}), "product");
        require(Arrays.equals(productExceptSelf(new int[]{0,2,0,4}), new int[]{0,0,0,0}), "product zeroes");
        int[] rotation = {1,2,3,4,5,6,7};
        rotateRight(rotation, 10);
        require(Arrays.equals(rotation, new int[]{5,6,7,1,2,3,4}), "rotation");
        require(longestUniqueCodePoints("a😀b😀c") == 3, "unicode window");
        require(summarizeRanges(new long[]{0,1,2,4,5,7}).equals(List.of("0->2","4->5","7")), "ranges");
        int[] first = {1,3,7,0,0,0};
        mergeIntoFirst(first, 3, new int[]{2,6,8}, 3);
        require(Arrays.equals(first, new int[]{1,2,3,6,7,8}), "merge");
        System.out.println("All arrays-and-strings checks passed.");
    }
}
