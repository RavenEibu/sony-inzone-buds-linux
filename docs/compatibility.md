# Compatibility with older systems

This page answers "would it run on a PC from 5, 10, 15 or 20 years ago?" with
what was **measured**, what is an **estimate**, and what was **not verified**.
The dongle itself dates from 2023, so the question is about older computers
and older software stacks driving it.

## What the program needs

| Part | Needs | Why |
| --- | --- | --- |
| `inzonectl`, `inzone-autoswitch`, `install.sh` | Bash 4.0, `pactl`, `awk`, `sed` | `${var,,}` (Bash 4.0) in the dongle check; Bash 3.x fails with "bad substitution" |
| WirePlumber rules (`51-inzone-buds.conf`) | WirePlumber 0.5 | the `wireplumber.conf.d` SPA-JSON format; older versions ignore the file |
| Mixer and tray | Python 3.7 or newer (README states 3.10 as the tested floor), PyGObject, GTK 4 | no syntax or library call newer than Python 3.7 (`vermin`, plus the Python 3.7-3.10 CI jobs); GTK 4 exists since December 2020 |
| Audio | PipeWire with its PulseAudio layer (`pactl`) | the Pro Audio profile with separate Game/Chat endpoints |

## Typical PCs by year

The hardware and software columns are typical consumer setups of those years,
from general knowledge rather than from a survey; treat them as orientation.

| Year | Typical PC | Typical Linux stack | Verdict for this program |
| --- | --- | --- | --- |
| 2006 (20 years) | Pentium 4 / Core 2 Duo, 1-2 GB RAM | Bash 3.1/3.2, Python 2.4/2.5, GTK 2, ALSA with early PulseAudio | **Not supported.** Bash 3.2 fails on the dongle check (verified); no GTK 4, no PipeWire, no Python 3 |
| 2011 (15 years) | Core i3/i5 (2nd gen), 4 GB | Bash 4.2, Python 2.7 / 3.2, GTK 3.0, PulseAudio 0.9-1.0 | **Shell scripts run** under Bash 4.2 (verified with a real Bash 4.2); **mixer not possible** (no GTK 4, no Python 3.7); no PipeWire, so the audio layer the scripts expect is absent |
| 2016 (10 years) | Core i5-6500, 8 GB | Bash 4.3, Python 3.5, GTK 3.18, PulseAudio 8 | **Shell scripts run** under Bash 4.3/4.4 (verified); mixer not possible (Python 3.5, no GTK 4); no PipeWire |
| 2021 (5 years) | Ryzen 5 3600 / Core i5-10400, 16 GB | Bash 5.0/5.1, Python 3.8-3.10, GTK 4.0-4.6 (Ubuntu 22.04: 4.6), PipeWire 0.3.x with WirePlumber 0.4 | **Mixer and scripts run** on GTK 4.6 / Python 3.10 (Ubuntu 22.04 job in CI); the WirePlumber rule file is for 0.5 and is ignored by 0.4, so endpoint names and Pro Audio priority fall back to what `inzone-autoswitch` does |
| today | Ryzen 7 9800X3D, 32 GB | everything current | developed and tested here, with the dongle |

## Found by the older-systems checks

The Ubuntu 20.04 job (Python 3.8, 2020) caught a real bug: `install.sh` and the
Debian build failed on Python older than 3.9 because `tools/localize-metainfo.py`
used `ElementTree.indent`. It now indents by hand and the whole tool needs only
Python 3.7 (`vermin`).

The same job found a second one: `audio.py` subscripted
`subprocess.CompletedProcess[str]` at runtime, which needs Python 3.9, so the
mixer backend crashed at import on Python 3.8. It is now a quoted annotation.
The first version of the Python CI jobs did not stop on failing tests (the
loop lacked `set -e`), which hid this on 3.7 and 3.8; that is fixed too.

## Measured: older Bash

Real Bash releases built from source (3.2.57, 4.0, 4.2, 4.3, 4.4, 5.0) were put
first in `PATH`, so every script's `#!/usr/bin/env bash` resolved to them.
`inzonectl`, the installer, the launcher and the autoswitch logic pass their
tests on 4.0 through 5.0. On 3.2.57 the tests pass only because they replace the
USB lookup; running `inzonectl status` for real stops with
`${vendor,,}: bad substitution`. Hence the Bash 4 requirement in the README.
The `Older systems` workflow repeats the 4.0-5.0 runs in CI.

## Measured and estimated: resources

`tools/emulate-pc.sh` limits the application's memory with a systemd user
cgroup (that part is enforced: the program is killed at the cap) and **projects**
the time on a slower CPU as `wait + cpu * 100 / speed`, with `speed` a rough
single-thread performance relative to the machine it runs on. CPU quotas were
not used because this kernel accepted `cpu.max` without throttling. The numbers
below come from the development machine (Ryzen 7 9800X3D), median of 5 runs;
"cpu" is the measured CPU time in ms.

| Profile | Assumed speed | App memory cap | `inzonectl status` | `inzonectl doctor` | Mixer cold start |
| --- | --- | --- | --- | --- | --- |
| 2006 | 8 % | 256 MB | 212 ms (cpu 16) | 420 ms (cpu 33) | 2962 ms (cpu 237) |
| 2011 | 25 % | 512 MB | 60 ms (cpu 13) | 118 ms (cpu 29) | 948 ms (cpu 237) |
| 2016 | 40 % | 1 GB | 41 ms (cpu 13) | 72 ms (cpu 28) | 595 ms (cpu 238) |
| 2021 | 65 % | 2 GB | 29 ms (cpu 14) | 47 ms (cpu 29) | 361 ms (cpu 235) |
| today | 100 % | none | 20 ms (cpu 12) | 29 ms (cpu 27) | 230 ms (cpu 230) |

Reading it: the work is small. Even at an assumed 8 % of today's speed the CLI
answers in well under half a second and the mixer opens in about three seconds.
The mixer window still started with its memory capped at 48 MB (the process
alone; GTK's shared libraries are page cache and are not counted in that cap),
and idle it showed about 67 MB resident and no measurable CPU over 10 s. The
speed percentages are guesses, not benchmarks, and none of this reproduces a
real old CPU's caches, disk, graphics or kernel.

## Not verified

- Anything on real old hardware or old kernels.
- PulseAudio-only systems: the scripts call `pactl`, which PulseAudio also
  provides, but the Pro Audio profile and the Game/Chat endpoints were only
  checked with PipeWire.
- Whether the dongle enumerates correctly on pre-2010 USB controllers.

## Reproduce

```bash
tools/emulate-pc.sh 5        # needs systemd --user and a display for the mixer row
```

The Bash, Python and distribution checks run in CI (`Older systems` workflow).
