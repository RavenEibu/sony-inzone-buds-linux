#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TEST_TMP=$(mktemp -d)
trap 'rm -rf -- "$TEST_TMP"' EXIT

MOCK_BIN="$TEST_TMP/mock-bin"
USER_BIN="$TEST_TMP/user-bin"
SYSTEM_BIN="$TEST_TMP/system-bin"
CONFIG_HOME="$TEST_TMP/config"
mkdir -p "$MOCK_BIN" "$SYSTEM_BIN"

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
INZONE_SYSTEM_BIN_DIR="$SYSTEM_BIN" \
  "$PROJECT_DIR/install.sh" >/dev/null 2>&1

[[ -x $USER_BIN/inzonectl ]]
[[ -x $USER_BIN/inzone-autoswitch ]]
[[ -L $SYSTEM_BIN/inzonectl ]]
[[ $(readlink "$SYSTEM_BIN/inzonectl") == "$USER_BIN/inzonectl" ]]
[[ $(PATH="$TEST_PATH" command -v inzonectl) == "$SYSTEM_BIN/inzonectl" ]]

PATH="$TEST_PATH" \
XDG_CONFIG_HOME="$CONFIG_HOME" \
XDG_BIN_HOME="$USER_BIN" \
INZONE_SYSTEM_BIN_DIR="$SYSTEM_BIN" \
  "$PROJECT_DIR/uninstall.sh" >/dev/null 2>&1

[[ ! -e $SYSTEM_BIN/inzonectl ]]
[[ ! -e $USER_BIN/inzonectl ]]

printf 'Install PATH tests passed.\n'
