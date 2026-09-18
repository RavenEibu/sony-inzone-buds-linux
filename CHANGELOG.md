# Changelog

## Unreleased

- Add the first `inzone-buds-mixer` GTK4 preview.
- Add overall Game/Chat volume, balance and microphone controls.
- Add a StatusNotifierItem tray icon for KDE and compatible GNOME extensions.
- Follow desktop light/dark appearance changes at runtime.
- Fix dark-to-light transitions by using the XDG desktop appearance portal as
  the independent color-scheme source.
- Apply the portal-selected GTK variant before constructing the window, fixing
  a light header bar when the mixer starts while the desktop is already dark.
- Declare the GTK4 GDK binding explicitly to avoid PyGI version warnings.
- Add Show Window and Quit actions through a native D-Bus tray menu.
- Add an original circular monochrome application and symbolic icon.
- Install desktop-entry and AppStream metadata for application menus.
- Add GUI backend and expanded installer tests.
- Make the hot-plug helper resolve `inzonectl` without relying on shell `PATH`.
- Add safe `/usr/local/bin` command links when `~/.local/bin` is absent from
  `PATH`, without overwriting existing commands.
- Remove only project-owned system links during uninstall.
- Document shell command-cache and `PATH` troubleshooting.

### Fixes from the 2026-09-17 repository review

- Keep the mixer's periodic refresh from moving sliders back, or committing
  the previous value, while a user change is pending or being applied.
- Report an unreachable PulseAudio-compatible server instead of exiting
  silently from `inzonectl status` and other commands.
- Generate the systemd user service from a template so it follows
  `XDG_BIN_HOME` instead of assuming `~/.local/bin`.
- Drop the service's `graphical-session.target` binding, which could leave it
  stopped after logging out and back in.
- Register the tray icon only after its D-Bus name is owned.
- Keep the AppStream release list to published versions and fix the developer
  ID reported by `appstreamcli validate`.
- Use a single main desktop menu category so the mixer is not listed twice.
- Describe KDE Plasma as expected to work but not yet tested.
- Create the PC-mode card directly in Pro Audio through a WirePlumber
  `device.profile.priority.rules` entry, avoiding a profile switch that once
  left generic analog nodes behind.
- Document the generic Analog/S/PDIF profile names, verified channel order and
  the 2026-09-17 hardware test results.

## 0.1.0 - 2026-09-13

- Add WirePlumber 0.5 rules for PC-mode dongle `054c:0ec2`.
- Label native Game, Chat and Microphone nodes.
- Prefer Pro Audio and automatically select Game/Microphone on hot-plug.
- Add endpoint volume, balance, status and diagnostic commands.
- Add reversible user-level installer and uninstaller.
- Add English architecture, hardware, troubleshooting and roadmap documents.
