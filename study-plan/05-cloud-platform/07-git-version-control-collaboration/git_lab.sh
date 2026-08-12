#!/usr/bin/env bash
set -Eeuo pipefail

lab=$(mktemp -d)
trap 'rm -rf -- "$lab"' EXIT
repo="$lab/repo"
mkdir "$repo"
git -C "$repo" init -q
git -C "$repo" config user.name 'Study User'
git -C "$repo" config user.email 'study@example.invalid'

printf 'base\n' >"$repo/service.txt"
git -C "$repo" add service.txt
git -C "$repo" commit -qm 'Create service baseline'
base=$(git -C "$repo" rev-parse HEAD)

git -C "$repo" switch -qc feature
printf 'feature\n' >>"$repo/service.txt"
git -C "$repo" add service.txt
git -C "$repo" commit -qm 'Add feature behavior'
feature=$(git -C "$repo" rev-parse HEAD)

git -C "$repo" switch -q master 2>/dev/null || git -C "$repo" switch -q main
printf 'operations\n' >"$repo/ops.txt"
git -C "$repo" add ops.txt
git -C "$repo" commit -qm 'Add operations note'
git -C "$repo" merge -q --no-ff feature -m 'Merge feature'
merge=$(git -C "$repo" rev-parse HEAD)

[[ $(git -C "$repo" rev-list --parents -n1 "$merge" | wc -w | tr -d ' ') == 3 ]]
git -C "$repo" merge-base --is-ancestor "$base" "$merge"
git -C "$repo" merge-base --is-ancestor "$feature" "$merge"

printf 'staged\n' >>"$repo/service.txt"
git -C "$repo" add service.txt
printf 'unstaged\n' >>"$repo/service.txt"
status=$(git -C "$repo" status --short service.txt)
[[ $status == MM* ]]
git -C "$repo" restore service.txt
git -C "$repo" restore --staged service.txt
[[ -z $(git -C "$repo" status --short) ]]

git -C "$repo" tag -a v1.0.0 -m 'Study release'
[[ $(git -C "$repo" rev-parse v1.0.0^{}) == "$merge" ]]
echo 'PASS: commits, branch DAG, two-parent merge, staging split, restore, and tag'
