#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME=${XDG_BIN_HOME:-"$HOME/.local/bin"}
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
SYSTEM_BIN_DIR=${INZONE_SYSTEM_BIN_DIR:-/usr/local/bin}
WIREPLUMBER_DIR="$CONFIG_HOME/wireplumber/wireplumber.conf.d"
SYSTEMD_USER_DIR="$CONFIG_HOME/systemd/user"
APP_DATA_DIR="$DATA_HOME/inzone-buds-mixer"
APPLICATIONS_DIR="$DATA_HOME/applications"
METAINFO_DIR="$DATA_HOME/metainfo"
ICON_SCALABLE_DIR="$DATA_HOME/icons/hicolor/scalable/apps"
ICON_SYMBOLIC_DIR="$DATA_HOME/icons/hicolor/symbolic/apps"
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

# Install a *.in file after replacing @BINDIR@ with the real command directory.
install_template() {
  local source=$1 destination=$2 rendered bindir
  rendered=$(mktemp)
  # Escape sed replacement metacharacters so any directory name is literal.
  bindir=$(printf '%s' "$BIN_HOME" | sed 's/[\\|&]/\\&/g')
  sed "s|@BINDIR@|$bindir|g" "$source" > "$rendered"
  install_one "$rendered" "$destination" 0644
  rm -f -- "$rendered"
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
  for name in inzonectl inzone-buds-mixer; do
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
  for name in inzonectl inzone-buds-mixer; do
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
install_one "$PROJECT_DIR/bin/inzone-buds-mixer" "$BIN_HOME/inzone-buds-mixer" 0755
install_template "$PROJECT_DIR/systemd/user/inzone-buds-autoswitch.service.in" \
  "$SYSTEMD_USER_DIR/inzone-buds-autoswitch.service"

for python_file in audio.py app.py tray.py; do
  install_one "$PROJECT_DIR/src/inzone_buds_mixer/$python_file" \
    "$APP_DATA_DIR/$python_file" 0644
done

install_one \
  "$PROJECT_DIR/data/icons/hicolor/scalable/apps/io.github.RavenEibu.InzoneBudsMixer.svg" \
  "$ICON_SCALABLE_DIR/io.github.RavenEibu.InzoneBudsMixer.svg" 0644
install_one \
  "$PROJECT_DIR/data/icons/hicolor/symbolic/apps/io.github.RavenEibu.InzoneBudsMixer-symbolic.svg" \
  "$ICON_SYMBOLIC_DIR/io.github.RavenEibu.InzoneBudsMixer-symbolic.svg" 0644
install_one \
  "$PROJECT_DIR/data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml" \
  "$METAINFO_DIR/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml" 0644

install_template \
  "$PROJECT_DIR/data/applications/io.github.RavenEibu.InzoneBudsMixer.desktop.in" \
  "$APPLICATIONS_DIR/io.github.RavenEibu.InzoneBudsMixer.desktop"

install_system_links_if_needed

systemctl --user daemon-reload
systemctl --user enable inzone-buds-autoswitch.service
systemctl --user restart inzone-buds-autoswitch.service
systemctl --user try-restart wireplumber.service || true

# WirePlumber may need a moment to rebuild the nodes after its restart.
sleep 1
"$BIN_HOME/inzonectl" default || true

if ! python3 -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk' \
    >/dev/null 2>&1; then
  printf '\nWarning: the command-line integration was installed, but the GTK4 app needs\n' >&2
  printf 'Python GObject bindings and GTK4. See the README dependency table.\n' >&2
fi

printf '\nSony INZONE Buds Linux integration installed.\n'
if (( SYSTEM_LINKS_INSTALLED == 1 )) || path_contains "$BIN_HOME"; then
  printf 'Run: inzonectl status\n'
  printf 'Open: inzone-buds-mixer\n'
  printf 'If your shell cached an earlier failed lookup, run rehash (Zsh) or hash -r (Bash).\n'
else
  printf 'Run: %s status\n' "$BIN_HOME/inzonectl"
fi
