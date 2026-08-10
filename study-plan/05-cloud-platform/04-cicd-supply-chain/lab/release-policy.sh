#!/usr/bin/env bash
set -euo pipefail

artifact=${1:?usage: release-policy.sh ARTIFACT CHECKSUMS EXPECTED_SHA256}
checksums=${2:?usage: release-policy.sh ARTIFACT CHECKSUMS EXPECTED_SHA256}
expected=${3:?usage: release-policy.sh ARTIFACT CHECKSUMS EXPECTED_SHA256}

actual=$(shasum -a 256 "$artifact" | awk '{print $1}')
recorded=$(awk -v name="$(basename "$artifact")" '$2 == name {print $1}' "$checksums")

[[ "$actual" =~ ^[0-9a-f]{64}$ ]] || { echo "invalid computed digest" >&2; exit 10; }
[[ "$recorded" == "$actual" ]] || { echo "checksum manifest mismatch" >&2; exit 11; }
[[ "$expected" == "$actual" ]] || { echo "deployment digest mismatch" >&2; exit 12; }

echo "verified sha256:$actual"
