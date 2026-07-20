#!/usr/bin/env bash
# One-command replay — validated net-CG QOI port (runner card B, 2026-07-16).
#
# REUSES the delivered netcg machinery READ-ONLY and BYTE-IDENTICALLY (netcg_qoi.py, realfrf.load_reduced,
# heldout_drive conventions, the cached L5 NUTS theta posterior). NOTHING is written outside this workspace.
# NO SAMPLER runs here: the L5 theta posterior is REUSED draws (card 5). float64; pinned BLAS threads.
#
# Gate order is enforced, not conventional: s3s4_assess.py ASSERTS out/n0_reference.json status == PASS
# before it will touch anything arm-related (card 2). If N0 had failed, the run stops and BLOCKED.md is the
# deliverable.
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONUNBUFFERED=1
PY=${PY:-python3}
mkdir -p out figures logs

echo "[1/6] GATE N0 — reproduce the delivered twin (1.508/2.301/2.526, tol 0.05) through the ORIGINAL"
echo "      netcg machinery + its reduced model + the reused L5 theta posterior.  HARD GATE."
$PY code/n0_reference.py 2>&1 | tee logs/n0.log

echo "[2/6] MC noise floor of the width-ratio statistic (24 seeds) — what counts as a real difference"
$PY code/mc_noise.py 2>&1 | tee logs/mc_noise.log

echo "[3/6] GATE N1 — bridge: theta POINT vs MODEL decomposition of the study's width gap (diagnostic)"
$PY code/n1_bridge.py 2>&1 | tee logs/n1.log

echo "[4/6] S3 (finalists B/D/R x 3 mapping variants, held-out DEV drives) + S4 (A5b tier update / H4)"
echo "      +XY vault guard active: any read of the +XY drive RAISES."
$PY code/s3s4_assess.py 2>&1 | tee logs/s3s4.log

echo "[5/6] Figures (Tufte-linted) + image-legibility QA"
$PY code/fig_port.py 2>&1 | tee logs/fig.log
$PY code/fig_qa.py 2>&1 | tee logs/fig_qa.log

echo "[6/6] Checker (immutable, SHA-locked). Exits non-zero ONLY on RED."
$PY check.py || true
echo "done."
