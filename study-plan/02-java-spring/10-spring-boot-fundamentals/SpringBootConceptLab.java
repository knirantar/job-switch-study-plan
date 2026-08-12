import java.util.*;

public final class SpringBootConceptLab {
    interface Notifier { String send(String message); }
    static final class EmailNotifier implements Notifier { public String send(String m) { return "email:" + m; } }
    static final class ClaimService {
        private final Notifier notifier;
        ClaimService(Notifier notifier) { this.notifier = Objects.requireNonNull(notifier); }
        String approve(String id) { return notifier.send("approved:" + id); }
    }
    static final class MiniContext {
        private final Map<Class<?>, Object> beans = new HashMap<>();
        <T> void register(Class<T> contract, T bean) {
            if (beans.putIfAbsent(contract, bean) != null) throw new IllegalStateException("duplicate bean " + contract);
        }
        <T> T get(Class<T> type) {
            Object bean = beans.get(type);
            if (bean == null) throw new NoSuchElementException("missing bean " + type);
            return type.cast(bean);
        }
    }
    public static void main(String[] args) {
        MiniContext context = new MiniContext();
        context.register(Notifier.class, new EmailNotifier());
        context.register(ClaimService.class, new ClaimService(context.get(Notifier.class)));
        check(context.get(ClaimService.class).approve("C1").equals("email:approved:C1"), "constructor injection");
        try { context.register(Notifier.class, new EmailNotifier()); throw new AssertionError("duplicate expected"); }
        catch (IllegalStateException expected) { check(expected.getMessage().contains("duplicate"), "duplicate detection"); }
        try { context.get(String.class); throw new AssertionError("missing expected"); }
        catch (NoSuchElementException expected) { check(expected.getMessage().contains("missing"), "missing dependency"); }
        System.out.println("All Spring Boot concept checks passed.");
    }
    static void check(boolean condition, String name) { if (!condition) throw new AssertionError(name); }
}
