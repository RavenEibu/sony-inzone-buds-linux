#!/usr/bin/env bash
set -euo pipefail

CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME=${XDG_BIN_HOME:-"$HOME/.local/bin"}
SYSTEM_BIN_DIR=${INZONE_SYSTEM_BIN_DIR:-/usr/local/bin}
WIREPLUMBER_FILE="$CONFIG_HOME/wireplumber/wireplumber.conf.d/51-inzone-buds.conf"
SERVICE_FILE="$CONFIG_HOME/systemd/user/inzone-buds-autoswitch.service"

remove_owned_system_link() {
  local name=$1 destination="$SYSTEM_BIN_DIR/$1" expected="$BIN_HOME/$1"
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

rm -f -- "$WIREPLUMBER_FILE"
rm -f -- "$SERVICE_FILE"
rm -f -- "$BIN_HOME/inzonectl"
rm -f -- "$BIN_HOME/inzone-autoswitch"

systemctl --user daemon-reload
systemctl --user try-restart wireplumber.service || true

printf 'Sony INZONE Buds Linux integration removed.\n'
printf 'Timestamped installer backups, if present, were preserved.\n'
