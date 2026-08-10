"""Validate an immutable, auditable ML run manifest using only the stdlib."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
MUTABLE = re.compile(r"(?:^|[/@:])(latest|staging|production|champion)$", re.I)
SENSITIVE_KEYS = {"password", "secret", "token", "api_key", "ssn", "pan", "aadhaar"}


def _walk_sensitive(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized_parts = set(re.split(r"[^a-z0-9]+|_", key.lower()))
            if key.lower() in SENSITIVE_KEYS or normalized_parts & SENSITIVE_KEYS:
                errors.append(f"sensitive key must not be recorded: {child_path}")
            errors.extend(_walk_sensitive(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_walk_sensitive(child, f"{path}[{index}]"))
    return errors


def validate(manifest: dict[str, Any], base_dir: Path) -> list[str]:
    errors: list[str] = []
    required = {"run_id", "code_commit", "environment_digest", "dataset", "splits", "seed", "feature_schema", "metrics", "gates", "model", "approval"}
    missing = sorted(required - manifest.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return errors

    if not HEX40.fullmatch(str(manifest["code_commit"])):
        errors.append("code_commit must be a full 40-character lowercase Git SHA")
    if not SHA256.fullmatch(str(manifest["environment_digest"])):
        errors.append("environment_digest must be a SHA-256 digest")

    dataset = manifest["dataset"]
    if not isinstance(dataset, dict) or not SHA256.fullmatch(str(dataset.get("sha256", ""))):
        errors.append("dataset.sha256 must identify exact input bytes")
    if isinstance(dataset, dict) and MUTABLE.search(str(dataset.get("uri", ""))):
        errors.append("dataset.uri must not use a mutable alias")

    splits = manifest["splits"]
    expected = {"train", "validation", "test"}
    if not isinstance(splits, dict) or set(splits) != expected:
        errors.append("splits must contain exactly train, validation, and test")
    else:
        sets = {name: set(values) for name, values in splits.items()}
        for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
            overlap = sorted(sets[left] & sets[right])
            if overlap:
                errors.append(f"split leakage between {left} and {right}: {overlap}")
        if any(not values for values in sets.values()):
            errors.append("every split must be non-empty")

    model = manifest["model"]
    registry_uri = str(model.get("registry_uri", ""))
    if MUTABLE.search(registry_uri) or not re.fullmatch(r"models:/[^/]+/[1-9][0-9]*", registry_uri):
        errors.append("model.registry_uri must pin a numeric immutable version")
    artifact = (base_dir / str(model.get("artifact_path", ""))).resolve()
    try:
        artifact.relative_to(base_dir.resolve())
    except ValueError:
        errors.append("model.artifact_path escapes the manifest directory")
    else:
        if not artifact.is_file():
            errors.append("model artifact does not exist")
        else:
            actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if model.get("sha256") != actual:
                errors.append(f"model digest mismatch: expected {model.get('sha256')}, actual {actual}")

    metrics, gates = manifest["metrics"], manifest["gates"]
    comparisons = (
        ("test_auc", "min_test_auc", lambda actual, limit: actual >= limit),
        ("test_brier", "max_test_brier", lambda actual, limit: actual <= limit),
        ("fairness_tpr_gap", "max_fairness_tpr_gap", lambda actual, limit: actual <= limit),
    )
    for metric, gate, passes in comparisons:
        try:
            actual, limit = float(metrics[metric]), float(gates[gate])
            if not passes(actual, limit):
                errors.append(f"quality gate failed: {metric}={actual}, {gate}={limit}")
        except (KeyError, TypeError, ValueError):
            errors.append(f"missing or invalid metric/gate pair: {metric}/{gate}")

    approval = manifest["approval"]
    if approval.get("status") != "approved" or not approval.get("ticket"):
        errors.append("deployment requires approved status and a review ticket")
    errors.extend(_walk_sensitive(manifest))
    return errors


def main(argv: list[str]) -> int:
    path = Path(argv[1] if len(argv) > 1 else "run-manifest.json").resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(manifest, path.parent)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"VALID: {manifest['run_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
