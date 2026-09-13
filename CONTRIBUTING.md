# Contributing

Bug reports, documentation improvements and verified hardware findings are
welcome.

## Before opening an issue

1. Confirm that the dongle switch is in PC mode.
2. Run `inzonectl doctor` and include the relevant output.
3. Describe the Linux distribution and desktop environment.
4. State the PipeWire and WirePlumber versions.

Remove usernames, unrelated device details and any other personal data before
posting diagnostics publicly.

## Development

Run the current shell tests with:

```bash
./tests/test_inzonectl.sh
```

If ShellCheck is installed:

```bash
shellcheck bin/inzonectl bin/inzone-autoswitch install.sh uninstall.sh \
  tests/test_inzonectl.sh
```

Keep hardware claims tied to reproducible evidence. In particular, do not
label a proprietary control as supported based only on a guessed USB packet.
Do not redistribute Sony binaries, firmware or extracted copyrighted assets.
