# Sony INZONE Buds for Linux

Open-source Linux integration for the Sony INZONE Buds USB dongle in **PC
mode** (`054c:0ec2`). It exposes and labels the dongle's native Game, Chat and
Microphone endpoints and makes Game the preferred output when the dongle is
connected.

This project is a userspace integration layer for PipeWire/WirePlumber. It is
not a replacement kernel driver: Linux already drives the USB audio interface
with `snd_usb_audio`.

## What works

- Game and Chat playback at the same time
- Microphone capture at the same time as both playback endpoints
- Friendly names in GNOME, KDE and `pavucontrol`
- Automatic `pro-audio` profile selection
- Game as the default output and the INZONE microphone as the default input
  whenever the PC-mode dongle appears
- Normal fallback to another audio device when the dongle is removed
- Per-endpoint volume and a Game/Chat balance command
- User-level install and uninstall; no root privileges required

Tested with the INZONE Buds dongle in PC mode:

| Endpoint | ALSA PCM | PipeWire profile node |
| --- | --- | --- |
| Chat | playback device 0 | `pro-output-0` |
| Game | playback device 1 | `pro-output-1` |
| Microphone | capture device 0 | `pro-input-0` |

All three endpoints expose 48 kHz, 16-bit audio. The USB card number is not
hard-coded and may change between computers or boots.

## Requirements

- PipeWire
- WirePlumber 0.5 or newer
- PulseAudio compatibility tools (`pactl`), normally provided by
  `pipewire-pulse`
- systemd user services for automatic hot-plug selection
- Bash 4 or newer

On Arch Linux and CachyOS:

```bash
sudo pacman -S pipewire pipewire-pulse wireplumber libpulse
```

## Install

Put the dongle switch in **PC**, clone this repository, then run:

```bash
./install.sh
```

The installer places files only in your user configuration:

- `~/.config/wireplumber/wireplumber.conf.d/51-inzone-buds.conf`
- `~/.config/systemd/user/inzone-buds-autoswitch.service`
- `~/.local/bin/inzonectl`
- `~/.local/bin/inzone-autoswitch`

It restarts WirePlumber, so audio streams may pause briefly. Log out and back
in if `~/.local/bin` was not already in your `PATH`.

## Use

Inspect the integration:

```bash
inzonectl status
inzonectl doctor
```

Choose defaults:

```bash
inzonectl game
inzonectl chat
inzonectl mic
```

Set endpoint volumes independently:

```bash
inzonectl volume game 50
inzonectl volume chat 40
inzonectl volume mic 100
```

Set Game/Chat balance. Position `0` means Chat, `50` is centered and `100`
means Game. The optional second argument is the maximum volume and defaults to
a conservative 50%:

```bash
inzonectl balance 70
inzonectl balance 70 45
```

At `balance 70 45`, Game is set to 45% and Chat to 27%.

For normal use, select these devices inside applications:

- Discord/voice output: **Sony INZONE Buds - Chat**
- Discord/voice input: **Sony INZONE Buds - Microphone**
- Games, Steam, music and general desktop audio: **Sony INZONE Buds - Game**

PipeWire/WirePlumber normally remembers a stream's selected target after it is
moved in `pavucontrol` or the desktop sound panel.

## Uninstall

```bash
./uninstall.sh
```

The uninstaller removes only files owned by this project. Installer-created
backups, if any, are kept next to the original path.

## Scope and limitations

Version 0.1 replaces the Game/Chat routing portion of Sony's Windows software.
It does **not** currently configure firmware, EQ, noise cancellation, touch
controls, spatial audio, battery reporting or other proprietary HID controls.
Those features require separate protocol research and should not be claimed as
supported until verified on hardware.

The MOBILE/PS5 dongle mode uses USB product ID `054c:0ec3` and exposes only one
playback endpoint. This project intentionally activates only for PC mode
`054c:0ec2`.

## Safety and troubleshooting

`inzonectl balance` never exceeds the maximum volume supplied to it, but check
your volume before putting the earbuds in. Run `inzonectl doctor` when filing
an issue; it reports audio topology and versions but does not upload anything.

If an existing file would be replaced during installation, the installer first
creates a timestamped backup in the same directory.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Hardware findings and captures must not
include personal data, account tokens or copyrighted Sony software.

## Documentation

- [Architecture](docs/architecture.md)
- [Verified hardware behavior](docs/hardware.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Roadmap](docs/roadmap.md)

## License

MIT. See [LICENSE](LICENSE).
