# Keyboard shortcut examples

`inzonectl` works from any key binding, so no application support is needed.
These examples are suggestions: the commands are checked against `inzonectl
help` by the test suite, but the bindings themselves have not been tried on
every desktop. Adjust paths if `inzonectl` is not on the `PATH` of your
session (`~/.local/bin/inzonectl` for a per-user install).

Useful commands:

| Command | Effect |
| --- | --- |
| `inzonectl game` | Make Game the default output |
| `inzonectl chat` | Make Chat the default output |
| `inzonectl balance 50` | Center Game and Chat |
| `inzonectl balance 20` | Favor Chat (0 = Chat only, 100 = Game only) |
| `inzonectl balance 80` | Favor Game |
| `inzonectl default` | Select Game output and the INZONE microphone |

Volume and mute keys already move Game and Chat together while the dongle is
the default output; see the [mixer guide](gui.md).

## GNOME

Custom shortcuts are stored in dconf. This adds `Super+F9` for "center":

```bash
base=/org/gnome/settings-daemon/plugins/media-keys
path=$base/custom-keybindings/inzone-center/
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings \
  "['$path']"
gsettings set "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$path" \
  name 'INZONE center'
gsettings set "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$path" \
  command 'inzonectl balance 50'
gsettings set "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$path" \
  binding '<Super>F9'
```

This replaces any existing custom shortcut list. If you already have some,
add the new path to the existing array instead (read it first with
`gsettings get ... custom-keybindings`), or use
Settings > Keyboard > Keyboard Shortcuts > Custom Shortcuts.

## KDE Plasma

System Settings > Keyboard > Shortcuts > Add New > Command or Script, then
enter for example `inzonectl balance 50` and assign a key.

## Sway

```text
bindsym $mod+F9  exec inzonectl balance 50
bindsym $mod+F10 exec inzonectl balance 20
bindsym $mod+F11 exec inzonectl balance 80
```

## Hyprland

```text
bind = SUPER, F9,  exec, inzonectl balance 50
bind = SUPER, F10, exec, inzonectl balance 20
bind = SUPER, F11, exec, inzonectl balance 80
```
