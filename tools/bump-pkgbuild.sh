#!/usr/bin/env bash
# Bump packaging/arch/PKGBUILD to a released version: sets pkgver, resets
# pkgrel to 1 and replaces sha256sums with the release tarball's checksum.
#
# Usage: tools/bump-pkgbuild.sh X.Y.Z [TARBALL]
#
# Without TARBALL the GitHub release tarball for vX.Y.Z is downloaded, which
# is exactly what the PKGBUILD builds from. TARBALL exists for offline use and
# tests.
set -euo pipefail

version=${1:-}
tarball=${2:-}
if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  printf 'Usage: %s X.Y.Z [TARBALL]\n' "${0##*/}" >&2
  exit 2
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
pkgbuild=${PKGBUILD:-$root/packaging/arch/PKGBUILD}

if [[ -z $tarball ]]; then
  tmp=$(mktemp -d)
  trap 'rm -rf -- "$tmp"' EXIT
  tarball=$tmp/release.tar.gz
  curl -fsSL -o "$tarball" \
    "https://github.com/RavenEibu/sony-inzone-buds-linux/archive/refs/tags/v$version.tar.gz"
fi

sum=$(sha256sum -- "$tarball")
sum=${sum%% *}

sed -i \
  -e "s/^pkgver=.*/pkgver=$version/" \
  -e 's/^pkgrel=.*/pkgrel=1/' \
  -e "s/^sha256sums=.*/sha256sums=('$sum')/" \
  "$pkgbuild"

printf 'PKGBUILD -> pkgver=%s sha256=%s\n' "$version" "$sum"
