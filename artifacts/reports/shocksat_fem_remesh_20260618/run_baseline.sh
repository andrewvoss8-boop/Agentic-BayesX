#!/usr/bin/env bash
# Card D — reproduce the BEFORE baseline in the copied workspace.
# assemble per-PID K blocks + M + T, then nominal eigensolve + MAC vs .ash.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=scripts
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p matrices logs out
echo "== assemble (per-PID K blocks + M + RBE2 T) =="
python3 scripts/assemble_fem.py
echo "== nominal eigensolve + obs_V + MAC vs .ash =="
python3 scripts/solve_nominal.py
echo "== BASELINE DONE =="
