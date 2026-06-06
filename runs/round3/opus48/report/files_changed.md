# Files changed — Stage 3 (Claude Code Opus 4.8 inference runner, BLIND)

All writes confined to `runs/round3/opus48/`. Immutable checkers untouched (verify
`shasum -a 256 -c harness/checkers/manifest.sha256`). Did NOT open `codex_truth/sealed_truth/`, Codex code,
or Codex report — consumed only `codex_truth/dataset/`.

## New code (`code/`)
- `blind3_model.py` — Stage-3 forward model: per-strut ASYMMETRIC hexapod load apparent mass (vectorized
  batched complex solve, JAX), source dome (rigid + axial bounce), M_pub=M_S+M_L; structure/property-based
  per-strut feature-kernel discrepancy (`feature_corr`, `apply_discrepancy`); canonical FBS netCG QOI.
- `blind3_infer.py` — hierarchical NumPyro NUTS: per-strut k_pop + structured discrepancy (+σ_d) + f_dome +
  per-build z_b (+σ_build) + σ_e; complex (re+im) likelihood; adaptive grid from data peaks; held-out
  calibration; without-d + starve-data companions; effective-vs-nominal sample count.
- `blind3_qoi.py` — full-uncertainty netCG (FBS contract) for BOTH posteriors (with-d, converged without-d);
  netCG transfer (f→0 limit + resonance), 3·GRMS vs truth, interface PSD vs spec (narrow-band exceedance).
- `blind3_figs.py` — posterior-predictive AM overlays (train + held-out, per DOF, log-f); with/without
  discrepancy split comparison; hyperparameter posteriors.
- `blind3_gridinv.py` — grid-invariance / over-counting companion (refit at 1× vs 2× grid density).
- `blind3_pptx.py` — Stage-3 review packet PPTX.

## New report artifacts (`report/`)
- `packet_stage3.md` (this run's packet), `packet.pptx` (regenerated for Stage 3).
- `blind3_results.json`, `blind3_companions.json`, `blind3_heldout.json`,
  `blind3_nuts_diagnostics.{md,json}`, `blind3_qoi_results.json`, `blind3_qoi_results_nodisc.json`,
  `blind3_gridinv.json`, `blind3_posterior.npz`, `blind3_posterior_nodisc.npz`, `blind3_run.log`,
  `blind3_gridinv.log`, `manifest.json` (Stage-3), `runtime.json` (Stage-3).
- `figures/blind3_*.png` (netcg transfer/grms/psd × {withd,nodisc}, ppc train/heldout, split_with_d,
  hyperparams).
- Appended: `decisions_log.md` (D25–D30), `priority_deliverables.md` (Stage-3 table), `blind_known_failures.md`
  (Stage-3 addendum), `commands.md` (Stage-3 replay).

## Unchanged (prior blind round, preserved for the master)
- `blind_*.{py,json,npz,md}`, prior `packet.md`, `handoff_to_master.md`, `master_plan.md`, etc.
