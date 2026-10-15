#!/usr/bin/env bash
# bin/inzone-buds-mixer turns --language into INZONE_LANGUAGE and passes
# every other argument through unchanged.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

cat > "$TMP/app.py" <<'PY'
import os
import sys

print(os.environ.get("INZONE_LANGUAGE", "<unset>"), *sys.argv[1:])
PY

run() { INZONE_BUDS_MIXER_DATADIR="$TMP" bin/inzone-buds-mixer "$@"; }

[[ $(env -u INZONE_LANGUAGE bash -c "INZONE_BUDS_MIXER_DATADIR='$TMP' bin/inzone-buds-mixer --hidden") \
    == '<unset> --hidden' ]] || fail 'plain arguments changed'
[[ $(run --language es --hidden) == 'es --hidden' ]] || fail '--language CODE'
[[ $(run --hidden --language=zh_CN) == 'zh_CN --hidden' ]] || fail '--language=CODE'
run --language 2>/dev/null && fail '--language without a code must fail'

printf 'Launcher language tests passed.\n'
