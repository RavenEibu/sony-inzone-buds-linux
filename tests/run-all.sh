#!/usr/bin/env bash
# Run every test. CI uses this same entry point.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# Tests assert English text; never let the developer's language or an installed
# catalog change it. tests/test_i18n.py sets its own language explicitly.
export INZONE_LANGUAGE=en

for test in tests/test_*.sh; do
  printf '== %s\n' "$test"
  "$test"
done

for test in tests/test_*.py; do
  printf '== %s\n' "$test"
  PYTHONDONTWRITEBYTECODE=1 python3 "$test"
done

printf 'All test suites passed.\n'
