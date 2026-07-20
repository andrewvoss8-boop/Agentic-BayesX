#!/usr/bin/env bash
# One-command replay for Card B (PIFT collapse / orthogonal-Schneider cure). Resumable: each stage skips
# finished work (per-cell JSONs, existing figures). Pin BLAS threads + float64 for the dense eigh/posterior math.
set -uo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 JAX_ENABLE_X64=1
PY=../../../.venv_nuts/bin/python
PY3=python3                      # python-pptx / fitz live in base python3
LINT=../../../scripts/tufte_lint.py
mkdir -p out logs figures slides
t0=$(date +%s)

echo "== [1/11] identifiability (strain energy + FIM) =="
[ -f out/identifiability.json ] || $PY code/identifiability.py 2>&1 | tee logs/identifiability.log

echo "== [2/11] discretization (reduced-vs-full inherited + internal refine) =="
[ -f out/discretization.json ] || $PY code/discretization.py 2>&1 | tee logs/discretization.log

echo "== [3/11] synthetic collapse N-ladder (resumable; NUTS) =="
$PY code/run_ladder.py --leg synth --nfreq 20,40,80,160,320 --nsensor 3,6,12,18 --arms M0,M1,M3 2>&1 | tee -a logs/ladder_synth.log

echo "== [4/11] real matched-path FRF build (P3) =="
[ -f out/config_real.json ] || $PY code/build_real_frf.py 2>&1 | tee logs/build_real_frf.log

echo "== [5/11] real collapse N-ladder (resumable; NUTS) =="
$PY code/run_ladder.py --leg real --nfreq 20,40,80,160,320 --nsensor 3,6,12,18 --arms M0,M1,M3 2>&1 | tee -a logs/ladder_real.log

echo "== [6/11] effective-sample-size accounting =="
$PY code/ess_accounting.py 2>&1 | tee logs/ess.log

echo "== [7/11] aggregate sweeps + verdict =="
$PY code/aggregate_sweep.py 2>&1 | tee logs/aggregate.log

echo "== [8/11] figures + tufte lint =="
for s in fig_collapse_curves fig_ess_vs_N fig_theta_width fig_synth_collapse_demo fig_schematic; do
  $PY code/$s.py 2>&1 | tee logs/$s.log
  $PY3 $LINT code/$s.py 2>&1 | tee logs/tufte_$s.txt
done

echo "== [9/11] image QA + text-overlap =="
$PY code/image_qa.py 2>&1 | tee logs/image_qa.log

echo "== [10/11] deck (.pptx, gated non-RED) =="
[ -f code/make_pptx.py ] && $PY3 code/make_pptx.py 2>&1 | tee logs/make_pptx.log || echo "make_pptx skipped"

echo "== [11/11] runtime + checker =="
t1=$(date +%s)
$PY3 - "$t0" "$t1" <<'PY'
import json,sys,glob
t0,t1=int(sys.argv[1]),int(sys.argv[2])
# active runtime = sum of per-cell NUTS runtimes + a wall estimate for the rest
import os
cell_t=0.0
for p in glob.glob("out/cell_*.json"):
    try: cell_t+=json.load(open(p)).get("runtime_s",0.0)
    except Exception: pass
rt={"active_runtime_s":round(cell_t,1),"elapsed_wallclock_s":round(t1-t0,1),
    "phases":{"P1_P2_synth_ladder":"see logs/ladder_synth.log","P3_real_ladder":"see logs/ladder_real.log",
              "P4_ess_aggregate_figs_deck":"see logs/*.log"},
    "note":"active_runtime_s = Σ per-cell NUTS runtime_s (resumable cells); elapsed = this run_all wallclock."}
json.dump(rt,open("runtime.json","w"),indent=1)
print("runtime.json:",rt["active_runtime_s"],"active /",rt["elapsed_wallclock_s"],"wall")
PY
$PY3 check.py
