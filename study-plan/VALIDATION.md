# Repository Validation Record

Originally validated on 2026-08-09 and fully revalidated after the all-parent prerequisite expansion on 2026-08-12 in the local macOS arm64 workspace.

## Curriculum contract

Run from `study-plan/`:

```bash
python3 validate_curriculum.py
```

Validated result: **8 parent directories, 73 child lessons, 256,978 lesson words and 8 parent capstones**. All parents include explicit from-scratch prerequisite phases before their existing advanced lessons. Every lesson retains sections 1–10 in order, at least eight worked problems, 6–10 self-test questions, curated resources, at least three bridge entries, exactly one final answer-key marker, at least 2,500 words and valid local Markdown links.

## Executable evidence

- OpenJDK 25 compiled all **36 Java sources** into temporary directories. Every runnable class passed from its documented working directory; `HelloServer` was compile-checked without binding a sandboxed socket, and the source-only `CodingFoundations` utility has no entry point.
- CPython compiled the entire study plan. **85 existing unit tests passed**, the new tooling lesson's **3 internal unit tests passed**, both SQLite schema/query checks passed, and all **20 directly executable Python curriculum/validation programs passed**.
- FastAPI was tested in the isolated environment containing FastAPI 0.138.2 and Pydantic 2.13.4. Five tests passed; Starlette emitted its documented TestClient/httpx deprecation warning.
- Terraform 1.11.4: `terraform fmt -check` and `terraform validate` passed.
- Supply-chain shell lab accepted the exact SHA-256 artifact and rejected tampering.
- Container Dockerfile and Kubernetes workload policy programs passed.
- All five JSON artifacts parsed successfully. Both YAML artifacts parsed successfully with Ruby Psych, and the Kubernetes workload also passed its Java policy validator.

## Cleanliness

Generated Java `.class`, Python `.pyc` and empty `__pycache__` directories were removed after validation. Terraform provider/cache directories are absent. Source code, data fixtures and lesson artifacts remain.

## Interpretation

These checks prove repository structure, local examples and declared fixtures. They do not turn educational examples into production certification, legal advice or universal performance benchmarks. Every lesson labels environment-specific measurements and points to primary sources for version-sensitive claims.
