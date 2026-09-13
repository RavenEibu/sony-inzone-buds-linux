#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TEST_TMP=$(mktemp -d)
trap 'rm -rf -- "$TEST_TMP"' EXIT
LOG_FILE="$TEST_TMP/pactl.log"
MOCK_PACTL="$TEST_TMP/pactl"

cat > "$MOCK_PACTL" <<'EOF'
#!/usr/bin/env bash
set -eu
: "${MOCK_LOG:?}"
case "${1:-} ${2:-} ${3:-}" in
  'list short cards')
    printf '7\talsa_card.usb-Sony_INZONE_Buds-00\tmodule-alsa-card.c\n'
    ;;
  'list short sinks')
    printf '185\talsa_output.usb-Sony_INZONE_Buds-00.pro-output-1\tPipeWire\ts16le 2ch 48000Hz\n'
    printf '191\talsa_output.usb-Sony_INZONE_Buds-00.pro-output-0\tPipeWire\ts16le 2ch 48000Hz\n'
    ;;
  'list short sources')
    printf '196\talsa_input.usb-Sony_INZONE_Buds-00.pro-input-0\tPipeWire\ts16le 1ch 48000Hz\n'
    ;;
  'get-default-sink  ')
    printf 'alsa_output.usb-Sony_INZONE_Buds-00.pro-output-1\n'
    ;;
  'get-default-source  ')
    printf 'alsa_input.usb-Sony_INZONE_Buds-00.pro-input-0\n'
    ;;
  *)
    printf '%q ' "$@" >> "$MOCK_LOG"
    printf '\n' >> "$MOCK_LOG"
    ;;
esac
EOF
chmod +x "$MOCK_PACTL"

export MOCK_LOG="$LOG_FILE"
export PACTL="$MOCK_PACTL"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_log_contains() {
  grep -F -- "$1" "$LOG_FILE" >/dev/null || fail "missing log entry: $1"
}

: > "$LOG_FILE"
"$PROJECT_DIR/bin/inzonectl" balance 70 45 >/dev/null
assert_log_contains 'set-sink-volume alsa_output.usb-Sony_INZONE_Buds-00.pro-output-1 45%'
assert_log_contains 'set-sink-volume alsa_output.usb-Sony_INZONE_Buds-00.pro-output-0 27%'

: > "$LOG_FILE"
"$PROJECT_DIR/bin/inzonectl" volume chat 35 >/dev/null
assert_log_contains 'set-sink-volume alsa_output.usb-Sony_INZONE_Buds-00.pro-output-0 35%'

: > "$LOG_FILE"
"$PROJECT_DIR/bin/inzonectl" default >/dev/null
assert_log_contains 'set-default-sink alsa_output.usb-Sony_INZONE_Buds-00.pro-output-1'
assert_log_contains 'set-default-source alsa_input.usb-Sony_INZONE_Buds-00.pro-input-0'

if "$PROJECT_DIR/bin/inzonectl" balance 101 >/dev/null 2>&1; then
  fail 'invalid balance was accepted'
fi

printf 'All tests passed.\n'
