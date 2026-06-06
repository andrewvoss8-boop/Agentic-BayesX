# Known Failures, Limitations & Residual Risk — BLIND round (vs Codex independent truth)

Role: INFERENCE runner, BLIND. I consumed ONLY `runs/round3/codex_truth/dataset/` (observations.npz +
data_contract.md). I did NOT open the sealed truth, the generator code, or Codex's report. The master
scores my posterior against the sealed truth. The whole point of this round is to expose bias / non-
coverage when the data-generating model is INDEPENDENT of (and richer than) my inference model — so the
items below are the EXPECTED, designed outcomes, not surprises to be hidden.

## 0. HEADLINE FAILURE — the inference does NOT converge (multimodal / non-identifiable)
The hierarchical StatFEM NUTS fit and **every reparameterization I tried** FAIL the convergence gate:
- rank-split R-hat ≈ 1.5–2.8, bulk ESS ≈ 5, 0 divergences, with **fast leapfrog steps but no
  between-chain mixing** → genuine **multimodality** (confirmed identical at 150 and 800–1500 warmup, so it
  is NOT under-warming).
- `sigma_e` inflates to ≈ 0.6–0.85 in log-magnitude (a factor ≈ 1.8–2.3 misfit): the coarse model fits
  the data poorly and the noise term absorbs the residual.
- Variants, all failing: (a) full hierarchical + LEARN sigma_d → the **sigma_d↔sigma_e ridge** returns
  (sigma_d runs to ~2.7, overriding its prior; D19); (b) capped sigma_d, low-rank discrepancy → R-hat ~2.4;
  (c) + fixed sigma_build → R-hat ~1.5; (d) minimal (learn k_strut + sigma_e only) → R-hat ~1.5 with a
  **bimodal** k_strut (a degenerate "very-stiff-struts → modes leave the band → discrepancy explains
  everything" mode = the parameter↔discrepancy trade); (e) pure physics, no discrepancy → WORST (R-hat
  ~2.1, sigma_e ~0.84).

**Consequence:** per CLAUDE.md I do NOT claim "NUTS active." The reported marginal medians/intervals are
labeled **NOT-YET-CONVERGED**; the worst-case R-hat/ESS are quoted next to every interval. The marginals
are reported because they are stable ACROSS the failing configs (k_strut q50 ~1.4–2.5e7 N/m, f_dome ~83 Hz,
sigma_e ~0.6–0.8), giving the master something to score — but they should be read as "best available from a
multimodal sampler," not a trustworthy posterior.

**Why this is the right result:** the independent truth carries model-form error genuinely OUTSIDE my coarse
symmetric model's representational span. Recovery is therefore not a tautology — it breaks. This is exactly
what the blind protocol (and round 2's "plumbing" critique) was designed to expose.

## 1. Coarse, symmetric forward model (the dominant model-form error)
- 6 IDENTICAL axial struts (perfect 6-fold symmetry). The data shows split lateral/rocking pairs (x 50.9 vs
  y 54.3; rx 62.6 vs ry 67.0) → the as-built breaks symmetry; my model cannot represent the split.
- ONE strut stiffness `k_strut` sets ALL 6 mount modes. The data wants different stiffnesses per DOF
  (lateral peaks ~51 Hz want stiffer; axial ~62/77 want softer) → no single k_strut fits → intrinsic
  multimodality + large residual.
- Single axial dome resonator only (z DOF). Lateral/rotational dome dynamics are lumped as rigid base
  mass → unmodeled lateral/rocking resonances.
- The model has essentially NO predictive content above ~115 Hz; the data has real peaks at 120–460 Hz.
  The inference band is restricted to 40–115 Hz (the first mode cluster, which also carries the QOI energy
  at 66/96 Hz); everything above is a documented gap.

## 2. Frequency-only discrepancy cannot represent the truth's error
The discrepancy is a per-DOF smooth GP over log-frequency (HSGP). It can correct gentle frequency trends
but NOT (i) the symmetry-breaking mode SPLITS (a spatial/asymmetry error) nor (ii) the sharp unmodeled
higher peaks. When given freedom (learn sigma_d), it instead trades off against sigma_e/sigma_build and
de-identifies the physics (the ridge). This motivates a STRUCTURE-based (property/per-strut) discrepancy
(decisions_log D12/Stage-3) — not built/validated for this blind run.

## 3. Magnitude-only likelihood; damping fixed
I fit log|apparent mass| (magnitude), not the complex (real+imag) data. Phase/loss information is unused,
so structural damping `eta` is fixed (0.04), not inferred. This loses information that could partly help
identify resonances and is a known limitation.

## 4. Rigid-body mass read from the low-f asymptote
`M_base6` is set from the measured low-frequency apparent-mass asymptote (build-averaged). This is standard
apparent-mass practice (the low-f asymptote IS the rigid-body mass), not peeking at hidden structure, but
it means the rigid-body level is calibrated-to-data rather than predicted; only the DYNAMICS are inferred.

## 5. QOI mapping carries its own ~2× model-form bias
My netCG QOI uses the driving-point accelerance: PSD_acg = PSD_F / (|M_zz|² g0²). Measured on the PUBLISHED
data (apparent mass + force + response, all observable), this mapping gives ≈ 2× the published 3·GRMS — the
truth's coupled force-transmission to the load CG attenuates more than a single driving-point accelerance.
I report this bias rather than tuning a fudge factor to the published response. Combined with the wide,
multimodal posterior, the QOI bands are wide and biased high.

## 6. Held-out coverage is "wide-but-covering," and under-covers held-out bands
New-build 95% coverage looks ~0.92–0.97 BUT with log-width ≈ 2.5 (~12× multiplicative bands) — driven by
the inflated sigma_e, not by a good fit. The held-out FREQUENCY band coverage is ~0.6–0.84 (under-covers).
Read coverage WITH sharpness: this is NOT calibrated success.

## 7. Companions are bounded/diagnostic, not gate-grade
without-d and starve-the-data fits use reduced samples and capped tree depth because the no-discrepancy
geometry is pathologically stiff (it hits max tree depth every draw — itself evidence the discrepancy is
needed). Their numbers are indicative comparisons, not converged posteriors.

## What would fix it (recommendation to the master / next stage)
1. STRUCTURE-based discrepancy (per-strut / property kernel) so the symmetry-breaking error is representable
   (Stage-3, D12) → should restore identifiability (sigma_d vs sigma_e separate) and reduce sigma_e.
2. An ASYMMETRIC / per-DOF-stiffness forward model (independent lateral/axial/rocking stiffnesses) so one
   k_strut no longer has to fit all DOF.
3. Higher-fidelity model above 115 Hz (panel/strut bending) to use the full band.
4. Complex (magnitude+phase) likelihood to identify damping.
5. Possibly modular/"cut" updating so a flexible discrepancy informs prediction without de-identifying the
   physics calibration.

---

# STAGE-3 ADDENDUM (structure-aware fix) — 2026-06-04

The three coupled fixes were built and tested BLIND on the re-published independent truth. Honest mixed
result; the with-discrepancy model still FAILS the convergence gate, for a NEW and informative reason.

## S0. HEADLINE — fix #1 converges; fix #2 (same-space discrepancy) does NOT
- **Per-strut ASYMMETRIC physics ALONE (without discrepancy) CONVERGES**: rank-split R-hat **1.009**, bulk
  ESS **487**, tail ESS 460, 0 divergences; k_pop 1.685e7 [1.678e7,1.693e7] near nominal 1.816e7. This is a
  real improvement over the prior blind run (which could not converge at all) — the asymmetric model removes
  the "one equal-strut k cannot fit 6 DOF" multimodality.
- **Adding the structure/property-based per-strut discrepancy BREAKS convergence**: R-hat **2.85**, bulk ESS
  **4.7**, σ_d runs to **1.33** (≫ its 0.20 prior), k_pop smears to [6.4e6,16.8e6]. 0 divergences, no
  mixing → multimodal. Per CLAUDE.md I do NOT claim "NUTS active" for the with-d model.
- **Why:** a per-strut discrepancy lives in the SAME parameter space as the per-strut stiffness → confounded
  by construction (both perturb the struts). It TRADES a frequency-only ridge for a parameter↔discrepancy
  ridge. The zero-mean constraint fixes the mean but not the 5-D shape confound. **Lesson:** a structure-
  based discrepancy must be ORTHOGONAL to the calibration parameters (e.g. output modes the physics lacks),
  not on the very parameters being calibrated.

## S1. Dominant residual error = MISSING HIGHER MODES (not the azimuthal split)
The data has more resonances per DOF (z: 62/77/120; lateral: 51/87/137) than the coarse model (6 mount
modes + 1 axial dome bounce) can produce in 35–160 Hz. Pre-run probe: best achievable coarse-model fit has
rms fractional residual ~1.9 (z-DOF 3.7) → an **irreducible σ_e floor**. So σ_e stays inflated (with-d 0.69,
without-d 0.93) regardless of the discrepancy; the structure-based discrepancy fixes the error it is
structured for (splits) but not this one. Real fix = Stage-4 higher-fidelity FEM (panel + strut/shell modes).

## S2. netCG bias improved by the FBS contract, but residual model-form bias remains
- Canonical FBS netCG (M_L/(M_S+M_L)·F/m_load) removed the prior ~2× drive-point definitional drift:
  bias 4.86× → **1.71×** (with-d, wide) / **3.10×** (without-d, converged). f→0 rigid limit exact (0.282).
- The converged without-d QOI is **biased 3.1× high, 0% coverage** — genuine model-form OVER-prediction (the
  coarse model misses the higher-mode antiresonances that attenuate real transmission). Reported, not tuned.
- f_dome biased low (72–76 Hz vs 93.5) — single axial dome resonator pulled to a z mount peak.

## S3. Held-out coverage improved + bands sharpened, band still under-covers
New-build coverage 0.911 with log-width 2.16 (~8.7× span) — far sharper than the prior 12–18× bands; held-out
FREQUENCY band 95–115 Hz coverage 0.715 (<0.95, under-covers). Read coverage WITH width.

## S4. Companions confirm the ridge is STRUCTURAL, not data-deluge
Starve-data (1 build, 40–100 Hz, with-d): still R-hat 2.85, σ_d 1.39 → removing data does not fix the ridge.
n_eff(k_pop) with-d ≈ 0.6 (multimodal posterior wider than prior = illusory, not fictitious-tight).

## What would fix it (Stage 4+)
1. Higher-fidelity FEM: flexible isogrid panel + strut/shell bending → the missing higher modes (the real
   floor on σ_e and netCG bias).
2. Discrepancy ORTHOGONAL to the calibration params (output-mode / participation space), or modular/cut
   updating, so it informs prediction without de-identifying k_pop.
3. Inferred damping via the complex likelihood (η currently fixed).
