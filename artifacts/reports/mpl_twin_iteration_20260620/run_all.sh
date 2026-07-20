#!/usr/bin/env bash
# One-command replay for the MPL twin-iteration harness (Phase 0). BLAS pinned (small dense eigh/posterior math).
# The NUTS calibration step uses the project NUTS venv. The whole-curve calibration is currently SMOKE/
# non-converged pending the D6 steer (the FEM transmissibility forward is uncorrelated with measured |T|).
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
ROOT="$(cd ../../.. && pwd)"
PY=python3
NUTS_PY="$ROOT/.venv_nuts/bin/python"

echo "[1/6] build gain-free transmissibility observable + unit tests"
$PY code/mpl_observe.py
echo "[2/6] 5 leave-one-location-out splits"
$PY code/mpl_splits.py
echo "[3/8] (M0) whole-curve transmissibility baseline vs climatology  [SMOKE=1 fast non-converged; uncorrelated forward, D6]"
SMOKE="${SMOKE:-1}" "$NUTS_PY" code/mpl_baseline.py
echo "[4/8] (b) FREQUENCY headline: matched-eigenfrequency NUTS calibration + held-out scoring (converges)"
"$NUTS_PY" code/mpl_freq_baseline.py
echo "[5/8] (a) near-resonance load-free mode-shape-ratio test"
"$NUTS_PY" code/near_resonance_test.py
echo "[6/8] figures (transmissibility diagnostic + frequency result + registry)"
$PY code/fig_forward_diagnostic.py
$PY code/fig_freq_registry.py
echo "[7/8] image-legibility QA"
$PY code/image_qa.py
echo "[8/8] checker"
$PY check.py
