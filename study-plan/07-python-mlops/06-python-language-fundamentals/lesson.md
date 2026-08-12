# Python Language Fundamentals from Scratch

Parent subject: `07-python-mlops`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### Why Python exists and where it fits

Python is a high-level, general-purpose programming language emphasizing readability, rapid development, and a large ecosystem. Guido van Rossum began it around 1989, drawing from ABC and systems scripting experience. Python now dominates automation, data science, ML, notebooks, testing, APIs, and glue code while also supporting substantial production services.

Python reduces ceremony but not engineering obligations. Dynamic typing moves many checks to execution or static-analysis tools. Mutable objects, exceptions, dependency environments, concurrency, numerical types, and packaging still need precise reasoning. A senior Java engineer should not write Java syntax in Python; learn Python's object/name and iteration models.

This lesson assumes no Python. It uses Python 3; Python 2 is end-of-life and has incompatible semantics. Verify the interpreter with `python3 --version`. A Python implementation such as CPython parses source, compiles it to bytecode, and executes it in a virtual machine; implementation details matter later, but language behavior is the starting point.

### Source, interpreter, REPL, script, and module

Python source is text commonly stored in `.py`. The **interpreter** executes it. A **REPL** reads, evaluates, prints, and loops interactively—useful for experiments, not reproducible production workflows. A **script** is executed as a top-level file. A **module** is an importable namespace backed commonly by a file; a **package** groups modules.

Run `python3 hello.py`. The block

```python
if __name__ == "__main__":
    main()
```

executes entry behavior only when the module is run directly, not imported. Keep import-time side effects minimal; opening network connections or starting jobs during import makes tests/tooling unpredictable.

### Indentation and statements

Python uses indentation to delimit suites instead of braces. Standard style uses four spaces and does not mix tabs. A colon starts a block after `if`, `for`, `while`, `def`, `class`, `try`, `with`, and related clauses.

Comments begin `#`. A **docstring** is a string literal as the first statement in module/class/function and documents its contract. Python style conventions are described in PEP 8; correctness comes first, but consistent formatting reduces review effort.

### Objects, values, names, and types

Everything manipulated is an object with identity, type, and value/state. A variable is better understood as a **name bound to an object**, not a Java-like box with a declared primitive type.

```python
a = [1, 2]
b = a
b.append(3)
```

Both names reference the same mutable list, so `a` is `[1,2,3]`. Assignment did not copy. `==` asks value equality; `is` asks object identity. Use `is None`, but generally `==` for values. Interpreter interning makes identity of small integers/strings an invalid assumption.

Built-in scalar types include `NoneType`, `bool`, `int`, `float`, `complex`, and `str`. Python integers have arbitrary precision limited by memory (though conversion/security limits may apply); floats are typically IEEE-754 binary64 and cannot exactly represent 0.1. `decimal.Decimal` supports decimal arithmetic under a context; `fractions.Fraction` exact rational values.

Types are dynamic: a name can later bind another type, but clear code avoids arbitrary type changes. Type hints document/analyze expected types; standard Python does not enforce most annotations at runtime.

### Mutability

Immutable built-ins include int, float, bool, str, bytes, tuple (though it can contain mutable objects), and frozenset. Mutable types include list, dict, set, bytearray, and most class instances. Hash-map/set keys must have stable hash/equality; immutable hashable types are typical.

Mutation changes an existing object; rebinding points a name elsewhere. This distinction controls function side effects, default arguments, copying, and concurrency.

### Expressions and operators

Arithmetic includes `+ - * / // % **`. `/` returns true division float; `//` floor division rounds toward negative infinity: `-3 // 2 == -2`. `%` is consistent with floor division: `-3 % 2 == 1`. `**` is exponentiation (unlike Java's bitwise XOR `^`).

Comparisons can chain: `0 <= x < 100`. Boolean `and`, `or`, `not` short-circuit and return operands, not necessarily bool: `name or "unknown"`. Use this intentionally; empty valid values can be mistakenly replaced. Truthy/falsey: false includes `False`, `None`, numeric zero, and empty containers/strings. Explicit checks are clearer when zero/empty differs from absent.

### Control flow

`if`/`elif`/`else` chooses. `for` iterates objects rather than exposing only numeric indexes. `range(start,stop,step)` produces a lazy integer sequence excluding stop. `while` repeats while truthy and needs progress. `break` exits a loop; `continue` starts next iteration; loop `else` runs if loop ends without `break`, useful for search but unfamiliar.

Structural pattern matching (`match`) in modern Python matches data shapes/patterns, not merely switch equality. Use it when it clarifies closed variants; avoid complex clever patterns for open domain rules.

### Functions

`def` creates a function object and binds its name. Parameters receive object references by assignment—often described as **call by sharing**. A function can mutate a mutable argument, but rebinding a parameter does not rebind caller's name.

```python
def add_claim(claims, claim):
    claims.append(claim)       # caller sees mutation

def replace(claims):
    claims = []                # caller binding unchanged
```

Functions return with `return`; falling off returns `None`. Values can be positional or keyword. Parameters can be positional-only (`/`), positional-or-keyword, variadic `*args`, keyword-only after `*`, and `**kwargs`. Prefer explicit APIs over catch-all kwargs.

Default arguments are evaluated once when `def` executes, not per call. Never use a mutable default such as `def f(items=[]):`; use `None` sentinel and allocate inside.

### Scope

Name lookup follows LEGB: local, enclosing function, global module, builtins. Assignment inside a function creates local binding unless declared `global` or `nonlocal`. Avoid mutable globals; inject dependencies and return values. Closures retain enclosing variables and are useful for factories/decorators, but late binding in loops surprises without explicit capture.

### Exceptions

Exceptions signal abnormal outcomes. `raise` creates/propagates; `try` catches specific types; `else` runs if no exception; `finally` runs for cleanup. Catch the narrow exception you can handle. `except Exception: pass` hides bugs and failures. Preserve cause with `raise DomainError(...) from exc`.

Built-ins include `ValueError` for correct type but invalid value, `TypeError` for inappropriate type/operation, `KeyError`, `IndexError`, `OSError` and subclasses. Domain exceptions can form a small meaningful hierarchy. Exceptions are not a replacement for normal absent results where absence is expected.

### Files and context managers

Open text with explicit encoding:

```python
with open("claims.csv", "r", encoding="utf-8", newline="") as handle:
    text = handle.read()
```

`with` invokes a **context manager** to acquire/release resources even on exceptions. File modes include `r`, `w` (truncate/create), `a`, `x` (exclusive create), plus `b` binary and `+` update. Do not load unbounded files blindly; stream line/chunk and enforce size. Paths should use `pathlib.Path` for portable composition.

### Imports

`import math` binds module; `from math import sqrt` binds selected object. Modules are loaded once per interpreter cache in normal operation, so top-level state persists. Avoid wildcard imports. Imports execute module top-level code; cyclic imports indicate tangled dependencies and can expose partially initialized modules.

Use standard library first: `pathlib`, `json`, `csv`, `datetime`, `decimal`, `collections`, `itertools`, `logging`, `argparse`, `subprocess`, `typing`, and `unittest`. Third-party dependencies require environments and packaging covered later.

## 2. CORE MECHANICS

### 2.1 Edit, run, and test a program

```python
def total_paise(amounts: list[int]) -> int:
    total = 0
    for amount in amounts:
        if amount < 0:
            raise ValueError(f"negative amount: {amount}")
        total += amount
    return total

def main() -> None:
    print(total_paise([129_900, 49_900, 25_000]))

if __name__ == "__main__":
    main()
```

Result 204800. Python int does not overflow at 64-bit, but external DB/API types may. Empty list returns zero. Passing `None` raises TypeError during iteration; decide whether to validate a clearer contract.

### 2.2 Strings

Python `str` is Unicode. `len` counts code points, not user-perceived grapheme clusters or UTF-8 bytes. `len("₹")=1`, while `len("₹".encode("utf-8"))=3`. Index/slice uses code points and half-open `[start:stop]`; negative indexes count from end.

Strings are immutable. Use f-strings for formatting trusted templates: `f"claim={claim_id} amount={amount}"`. Do not construct SQL with f-strings; use driver parameters. Normalize/compare user identifiers according to domain, not arbitrary `.lower()`.

### 2.3 Lists, tuples, dictionaries, and sets at first use

```python
amounts = [129_900, 49_900]
claim = ("C-1", 129_900)          # tuple record-like pair
by_id = {"C-1": 129_900}
seen = {"C-1", "C-2"}
```

List preserves order and permits duplicates. Tuple is immutable sequence. Dict maps unique hashable keys and preserves insertion order as language guarantee in current Python. Set stores distinct hashable elements and is unordered for semantic purposes. Do not rely on stable set iteration.

### 2.4 Conditions and None

```python
if consent is None:
    return "UNKNOWN"
if not consent:
    return "DENIED"
return "ALLOWED"
```

This distinguishes missing from false. `if not consent` alone merges them. In healthcare/fintech, unknown and denied/zero are often distinct.

### 2.5 Iteration tools

Use `enumerate(items, start=0)` for index+value and `zip(a,b, strict=True)` in modern Python when equal lengths are required. Ordinary zip truncates to shorter silently. `reversed` and `sorted` return iteration/new list respectively; list `.sort()` mutates and returns `None`.

```python
for index, amount in enumerate(amounts):
    print(index, amount)
```

Avoid `range(len(items))` unless index is genuinely needed for mutation/neighbors.

### 2.6 Function parameter rules

```python
def create_claim(patient_id: str, amount_paise: int, *, currency: str = "INR") -> dict:
    if amount_paise <= 0:
        raise ValueError("amount must be positive")
    return {"patientId": patient_id, "amountPaise": amount_paise, "currency": currency}
```

`*` makes currency keyword-only: `create_claim("P1",129900,currency="INR")`, reducing swapped arguments. Type annotations help tools but runtime still accepts wrong types unless code/library validates.

### 2.7 Mutable default repair

Bad:

```python
def record(value, history=[]):
    history.append(value)
    return history
```

Calls share one list. Correct:

```python
def record(value, history=None):
    if history is None:
        history = []
    history.append(value)
    return history
```

If the caller supplies a list, this intentionally mutates it; document or copy `list(history)` for pure behavior.

### 2.8 Exceptions and cleanup

```python
try:
    amount = int(raw_amount)
except ValueError as exc:
    raise ValueError("amount must be a base-10 integer") from exc
else:
    validate_amount(amount)
finally:
    metrics.increment("parse_attempt")
```

Do not catch around more code than necessary; otherwise unrelated `ValueError` is mislabeled. `finally` should not return because it can suppress exceptions/returns.

### 2.9 Read CSV safely

```python
import csv
from pathlib import Path

with Path("claims.csv").open(encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    required = {"claim_id", "amount_paise"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("missing columns")
    for line_no, row in enumerate(reader, start=2):
        try:
            amount = int(row["amount_paise"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid amount at line {line_no}") from exc
```

The csv module handles quoted commas/newlines. Spreadsheet exports can contain formula injection when later opened; data pipelines must escape/policy output appropriately.

### 2.10 Debug

Read the traceback from final exception upward: type/message, failing line, call stack. Reproduce with smallest input. Use `breakpoint()`/`pdb`, logging with safe context, and assertions/tests for invariants. `print` is fine for a tiny local experiment but structured logging and regression tests persist.

Run warnings and static tools in development. Avoid debugging by catching all exceptions or mutating production data interactively.

## 3. WORKED PROBLEMS

### Problem 1 — Name aliasing (easy)

`a=[1]; b=a; b.append(2)`. What is a?

**Solution.** `[1,2]`; both names reference same mutable list.

**Trap:** assuming assignment copies.

### Problem 2 — Division (easy)

Evaluate `5/2`, `5//2`, `-5//2`, `-5%2`.

**Solution.** 2.5, 2, -3, 1. Floor division rounds down and remainder satisfies `a=(a//b)*b+a%b`.

**Trap:** importing Java truncation-toward-zero intuition.

### Problem 3 — Range boundary (easy)

Values from `range(2,10,3)`.

**Solution.** 2,5,8; stop 10 excluded.

**Trap:** including 11/10 or miscounting step.

### Problem 4 — Identity versus equality (medium)

Should strings be compared with `is`?

**Solution.** No. `==` compares value; `is` identity may appear to work due to interning but is not the contract. Use `is None` for singleton sentinel.

**Trap:** tests pass on short literals and fail on runtime input.

### Problem 5 — Mutable default (medium)

Why does `append_claim("C1")`, then `append_claim("C2")` return both in second call?

**Solution.** Default list was created once at function definition and reused. Use `None` then allocate each call.

**Trap:** clearing list at return, which retains brittle shared state.

### Problem 6 — zip truncation (medium)

IDs length 3, amounts length 2, ordinary zip. How many pairs?

**Solution.** Two; third ID silently ignored. Use `zip(ids,amounts,strict=True)` to raise when equality is invariant.

**Trap:** believing zip validates equal lengths.

### Problem 7 — Float money (hard)

Why can `0.1+0.2==0.3` be false?

**Solution.** Binary64 cannot exactly encode most decimal fractions; operations round. Use integer minor units or `Decimal` constructed from strings with explicit rounding/context for financial rules.

**Trap:** `Decimal(0.1)`, which imports float approximation; use `Decimal("0.1")`.

### Problem 8 — Exception scope (hard)

`try: parse(); save(); except ValueError: invalid input`. Problem?

**Solution.** `save` may raise ValueError for unrelated bug/data, mislabeled as input. Catch narrowly around parse, validate, then let/wrap persistence errors appropriately.

**Trap:** broad try block because exception type seems specific.

### Problem 9 — Unknown consent (hard)

`if not consent: deny` handles `None` and false alike. Is that okay?

**Solution.** Deny may be safe for access, but observability/audit/business state should distinguish unavailable/unknown from explicit denial. Use `is None` branch and approved failure workflow.

**Trap:** truthiness erasing domain states.

## 4. REAL-WORLD / APPLIED CONTEXT

### Python in ML pipelines

Python orchestrates feature transforms, training, evaluation, registry, and serving due to NumPy/pandas/scikit-learn/PyTorch ecosystems. Object mutability and notebook state can make experiments irreproducible; move production logic into importable tested modules with explicit inputs.

### Azure ML scripts

Azure ML jobs run Python entry scripts in versioned environments with mounted/downloaded data and outputs. Environment/dependency/code/data identities must be recorded. A local `pip install` or implicit current directory makes remote failure likely.

### FastAPI

FastAPI uses Python annotations and Pydantic models to describe API data, validation, and docs. Annotations are metadata; Pydantic performs runtime validation. Async endpoints require knowing which calls block—covered later.

## 5. COMPARISON TABLE

| Type | Ordered | Mutable | Duplicates | Access | Common use |
|---|---|---|---|---|---|
| `list` | Yes | Yes | Yes | Index O(1) | Sequence/batch |
| `tuple` | Yes | No | Yes | Index O(1) | Fixed record/key if hashable |
| `dict` | Insertion | Yes | Keys unique | Avg key O(1) | Mapping/JSON-like object |
| `set` | No semantic order | Yes | No | Avg membership O(1) | Dedup/membership |
| `frozenset` | No semantic order | No | No | Avg membership O(1) | Immutable set/key |
| `str` | Code-point sequence | No | Yes | Index/slice | Unicode text |
| `bytes` | Byte sequence | No | Yes | Integer/slice | Binary/wire data |
| `float` | n/a | immutable | n/a | binary64 approx | Scientific approximate values |
| `Decimal` | n/a | immutable | n/a | decimal context | Explicit decimal rules |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. **Assignment copies objects.** It binds another name.
2. **`is` compares values.** It compares identity.
3. **Tuple is deeply immutable.** It can contain mutable objects.
4. **Annotations enforce runtime types.** Tools/libraries may, language generally does not.
5. **`//` truncates toward zero.** It floors.
6. **Truthiness preserves absent versus empty/zero.** It merges them.
7. **Mutable default is created per call.** It is created at definition.
8. **zip checks lengths.** Ordinary zip truncates.
9. **List sort returns sorted list.** `.sort()` mutates and returns None; `sorted` returns list.
10. **Float is exact decimal.** Use minor units/Decimal.
11. **Catch Exception and continue improves robustness.** It hides failures/corrupts meaning.
12. **Import only declares names.** It executes module top-level code.

## 7. CHEAT SHEET — REVIEW ONLY

Review only; not a substitute for the lesson.

- Python names bind objects; assignment does not copy.
- `==` value, `is` identity; use `is None`.
- Mutable: list/dict/set; immutable: int/str/tuple container.
- `/` true division; `//` floor; `**` exponent.
- Blocks use indentation; range stop excluded.
- Iterate directly; enumerate for index; strict zip for equal-length invariant.
- Function receives shared object reference; mutation visible, rebinding local.
- Mutable defaults persist—use None sentinel.
- Type hints aid tools; runtime validation separate.
- Catch only exceptions you can handle and preserve causes.
- `with` manages resources; specify text encoding.
- Float is approximate; money uses minor units/Decimal rules.

## 8. PRACTICE SET FOR SELF-TEST

1. Predict `a={"x":[]}; b=a.copy(); b["x"].append(1); print(a)`.
2. Evaluate `7//3`, `-7//3`, `-7%3`.
3. List `range(10,2,-3)`.
4. Distinguish false, zero, empty string, and None in validation.
5. Write a keyword-only `currency` parameter.
6. Explain why `list.sort()` assigned to a variable yields None.
7. Repair a mutable dict default argument.
8. Read a UTF-8 file while guaranteeing close on exception.
9. Choose exception for positive integer receiving `-1`.
10. Explain why request ID should not be a global mutable variable in a server.

## 9. CURATED RESOURCES

- Python 3 official tutorial, Chapters 3–9 — authoritative informal introduction to control flow, data structures, modules, I/O, errors, classes.
- Python Language Reference, “Data model,” “Execution model,” “Expressions,” “Simple/compound statements,” and “Import system” — exact identity, mutability, scope, operators, calls, and import semantics.
- Python Standard Library docs for `pathlib`, `csv`, `json`, `decimal`, `logging`, and `pdb` — production-ready basics beyond hand-written parsing.
- Luciano Ramalho, *Fluent Python*, 2nd ed., Chapters 1–3, 6, and 7 — Pythonic data model, sequences, mappings, sets, and function object semantics.
- Brett Slatkin, *Effective Python*, 2nd ed., Items 1–31 — concise idioms and failure-prone language mechanics.
- PEP 8, “Style Guide for Python Code,” and PEP 257, “Docstring Conventions” — canonical style/documentation conventions.
- David Beazley, *Python Distilled*, Chapters 1–5 — compact but rigorous language, functions, objects, modules, and exceptions.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Programming Logic and Debugging:** language-independent state, control, contracts, and tests.
2. **Java Language Model:** useful contrast for names, objects, typing, equality, exceptions, and GC.

### After

1. **Python Collections, Functions, and OOP:** deepens containers, iteration, call behavior, classes, protocols, and contexts.
2. **Python Tooling/Testing/Data:** makes programs reproducible and testable.
3. **Production Python:** deepens runtime, typing, concurrency, packaging, and security.
4. **FastAPI:** applies functions, annotations, exceptions, and async to services.
5. **ML Fundamentals:** uses Python/Numeric ecosystem for models and evaluation.

---ANSWER KEY BELOW---

1. `{'x':[1]}` because shallow copy shares nested list.
2. 2, -3, 2.
3. 10,7,4.
4. Use explicit domain checks (`is None`, type/range, `==""`) rather than one truthiness branch when meanings differ.
5. `def f(amount: int, *, currency: str = "INR"):`.
6. In-place mutation methods conventionally return None to prevent confusion; use `sorted(x)` for new list.
7. `def f(options=None): options={} if options is None else options` (copy if no mutation promised).
8. `with open(path,"r",encoding="utf-8") as f: ...`.
9. `ValueError` when type int is correct but value violates range.
10. Concurrent requests overwrite/shared state and leak context; pass explicitly or use scoped context mechanisms.
