#!/usr/bin/env bash
# One-command replay - Confidently-Wrong Model-Form-Error experiment.
# Resumable: run_sweep.py skips finished (class,delta,arm) cells. Float64; BLAS threads pinned.
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
WALL0=$(date +%s)

PY="../../../.venv_nuts/bin/python"
[ -x "$PY" ] || PY="python3"
LINT="../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py"
mkdir -p logs out figures
ACTIVE=0
stage () {  # stage "name" cmd...
  local name="$1"; shift
  local t0; t0=$(date +%s)
  echo "== $name =="
  "$@"
  local t1; t1=$(date +%s)
  ACTIVE=$((ACTIVE + t1 - t0))
}

# 1. the delta x arms NUTS sweep (resumable) + E-LIMIT
stage sweep      bash -c "cd code && '$PWD/$PY' run_sweep.py --only all > '$PWD/logs/run_sweep.log' 2>&1"
stage e_limit    bash -c "cd code && '$PWD/$PY' exp_limit.py > '$PWD/logs/exp_limit.log' 2>&1"
stage aggregate  bash -c "cd code && '$PWD/$PY' aggregate.py > '$PWD/logs/aggregate.log' 2>&1"

# 2. figures (each its own saved script + tufte lint)
for s in fig_testbed fig_coverage fig_sigmad fig_alpha fig_limit fig_identifiability; do
  stage "$s" bash -c "cd code && '$PWD/$PY' ${s}.py > '$PWD/logs/${s}.log' 2>&1"
  "$PY" "$LINT" "code/${s}.py" > "logs/tufte_${s}.txt" 2>&1 || true
done
stage gif        bash -c "cd code && '$PWD/$PY' gif_frf.py > '$PWD/logs/gif_frf.log' 2>&1"
"$PY" "$LINT" "code/gif_frf.py" > "logs/tufte_gif_frf.txt" 2>&1 || true

# 3. image gates
stage image_qa   bash -c "cd code && '$PWD/$PY' image_qa.py > '$PWD/logs/image_qa.log' 2>&1"

# 4. runtime accounting + checker
WALL1=$(date +%s)
"$PY" - "$ACTIVE" "$((WALL1 - WALL0))" <<'PY'
import json, sys, glob
cmd_active = int(sys.argv[1]); wall = int(sys.argv[2])
# also report the pure NUTS active time (sum of stored per-cell runtimes + E-LIMIT)
nuts = 0.0
for p in glob.glob("out/cell_*.json"):
    nuts += json.load(open(p)).get("runtime_s", 0.0)
try:
    nuts += json.load(open("out/limit_summary.json")).get("runtime_s", 0.0)
except Exception:
    pass
json.dump({"active_runtime_s": cmd_active, "elapsed_wallclock_s": wall,
           "nuts_only_active_s": round(nuts, 1),
           "note": "active_runtime_s = sum of run_all stage durations; nuts_only_active_s = sum of "
                   "stored per-cell + E-LIMIT NUTS runtimes (resumable replay skips finished cells)."},
          open("runtime.json", "w"), indent=1)
print("runtime.json written")
PY

stage check      bash -c "'$PWD/$PY' check.py | tee '$PWD/logs/check.txt'"
echo "run_all complete; see packet.md, checker_report.json, runtime.json"
