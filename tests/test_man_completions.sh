#!/usr/bin/env bash
# The man page and shell completions must list exactly inzonectl's commands.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

# Commands according to `inzonectl help` (first word of each command line).
mapfile -t commands < <(
  PACTL=true bin/inzonectl help | sed -n 's/^  \([a-z][a-z-]*\)[ ,].*/\1/p;s/^  \([a-z][a-z-]*\)$/\1/p' |
    sort -u
)
[[ ${#commands[@]} -ge 9 ]] || fail "could not extract commands from help: ${commands[*]}"

for command_name in "${commands[@]}"; do
  grep -Eq "^\.B(R)? $command_name|^\.BI? \"?$command_name" data/man/inzonectl.1 ||
    fail "man page does not document: $command_name"
  grep -q "\b$command_name\b" data/completions/inzonectl.bash ||
    fail "bash completion misses: $command_name"
  grep -q "'$command_name:" data/completions/_inzonectl ||
    fail "zsh completion misses: $command_name"
  grep -q "\b$command_name\b" data/completions/inzonectl.fish ||
    fail "fish completion misses: $command_name"
done

# Man page syntax: groff warnings mean a broken page (skipped without groff).
if command -v groff >/dev/null 2>&1; then
  warnings=$(groff -man -ww -z data/man/inzonectl.1 2>&1 || true)
  [[ -z $warnings ]] || fail "groff warnings: $warnings"
fi

# The bash completion actually completes.
# shellcheck source=/dev/null
source data/completions/inzonectl.bash
COMP_WORDS=(inzonectl ba) COMP_CWORD=1
_inzonectl
[[ ${COMPREPLY[*]} == balance ]] || fail "bash completion of 'ba' gave: ${COMPREPLY[*]}"
COMP_WORDS=(inzonectl volume c) COMP_CWORD=2
_inzonectl
[[ ${COMPREPLY[*]} == chat ]] || fail "bash completion of 'volume c' gave: ${COMPREPLY[*]}"

printf 'Man page and completion tests passed.\n'
