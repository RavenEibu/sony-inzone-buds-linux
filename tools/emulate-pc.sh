#!/usr/bin/env bash
# Approximate older PCs and time the commands that matter.
# Usage: tools/emulate-pc.sh [RUNS]
#
# Memory is emulated for real: systemd-run caps the application's memory
# (MemoryMax, no swap) and the command is killed if it needs more.
# CPU speed is ESTIMATED, not enforced: CPU quotas are not reliable on every
# kernel (CachyOS's accepted cpu.max without throttling), so each command is run
# at full speed, its wall time and CPU time are measured inside the cgroup, and
# the time on a slower CPU is projected as
#     wait + cpu * 100 / speed
# where `wait` = wall - cpu (time not spent computing) and speed is a rough
# single-thread performance relative to this machine. It does not reproduce
# caches, disk, GPU or a real CPU's behavior, and it runs on today's kernel and
# libraries. See docs/compatibility.md for how to read the numbers.
#
# Needs systemd --user (systemd-run) and cgroup v2; the mixer rows need a
# display. Read-only: it runs `inzonectl status`/`doctor` and starts the mixer
# window with a throw-away config directory; it never changes volumes.
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
RUNS=${1:-3}

# name | rough single-thread speed vs. a current desktop CPU (percent) | RAM the
# application may use (a desktop of that year leaves roughly this much free)
PROFILES=(
  "2006|8|256M"
  "2011|25|512M"
  "2016|40|1G"
  "2021|65|2G"
  "today|100|infinity"
)

median() { sort -n | awk '{a[NR]=$1} END {print a[int((NR+1)/2)]}'; }

ROOT=$PWD

# Runs a command inside a memory-capped cgroup and prints "WALL_MS CPU_MS".
# Fails (printing nothing) if the command fails, e.g. killed at its memory cap.
run_capped() {  # MEMORY COMMAND...
  local memory=$1
  shift
  # shellcheck disable=SC2016  # the inner script runs in the cgroup, not here
  systemd-run --user --pipe --wait --collect --quiet \
    -p "MemoryMax=$memory" -p MemorySwapMax=0 -p "WorkingDirectory=$ROOT" \
    --setenv=DISPLAY="${DISPLAY:-}" --setenv=WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
    --setenv=XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-}" --setenv=PATH="$PATH" \
    --setenv=DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-}" \
    -- bash -c '
      cg=/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)
      cpu() { awk "/^usage_usec/ {print \$2}" "$cg/cpu.stat"; }
      u0=$(cpu); a=$(date +%s%N)
      "$@" >/dev/null 2>&1; rc=$?
      b=$(date +%s%N); u1=$(cpu)
      (( rc == 0 )) && echo "$(( (b - a) / 1000000 )) $(( (u1 - u0) / 1000 ))"
      exit $rc' _ "$@"
}

# Median "WALL CPU" over RUNS runs (median of each column).
measure() {  # MEMORY COMMAND...
  local i line walls=() cpus=()
  for (( i = 0; i < RUNS; i++ )); do
    line=$(run_capped "$@") || { echo "KILLED"; return 0; }
    walls+=("${line% *}")
    cpus+=("${line#* }")
  done
  echo "$(printf '%s\n' "${walls[@]}" | median) $(printf '%s\n' "${cpus[@]}" | median)"
}

# Projected wall time in ms on a CPU running at SPEED percent of this one.
project() {  # "WALL CPU" SPEED
  local wall=${1% *} cpu=${1#* } speed=$2
  echo $(( (wall > cpu ? wall - cpu : 0) + cpu * 100 / speed ))
}

printf '| Profile | CPU speed | App memory cap | status (ms) | doctor (ms) | Mixer cold start (ms) |\n'
printf '| --- | --- | --- | --- | --- | --- |\n'
for profile in "${PROFILES[@]}"; do
  IFS='|' read -r name speed memory <<< "$profile"
  cells=()
  for entry in "status|$ROOT/bin/inzonectl status" "doctor|$ROOT/bin/inzonectl doctor" \
               "start|python3 $ROOT/tools/measure-startup.py"; do
    key=${entry%%|*}
    command=${entry#*|}
    if [[ $key == start && -z ${DISPLAY:-}${WAYLAND_DISPLAY:-} ]]; then
      cells+=("n/a")
      continue
    fi
    # shellcheck disable=SC2086  # the command string is split on purpose
    result=$(measure "$memory" $command)
    if [[ $result == KILLED ]]; then
      cells+=("killed at cap")
    else
      cells+=("$(project "$result" "$speed") (cpu ${result#* })")
    fi
  done
  printf '| %s | %s%% | %s | %s | %s | %s |\n' "$name" "$speed" "$memory" "${cells[@]}"
done

# Smallest memory cap at which the mixer still starts at full speed.
printf '\nSmallest MemoryMax at which the mixer window still starts: '
for cap in 32M 48M 64M 80M 96M 128M 192M 256M; do
  if run_capped "$cap" python3 "$ROOT/tools/measure-startup.py" >/dev/null 2>&1; then
    printf '%s\n' "$cap"
    exit 0
  fi
done
printf 'more than 256M\n'
