# Priority deliverables — Task Card A (ShockSat closure analyses, 2026-07-22)

Card: `docs/agents/closure_analyses_20260722/task_card_A_closure_analyses.md`. Approved by Andrew
(2026-07-22 adjudication). Everything runs from frozen, hashed artifacts; no new physics, no
model-form work, no formulation calibration. Hard cap 4 h active runtime.

| # | Priority ask (my restatement) | Interpretation / acceptance | Delivered at |
|---|---|---|---|
| A1 | What do the 18 modal frequencies actually identify? Eigendecompose the prior-whitened LOG-θ posterior covariance of the stored 4000 NUTS draws; block-bootstrap CIs; name the strong directions physically via the stored strain-energy artifact. | Known-answer gate: eigenvalues must match Andrew's read-only values ~0.019/0.029/0.259/0.355 (contracted) + five prior-like 0.872–1.166 within bootstrap CI, else STOP. Claim is SUBSPACE-level only, never per-parameter. | `out/a1_subspace.json`, `figures/a1_subspace.png` |
| A2 | Is the 4.6% σ_f discrepancy floor data-driven or prior-driven? Rerun the frozen modal-frequency NUTS model under 5 σ_f priors (HalfNormal 0.02/0.05/0.15, HalfCauchy 0.05, Exponential mean 0.05), ≥4 chains, per-chain draws retained. | Known-answer gate: HalfNormal(0.05) rerun reproduces stored posterior (σ_f median ≈4.6%, θ medians within MC error of theta_full.json) before other variants are interpreted. Non-converged variants = YELLOW with worst R-hat/ESS, never dropped. Plus prior + posterior predictive checks. | `out/a2_sigma_f_sweep.json`, 2 figures |
| A3 | Do the statFEM load bands beat the FEM+6 dB incumbent under calibration AND a proper score, not width alone? Reproduce the stored incumbent undercoverage FIRST, then add CRPS columns for FEM+6 dB (stated-width interval, convention + sensitivity), delivered statFEM band, and parameter-only modal propagation. | Known-answer gate: stored 0.71–0.87 weighted coverage (shear_Y 0.706, normal 0.738, shear_X 0.865), statFEM 2.301×/cov 0.982 reproduced from stored arrays before new columns; STOP if arrays missing. Shear = measured held-out evidence; normal-Z = synthetic self-consistency, labeled in table AND figure. State 2.526 vs 2.958 adjacently. | `out/a3_calibration_table.json`, 2 figures |
| A4 | Why did the whole-FRF posterior separate? 1-D profile likelihood of the iid log-magnitude whole-FRF likelihood along the TWO most FRF-sensitive stiffness multipliers (≥41 grid points over prior 95% range), PROFILING nuisances (drive gain, noise scale), inner-opt convergence recorded per point; annotate separated NUTS chain locations. | Deliverable claim is diagnostic (multimodal or not), turning "posterior geometry" from verdict into diagnosis. Exact likelihood form documented from the source study before computing. | `out/a4_profile_likelihood.json`, 1 figure |
| A5 | Recover the negative phase evidence (circular variance ~0.854, "no sharper slice than magnitude"). | FOUND during recon: `statfem_real_validation_20260617/out/phase_likelihood.json` (circ var 0.8536). Deliverable = hash + citation + provenance note "found, not re-derived". | `out/a5_phase_diagnostic.json` |

Ambiguities flagged at start: none blocking. A3 array availability was the flagged risk; recon shows
`bakeoff_scorecard.json` + `theta_post_L5.npz` + measured caches + frozen `code/bakeoff.py` pipeline exist,
so reproduction runs the stored code path read-only. If the recomputation does not match the stored
scorecard numbers, that is a STOP-and-report event per the card.

Sampler statement (AGENTS.md): NUTS only for A2 (differentiable modal-frequency likelihood, matches the
frozen twin). A1/A3/A4/A5 are deterministic post-processing/optimization; no sampler used or claimed.
