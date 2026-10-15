# Contributing

Bug reports, documentation improvements and verified hardware findings are
welcome.

## Before opening an issue

1. Confirm that the dongle switch is in PC mode.
2. Run `inzonectl doctor` and include the relevant output. Its first line shows
   the installed version.
3. Describe the Linux distribution and desktop environment.
4. State the PipeWire and WirePlumber versions.

Remove usernames, unrelated device details and any other personal data before
posting diagnostics publicly.

## Development

Run every test, and the static checks, with:

```bash
./tests/run-all.sh
./tests/lint.sh
```

To run them automatically before every push:

```bash
git config core.hooksPath .githooks
```

GitHub Actions runs both scripts on Ubuntu 24.04 for every push and pull
request, so they are the same commands locally and in CI.

No test requires physical hardware. `test_gui_refresh.py` needs Python GObject
bindings and GTK4 but no display; it is skipped when they are missing, except
in CI, where `INZONE_REQUIRE_GTK_TESTS=1` makes a missing GTK a failure.
`lint.sh` needs ShellCheck, `appstreamcli` and `desktop-file-validate`, and
runs `ruff` when it is installed (CI requires it). Running
the application itself requires Python GObject bindings and GTK4.

Keep hardware claims tied to reproducible evidence. In particular, do not
label a proprietary control as supported based only on a guessed USB packet.
Do not redistribute Sony binaries, firmware or extracted copyrighted assets.

## HID research

`tools/inzone-hid-capture` prints the dongle's raw HID input reports; it is
read-only and never writes to the device. It needs read access to the hidraw
node, which `config/udev/70-inzone-buds-hidraw.rules` grants to the logged-in
user (see `docs/hardware.md#passive-capture` for install steps). Neither file
is installed by `install.sh`; they are for contributors investigating the
proprietary controls in [docs/roadmap.md](docs/roadmap.md#experimental-proprietary-controls).

Do not send output or feature reports to the device outside a controlled test
where the result is documented; see the contribution standard in the roadmap.

Unverified findings, partial decodes and speculative notes for proprietary
controls go on the long-lived `experimental/hid` branch, not on `main` or on
a short-lived feature branch. Rebase it onto `main` occasionally; do not merge
it into `main` directly. Once a finding meets the contribution standard, cut
an ordinary feature branch from it (or from `main`) for the actual
`inzonectl`/mixer change, and follow the normal test-then-CI-then-merge flow
for that branch.

## Releasing

Versions follow semantic versioning within 0.x: a minor release for new
features or behavior changes, a patch release for fixes only.

1. Set `VERSION` in `bin/inzonectl`.
2. Add a `## X.Y.Z - YYYY-MM-DD` section at the top of `CHANGELOG.md`, with
   Added, Changed and Fixed entries relative to the previous release.
3. Add the same version and date as the first `<release>` in
   `data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml`.
4. Update `docs/roadmap.md`.
5. Run `tests/run-all.sh` and `tests/lint.sh`, and check that CI passes;
   `tests/test_inzonectl.sh` fails if the three versions differ.
6. Create an annotated `vX.Y.Z` tag and push it. The `Release` workflow
   verifies that the tag, `inzonectl`, the metainfo and the CHANGELOG agree,
   publishes the GitHub release (CHANGELOG section as notes, tarball and
   `SHA256SUMS`) and opens a PR bumping the PKGBUILD. To do these by hand, use
   `tools/release-notes.sh X.Y.Z` and `tools/bump-pkgbuild.sh X.Y.Z`.
7. Merge the PKGBUILD bump PR, then update the AUR (see
   `packaging/arch/README.md`).
