# Repository Validation Record

Originally validated on 2026-08-09 and revalidated after the Java/Spring prerequisite expansion on 2026-08-12 in the local macOS arm64 workspace.

## Curriculum contract

Run from `study-plan/`:

```bash
python3 validate_curriculum.py
```

Verified result: **8 parent directories, 47 child lessons, 176,038 lesson words and 8 parent capstones**. Parent 02 now includes seven prerequisite lessons before its five existing advanced lessons. Every lesson has sections 1–10 in order, at least eight worked problems, 6–10 self-test questions, curated resources, at least three bridge entries, exactly one final answer-key marker, at least 2,500 words and valid local Markdown links. No parent tracker remains pending or in progress.

## Executable evidence

- OpenJDK 25 compiled every Java source into temporary directories. All 12 Java/Spring policy/lab programs executed successfully during the 2026-08-12 expansion; the full earlier Java audit remains recorded. The minimal `HelloServer` compiled successfully but socket binding is prohibited by this sandbox.
- CPython tests: **85 tests passed** across identity/networking, SRE, production Python, FastAPI, ML fundamentals/lifecycle/serving and all Parent 08 labs; rerun on 2026-08-12.
- FastAPI was tested in the isolated environment containing FastAPI 0.138.2 and Pydantic 2.13.4. Five tests passed; Starlette emitted its documented TestClient/httpx deprecation warning.
- Terraform 1.11.4: `terraform fmt -check` and `terraform validate` passed.
- Supply-chain shell lab accepted the exact SHA-256 artifact and rejected tampering.
- Container Dockerfile and Kubernetes workload policy programs passed.
- All five JSON artifacts parsed successfully; both YAML artifacts parsed successfully.

## Cleanliness

Generated Java `.class`, Python `.pyc` and empty `__pycache__` directories were removed after validation. Terraform provider/cache directories are absent. Source code, data fixtures and lesson artifacts remain.

## Interpretation

These checks prove repository structure, local examples and declared fixtures. They do not turn educational examples into production certification, legal advice or universal performance benchmarks. Every lesson labels environment-specific measurements and points to primary sources for version-sensitive claims.
