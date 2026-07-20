# bilionis_update_20260702 — 2-slide status deck + one-paragraph update (CONSOLIDATION ONLY, no new science)

Deliverable: `slides/bilionis_update_20260702.pptx` (2 slides). Rebuild: `python3 code/make_update_deck.py`.

- Figures are provenance-labeled COPIES (`reuse_` prefix): ShockSat node cloud w/ 9 calibration groups
  (modelclass_L5_20260619) + measured-vs-FEM FRF comparison grid (psd_envelope_twin_20260623).
- Every number traces to a checker-backed artifact: shocksat_composite_bakeoff_20260702 (OVERALL YELLOW
  57G/6Y/0R — Beck CRPS-skill −0.78→−0.34, remodel evidence P≈0.72 fails held-out, MAC null),
  shocksat_netcg_method_selection_20260701 (GREEN 22/0/0 — bands/coverage, FEM+6dB under-covers),
  bilionis_review_20260626 (FRF corr 0.269→0.338).
- Nothing stated stronger than the checkers; the paragraph text lives in code/make_update_deck.py (PARA).
