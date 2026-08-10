import java.util.EnumSet;

public final class MigrationCompatibility {
  enum Schema { OLD_ONLY, BOTH_NULLABLE, BOTH_BACKFILLED, NEW_ONLY }
  enum App { OLD_READ_WRITE, DUAL_WRITE_OLD_READ, DUAL_WRITE_NEW_READ, NEW_ONLY }

  static boolean compatible(Schema s, App a) {
    return switch (s) {
      case OLD_ONLY -> a == App.OLD_READ_WRITE;
      case BOTH_NULLABLE -> a != App.NEW_ONLY;
      case BOTH_BACKFILLED -> true;
      case NEW_ONLY -> a == App.NEW_ONLY;
    };
  }

  static boolean safeTransition(Schema from, Schema to) {
    return (from == Schema.OLD_ONLY && to == Schema.BOTH_NULLABLE)
        || (from == Schema.BOTH_NULLABLE && to == Schema.BOTH_BACKFILLED)
        || (from == Schema.BOTH_BACKFILLED && to == Schema.NEW_ONLY);
  }

  public static void main(String[] args) {
    if (!compatible(Schema.BOTH_NULLABLE, App.OLD_READ_WRITE)) throw new AssertionError();
    if (!compatible(Schema.BOTH_BACKFILLED, App.NEW_ONLY)) throw new AssertionError();
    if (compatible(Schema.NEW_ONLY, App.OLD_READ_WRITE)) throw new AssertionError();
    if (safeTransition(Schema.OLD_ONLY, Schema.NEW_ONLY)) throw new AssertionError();
    if (!safeTransition(Schema.BOTH_NULLABLE, Schema.BOTH_BACKFILLED)) throw new AssertionError();
    System.out.println("Migration compatibility checks passed.");
  }
}
