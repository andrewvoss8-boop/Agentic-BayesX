#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=scripts OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
for c in e11_combo_caltheta_topbox092 e12_combo_caltheta_joints07 e13_combo_caltheta_topbox095_joints07; do
  [ -f "out/edits/$c/result.json" ] && { echo "SKIP $c"; continue; }
  echo "== RUN $c =="; python3 code/edit_solve.py "$c" || echo "FAILED $c"
done
echo "== COMBOS DONE =="
