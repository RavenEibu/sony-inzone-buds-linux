# Troubleshooting

## Start with diagnostics

Run:

```bash
inzonectl doctor
```

The command prints local USB and PipeWire topology. It does not upload or send
the information anywhere. Review and remove unrelated personal details before
posting its output publicly.

## `cannot connect to the PulseAudio-compatible server`

`inzonectl` uses `pactl`, which talks to PipeWire through `pipewire-pulse`.
Check the user services:

```bash
systemctl --user status pipewire.service pipewire-pulse.service wireplumber.service
```

Restart them if one has failed:

```bash
systemctl --user restart pipewire.service pipewire-pulse.service wireplumber.service
```

`inzonectl doctor` still runs in this state and shows what WirePlumber reports.

## Game and Chat do not both appear

1. Confirm that the dongle's physical switch is in **PC** mode.
2. Check that the PC product ID is present:

   ```bash
   lsusb -d 054c:0ec2
   ```

3. Activate Pro Audio:

   ```bash
   inzonectl profile
   ```

4. Inspect the result:

   ```bash
   inzonectl status
   ```

Expected output includes node names ending in `pro-output-0`, `pro-output-1`
and `pro-input-0`.

## The Analog and S/PDIF outputs disappeared

This is expected. With the generic profiles, the desktop shows the dongle as
**Analog Output** or **Digital Output (S/PDIF)**, one at a time. They are not
extra connectors: Analog is the Chat endpoint and S/PDIF is the Game endpoint,
under ALSA's generic names. Pro Audio exposes both together as
**Sony INZONE Buds - Game** and **Sony INZONE Buds - Chat**. See
[Generic ALSA profile names](hardware.md#generic-alsa-profile-names).

To return to the single generic output, choose another profile for the card in
`pavucontrol` under **Configuration**. The project selects Pro Audio again the
next time `inzonectl profile` or `inzonectl default` runs.

## Extra "INZONE Buds Analog Stereo" or "Mono" devices next to Game and Chat

These are generic-profile nodes left behind while the card changed to Pro
Audio. They use the same ALSA devices as Chat and the microphone, and the mono
input can outrank the INZONE microphone when WirePlumber chooses a default.
This was observed once right after a first installation and could not be
reproduced afterwards.

Cycle the card profile once to remove them:

```bash
pactl set-card-profile alsa_card.usb-Sony_INZONE_Buds-00 output:analog-stereo+input:mono-fallback
inzonectl default
```

`inzonectl default` switches back to Pro Audio and restores the defaults. The
installed WirePlumber rule creates the card directly in Pro Audio, which avoids
the switch that left these nodes behind.

## `inzonectl: command not found`

The installer stores the scripts in `~/.local/bin`. When that directory is not
in the current `PATH`, it creates an `inzonectl` link in `/usr/local/bin` after
displaying a standard `sudo` prompt. It never replaces an existing command.

First check whether the program itself works:

```bash
~/.local/bin/inzonectl status
```

Then check command resolution:

```bash
command -v inzonectl
```

If installation completed after the shell had already failed to find the
command, clear the shell's command cache:

```bash
rehash   # Zsh
hash -r  # Bash
```

Changing from Zsh to Bash does not repair a missing `PATH`; child shells inherit
the parent's exported environment. Re-run `./install.sh` to let the updated
installer create the safe `/usr/local/bin` links when necessary.

The hot-plug service does not depend on the interactive shell's `PATH` because
it resolves `inzonectl` relative to its own installed location.

## The names remain "INZONE Buds Pro"

Check that the fragment exists:

```bash
test -f ~/.config/wireplumber/wireplumber.conf.d/51-inzone-buds.conf
```

Then restart WirePlumber:

```bash
systemctl --user restart wireplumber.service
```

Existing audio streams may pause during the restart.

## Another output remains the default after reconnecting

Check the service:

```bash
systemctl --user status inzone-buds-autoswitch.service
```

Restart it if necessary:

```bash
systemctl --user restart inzone-buds-autoswitch.service
```

The service selects Game only when the Game endpoint newly appears. It does not
continually undo manual output changes while the dongle stays connected.

## Discord uses Game instead of Chat

While Discord is producing audio, open `pavucontrol` and move its playback
stream to **Sony INZONE Buds - Chat**. Set its recording stream to
**Sony INZONE Buds - Microphone**. WirePlumber normally remembers an
application stream's selected destination.

Some Discord builds also expose explicit input and output selectors in Voice &
Video settings. Use the named INZONE endpoints there when available.

## Audio moved to the wrong device after a WirePlumber restart

Reapply the project defaults:

```bash
inzonectl default
```

If another manually saved default continues to win, clear the saved selection
and reconnect the dongle:

```bash
wpctl clear-default
```

This clears saved default selections globally, so use it only when you want
WirePlumber to choose again from available priorities.

## The dongle is in MOBILE/PS5 mode

MOBILE/PS5 mode reports USB product ID `054c:0ec3` and does not provide separate
Game and Chat playback endpoints. Move the physical switch to PC and reconnect
the dongle.

## Restore the previous setup

From a checkout of this repository, run:

```bash
./uninstall.sh
```

The uninstaller removes only the files installed by this project. Timestamped
backups created during installation are preserved.
