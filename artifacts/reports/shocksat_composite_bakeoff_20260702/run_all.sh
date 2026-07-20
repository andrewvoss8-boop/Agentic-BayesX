#!/bin/bash
# One-command replay — composite bake-off (all stages resumable; tier-2 is the ~3.5 h step).
# Checker (check.py) is SHA-locked (CHECKER.sha256); it exits non-zero only on RED.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4
python3 code/gen_candidates.py                     # 151 model-form candidates (allowed families only)
python3 code/tier1_screen.py                       # cheap subspace screen (~30 s)
python3 code/tier2_full.py                         # full 399k-DOF eigensolves, top ~30 (+M0)  [resumable]
python3 code/tier3_evidence.py                     # shape-inclusive evidence + prior sweep
python3 code/run_arms.py                           # NUTS for the 6 arms                      [resumable]
python3 code/score_matrix.py                       # R1/R2/R3 + delivery selection
python3 code/fig_matrix.py                         # figures (tufte-linted script)
python3 check.py                                   # locked checker
