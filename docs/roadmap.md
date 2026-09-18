# Roadmap

The roadmap separates the verified audio integration from proprietary device
control work.

## Version 0.1: audio routing

- [x] Identify PC and MOBILE/PS5 USB product IDs.
- [x] Verify Game, Chat and Microphone endpoint mapping.
- [x] Expose all PC-mode endpoints with Pro Audio.
- [x] Add friendly WirePlumber descriptions.
- [x] Prefer Game output and INZONE microphone on hot-plug.
- [x] Add endpoint volume and Game/Chat balance controls.
- [x] Provide reversible user-level installation.

## Version 0.2: desktop mixer (released 2026-09-17)

- [x] Add an optional GTK4 Game/Chat balance and volume control.
- [x] Add StatusNotifierItem activation for KDE and compatible GNOME setups.
- [x] Add a tray context menu with Show Window, Center Game/Chat and Quit
  actions.
- [x] Reflect volume changes made outside the mixer immediately.
- [x] Move Game and Chat together with the desktop volume and mute keys.
- [x] Create the PC-mode card directly in Pro Audio.
- [x] Report the version with `inzonectl --version`.

## Version 0.3: compatibility and packaging

- [ ] Test current Fedora, Ubuntu, Debian, Arch Linux and openSUSE releases.
- [ ] Test KDE Plasma and additional desktop audio panels.
- [ ] Test GNOME without a StatusNotifierItem extension.
- [x] Run the tests, ShellCheck and metadata validation in GitHub Actions.
- [ ] Add automated configuration validation with WirePlumber available in CI.
- [x] Add Arch Linux packaging (`packaging/arch/`, not yet submitted to the
  AUR).
- [ ] Add Debian packaging.
- [ ] Add release artifacts and checksums through GitHub Actions.

## Version 0.4: desktop controls

- [x] Add more Game/Chat presets to the tray context menu (Boost Chat 70%).
- [x] Add launch-at-login preference, starting hidden in the tray.
- [ ] Add translated interface strings.
- [x] Add desktop notifications for connect/disconnect events.
- [x] Support configurable default behavior without editing scripts or service
  files, including volume-key linking.
- [ ] Add optional keyboard-shortcut examples.

## Experimental: proprietary controls

The following work requires protocol research and real-device verification:

- [x] Enumerate HID interfaces and report descriptors.
- [x] Build a udev rule and a read-only capture tool
  (`tools/inzone-hid-capture`) for recording input reports without root.
- [x] Record input reports while changing one device state at a time (remove
  an earbud from the case, connect a charger, touch a control) and document
  which report changes.
- [ ] Capture one setting change at a time on a controlled Windows test system.
- [ ] Document request/response framing and checksums.
- [ ] Build a read-only device-status prototype.
- [ ] Investigate battery reporting: report `0x02`'s `14 04` sub-message is a
  candidate, but three short, timed removal tests failed to reproduce the one
  change seen so far (see `docs/hardware.md#hypotheses-not-verified`) — try a
  long, untimed passive capture during normal use, reproduce on both
  earbuds, and cross-check against an independent battery reading before
  treating it as supported. Once verified, implement it on its own branch
  (do not build on top of unverified proprietary-control findings on `main`).
- [ ] Investigate EQ, noise control and sidetone.
- [ ] Investigate touch-control and power settings.

Firmware-writing support is not planned until the protocol, recovery path and
failure behavior are independently understood. Safety takes precedence over
feature parity.

## Contribution standard

A proprietary control is considered supported only when:

1. the packet or request is documented;
2. the result is repeatable across reconnects;
3. failure behavior is understood;
4. the behavior has been confirmed on hardware;
5. the implementation does not depend on redistributing Sony software or
   firmware.
