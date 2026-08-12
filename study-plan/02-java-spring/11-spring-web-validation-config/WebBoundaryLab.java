import java.util.*;

public final class WebBoundaryLab {
    record CreateClaimRequest(String externalId, long amountPaise, String currency) {}
    record Violation(String field, String code, String message) {}
    record Problem(String type, String title, int status, List<Violation> violations) {}

    static List<Violation> validate(CreateClaimRequest request) {
        List<Violation> errors = new ArrayList<>();
        if (request.externalId() == null || request.externalId().isBlank())
            errors.add(new Violation("externalId", "NotBlank", "must not be blank"));
        if (request.amountPaise() <= 0)
            errors.add(new Violation("amountPaise", "Positive", "must be greater than zero"));
        if (request.currency() == null || !request.currency().matches("[A-Z]{3}"))
            errors.add(new Violation("currency", "Currency", "must be a three-letter uppercase code"));
        return List.copyOf(errors);
    }

    static int parseLimit(String text) {
        try {
            int limit = Integer.parseInt(text);
            if (limit < 1 || limit > 100) throw new IllegalArgumentException("limit must be 1..100");
            return limit;
        } catch (NumberFormatException error) { throw new IllegalArgumentException("limit must be integer", error); }
    }

    static Problem invalid(List<Violation> errors) {
        return new Problem("https://example.test/problems/validation", "Request validation failed", 400, List.copyOf(errors));
    }

    public static void main(String[] args) {
        List<Violation> errors = validate(new CreateClaimRequest(" ", 0, "inr"));
        check(errors.size() == 3, "aggregate validation");
        check(invalid(errors).status() == 400, "problem mapping");
        check(parseLimit("100") == 100, "limit boundary");
        try { parseLimit("101"); throw new AssertionError("invalid expected"); }
        catch (IllegalArgumentException expected) { check(expected.getMessage().contains("1..100"), "range failure"); }
        System.out.println("All Spring Web boundary checks passed.");
    }
    static void check(boolean condition, String name) { if (!condition) throw new AssertionError(name); }
}
