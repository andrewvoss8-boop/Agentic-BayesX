#!/usr/bin/env bash
# One-command offline replay of this workspace (no NASA access needed).
#   bash run_all.sh            replay everything, then run the checker
#   NETWORK=1 bash run_all.sh  also run the live ranged-download test against PyPI and the NASA gate
# Needs python3 with numpy, scipy, matplotlib, pillow, requests, openpyxl (PYTHON=... to choose).
# Writes runtime.json (active = sum of command times, elapsed = wall clock).
set -uo pipefail
WS=$(cd "$(dirname "$0")" && pwd); cd "$WS"
PY=${PYTHON:-python3}
T0=$(date +%s.%N); ACTIVE=0; FAIL=0; FAILED=""
step() {  # step NAME CMD...
  local n=$1; shift; local s=$(date +%s.%N)
  "$@" > "logs/replay_$n.log" 2>&1; local rc=$?
  local e=$(date +%s.%N); ACTIVE=$(echo "$ACTIVE + $e - $s" | bc)
  printf '%-28s exit %s  %6.1f s\n' "$n" "$rc" "$(echo "$e - $s" | bc)"
  [ $rc -ne 0 ] && FAIL=$((FAIL+1)) && FAILED="$FAILED\"$n\","
  return 0
}
mkdir -p logs
if [ "${NETWORK:-0}" = 1 ]; then step zip_tools_test "$PY" code/test_zip_tools.py --network; else step zip_tools_test "$PY" code/test_zip_tools.py; fi
step build_listings        "$PY" code/build_listings.py
step deck_evidence         "$PY" code/deck_evidence.py
step reference_numbers     "$PY" code/project_reference_numbers.py
step digitizer_test        "$PY" code/test_digitize.py
step pilot                 "$PY" code/frf_wall_pilot.py
step freeze_verify         "$PY" code/freeze_predictions.py --verify
step adf_probe_test        "$PY" code/test_adf_probe.py
step tier4_dry_run         "$PY" code/tier4_study.py --dry-run
step rehearsal             env OMP_NUM_THREADS=1 "$PY" code/rehearsal_burst.py
step figures               "$PY" code/make_figures.py
step tufte_lint            sh -c "$PY ../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py code/make_figures.py > qa/tufte_lint.txt"
[ "${NETWORK:-0}" = 1 ] && step nasa_gate bash gated_run.sh
T1=$(date +%s.%N)
printf '{"active_runtime_s": %.1f, "elapsed_wallclock_s": %.1f, "note": "offline replay; excludes human wait and the network-gated fetch", "failed_steps": %d, "failed_step_names": [%s]}\n' \
  "$ACTIVE" "$(echo "$T1 - $T0" | bc)" "$FAIL" "${FAILED%,}" > runtime.json
cat runtime.json
"$PY" check.py
