#!/usr/bin/env bash
# Targeted re-run of the two RED-gate fixes: discretization (k=90 full solve) + figD overlap, then QA + check.
set -uo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
PY="$(cd ../../../.venv_nuts/bin && pwd)/python"
LINT="$(cd ../../.. && pwd)/.claude/skills/tufte-data-graphics/scripts/tufte_lint.py"
rm -f out/full_modes_combo3.npz
( cd code && "$PY" discretization.py ) > logs/discretization.log 2>&1
( cd code && "$PY" fig_heldout_frf.py ) > logs/fig_heldout_frf.log 2>&1
"$PY" "$LINT" code/fig_heldout_frf.py > logs/tufte_fig_heldout_frf.txt 2>&1 || true
( cd code && "$PY" image_qa.py ) > logs/image_qa.log 2>&1
"$PY" code/aggregate.py > logs/aggregate.log 2>&1
set -o pipefail
"$PY" check.py | tee logs/check.txt
echo "FIXDONE rc=$?" > logs/fix.done
