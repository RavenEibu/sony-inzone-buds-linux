# Sony INZONE Buds for Linux

[![CI](https://github.com/RavenEibu/sony-inzone-buds-linux/actions/workflows/ci.yml/badge.svg)](https://github.com/RavenEibu/sony-inzone-buds-linux/actions/workflows/ci.yml)

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
- Friendly names in GNOME Settings and `pavucontrol`
- Automatic `pro-audio` profile selection
- Game as the default output and the INZONE microphone as the default input
  whenever the PC-mode dongle appears
- Normal fallback to another audio device when the dongle is removed
- Per-endpoint volume and a Game/Chat balance command
- Volume and mute keys move Game and Chat together, keeping their balance
- GTK4 mixer for Game/Chat balance, overall volume and microphone level,
  immediately reflecting changes made with volume keys or other mixers
- StatusNotifierItem tray icon, tested on GNOME with AppIndicator support
- Automatic light/dark appearance tracking while the application is running
- Native tray menu actions to show the window or quit
- User-level configuration, with rootless commands when `~/.local/bin` is
  already available in `PATH`

KDE Plasma implements the same desktop interfaces natively and is expected to
work, but it has not been tested yet; see the [roadmap](docs/roadmap.md).

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
- Python 3.10 or newer, PyGObject and GTK4 for the graphical mixer

On Arch Linux and CachyOS:

```bash
sudo pacman -S pipewire pipewire-pulse wireplumber libpulse
sudo pacman -S python-gobject gtk4
```

On Fedora:

```bash
sudo dnf install pipewire pipewire-pulseaudio wireplumber python3-gobject gtk4
```

On Debian or Ubuntu:

```bash
sudo apt install pipewire pipewire-pulse wireplumber python3-gi gir1.2-gtk-4.0
```

## Install

Put the dongle switch in **PC**, clone this repository, then run:

```bash
./install.sh
```

The installer places its configuration and program files under your home
directory:

- `~/.config/wireplumber/wireplumber.conf.d/51-inzone-buds.conf`
- `~/.config/systemd/user/inzone-buds-autoswitch.service`
- `~/.local/bin/inzonectl`
- `~/.local/bin/inzone-autoswitch`
- `~/.local/bin/inzone-buds-mixer`
- `~/.local/share/inzone-buds-mixer/` (GTK application code)
- application, AppStream and icon files under `~/.local/share`

`XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_BIN_HOME` are honored when set. The
installed service and application-menu entry point to the directory that
actually received the commands.

It restarts WirePlumber, so audio streams may pause briefly. The program files
remain under `~/.local/bin`. If that directory is missing from the current
`PATH`, the installer offers the normal `sudo` prompt and creates an
`inzonectl` command link under `/usr/local/bin`, without overwriting an existing
command. This makes
`inzonectl` available in the same terminal. Systems that already include
`~/.local/bin` remain fully rootless.

If Zsh or Bash cached an unsuccessful lookup made before installation, refresh
its command cache once:

```bash
rehash   # Zsh
hash -r  # Bash
```

## Use

Launch the graphical mixer from the desktop application menu or run:

```bash
inzone-buds-mixer
```

Turn on **Start at login in the tray** in the mixer to start it hidden, with
only its tray icon, when you log in. `inzone-buds-mixer --hidden` does the same
from a terminal. Without a tray the window is shown after 10 seconds, so the
mixer never becomes unreachable.

The **Overall volume** slider controls the louder Game/Chat endpoint. The
**Game / Chat balance** slider attenuates the opposite endpoint. **Center**
sets the balance to `50`, giving Game and Chat the same volume without
changing the overall level. Set balance to `50` and overall volume to `100%`
when both Game and Chat should be at their maximum level. The microphone
slider is independent.

KDE Plasma provides StatusNotifierItem support. GNOME requires an extension
such as **AppIndicator and KStatusNotifierItem Support**. When tray support is
available, closing the window hides it; use the quit button in the header to
stop the application. Right-click the indicator for **Show Window**,
**Center Game/Chat** and **Quit** actions.

The application follows GTK's desktop-wide color-scheme setting and updates
between its light and dark appearances without needing a restart.

See [Graphical mixer](docs/gui.md) for the control model and current desktop
integration limitations.

### Command line

Inspect the integration:

```bash
inzonectl status
inzonectl doctor
inzonectl --version
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

The desktop volume and mute keys change only the default output, normally
Game. The hot-plug service follows such a change on the other endpoint, so
Game and Chat rise, fall and mute together and keep their balance. The louder
endpoint is capped at 100%. Changes made with `inzonectl` or the mixer are
treated as deliberate and are not mirrored, so `inzonectl volume game 30`
still changes Game alone. See
[Troubleshooting](docs/troubleshooting.md#volume-keys-move-game-and-chat-together)
to turn this off.

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

The generic **Analog Output** and **Digital Output (S/PDIF)** entries disappear
once the integration is active. They were the Chat and Game endpoints under
ALSA's generic names, one at a time; see
[Troubleshooting](docs/troubleshooting.md#the-analog-and-spdif-outputs-disappeared).

## Uninstall

```bash
./uninstall.sh
```

The uninstaller removes only files owned by this project. Configuration
backups created by the installer, if any, are kept next to the original path.

## Scope and limitations

The project replaces the Game/Chat routing portion of Sony's Windows software.
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

If the WirePlumber rule or the systemd user service under `~/.config` differs
from the version being installed, for example because it was edited by hand,
the installer first keeps a timestamped backup next to it. Program and data
files owned by the project are replaced without backups, so upgrades do not
leave extra files in `~/.local/bin`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Hardware findings and captures must not
include personal data, account tokens or copyrighted Sony software.

## Documentation

- [Architecture](docs/architecture.md)
- [Verified hardware behavior](docs/hardware.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Roadmap](docs/roadmap.md)
- [Graphical mixer](docs/gui.md)

## License

MIT. See [LICENSE](LICENSE).
