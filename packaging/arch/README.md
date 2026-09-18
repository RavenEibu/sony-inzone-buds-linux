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

1. Bump `pkgver` (and reset `pkgrel=1`) to match the new git tag.
2. Update `sha256sums` with the new tarball's checksum:
   ```bash
   curl -sL -o /tmp/inzone.tar.gz \
     "https://github.com/RavenEibu/sony-inzone-buds-linux/archive/refs/tags/v$PKGVER.tar.gz"
   sha256sum /tmp/inzone.tar.gz
   ```
3. Build and test as above.
4. Update the separate AUR git repository (`ssh://aur@aur.archlinux.org/inzone-buds-mixer.git`),
   which is not this repository: copy `PKGBUILD` and
   `inzone-buds-mixer.install` into it, run `makepkg --printsrcinfo > .SRCINFO`,
   commit both files, and push.
