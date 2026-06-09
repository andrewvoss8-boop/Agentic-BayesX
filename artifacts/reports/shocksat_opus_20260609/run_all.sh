#!/usr/bin/env bash
# One-command replay for the Opus ShockSat corrected-FRF run.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="$REPO/.venv_nuts/bin/python"
[ -x "$PY" ] || PY="python3"
"$PY" "$HERE/scripts/opus_hammer_frf.py"
"$PY" "$HERE/scripts/opus_point_reconcile.py"
"$PY" "$HERE/scripts/opus_statfem_v1_heldout.py"
"$PY" "$HERE/scripts/check_opus.py"
