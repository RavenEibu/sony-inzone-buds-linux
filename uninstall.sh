#!/usr/bin/env bash
set -euo pipefail

CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME=${XDG_BIN_HOME:-"$HOME/.local/bin"}
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
SYSTEM_BIN_DIR=${INZONE_SYSTEM_BIN_DIR:-/usr/local/bin}
WIREPLUMBER_FILE="$CONFIG_HOME/wireplumber/wireplumber.conf.d/51-inzone-buds.conf"
SERVICE_FILE="$CONFIG_HOME/systemd/user/inzone-buds-autoswitch.service"
APP_DATA_DIR="$DATA_HOME/inzone-buds-mixer"
DESKTOP_FILE="$DATA_HOME/applications/io.github.RavenEibu.InzoneBudsMixer.desktop"
AUTOSTART_FILE="$CONFIG_HOME/autostart/io.github.RavenEibu.InzoneBudsMixer.desktop"
METAINFO_FILE="$DATA_HOME/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml"
ICON_FILE="$DATA_HOME/icons/hicolor/scalable/apps/io.github.RavenEibu.InzoneBudsMixer.svg"
SYMBOLIC_ICON_FILE="$DATA_HOME/icons/hicolor/symbolic/apps/io.github.RavenEibu.InzoneBudsMixer-symbolic.svg"

remove_owned_system_link() {
  local destination="$SYSTEM_BIN_DIR/$1" expected="$BIN_HOME/$1"
  local existing_target
  [[ -L $destination ]] || return 0
  existing_target=$(readlink -- "$destination" 2>/dev/null || true)
  [[ $existing_target == "$expected" ]] || return 0
  if command -v sudo >/dev/null 2>&1; then
    sudo rm -f -- "$destination"
  else
    printf 'Could not remove %s because sudo is unavailable.\n' "$destination" >&2
  fi
}

systemctl --user disable --now inzone-buds-autoswitch.service 2>/dev/null || true

remove_owned_system_link inzonectl
remove_owned_system_link inzone-buds-mixer

rm -f -- "$WIREPLUMBER_FILE"
rm -f -- "$SERVICE_FILE"
rm -f -- "$BIN_HOME/inzonectl"
rm -f -- "$BIN_HOME/inzone-autoswitch"
rm -f -- "$BIN_HOME/inzone-buds-mixer"
rm -f -- "$DESKTOP_FILE"
rm -f -- "$AUTOSTART_FILE"
rm -f -- "$METAINFO_FILE"
rm -f -- "$ICON_FILE"
rm -f -- "$SYMBOLIC_ICON_FILE"
rm -f -- "$APP_DATA_DIR/audio.py"
rm -f -- "$APP_DATA_DIR/app.py"
rm -f -- "$APP_DATA_DIR/autostart.py"
rm -f -- "$APP_DATA_DIR/tray.py"
rmdir -- "$APP_DATA_DIR" 2>/dev/null || true

systemctl --user daemon-reload
systemctl --user try-restart wireplumber.service || true

printf 'Sony INZONE Buds Linux integration removed.\n'
printf 'Timestamped installer backups, if present, were preserved.\n'
