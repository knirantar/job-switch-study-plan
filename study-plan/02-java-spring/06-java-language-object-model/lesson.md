# Java Language and Object Model — From Source File to Correct Domain Code

**Parent:** 02 — Java and Spring  
**Level:** prerequisite; study before the existing JVM lesson  
**Study time:** 3–4 hours plus lab  
**Lab:** `JavaBasicsLab.java` (verified with OpenJDK 25)

## 1. FOUNDATIONS

### Why Java exists

Java was designed in the 1990s to make networked software safer and more portable than manually managed native programs. Source code is compiled by `javac` into JVM bytecode stored in `.class` files. A Java Virtual Machine verifies, loads and executes that bytecode, initially by interpretation and commonly by just-in-time compilation of hot paths. “Write once, run anywhere” means a compatible JVM abstracts many operating-system and processor differences; it does not mean every library, filesystem path, native dependency or timing behaves identically.

A **JDK** (Java Development Kit) contains the compiler, launcher, debugger and tools. A **JRE** historically meant the runtime needed to execute applications; modern deployments usually create/use a runtime image from a JDK distribution. Java SE defines the language and standard APIs. Spring is a framework running on Java; Spring Boot adds conventions and runtime assembly. Learn this boundary: the JVM does not know `@RestController`, and Spring does not define Java inheritance.

Java is statically typed: each expression has a compile-time type. It is strongly typed in the practical sense that unrelated values are not silently treated as interchangeable. Types let the compiler reject many invalid operations, drive overload resolution and document contracts. Static typing cannot prove business correctness: an `int` can still contain a negative age.

### Program structure

A source file belongs to a **package**, a namespace such as `com.example.claims`. Imports shorten type names; they do not copy code or install dependencies. A top-level public class normally has the same filename. A class declares fields, constructors and methods. `public static void main(String[] args)` is a conventional application entry point: `public` lets the launcher call it, `static` needs no instance, `void` returns no value, and `String[]` carries command-line arguments.

Java is case-sensitive. Statements usually end with semicolons; blocks use braces. Whitespace is mostly insignificant but formatting communicates scope. Comments are `//`, `/* ... */`, and Javadoc `/** ... */`. Identifiers conventionally use `lowerCamelCase`; classes `UpperCamelCase`; constants `UPPER_SNAKE_CASE`; packages lowercase.

### Values, references and objects

Java has eight **primitive types**: `boolean`, `byte`, `short`, `int`, `long`, `char`, `float`, `double`. A primitive variable contains its value. A variable of class/array/interface type contains a reference to an object or `null`. Java is always pass-by-value: a method receives a copy of the primitive value or a copy of the object reference. Mutating the referenced object is visible; reassigning the parameter is not.

An **object** has identity, state and behavior. A **class** is its implementation/type blueprint. `new Claim("C1001")` allocates and invokes a constructor. Garbage collection eventually reclaims unreachable objects, but files/sockets/database connections need deterministic closing.

### Object-oriented purpose

Encapsulation protects invariants by keeping representation private and exposing meaningful operations. Inheritance lets a subtype reuse/extend a base contract but creates coupling. Polymorphism lets code depend on an interface and execute implementation-specific behavior. Abstraction exposes what callers need while hiding details. Composition (“has a”) is usually safer than inheritance (“is a”) for changing business behavior.

Without encapsulation, any caller could set a paid claim back to received. Without polymorphism, every new payment method would add conditionals everywhere. Poor inheritance creates fragile base-class effects and misleading subtype relationships.

## 2. CORE MECHANICS

### 2.1 Variables, literals and initialization

Declare `int attempts = 3;`, `long population = 1_400_000_000L;`, `double rate = 0.15;`, `char grade = 'A';`, `boolean active = true;`. Underscores improve numeric readability. Local variables must be definitely assigned before use. Fields receive defaults (`0`, `false`, `null`), but relying on defaults can hide missing initialization.

`var total = 10;` asks the compiler to infer the local static type `int`; it is not dynamic typing and cannot be used for fields/parameters/return types. Prefer it when the initializer makes the type obvious, not when it obscures meaning.

Integer arithmetic truncates: `7 / 2 == 3`. If either operand is floating, `7 / 2.0 == 3.5`. Integer overflow wraps in two's complement: `Integer.MAX_VALUE + 1` becomes `Integer.MIN_VALUE`; use `Math.addExact` when overflow must fail. `double` cannot exactly represent many decimal fractions; use `BigDecimal` or minor units for money.

### 2.2 Operators, precedence and short-circuiting

Arithmetic: `+ - * / %`; comparison: `< <= > >= == !=`; boolean: `&& || !`; assignment includes `+=`. `&&` and `||` short-circuit, so `claim != null && claim.isValid()` safely avoids dereferencing null. `&`/`|` on booleans evaluate both operands and are also bitwise integer operators.

Do not depend on remembered precedence in complex expressions. Write parentheses and name intermediate boolean conditions. `a && b || c` means `(a && b) || c`, which may authorize `c` unexpectedly if the intended policy was `a && (b || c)`.

### 2.3 Control flow

`if/else` selects paths. `switch` selects among constants/patterns and modern switch expressions return a value. Loops are `for`, enhanced `for`, `while`, and `do/while`. `break` exits; `continue` advances. A `return` exits a method.

Boundary conditions dominate interview bugs. Iterating an array uses indices `0` through `length-1`; `i <= array.length` is out of bounds. Choose loop invariants: before each iteration, what portion is already correct? Prefer enhanced `for` when no index is needed.

### 2.4 Methods, parameters and overloading

A method has modifiers, return type, name, parameters and body. Its **signature** for overloading is name plus parameter types, not return type. `score(int)` and `score(long)` overload; `int score(String)` and `double score(String)` cannot coexist only by return type.

Java copies arguments. Given `void reset(Claim c) { c = new Claim("X"); }`, the caller's variable is unchanged. Given `void approve(Claim c) { c.approve(); }`, the shared object changes. Avoid hidden mutation; name commands clearly and favor immutable values.

Varargs `method(String... values)` compile as an array and must be last. They can allocate and introduce ambiguous overloads. Recursion needs a base case and consumes stack; iteration is often safer for deep input.

### 2.5 Arrays and strings

Arrays are fixed-length, zero-indexed objects with runtime component type. `new int[3]` contains zeros. `int[][]` is an array of array references and can be ragged. Assignment copies references, not contents; use `Arrays.copyOf` for a shallow array copy.

`String` is immutable. Concatenation creates a result (the compiler may optimize expressions); use `StringBuilder` for repeated construction in a loop. `==` compares references for objects; `equals` compares value according to the class. Interning can make some strings share identity, which is exactly why `==` appears to work in misleading examples.

### 2.6 Fields, constructors and access

Instance fields belong to objects; `static` fields belong to the class. A constructor has no return type and establishes invariants. `this` refers to the receiver; `this(...)` delegates to another constructor and must be first. If no constructor is declared, the compiler provides a default no-arg constructor; declaring any constructor removes that implicit one.

Access: `private` within class, package-private with no modifier, `protected` for package/subclass rules, `public` everywhere accessible. Start private and widen intentionally. `final` field assignment occurs once; for an object reference, the object may still mutate. A class `final` cannot be extended; a method `final` cannot be overridden.

### 2.7 Encapsulation and invariants

Do not generate setters for every field. A `Claim.approve()` method can require current state RECEIVED; `setStatus(APPROVED)` cannot express why/when. Validate constructor arguments and make invalid states hard to represent. Defensive copies protect mutable collections/dates crossing boundaries.

Records provide concise immutable data carriers with generated accessors, `equals`, `hashCode`, `toString`; record component references can still point to mutable objects. The lab's `Money` record validates nonnegative amount and three-letter currency and refuses cross-currency addition.

### 2.8 Inheritance, interfaces and polymorphism

`class CardPayment extends Payment` inherits accessible members; Java has single class inheritance. `implements` fulfills one or more interfaces. Override with exactly compatible signature; use `@Override` so the compiler catches mistakes. Dynamic dispatch chooses the runtime implementation for instance methods. Fields/static methods are not polymorphically overridden in the same way.

An interface expresses capability/contract and may have abstract, default, static and private helper methods. An abstract class can hold state/constructors and partial implementation. Prefer interface plus composition for replaceable services; use inheritance only for a genuine substitutable “is-a” relationship (Liskov substitution).

### 2.9 `Object`, equality and hashing

Every class ultimately extends `Object`. Important methods: `toString`, `equals`, `hashCode`, `getClass`. Default equality is identity. Value equality must be reflexive, symmetric, transitive, consistent and false for null. Equal objects must have equal hash codes. If fields participating in hash code mutate while an object is a `HashSet` key, lookup may fail.

Choose identity deliberately. The lab treats claims with the same stable ID as equal. In JPA entities, generated IDs/proxies complicate equality; do not blindly copy record-style equality.

### 2.10 Enums, records and sealed types

An enum is a fixed set of singleton instances and can have fields/methods. Compare enum values with `==`. Do not persist ordinal because inserting a constant changes numbers; persist stable names/codes with migration strategy.

A sealed class/interface restricts permitted implementations. Together with pattern matching and exhaustive switch, it models closed alternatives. The lab permits only `Approve` and `Review`; adding a new permitted decision forces the switch to be reconsidered.

### 2.11 Packages, modules and classpath

Packages organize names/access. Directory layout should match package convention. The **classpath** tells compiler/runtime where classes/resources are. “Could not find or load main class” often means wrong fully qualified name or classpath. JAR is a ZIP-based archive of classes/resources with metadata. Java Platform Module System adds explicit module dependencies/exports, but many Spring applications primarily use classpath/module-path indirectly through build tools.

### 2.12 Null, wrappers and boxing

`null` means no object reference. Dereferencing throws `NullPointerException`; modern messages often identify the failing expression. Validate required arguments (`Objects.requireNonNull`) and use empty collections rather than null collections. Optional is for explicit possible absence mainly at API return boundaries, not every field/parameter.

Wrapper classes (`Integer`, `Long`, etc.) enable primitives in generics and nullable values. Autoboxing converts automatically, but `Integer a=128; Integer b=128; a==b` may be false while small cached values may be true. Always use `equals` for wrapper values; unboxing null throws NPE.

### 2.13 Resources and try-with-resources

`AutoCloseable` resources are closed by `try (var stream = ...) { ... }`, including on exceptions. Multiple resources close in reverse order. A close exception may be **suppressed** behind the body exception and is inspectable. Garbage collection is not resource management; finalization is deprecated/unsafe for correctness.

### 2.14 Compile and run the lab

```bash
javac JavaBasicsLab.java
java JavaBasicsLab
```

It checks integer division, string equality, exact decimal money, equality/hash contract, guarded state transition and exhaustive sealed-type switch.

## 3. WORKED PROBLEMS

### Problem 1 — Integer arithmetic (easy)

What are `5/2`, `5%2`, and `(double)5/2`? **Solution:** 2, 1, 2.5. Both first operands are integers; casting before division changes promotion. **Mistake:** expecting mathematical rational division.

### Problem 2 — String identity (easy)

Why can `"x" == new String("x")` be false but `.equals` true? **Solution:** left/right are different object references with equal character values. `==` tests identity. **Mistake:** relying on string-pool behavior.

### Problem 3 — Pass-by-value (medium)

`void change(List<String> x){ x.add("A"); x=new ArrayList<>(); }`. What caller sees? **Solution:** original list gains A; parameter reassignment changes only copied reference. **Mistake:** saying Java passes objects by reference.

### Problem 4 — Equality/hash (medium)

`equals` compares claim ID but `hashCode` is inherited. What breaks? **Solution:** equal claims may have unequal identity hashes, so HashSet/HashMap can store/find incorrectly. Override both from same stable fields. **Mistake:** treating hash as optional optimization.

### Problem 5 — Mutable key (medium)

An object's email forms hash code; email changes after insertion into HashSet. **Solution:** it remains in bucket chosen by old hash and lookup under new hash can fail. Use immutable key/stable identity or remove/reinsert. **Mistake:** mutating equality fields in hashed collection.

### Problem 6 — Overload resolution (medium)

Given `f(long)` and `f(Integer)`, what does `f(1)` choose? **Solution:** primitive widening to long is preferred over boxing to Integer. **Mistake:** assuming exact-looking wrapper wins.

### Problem 7 — Encapsulation (hard)

Design claim status updates. **Solution:** private status, constructor initial RECEIVED, `approve/reject` methods validate transition/authority inputs and emit evidence; expose read access, no general setter. **Mistake:** anemic model with arbitrary setter.

### Problem 8 — Substitution (hard)

`ReadOnlyList extends ArrayList` but throws on `add`. Is it substitutable? **Solution:** callers expecting ArrayList mutation break; inheritance violates contract. Expose `List.copyOf`/unmodifiable view or separate read interface/composition. **Mistake:** inheritance for code reuse without behavioral compatibility.

### Problem 9 — Resource failure (hard)

Body throws E1 and `close()` throws E2. Which escapes? **Solution:** E1 is primary; E2 is suppressed and available via `getSuppressed()`. **Mistake:** assuming close replaces original failure or is ignored.

## 4. REAL-WORLD / APPLIED CONTEXT

Spring beans are ordinary Java objects whose constructors, access modifiers, equality and exceptions still obey these rules. Hibernate may create proxy subclasses, so final classes/methods and entity equality require informed decisions. Jackson constructs/maps objects according to Java visibility/constructors/records and configuration; it does not bypass domain validation safely by magic.

Money code in fintech commonly uses `BigDecimal` or integer minor units. `new BigDecimal(0.1)` captures the binary double approximation; use `new BigDecimal("0.1")` or `BigDecimal.valueOf(0.1)`. Always specify rounding where division is non-terminating.

OpenJDK 25 compiled and ran the included dependency-free lab. The checks are deterministic language invariants, not performance benchmarks.

## 5. COMPARISON TABLE

| Choice | Property | Use | Boundary |
|---|---|---|---|
| primitive `int` | 32-bit, no null | counters within range | overflow, no generics |
| `long` | 64-bit | IDs/counts/time units | still overflows |
| `double` | fast binary floating | measurement/statistics | not exact money |
| `BigDecimal` | decimal arbitrary precision | money/rates | scale/rounding/performance |
| class | mutable/behavior/state | domain entity/service | boilerplate |
| record | concise value carrier | immutable DTO/value | shallow immutability |
| interface | multiple contracts | service abstraction | no ordinary instance state |
| abstract class | state + partial implementation | genuine hierarchy | single inheritance/coupling |
| composition | explicit delegation | replaceable behavior | forwarding code |
| inheritance | runtime subtype reuse | true substitutability | fragile coupling |
| array | fixed size, indexed | compact known-size data | no growth |
| `ArrayList` | dynamic collection | general sequence | boxing/growth |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Java is pass-by-reference—the value passed may be a reference, but it is copied.
2. `==` compares object content—it compares references except primitives.
3. `final` object is immutable—only reference reassignment is prevented.
4. `static` means constant—it means class-associated; mutable static state is global.
5. Constructor has return type—then it is a method, not constructor.
6. Overloading differs by return type—parameter list must differ.
7. `double` is suitable for rupees—decimal amounts require exact rules.
8. Every field needs getter/setter—expose behavior and preserve invariants.
9. Records are deeply immutable—contained list/object can mutate unless copied.
10. GC closes files/connections—use try-with-resources.
11. Enum ordinal is stable persistence—reordering constants corrupts meaning.
12. Inheritance is always reuse—composition often preserves contracts better.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full lesson.

- Compile: `javac File.java`; run: `java FullyQualifiedClass`.
- Primitive stores value; reference variable stores object reference or null.
- Java passes everything by value.
- Integer division truncates; overflow wraps unless exact arithmetic used.
- Object content: `equals`; identity: `==`; equal → same hash code.
- `private` by default; constructor establishes invariants; behavior over setters.
- Override = runtime polymorphism; overload = compile-time parameter selection.
- Prefer composition/interface; inheritance requires substitutability.
- String immutable; use builder in loops; BigDecimal from string for exact decimal.
- `final` reference is not deep immutability; records are shallowly immutable.
- Use try-with-resources for AutoCloseable.

## 8. PRACTICE SET FOR SELF-TEST

1. What values result from `9/4`, `9%4`, and `9/4.0`?
2. Explain why reassigning a method parameter does not reassign the caller variable.
3. What contract connects `equals` and `hashCode`?
4. Why is `new BigDecimal("0.10")` preferable to `new BigDecimal(0.10)`?
5. Design a class that cannot represent a negative claim amount.
6. Distinguish overload from override with one example each.
7. When would you choose an interface over an abstract class?
8. What happens when try body and resource close both throw?
9. Why is persisting enum ordinal unsafe?
10. Is a record containing `ArrayList<String>` deeply immutable? Explain.

## 9. CURATED RESOURCES

1. **Java Language Specification, Java SE 25, Chapters 4–15** — authoritative types, conversions, expressions, statements, classes and method rules.
2. [OpenJDK Java Tutorials: Learning the Java Language](https://dev.java/learn/) — official modern guided examples from syntax through objects.
3. **Joshua Bloch, _Effective Java_, 3rd ed., Items 10–25 and 50** — equality, API/object construction, composition and defensive copies.
4. **Cay Horstmann, _Core Java Volume I_, 13th ed., Chapters 3–6** — systematic language/OOP treatment with practical examples.
5. [JEP 395: Records](https://openjdk.org/jeps/395) — exact motivation and semantics for records.
6. [JEP 409: Sealed Classes](https://openjdk.org/jeps/409) — controlled hierarchies and exhaustive modeling.
7. [BigDecimal Java SE API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/math/BigDecimal.html) — scale, constructors, equality and rounding behavior.
8. [AutoCloseable Java SE API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/AutoCloseable.html) — precise close/suppressed-exception contract.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Basic programming logic** — variables, conditions and loops are language-independent prerequisites.
2. **Complexity analysis** — helps judge the operations written with arrays and loops.
3. **Arrays and strings** — supplies problem-solving practice for Java syntax.

### After

1. **Collections, Generics and Exceptions** — generalizes arrays/types and builds reliable APIs.
2. **Modern Java and Streams** — uses interfaces, immutability and lambdas fluently.
3. **Build, Testing and Debugging** — turns source into repeatable applications.
4. **Spring Boot Fundamentals** — manages ordinary Java objects through dependency injection.
5. **JVM Memory and GC** — explains runtime representation/allocation after language objects are understood.

---ANSWER KEY BELOW---

1. 2, 1, and 2.25.
2. Java copies the reference value into the parameter. Parameter assignment changes only that local copy; mutation through either copied reference reaches the same object.
3. If `a.equals(b)` is true, `a.hashCode()==b.hashCode()` must be true; equality also must be reflexive, symmetric, transitive, consistent and false for null.
4. The string represents exact decimal 0.10; the double constructor captures the nearest binary floating approximation.
5. Private final `BigDecimal amount`; constructor requires non-null and `signum() >= 0`; no setter; operations return new validated values.
6. Overload: `pay(int)` versus `pay(long)`, selected at compile time. Override: subclass implementation of interface/base `pay`, dispatched by runtime receiver.
7. Choose interface for replaceable capability/multiple implementations without shared mutable base state; abstract class when a genuine hierarchy needs constructors/state/common protected implementation.
8. Body exception escapes as primary; close exception is attached as suppressed.
9. Inserting/reordering enum constants changes ordinals and silently remaps stored values.
10. No. The record reference is final, but callers can mutate the list unless the constructor makes an immutable defensive copy.
