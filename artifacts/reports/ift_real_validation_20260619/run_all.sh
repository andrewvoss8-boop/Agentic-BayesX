#!/usr/bin/env bash
# One-command, RESUMABLE replay for the IFT real-validation study.
# Long NUTS/TMCMC cells are cached (out/*_cells/) and skipped if present, so a re-run just re-aggregates +
# re-checks fast. A from-scratch run launches the heavy cells in the foreground (hours) -- for a fresh machine
# prefer the detached launches documented in decisions_log (NUTS/TMCMC exceed the agent tool timeout).
set -e
cd "$(dirname "$0")"
PY=../../../.venv_nuts/bin/python
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T0=$(date +%s)

echo "[1/7] IFT under NUTS (multimodality evidence; resumable)"
[ -f out/ift_cells/ift_seed00.json ] || $PY code/ift_arm.py --seed=0 --force

echo "[2/7] IFT-TMCMC subset (the escalation; resumable cells)"
for s in 0 1 2 3 4; do $PY code/ift_tmcmc.py --seed=$s --n=1500 --runs=4; done

echo "[3/7] L5 25-split bar (resumable cells)"
$PY -c "import sys;sys.path.insert(0,'code');import run_sweep;[run_sweep.l5_split(s,600,600,4,300,False) for s in range(25)]"

echo "[4/7] M2 whole-FRF subset (divergence contrast; resumable cells)"
$PY -c "import sys;sys.path.insert(0,'code');import run_sweep;[run_sweep.m2_split(s,1000,1000,4,300,False) for s in range(5)]"

echo "[5/7] figC FRF overlay + figD discretization (§8) + beta-prior sensitivity (§11) (resumable)"
$PY code/extras.py all || true

echo "[6/7] aggregate scorecard + figures (+ per-figure tufte/image-QA/overlap)"
$PY code/aggregate_scorecard.py
bash code/build_figs.sh || true

echo "[7/7] checker (exits non-zero only on RED)"
$PY check.py || CHECK_RED=1

T1=$(date +%s)
$PY -c "import json,os; p='runtime.json'; \
d=json.load(open(p)) if os.path.exists(p) else {}; \
d['elapsed_wallclock_s']=$T1-$T0; d.setdefault('active_runtime_s', $T1-$T0); \
json.dump(d, open(p,'w'), indent=1); print('runtime.json:', d)"
echo "done in $((T1-T0))s"
exit ${CHECK_RED:-0}
