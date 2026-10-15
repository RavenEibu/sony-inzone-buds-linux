#!/usr/bin/env bash
# Merge the translations in po/*.po into a desktop entry or AppStream file.
# Usage: tools/localize-metadata.sh desktop|metainfo INPUT OUTPUT
# Without msgfmt (gettext) the input is copied unchanged, so the English text
# is still installed.
set -euo pipefail

kind=${1:?usage: localize-metadata.sh desktop|metainfo INPUT OUTPUT}
input=${2:?missing INPUT}
output=${3:?missing OUTPUT}
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

if ! command -v msgfmt >/dev/null 2>&1; then
  cp -- "$input" "$output"
  exit 0
fi

case $kind in
  desktop)
    msgfmt --desktop --template "$input" -d "$root/po" -o "$output"
    ;;
  metainfo)
    # msgfmt's AppStream rules would also translate the release notes, so the
    # merge is done by a small script that touches only name, summary and
    # description paragraphs.
    python3 -I "$root/tools/localize-metainfo.py" "$root/po" "$input" "$output"
    ;;
  *)
    printf 'localize-metadata: unknown kind: %s\n' "$kind" >&2
    exit 2
    ;;
esac
