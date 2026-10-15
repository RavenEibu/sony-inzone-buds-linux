# Security policy

## Scope

This project is a userspace integration layer: shell and Python scripts that
call `pactl`/`wpctl`, a GTK4 mixer, and optional WirePlumber and systemd user
configuration. It never runs with elevated privileges and does not install a
kernel module or a root-owned service.

The HID research tools (`tools/inzone-hid-capture`, `tools/inzone-hid-analyze`
and the opt-in udev rule) are read-only and are not installed by default.

## Reporting a vulnerability

Please report suspected vulnerabilities privately through GitHub's
[private vulnerability reporting](https://github.com/RavenEibu/sony-inzone-buds-linux/security/advisories/new)
instead of a public issue. Include the affected version (`inzonectl --version`),
what an attacker needs, and the impact.

Expect an acknowledgement within a few days. Fixes ship in the next patch
release; only the latest release is supported.
