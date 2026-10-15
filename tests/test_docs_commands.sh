#!/usr/bin/env bash
# Every `inzonectl <subcommand>` used in docs/shortcuts.md must exist in help.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# `help` still requires pactl to exist; a stub is enough.
help=$(PACTL=true bin/inzonectl help)
mapfile -t subcommands < <(
  grep -o 'inzonectl [a-z-]*' docs/shortcuts.md | awk '{print $2}' | sort -u
)
[[ ${#subcommands[@]} -gt 0 ]] || { printf 'FAIL: no commands found\n' >&2; exit 1; }

for subcommand in "${subcommands[@]}"; do
  # "inzonectl help" in prose is fine; otherwise it must be a listed command.
  if ! grep -Eq "^  $subcommand( |$)" <<< "$help"; then
    printf 'FAIL: docs/shortcuts.md uses unknown subcommand: %s\n' "$subcommand" >&2
    exit 1
  fi
done
printf 'Documentation command tests passed.\n'
