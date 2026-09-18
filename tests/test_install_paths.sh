#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TEST_TMP=$(mktemp -d)
trap 'rm -rf -- "$TEST_TMP"' EXIT

MOCK_BIN="$TEST_TMP/mock-bin"
USER_BIN="$TEST_TMP/user-bin"
SYSTEM_BIN="$TEST_TMP/system-bin"
CONFIG_HOME="$TEST_TMP/config"
DATA_HOME="$TEST_TMP/data"
mkdir -p "$MOCK_BIN" "$SYSTEM_BIN" "$DATA_HOME"

cat > "$MOCK_BIN/systemctl" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF

cat > "$MOCK_BIN/sudo" <<'EOF'
#!/usr/bin/env bash
exec "$@"
EOF

cat > "$MOCK_BIN/pactl" <<'EOF'
#!/usr/bin/env bash
case "${1:-} ${2:-} ${3:-}" in
  'list short cards'|'list short sinks'|'list short sources') exit 0 ;;
  *) exit 0 ;;
esac
EOF

chmod +x "$MOCK_BIN/systemctl" "$MOCK_BIN/sudo" "$MOCK_BIN/pactl"

TEST_PATH="$MOCK_BIN:$SYSTEM_BIN:/usr/bin"

PATH="$TEST_PATH" \
XDG_CONFIG_HOME="$CONFIG_HOME" \
XDG_BIN_HOME="$USER_BIN" \
XDG_DATA_HOME="$DATA_HOME" \
INZONE_SYSTEM_BIN_DIR="$SYSTEM_BIN" \
  "$PROJECT_DIR/install.sh" >/dev/null 2>&1

[[ -x $USER_BIN/inzonectl ]]
[[ -x $USER_BIN/inzone-autoswitch ]]
[[ -x $USER_BIN/inzone-buds-mixer ]]
[[ -L $SYSTEM_BIN/inzonectl ]]
[[ -L $SYSTEM_BIN/inzone-buds-mixer ]]
[[ $(readlink "$SYSTEM_BIN/inzonectl") == "$USER_BIN/inzonectl" ]]
[[ $(readlink "$SYSTEM_BIN/inzone-buds-mixer") == "$USER_BIN/inzone-buds-mixer" ]]
[[ $(PATH="$TEST_PATH" command -v inzonectl) == "$SYSTEM_BIN/inzonectl" ]]
[[ -f $DATA_HOME/inzone-buds-mixer/app.py ]]
[[ -f $DATA_HOME/inzone-buds-mixer/autostart.py ]]
[[ -f $DATA_HOME/applications/io.github.RavenEibu.InzoneBudsMixer.desktop ]]
grep -F "Exec=$USER_BIN/inzone-buds-mixer" \
  "$DATA_HOME/applications/io.github.RavenEibu.InzoneBudsMixer.desktop" >/dev/null
[[ -f $DATA_HOME/icons/hicolor/scalable/apps/io.github.RavenEibu.InzoneBudsMixer.svg ]]
[[ -f $CONFIG_HOME/inzone-buds-mixer/config ]]
cmp -s "$PROJECT_DIR/config/inzone-buds-mixer/config.example" \
  "$CONFIG_HOME/inzone-buds-mixer/config"
# The service must follow XDG_BIN_HOME instead of assuming ~/.local/bin.
grep -Fx "ExecStart=\"$USER_BIN/inzone-autoswitch\"" \
  "$CONFIG_HOME/systemd/user/inzone-buds-autoswitch.service" >/dev/null

# Reinstalling over an older version backs up only edited configuration.
WIREPLUMBER_CONF="$CONFIG_HOME/wireplumber/wireplumber.conf.d/51-inzone-buds.conf"
SERVICE="$CONFIG_HOME/systemd/user/inzone-buds-autoswitch.service"
USER_CONFIG="$CONFIG_HOME/inzone-buds-mixer/config"
echo '# edited by the user' >> "$WIREPLUMBER_CONF"
echo '# edited by the user' >> "$SERVICE"
echo '# edited by the user' >> "$USER_CONFIG"
echo '# older version' >> "$USER_BIN/inzonectl"
echo '# older version' >> "$DATA_HOME/inzone-buds-mixer/app.py"

PATH="$TEST_PATH" \
XDG_CONFIG_HOME="$CONFIG_HOME" \
XDG_BIN_HOME="$USER_BIN" \
XDG_DATA_HOME="$DATA_HOME" \
INZONE_SYSTEM_BIN_DIR="$SYSTEM_BIN" \
  "$PROJECT_DIR/install.sh" >/dev/null 2>&1

backups() { compgen -G "$1.backup-*" | wc -l; }
(( $(backups "$WIREPLUMBER_CONF") == 1 )) || { echo 'FAIL: WirePlumber config not backed up' >&2; exit 1; }
(( $(backups "$SERVICE") == 1 )) || { echo 'FAIL: service not backed up' >&2; exit 1; }
(( $(backups "$USER_CONFIG") == 1 )) || { echo 'FAIL: user config not backed up' >&2; exit 1; }
(( $(backups "$USER_BIN/inzonectl") == 0 )) || { echo 'FAIL: program was backed up' >&2; exit 1; }
(( $(backups "$DATA_HOME/inzone-buds-mixer/app.py") == 0 )) || { echo 'FAIL: app.py was backed up' >&2; exit 1; }
cmp -s "$PROJECT_DIR/bin/inzonectl" "$USER_BIN/inzonectl"
cmp -s "$PROJECT_DIR/src/inzone_buds_mixer/app.py" "$DATA_HOME/inzone-buds-mixer/app.py"
cmp -s "$PROJECT_DIR/config/wireplumber/51-inzone-buds.conf" "$WIREPLUMBER_CONF"

# The mixer's launch-at-login entry is removed on uninstall.
AUTOSTART_FILE="$CONFIG_HOME/autostart/io.github.RavenEibu.InzoneBudsMixer.desktop"
mkdir -p "$(dirname "$AUTOSTART_FILE")"
printf '[Desktop Entry]\nType=Application\n' > "$AUTOSTART_FILE"

PATH="$TEST_PATH" \
XDG_CONFIG_HOME="$CONFIG_HOME" \
XDG_BIN_HOME="$USER_BIN" \
XDG_DATA_HOME="$DATA_HOME" \
INZONE_SYSTEM_BIN_DIR="$SYSTEM_BIN" \
  "$PROJECT_DIR/uninstall.sh" >/dev/null 2>&1

[[ ! -e $SYSTEM_BIN/inzonectl ]]
[[ ! -e $SYSTEM_BIN/inzone-buds-mixer ]]
[[ ! -e $USER_BIN/inzonectl ]]
[[ ! -e $USER_BIN/inzone-buds-mixer ]]
[[ ! -e $DATA_HOME/applications/io.github.RavenEibu.InzoneBudsMixer.desktop ]]
[[ ! -e $AUTOSTART_FILE ]]
[[ ! -e $DATA_HOME/inzone-buds-mixer ]]
[[ ! -e $USER_CONFIG ]]

printf 'Install PATH tests passed.\n'
