#!/usr/bin/env bash
# Regenerate artifacts, run checkers, and build plots.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=.
export MPLCONFIGDIR="$ROOT/artifacts/.matplotlib"
mkdir -p "$MPLCONFIGDIR"

echo "== Canary harness =="
python3 harness/driver.py --config harness/configs/canary_trial.json

echo "== Synthetic data =="
python3 src/twodof/synthetic_data.py

echo "== MCMC =="
python3 src/inference/mcmc.py

echo "== Smoke tests =="
python3 tests/test_posterior_recovery.py
python3 tests/test_mdof_transfer.py

echo "== Canonical synthetic data and MCMC =="
python3 src/twodof/synthetic_data.py
python3 src/inference/mcmc.py

echo "== Artifact checks =="
python3 tests/test_channel_definitions.py
python3 tests/test_tied_coupling_and_errors.py

echo "== Plots =="
python3 scripts/visualize_results.py
python3 tests/test_key_transfer_functions.py

echo "== Sensitivity =="
python3 scripts/run_sensitivity_study.py
python3 tests/test_sensitivity_artifact.py

echo "== Review packet =="
python3 scripts/generate_review_packet.py
python3 tests/test_review_packet.py

echo "Done. See artifacts/plots/ and artifacts/reports/"
