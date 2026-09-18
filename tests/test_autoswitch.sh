#!/usr/bin/env bash
# Volume-linking tests for inzone-autoswitch with a stateful pactl mock.
set -euo pipefail

PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TEST_TMP=$(mktemp -d)
trap 'rm -rf -- "$TEST_TMP"' EXIT
STATE="$TEST_TMP/state"
mkdir -p "$STATE" "$TEST_TMP/run"

cat > "$TEST_TMP/pactl" <<'EOF'
#!/usr/bin/env bash
set -eu
: "${MOCK_STATE:?}"
endpoint() { [[ $1 == *pro-output-1 ]] && echo game || echo chat; }
case "${1:-}" in
  list)
    printf '72\talsa_output.usb-Sony_INZONE_Buds-00.pro-output-1\tPipeWire\n'
    printf '77\talsa_output.usb-Sony_INZONE_Buds-00.pro-output-0\tPipeWire\n'
    ;;
  get-sink-volume)
    v=$(< "$MOCK_STATE/$(endpoint "$2").vol")
    printf 'Volume: aux0: %s /  %s%% / 0.00 dB,   aux1: %s /  %s%% / 0.00 dB\n' \
      "$v" $(( v * 100 / 65536 )) "$v" $(( v * 100 / 65536 ))
    printf '        balance 0.00\n'
    ;;
  get-sink-mute)
    [[ $(< "$MOCK_STATE/$(endpoint "$2").mute") == 1 ]] && echo 'Mute: yes' || echo 'Mute: no'
    ;;
  set-sink-volume)
    value=$3
    [[ $value == *% ]] && value=$(( ${value%\%} * 65536 / 100 ))
    echo "$value" > "$MOCK_STATE/$(endpoint "$2").vol"
    echo "set-sink-volume $(endpoint "$2") $value" >> "$MOCK_STATE/log"
    ;;
  set-sink-mute)
    echo "$3" > "$MOCK_STATE/$(endpoint "$2").mute"
    echo "set-sink-mute $(endpoint "$2") $3" >> "$MOCK_STATE/log"
    ;;
  *) exit 0 ;;
esac
EOF
chmod +x "$TEST_TMP/pactl"

export MOCK_STATE="$STATE"
export PACTL="$TEST_TMP/pactl"
export INZONE_RUNTIME_DIR="$TEST_TMP/run"
export INZONE_CONFIG_FILE="$TEST_TMP/no-such-config"  # do not read the real user config

# shellcheck source-path=SCRIPTDIR source=../bin/inzone-autoswitch
source "$PROJECT_DIR/bin/inzone-autoswitch"
set -euo pipefail  # the sourced script only sets -u

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

pct() { echo $(( $1 * 65536 / 100 )); }
set_state() {  # GAME_PERCENT CHAT_PERCENT [GAME_MUTE CHAT_MUTE]
  pct "$1" > "$STATE/game.vol"
  pct "$2" > "$STATE/chat.vol"
  echo "${3:-0}" > "$STATE/game.mute"
  echo "${4:-0}" > "$STATE/chat.mute"
}
volume_is() {  # ENDPOINT EXPECTED_RAW DESCRIPTION
  local actual
  actual=$(< "$STATE/$1.vol")
  (( actual == $2 )) || fail "$3: $1 is $actual, expected $2"
}
start_link() {
  link_reset
  link_grace_until=0  # skip the device-appearance grace period
  rm -f -- "$INZONE_RUNTIME_DIR/inzone-buds-manual-change"
  link_volumes      # adopt the current volumes as the reference
}
key_press() {  # ENDPOINT PERCENT: a change made outside this project
  pct "$2" > "$STATE/$1.vol"
  link_volumes
}

# A volume key on Game scales Chat by the same factor.
set_state 60 30
start_link
key_press game 50
volume_is chat "$(scale_volume "$(pct 30)" "$(pct 50)" "$(pct 60)")" 'key press on Game'

# The balance survives a trip through zero without accumulated rounding.
key_press game 0
volume_is chat 0 'Game lowered to zero'
key_press game 60
volume_is chat "$(pct 30)" 'Game raised back'

# A key press on Chat (when it is the default output) scales Game.
key_press chat 15
volume_is game "$(scale_volume "$(pct 60)" "$(pct 15)" "$(pct 30)")" 'key press on Chat'

# inzonectl marks its changes as intentional: the other endpoint is not
# touched, and the new volumes become the balance reference.
set_state 60 30
start_link
date +%s%N > "$INZONE_RUNTIME_DIR/inzone-buds-manual-change"
key_press game 80
volume_is chat "$(pct 30)" 'intentional Game change'
rm -f -- "$INZONE_RUNTIME_DIR/inzone-buds-manual-change"
key_press game 40
volume_is chat "$(scale_volume "$(pct 30)" "$(pct 40)" "$(pct 80)")" 'key press after intentional change'

# Both endpoints changing together is a balance change, not a key press.
set_state 60 30
start_link
pct 50 > "$STATE/game.vol"
pct 50 > "$STATE/chat.vol"
: > "$STATE/log"
link_volumes
[[ ! -s $STATE/log ]] || fail 'balance change was followed'
key_press game 25
volume_is chat "$(pct 25)" 'key press after balance change'

# The louder side is capped at 100%.
set_state 50 100
start_link
key_press game 60
volume_is chat 65536 'Chat capped at 100%'

# Muting either endpoint outside the project mutes the other.
set_state 60 30
start_link
echo 1 > "$STATE/game.mute"
link_volumes
[[ $(< "$STATE/chat.mute") == 1 ]] || fail 'mute key did not mute Chat'
echo 0 > "$STATE/chat.mute"
link_volumes
[[ $(< "$STATE/game.mute") == 0 ]] || fail 'unmuting Chat did not unmute Game'

# The device-appearance grace period adopts restored volumes.
set_state 60 30
link_reset
link_volumes
key_press game 20
volume_is chat "$(pct 30)" 'volume restored after the dongle appeared'

# No change, no action.
set_state 60 30
start_link
: > "$STATE/log"
link_volumes
[[ ! -s $STATE/log ]] || fail 'unchanged volumes triggered an action'

# A reference of zero cannot be scaled; the change becomes the new reference.
[[ $(link_plan 0 100 0 100 50 100 0) == reference ]] || fail 'zero Game reference'
[[ $(link_plan 100 0 100 0 100 50 0) == reference ]] || fail 'zero Chat reference'

# notify() calls notify-send with the given title and body.
cat > "$TEST_TMP/notify-send" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$MOCK_STATE/notify.log"
EOF
chmod +x "$TEST_TMP/notify-send"
NOTIFY_SEND="$TEST_TMP/notify-send"

: > "$STATE/notify.log"
notify 'Title' 'Body text'
grep -q -- '--app-name=INZONE Buds --icon=audio-headset -- Title Body text' "$STATE/notify.log" \
  || fail 'notify did not call notify-send with the expected arguments'

# INZONE_NOTIFY=0 disables notifications.
NOTIFY=0
: > "$STATE/notify.log"
notify 'Title' 'Body text'
[[ ! -s $STATE/notify.log ]] || fail 'notify ran with NOTIFY=0'
NOTIFY=1

# A missing notify-send is silently ignored.
NOTIFY_SEND="$TEST_TMP/does-not-exist"
notify 'Title' 'Body text' || fail 'notify failed with a missing notify-send'

# The user config file sets a default, but an already-set environment
# variable still takes precedence over it.
CONFIG="$TEST_TMP/config"
# shellcheck disable=SC2016  # literal text for the config file, not this script
printf ': "${INZONE_LINK_VOLUMES:=0}"\n' > "$CONFIG"
value=$(INZONE_CONFIG_FILE="$CONFIG" PACTL="$TEST_TMP/pactl" \
  bash -c 'source "$1"; echo "$LINK_VOLUMES"' _ "$PROJECT_DIR/bin/inzone-autoswitch")
[[ $value == 0 ]] || fail "config file default did not apply: LINK_VOLUMES=$value"

value=$(INZONE_CONFIG_FILE="$CONFIG" INZONE_LINK_VOLUMES=1 PACTL="$TEST_TMP/pactl" \
  bash -c 'source "$1"; echo "$LINK_VOLUMES"' _ "$PROJECT_DIR/bin/inzone-autoswitch")
[[ $value == 1 ]] || fail "environment did not override the config file: LINK_VOLUMES=$value"

# A missing config file is not an error.
value=$(INZONE_CONFIG_FILE="$TEST_TMP/does-not-exist" PACTL="$TEST_TMP/pactl" \
  bash -c 'source "$1"; echo "$LINK_VOLUMES"' _ "$PROJECT_DIR/bin/inzone-autoswitch")
[[ $value == 1 ]] || fail "missing config file changed the hardcoded default: LINK_VOLUMES=$value"

printf 'Autoswitch volume-link tests passed.\n'
