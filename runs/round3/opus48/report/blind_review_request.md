# Review request — BLIND inference round (for the master / a labmate)

## What to check first
1. **Blindness held:** I only read `runs/round3/codex_truth/dataset/` (observations.npz + data_contract.md).
   No reference to `sealed_truth/`, Codex `code/`, or Codex `report/` in my code or docs
   (`grep -rn "sealed_truth\|codex_truth/code\|codex_truth/report" code/` → none).
2. **Convergence is reported as a FAILURE, not hidden.** `blind_nuts_diagnostics.md`: worst R-hat 2.41,
   min ESS 5, multimodal. I do NOT claim "NUTS active." All intervals are labeled NOT-YET-CONVERGED.
3. **Coverage read WITH sharpness:** held-out new-build coverage 0.94 but log-width 2.84 (~12×) =
   wide-but-covering; held-out band coverage 0.88 (< 0.95). See `figures/blind_heldout_calibration.png`.
4. **QOI bias stated up front:** netCG 3·GRMS q50 3.16 g vs published 0.46–0.96 g (~5× high); driving-point
   QOI mapping alone is ~2× high (measured on published data). `blind_qoi_results.json`.

## For the master's scoring (vs the SEALED truth)
- Posterior draws: `report/blind_posterior.npz` (k_strut_pop, f_dome, sigma_build, sigma_e, sigma_d, beta,
  z_b) + model constants (M_base6, m_dome, grid, ell_d). Marginal summaries in `blind_results.json`.
- Caveat: the posterior is MULTIMODAL / non-converged. Score bias/coverage if useful, but the honest
  finding is that blind recovery BROKE — the independent truth's model-form error is outside my coarse
  model's span. Expect bias (k_strut low, f_dome low, σ_e inflated) and QOI over-prediction.

## Known limitations (full list: `blind_known_failures.md`)
Coarse symmetric model (6 equal struts, single axial dome mode), magnitude-only likelihood, nothing > 115 Hz,
frequency-only discrepancy (cannot represent symmetry-breaking/higher-mode error → de-identifies physics).

## Suggested next step (not done this run)
Structure-based (per-strut/property) discrepancy + asymmetric/higher-fidelity forward model + complex
likelihood; possibly modular/cut updating. This is the Stage-3 direction (decisions_log D12).
