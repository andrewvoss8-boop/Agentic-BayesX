# Review Packet — ShockSat FULL-SPECTRUM FRF study (2026-07-14/15)

> **⚠ POST-REVIEW STATUS (2026-07-16): the original package is RED**, per the adversarial GPT-5.6 review
> (`shocksat_fullspec_review_gpt56_20260716/`) — the lead verified and accepts the findings: NaN S1/S2
> verdict statistics + an invalid F=R row (collector/checker defect), a LEAKY arm-C exact aggregate
> (withdrawn), an over-claimed identifiability statement, and S3/S4 mis-labeled (CANNOT-VERIFY, not
> "not-met"). **Corrected S1/S2/F numbers live in the isolated repair
> `shocksat_full_spectrum_frf_repair_20260716/`** (S1 not met +0.0497<0.05; S2 not met −0.0017). The full
> correction is the dated addendum at the top of `findings.md`; the text below is the original audit record.

**Status: RED post-review (see above); the SHA-locked checker's own replay remains YELLOW but its G09 gate
was shown too weak (accepted NaN/null/F=R).** One-command replay: `bash run_all.sh`. Card: pasted runner
card (Fable, dispatched by Andrew 2026-07-14). Workspace: `artifacts/reports/shocksat_full_spectrum_frf_20260714/`.



## 0. One-paragraph summary
Checker OVERALL **YELLOW** (11 GREEN / 1 YELLOW / 0 RED; the YELLOW is the honestly-reported arm-B/C NUTS
non-convergence). The first ShockSat study to TRAIN on per-channel FRF amplitude. Five raw modal-hammer
drives were re-distilled wide-band and validated **bit-identically** against the existing caches WITH live
force (closing the prior run's Gate W). The FEM twin is credible only to ~640 Hz (dense local-mode forest;
1250 Hz solve infeasible on a 16 GB CPU), so FRF scoring is capped at 500 Hz — the 500–1000 Hz band the DATA
supports is FEM/compute-limited. **All five pre-registered criteria resolve falsified/not-met:** no lever
cleanly beats the baseline on sub-200 (S1); the amplitude-compass agent ties equal-budget random on the
trusted exact bases (S2 — a screening +0.0138 lead OVERTURNED by the exact-at-θ_MAP re-evaluation, the D22
reduced-basis trap, confirming H2 impotence); amplitude-inclusive selection does not track held-out skill
(S5, Spearman −0.3); the net-CG QOI could not be validly reassessed (S3/S4, reimplementation caveat). What
amplitude training DID do: it improves the 200–500 Hz band (arm B +0.11..+0.16) but not sub-200 — it fixes
mid-band amplitude *levels*, not the sub-200 *shapes*. The inherited FEM + statFEM twin stands unchanged;
the remaining error is not reachable by any lever we own, now shown WITH amplitude training and the full
spectrum. Full per-H detail in `findings.md`; numbers in `out/verdicts.json`, `out/exact_freeze_scores.json`.

## 1. Method summary (first-pass, plain English)

### The question and arms
Can amplitude-TRAINED Bayesian updating (arm B), amplitude-trained shape inference (arm C), or an
amplitude-compass remodeling loop (arm D) beat the resolution-consistent baseline (A1) on held-out
per-channel FRF amplitude, per band, and improve the net-CG force QOIs? Each arm challenges one standing
explanation H1–H5 (see `question_framing.md`). A falsified pre-registered claim is a valid outcome.

### Model form
- **Structure:** the inherited ShockSat FEM (67,683 grids, ~406k DOF), reduced to a modal basis
  `K(θ) = A_fix + Σ_g θ_g A_g`, mass = I (mass-normalized). θ = 9 group stiffness scalings (al_welds,
  angle_brackets, bottom_box, contact, cross_beam, joints, plates, steel_welds, top_box).
- **Wide basis (this study):** full-order eigensolution at θ=1 to the credible ceiling. The k=560 shift-
  invert converged 215 real modes to 667 Hz (cross-validated to 639 Hz by an independent interior-shift
  solve); 338 unconverged clamp modes were removed (D11). **The FEM twin is credible to ~640 Hz** — below
  the >1 kHz data ceiling. Scored band capped at 500 Hz (card's 1.25× modal-truncation rule).
- **FRF forward:** modal-superposition accelerance H (g/lbf), free-free, processed through the EXACT
  measurement-window operator 𝒲 (reused verbatim from the resolution run: 122,880-sample frame @ 250 kHz,
  exponential window end 0.05, adds apparent damping ζ_w(f)=1/(2πfτ)). Damping = measured survey per-mode ζ
  (percent→ratio, interpolated), band-median above the survey top; NO free damping fitting.

### Likelihood and inference (per arm)
- **Metric:** P1′ = per-channel Pearson correlation of log10|H| after a TRAIN-side FDAC frequency-alignment
  warp (one scalar ρ per fold) + coherence masking (median in-band coh ≥ 0.6). ONE global gain per fold; NO
  per-channel/per-mode amplitude least-squares in any selection score (checker-grepped). Bands: sub-200 /
  200–500 / 500–ceiling Hz. Splits: leave-one-drive-out over the 4 dev drives; +XY the SHA-frozen vault
  (read once, post-freeze; honestly the 3rd program read).
- **Arm B (amplitude-trained θ):** NUTS (NumPyro, 4 chains, float64) over θ + one global gain/train-drive +
  a statFEM-style frequency-correlated output-error term (σ_e, ℓ inferred; θ-only control drops it). The
  in-NUTS forward is an EXACT eigensolve on a Galerkin sub-basis (θ=1 modes ≤450 Hz; validated to 0.028 dex
  vs the full forward — the first-order surrogate was rejected at 0.51 dex, D6/D10). Likelihood band 45–400
  Hz (whole-data over channels+bins, NOT peak features). **The posterior is multimodal / non-converged
  (R-hat 29–360, ESS≈2)** — reported YELLOW; the mechanism (rugged resonance-alignment likelihood, NOT
  under-identification — FIM 9/9 combinations clear the prior) is proven sampler-independently in
  `identifiability.json`. Arm B is therefore SCORED at a deterministic multi-start amplitude-MAP (best mode,
  train-only, leakage-safe), clearly labeled (D12).
- **Arm C (amplitude-trained shape field):** Beck-style shape perturbations (NUTS) over the matched modes,
  θ fixed at MAP, likelihood = survey-frequency + survey-shape MAC + TRAIN-amplitude terms.
- **Arm D (remodeling loop):** ≥3 rounds; TRAIN-side per-channel-amplitude residual diagnosis (the
  "amplitude compass") → model edits from the validated action families → own-space eigensolve → dev score;
  equal-budget seeded random control; ≤80 scored queries each.
- **Arm E (selection re-test):** amplitude-inclusive Laplace evidence (prior-width sweep) vs held-out rank.
- **Arm F:** best combination of the above (or A1 if nothing beats it).

### Data count
5 measured drives (hammer references), ~6 hits each, ~111 accel channels; wide caches ~470 bins (45–3000 Hz
kept, scored ≤500). Single article / single test campaign — NO build-to-build or test-to-test variability is
modeled (stated limitation). Inferred: θ (9), gain/drive, σ_e, ℓ, σ_n (arm B); shape field (arm C). Fixed:
window constants, ζ table, mode pairing (frozen Hungarian), channel mask. Not inferred: true mode shapes
above the survey, damping above 258 Hz.

## 2. Arms × bands table (the centerpiece — EXACT basis; `out/arms_bands_table.json`, fig_bands_table.png)
| arm | sub-200 (exact) | 200–500 (exact) | 500–ceiling | θ=1 screening sub-200 |
|---|---|---|---|---|
| A0 (historical) | 0.112 | 0.050 | not certified (FEM ≤640 Hz) | 0.131 |
| A1 (baseline) | 0.114 | 0.033 | not certified | 0.145 |
| B (amplitude-θ) | 0.154 | **0.197** | not certified | 0.142 |
| C (shape field) | 0.157 | 0.022 | not certified | **0.189** |
| D (agent) | 0.163 | 0.188 | not certified | 0.179 |
| R (random) | **0.165** | 0.188 | not certified | 0.166 |
The θ=1 SCREENING scores were partly inflated (D22 reduced-basis trap: θ_MAP far from 1); the EXACT-at-θ_MAP
re-evaluation (self-consistency 0.0000%) is the trusted basis and **reordered the leaders** — screening
crowned C (0.189), exact crowns D≈R (0.163–0.165). This reordering is the study's central methodological
result and is why S2 flips (H2). Vault (+XY, single post-freeze read): A0 0.443 / A1 0.451 / B 0.429 /
D 0.438 / R 0.455 — the uniform +0.29 location effect, no candidate win, random ≥ agent.

## 3. Per-H verdicts — see `findings.md` (per-H answers with numbers) and `out/verdicts.json`
All S1–S5 YELLOW (falsified/not-met). H1 wall dented not cleared; H2 impotence CONFIRMED (agent ties random
on exact/vault); H3 window is the lever not damping; H4 cluster measured but QOI not validly reassessable;
H5 selection ≠ held-out (Spearman −0.3). Sampler status: arm B/C multimodal non-converged (YELLOW), scored
at labeled MAPs; `identifiability.json` proves multimodality (not under-identification).

## 4. Net-CG QOI (`out/netcg_results.json`, fig_netcg_bands.png) — reimplementation caveat
The wide-package QOI band reimplementation does NOT reproduce the delivered twin's calibrated bands
(8.2×/3.66×/5.12× vs 1.51×/2.30×/2.53×) — a marginal-calibration difference in the reimplemented statFEM
F(k), NOT a real widening by any arm. **S3/S4 cannot be validly assessed; the delivered net-CG twin stands
unchanged and no arm is shown to improve or degrade it.** Overconfidence audit partially works (shear_y
widens 1.23× when hiding the top-3 modes; shear_x/normal ~1.0, flagged).

## 5. Sensitivity / identifiability
- **Basis sensitivity (the decision-driving one):** θ=1 screening vs exact-at-θ_MAP reordered the leaders and
  flipped S2 — reported in full (§2). The exact basis is the trusted one.
- **Identifiability (arm B):** FIM eigenvalues 1641–3.6e6 (all 9 θ combinations ≫ prior precision 16) at the
  realized 0.73 dex discrepancy floor → the amplitude posterior is multimodal, not under-identified;
  strain-energy peaks bottom_box 0.99 / plates 0.98 / top_box 0.89 match the Y-box residual compass.
- **Extended-band tiers (H4):** 11 cross-drive measured peaks; tier table updated (ledger A5b).

## 6. Figures (`figures/`; scripts in `code/make_figs.py`; `out/tufte_lint.txt`, `out/fig_qa.json`)
fig_bands_table (arms×bands), fig_identifiability (FIM vs prior), fig_qoi_sensors (net-CG-shear sensor
weights), fig_loop_trajectory (agent vs random), fig_selection_scatter (evidence vs held-out, H5),
fig_netcg_bands (QOI vs delivered), fig_graphical_model (arm-B run-specific likelihood). All 7 QA-passed;
tufte lint advisory-only (bar/scatter comparisons, not FRF-vs-frequency line plots — documented).

## 7. Honest limitations carried
- FEM twin credible ≤~640 Hz (compute-bound); 500–1000 Hz FRF scoring is FEM-limited, not data-limited.
- Arm B posterior multimodal/non-converged (YELLOW); scored at a labeled deterministic MAP.
- +XY vault is the program's 3rd read (directional confirmation only, never a win).
- No sampler was pushed to GPU/TMCMC (compute protocol: method not yet validated; multimodal twin).
