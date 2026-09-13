# Troubleshooting

## Start with diagnostics

Run:

```bash
inzonectl doctor
```

The command prints local USB and PipeWire topology. It does not upload or send
the information anywhere. Review and remove unrelated personal details before
posting its output publicly.

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
