import java.util.EnumSet;

/** Run: javac DiscreteMathLab.java && java -ea DiscreteMathLab */
public final class DiscreteMathLab {
    enum Permission { READ, WRITE, EXPORT, ADMIN }

    static boolean allowed(boolean employee, boolean contractor, boolean consent) {
        return (employee || contractor) && consent;
    }

    static int gcd(int a, int b) {
        a = Math.abs(a); b = Math.abs(b);
        while (b != 0) { int remainder = a % b; a = b; b = remainder; }
        return a;
    }

    static boolean isPowerOfTwo(int n) {
        return n > 0 && (n & (n - 1)) == 0;
    }

    static int bitCount(int n) {
        int count = 0;
        while (n != 0) { n &= n - 1; count++; }
        return count;
    }

    static int uniquePaired(int[] values) {
        int result = 0;
        for (int value : values) result ^= value;
        return result;
    }

    public static void main(String[] args) {
        assert allowed(true, false, true);
        assert !allowed(true, false, false);
        assert allowed(false, true, true);
        assert gcd(252, 105) == 21;
        assert Math.floorMod(-1, 8) == 7;
        assert isPowerOfTwo(1) && isPowerOfTwo(1_024) && !isPowerOfTwo(0) && !isPowerOfTwo(70);
        assert bitCount(44) == 3;
        assert uniquePaired(new int[]{503, 200, 429, 503, 429}) == 200;
        EnumSet<Permission> user = EnumSet.of(Permission.READ, Permission.EXPORT);
        EnumSet<Permission> effective = EnumSet.copyOf(user);
        effective.retainAll(EnumSet.of(Permission.READ, Permission.WRITE));
        assert effective.equals(EnumSet.of(Permission.READ));
        System.out.println("PASS: logic, sets, modular arithmetic, and bits");
    }
}
