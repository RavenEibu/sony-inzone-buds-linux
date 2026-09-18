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

The dongle's own USB descriptors confirm the mapping: it names its first audio
function "INZONE Buds - Chat" and its second "INZONE Buds - Game" (see
[USB interfaces](#usb-interfaces)).

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

## USB interfaces

Read with `lsusb -v -d 054c:0ec2` and sysfs on 2026-09-18. The PC-mode dongle
is a USB 2.0 device (`bcdDevice` 1.00, no serial number) with one configuration
and six interfaces forming two USB Audio Class functions and one HID interface:

| Interface | Class | Device-provided name | Endpoint | Purpose |
| --- | --- | --- | --- | --- |
| 0 | Audio control | INZONE Buds - Chat | — | Chat function |
| 1 | Audio streaming | — | `0x01` OUT, 192 bytes/ms | Chat playback (48 kHz, 2 × 16-bit) |
| 2 | Audio streaming | — | `0x81` IN, 96 bytes/ms | Microphone (48 kHz, 1 × 16-bit) |
| 3 | Audio control | INZONE Buds - Game | — | Game function |
| 4 | Audio streaming | — | `0x02` OUT, 192 bytes/ms | Game playback (48 kHz, 2 × 16-bit) |
| 5 | HID | Hid Interface | `0x83` IN, interrupt, 64 bytes, 3 ms | Proprietary controls and media keys |

The microphone belongs to the Chat function: the Chat audio-control header
lists interfaces 1 and 2 as its streaming interfaces (`baInterfaceNr`), while
the Game header lists only interface 4. The dongle has no Interface
Association Descriptors. `snd_usb_audio` drives interfaces 0–4 and
`hid-generic` drives interface 5.

## HID interface

The HID interface has only an interrupt IN endpoint. Output and feature reports
must therefore travel as control transfers (`SET_REPORT`/`GET_REPORT`) on
endpoint 0.

The 158-byte report descriptor can be read without root from
`/sys/class/hidraw/hidrawN/device/report_descriptor` and decoded with
`hid-decode` from `hid-tools`. It declares five top-level collections:

| Collection | Report ID | Direction | Payload | Notes |
| --- | --- | --- | --- | --- |
| Vendor page `0xFF13`, usage `0x01` | `0x06` | Output | 61 bytes | Paired with report `0x07` |
| | `0x07` | Input | 61 bytes | |
| Consumer Control | `0x0C` | Input | 6 bits + 2 padding | Volume Up, Volume Down, Mute, Play/Pause, Next, Previous |
| Vendor page `0xFF04`, usage `0x01` | `0x02` | Input and Output | 63 bytes | Same report ID in both directions |
| Vendor page `0xFF03`, usage `0x20` | `0xA0` | Feature | 34 bytes | |
| | `0xA1` | Feature | 22 bytes | |
| Vendor page `0xFF01`, usage `0x20` | `0xB0` | Input | 7 × 1 byte | Seven separate usages, `0x25`–`0x2B` |

`hid-generic` creates four input devices from these collections. One of them,
"Sony INZONE Buds Consumer Control", reports `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN`,
`KEY_MUTE`, `KEY_PLAYPAUSE`, `KEY_NEXTSONG` and `KEY_PREVIOUSSONG`. The others
expose the vendor collections as `ABS_MISC` axes, which do not carry their
content in a usable form.

Access on a default system: the report descriptor is world-readable,
`/dev/hidrawN` is `root:root 0600`, and the `/dev/input/eventN` nodes are
`root:input 0660`.

### Hypotheses, not verified

The descriptor names no usages, so the purpose of every vendor report is
unknown. Only the structure above is established. The following are working
hypotheses to test, not supported features:

- reports `0x06`/`0x07` and report `0x02` look like request/response command
  channels;
- report `0xB0`, seven separate one-byte values sent by the device, is a
  plausible candidate for status such as battery levels;
- feature reports `0xA0`/`0xA1` may carry device information or settings;
- if the earbuds' touch controls are assigned to volume, the Consumer Control
  report would reach the desktop as ordinary volume keys. This has not been
  observed.

The next step is passive: grant the logged-in user read access to the dongle's
hidraw node only, then record input reports while changing one thing at a time,
such as removing an earbud from the case or connecting a charger. No output or
feature report is to be sent until its effect is documented.

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
