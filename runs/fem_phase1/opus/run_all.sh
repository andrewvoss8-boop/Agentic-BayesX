#!/usr/bin/env bash
# One-command replay of all four Opus Phase-1 hexapod builds.
# Env was set up during the build:
#   .venv : python3 -m venv .venv && pip install numpy==1.26.4 scipy==1.10.1 \
#           jax==0.4.30 jaxlib==0.4.30 matplotlib discretize==0.10.0
#   ccx   : conda create -p <env> -c conda-forge calculix   (CalculiX 2.23)
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
PY="$ROOT/.venv/bin/python"
export JAX_PLATFORM_NAME=cpu JAX_ENABLE_X64=1
export CCX="${CCX:-$HOME/miniforge3_bayesx_femphase1/envs/ccx/bin/ccx}"

echo "== spec self-check =="
"$PY" shared/spec.py

echo "== JAX (element verification + build) =="
( cd jax/code && "$PY" fe_validate.py && "$PY" build_jax.py )

echo "== TensorMesh =="
( cd tensormesh/code && "$PY" build_tensormesh.py )

echo "== CalculiX (build deck + ccx + parse + convergence) =="
( cd calculix/code && "$PY" run_ccx.py )

echo "== Nastran deck (generate + render; human solves) =="
( cd nastran_deck/code && "$PY" make_bdf.py && "$PY" render_and_results.py )

echo "== done: see */results.json, */figures, COMPARISON_opus_cross_software.md =="
