#!/usr/bin/env bash
# Static checks. Requires shellcheck, appstreamcli and desktop-file-validate.
# ruff is optional locally (skipped with a notice) and mandatory when
# INZONE_REQUIRE_RUFF=1, which CI sets.
# CI uses this same entry point.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

printf '== shellcheck\n'
shellcheck -x bin/inzonectl bin/inzone-autoswitch bin/inzone-buds-mixer \
  install.sh uninstall.sh tests/*.sh tools/*.sh .githooks/pre-push

printf '== appstreamcli\n'
appstreamcli validate --no-net \
  data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml

printf '== desktop-file-validate\n'
desktop_file="$TMP/io.github.RavenEibu.InzoneBudsMixer.desktop"
sed 's|@BINDIR@|/usr/bin|g' \
  data/applications/io.github.RavenEibu.InzoneBudsMixer.desktop.in > "$desktop_file"
desktop-file-validate "$desktop_file"

printf '== python syntax\n'
python3 - src/inzone_buds_mixer/*.py tests/*.py tools/inzone-hid-capture <<'EOF'
import ast
import sys

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as source:
        ast.parse(source.read(), path)
EOF

printf '== ruff\n'
if command -v ruff >/dev/null 2>&1; then
  ruff check src tests tools/inzone-hid-capture
elif [[ ${INZONE_REQUIRE_RUFF:-0} = 1 ]]; then
  printf 'ruff is required but not installed\n' >&2
  exit 1
else
  printf 'ruff not installed; skipped\n'
fi

printf 'Lint passed.\n'
