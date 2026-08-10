import java.util.*;

public final class ConsistencyLab {
  enum Order { BEFORE, AFTER, EQUAL, CONCURRENT }
  record Clock(Map<String,Integer> values) {
    Clock { values = Map.copyOf(values); }
    Order compare(Clock other) {
      boolean less=false, greater=false;
      Set<String> nodes = new HashSet<>(values.keySet()); nodes.addAll(other.values.keySet());
      for (String n : nodes) {
        int a=values.getOrDefault(n,0), b=other.values.getOrDefault(n,0);
        less |= a < b; greater |= a > b;
      }
      if (less && greater) return Order.CONCURRENT;
      if (less) return Order.BEFORE;
      if (greater) return Order.AFTER;
      return Order.EQUAL;
    }
  }

  static boolean quorumOverlap(int replicas, int reads, int writes) {
    return reads + writes > replicas && writes * 2 > replicas;
  }

  static final class Ledger {
    private final Set<String> applied = new HashSet<>();
    private long balance;
    boolean credit(String operationId, long amount) {
      if (amount <= 0) throw new IllegalArgumentException();
      if (!applied.add(operationId)) return false;
      balance = Math.addExact(balance, amount); return true;
    }
    long balance() { return balance; }
  }

  record Reservation(String sagaId, boolean inventoryHeld, boolean paymentCaptured) {
    Reservation capture() { return new Reservation(sagaId, inventoryHeld, true); }
    Reservation compensateInventory() { return new Reservation(sagaId, false, paymentCaptured); }
  }

  public static void main(String[] args) {
    Clock a=new Clock(Map.of("A",2,"B",1));
    Clock b=new Clock(Map.of("A",1,"B",2));
    if (a.compare(b)!=Order.CONCURRENT) throw new AssertionError();
    if (a.compare(new Clock(Map.of("A",3,"B",1)))!=Order.BEFORE) throw new AssertionError();
    if (!quorumOverlap(3,2,2) || quorumOverlap(3,1,2)) throw new AssertionError();
    Ledger l=new Ledger();
    if (!l.credit("op-7",125000) || l.credit("op-7",125000) || l.balance()!=125000)
      throw new AssertionError();
    Reservation r=new Reservation("s1",true,false).compensateInventory();
    if (r.inventoryHeld) throw new AssertionError();
    System.out.println("Clock, quorum, idempotency, and compensation checks passed.");
  }
}
