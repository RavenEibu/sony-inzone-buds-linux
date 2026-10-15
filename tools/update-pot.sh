#!/usr/bin/env bash
# Regenerate po/inzone-buds-mixer.pot from the sources in po/POTFILES.in and
# merge it into every po/*.po. Usage: tools/update-pot.sh [--check]
# --check fails if the committed template is out of date (used by tests/CI).
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

pot=po/inzone-buds-mixer.pot
out=$pot
[[ ${1:-} == --check ]] && out=$(mktemp)

LC_ALL=C xgettext --files-from=po/POTFILES.in --directory=. --keyword=tr \
  --language=Python --from-code=UTF-8 --add-comments=TRANSLATORS \
  --package-name=inzone-buds-mixer --msgid-bugs-address=https://github.com/RavenEibu/sony-inzone-buds-linux/issues \
  --no-location -o "$out"

if [[ ${1:-} == --check ]]; then
  # Compare only the message ids: headers and ordering details differ between
  # gettext versions.
  if ! diff <(grep '^msgid' "$pot" | sort) <(grep '^msgid' "$out" | sort) >/dev/null; then
    rm -f -- "$out"
    printf 'po/inzone-buds-mixer.pot is out of date; run tools/update-pot.sh\n' >&2
    exit 1
  fi
  rm -f -- "$out"
  exit 0
fi

for po in po/*.po; do
  [[ -e $po ]] || continue
  msgmerge --update --backup=none --quiet "$po" "$pot"
done
