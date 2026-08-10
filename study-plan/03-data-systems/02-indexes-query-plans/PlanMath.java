public final class PlanMath {
  static double estimationFactor(long estimated, long actual) {
    if (estimated <= 0 || actual <= 0) return Double.POSITIVE_INFINITY;
    return Math.max((double) estimated / actual, (double) actual / estimated);
  }
  static long totalRows(long averageRows, long loops) {
    return Math.multiplyExact(averageRows, loops);
  }
  static boolean keysetAfter(long ts, long id, long cursorTs, long cursorId) {
    return ts < cursorTs || (ts == cursorTs && id < cursorId);
  }
  public static void main(String[] args) {
    if (estimationFactor(100, 12_000) != 120.0) throw new AssertionError();
    if (totalRows(3, 10_000) != 30_000) throw new AssertionError();
    if (!keysetAfter(100, 7, 100, 8)) throw new AssertionError();
    if (keysetAfter(100, 9, 100, 8)) throw new AssertionError();
    System.out.println("Plan arithmetic and keyset checks passed.");
  }
}
