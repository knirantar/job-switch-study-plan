import java.math.BigDecimal;
import java.util.Objects;

public final class JavaBasicsLab {
    enum Status { RECEIVED, APPROVED, REJECTED }

    record Money(BigDecimal amount, String currency) {
        Money {
            Objects.requireNonNull(amount, "amount");
            Objects.requireNonNull(currency, "currency");
            if (amount.signum() < 0) throw new IllegalArgumentException("negative amount");
            if (currency.length() != 3) throw new IllegalArgumentException("ISO currency required");
        }
        Money add(Money other) {
            if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
            return new Money(amount.add(other.amount), currency);
        }
    }

    sealed interface ClaimDecision permits Approve, Review { String reason(); }
    record Approve(String reason) implements ClaimDecision {}
    record Review(String reason) implements ClaimDecision {}

    static final class Claim {
        private final String id;
        private Status status;
        Claim(String id) { this.id = Objects.requireNonNull(id); this.status = Status.RECEIVED; }
        String id() { return id; }
        Status status() { return status; }
        void approve() {
            if (status != Status.RECEIVED) throw new IllegalStateException("invalid transition");
            status = Status.APPROVED;
        }
        @Override public boolean equals(Object other) {
            return this == other || other instanceof Claim claim && id.equals(claim.id);
        }
        @Override public int hashCode() { return id.hashCode(); }
    }

    static String describe(ClaimDecision decision) {
        return switch (decision) {
            case Approve approve -> "APPROVE:" + approve.reason();
            case Review review -> "REVIEW:" + review.reason();
        };
    }

    public static void main(String[] args) {
        check(7 / 2 == 3, "integer division");
        check(Math.abs(7 / 2.0 - 3.5) < 0.0001, "floating division");
        check("claim".equals(new String("claim")), "value equality");
        check(new Money(new BigDecimal("10.25"), "INR").add(new Money(new BigDecimal("0.75"), "INR"))
                .amount().equals(new BigDecimal("11.00")), "exact decimal addition");
        Claim first = new Claim("C1001");
        Claim sameIdentity = new Claim("C1001");
        check(first.equals(sameIdentity) && first.hashCode() == sameIdentity.hashCode(), "equality contract");
        first.approve();
        check(first.status() == Status.APPROVED, "state transition");
        check(describe(new Review("HIGH_VALUE")).equals("REVIEW:HIGH_VALUE"), "sealed switch");
        System.out.println("All Java language/object-model checks passed.");
    }

    private static void check(boolean condition, String name) {
        if (!condition) throw new AssertionError(name);
    }
}
