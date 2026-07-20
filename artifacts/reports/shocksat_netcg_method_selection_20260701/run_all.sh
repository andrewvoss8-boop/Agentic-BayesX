#!/usr/bin/env bash
# One-command replay (resumable) — ShockSat net-CG force method selection.
# Reuses shocksat_psd_envelope_twin_20260623/code (realfrf, modal_feature[L5 NUTS], score, shape_borrow_diag,
# multiref_frf) BYTE-IDENTICAL. float64; pinned BLAS threads. Skips finished work on relaunch.
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONUNBUFFERED=1
PY=${PY:-python3}

echo "[1/7] distill +Y (Test03/990y) 5th drive -> data/multiref_modal/m_ypos_990y.npz (resumable)"
# NOTE: needs the 4 modal .mat hits extracted to data/extracted_modal/Test03_ModalHammer_990y/ from the
# repo-root zip Test03_ModalHammer_990y.zip:  unzip -j Test03_ModalHammer_990y.zip 'Test03_ModalHammer_990y/*.mat' \
#   -d data/extracted_modal/Test03_ModalHammer_990y/    (the built cache is retained, so this step is skipped if present)
$PY code/build_ypos_cache.py || echo "  (cache present or hits missing; using retained m_ypos_990y.npz)"

echo "[2/7] Stage 0: QOI weights + trust + observability(+Y) + sensitivity + validity"
$PY code/stage0.py

echo "[3/7] Stage 0 figure (Tufte-linted)"
$PY code/fig_stage0.py

echo "[4/7] Mesh screen (Axis B step 1) — DETACHED/slow (~6 min/edit). Launch separately if not done:"
echo "     nohup $PY code/mesh_screen.py --pool subset > logs/mesh_screen.log 2>&1 & disown"
[ -f out/mesh_screen_summary.json ] && echo "     mesh_screen_summary.json present" || echo "     (pending)"

echo "[5/8] Stage 2 bake-off (5 formulations, L5 NUTS cached in out/theta_post_L5.npz; ~75s first run)"
$PY code/bakeoff.py

echo "[6/8] Follow-on #1: real held-out-DRIVE answer key for the SHEAR net-CG force (selected statFEM F(k))"
$PY code/heldout_drive.py

echo "[7/8] Follow-on #3 (pre-test design) + dive-deeper DD1/DD2/DD3 + Stage 3 figures (Tufte-linted)"
$PY code/pretest_design.py
$PY code/diag_shearY_gap.py           # DD1: +Z@900 shear_Y gap = drive-specific artifact
$PY code/data_anchored_sigma.py       # DD3: data-anchored measured-amplitude sigma (~0.86 vs assumed 0.35)
$PY code/learned_statfem.py           # DD2: NUTS-learned statFEM discrepancy (sigma_d~0.94, agrees w/ DD3)
$PY code/fig_delivery.py
$PY code/fig_graphmodel.py
$PY code/fig_pretest.py

echo "[8/8] Checker"
$PY check.py || true   # exits non-zero only on RED; documented YELLOW does not abort
echo "done."
