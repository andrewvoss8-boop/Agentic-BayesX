# StatFEM ShockSat held-out-QOI evaluation — Human-Review Packet

**Workspace:** `artifacts/reports/statfem_shocksat_eval_20260616/`
**Replay:** `bash run_all.sh` (resumable; launch detached for the ~2-3 hr NUTS sweep). **Checker:** `python3 check.py` → `checker_report.json`.
**Date:** 2026-06-16. **Sampler:** NumPyro NUTS (No-U-Turn HMC), 4 chains, float64, pinned `.venv_nuts` (jax 0.4.30 / numpyro 0.15.3), dense mass, `max_tree_depth=6`, `target_accept=0.9`.
**Experiment B** of the StatFEM-evaluation pair (this runner = the ShockSat held-out-QOI study; a sibling runs the simple consistency toy).

> **Read this first — honesty banner.** This is an EVALUATION of StatFEM, not a defense or an attack
> (Ilias: "build, evaluate, identify its gaps, suggest improvements"). "StatFEM does not work here" is a
> permitted, valuable finding. The checker certifies the criterion is BUILT and REPORTED WITH NUMBERS; it does
> NOT force StatFEM to win. Every interval is printed next to its worst-case R-hat/ESS; nothing is called
> "converged" unless it passed the gate (max R-hat ≤ 1.05, min ESS ≥ 200, div-frac < 2% over ALL variables).
> Scope: SYNTHETIC, plain ShockSat (9-group, NO tray), ONE synthetic realization per combo (5 combos = 5
> distinct truths). **Checker overall: see `checker_report.json` (filled by `bash run_all.sh`).**

---

## 0. Method summary (model form, likelihood, data, what's inferred)

**Glossary (plain English; ML/stats terms defined on first use).** *StatFEM* (statistical finite element method)
= a FEM whose output is corrected by a learned statistical *discrepancy* `d` (a model-form-error function), so
predictions carry "my physics may be wrong" uncertainty, not just measurement noise. *θ_g* (theta,
dimensionless) = per-part-group stiffness scale; θ_g=1.15 is exactly +15% Young's modulus / spring rate of that
group (9 groups). *Coverage* = fraction of held-out truth values inside the predicted 95% band; calibrated ≈
0.95, "confidently wrong" = a tight band that misses (coverage ≪ 0.95). *NUTS* = the gradient MCMC; "converged"
needs the diagnostics above, not merely that it ran. *σ_d* = the learned discrepancy scale (a model-form-error
thermometer). *QOI* = quantity of interest (here a shock/vibration response metric) at a held-out sensor.

**Forward model (plain ShockSat, differentiable, reduced).** The 9-group reduced ShockSat FEM from
`shocksat_fem_modal_twin_20260609` (COPIED, never edited): `K_red(θ)=A_fix+Σ_g θ_g A_g` (74×74, mass = I).
The per-sensor accelerance FRF (Frequency Response Function = response acceleration per unit input force, vs
frequency) is synthesized with constant hysteretic damping (loss factor η = 2ζ) via the resolvent of K_red(θ):

    H_s(ω) = -ω² · obs_V[s,:] · [(1+iη) K_red(θ) - ω² I]^-1 · obs_V[d,:]^T

(point-force drive at DOF d, response at sensor DOF s). This uses an `eigh` of K_red OUTSIDE the gradient path
(the FRF sum is degeneracy-robust); it avoids the near-degenerate-eigenvector gradient blow-up that the modal
twin's MAC arm hit (D10). Verified: numpy ≡ jax to 1e-14; gradient finite across 300 prior draws; 0.71 ms/grad.

**Likelihood (WHOLE LOG-MAGNITUDE FRF — no peak/feature selection).** The residual on each observed channel is
`R_s(f) = log|H_meas,s(f)| - log|H_model,s(f;θ)|` over all 160 band points (45–260 Hz). This is the
**whole-data (whole log FRF)** likelihood choice (not selected peaks/features), stated explicitly per the
likelihood-data-usage gate. The four arms differ only in the residual covariance:

- **M0 naive:** `R ~ N(0, σ_meas² I)` — σ_d ≡ 0, no model-form mechanism (Bilionis's confidently-wrong arm).
- **M1 StatFEM-iid:** `R ~ N(0, (σ_meas²+σ_d²) I)` — learn σ_d, iid output discrepancy.
- **M2 StatFEM-Schneider:** `R ~ N(0, σ_meas² I + σ_d² C)`, `C = C_f ⊗ C_z` correlated over log-frequency AND
  sensor distance (Schneider 2022 complex-correlated discrepancy; reused from `papers_statfem_studies_20260612`).
- **M3 StatFEM-orthogonal:** `C → P_⊥ C P_⊥`, `P_⊥ = I − J(JᵀJ)⁻¹Jᵀ` removes the θ→FRF sensitivity span (the
  discrepancy cannot absorb θ-like variation — Brynjarsdottir-O'Hagan / Plumlee orthogonal-GP idea).

**Held-out prediction (the trust test).** θ predicts all sensors (modes are global). At held-out sensors the
discrepancy is: M0 none; M1 marginal iid σ_d (no spatial transfer); **M2/M3 GP-conditional (kriged) from the
observed-sensor residuals** using the Schneider freq×space covariance. QOIs (Q2/Q3): (a) peak |H| in the band,
(b) band-GRMS-like `√(∫|H|² df)`. Coverage = fraction of held-out CLEAN-truth QOI inside the 95% predictive band.

**Inferred:** θ_g (9) + σ_d (M1/M2/M3; M0 fixes σ_d=0). **Fixed:** mass, geometry, mesh, reduced basis, drive
DOF, ζ, frequency grid, discrepancy correlation lengths (M2/M3), σ_meas, projector P_⊥. **Priors:**
θ_g ~ LogNormal(0, 0.25); σ_d ~ HalfNormal(0.3).

**Data counts.** **One synthetic realization per (combo, arm)**; the 5 combos are 5 DISTINCT truths (distinct θ
bias AND distinct Schneider field realization), reported as a distribution over 5. No flight/build/test
variability modeled (one nominal article). Two injected model-form-error layers: parametric θ bias (the 5
combos) + the Schneider correlated-complex field (std 0.03→0.12, lengths ℓ_f=0.30 log-Hz, ℓ_z=12 in).

**Why synthetic is valid here (it was NOT for the real test data).** Truth and inference share the FEM geometry,
so the test-tap-vs-FEM transfer-path objection (the upstream observation-layer constraint) does not apply.

**Run-specific schematic:** `figures/fig_schematic.png`.

---

## 1. The five truth bias combos (same data per combo, all 4 arms)

| combo | name | injected θ_truth offsets |
|---|---|---|
| 1 | identifiable_only | top_box ×1.15, bottom_box ×0.90 |
| 2 | unidentifiable_only | joints ×1.20, contact ×1.15 |
| 3 | mixed | top_box ×1.15, joints ×1.20, plates ×0.88 |
| 4 | large | cross_beam ×1.20, joints ×0.82 |
| 5 | broad_small | bottom_box 1.08, top_box 0.92, plates 1.10, cross_beam 0.90, joints 1.10 |

Plus the Schneider correlated-complex discrepancy on every combo (a distinct realization per combo).

---

## 2. MONEY RESULT — held-out-QOI coverage across the 5 combos, by arm

*(Filled from `out/coverage_summary.json` / `out/scorecard.json` by `bash run_all.sh`. Figure:
`figures/figA_heldout_qoi_coverage.png`.)*

<!-- RESULTS_MONEY -->

---

## 3. Discrepancy-structure comparison (naive vs iid vs Schneider vs orthogonal)

*(Filled from `out/arm_comparison.json`. Figure: `figures/figB_arm_comparison.png`.)*

<!-- RESULTS_ARMS -->

---

## 4. θ recovery and the identifiability gate

Only ~4/9 groups carry real modal strain energy (bottom_box, top_box, plates, cross_beam) — reproducing the
ShockSat modal-twin 4/9 finding on a DIFFERENT observable (FRF vs frequency-only). The FRF-FIM at the realized
σ_d floor is reported but is a linearization that over-states identifiability near resonances; the operative
test is the posterior recovery in the cells. Figures: `figures/figC_theta_recovery.png`,
`figures/figE_identifiability.png`.

<!-- RESULTS_THETA -->

---

## 5. Discretization-resolution gate

Frequency grid: log-spaced 45–260 Hz, 160 points (A4). Reduced 74-mode basis (54.6–321.7 Hz). The reduced FRF is
validated against a FULL-ORDER direct eigensolve of the 399,510-DOF reduced(independent)-DOF system at a biased
θ (combo 3); plus grid-density and modal-truncation refinement. *(Filled from `out/discretization.json`.)*

<!-- RESULTS_DISC -->

---

## 6. Sensitivity gate

Varied (on combo 3, arms M0/M2): held-out-channel choice, damping ζ∈{0.01,0.03}, narrower band, and an
inference correlation-length MISMATCH. *(Filled from `out/sensitivity.json`.)*

<!-- RESULTS_SENS -->

---

## 7. StatFEM evaluation scorecard

*(Filled from `out/scorecard.json`: claim → evidence(number) → verdict → suggested improvement.)*

<!-- RESULTS_SCORECARD -->

---

## 8. Limitations / what would change the conclusion

- **Synthetic surrogate discrepancy.** The injected model-form error is a parametric θ bias + a Schneider
  correlated-complex field, not a measured real-structure discrepancy; real error may differ in structure.
- **One realization per combo** (5 combos = 5 truths); no flight/build/test variability.
- **Schneider inference uses the TRUE correlation lengths** (favorable to M2/M3); the length-mismatch
  sensitivity arm tests robustness to this.
- **Partial θ recovery is expected** (the 4/9 strain-energy limit); we do NOT claim recovery of out-of-floor
  groups (joints/contact/welds) — a data/identifiability limit, not a sampler bug.
- **Coverage can be restored partly by wider bands**; the arm comparison reports band width so "covered" is not
  confused with "sharp".
- **M3 prediction uses the Schneider spatial conditional with the orthogonally-calibrated posterior**; the
  orthogonal projection's main effect is on the θ posterior (de-biasing), evaluated at prediction via that
  posterior (documented approximation).

## 9. Checker — green / yellow / red

`check.py` reports each gate on the three-tier light (AGENTS.md Result Status Standard) and writes
`checker_report.json`. Overall is filled by `bash run_all.sh`. Exit non-zero only on RED.
