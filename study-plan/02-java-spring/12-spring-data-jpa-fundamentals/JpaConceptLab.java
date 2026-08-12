import java.util.*;

public final class JpaConceptLab {
    enum State { TRANSIENT, MANAGED, DETACHED, REMOVED }
    record ClaimRow(long id, String tenant, String externalId, long version, long amountPaise) {}

    static final class PersistenceContext {
        private final Map<Long, ClaimRow> managed = new HashMap<>();
        ClaimRow find(long id, Map<Long, ClaimRow> database) {
            return managed.computeIfAbsent(id, key -> database.get(key));
        }
        void clear() { managed.clear(); }
    }

    static ClaimRow updateAmount(ClaimRow current, long expectedVersion, long newAmount) {
        if (current.version() != expectedVersion) throw new ConcurrentModificationException("stale version");
        if (newAmount <= 0) throw new IllegalArgumentException("positive amount required");
        return new ClaimRow(current.id(), current.tenant(), current.externalId(), current.version() + 1, newAmount);
    }

    static List<ClaimRow> keysetAfter(List<ClaimRow> sorted, long lastId, int limit) {
        return sorted.stream().filter(row -> row.id() > lastId).limit(limit).toList();
    }

    public static void main(String[] args) {
        Map<Long, ClaimRow> db = Map.of(1L, new ClaimRow(1, "T1", "E1", 0, 10_000));
        PersistenceContext pc = new PersistenceContext();
        ClaimRow a = pc.find(1, db), b = pc.find(1, db);
        check(a == b, "first-level identity");
        ClaimRow changed = updateAmount(a, 0, 12_000);
        check(changed.version() == 1, "optimistic version");
        try { updateAmount(changed, 0, 13_000); throw new AssertionError("stale expected"); }
        catch (ConcurrentModificationException expected) { check(expected.getMessage().contains("stale"), "stale update"); }
        List<ClaimRow> rows = List.of(db.get(1L), new ClaimRow(2,"T1","E2",0,20_000), new ClaimRow(3,"T2","E3",0,30_000));
        check(keysetAfter(rows, 1, 1).getFirst().id() == 2, "keyset page");
        System.out.println("All JPA concept checks passed.");
    }
    static void check(boolean condition, String name) { if (!condition) throw new AssertionError(name); }
}
