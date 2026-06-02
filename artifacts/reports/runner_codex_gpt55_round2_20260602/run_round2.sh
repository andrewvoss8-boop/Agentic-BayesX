#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv_nuts"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi

"$VENV/bin/python" - <<'PY' || "$VENV/bin/pip" install --quiet --disable-pip-version-check numpyro matplotlib pillow 'arviz<0.19' 'scipy<1.13'
import numpyro, jax, matplotlib, PIL, scipy, arviz
PY

"$VENV/bin/python" - <<'PY'
import numpyro, jax, numpy, scipy, arviz, matplotlib, PIL
print("numpyro", numpyro.__version__)
print("jax", jax.__version__)
print("numpy", numpy.__version__)
print("scipy", scipy.__version__)
print("arviz", arviz.__version__)
print("matplotlib", matplotlib.__version__)
print("pillow", PIL.__version__)
PY

"$VENV/bin/python" artifacts/reports/runner_codex_gpt55_round2_20260602/run_round2.py
shasum -a 256 -c harness/checkers/manifest.sha256
