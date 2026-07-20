#!/bin/bash
# One-command replay — ShockSat FULL-SPECTRUM FRF study (20260714).
# Stages are resumable; artifacts already present are skipped. Long stages (downloads ~4.5 GB, k=650
# eigensolve ~1-2 h, NUTS folds, remodel loop) run FOREGROUND here for replay fidelity; the original run
# executed them detached (see logs/). Exits non-zero only on RED (checker convention).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

echo "== continuity bars (A0 hard gate) =="
python3 code/repro_continuity.py

echo "== data phase: downloads + wide distillation + vault freeze =="
for Z in "Test03_ModalHammer_990y.zip 676070160 m_ypos_990y" \
         "Test06_ModalHammer_900z.zip 923723571 m_zpos_900z" \
         "Test02_ModalHammer_990z.zip 952326672 m_zpos_990z" \
         "Test04_ModalHammer_990xy.zip 967685959 m_xy_990xy" \
         "Test01_ModalHammer_990x.zip 1069342844 m_xpos_990x"; do
  set -- $Z
  if [ ! -f "data/multiref_wide/${3}_wide.npz" ]; then
    bash code/fetch_zip.sh "$1" "$2"
    python3 code/wide_distill.py "$3"
    rm -f "data/zips/$1"
  fi
done
python3 code/extended_peaks.py

echo "== model/basis phase =="
[ -f out/full_eig_V.npy ] || OMP_NUM_THREADS=6 VECLIB_MAXIMUM_THREADS=6 python3 code/full_eig2.py
[ -f data/packages_wide/A0_wide.npz ] || python3 code/wide_package.py A0_wide
python3 code/check_jax_window.py
python3 code/qoi_weights.py
python3 code/run_baseline_arms.py
python3 code/check_surrogate.py

echo "== arm B (NUTS, 4 folds x 2 variants) =="
for FOLD in m_xpos_990x m_zpos_990z m_ypos_990y m_zpos_900z; do
  python3 code/arm_b_nuts.py "$FOLD"
  python3 code/arm_b_nuts.py "$FOLD" --theta-only
done
python3 code/arm_b_score.py

echo "== arm C (NUTS shape field, 4 folds) =="
for FOLD in m_xpos_990x m_zpos_990z m_ypos_990y m_zpos_900z; do
  python3 code/arm_c_nuts.py "$FOLD"
done
python3 code/arm_c_score.py

echo "== arm D (remodel loop: 3 rounds, agent amplitude-compass + equal-budget seeded random) =="
# Round 1: diagnose the inherited model, score the pre-written agent proposals + seeded random control.
python3 code/diag_wide.py 1 A0_wide
python3 code/run_r1.py
# Round 2: diagnose the round-1 winner, score round-2 proposals + random.
python3 code/diag_wide.py 2 wa1_tbox_soft
python3 code/run_r2.py
# Round 3: diagnose the round-2 winner, score round-3 proposals + random.
python3 code/diag_wide.py 3 wa2_brackets_soft
python3 code/run_r3.py
# Exact-basis spot checks on the projected freeze-set candidates (G04).
python3 code/spot_freeze.py

echo "== arm E (amplitude-inclusive selection re-test) =="
python3 code/arm_e_evidence.py

echo "== arm F + QOI + audits =="
python3 code/arm_f_combine.py
python3 code/netcg_wide.py
python3 code/leakage_audit.py
python3 code/collect_results.py

echo "== vault (single post-freeze read) =="
python3 code/vault_grade.py

echo "== figures + finalize =="
python3 code/make_figs.py
python3 code/finalize_runtime.py
python3 check.py
