#!/usr/bin/env bash
# Card D — correlated-update campaign (resumable). Each cell: edit -> re-solve ->
# measure global+region MAC + |df%| vs .ash. Skips cells whose result exists.
set -uo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=scripts
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p out/edits logs
python3 code/make_edit_specs.py
CELLS="baseline_reuse e01_calibrated_theta e02_joints_soft e03_joints_stiff \
e04_bottombox_soft e05_bottombox_stiff e06_topbox_stiff e07_topbox_soft \
e08_joint801_soft e09_strut807_soft e10_contact902_stiff"
for c in $CELLS; do
  if [ -f "out/edits/$c/result.json" ]; then echo "SKIP $c (done)"; continue; fi
  echo "== RUN $c =="
  python3 code/edit_solve.py "$c" || echo "FAILED $c"
done
echo "== CAMPAIGN DONE =="
