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

# Game/Chat volume commands tell inzone-autoswitch that the change is
# intentional; the microphone is not part of the Game/Chat balance.
export INZONE_RUNTIME_DIR="$TEST_TMP/run"
mkdir -p "$INZONE_RUNTIME_DIR"
MARKER="$INZONE_RUNTIME_DIR/inzone-buds-manual-change"
for command in 'balance 50 30' 'volume game 40' 'volume chat 40'; do
  rm -f -- "$MARKER"
  # shellcheck disable=SC2086 # split the command into its arguments
  "$PROJECT_DIR/bin/inzonectl" $command >/dev/null
  [[ $(< "$MARKER") =~ ^[0-9]+$ ]] || fail "$command did not mark an intentional change"
done
rm -f -- "$MARKER"
"$PROJECT_DIR/bin/inzonectl" volume mic 80 >/dev/null
[[ ! -e $MARKER ]] || fail 'microphone volume marked a Game/Chat change'

if "$PROJECT_DIR/bin/inzonectl" balance 101 >/dev/null 2>&1; then
  fail 'invalid balance was accepted'
fi

# An unreachable audio server must produce an explanation, not a silent exit.
FAILING_PACTL="$TEST_TMP/pactl-down"
cat > "$FAILING_PACTL" <<'EOF'
#!/usr/bin/env bash
printf 'Connection failure: Connection refused\n' >&2
exit 1
EOF
chmod +x "$FAILING_PACTL"

for command in status 'volume game 40'; do
  # shellcheck disable=SC2086 # split the command into its arguments
  if error_output=$(PACTL="$FAILING_PACTL" "$PROJECT_DIR/bin/inzonectl" $command 2>&1); then
    fail "$command succeeded without an audio server"
  fi
  [[ $error_output == *'pipewire-pulse'* ]] ||
    fail "$command did not explain the audio server failure: ${error_output:-<empty>}"
done

PACTL="$FAILING_PACTL" "$PROJECT_DIR/bin/inzonectl" help >/dev/null ||
  fail 'help required an audio server'

# doctor reports the PipeWire and WirePlumber versions, even if a tool is missing.
MOCK_PW="$TEST_TMP/pipewire"
MOCK_WP="$TEST_TMP/wireplumber"
printf '#!/usr/bin/env bash\nprintf "pipewire\\nCompiled with libpipewire 1.2.3\\nLinked with libpipewire 1.2.4\\n"\n' > "$MOCK_PW"
printf '#!/usr/bin/env bash\nprintf "wireplumber\\nCompiled with libwireplumber 0.5.1\\nLinked with libwireplumber 0.5.2\\n"\n' > "$MOCK_WP"
chmod +x "$MOCK_PW" "$MOCK_WP"
MOCK_WPCTL="$TEST_TMP/wpctl"
printf '#!/usr/bin/env bash\nexit 0\n' > "$MOCK_WPCTL"
chmod +x "$MOCK_WPCTL"
doctor_out=$(PIPEWIRE="$MOCK_PW" WIREPLUMBER="$MOCK_WP" WPCTL="$MOCK_WPCTL" \
  "$PROJECT_DIR/bin/inzonectl" doctor)
grep -Fx 'PipeWire: 1.2.4' <<<"$doctor_out" >/dev/null || fail 'doctor missing PipeWire version'
grep -Fx 'WirePlumber: 0.5.2' <<<"$doctor_out" >/dev/null || fail 'doctor missing WirePlumber version'
doctor_out=$(PIPEWIRE=/nonexistent WIREPLUMBER=/nonexistent WPCTL="$MOCK_WPCTL" \
  "$PROJECT_DIR/bin/inzonectl" doctor) || fail 'doctor failed without version tools'
grep -Fx 'PipeWire: unknown' <<<"$doctor_out" >/dev/null || fail 'doctor should report unknown PipeWire'

# The version must match the newest CHANGELOG entry and AppStream release.
version=$("$PROJECT_DIR/bin/inzonectl" --version)
version=${version#inzonectl }
changelog_version=$(sed -n 's/^## \([0-9][0-9.]*\) - .*/\1/p' "$PROJECT_DIR/CHANGELOG.md" | head -1)
metainfo_version=$(sed -n 's/.*<release version="\([^"]*\)".*/\1/p' \
  "$PROJECT_DIR/data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml" | head -1)
[[ $version == "$changelog_version" ]] ||
  fail "inzonectl $version does not match CHANGELOG $changelog_version"
[[ $version == "$metainfo_version" ]] ||
  fail "inzonectl $version does not match metainfo $metainfo_version"

printf 'All tests passed.\n'
