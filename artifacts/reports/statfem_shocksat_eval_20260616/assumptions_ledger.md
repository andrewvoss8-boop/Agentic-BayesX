# assumptions_ledger.md — StatFEM ShockSat held-out-QOI evaluation

Numerical values, units, rationale, source, sensitivity priority. Distinguishes parameter uncertainty,
observation noise, model discrepancy, and QOI uncertainty.

## A0 — Testbed = plain ShockSat ONLY (NOT coupled tray)
9-group reduced ShockSat FEM from `shocksat_fem_modal_twin_20260609`: `K_red(θ)=A_fix+Σ_g θ_g A_g`, 74 nominal
elastic modes (54.6–321.7 Hz), mass = I in modal coords, mode shapes at 76 accel nodes / 228 translational DOFs
(`obs_V`, 228×74). Source: COPIED to `data/reduced_blocks.npz`. The coupled ShockSat×tray model is FORBIDDEN
(Andrew, task §3). **Sensitivity priority: N/A (hard constraint, checker-enforced).**

## A1 — Forward observable: modal-superposition accelerance FRF
`H_s(ω) = -ω² Σ_k Φ_obs[s,k]·Φ_obs[d,k] / (ω_k² - ω² + 2 i ζ_k ω_k ω)` per response sensor DOF s, point-force
drive at DOF d. Φ_obs = obs_V @ Q(θ); ω_k = √λ_k(θ). Units: synthetic accelerance (in/s²)/lbf; QOI is reported
as a coverage/ratio, not an absolute certified load. **Source: standard modal-superposition (mass-normalized).
Sensitivity priority: LOW (definitional).**

## A2 — Drive DOF d
Documented single point-force drive at the +Z (vertical / long-axis) DOF of a near-base corner sensor node
(stated explicitly in `quantity_contracts.md` and `out/config.json`). Chosen to excite the box/plate/cross-beam
band. **Sensitivity priority: MEDIUM (drive choice changes which modes are excited; covered by band sensitivity).**

## A3 — Modal damping ζ (DISCREPANCY/uncertainty input)
Nominal ζ = 0.02 (2% critical), all modes. Rationale: installed-configuration representative; the bare free-free
.ash test damping (median 0.32%, range 0.058–1.052%) is artificially light. 2% keeps resonance half-power
bandwidth ≈ 2ζf resolvable on a log grid. **Source: D5; engineering value, not measured-in-config. Sensitivity
priority: HIGH — sensitivity arm runs ζ=0.01 and ζ=measured-mode values.**

## A4 — Frequency grid (DISCRETIZATION)
Log-spaced, band 45–260 Hz, n_freq = 160 (≈0.31% spacing → ≈0.3 Hz at 100 Hz). Covers the calibration-mode band
(<222 Hz) where 4/9 groups are identifiable. **Source: D6. Sensitivity priority: MEDIUM — refinement n vs 2n,
modal truncation 74 vs fewer, and a direct full-order spot-frequency solve (discretization gate).**

## A5 — Parameter uncertainty: θ prior (inference)
θ_g ~ LogNormal(0, 0.25), median 1, untruncated 95% range [0.613, 1.632] — same as the modal twin (honest
"joints not well known" width). Inference starts at θ = 1 (nominal). **Source: modal twin packet §0. Sensitivity
priority: LOW (modal twin showed verdict robust to prior width 0.15–0.40).**

## A6 — Parametric bias (truth-side INJECTED, layer 1) — the 5 combos
θ_truth offsets (dimensionless multipliers): (1) top_box 1.15, bottom_box 0.90; (2) joints 1.20, contact 1.15;
(3) top_box 1.15, joints 1.20, plates 0.88; (4) cross_beam 1.20, joints 0.82; (5) broad-small ±~10% across
bottom_box 1.08, top_box 0.92, plates 1.10, cross_beam 0.90, joints 1.10. **Source: task §6 / D7. Sensitivity
priority: HIGH — bias magnitude is an explicit sensitivity arm.**

## A7 — Model-form discrepancy (truth-side INJECTED, layer 2): Schneider field
Complex multiplicative field `d(ω,s) = exp(w + iφ)` on the truth FRFs, where (w, φ) are zero-mean Gaussian
correlated over log-frequency (squared-exponential, length ℓ_f = 0.30 in log-Hz) AND sensor distance
(exponential, length ℓ_z = 12 in). Log-amplitude std grows with frequency from σ_lo = 0.03 to σ_hi = 0.12
(≈3%→12% multiplicative), phase std = 0.5×amplitude std. NOT representable by any θ scaling. Fixed std profile
across combos; per-combo random seed. **Source: Schneider 2022 correlated-complex discrepancy
(`papers_statfem_studies_20260612/code/forward.py`); D4. Sensitivity priority: HIGH — this is an arm AND the
injected-error magnitude is swept.** σ_hi ≈ 0.12 is chosen comparable to the ShockSat real model-form floor
σ_f ≈ 4.6% but larger so the malady can appear.

## A8 — Observation noise (measurement)
iid complex log-noise σ_meas = 0.05 (5%) on each observed-sensor FRF point (amplitude and phase). **Source:
matches the confidently_wrong toy / modal-test FRF noise scale. Sensitivity priority: LOW.**

## A9 — Orthogonal projection (M3)
Discrepancy covariance projected onto the orthogonal complement of the θ→(log|H_obs|) sensitivity span,
`P_⊥ = I − J(JᵀJ)⁻¹Jᵀ`, J evaluated at NOMINAL θ=1 (linearization, documented). Prevents the discrepancy from
absorbing variation θ could explain (Brynjarsdottir–O'Hagan / Plumlee orthogonal-GP idea). **Source: D4/D9;
papers_statfem Study H "H-orth". Sensitivity priority: this IS an arm.**

## A10 — Sensor split (observed vs held-out)
Default: observe 6 accel translational DOFs (documented node/axis list in `out/config.json`), hold out the rest
of the 132 measured DOFs; predict QOIs at a documented held-out subset near and far from the observed set.
**Source: task §7. Sensitivity priority: HIGH — held-out-channel-choice sensitivity arm.**

## A11 — QOI definitions (quantity contract — see quantity_contracts.md)
(a) Peak |H_s| over the band 45–260 Hz (linear accelerance magnitude). (b) Band-GRMS-like metric:
`√(∫ |H_s(f)|² S_FF df)` over the band with flat input PSD S_FF = 1 (synthetic) — a response-energy proxy.
**Sensitivity priority: MEDIUM (band edges swept).**

## A12 — Data counts / variability
ONE synthetic realization per (combo, arm) — but 5 combos = 5 distinct truths (distinct θ-bias AND distinct
Schneider field realization), reported as a distribution. NO flight-to-flight / build-to-build / test-to-test
variability modeled (one nominal article). Discrepancy field, σ_meas, and θ prior are the only stochastic inputs.
**Sensitivity priority: documented LIMIT (single realization per combo).**

## A13 — Inferred vs fixed
INFERRED (per arm): θ_g (9), σ_d (M1/M2/M3 only; M0 fixes σ_d=0). FIXED (not inferred): mass matrix, geometry,
mesh, reduced basis, drive DOF, ζ, frequency grid, discrepancy correlation lengths ℓ_f/ℓ_z (M2/M3), σ_meas,
orthogonal projector P_⊥ (M3). NOT-inferred acknowledged latent: the realized discrepancy field on observed
channels (M2/M3 learn its scale + krige it to held-out, but the hyper-lengths are fixed).

## A14 — Uncertainty taxonomy (kept distinct in reporting)
Parameter uncertainty (θ posterior) ≠ observation noise (σ_meas) ≠ model discrepancy (σ_d / Schneider field) ≠
QOI uncertainty (predictive band on peak/GRMS). Aleatory build/test variability = ABSENT (A12). Forcing
uncertainty = absent (flat synthetic input PSD).
