#!/usr/bin/env bash
# Card D — assemble + solve the dish-2x-refined model, measure MAC vs baseline.
set -euo pipefail
cd "$(dirname "$0")/out/dish_refined"
export PYTHONPATH="$(cd ../../scripts && pwd)"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p matrices
echo "== assemble refined =="
python3 "$PYTHONPATH/assemble_fem.py"
echo "== solve refined =="
python3 "$PYTHONPATH/solve_nominal.py"
echo "== DISH REFINED DONE =="
