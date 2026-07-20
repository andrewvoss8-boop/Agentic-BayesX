#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=scripts OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
# wait for any running campaign/combo solves to free the CPU
while pgrep -f run_combos.sh >/dev/null; do sleep 20; done
for cell in "801 0.3" "801 2.0" "807 0.3"; do
  set -- $cell; pid=$1; sc=$2; eid="loc_${pid}_${sc}"
  [ -f "out/local/$eid/result.json" ] && { echo "SKIP $eid"; continue; }
  echo "== RUN $eid =="; python3 code/local_interface.py "$pid" "$sc" || echo "FAILED $eid"
done
echo "== LOCAL DONE =="
