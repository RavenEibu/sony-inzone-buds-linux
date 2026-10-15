# Arch Linux packaging

`PKGBUILD` builds `inzone-buds-mixer` from the GitHub release tarball, not
from a local checkout, so it always matches what a user would download. It is
not shipped by `install.sh`; it is for building the package or submitting it
to the AUR.

## Build and test locally

```bash
cd packaging/arch
makepkg -sf
namcap PKGBUILD
namcap inzone-buds-mixer-*.pkg.tar.zst
sudo pacman -U inzone-buds-mixer-*.pkg.tar.zst
```

`config/udev/70-inzone-buds-hidraw.rules` and `tools/inzone-hid-capture` are
intentionally not packaged, matching `install.sh`: they are opt-in tools for
HID research (see `CONTRIBUTING.md#hid-research`), not part of the verified
audio integration.

## Releasing a new version

1. Run `tools/bump-pkgbuild.sh X.Y.Z` from the repository root once the tag
   exists. It sets `pkgver`, resets `pkgrel=1` and writes the release
   tarball's `sha256sums`. The `Release` workflow does this and opens a PR.
2. Review the diff: only `pkgver`, `pkgrel` and `sha256sums` should change.
3. Build and test as above.
4. Update the separate AUR git repository (`ssh://aur@aur.archlinux.org/inzone-buds-mixer.git`),
   which is not this repository: copy `PKGBUILD` and
   `inzone-buds-mixer.install` into it, run `makepkg --printsrcinfo > .SRCINFO`,
   commit both files, and push.
