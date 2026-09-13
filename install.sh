#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME=${XDG_BIN_HOME:-"$HOME/.local/bin"}
WIREPLUMBER_DIR="$CONFIG_HOME/wireplumber/wireplumber.conf.d"
SYSTEMD_USER_DIR="$CONFIG_HOME/systemd/user"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

install_one() {
  local source=$1 destination=$2 mode=$3
  mkdir -p "$(dirname "$destination")"
  if [[ -e $destination ]] && ! cmp -s "$source" "$destination"; then
    cp -a "$destination" "${destination}.backup-${TIMESTAMP}"
    printf 'Backed up %s\n' "$destination"
  fi
  install -m "$mode" "$source" "$destination"
}

for command_name in pactl systemctl; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

install_one "$PROJECT_DIR/config/wireplumber/51-inzone-buds.conf" \
  "$WIREPLUMBER_DIR/51-inzone-buds.conf" 0644
install_one "$PROJECT_DIR/bin/inzonectl" "$BIN_HOME/inzonectl" 0755
install_one "$PROJECT_DIR/bin/inzone-autoswitch" "$BIN_HOME/inzone-autoswitch" 0755
install_one "$PROJECT_DIR/systemd/user/inzone-buds-autoswitch.service" \
  "$SYSTEMD_USER_DIR/inzone-buds-autoswitch.service" 0644

systemctl --user daemon-reload
systemctl --user enable --now inzone-buds-autoswitch.service
systemctl --user try-restart wireplumber.service || true

# WirePlumber may need a moment to rebuild the nodes after its restart.
sleep 1
"$BIN_HOME/inzonectl" default || true

printf '\nSony INZONE Buds Linux integration installed.\n'
printf 'Run: %s status\n' "$BIN_HOME/inzonectl"
