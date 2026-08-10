import java.nio.file.*;
import java.util.*;

public final class ContainerPolicy {
  public static void main(String[] args) throws Exception {
    Path file=Path.of(args.length==0 ? "Dockerfile" : args[0]);
    String d=Files.readString(file);
    List<String> errors=new ArrayList<>();
    if (d.lines().filter(s->s.stripLeading().startsWith("FROM ")).count()<2) errors.add("multi-stage build");
    if (!d.contains("USER 10001:10001")) errors.add("numeric non-root USER");
    if (!d.contains("ENTRYPOINT [\"java\"")) errors.add("exec-form entrypoint");
    if (!d.contains("COPY --from=build")) errors.add("runtime copies build artifact");
    if (d.matches("(?s).*\\b(ADD|COPY)\\s+\\.\\s+.*")) errors.add("broad context copy");
    if (!errors.isEmpty()) throw new AssertionError(errors);
    System.out.println("Container policy checks passed.");
  }
}
