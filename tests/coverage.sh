#!/usr/bin/env bash
# Run the Python tests under coverage.py and report coverage of the mixer.
# Usage: tests/coverage.sh [--html]
# Needs `python3 -m coverage` (pip install coverage; with GTK tests the
# interpreter must also see PyGObject, e.g. a venv --system-site-packages).
# The window tests need a display (xvfb-run in CI); without one the figure is
# lower (about 44 %), so run with INZONE_COVERAGE_MIN=40 there. The threshold
# sits a little under the current figure (63 % with a display): raise it with
# the tests.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

THRESHOLD=${INZONE_COVERAGE_MIN:-55}
export INZONE_LANGUAGE=en
export COVERAGE_FILE=${COVERAGE_FILE:-$(mktemp -d)/.coverage}

python3 -m coverage --version >/dev/null 2>&1 || {
  printf 'coverage.py is not installed (pip install coverage)\n' >&2
  exit 1
}

for test in tests/test_*.py; do
  PYTHONDONTWRITEBYTECODE=1 python3 -m coverage run --parallel-mode \
    --source=src/inzone_buds_mixer --branch "$test" >/dev/null 2>&1 ||
    { printf 'FAIL: %s\n' "$test" >&2; exit 1; }
done

python3 -m coverage combine --quiet
python3 -m coverage report --show-missing --fail-under="$THRESHOLD"
[[ ${1:-} == --html ]] && python3 -m coverage html -d coverage-html
exit 0
