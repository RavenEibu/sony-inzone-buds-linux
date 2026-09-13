#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME=${XDG_BIN_HOME:-"$HOME/.local/bin"}
SYSTEM_BIN_DIR=${INZONE_SYSTEM_BIN_DIR:-/usr/local/bin}
WIREPLUMBER_DIR="$CONFIG_HOME/wireplumber/wireplumber.conf.d"
SYSTEMD_USER_DIR="$CONFIG_HOME/systemd/user"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SYSTEM_LINKS_INSTALLED=0

install_one() {
  local source=$1 destination=$2 mode=$3
  mkdir -p "$(dirname "$destination")"
  if [[ -e $destination ]] && ! cmp -s "$source" "$destination"; then
    cp -a "$destination" "${destination}.backup-${TIMESTAMP}"
    printf 'Backed up %s\n' "$destination"
  fi
  install -m "$mode" "$source" "$destination"
}

path_contains() {
  case ":${PATH:-}:" in
    *":$1:"*) return 0 ;;
    *) return 1 ;;
  esac
}

install_system_links_if_needed() {
  local name source destination existing_target

  path_contains "$BIN_HOME" && return 0

  if ! path_contains "$SYSTEM_BIN_DIR"; then
    printf '\nWarning: %s is not in PATH, and %s is not in PATH either.\n' \
      "$BIN_HOME" "$SYSTEM_BIN_DIR" >&2
    printf 'Use the absolute command path or add %s to your shell PATH.\n' \
      "$BIN_HOME" >&2
    return 0
  fi

  if ! command -v sudo >/dev/null 2>&1; then
    printf '\nWarning: %s is not in PATH and sudo is unavailable.\n' "$BIN_HOME" >&2
    printf 'Use the absolute command path or add %s to your shell PATH.\n' \
      "$BIN_HOME" >&2
    return 0
  fi

  # Check every destination before writing either link. Never replace an
  # unrelated system command.
  for name in inzonectl; do
    source="$BIN_HOME/$name"
    destination="$SYSTEM_BIN_DIR/$name"
    if [[ -e $destination || -L $destination ]]; then
      existing_target=$(readlink -- "$destination" 2>/dev/null || true)
      if [[ $existing_target != "$source" ]]; then
        printf '\nWarning: refusing to replace existing %s.\n' "$destination" >&2
        printf 'Use %s directly or resolve the command-name collision.\n' \
          "$source" >&2
        return 0
      fi
    fi
  done

  printf '\n%s is not in the current PATH.\n' "$BIN_HOME"
  printf 'Installing command links in %s so they are available immediately.\n' \
    "$SYSTEM_BIN_DIR"
  sudo mkdir -p -- "$SYSTEM_BIN_DIR"
  for name in inzonectl; do
    source="$BIN_HOME/$name"
    destination="$SYSTEM_BIN_DIR/$name"
    if [[ ! -L $destination ]]; then
      sudo ln -s -- "$source" "$destination"
    fi
  done
  SYSTEM_LINKS_INSTALLED=1
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

install_system_links_if_needed

systemctl --user daemon-reload
systemctl --user enable inzone-buds-autoswitch.service
systemctl --user restart inzone-buds-autoswitch.service
systemctl --user try-restart wireplumber.service || true

# WirePlumber may need a moment to rebuild the nodes after its restart.
sleep 1
"$BIN_HOME/inzonectl" default || true

printf '\nSony INZONE Buds Linux integration installed.\n'
if (( SYSTEM_LINKS_INSTALLED == 1 )) || path_contains "$BIN_HOME"; then
  printf 'Run: inzonectl status\n'
  printf 'If your shell cached an earlier failed lookup, run rehash (Zsh) or hash -r (Bash).\n'
else
  printf 'Run: %s status\n' "$BIN_HOME/inzonectl"
fi
