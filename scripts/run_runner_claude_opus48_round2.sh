#!/usr/bin/env bash
# One-command replay for the round-2 runner (Claude Opus 4.8).
# Builds the NUTS venv if needed, runs the hierarchical NUTS pipeline, then the
# runner-local artifact checker. Does NOT touch immutable checker files.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
VENV="$ROOT/.venv_nuts"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[setup] creating venv (system Python 3.9.6 lacks numpyro/jax)"
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip
  "$VENV/bin/python" -m pip install --quiet \
    "numpyro==0.15.3" "jax==0.4.30" "jaxlib==0.4.30" "numpy<2" \
    "arviz==0.17.1" "scipy==1.10.1" matplotlib imageio pillow
fi

echo "[checker] immutable checker integrity (pre-run)"
shasum -a 256 -c harness/checkers/manifest.sha256

echo "[run] hierarchical NUTS pipeline"
PYTHONUNBUFFERED=1 "$VENV/bin/python" scripts/runner_claude_opus48_round2.py

echo "[run] write runtime.json"
"$VENV/bin/python" scripts/write_runtime_round2.py

echo "[checker] runner-local artifact acceptance"
"$VENV/bin/python" scripts/check_round2_artifacts.py

echo "[checker] immutable checker integrity (post-run)"
shasum -a 256 -c harness/checkers/manifest.sha256
echo "[done]"
