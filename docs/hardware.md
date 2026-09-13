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
