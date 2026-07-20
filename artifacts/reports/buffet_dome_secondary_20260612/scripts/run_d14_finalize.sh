#!/usr/bin/env bash
# D14 finalize (detached; resumable). Assumes solve_d14 (bcA,bcB) is running or
# done. Order: wait modes -> QOI both -> v1/d14 compare -> figures -> image QA
# -> meshf variant (D14, Discretization gate) -> done. Mode files are large;
# we delete the meshf mode file after its QOI to bound disk.
set -uo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

wait_for () { local f="$1"; local mm="$2"; local n=0
  until [ -f "$f" ]; do sleep 60; n=$((n+1))
    if [ "$n" -ge "$mm" ]; then echo "TIMEOUT $f"; return 1; fi; done; }

echo "[d14] wait bcA modes"; wait_for out/modes_bcA_meta.json 120 || exit 1
[ -f out/qoi_bcA_summary.json ] || python3 scripts/forcing_qoi.py bcA \
  > logs/qoi_bcA_d14.log 2>&1; echo "[d14] qoi bcA ready"
echo "[d14] wait bcB modes"; wait_for out/modes_bcB_meta.json 180 || exit 1
[ -f out/qoi_bcB_summary.json ] || python3 scripts/forcing_qoi.py bcB \
  > logs/qoi_bcB_d14.log 2>&1; echo "[d14] qoi bcB ready"

python3 scripts/compare_v1_d14.py > logs/compare.log 2>&1 && echo "[d14] compare done"

# D14 changes the COPV channels (rotational mount is a real load path), so the
# COPV CI bands must be recomputed on the D14 basis for consistency.
rm -f out/ci_bcA.npz out/ci_bcA_summary.json out/ci_bcB.npz out/ci_bcB_summary.json
python3 scripts/ci_mc.py bcA > logs/ci_bcA_d14.log 2>&1 && echo "[d14] ci bcA done"
python3 scripts/ci_mc.py bcB > logs/ci_bcB_d14.log 2>&1 && echo "[d14] ci bcB done"

python3 scripts/make_figures.py > logs/figures.log 2>&1 && echo "[d14] figures done"
python3 scripts/image_qa.py > logs/image_qa.log 2>&1 && echo "[d14] image QA done"

# meshf discretization-convergence variant under D14
if [ ! -f out/qoi_bcA_meshf_summary.json ]; then
  echo "[d14] meshf variant build+solve+qoi"
  BUFFET_TAG=meshf BUFFET_PAR_OVERRIDES='{"Nth":300,"Nz":20,"Nu":30}' \
    python3 scripts/build_model.py > logs/build_meshf.log 2>&1
  BUFFET_TAG=meshf python3 scripts/solve_modes.py bcA_meshf \
    > logs/solve_meshf.log 2>&1
  BUFFET_TAG=meshf python3 scripts/forcing_qoi.py bcA_meshf \
    > logs/qoi_meshf.log 2>&1
  rm -f out/modes_bcA_meshf.npz   # reclaim ~0.5 GB; QOI summary kept
  echo "[d14] meshf done"
fi

python3 check.py > /dev/null 2>&1 && echo "[d14] checker refreshed"
echo "[d14] ALL DONE"
