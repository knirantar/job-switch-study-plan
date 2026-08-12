# Python Collections, Functions, and Object-Oriented Programming

Parent subject: `07-python-mlops`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why this layer matters

Python programs are built less from explicit class hierarchies than many Java programs. They rely heavily on sequences, mappings, iterators, first-class functions, protocols, context managers, and small composed objects. Knowing syntax without this model produces code that is unnecessarily imperative, accidentally quadratic, mutable in surprising ways, or tightly coupled.

Python's **data model** defines special methods through which user types participate in built-in operations. `len(x)` invokes `x.__len__`; iteration asks for `__iter__`; `with` uses context-manager methods; equality uses `__eq__`. This creates a coherent protocol ecosystem without requiring every type to inherit from one concrete collection base.

### Collection abstractions

A **container** holds references to objects. A **sequence** has ordered positions; a **mapping** associates keys with values; a **set** represents distinct membership. A collection can be mutable or immutable, finite or lazy, materialized or computed.

Choose from required operations, not habit. Lists provide amortized O(1) append and O(1) indexing, but inserting/removing at the front is O(n). `collections.deque` gives O(1) append/pop at both ends. Dict and set give average O(1) lookup under normal hashing, but equality/hash correctness and memory matter. A generator can process a billion-line stream in bounded memory, while a list cannot.

### Iterables, iterators, and generators

An **iterable** can produce an iterator, commonly via `iter(x)`. An **iterator** maintains traversal state, returns items with `next`, and raises `StopIteration` when exhausted. Iterators are generally single-pass. Calling `iter` on a list produces a new iterator; calling it on an iterator often returns itself.

A **generator function** contains `yield`. Calling it returns a generator without executing the body immediately. Each `next` resumes until the next yield. Generators enable pipelines and resource-efficient streaming, but errors can occur during iteration rather than construction, and an open resource must remain alive while consumption occurs.

### Comprehensions

List, set, and dict comprehensions express transformation/filtering close to mathematical set-builder notation:

```python
paid_ids = [c.id for c in claims if c.status == "PAID"]
amount_by_id = {c.id: c.amount_paise for c in claims}
```

A generator expression uses parentheses and is lazy. Comprehensions should remain readable; nested business rules deserve named functions/loops. Building a dict silently overwrites duplicate keys, so uniqueness must be validated when duplicates are invalid.

### First-class functions

Functions are objects: assign, store, pass, return, and decorate them. A **higher-order function** accepts or returns functions. `sorted(items, key=...)`, `map`, `filter`, callbacks, dependency injection, and decorators use this ability.

A **closure** is a function retaining bindings from an enclosing scope. It can create configured validators without a class. Be aware of late binding: closures created in a loop reference the same loop variable unless captured through a default/factory.

### Call semantics in depth

Arguments are evaluated before call and bound to parameter names. Objects are shared; a callee can mutate an object if its API permits. `*iterable` expands positional items and `**mapping` expands keyword items. Duplicate or unexpected bindings raise `TypeError`.

Use positional-only parameters when names are not API, keyword-only for clarity/evolution, and immutable inputs/outputs where possible. Functions should expose side effects in names/contracts. Pure transformations are simpler to test and parallelize.

### Classes and instances

A **class** is an object that defines construction and behavior; an **instance** has class association and instance state. `__init__` initializes an already created instance; `__new__` creates it and is rarely overridden in ordinary code.

```python
class Claim:
    def __init__(self, claim_id: str, amount_paise: int):
        self.claim_id = claim_id
        self.amount_paise = amount_paise
```

`self` is the conventional instance parameter passed explicitly by bound-method machinery. Python does not enforce private fields; `_name` means non-public by convention, while double-leading names trigger name mangling mainly to avoid subclass collisions, not provide security.

### Class attributes and instance attributes

A class attribute is shared lookup state unless shadowed by an instance. A mutable class attribute can unintentionally be shared across every instance:

```python
class Bad:
    tags = []
```

Initialize mutable per-instance state inside `__init__` or use dataclass `default_factory`. Class attributes suit constants and deliberate shared descriptors/registries with care.

### Dataclasses

`@dataclass` generates initialization, representation, equality, and optionally ordering/frozen/hash-related methods from annotated fields. It is ideal for value-oriented records, not automatic validation. `frozen=True` prevents normal attribute rebinding but does not deeply freeze contained mutable objects.

```python
@dataclass(frozen=True, slots=True)
class Money:
    amount_paise: int
    currency: str
```

Validate in `__post_init__`; frozen classes use `object.__setattr__` only for justified derived initialization. `slots=True` can reduce instance memory and prevent arbitrary attributes, but affects inheritance/weak references/pickling considerations.

### Encapsulation, properties, and invariants

A property exposes method logic through attribute syntax. It can preserve an API while computing/validating. Avoid Java-style getters/setters that add no invariant. Make invalid states hard to create and prefer operations such as `claim.approve()` over public status mutation when transitions matter.

Python callers can bypass conventions, so encapsulation is social plus architectural rather than a security boundary. Validate at external boundaries and persist constraints in the database.

### Inheritance, composition, and protocols

Inheritance expresses an **is-a** substitutability relationship. Multiple inheritance and method resolution order (MRO) are supported, but deep hierarchies become fragile. `super()` follows MRO cooperatively, not simply “call parent.”

Composition gives an object collaborators and delegates. It generally handles changing behavior better. **Duck typing** accepts objects based on supported operations: “if it quacks.” `typing.Protocol` makes this structural contract visible to static checkers without inheritance.

```python
class ModelStore(Protocol):
    def load(self, model_id: str) -> bytes: ...
```

An Azure store and in-memory test store can satisfy this protocol independently. This reduces coupling to SDK classes.

### Resource management and context managers

Objects representing files, locks, DB transactions, temp directories, or spans need deterministic cleanup. A context manager defines `__enter__`/`__exit__`, or is built with `contextlib.contextmanager`. `__exit__` returning true suppresses an exception; usually return false/None unless suppression is deliberate and narrow.

Garbage collection timing is not a resource-management contract. Use `with`, even on CPython where reference counting often closes objects promptly.

### Equality, hashing, representation, and ordering

`__repr__` should give an unambiguous developer representation without secrets. `__str__` is user-friendly. `__eq__` defines equality; hashable objects used as dict/set keys must have a hash stable during membership and equal objects must have equal hashes. Mutable value objects should usually be unhashable.

Ordering uses rich comparisons or a key function. Prefer `key` sorting to implementing all comparisons. Never include secrets/PHI in repr because tracebacks/logs/notebooks display it.

## 2. CORE MECHANICS

### 2.1 List and deque operations

For one million queue operations, `list.pop(0)` shifts remaining references each time and becomes quadratic. Use:

```python
from collections import deque
q = deque(["J1", "J2"])
q.append("J3")
assert q.popleft() == "J1"
```

List slicing creates a shallow new list; nested objects remain shared. `copy.deepcopy` recursively copies according to object protocols but can be expensive or semantically wrong for connections/locks. Prefer explicit immutable value construction.

### 2.2 Dict patterns

Use `d.get(key)` only when missing and stored `None` can share meaning. Membership `if key in d` distinguishes. `setdefault` can initialize, but `defaultdict` clarifies repeated grouping:

```python
from collections import defaultdict
by_tenant = defaultdict(list)
for claim in claims:
    by_tenant[claim.tenant_id].append(claim)
```

For counting, `Counter(statuses)`. Dict union `a | b` lets right values win; ensure overwrite policy. Iterating keys while changing dict size raises runtime error; iterate a copy if mutation is intentional.

### 2.3 Set algebra

`a | b` union, `a & b` intersection, `a - b` difference, `a ^ b` symmetric difference, `a <= b` subset. For permissions, effective set is often intersection, while required <= effective verifies authorization. Never use union to combine independently restrictive policies.

### 2.4 Lazy pipelines

```python
def valid_amounts(rows):
    for line_no, row in enumerate(rows, 1):
        try:
            amount = int(row["amount_paise"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"bad row {line_no}") from exc
        if amount > 0:
            yield amount

total = sum(valid_amounts(reader))
```

Memory is O(1) beyond input buffers. If iteration stops early, generator cleanup/finalization matters; keep file `with` around consumption.

### 2.5 Sorting and grouping

Python sort is stable. Sort claims by amount descending then ID ascending using a key; for mixed direction, numeric negation works when safe:

```python
ordered = sorted(claims, key=lambda c: (-c.amount_paise, c.claim_id))
```

`itertools.groupby` groups only consecutive equal keys; sort first or use dict accumulation. Sorting one million objects is O(n log n) and materializes result. For top 100, `heapq.nlargest` may use O(100) memory and O(n log 100).

### 2.6 Dataclass invariant

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Money:
    amount_paise: int
    currency: str

    def __post_init__(self):
        if self.amount_paise < 0:
            raise ValueError("negative money")
        if self.currency not in {"INR", "USD"}:
            raise ValueError("unsupported currency")

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("currency mismatch")
        return Money(self.amount_paise + other.amount_paise, self.currency)
```

This returns a new value and prohibits mixed-currency addition.

### 2.7 Class methods and static methods

Instance method receives self. `@classmethod` receives class and is useful for alternative constructors preserving subclasses:

```python
@classmethod
def from_rupees(cls, text: str): ...
```

`@staticmethod` receives neither and is namespaced utility; often a module function is simpler. Do not use classmethod merely to access global singleton state.

### 2.8 Protocol-driven composition

```python
class Predictor(Protocol):
    def predict(self, features: tuple[float, ...]) -> float: ...

class EligibilityService:
    def __init__(self, predictor: Predictor):
        self._predictor = predictor

    def score(self, features):
        value = self._predictor.predict(tuple(features))
        if not 0 <= value <= 1:
            raise ValueError("invalid model score")
        return value
```

Tests inject a deterministic fake. Runtime code injects a model client. The service validates its dependency boundary.

### 2.9 Context manager

```python
from contextlib import contextmanager

@contextmanager
def transaction(connection):
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
```

Production drivers may already provide context semantics; use them correctly. Rollback failure can mask the original exception, so log/chain safely and return connection to pool only if valid.

### 2.10 Decorators

A decorator receives a function and returns a callable. Preserve metadata with `functools.wraps`:

```python
def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        try: return fn(*args, **kwargs)
        finally: observe(fn.__name__, perf_counter()-start)
    return wrapper
```

Decorators can obscure control flow, signatures, async behavior, and dependency injection. Keep cross-cutting behavior small and tested; never log raw args by default.

## 3. WORKED PROBLEMS

### Problem 1 — Queue choice (easy)

Need FIFO enqueue/dequeue at both ends for 500,000 jobs.

**Solution.** `deque`; list front removal shifts O(n).

**Trap:** list `pop(0)` because it works on ten items.

### Problem 2 — Shallow copy (easy)

`a=[[1],[2]]; b=a.copy(); b[0].append(9)`. What is a?

**Solution.** `[[1,9],[2]]`; outer list copied, inner shared.

**Trap:** calling `.copy()` deep copy.

### Problem 3 — Generator exhaustion (easy)

Consume `g=(x*x for x in range(3))` twice.

**Solution.** First gives 0,1,4; second nothing. Generator is single-pass.

**Trap:** treating it as reusable list.

### Problem 4 — Duplicate dict key (medium)

Build `{c.external_ref:c for c in claims}` with duplicates.

**Solution.** Later claim overwrites earlier silently. If uniqueness required, detect membership and raise/report or enforce upstream DB unique constraint.

**Trap:** dict construction as validation.

### Problem 5 — Closure late binding (medium)

Functions created with `[lambda: i for i in range(3)]` return what?

**Solution.** Each returns 2 when called later because all close over the same final `i`. Capture `lambda i=i: i` or factory.

**Trap:** assuming value copied each iteration.

### Problem 6 — Shared class list (medium)

Two instances append to class attribute `tags=[]`.

**Solution.** Both observe the same list. Create `self.tags=[]` or dataclass `field(default_factory=list)`.

**Trap:** annotations without assignment/default factory.

### Problem 7 — Hash mutation (hard)

Why not hash an object by mutable email?

**Solution.** After insertion into set/dict, changing email changes hash/equality location; lookup/removal can fail and invariants break. Use immutable identity/value or make object unhashable.

**Trap:** defining `__hash__` to silence an error.

### Problem 8 — Inheritance substitution (hard)

Subclass `ReadOnlyStore` overrides `save` to throw. Is it subtype of writable Store?

**Solution.** No under a contract requiring successful save; it violates substitutability. Split read/write protocols and depend on the needed one.

**Trap:** inheritance based on shared fields/names alone.

### Problem 9 — Context suppression (hard)

`__exit__` returns True for every exception. Risk?

**Solution.** All block exceptions disappear, potentially committing/continuing after failure. Suppress only specifically intended exceptions; normally return false/None.

**Trap:** thinking True means cleanup succeeded.

## 4. REAL-WORLD / APPLIED CONTEXT

### pandas and iterables

pandas operates on columnar Series/DataFrames rather than Python row loops for many transformations. Still, iterators stream input chunks and dataclasses/protocols structure pipeline boundaries. Converting a huge generator to list defeats streaming.

### PyTorch datasets

PyTorch distinguishes map-style datasets with indexing/length and iterable datasets for streams. Multi-worker iterable datasets must shard work to avoid duplicate samples. This is the iterable protocol applied to distributed data loading.

### Dependency injection in FastAPI

FastAPI dependencies are callables and can yield resources for cleanup. First-class functions, generators/context managers, annotations, and protocols underpin testable DB/model-client injection.

## 5. COMPARISON TABLE

| Structure | Key operations | Typical complexity | Use |
|---|---|---|---|
| list | index/append | O(1), amortized append | ordered materialized sequence |
| deque | append/pop both ends | O(1) | queue/window |
| dict | key lookup/insert | average O(1) | mapping/index/group |
| set | membership/add | average O(1) | dedup/algebra |
| heap | push/pop minimum | O(log n) | priority/top-k |
| generator | next | O(1) state plus computation | streaming/lazy pipeline |
| dataclass | value record | field-dependent | domain/config/result values |
| Protocol | structural interface | static-analysis abstraction | decoupled collaborators |
| inheritance | shared substitutable behavior | MRO-dependent | stable is-a relationship |
| composition | delegation | explicit | evolving behavior/dependencies |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. List is a good queue at the front—use deque.
2. Shallow copy isolates nested state—it does not.
3. Generators execute at construction—they execute during iteration.
4. Iterators can always be restarted—they are usually consumed.
5. Dict comprehension rejects duplicate keys—it overwrites.
6. `groupby` groups all equal items—it groups consecutive items.
7. Class annotation creates instance field automatically—not in a plain class.
8. Dataclass frozen means deeply immutable—nested objects can mutate.
9. Underscore makes data secure—it is convention.
10. Inheritance is code reuse—substitutability is the real contract.
11. Equal objects may have different hashes—this violates hash contract.
12. Garbage collection is deterministic resource cleanup—use context managers.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- Iterable creates iterator; iterator is stateful/single-pass.
- Generator is lazy and resumes at yield.
- List front operations O(n); deque ends O(1).
- Dict/set average O(1), keys require stable equality/hash.
- Comprehensions should stay readable; dict duplicate overwrites.
- Functions are objects; closures retain bindings and bind late.
- Class attributes are shared; per-instance mutable state in init/default_factory.
- Dataclass generates mechanics, not business validation.
- Prefer composition; use inheritance only for substitutability.
- Protocol expresses structural interface without shared base.
- Context manager deterministically releases/commits/rolls back.
- repr/logging must exclude secrets and regulated data.

## 8. PRACTICE SET FOR SELF-TEST

1. Choose list/deque for sliding window with removal from left.
2. Explain shallow versus deep copy of a dict containing lists.
3. Write a generator for positive amounts.
4. Count status strings with standard library.
5. Validate duplicate IDs while constructing a mapping.
6. Fix three lambdas created in a loop so they return 0,1,2.
7. Define frozen Money dataclass and currency-safe addition.
8. Define a protocol for an artifact store with `put` and `get`.
9. Explain why a mutable dataclass defaults to unhashable.
10. Describe transaction context behavior on success and exception.

## 9. CURATED RESOURCES

- Python Language Reference, “Data model,” “Compound statements,” and “Expressions” — exact protocols, class, iterator, generator, with, and call semantics.
- Python Standard Library docs for `collections`, `itertools`, `functools`, `heapq`, `dataclasses`, `contextlib`, and `typing.Protocol` — canonical tools used here.
- Luciano Ramalho, *Fluent Python*, 2nd ed., Chapters 1–3, 5–10, 12–14, 17–18 — sequences, mappings, functions, decorators, data classes, interfaces, inheritance, iterators, context managers.
- Brett Slatkin, *Effective Python*, 2nd ed., Items 18–47 — comprehensions, generators, functions, classes, composition, and descriptors.
- PEP 557 “Data Classes,” PEP 544 “Protocols,” PEP 343 “with Statement,” and PEP 255 “Simple Generators” — primary design rationale.
- Gamma et al., *Design Patterns*, Strategy, Adapter, Composite, and Template Method chapters — useful contrast with Python functions/protocols/composition.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Python Language Fundamentals:** names, mutability, loops, functions, exceptions, modules.
2. **DSA Collections:** complexity and invariants behind built-ins.

### After

1. **Python Tooling/Testing/Data:** validates these functions/types and applies them to arrays/tables.
2. **Production Python:** deepens data model, memory, typing, concurrency, packaging.
3. **FastAPI:** uses callables, protocols, dataclasses/models, dependency generators.
4. **ML Fundamentals:** uses iterators, arrays, pipeline composition, estimators.

---ANSWER KEY BELOW---

1. deque.
2. Shallow copies outer mapping but shares nested lists; deep recursively copies supported state, though explicit copy is often safer.
3. `def positives(xs): for x in xs: if x>0: yield x`.
4. `collections.Counter(statuses)`.
5. Check `if id in result: raise...` before assignment; DB uniqueness remains authoritative for concurrent persistence.
6. `[lambda i=i: i for i in range(3)]` or factory.
7. Annotated frozen dataclass, validate nonnegative/currency, add only same currency and return new Money.
8. `class ArtifactStore(Protocol): def put(...)->...; def get(...)->bytes: ...` with precise errors/types.
9. Value-based hash would become unstable after mutation; dataclass prevents unsafe default hash.
10. Acquire/yield; commit on normal completion; rollback and re-raise on exception; always release valid connection.
