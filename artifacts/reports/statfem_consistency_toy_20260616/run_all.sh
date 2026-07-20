#!/usr/bin/env bash
# One-command replay - StatFEM consistency toy (Experiment A).
# Resumable: run_sweep.py skips finished cells. Chunked so jax compilation memory is freed between
# groups (decisions_log D16). Float64; BLAS threads pinned.
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

# 1. solver validation FIRST (gate), then identifiability
stage solver_validation  bash -c "'$PWD/$PY' code/solver_validation.py > '$PWD/logs/solver_validation.log' 2>&1"
stage identifiability    bash -c "'$PWD/$PY' code/identifiability.py   > '$PWD/logs/identifiability.log' 2>&1"

# 2. the consistency sweep (chunked, resumable) -- one fresh process per chunk
for ch in mlik_sr mlik_nc mift_nc statfem_h concentration; do
  stage "sweep_$ch" bash -c "'$PWD/$PY' code/run_sweep.py --only $ch >> '$PWD/logs/sweep.log' 2>&1"
done

# 3. aggregate -> sweep_summary.json (+ verdicts from the numbers)
stage aggregate   bash -c "'$PWD/$PY' code/aggregate.py > '$PWD/logs/aggregate.log' 2>&1"

# 4. figures (each its own saved script + tufte lint)
for s in fig_solver fig_schematic fig_money fig_concentration fig_coverage fig_identifiability; do
  stage "$s" bash -c "cd code && '$PWD/$PY' ${s}.py > '$PWD/logs/${s}.log' 2>&1"
  "$PY" "$LINT" "code/${s}.py" > "logs/tufte_${s}.txt" 2>&1 || true
done

# 5. image-legibility QA (pixel) ; the text-overlap auditor already ran at figure save-time
stage image_qa  bash -c "'$PWD/$PY' code/image_qa.py > '$PWD/logs/image_qa.log' 2>&1"

# 6. runtime accounting
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
                   "per-cell NUTS runtimes (resumable replay skips finished cells)."},
          open("runtime.json", "w"), indent=1)
print("runtime.json written")
PY

# 7. immutable checker (exits non-zero only on RED)
stage check  bash -c "'$PWD/$PY' check.py | tee '$PWD/logs/check.txt'"
echo "run_all complete; see packet.md, checker_report.json, runtime.json"
