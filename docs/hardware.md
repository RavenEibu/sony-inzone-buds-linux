# Verified hardware behavior

This document records observations made from a Sony INZONE Buds USB dongle on
Linux. It distinguishes verified behavior from assumptions and future research.

## USB modes

The physical switch changes the USB product exposed to the host:

| Dongle mode | USB ID | Playback topology | Capture topology |
| --- | --- | --- | --- |
| PC | `054c:0ec2` | Game + Chat | Microphone |
| MOBILE/PS5 | `054c:0ec3` | One stereo endpoint | One mono microphone |

The integration currently targets PC mode only.

## PC-mode endpoint mapping

The following mapping was confirmed using ALSA enumeration and `wpctl inspect`:

| Purpose | ALSA direction/device | ALSA path example | PipeWire node suffix |
| --- | --- | --- | --- |
| Chat | playback device 0 | `hw:7,0` | `pro-output-0` |
| Game | playback device 1 | `hw:7,1` | `pro-output-1` |
| Microphone | capture device 0 | `hw:7,0` | `pro-input-0` |

The `7` in the example ALSA paths was the card number on one test system. It is
not stable and is not used by the implementation.

## Formats

Both PC-mode playback endpoints reported:

- signed 16-bit little-endian PCM (`S16_LE` / `s16le`);
- two channels;
- 48,000 Hz.

The microphone reported one channel at 16-bit/48,000 Hz.

These findings do not support describing Chat as a lower-resolution playback
path. Any audible or functional difference between Game and Chat is therefore
not explained by the advertised USB sample format alone.

## Generic ALSA profile names

Without Pro Audio, the ALSA card profiles expose only one playback endpoint at a
time and name it after ALSA's generic USB-audio conventions. The names do not
describe real connectors: the dongle has no analog or optical output.

| Generic profile or port | ALSA PCM | Actual endpoint |
| --- | --- | --- |
| Analog Stereo (`analog-stereo`) | playback device 0 | Chat |
| Digital Stereo / S/PDIF (`iec958-stereo`) | playback device 1 | Game |
| Digital Surround 5.1 (IEC958/AC3) | playback device 1 | Game, with an encoded format the dongle is not known to decode |
| Mono input (`mono-fallback`) | capture device 0 | Microphone |

Pro Audio is the only profile that exposes both playback devices at the same
time. Each ALSA PCM can be opened by only one PipeWire node, so the generic
nodes cannot coexist with Game and Chat.

## Channel order

Pro Audio nodes use positionless `AUX0`/`AUX1` channels instead of
`FL`/`FR`. A left-only test tone played to the Game node was heard in the left
earbud, so ordinary stereo streams keep the correct left/right order.

## Concurrent operation

The following behavior was tested successfully:

- audio playing through Game;
- Discord voice-test audio playing through Chat at the same time;
- microphone capture operating during both playback streams.

This confirms that no software-created combined sink is required for the basic
Game/Chat workflow.

## Test environment

The initial investigation used:

- PipeWire 1.6.8;
- WirePlumber with the 0.5 configuration format;
- the standard Linux `snd_usb_audio` driver;
- a Sony INZONE Buds dongle connected in PC mode.

A second hardware session on 2026-09-17 (CachyOS, Linux 7.2.6, PipeWire 1.6.8,
WirePlumber 0.5.17, GNOME on Wayland) confirmed:

- separate test tones on Game and Chat, individually and at the same time;
- left/right channel order on Game;
- microphone capture as 48 kHz mono, with speech well above the noise floor;
- unplug fallback to the built-in audio device, and Game plus the INZONE
  microphone selected again less than one second after reconnecting;
- the GTK mixer's overall volume and balance controls applying the documented
  balance model;
- the card being created directly in Pro Audio by the WirePlumber profile rule,
  with no saved profile and without `inzone-autoswitch` running.

## Not yet verified

The following functions are outside the verified audio topology and must not be
reported as supported:

- battery status;
- firmware updates;
- equalizer settings;
- noise-control settings;
- sidetone configuration;
- touch-control assignments;
- spatial-audio configuration;
- automatic power-off settings.

These may use proprietary HID interfaces rather than the standard USB Audio
Class endpoints documented above.
