import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

public final class HashingSetsLab {
    public record Pair(int first, int second) {}

    public static Optional<Pair> twoSum(int[] values, int target) {
        Map<Integer, Integer> firstIndex = new HashMap<>();
        for (int i = 0; i < values.length; i++) {
            long required = (long) target - values[i];
            if (required >= Integer.MIN_VALUE && required <= Integer.MAX_VALUE) {
                Integer earlier = firstIndex.get((int) required);
                if (earlier != null) return Optional.of(new Pair(earlier, i));
            }
            firstIndex.putIfAbsent(values[i], i);
        }
        return Optional.empty();
    }

    public static int[] multisetIntersection(int[] a, int[] b) {
        if (a.length > b.length) return multisetIntersection(b, a);
        Map<Integer, Integer> counts = new HashMap<>();
        for (int x : a) counts.merge(x, 1, Integer::sum);
        int[] buffer = new int[a.length];
        int size = 0;
        for (int x : b) {
            int remaining = counts.getOrDefault(x, 0);
            if (remaining > 0) {
                buffer[size++] = x;
                if (remaining == 1) counts.remove(x); else counts.put(x, remaining - 1);
            }
        }
        return Arrays.copyOf(buffer, size);
    }

    public static long countSubarraysWithSum(int[] values, long target) {
        Map<Long, Long> prefixFrequency = new HashMap<>();
        prefixFrequency.put(0L, 1L);
        long prefix = 0, answer = 0;
        for (int value : values) {
            prefix += value;
            answer += prefixFrequency.getOrDefault(prefix - target, 0L);
            prefixFrequency.merge(prefix, 1L, Long::sum);
        }
        return answer;
    }

    public static List<List<String>> groupAnagrams(List<String> words) {
        Map<String, List<String>> groups = new LinkedHashMap<>();
        for (String word : words) {
            int[] cp = word.codePoints().sorted().toArray();
            String key = Arrays.toString(cp);
            groups.computeIfAbsent(key, unused -> new ArrayList<>()).add(word);
        }
        return new ArrayList<>(groups.values());
    }

    public static final class LruCache<K,V> extends LinkedHashMap<K,V> {
        private final int capacity;
        public LruCache(int capacity) {
            super(Math.max(1, capacity), 0.75f, true);
            if (capacity < 0) throw new IllegalArgumentException("negative capacity");
            this.capacity = capacity;
        }
        @Override protected boolean removeEldestEntry(Map.Entry<K,V> eldest) {
            return size() > capacity;
        }
    }

    public static final class BloomFilter {
        private final BitSet bits;
        private final int bitCount;
        private final int hashCount;

        public BloomFilter(int bitCount, int hashCount) {
            if (bitCount <= 0 || hashCount <= 0) throw new IllegalArgumentException();
            this.bits = new BitSet(bitCount);
            this.bitCount = bitCount;
            this.hashCount = hashCount;
        }
        public void add(String value) { indexes(value).forEach(bits::set); }
        public boolean mightContain(String value) { return indexes(value).allMatch(bits::get); }
        private java.util.stream.IntStream indexes(String value) {
            byte[] digest;
            try { digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)); }
            catch (NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
            int h1 = java.nio.ByteBuffer.wrap(digest, 0, 4).getInt();
            int h2 = java.nio.ByteBuffer.wrap(digest, 4, 4).getInt() | 1;
            return java.util.stream.IntStream.range(0, hashCount)
                    .map(i -> Math.floorMod(h1 + i * h2, bitCount));
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        require(twoSum(new int[]{3,3}, 6).orElseThrow().equals(new Pair(0,1)), "twoSum duplicates");
        require(Arrays.equals(multisetIntersection(new int[]{4,9,5,4}, new int[]{9,4,9,8,4}), new int[]{9,4,4}), "intersection");
        require(countSubarraysWithSum(new int[]{3,4,7,2,-3,1,4,2}, 7) == 4, "prefix counting");
        require(groupAnagrams(List.of("eat","tea","tan","ate","nat","bat")).size() == 3, "anagrams");
        LruCache<Integer,String> cache = new LruCache<>(2);
        cache.put(1,"A"); cache.put(2,"B"); cache.get(1); cache.put(3,"C");
        require(!cache.containsKey(2) && cache.containsKey(1), "LRU access order");
        BloomFilter bloom = new BloomFilter(10_000, 7);
        bloom.add("payment-9f4d");
        require(bloom.mightContain("payment-9f4d"), "Bloom false negative");
        System.out.println("All hashing-and-sets checks passed.");
    }
}
