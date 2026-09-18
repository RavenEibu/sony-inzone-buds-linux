# Changelog

## Unreleased

### Added

- GitHub Actions CI on Ubuntu 24.04 runs every test, ShellCheck, AppStream and
  desktop-entry validation for each push and pull request. `tests/run-all.sh`
  and `tests/lint.sh` run the same checks locally.
- **Start at login in the tray** in the mixer writes an XDG autostart entry
  that starts it hidden. `inzone-buds-mixer --hidden` starts it with only its
  tray icon; without a tray the window appears after 10 seconds. The
  uninstaller removes the entry.
- The mixer window reappears if the tray host disappears while it is hidden.
- Document the dongle's USB interfaces, including the device-provided Chat and
  Game function names, its HID report descriptor and the input devices the
  kernel creates from it.
- Add `config/udev/70-inzone-buds-hidraw.rules`, an optional udev rule that
  grants the logged-in user read/write access to the dongle's hidraw device
  through systemd-logind (no group membership, no world-accessible device),
  and `tools/inzone-hid-capture`, a read-only tool that prints its HID input
  reports for hardware research. Neither is installed by `install.sh`.
- Document the nested framing of HID input report `0x02` and a candidate,
  not-yet-verified battery-percentage field in its `14 04` sub-message; see
  `docs/hardware.md#hypotheses-not-verified`.

## 0.2.0 - 2026-09-17

Adds the INZONE Buds Mixer and makes the desktop volume keys control Game and
Chat together. Verified with the dongle on CachyOS with GNOME on Wayland. KDE
Plasma is expected to work but has not been tested.

### Added

- `inzone-buds-mixer`, a GTK4 application with overall volume, Game/Chat
  balance and microphone controls, and a **Center** button that sets the
  balance to 50 without changing the overall volume.
- A StatusNotifierItem tray icon with **Show Window**, **Center Game/Chat** and
  **Quit** actions, for KDE Plasma and for GNOME with AppIndicator support.
- The mixer reflects changes made elsewhere, such as volume keys, the desktop
  sound panel or other mixers, immediately, and follows the desktop light/dark
  appearance.
- Desktop entry, AppStream metadata and an original application icon.
- `inzonectl --version`; `inzonectl doctor` also reports the version.
- `/usr/local/bin` command links when `~/.local/bin` is not in `PATH`, without
  overwriting existing commands. The uninstaller removes only links it created.
- Documentation of the generic Analog and S/PDIF profile names, the verified
  channel order and the hardware test results.

### Changed

- **Volume and mute keys move Game and Chat together**, keeping their balance.
  The hot-plug service mirrors a change that affected only one endpoint; changes
  made with `inzonectl` or the mixer stay independent. Set
  `INZONE_LINK_VOLUMES=0` on the service to restore the previous behavior.
- WirePlumber creates the PC-mode card directly in Pro Audio through a
  `device.profile.priority.rules` entry instead of starting the analog profile
  first. A profile the user saved explicitly still takes precedence.
- The installer backs up only edited configuration, the WirePlumber rule and
  the systemd service. Program and data files are replaced without
  `*.backup-*` copies.

### Fixed

- `inzonectl status` and other commands exited silently when the
  PulseAudio-compatible server was unreachable. They now explain the error, and
  `doctor` still runs.
- The systemd service assumed `~/.local/bin` and failed when `XDG_BIN_HOME`
  pointed elsewhere; it is now generated from a template.
- The service could stay stopped after logging out and back in.
- The hot-plug helper found `inzonectl` only through the shell `PATH`.
- Switching the card to Pro Audio once left generic analog nodes behind, and
  their mono input outranked the INZONE microphone.

## 0.1.0 - 2026-09-13

- Add WirePlumber 0.5 rules for PC-mode dongle `054c:0ec2`.
- Label native Game, Chat and Microphone nodes.
- Prefer Pro Audio and automatically select Game/Microphone on hot-plug.
- Add endpoint volume, balance, status and diagnostic commands.
- Add reversible user-level installer and uninstaller.
- Add English architecture, hardware, troubleshooting and roadmap documents.
