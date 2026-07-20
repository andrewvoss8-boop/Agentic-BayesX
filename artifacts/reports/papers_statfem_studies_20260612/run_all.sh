#!/usr/bin/env bash
# One-command replay: Schneider+Das/Debnath x StatFEM study program.
# Studies A (FRF discrepancy A/B), Phase-1 (control+sweep), C (REAL panel), D (complex-modal),
# all figures + GIF, the deck, and the checker.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd ../../.. && pwd)"
NUTS="$ROOT/.venv_nuts/bin/python"          # jax/numpyro
FEM="$ROOT/.venv_fem_phase1/bin/python"     # matplotlib/PIL/scipy
SYS=python3                                  # python-pptx
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export XLA_FLAGS="--xla_force_host_platform_device_count=4"

# NOTE: full replay ~2.5-3 h (Study G NUTS dominates). Steps are resumable where marked.
echo "[1/14] Study A NUTS (V1/V2/V3, two holdout schemes)";      "$NUTS" code/run_study_a.py
echo "[1b]   Study A ablation (D37: log-iid isolates correlation)"; "$NUTS" code/study_a_ablation.py
echo "[2/14] Phase 1 NUTS (control truth=2DOF + len_f sweep)";   "$NUTS" code/run_phase1.py
echo "[3/14] Study D NUTS (Das/Debnath latent vs eigh)";         "$NUTS" code/study_d.py
echo "[4/16] Study G self-tests";                                "$NUTS" code/ums_model.py | tee out/ums_selftest.log
echo "[5/16] Study G UMS-FEM headline (production; ~25 min)";    "$NUTS" code/run_ums2.py
echo "[6/16] Study G frames (10 reduced UMS-FEM runs)";          "$NUTS" code/run_ums2_frames.py
echo "[6b]   Study H cure A/B (3 arms)";                         H_PROBE=1 "$NUTS" code/run_ums3.py
echo "[6c]   Study I unknown forcing (2 arms)";                  I_PROBE=1 "$NUTS" code/run_ums4.py
echo "[6d]   Study F-mini front-end guardrail (forward-only)";   "$NUTS" code/study_f_mini.py
echo "[6e]   Study J REAL-panel UMS calibration";              J_PROBE=1 "$NUTS" code/run_studyj.py
echo "[6f]   Study K real-data per-mode freq A/B";              K_PROBE=1 "$NUTS" code/study_k.py
echo "[6g]   Study L real-data sharpen A/B (freq vs freq+amp)"; L_PROBE=1 "$NUTS" code/study_l.py
echo "[6h]   Study M virtual sensing under sensor faults (no MCMC)";    "$NUTS" code/study_m.py
echo "[7/16] Study A figures + GIF";                             "$FEM"  code/plots.py
echo "[7b]   Study A ablation figure";                           "$FEM"  code/plot_ablation.py
echo "[8/16] Phase 1 figures";                                   "$FEM"  code/plot_phase1.py
echo "[9/16] Study C REAL-data figures";                         "$FEM"  code/study_c.py
echo "[10/16] panel FEA xlsx->npy (system py: openpyxl)";        "$SYS"  code/extract_panel_fea.py
echo "[10b/16] Study C2 real-panel prep (D19-unblocked)";        "$FEM"  code/study_c2_realprep.py
echo "[11/16] Study D figure";                                   "$FEM"  code/plot_d.py
echo "[12/16] Study G figures";                                  "$FEM"  code/plot_ums.py
echo "[13/16] Study G GIFs";                                     "$FEM"  code/make_gifs_ums.py
echo "[13b]  Study H/I figures";                                 "$FEM"  code/plot_hi.py
echo "[13c]  Study G bimodality figure";                         "$FEM"  code/plot_g_bimodal.py
echo "[13d]  Study J figure";                                    "$FEM"  code/plot_j.py
echo "[13e]  Study K figure";                                    "$FEM"  code/plot_k.py
echo "[13f]  Study L figure";                                    "$FEM"  code/plot_l.py
echo "[13g]  Study M figure";                                    "$FEM"  code/plot_m.py
echo "[14/16] slide deck";                                       "$SYS"  code/make_deck.py
echo "[15/16] checker";                                          "$SYS"  code/check.py
echo "[16/16] done"
echo "done -> packet.md, slides/papers_statfem_studies.pptx, checker_report.json"
