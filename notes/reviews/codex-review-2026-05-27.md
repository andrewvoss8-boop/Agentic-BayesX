# Codex Review - 2026-05-27

## Original prompt recalled
The project goal is to start Agentic BayesX as a harness-first, agentic scientific computing workflow: implement Ilias-style best practices for coding agents, begin with a replication project, then build a simple 2DOF FBS/STATFEM example before moving toward MDOF/FEM transfer functions and eventually autonomous experiment control. The first technical example is a fixed-base 2DOF system with a dome primary at 110 Hz and tray secondary at 75 Hz, synthetic modal/test/flight channels, uncertainty assumptions, Bayesian updating of stiffness/damping/forcing, and a tray peak-response QOI. The meta-goal is more important than the toy output: make agent work verifiable, documented, anti-cheating, reproducible, and easy for a human to inspect and redirect.

## Files reviewed
- `docs/CODEX.md`, `docs/codex_prompts/{replicate,review,extend}.md`
- `AGENTS.md`, `harness/program.md`, immutable checker manifest
- `design/statfem-assumptions.md`
- `src/twodof/model.py`, `src/twodof/synthetic_data.py`
- `src/inference/mcmc.py`
- `src/mdof/reduced_transfer.py`
- `tests/test_posterior_recovery.py`, `tests/test_mdof_transfer.py`
- `scripts/run_pipeline.sh`, `scripts/visualize_results.py`
- `references/*`, `experiments/fem-agent-setup/README.md`, prior notes

## Assumptions and units
- Frequencies are in Hz.
- Nominal masses are synthetic: `m1 = 1.0`, `m2 = 0.6`. Treat these as arbitrary mass units until a physical article is defined.
- Stiffness and damping are derived from these masses and target natural frequencies, so their units are consistent with the synthetic mass and SI-like frequency convention but are not calibrated hardware values.
- Apparent mass, transfer functions, forcing amplitude, and tray acceleration QOI are synthetic/arbitrary-unit quantities.
- The flight forcing model is not a general unknown spectrum; it is currently a positive real two-parameter power-law magnitude model.

## Baseline before sampler fix
Command: `bash scripts/run_pipeline.sh`

Result: canary harness passed, immutable checker hashes matched, posterior recovery passed, MDOF transfer test passed, plots regenerated.

Key baseline sampler metric from `artifacts/tests/posterior_recovery_report.json`:
- `acceptance_rate = 0.016666666666666666`
- All tracked posterior relative errors were under the existing `0.35` smoke-test threshold.

## Sampler changes made
File: `src/inference/mcmc.py`

- Replaced all-parameter random-walk MH with random-scan MH that proposes one log-parameter per step by default.
- Added burn-in proposal adaptation toward a target acceptance rate.
- Lowered the default proposal scale from `0.06` to `0.02`, which improved the full 240-frequency MCMC artifact.
- Rewrote the Gaussian likelihood evaluation to use a Cholesky-based whitening factor instead of building and inverting a 2n-by-2n real/imag block covariance.
- Added a small covariance-factor cache keyed by discrepancy hyperparameters.
- Added config validation for `n_steps`, `burn_in`, `thin`, proposal scale, target acceptance, and proposal block size.
- Added sampler diagnostics, post-burn acceptance, posterior standard deviations, 95 percent intervals, and QOI intervals to `artifacts/inference/twodof_mcmc_result.json`.
- Changed QOI posterior mean to the sample mean of the QOI, while also preserving `qoi_peak_tray_accel_at_mean_params`.

## Validation after fix
Final command: `bash scripts/run_pipeline.sh`

Final canary result:
- `artifacts/runs/canary-20260527-183723/metadata.json`
- `status = pass`
- `checker_manifest_mismatch_before = []`
- `checker_manifest_mismatch_after = []`

Final posterior recovery smoke test:
- `artifacts/tests/posterior_recovery_report.json`
- `acceptance_rate = 0.216`
- Relative errors: `k1 = 0.0125`, `k2 = 0.0325`, `k12 = 0.2022`, `force_amp = 0.3214`, `force_fc = 0.1043`, `qoi_peak_tray_accel = 0.00117`
- `pass = true`

Final full default MCMC artifact:
- `artifacts/inference/twodof_mcmc_result.json`
- `acceptance_rate = 0.2009`
- `post_burn_acceptance_rate = 0.1408`
- Relative errors in tracked quantities: `k1 = 0.0104`, `k2 = 0.0210`, `k12 = 0.1393`, `force_amp = 0.1163`, `force_fc = 0.0671`, `qoi_peak_tray_accel = 0.00303`

Final MDOF test:
- `artifacts/tests/mdof_transfer_report.json`
- `relative_l2_error = 0.0514`
- `pass = true`

Final plots:
- `artifacts/plots/manifest.json` lists six PNGs: nominal 2DOF FRFs, synthetic channels, posterior vs truth, posterior channel fit, MDOF FRF comparison, and MCMC traces.

Note: `python3 tests/test_posterior_recovery.py` fails without `PYTHONPATH=.` because the scripts import `src.*`. `scripts/run_pipeline.sh` sets `PYTHONPATH=.` and passes.

## Review findings
1. The original sampler was the main objective issue: acceptance around `0.017` means the chain was barely moving. This is now improved in the smoke test and full artifact, but it is still a simple MH baseline, not production Bayesian inference.
2. Channels 2 and 3 are currently identical forward models (`apparent_mass_from_drivepoint(..., dof=1)`), so they are two noisy replicates of the same quantity rather than distinct interface modal and tray impact measurements. This can overweight one modeled transfer function and hide FBS mistakes.
3. The flight case is simplified much more than the prompt implies. The unknown input is estimated as a two-parameter, positive real, power-law magnitude, not an arbitrary forcing spectrum with phase/cross-spectral uncertainty.
4. Noise and model discrepancy are additive in raw complex units and share one covariance model across all channels. Because the channels have different magnitudes and physical meanings, this can misweight measurements. Per-channel scales or normalized residual models should be considered next.
5. The discrepancy GP hyperparameters are inferred from the same synthetic data used for parameter recovery. This is acceptable for the bootstrap, but identifiability between discrepancy, damping, and forcing remains a real risk.
6. The MDOF prototype is a useful shape test, but `chain_system` is not clearly fixed-base; it has no explicit ground spring at the first DOF and includes a rigid-body mode. That is fine if labeled as a free-chain prototype, but it conflicts with fixed-base language.
7. MDOF modal reduction uses simple dense eigenvalue routines and diagonal damping. This is okay for the current toy model, but it is not yet a general FEM workflow.
8. Harness discipline is good for the canary trial, but the posterior/MDOF tests are not yet wrapped in a single immutable trial manifest like the canary. The pipeline is reproducible, but not all scientific metrics have canary-style anti-cheating protection.
9. The docs refer to `docs/CODEX.md`; the user requested `docs/codex.md`. This works on the current filesystem but could break on a case-sensitive filesystem.
10. Plot generation emits a Matplotlib cache warning because `/Users/avoss/.matplotlib` is not writable. The plots still generate, but `scripts/run_pipeline.sh` should eventually set `MPLCONFIGDIR` to a writable artifact/cache directory.

## Questions for the human
- What should the interface apparent mass physically mean: drive/response at the dome side, tray side, or an assembled boundary/interface coordinate?
- Should the flight forcing be a parametric spectrum, a nonparametric spectrum over frequency, or a latent process with smoothness/positivity constraints?
- Are `m1 = 1.0` and `m2 = 0.6` just normalized masses, or should they map to credible dome/tray effective modal masses?
- Should success for agent trials prioritize posterior recovery, posterior predictive checks, model-form-discrepancy calibration, or engineering QOI coverage?
- Should the next milestone be measurement-channel fidelity or inference diagnostics?

## Prioritized next extensions
1. Distinguish channels 2 and 3 with separate forward models and tests. Effort: medium.
2. Add per-channel noise/discrepancy scaling and posterior predictive checks on held-out frequency bands. Effort: medium.
3. Add effective sample size, trace/autocorrelation summaries, and multi-chain convergence checks. Effort: medium.
4. Make the MDOF prototype explicitly fixed-base and export mass/stiffness/damping matrices as checkable artifacts. Effort: small to medium.
5. Add a hardware-control stub trial with deterministic fake spectra before connecting real lab equipment. Effort: medium.

## Limitations
This remains a synthetic benchmark. It is good enough to exercise harness discipline and agent workflow, but it is not yet a validated STATFEM/FBS structural dynamics workflow for aerospace hardware.
