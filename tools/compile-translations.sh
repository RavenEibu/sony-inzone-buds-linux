#!/usr/bin/env bash
# Compile every po/*.po into DESTDIR/<lang>/LC_MESSAGES/inzone-buds-mixer.mo.
# Usage: tools/compile-translations.sh LOCALE_DIR
# Needs msgfmt (gettext). Used by install.sh and the Debian package build.
set -euo pipefail

dest=${1:?usage: compile-translations.sh LOCALE_DIR}
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

command -v msgfmt >/dev/null 2>&1 || {
  printf 'compile-translations: msgfmt (gettext) is not installed\n' >&2
  exit 1
}

for po in po/*.po; do
  [[ -e $po ]] || continue
  lang=$(basename -- "$po" .po)
  mkdir -p -- "$dest/$lang/LC_MESSAGES"
  msgfmt --check -o "$dest/$lang/LC_MESSAGES/inzone-buds-mixer.mo" "$po"
done
