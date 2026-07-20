#!/usr/bin/env bash
# One-command replay -- StatFEM ShockSat held-out-QOI evaluation (Experiment B).
# Resumable: run_sweep.py / sensitivity.py skip finished cells; discretization caches the full eigensolve.
# Float64; BLAS threads pinned (small dense eigh/posterior math). Launch detached for the long sweep.
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
WALL0=$(date +%s)

PY="../../../.venv_nuts/bin/python"
[ -x "$PY" ] || PY="python3"
LINT="../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py"
mkdir -p logs out figures slides
ACTIVE=0
stage () { local name="$1"; shift; local t0; t0=$(date +%s); echo "== $name =="; "$@"; local t1; t1=$(date +%s); ACTIVE=$((ACTIVE + t1 - t0)); }

# 1. main NUTS sweep (5 combos x 4 arms) + sensitivity arms (resumable)
stage sweep        bash -c "cd code && '$PWD/$PY' run_sweep.py --combos 1,2,3,4,5 --arms M0,M1,M2,M3 > '$PWD/logs/run_sweep.log' 2>&1"
stage sensitivity  bash -c "cd code && '$PWD/$PY' sensitivity.py > '$PWD/logs/sensitivity.log' 2>&1"

# 2. identifiability gate + discretization-resolution gate (the full eigensolve is cached)
stage identifiability bash -c "cd code && '$PWD/$PY' identifiability.py > '$PWD/logs/identifiability.log' 2>&1"
stage discretization  bash -c "cd code && '$PWD/$PY' discretization.py > '$PWD/logs/discretization.log' 2>&1"

# 3. aggregate cells -> money result + arm comparison + scorecard
stage aggregate    bash -c "cd code && '$PWD/$PY' aggregate.py > '$PWD/logs/aggregate.log' 2>&1"

# 4. figures (each its own saved script + tufte lint)
for s in fig_schematic fig_coverage fig_arm_comparison fig_theta_recovery fig_heldout_frf fig_identifiability fig_spatial; do
  stage "$s" bash -c "cd code && '$PWD/$PY' ${s}.py > '$PWD/logs/${s}.log' 2>&1"
  "$PY" "$LINT" "code/${s}.py" > "logs/tufte_${s}.txt" 2>&1 || true
done

# 5. image legibility QA
stage image_qa     bash -c "cd code && '$PWD/$PY' image_qa.py > '$PWD/logs/image_qa.log' 2>&1"

# 6. deck: PNG slides (.venv_nuts) + an editable .pptx (base python3 has python-pptx; skip gracefully if absent)
stage deck         bash -c "cd code && '$PWD/$PY' make_deck.py > '$PWD/logs/make_deck.log' 2>&1"
stage pptx         bash -c "cd '$PWD' && (python3 code/make_pptx.py > logs/make_pptx.log 2>&1 || echo 'python-pptx unavailable; .pptx skipped (PNG slides still produced)' > logs/make_pptx.log)"

# 7. runtime accounting + checker
WALL1=$(date +%s)
"$PY" - "$ACTIVE" "$((WALL1 - WALL0))" <<'PY'
import json, sys, glob
cmd_active = int(sys.argv[1]); wall = int(sys.argv[2])
nuts = 0.0
for p in glob.glob("out/cell_*.json"):
    nuts += json.load(open(p)).get("runtime_s", 0.0)
json.dump({"active_runtime_s": cmd_active, "elapsed_wallclock_s": wall,
           "nuts_only_active_s": round(nuts, 1),
           "note": "active_runtime_s = sum of run_all stage durations; nuts_only_active_s = sum of stored "
                   "per-cell NUTS+predict runtimes (resumable replay skips finished cells)."},
          open("runtime.json", "w"), indent=1)
print("runtime.json written")
PY

stage check        bash -c "set -o pipefail; '$PWD/$PY' check.py | tee '$PWD/logs/check.txt'"
echo "run_all complete; see packet.md, checker_report.json, runtime.json"
