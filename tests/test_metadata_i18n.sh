#!/usr/bin/env bash
# The desktop entry and AppStream file stay valid after translations are merged
# in, and actually contain them.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v msgfmt >/dev/null 2>&1; then
  printf 'msgfmt not installed; skipped\n'
  exit 0
fi

TMP=$(mktemp -d)
trap 'rm -rf -- "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

sed 's|@BINDIR@|/usr/bin|g' \
  data/applications/io.github.RavenEibu.InzoneBudsMixer.desktop.in > "$TMP/desktop.in"
tools/localize-metadata.sh desktop "$TMP/desktop.in" "$TMP/app.desktop"
tools/localize-metadata.sh metainfo \
  data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml "$TMP/app.metainfo.xml"

grep -q '^Comment=Control Game, Chat' "$TMP/app.desktop" || fail 'English Comment missing'
grep -q '^Comment\[es\]=Controla los niveles' "$TMP/app.desktop" || fail 'Spanish Comment missing'
grep -q '^Comment\[zh_CN\]=' "$TMP/app.desktop" || fail 'zh_CN Comment missing'
grep -q '^Keywords\[de\]=.*;$' "$TMP/app.desktop" || fail 'German Keywords must end with ;'
grep -q 'xml:lang="fr"' "$TMP/app.metainfo.xml" || fail 'French AppStream text missing'
grep -q 'xml:lang="ar"' "$TMP/app.metainfo.xml" || fail 'Arabic AppStream text missing'
# Every language translates the summary and both description paragraphs.
while read -r -a languages; do :; done < po/LINGUAS
for lang in "${languages[@]}"; do
  [[ $(grep -c "xml:lang=\"$lang\"" "$TMP/app.metainfo.xml") -eq 3 ]] ||
    fail "AppStream translations incomplete for $lang"
done

# Release notes are deliberately not translated.
releases=$(grep -c '<release ' "$TMP/app.metainfo.xml")
grep -c 'xml:lang' "$TMP/app.metainfo.xml" >/dev/null
awk '/<releases>/,/<\/releases>/' "$TMP/app.metainfo.xml" | grep -q 'xml:lang' &&
  fail 'release notes were translated'
[[ $releases -ge 1 ]] || fail 'releases lost'

desktop-file-validate "$TMP/app.desktop"
appstreamcli validate --no-net "$TMP/app.metainfo.xml" >/dev/null

# Without msgfmt the English files are installed unchanged.
mkdir "$TMP/nobin"
ln -s "$(command -v cp)" "$TMP/nobin/cp"
ln -s "$(command -v dirname)" "$TMP/nobin/dirname"
PATH="$TMP/nobin" /bin/bash tools/localize-metadata.sh desktop "$TMP/desktop.in" "$TMP/plain.desktop" 2>/dev/null ||
  fail 'localize-metadata failed without msgfmt'
cmp -s "$TMP/desktop.in" "$TMP/plain.desktop" || fail 'fallback did not copy the input'

printf 'Metadata translation tests passed.\n'
