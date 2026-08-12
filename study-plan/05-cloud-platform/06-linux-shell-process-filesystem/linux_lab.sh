#!/usr/bin/env bash
set -Eeuo pipefail

lab_dir=$(mktemp -d)
trap 'rm -rf -- "$lab_dir"' EXIT

mkdir -p "$lab_dir/run logs"
printf 'ok\nwarning\nok\n' >"$lab_dir/run logs/app one.log"
printf 'error\nok\n' >"$lab_dir/run logs/app two.log"
chmod 640 "$lab_dir/run logs/app one.log"

mode=$(stat -f '%Lp' "$lab_dir/run logs/app one.log" 2>/dev/null || stat -c '%a' "$lab_dir/run logs/app one.log")
[[ $mode == 640 ]]

file_count=0
line_count=0
while IFS= read -r -d '' file; do
  ((file_count += 1))
  lines=$(wc -l <"$file")
  ((line_count += lines))
done < <(find "$lab_dir/run logs" -maxdepth 1 -type f -name '*.log' -print0)

[[ $file_count == 2 ]]
[[ $line_count == 5 ]]

set +e
false | true
pipeline_status=$?
set -e
[[ $pipeline_status != 0 ]]

echo "PASS: quoted paths, modes, null-delimited traversal, cleanup, and pipefail"
