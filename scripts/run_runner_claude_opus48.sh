#!/usr/bin/env bash
# One-command replay for the Claude Opus 4.8 full sequential vibe/modal/flight runner.
#
# Creates an isolated venv (numpyro/jax not available in system Python 3.9.6),
# runs NUTS/HMC inference, then runs the runner checker.
#
# Usage:  bash scripts/run_runner_claude_opus48.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv_nuts"
if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv at $VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --disable-pip-version-check numpyro matplotlib
fi

echo "[run] versions:"
"$VENV/bin/python" -c "import numpyro, jax, numpy, matplotlib; \
print('numpyro', numpyro.__version__, '| jax', jax.__version__, \
'| numpy', numpy.__version__, '| matplotlib', matplotlib.__version__)"

echo "[run] NUTS inference (full + peak likelihoods, 4 chains)"
"$VENV/bin/python" scripts/runner_claude_opus48_full_experiment.py

echo "[check] runner artifact checker"
"$VENV/bin/python" tests/test_runner_claude_opus48_full_experiment.py

echo "[check] immutable checker hashes"
shasum -a 256 -c harness/checkers/manifest.sha256

echo "[done] outputs in artifacts/reports/runner_claude_opus48_20260602/"
