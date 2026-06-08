#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."

python3 runs/fem_phase1/codex/tensormesh/code/run_tensormesh.py
python3 runs/fem_phase1/codex/jax/code/run_jax.py
python3 runs/fem_phase1/codex/calculix/code/run_calculix.py
python3 runs/fem_phase1/codex/nastran_deck/code_generate_nastran.py
