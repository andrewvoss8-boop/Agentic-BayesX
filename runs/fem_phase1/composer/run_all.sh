#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."

python3 runs/fem_phase1/composer/tensormesh/code/run_tensormesh.py
python3 runs/fem_phase1/composer/jax/code/run_jax.py
python3 runs/fem_phase1/composer/calculix/code/run_calculix.py
python3 runs/fem_phase1/composer/nastran_deck/code_generate_nastran.py
