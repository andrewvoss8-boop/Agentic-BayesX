#!/bin/bash
# One-command replay for shocksat_tray_coupled_qoi_20260610.
# Reads ONLY read-only upstream inputs (hashes pinned in
# inputs_sha256_start.json); all stages are resumable (each skips itself if
# its output exists -- delete out/ to force a full rerun).
# Exit code: non-zero only on a RED checker result (documented yellows pass).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
PY=python3

echo "== [1/9] verification gates (V1-V9) =="
$PY code/verify.py

echo "== [2/9] QOI production (nominal + srscache + MC + sweeps) =="
$PY code/run_qoi.py --stage all

echo "== [3/9] mount identifiability gate + variance-decomposition CIs =="
$PY code/identifiability.py
$PY code/variance_ci.py

echo "== [4/9] response-limit proxy QOI (D7) =="
$PY code/proxy_qoi.py

echo "== [5/9] overnight O1+O2: coupled ROM + synthetic survey (D10) =="
$PY code/build_coupled_rom.py
$PY code/make_truth.py

echo "== [6/9] overnight O3: NUTS mount calibration (pinned venv; ~1 h cold) =="
../../../.venv_nuts/bin/python code/run_nuts_mount.py

echo "== [7/9] overnight O4: posterior QOI + value of information =="
$PY code/posterior_qoi.py
$PY code/diagnose_multimodality.py || true
echo "== [7b/9] pooled-mount arm (D15/D16) =="
$PY code/pooled_fim.py
../../../.venv_nuts/bin/python code/run_nuts_pooled.py
$PY code/pooled_diagnosis.py

echo "== [8/9] figures (tufte-linted) =="
$PY code/make_figures.py
$PY ../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py code/make_figures.py || true

echo "== [9/9] checker (green/yellow/red) =="
$PY check.py
