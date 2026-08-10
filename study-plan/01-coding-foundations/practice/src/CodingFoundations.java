import java.util.*;
import java.util.concurrent.atomic.LongAdder;

public final class CodingFoundations {
    public static void moveZeroes(int[] a) {
        int write = 0;
        for (int x : a) if (x != 0) a[write++] = x;
        while (write < a.length) a[write++] = 0;
    }

    public static int[] twoSum(int[] a, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < a.length; i++) {
            int need = target - a[i];
            if (seen.containsKey(need)) return new int[]{seen.get(need), i};
            seen.putIfAbsent(a[i], i);
        }
        return new int[0];
    }

    public static int longestUnique(String s) {
        Map<Character, Integer> last = new HashMap<>();
        int left = 0, best = 0;
        for (int right = 0; right < s.length(); right++) {
            char c = s.charAt(right);
            if (last.containsKey(c)) left = Math.max(left, last.get(c) + 1);
            last.put(c, right);
            best = Math.max(best, right - left + 1);
        }
        return best;
    }

    public static int subarraySum(int[] a, int k) {
        Map<Integer, Integer> prefixFrequency = new HashMap<>();
        prefixFrequency.put(0, 1);
        int sum = 0, answer = 0;
        for (int x : a) {
            sum += x;
            answer += prefixFrequency.getOrDefault(sum - k, 0);
            prefixFrequency.merge(sum, 1, Integer::sum);
        }
        return answer;
    }

    public static int minimumShipCapacity(int[] weights, int days) {
        int low = 0, high = 0;
        for (int w : weights) { low = Math.max(low, w); high += w; }
        while (low < high) {
            int mid = low + (high - low) / 2;
            if (canShip(weights, days, mid)) high = mid;
            else low = mid + 1;
        }
        return low;
    }

    private static boolean canShip(int[] weights, int days, int capacity) {
        int usedDays = 1, load = 0;
        for (int w : weights) {
            if (load + w > capacity) { usedDays++; load = 0; }
            load += w;
        }
        return usedDays <= days;
    }

    static final class RequestCounter {
        private final LongAdder count = new LongAdder();
        void record() { count.increment(); }
        long total() { return count.sum(); }
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        int[] values = {0, 4, 0, 0, 7, 2, 0};
        moveZeroes(values);
        require(Arrays.equals(values, new int[]{4, 7, 2, 0, 0, 0, 0}), "moveZeroes");
        require(Arrays.equals(twoSum(new int[]{2, 7, 11, 15}, 9), new int[]{0, 1}), "twoSum");
        require(longestUnique("pwwkew") == 3, "longestUnique");
        require(subarraySum(new int[]{3, 4, 7, 2, -3, 1, 4, 2}, 7) == 4, "subarraySum");
        require(minimumShipCapacity(new int[]{1,2,3,4,5,6,7,8,9,10}, 5) == 15, "shipCapacity");
        System.out.println("All Coding Foundations checks passed.");
    }
}

