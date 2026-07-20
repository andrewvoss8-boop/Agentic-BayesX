#!/usr/bin/env bash
# Replay the Bilionis review packet end-to-end (consolidation only; no science run).
# Regenerates the 4 new figures, re-copies the reused figures, builds the deck, and QAs it.
set -euo pipefail
cd "$(dirname "$0")"
ROOT=".."   # artifacts/reports (sibling workspaces live here)

echo "[0/4] best-remesh + best-Bayes combined run (~6 min eigensolve + NUTS; writes out/combine_best.json)"
if [ ! -f out/combine_best.json ]; then
  OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python3 code/combine_best.py
else
  echo "  out/combine_best.json exists — skip (delete to re-run)"
fi

echo "[1/4] new consolidation figures (tufte-linted source)"
python3 code/make_review_figs.py

echo "[2/4] copy reused figures from prior workspaces"
cp "$ROOT/shocksat_psd_envelope_twin_20260623/figures/frf_comparison_grid.png"  figures/reuse_frf_grid.png
cp "$ROOT/shocksat_psd_envelope_twin_20260623/figures/residual_map.png"         figures/reuse_residual_map.png
cp "$ROOT/shocksat_psd_envelope_twin_20260623/figures/heldout_psd_examples.png" figures/reuse_heldout_frf.png
cp "$ROOT/ift_real_validation_20260619/figures/figA_scorecard.png"              figures/reuse_ift_scorecard.png
cp "$ROOT/ift_real_validation_20260619/figures/figB_beta.png"                   figures/reuse_ift_beta.png
cp "$ROOT/statfem_consistency_toy_20260616/figures/figA_money_theta_vs_knob.png" figures/reuse_consistency_money.png
cp "$ROOT/statfem_consistency_toy_20260616/figures/figS_schematic.png"          figures/reuse_consistency_schematic.png
cp "$ROOT/shocksat_modelclass_L5_20260619/figures/fig_value_summary.png"        figures/reuse_value_summary.png
cp "$ROOT/shocksat_modelclass_L5_20260619/figures/fig_likelihood_inventory.png" figures/reuse_likelihood_inventory.png
cp "$ROOT/shocksat_modelclass_L5_20260619/figures/fig_strain_energy.png"        figures/reuse_strain_energy.png
cp "$ROOT/shocksat_modelclass_L5_20260619/figures/fig_sensor_map.png"           figures/reuse_sensor_map.png
cp "$ROOT/shocksat_modelclass_L5_20260619/figures/fig_roadblock_remesh.png"     figures/reuse_roadblock_remesh.png
cp "$ROOT/statfem_real_validation_20260617/figures/fig_heldout_frf.png"         figures/reuse_cardC_heldout_frf.png

echo "[3/4] build deck"
python3 code/make_deck.py

echo "[4/4] QA deck (overflow / table-width / spill)"
python3 code/qa_deck.py

echo "DONE -> slides/shocksat_bilionis_review.pptx"
