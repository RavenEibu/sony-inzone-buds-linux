# Graphical mixer

`inzone-buds-mixer` is a GTK4 front end for the verified `inzonectl` and
PipeWire integration. It does not emulate Sony's Windows application or send
undocumented commands to the earbuds.

## Controls

| Control | Result |
| --- | --- |
| Overall volume | Sets the maximum of the Game and Chat endpoints |
| Game / Chat balance | Attenuates Game or Chat relative to the maximum |
| Microphone volume | Sets the native microphone endpoint level |
| Use Game output + INZONE microphone | Restores the recommended defaults |

Balance `0` selects the Chat side, `50` gives both endpoints the same volume,
and `100` selects the Game side. **Both endpoints are at maximum when balance
is 50 and overall volume is 100%.** No virtual sink or software resampling is
created; the dongle receives both native playback streams.

The application follows `pactl subscribe` and refreshes as soon as PipeWire
reports a sink, source, card or default-device change. Volume keys, the desktop
sound panel and other mixers are therefore reflected immediately, as are
unplugging and reconnecting the dongle. Client and per-application stream
events are ignored, since every `pactl` call, including the mixer's own reads,
produces them. If the event stream ends, for example when `pipewire-pulse`
restarts, it is started again; a two-second poll remains as a fallback.
Slider changes are briefly coalesced before invoking `inzonectl`, which avoids
sending an unnecessary command for every pixel of pointer movement. A periodic
refresh that was read before, or while, a slider change is pending or being
applied is discarded, so it cannot move the slider back to the old level; a
new refresh runs after every applied change.

## Tray integration

The application exports `org.kde.StatusNotifierItem` over the session D-Bus.
KDE Plasma supports this interface directly. GNOME Shell requires a compatible
extension, such as **AppIndicator and KStatusNotifierItem Support**.

Clicking the tray icon shows or hides the mixer. When a StatusNotifierItem
watcher is present, closing the window hides it and keeps the process running.
Without a watcher, closing the window exits normally so the application cannot
become inaccessible.

Right-clicking the indicator opens a desktop-native D-Bus menu containing
**Show Window** and **Quit**. The menu is rendered by the StatusNotifierHost,
rather than positioned by the application, which also works under Wayland.

## Light and dark appearance

The mixer reads `org.freedesktop.appearance color-scheme` from XDG Desktop
Portal and watches its `SettingChanged` signal. The application switches its
window and header colors immediately when the desktop preference changes. The
portal value selects GTK's application-local theme variant before the window is
constructed, so controls and the header start with the correct appearance. The
portal remains the independent source of truth, preventing that GTK preference
from becoming sticky when the desktop returns to normal/light mode. GTK
color-scheme and theme-name fallbacks are retained for desktops without a
working settings portal.

## Architecture

The GTK process does not duplicate device matching rules. Read operations use
`pactl`; mutations use the adjacent `inzonectl` installation. This preserves a
single tested implementation for profile activation, endpoint discovery and
balance calculations.

## Packaging names

The source package and native distribution package are named
`inzone-buds-mixer`. The planned precompiled AUR variant is named
`inzone-buds-mixer-bin`. Both names explicitly identify the supported hardware.

The application is unofficial and is not affiliated with or endorsed by Sony.
The original project logo is deliberately abstract and contains no Sony or
INZONE wordmark.
