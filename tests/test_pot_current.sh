#!/usr/bin/env bash
# po/inzone-buds-mixer.pot must list every tr() string in the sources.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v xgettext >/dev/null 2>&1; then
  if [[ ${INZONE_REQUIRE_GETTEXT:-0} = 1 ]]; then
    printf 'FAIL: xgettext is required but not installed\n' >&2
    exit 1
  fi
  printf 'xgettext not installed; skipped\n'
  exit 0
fi

tools/update-pot.sh --check
printf 'Translation template is current.\n'
