#!/usr/bin/env bash
# Tonight's chained pipeline (detached; resumable at every step).
# Order: wait for modes -> nominal QOI sweeps -> figures -> CI MC -> variants.
set -uo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

wait_for () {  # wait_for <file> <max_minutes>
  local f="$1"; local mm="$2"; local n=0
  until [ -f "$f" ]; do
    sleep 60; n=$((n+1))
    if [ "$n" -ge "$mm" ]; then echo "TIMEOUT waiting for $f"; return 1; fi
  done
}

echo "[pipeline] waiting for bcA modes meta..."
wait_for out/modes_bcA_meta.json 120 || exit 1
[ -f out/qoi_bcA_summary.json ] || python3 scripts/forcing_qoi.py bcA \
  > logs/qoi_bcA.log 2>&1 || { echo "qoi bcA FAILED"; exit 1; }
echo "[pipeline] qoi bcA done"

echo "[pipeline] waiting for bcB modes meta..."
wait_for out/modes_bcB_meta.json 180 || exit 1
[ -f out/qoi_bcB_summary.json ] || python3 scripts/forcing_qoi.py bcB \
  > logs/qoi_bcB.log 2>&1 || { echo "qoi bcB FAILED"; exit 1; }
echo "[pipeline] qoi bcB done"

python3 scripts/make_figures.py > logs/figures.log 2>&1 \
  && echo "[pipeline] figures done" || echo "[pipeline] figures FAILED (non-fatal)"

[ -f out/ci_bcA_summary.json ] || python3 scripts/ci_mc.py bcA \
  > logs/ci_bcA.log 2>&1 && echo "[pipeline] ci bcA done"
[ -f out/ci_bcB_summary.json ] || python3 scripts/ci_mc.py bcB \
  > logs/ci_bcB.log 2>&1 && echo "[pipeline] ci bcB done"

python3 scripts/resolve_variants.py > logs/variants.log 2>&1 \
  && echo "[pipeline] variants done" || echo "[pipeline] variants INCOMPLETE"

echo "[pipeline] ALL DONE"
