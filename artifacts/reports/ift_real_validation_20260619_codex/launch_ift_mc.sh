#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
PY="${PYTHON:-../../../.venv_nuts/bin/python}"
if [ ! -x "$PY" ]; then
  PY="python3"
fi
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export JAX_ENABLE_X64=1
nohup "$PY" code/ift_arm.py --n-splits 25 --warmup 200 --samples 200 --chains 4 --pred-draws 160 --tag headline > logs/ift_mc_headline.log 2>&1 &
pid=$!
disown "$pid" || true
echo "$pid" > logs/ift_mc_headline.pid
echo "launched IFT MC pid=$pid log=logs/ift_mc_headline.log"
