#!/usr/bin/env bash
set -euo pipefail

lab_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT

printf '%s\n' 'patient-risk-service release 2026.08.09 commit 9f31c2a' > "$work_dir/app.jar"
digest=$(shasum -a 256 "$work_dir/app.jar" | awk '{print $1}')
printf '%s  %s\n' "$digest" app.jar > "$work_dir/SHA256SUMS"

bash "$lab_dir/release-policy.sh" "$work_dir/app.jar" "$work_dir/SHA256SUMS" "$digest"

printf '%s\n' 'tampered' >> "$work_dir/app.jar"
if bash "$lab_dir/release-policy.sh" "$work_dir/app.jar" "$work_dir/SHA256SUMS" "$digest" >/dev/null 2>&1; then
  echo "FAIL: tampered artifact was accepted" >&2
  exit 1
fi

echo "PASS: exact artifact accepted and tampering rejected"
