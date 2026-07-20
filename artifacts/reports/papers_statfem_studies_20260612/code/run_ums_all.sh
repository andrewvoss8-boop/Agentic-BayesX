#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export XLA_FLAGS="--xla_force_host_platform_device_count=4"
PY=../../../../.venv_nuts/bin/python
echo "[G1] headline (unified 4x800+800, iid 4x600+600)"; $PY run_ums.py
echo "[G2] frames (10 reduced runs, resumable)";          $PY run_ums_frames.py
echo "UMS pipeline done"
