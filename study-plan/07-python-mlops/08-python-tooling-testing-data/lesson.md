# Python Tooling, Testing, Packaging, and Data Handling from Scratch

Parent subject: `07-python-mlops`
Study time: 3–4 hours
Target: senior backend / AI platform / MLOps interviews

## 1. FOUNDATIONS

### A script is not yet a reproducible project

A Python file may run on one laptop because of an unrecorded interpreter, globally installed libraries, current directory, environment variables, cached data, and IDE behavior. Production and ML work requires an explicit project: source layout, declared build metadata, isolated environment, resolved dependencies, tests, static checks, structured logs, data contracts, and repeatable commands.

Python's packaging history includes distutils, setuptools, eggs, wheels, virtual environments, pip, and modern standardized `pyproject.toml` build interfaces. Multiple tools remain, but the underlying concepts are stable: declare project metadata/dependencies, build standard artifacts, install into isolated environments, lock deployments as policy requires, and record provenance.

### Interpreter and environment

An interpreter has a version and implementation, such as CPython 3.13. A **virtual environment** creates an isolated interpreter environment with its own installed distributions and scripts while referencing a base interpreter. It prevents project A's library versions from silently modifying project B.

Create with `python3 -m venv .venv`; activate for convenience, or call `.venv/bin/python` explicitly. Activation mostly changes PATH; it is not container/security isolation. Never commit `.venv`. Record supported Python versions in project metadata and CI.

### Distribution package versus import package

A **distribution package** is installed artifact/metadata known to package managers, e.g. `scikit-learn`; an **import package** is Python namespace, e.g. `sklearn`. Names can differ. A wheel (`.whl`) is a built distribution with files/metadata; a source distribution (`sdist`) contains source for a build. Wheels avoid compiling at install time and can be platform-specific when native code exists.

An importable package should not depend on repository current directory accidentally. A `src/` layout places packages under `src`, encouraging tests to use the installed package rather than an uninstalled working copy.

### `pyproject.toml`

`pyproject.toml` centralizes build-system requirements and standardized project metadata (PEP 517/518/621), and many tools place configuration there.

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "claims-ml"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = ["numpy>=2.0,<3", "pandas>=2.2,<3"]

[project.optional-dependencies]
test = ["pytest>=8,<9", "mypy>=1.11,<2", "ruff>=0.6,<1"]
```

Broad compatible ranges help reusable libraries; applications commonly lock a fully resolved transitive environment for deployment. A lock records exact versions/hashes/tool resolution, but the standard/tool varies (`pip-tools`, uv, Poetry, PDM). Do not handwave: CI must recreate and verify the chosen lock.

### Dependencies and supply chain

Direct dependencies are declared; transitive dependencies arrive through them. Pinning only direct packages does not fix transitive versions. Floating latest makes rebuilds change; exact forever blocks security/compatibility updates. Use automated update proposals, tests, vulnerability/license policy, artifact hashes/signatures/provenance, and regular refresh.

Dependency confusion and typosquatting exploit package names/index priority. Configure approved indexes, authentication, internal namespace, hashes where applicable, and never install random packages to solve an import error. Native wheels execute compiled code and have platform/ABI constraints.

### Project layout and imports

Typical:

```text
claims-ml/
  pyproject.toml
  src/claims_ml/__init__.py
  src/claims_ml/features.py
  tests/test_features.py
  README.md
```

Install editable for development (`python -m pip install -e '.[test]'`) so imports resolve through package metadata. Editable install reflects source changes and is not a production artifact. Build a wheel once and promote it or a container containing it.

### Formatting, linting, and static typing

A formatter makes style deterministic. A linter detects unused imports, suspicious constructs, complexity, and style. Ruff can lint/format many rules quickly; Black is another formatter. Static type checkers such as mypy or Pyright analyze annotations without executing code.

Typing catches incompatible calls, missing Optional handling, and interface drift, but not business validity, runtime input, data distributions, or all dynamic behavior. Gradually type public boundaries and core domain logic; use `Any` deliberately rather than allowing it to silently erase checks.

Useful types include `list[str]`, `dict[str,int]`, `str | None`, `Literal`, `TypedDict`, dataclass, `Protocol`, generics, and `TypeVar`. Runtime validation belongs to parsers/models such as Pydantic, dataclasses with checks, JSON Schema, or explicit code.

### Testing levels

A **unit test** isolates a small behavior. An **integration test** verifies collaboration with real boundaries such as PostgreSQL or filesystem. A **contract test** verifies producer/consumer/API compatibility. An **end-to-end test** exercises a user path. A **property-based test** generates many cases around invariants. A **performance test** measures throughput/latency/resources. ML adds data validation, leakage checks, metric thresholds, robustness/fairness, and reproducibility tests.

Testing pyramid is guidance, not fixed counts: many fast deterministic tests, fewer boundary tests, targeted end-to-end. Mocking every collaborator can test an imaginary system; use fakes for controlled behavior and real integration for semantics.

### pytest mechanics

pytest discovers functions/classes/files by conventions, uses plain `assert`, fixtures for setup/teardown, parametrization for cases, markers for categories, and plugins. Fixtures have scopes and dependency graphs. Keep fixtures explicit, small, and immutable where possible; broad session fixtures create order coupling.

A test should arrange, act, assert, and communicate one behavior. Verify public outcome, not private implementation. Include happy path, empty, boundaries, invalid input, exceptions, duplicates, time, and concurrency when relevant.

### Determinism and test isolation

Tests must control time, randomness, environment, locale/timezone, network, filesystem, and shared state. Seeded randomness improves repeatability but a seed alone does not guarantee results across library/hardware/version changes. Record versions and test tolerances based on numerical/domain requirements.

Use temporary directories/databases, rollback transactions, unique IDs, and dependency injection. Never point tests at production. Parallel tests expose hidden global state and port conflicts; design isolation rather than disabling parallelism permanently.

### Logging

Use Python `logging` or structured logging facade rather than print in services. Configure at application entry, not libraries. Libraries emit through named loggers and do not add global handlers. Stable fields include event name, service/version, safe request/trace ID, outcome, duration, bounded error code. Exceptions can be logged with stack once at handling boundary.

Do not interpolate expensive/sensitive values blindly. Standard logging parameterization `logger.info("claim processed id=%s", safe_id)` defers formatting. Redaction and access controls do not make raw secrets acceptable.

### JSON and data contracts

JSON supports object, array, string, number, boolean, and null. It has no timestamp, decimal, bytes, NaN, tuple, or integer-width type. Define encoding: ISO-8601 UTC timestamp, decimal string/minor units, base64 bytes where justified, reject nonfinite floats. Python's json encoder may accept NaN by default even though interoperable strict JSON should reject it with `allow_nan=False`.

Schemas define required fields, types, ranges, formats, enums, additional fields, and versions. Validate before training/processing and distinguish missing from null. Canonicalization matters for hashes/signatures; ordinary JSON key order/whitespace is not a universal canonical form.

### CSV

CSV has dialects: delimiter, quote, escape, newline, encoding, headers. Use `csv` module and `newline=""`. It lacks types/schema; `"00123"` may be identifier not integer. Spreadsheet formula injection occurs when cells beginning `= + - @` are opened in office software; exporting untrusted data needs policy.

### NumPy foundations

NumPy's `ndarray` is a typed, n-dimensional, usually homogeneous array with shape, dtype, strides, and contiguous/shared memory. Vectorized operations execute loops in optimized native code and avoid Python object overhead. A million Python integers are objects/references with large overhead; a NumPy `int64` array stores about 8 MB of raw values.

Broadcasting aligns shapes from trailing dimensions; dimensions are compatible if equal or one. It can avoid copies but accidental shape expansion produces wrong results or huge temporaries. Views share data; basic slicing often returns a view, while advanced indexing often copies. Dtype overflow is fixed-width: NumPy int32 can overflow unlike Python int.

### pandas foundations

A `Series` is labeled one-dimensional data; `DataFrame` is tabular columns with index and potentially different dtypes. pandas aligns operations by labels, not just position. This is powerful and surprising: adding Series with different indexes produces union with missing values.

Use vectorized column operations, explicit dtypes, parse dates, validate keys/cardinality, and avoid row-wise `apply` for operations expressible natively. Joins can multiply rows; validate one-to-one/many-to-one expectations. Missing values vary by dtype (`NaN`, `NaT`, `pd.NA`, None), and equality/filter semantics require care.

For large data, select columns, filter early, read chunks, use Parquet/Arrow for typed columnar storage, and move computation to database/distributed engine when appropriate. pandas is memory-resident and often needs multiple times raw file size.

## 2. CORE MECHANICS

### 2.1 Create and verify an environment

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -c 'import sys; print(sys.executable, sys.version)'
```

Use `python -m pip` to ensure pip belongs to intended interpreter. Capture `pip list`, `pip check`, lock sync, and wheel build in CI. Avoid `sudo pip install` and global mutation.

### 2.2 Build and inspect artifact

With build tool installed:

```bash
python -m build
python -m zipfile -l dist/claims_ml-0.1.0-py3-none-any.whl
```

Test installation into a fresh environment, import, metadata/version, entry point, and smoke behavior. `py3-none-any` means Python 3, no ABI/platform-specific binary; native packages have platform tags. Do not upload secrets/test data accidentally; define included files.

### 2.3 Write tests

```python
import pytest

@pytest.mark.parametrize("raw, expected", [("129900",129900),("0",0)])
def test_parse_amount(raw, expected):
    assert parse_amount(raw) == expected

@pytest.mark.parametrize("raw", ["", "12.5", "-1", None])
def test_parse_amount_rejects(raw):
    with pytest.raises((TypeError, ValueError)):
        parse_amount(raw)
```

Do not accept multiple exception types unless contract truly permits both; stronger tests specify exact error and safe code/message.

### 2.4 Test boundaries with standard library

Use `tempfile.TemporaryDirectory`, `unittest.mock` selectively, `subprocess.run(...,check=True,capture_output=True,text=True,timeout=...)`, and local ephemeral servers/databases. Avoid shell=True with untrusted strings. Assert exit status, stdout/stderr contract, generated files, and cleanup.

### 2.5 Type a data boundary

```python
from typing import TypedDict, NotRequired

class ClaimPayload(TypedDict):
    claim_id: str
    amount_paise: int
    reason: NotRequired[str]
```

TypedDict is static shape; runtime dict remains ordinary and may contain bad data. Parse JSON into validated domain object before core logic. Keep `dict[str, object]` at raw boundary, not throughout the program.

### 2.6 Structured JSON

```python
json.dumps(record, ensure_ascii=False, allow_nan=False,
           separators=(",", ":"), sort_keys=True)
```

This deterministic representation helps tests, but is not necessarily a formal canonical JSON signature format. On read, impose byte/depth/field limits at server layer, validate type, and reject duplicate-key ambiguity if security protocol requires a parser that detects it.

### 2.7 NumPy shape/dtype

```python
import numpy as np
x = np.array([[1.,2.,3.],[4.,5.,6.]], dtype=np.float32) # shape (2,3)
mean = x.mean(axis=0)                                   # shape (3,)
centered = x - mean                                     # broadcasting
```

Memory x is 2×3×4=24 bytes payload. `axis=0` aggregates rows per feature. Omitting axis produces scalar. Verify shapes with assertions at ML boundaries. Use float64 for numerically sensitive work where cost allows; float32 for many ML operations; never choose blindly.

### 2.8 Numerical comparisons

Use `math.isclose`/`numpy.allclose` with justified relative and absolute tolerance, not exact floats. Near zero, absolute tolerance matters. A tolerance of 0.01 is unacceptable for a probability threshold decision if it can flip thousands of approvals; connect tolerance to domain.

### 2.9 pandas merge validation

```python
features.merge(labels, on="claim_id", how="left", validate="one_to_one", indicator=True)
```

Inspect `_merge` for missing labels and duplicate violations. For feature joins include entity and point-in-time condition; ordinary merge by ID can leak future data. Record row counts, key uniqueness, null rates, schema, min/max timestamps before/after.

### 2.10 Reproducibility manifest

Record source commit, dirty status, built artifact digest, Python implementation/version, OS/container digest, exact dependencies/lock hash, command/config, random seeds, dataset/feature snapshot and schema, model hyperparameters/code, hardware, outputs/checksums, metrics, and timestamp/owner. A seed alone is not reproducibility.

## 3. WORKED PROBLEMS

### Problem 1 — Virtual environment (easy)

Why does activation not isolate OS files/processes?

**Solution.** It primarily adjusts interpreter/package paths; it is dependency isolation, not container/sandbox.

**Trap:** treating venv as security boundary.

### Problem 2 — Import/distribution names (easy)

Why can `pip install scikit-learn` lead to `import sklearn`?

**Solution.** Distribution and import package names are distinct metadata/namespaces.

**Trap:** installing an unrelated package named `sklearn` from an index blindly.

### Problem 3 — Test a clock (easy)

How test expiration without sleeping?

**Solution.** Inject clock/current instant into function/object; use fixed fake and boundary instants.

**Trap:** `time.sleep`, making slow/flaky tests.

### Problem 4 — Cardinality join (medium)

Features has duplicate claim C1 twice; labels C1 twice. Merge rows?

**Solution.** Four C1 combinations (many-to-many). Validate intended cardinality and deduplicate/fix source with explicit rule.

**Trap:** assuming two rows result.

### Problem 5 — JSON NaN (medium)

Can standard interoperable JSON contain NaN?

**Solution.** No under JSON grammar. Python encoder may emit it by default; use allow_nan=False and define missing/nonfinite policy.

**Trap:** library permissiveness treated as standard contract.

### Problem 6 — NumPy overflow (medium)

`np.int32(2_000_000_000)+np.int32(2_000_000_000)`?

**Solution.** Fixed-width overflow/wrap behavior with warning/version nuances, not Python 4 billion. Use suitable dtype and overflow checks.

**Trap:** importing arbitrary-precision Python int semantics.

### Problem 7 — Series alignment (hard)

Series A index `[x,y]`, B `[y,z]`; add.

**Solution.** Result indexes x,y,z; only y has both and sums; x/z missing (NaN/NA). Use positional arrays only when intended or align/validate indexes.

**Trap:** assuming first elements add.

### Problem 8 — Mock overload (hard)

All DB tests use mocks returning expected dicts. Risk?

**Solution.** Miss SQL syntax, transaction/isolation, driver types, null/timezone, constraints, and schema drift. Keep unit tests but add real disposable PostgreSQL integration/migration tests.

**Trap:** calling 100% coverage proof of integration correctness.

### Problem 9 — Reproducible model (hard)

Same seed yields different GPU results. Why?

**Solution.** Library/kernel/version, nondeterministic algorithms, parallel reduction order, hardware, data order, preprocessing, and environment differ. Enable documented deterministic modes where needed, record environment, define tolerance and verify.

**Trap:** seed as complete reproducibility.

## 4. REAL-WORLD / APPLIED CONTEXT

### scikit-learn pipelines

Pipelines compose preprocessing and estimators so transformations fit only on training folds, reducing leakage. Persist pipeline plus library versions/schema and test inference feature shape. Pickle/joblib loading executes trusted Python object reconstruction and must not consume untrusted artifacts.

### MLflow/Azure ML environments

Experiment systems record parameters, metrics, artifacts, environments, and lineage. Their records are only as complete as inputs supplied. Mutable datasets or `latest` model names undermine reproducibility; record immutable versions/digests.

### Apache Arrow/Parquet

Arrow provides a columnar in-memory format; Parquet is columnar storage with typed schema/compression/statistics. pandas can use them to preserve types and read selected columns, unlike CSV's text-only ambiguity. Schema evolution and timezone/decimal compatibility still need testing.

## 5. COMPARISON TABLE

| Tool/concept | Purpose | Strength | Limitation |
|---|---|---|---|
| venv | dependency environment | built-in/simple | no lock/security isolation |
| wheel | install artifact | fast/reproducible input | platform variants/native trust |
| lockfile | exact resolution | repeat deployment | tool/platform/update policy |
| Ruff | lint/format | fast broad rules | static heuristics |
| mypy/Pyright | type analysis | boundary/interface errors | runtime/data semantics remain |
| pytest | tests/fixtures | concise ecosystem | plugin/fixture complexity |
| mock | controlled interaction | fast fault injection | imaginary behavior risk |
| integration test | real boundary | semantic confidence | slower/environment cost |
| NumPy | homogeneous arrays | vectorized/memory efficient | dtype/shape/view pitfalls |
| pandas | labeled tables | rich analysis/joins | memory/cardinality/alignment pitfalls |
| CSV | interoperable text | ubiquitous | no types/schema/dialect ambiguity |
| Parquet | typed columnar | compression/selective reads | tooling/schema evolution |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. venv reproduces dependencies—it only isolates installed state.
2. `pip freeze` is always a designed lock—it may include incidental packages and lacks policy context.
3. Direct pins fix transitives—not without full resolution.
4. Editable install is production artifact—it points to mutable source.
5. Type hints validate JSON—they do not by themselves.
6. High coverage means strong tests—assertions/boundaries/integration matter.
7. Mocking every dependency increases realism—it can decrease it.
8. Seed guarantees reproducibility—environment/algorithms/data also matter.
9. JSON supports datetime/decimal/NaN—it requires encoding contracts.
10. CSV is a typed table—it is text with dialect.
11. NumPy behaves like Python numbers—fixed dtypes overflow and broadcast.
12. pandas join preserves row count—many-to-many multiplies.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- Use `python -m venv`; `python -m pip` for intended interpreter.
- `pyproject.toml` declares build/project/tool metadata.
- Distribution name can differ from import name.
- Build wheel once; test fresh install; promote digest.
- Lock exact app environment; automate reviewed updates.
- Formatter/linter/type checker/test solve different problems.
- Inject time/random/network; tests must be isolated/deterministic.
- Runtime data validation separate from type hints.
- Strict JSON: reject NaN, define time/decimal/bytes.
- NumPy: shape + dtype + strides/views; broadcasting needs assertions.
- pandas aligns labels; validate merge cardinality and row counts.
- Reproducibility = code+artifact+env+deps+data+config+seed+hardware+outputs.

## 8. PRACTICE SET FOR SELF-TEST

1. Explain why `pip` and `python` can target different environments.
2. Distinguish wheel, sdist, import package, distribution.
3. Design a `src` project tree with tests.
4. Name five boundary cases for amount parser.
5. Explain static typing versus runtime Pydantic validation.
6. Compute memory payload for shape `(1_000_000,32)` float32.
7. Determine broadcast result shape `(1000,1)+(1,512)`.
8. Explain basic-slice view mutation risk.
9. Validate a many-to-one pandas feature lookup.
10. List a model reproducibility manifest.

## 9. CURATED RESOURCES

- Python Packaging User Guide, “Installing packages,” “Packaging Python Projects,” and `pyproject.toml` specifications — official environment/build/distribution workflow.
- PEP 517, 518, 621, 660, and 440 — primary build backend, metadata, editable install, and version specifier standards.
- pytest official documentation, “Getting Started,” fixtures, parametrization, monkeypatch, and good practices — exact test mechanics.
- mypy documentation, “Getting started,” kinds of types, protocols, generics, and configuration — practical static typing; compare Pyright docs if used by team.
- NumPy official “Absolute basics,” “Broadcasting,” “Copies and views,” and dtype reference — authoritative array semantics.
- pandas official “10 minutes to pandas,” indexing, missing data, merge, groupby, IO, and scaling guides — core DataFrame behavior and pitfalls.
- Hynek Schlawack, “Testing & Packaging” articles and PyPA guidance — modern src layouts and testing installed artifacts.
- David Sculley et al., “Hidden Technical Debt in Machine Learning Systems,” 2015 — why data/dependency/testing/reproducibility tooling is central ML engineering.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Python Fundamentals:** language execution, modules, files, exceptions.
2. **Collections/Functions/OOP:** package code structure and testable abstractions.
3. **Git/CI:** versioned source and automated checks.

### After

1. **Mathematics/Statistics for ML:** uses NumPy/pandas for quantitative work.
2. **Production Python:** deepens packaging, types, runtime, concurrency, security.
3. **ML Fundamentals:** uses pipelines, tests, data contracts, array/table mechanics.
4. **ML Lifecycle:** records environments, lineage, artifacts, validation and promotion.
5. **FastAPI:** packages/validates/tests services and structured logs.

---ANSWER KEY BELOW---

1. PATH/shell resolution can select different executables; use intended interpreter's `-m pip` and inspect `sys.executable`.
2. Wheel built install artifact; sdist build source; import package Python namespace; distribution package installer metadata/artifact.
3. `pyproject.toml`, `src/name/__init__.py`+modules, `tests/test_*.py`, README/lock/config.
4. Empty, null/wrong type, zero, negative, maximum/external overflow, decimal string, whitespace/leading zeros (any five with contract).
5. Checker analyzes annotated code before run; Pydantic parses/validates actual runtime input per model.
6. 32,000,000×4=128,000,000 bytes≈122.07 MiB payload.
7. `(1000,512)`.
8. Basic slice may share original buffer; writing slice changes original. Copy explicitly when isolation required.
9. Use `merge(...,validate="many_to_one")`, assert key uniqueness on lookup, indicator/missing rates and row count.
10. Source/dirty, artifact digest, interpreter/OS/container, exact deps, command/config/seed, immutable data/schema/features, hardware, outputs/checksums, metrics/time/owner.
