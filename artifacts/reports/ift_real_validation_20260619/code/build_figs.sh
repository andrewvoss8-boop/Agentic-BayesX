#!/usr/bin/env bash
# Render all 5 figures (each writes its own tufte+image-QA+overlap figures/<name>.qa.json) + pixel QA sweep.
cd "$(dirname "$0")/.."
PY=../../../.venv_nuts/bin/python
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
for f in figA_scorecard figB_beta figC_heldout_frf_overlay figD_discretization fig_convergence_table; do
  $PY figures/src/$f.py || echo "FIG FAIL: $f"
done
$PY code/image_qa.py || true
