#!/usr/bin/env bash
set -euo pipefail

CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME=${XDG_BIN_HOME:-"$HOME/.local/bin"}
WIREPLUMBER_FILE="$CONFIG_HOME/wireplumber/wireplumber.conf.d/51-inzone-buds.conf"
SERVICE_FILE="$CONFIG_HOME/systemd/user/inzone-buds-autoswitch.service"

systemctl --user disable --now inzone-buds-autoswitch.service 2>/dev/null || true

rm -f -- "$WIREPLUMBER_FILE"
rm -f -- "$SERVICE_FILE"
rm -f -- "$BIN_HOME/inzonectl"
rm -f -- "$BIN_HOME/inzone-autoswitch"

systemctl --user daemon-reload
systemctl --user try-restart wireplumber.service || true

printf 'Sony INZONE Buds Linux integration removed.\n'
printf 'Timestamped installer backups, if present, were preserved.\n'
