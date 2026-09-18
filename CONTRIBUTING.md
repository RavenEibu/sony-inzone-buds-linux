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

Run the current shell tests with:

```bash
./tests/test_inzonectl.sh
./tests/test_install_paths.sh
./tests/test_autoswitch.sh
python3 ./tests/test_gui_backend.py
python3 ./tests/test_desktop_integration.py
python3 ./tests/test_gui_refresh.py
```

The GUI backend tests do not require GTK or physical hardware.
`test_gui_refresh.py` needs Python GObject bindings and GTK4 but no display; it
is skipped when they are missing. Running the application itself requires
Python GObject bindings and GTK4.

If ShellCheck is installed:

```bash
shellcheck bin/inzonectl bin/inzone-autoswitch bin/inzone-buds-mixer \
  install.sh uninstall.sh \
  tests/test_inzonectl.sh tests/test_install_paths.sh tests/test_autoswitch.sh
```

Keep hardware claims tied to reproducible evidence. In particular, do not
label a proprietary control as supported based only on a guessed USB packet.
Do not redistribute Sony binaries, firmware or extracted copyrighted assets.

## Releasing

Versions follow semantic versioning within 0.x: a minor release for new
features or behavior changes, a patch release for fixes only.

1. Set `VERSION` in `bin/inzonectl`.
2. Add a `## X.Y.Z - YYYY-MM-DD` section at the top of `CHANGELOG.md`, with
   Added, Changed and Fixed entries relative to the previous release.
3. Add the same version and date as the first `<release>` in
   `data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml`.
4. Update `docs/roadmap.md`.
5. Run every test; `tests/test_inzonectl.sh` fails if the three versions differ.
6. Create an annotated `vX.Y.Z` tag and a GitHub release whose notes are the
   CHANGELOG section.
