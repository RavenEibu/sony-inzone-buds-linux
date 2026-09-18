#!/usr/bin/env bash
# Run every test. CI uses this same entry point.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

for test in tests/test_*.sh; do
  printf '== %s\n' "$test"
  "$test"
done

for test in tests/test_*.py; do
  printf '== %s\n' "$test"
  PYTHONDONTWRITEBYTECODE=1 python3 "$test"
done

printf 'All test suites passed.\n'
