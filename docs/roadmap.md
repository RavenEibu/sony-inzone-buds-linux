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

## Version 0.2: compatibility and packaging

- [ ] Test current Fedora, Ubuntu, Debian, Arch Linux and openSUSE releases.
- [ ] Add automated configuration validation with WirePlumber available in CI.
- [ ] Add Arch Linux packaging.
- [ ] Add Debian packaging.
- [ ] Test KDE Plasma and additional desktop audio panels.
- [ ] Add release artifacts and checksums through GitHub Actions.

## Version 0.3: desktop controls

- [x] Add an optional GTK4 Game/Chat balance and volume control.
- [x] Add StatusNotifierItem activation for KDE and compatible GNOME setups.
- [ ] Add a tray context menu with quick presets.
- [ ] Add launch-at-login preference.
- [ ] Add translated interface strings.
- [ ] Add desktop notifications for connect/disconnect events.
- [ ] Support configurable default behavior without editing scripts.
- [ ] Add optional keyboard-shortcut examples.

## Experimental: proprietary controls

The following work requires protocol research and real-device verification:

- [ ] Enumerate HID interfaces and report descriptors.
- [ ] Capture one setting change at a time on a controlled Windows test system.
- [ ] Document request/response framing and checksums.
- [ ] Build a read-only device-status prototype.
- [ ] Investigate battery reporting.
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
