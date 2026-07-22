# ShockSat closure analyses — human-review packet (Task Card A, 2026-07-22)

**Status: see `out/checker_report.json` (immutable checker fe77b00b…; RED-on-empty proven).**
Replay: `bash run_all.sh` (A2 NUTS resume-skips on retained draws; delete `out/a2_draws/` for full
~75-min recompute; all else < 1 min). All five analyses run on frozen, hashed artifacts — no new
physics, no model-form work.

## Method summary (first, per plot gate)

**What this study is.** Five audit calculations that convert asserted report conclusions into
demonstrated ones. Data counts: one flight article, one modal survey (18 paired modal frequencies);
5 measured multiref drives (111 channels × 105 freq pts H1, 45–260 Hz) as the shear evidence; no
flight/build/test-to-test variability anywhere (inherited ceiling).

**Model form + likelihood equations used (all frozen, hashed):**
- A1/A2 (modal twin): K(θ) = A_fix + Σ_g θ_g A_g (74×74 reduced, mass = I), 9 dimensionless group
  stiffness multipliers θ_g, prior log θ ~ N(0, 0.25²) i.i.d. Likelihood (feature-summary choice:
  18 paired log-frequencies, whole-shape/MAC NOT used):
  log f_meas,m ~ Normal(log f_pred,m(θ), σ_f), m = 1..18. σ_f (log-frequency sd, dimensionless,
  ×100 ≈ % frequency error) pools observation noise AND model discrepancy. Inferred: θ (9), σ_f.
  Fixed/not inferred: ζ, boundary conditions, mode pairing (stop-gradient tracking), reduction basis.
- A3 (net-CG bands): tray-region net-CG force spectrum on 400-pt linear grid 45–260 Hz, ζ=0.01;
  method bands from the converged L5 NUTS θ posterior + tier discrepancy models; incumbent =
  nominal ±6 dB. Whole-curve scoring (1-octave smoothed), energy-weighted.
- A4 (whole-FRF): iid log-magnitude WHOLE-data likelihood y_{d,ch}(f) = log10|H1| ~
  Normal(log10|H_model(θ)| + gain_d, σ_n), 3 train drives, 45–400 Hz thinned, ≤30 ch/drive
  (N=6,525 points), exact sub-basis eigh (r0=118) + window operator. Nuisances gain_d, σ_n.
- Sampler statement: NUTS only in A2 (4 chains × 1000/1000, dense mass, tree depth 8 — identical to
  the frozen twin). A1/A3/A4/A5 are deterministic post-processing/optimization; no sampler claimed.

## A1 — What do the 18 modal frequencies actually identify? (GREEN)

Prior-whitened log-θ posterior covariance eigendecomposition (4000 stored converged NUTS draws;
block bootstrap: blocks of 40 within chains, 1000 resamples). **Known-answer gate PASS**: eigenvalues
0.019 / 0.029 / 0.259 / 0.355 (contracted) + five prior-like 0.872–1.166 — all match Andrew's
adjudicated values within bootstrap CI.

**Finding:** the test pins down FOUR stiffness combinations, and they are nearly pure single groups:
bottom_box (λ=0.019, loading +0.97), top_box (0.029, −0.95), plates (0.259, +0.95), cross_beam
(0.355, −0.95). The other five directions (mixes of al_welds, angle_brackets, contact, joints,
steel_welds) return the prior — consistent with the frozen strain-energy table (bottom_box/top_box
carry 47%/35% mean modal strain energy; the weld/bracket/contact groups sit below the σ_f floor).
Claim is **subspace-level only**; no per-parameter identifiability is asserted beyond what the
eigenvectors show. Figure: `figures/a1_subspace.png`.

## A2 — Is the 4.6% σ_f floor data-driven or prior-driven? (YELLOW — the documented honesty tier, not a failure)

Reference HalfNormal(0.05) rerun (same frozen likelihood/settings/seed 42): **PASS — sigma_f median 0.0460 vs stored 0.0463 (dev 0.0002); all 9 theta medians within their per-parameter 3x-MC-SE tolerances (max dev 0.0066 = contact, tol 0.0437; note the checker message juxtaposes max-dev with MIN tol — see decisions_log D6). Reference run converged: worst R-hat 1.009, min ESS 464, 0 divergences**.
Per-variant results (all 4-chain, per-chain draws retained in `out/a2_draws/`, all-variable
diagnostics in the JSON):

| prior | sigma_f median [95% CI] | worst R-hat | min ESS | status |
|---|---|---|---|---|
| HalfNormal(0.02) | 4.2% [3.2, 5.6] | 1.125 | 17 | YELLOW — NOT converged; interval not trustworthy |
| HalfNormal(0.05) reference | 4.6% [3.4, 6.8] | 1.009 | 464 | GREEN |
| HalfNormal(0.15) | 4.8% [3.4, 7.3] | 1.013 | 360 | GREEN |
| HalfCauchy(0.05) | 4.8% [3.5, 6.9] | 1.418 | 6 | YELLOW — NOT converged; interval not trustworthy |
| Exponential(mean 0.05) | 4.3% [3.4, 6.7] | 1.338 | 4 | YELLOW — NOT converged; interval not trustworthy |

**Finding:** the ~4.6% floor is DATA-driven, not prior-driven: the median stays at 4.2–4.8% across a 7.5x range of prior scales and two heavy-tailed families, including the converged loose HalfNormal(0.15) arm (4.8%) — the model-form conclusion survives every variant. Three variants are honestly non-converged (worst R-hat/ESS printed beside every interval and ON the figure); their medians agree with the converged arms but their intervals are not trustworthy. Prior predictive: 18/18 measured frequencies inside the per-mode central 95% prior predictive envelope under ALL five priors (the prior is generous, not restrictive). Posterior-predictive PIT (reference):
per-mode PIT spans 0.08–0.90 and tracks the uniform diagonal — no systematic over/under-dispersion at the reference prior. Figures: `figures/a2_sigma_f_sweep.png`, `figures/a2_predictive_checks.png`.

## A3 — Do the statFEM bands beat FEM+6 dB under a proper score? (GREEN)

**Known-answer gate PASS:** all 28 stored numbers reproduced with max|dev| = 0.000 (scorecard
coverage/width for 3 axes × 3 methods AND per-drive held-out shear coverage), by importing the frozen
bake-off modules read-only with the stored seeds. Incumbent FEM+6 dB weighted coverage 0.865 /
0.706 / 0.738 (shear_X / shear_Y / normal_Z) — it leaks; delivered statFEM 0.995 / 0.982 / 0.987 at
1.508× / 2.301× / 2.526× width.

**New — CRPS (fair-ensemble, energy-weighted, lower better).** On the MEASURED held-out drive answer
keys (5 drives × 2 shear axes): statFEM 1.137 / 0.709 (shear_X / shear_Y strong-drive mean) vs
FEM+6 dB 1.252 / 0.771 (log-uniform envelope convention) vs parameter-only 1.465 / 0.820. statFEM
wins 8/10 drive-axis cells, and the ranking is stable under ALL THREE envelope conventions
(log-uniform, linear-uniform, Gaussian-95%) — the two losses are cross-axis weakly-excited cells
(shear_X under +Y and +Z(990) drives). normal_Z CRPS (13460 / 11290 / 11121) is computed on the
synthetic truth ensemble and is labeled **self-consistency, NOT validation** in the table AND the
figures. Normal-Z widths stated adjacently: **2.526×** (delivered reference) vs **2.958×**
(tier-updated configuration — the one matched extended-band mode's observed cross-drive ln-amplitude
scatter 1.393 exceeded the assumed 0.80, honestly widening the band).

**Conclusion:** the load-band claim survives a proper score on measured evidence — the incumbent is
sharp but miscalibrated; statFEM is both better-calibrated AND better-scored. The A3 stop condition
(narrative flip) was NOT triggered. Figures: `figures/a3_table.png`, `figures/a3_coverage_width.png`.

## A4 — Why did the whole-FRF posterior separate? (GREEN)

Profile likelihood of the exact iid θ-only likelihood (form documented from the frozen source in the
output JSON) along the two most FRF-sensitive multipliers (choice rule: energy-weighted RMS
∂log10|H|/∂log θ_g at θ=1 — bottom_box 6.35, top_box 4.86, next 2.90). 41 log-spaced points over the
prior 95% range; drive gains + σ_n PROFILED at every point (closed-form MLE, gradient norm < 1e-4
recorded at all 82 points; penalized L-BFGS-B variant also recorded).

**Finding:** both profiles are severely multimodal — **10 local maxima each**, tens-of-nats deep
ridges from peak-crossing structure. The four separated NUTS chain means of the stored non-converged
run (R-hat 44.7, min ESS 2.0) sit in DIFFERENT local modes near θ≈1. "Posterior geometry" is now a
diagnosis (rugged multimodal likelihood), not a verdict word. Figure: `figures/a4_profile.png`.

## A5 — Negative phase evidence (GREEN, found — not re-derived)

The original artifact was **located**: `statfem_real_validation_20260617/out/phase_likelihood.json`
(SHA-256 recorded). Circular variance of measured-vs-model phase at matched modes = **0.8536** (~1 ⇒
incoherent across channels); θ-slice relative contrast: complex 0.000127 vs magnitude 0.009355 — no
sharper parameter slice from phase. Scope: the single-hit dataset (46 channels, 12 matched modes),
predating the multiref caches; documented as such. `out/a5_phase_diagnostic.json`.

## Result status & inherited ceiling

Gate-by-gate: see `out/checker_report.json`. Inherited science ceiling (unchanged, restated per
card): no direct net-CG answer key for normal_Z (synthetic self-consistency only), one flight
article / one campaign, no build/test variability modeled, and the whole-FRF/-held-out posteriors
remain non-converged (now with a demonstrated mechanism). Runtime: `runtime.json` (active ≤ 4 h cap).

## Files

`out/a1_subspace.json` · `out/a2_sigma_f_sweep.json` + `out/a2_draws/` · `out/a3_calibration_table.json`
· `out/a4_profile_likelihood.json` · `out/a5_phase_diagnostic.json` · `source_manifest.json` (57
inputs, verified unchanged end-to-end in `out/end_hash_verify.json`) · figures + `out/fig_manifest.json`
+ `out/fig_qa.json` + `out/tufte_lint.txt` · `check.py` + `CHECKER.sha256` + `out/checker_empty_report.json`.
