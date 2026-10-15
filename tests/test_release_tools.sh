#!/usr/bin/env bash
# Offline tests for tools/release-notes.sh and tools/bump-pkgbuild.sh.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

# --- release-notes.sh -------------------------------------------------------
version=$(sed -n 's/^VERSION=//p' bin/inzonectl)
notes=$(tools/release-notes.sh "$version")
[[ -n $notes ]] || fail "empty release notes for $version"
[[ $notes != '## '* ]] || fail "release notes include a version heading"
[[ $notes != *$'\n\n' ]] || fail "release notes keep trailing blank lines"

tools/release-notes.sh 0.0.0 2>/dev/null && fail "missing version must fail"
tools/release-notes.sh not-a-version 2>/dev/null && fail "invalid version must fail"

# Sections must not bleed into each other.
previous=$(tools/release-notes.sh 0.3.0)
[[ $previous != *"Boost Chat** could set Game to 100%"* ]] ||
  fail "0.3.0 notes contain the 0.3.1 section"

# --- bump-pkgbuild.sh -------------------------------------------------------
cp packaging/arch/PKGBUILD "$TMP/PKGBUILD"
printf 'fixture tarball\n' > "$TMP/release.tar.gz"
expected=$(sha256sum "$TMP/release.tar.gz")
expected=${expected%% *}

PKGBUILD="$TMP/PKGBUILD" tools/bump-pkgbuild.sh 9.8.7 "$TMP/release.tar.gz" > /dev/null

grep -qx 'pkgver=9.8.7' "$TMP/PKGBUILD" || fail "pkgver not bumped"
grep -qx 'pkgrel=1' "$TMP/PKGBUILD" || fail "pkgrel not reset"
grep -qx "sha256sums=('$expected')" "$TMP/PKGBUILD" || fail "sha256sums not updated"

# Only pkgver and sha256sums differ here (pkgrel is already 1).
changed=$(diff <(cat packaging/arch/PKGBUILD) "$TMP/PKGBUILD" | grep -c '^>' || true)
[[ $changed -eq 2 ]] || fail "expected 2 changed lines, got $changed"

PKGBUILD="$TMP/PKGBUILD" tools/bump-pkgbuild.sh bogus 2>/dev/null && fail "invalid version must fail"

printf 'Release tool tests passed.\n'
