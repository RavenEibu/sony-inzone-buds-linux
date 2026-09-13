# Changelog

## Unreleased

- Add the first `inzone-buds-mixer` GTK4 preview.
- Add overall Game/Chat volume, balance and microphone controls.
- Add a StatusNotifierItem tray icon for KDE and compatible GNOME extensions.
- Follow desktop light/dark appearance changes at runtime.
- Add Show Window and Quit actions through a native D-Bus tray menu.
- Add an original circular monochrome application and symbolic icon.
- Install desktop-entry and AppStream metadata for application menus.
- Add GUI backend and expanded installer tests.
- Make the hot-plug helper resolve `inzonectl` without relying on shell `PATH`.
- Add safe `/usr/local/bin` command links when `~/.local/bin` is absent from
  `PATH`, without overwriting existing commands.
- Remove only project-owned system links during uninstall.
- Document shell command-cache and `PATH` troubleshooting.

## 0.1.0 - 2026-09-13

- Add WirePlumber 0.5 rules for PC-mode dongle `054c:0ec2`.
- Label native Game, Chat and Microphone nodes.
- Prefer Pro Audio and automatically select Game/Microphone on hot-plug.
- Add endpoint volume, balance, status and diagnostic commands.
- Add reversible user-level installer and uninstaller.
- Add English architecture, hardware, troubleshooting and roadmap documents.
