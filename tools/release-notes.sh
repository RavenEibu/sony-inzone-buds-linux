#!/usr/bin/env bash
# Print the CHANGELOG.md section for one version (without its heading).
# Usage: tools/release-notes.sh X.Y.Z
set -euo pipefail

version=${1:-}
if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  printf 'Usage: %s X.Y.Z\n' "${0##*/}" >&2
  exit 2
fi

changelog="$(dirname -- "${BASH_SOURCE[0]}")/../CHANGELOG.md"

notes=$(awk -v ver="$version" '
  /^## / {
    if (found) exit
    if ($2 == ver) { found = 1; next }
  }
  found { print }
' "$changelog")

# Trim leading and trailing blank lines.
notes=$(printf '%s\n' "$notes" | sed -e '/./,$!d' | sed -e ':a' -e '/^\n*$/{$d;N;ba' -e '}')

if [[ -z $notes ]]; then
  printf 'No CHANGELOG section found for %s\n' "$version" >&2
  exit 1
fi

printf '%s\n' "$notes"
