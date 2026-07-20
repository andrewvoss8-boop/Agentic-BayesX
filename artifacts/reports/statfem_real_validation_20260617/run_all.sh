#!/usr/bin/env bash
# One-command replay for Card A (validate the StatFEM twin on the REAL ShockSat).
# Fast path: regenerate figures + QA + checker from the cached compute artifacts in out/.
# Heavy compute steps (commented, RESUMABLE: each skips if its out/*.json exists) reproduce out/ from raw data.
set -euo pipefail
cd "$(dirname "$0")"
PY=../../../.venv_nuts/bin/python
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

# ---- heavy compute (hours; each is resumable / skips if its artifact exists). Uncomment for a full rebuild. ----
# $PY code/probe_observable.py           # out/observable_investigation.json   (P1 observable)
# $PY code/probe_matched_path.py         # out/matched_path_sanity.json        (P1.5 gate)
# $PY code/identifiability.py            # out/identifiability.json            (strain energy + FIM)
# $PY code/modal_feature.py             # out/modal_feature.json              (L5 modal, CONVERGES)
# $PY code/heldout_qoi.py               # out/heldout_qoi_L5.json             (held-out-sensor QOI)
# $PY -c "import sys;sys.path.insert(0,'code');import schneider_faithful as s;[s.run(a,n=4000) for a in ('M0','M1','M2','M3')]"  # arms keystone
# $PY code/score_arms.py                # out/scores_summary.json             (arm held-out scoring)
# $PY code/fem_error_sweep.py           # out/fem_error_sweep.json            (Sim A)
# $PY code/modal_amp_feature.py         # out/modal_amp_feature.json          (Sim B)
# $PY code/mc_heldout.py                # out/mc_summary.json                 (>=25-split MC)
# $PY code/heldout_frf_band.py          # out/heldout_frf_band.json           (held-out FRF band)

# ---- fast path: figures + QA + checker (seconds) ----
$PY code/figures.py
$PY code/qa_reports.py
$PY code/image_qa.py || true
echo "---- checker ----"
$PY check.py
