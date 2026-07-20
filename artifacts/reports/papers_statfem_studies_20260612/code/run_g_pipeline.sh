#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export XLA_FLAGS="--xla_force_host_platform_device_count=4"
PY=../../../../.venv_nuts/bin/python
echo "[G-headline]"; $PY run_ums2.py
echo "[G-frames]";   $PY run_ums2_frames.py
echo "G-PIPELINE-DONE"
