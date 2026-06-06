# Blind Round-3 Independent Review + Score — StatFEM (Opus 4.8 inference vs Codex independent truth)

**Reviewer role:** independent grader. I am not the truth-author (Codex), the inference runner (opus48),
or the master. I read everything including the sealed truth (I am the scorer). I wrote ONLY to
`artifacts/reports/blind_round3_review_20260604/`; I did not modify `runs/round3/opus48/` or
`runs/round3/codex_truth/`.

**Date:** 2026-06-04. **Inference run:** [blind_results.json](../../../runs/round3/opus48/report/blind_results.json)
(runtime 375.5 s, NUTS 4 chains × (1000+1000)). **Sealed truth:**
[true_parameters.json](../../../runs/round3/codex_truth/sealed_truth/true_parameters.json),
[scoring_key.npz](../../../runs/round3/codex_truth/sealed_truth/scoring_key.npz).

---

## TL;DR verdict

| Question | Verdict |
|---|---|
| 1. Score vs sealed truth | **netCG biased 4.86× high; 0% coverage at 95%, 61% at 99%. f_dome biased ~11 Hz LOW, truth OUTSIDE its 95% CI. Held-out coverage "wide-but-covering" (0.94) only via inflated noise; held-out band under-covers (0.89 < 0.95).** All independently reproduced vs clean truth. |
| 2. Convergence over ALL latents | **FAILS, genuinely.** I recomputed rank-split R-hat = **2.41** (z_b), min bulk ESS ≈ **5** — exactly matching the reported numbers. The σ_d↔σ_e ridge is suppressed only by CAPPING σ_d=0.3; multimodality persists. Inference correctly does NOT claim "NUTS active." |
| 3. Blindness + integrity | **PASS.** No reference to any sealed file in inference code; reads only `dataset/observations.npz`. Figures authentic. **Strongest evidence: results are BIASED and NON-COVERING — the opposite of a leakage signature.** |
| 4. Headline | **Honest model-form BIAS / UNDER-COVERAGE — the informative (not the strong) result.** The frequency-only discrepancy cannot represent the truth's real symmetry-breaking mode splits + higher modes. This is the experiment working as designed and it MOTIVATES the Stage-3 structure/property-based discrepancy. No overclaim. |

Bottom line: this is an **honest, well-labeled negative result**, not a fabricated success. The inference's
self-assessment is corroborated by my independent scoring against the sealed truth on every point checked.

---

## 1. Scoring against the sealed truth

### 1a. Parameter bias / coverage

The inference's internal physical parameters are NOT 1:1 comparable to the truth's, because the two
forward models parameterize the structure differently (the inference uses a single equal-strut hexapod +
one axial dome resonator; the truth uses 6 per-strut stiffnesses + per-DOF source/load modal banks). I
therefore score the **physically interpretable** quantities and flag where a direct numeric compare is
not meaningful.

| Quantity | Inference posterior (q50, 95% CI) | Truth (sealed) | Inside CI? | Read |
|---|---|---|---|---|
| `f_dome` (axial dome bounce, Hz) | 83.2, [81.9, 85.1] | z **source** mode ≈ **92.1–97.5 Hz** across 8 builds (nominal 93.5) | **NO** | Biased ~9–14 Hz LOW; truth above the 95% CI. Genuine bias + non-coverage. |
| `k_strut` (N/m) | 1.42e7, [1.08e7, 3.29e7] | per-strut axial k ≈ **8.05e6–8.46e6** (truth), but **different parameterization** | n/a (not comparable) | Inference is also biased LOW vs its OWN nominal (1.82e7). The cross-model number is not a fair bias score; the mode-frequency comparison (f_dome, netCG) is the fair one. |
| `σ_e` (log-mag) | 0.62, [0.56, 0.70] | true sensor frac-noise median **0.46%** (≈0.005 log) | — | **Inflated ~120×** above the true sensor scale. Confirms model-form error leaking into the noise term (not real sensor noise). |
| `σ_build` | 0.20, [0.02, 0.40] | per-build ~5%/3 log scatter on fundamentals | (wide) | Non-identified (bimodal); traded against σ_e. |

Source: truth modes from
[true_parameters.json](../../../runs/round3/codex_truth/sealed_truth/true_parameters.json) (`builds[b].dofs.z`),
sensor noise from `noise_summary.apparent_mass_fraction_noise_median = 0.00457`. Inference values from
[blind_results.json](../../../runs/round3/opus48/report/blind_results.json) `learned_with_d`.

### 1b. QOI — netCG 3·GRMS (independently recomputed)

Truth clean netCG (88 build×flight values, [scoring_key.npz](../../../runs/round3/codex_truth/sealed_truth/scoring_key.npz)
`clean_netcg_3grms_g`): **min 0.466, max 0.935, mean 0.650 g**. (Published observed mean 0.651 — sensor
noise negligible, so clean ≈ observed.)

| netCG 3·GRMS [g] | Inference predicted (full unc.) | Truth | Coverage of truth |
|---|---|---|---|
| q50 / mean | **3.16** | 0.650 | **bias ratio 4.86×** |
| 95% CI | [1.22, 6.08] | 0.466–0.935 | **0.000** (entire truth below the lower bound) |
| 99% CI | [0.60, 6.38] | 0.466–0.935 | **0.614** |

My recompute (`sources/scoring_recompute.txt`): 95% coverage **0.000**, 99% coverage **0.614**, ratio
**4.86×**. The inference reported "~5× high … published low values fall below my 99% CI → honest
over-prediction/non-coverage." **Confirmed and accurate.**

Decomposition (honestly disclosed by the inference, [blind_known_failures.md §5](../../../runs/round3/opus48/report/blind_known_failures.md)):
~2× of the bias is a **QOI-transfer definitional mismatch** — the inference uses driving-point accelerance
`PSD_acg = PSD_F/(|M_zz|² g0²)`, whereas the truth uses impedance-sharing transmission
`F_iface = M_load/(M_source+M_load)·F` (sealed
[hidden_decisions_log.md](../../../runs/round3/codex_truth/sealed_truth/hidden_decisions_log.md);
truth M_source≈430, M_load=170 → transmission ≈0.28). The remaining ~2.4× is the inflated/multimodal
posterior. The inference reported this rather than tuning a fudge factor — good practice.

**Spec/narrow-band verdict:** inference reports overall scalar margin 4.52× yet 99%-hi exceeds the spec on
42.75% of the band. The "large overall margin can hide narrow-band exceedance" headline is structurally
demonstrated, but note the bands are inflated by the failed posterior, so the *quantitative* exceedance
fraction is not trustworthy (the inference says as much).

### 1c. Held-out calibration (the decisive test) — recomputed vs CLEAN truth

I reconstructed the inference's posterior-predictive band (`bm.forward_logmag` + saved posterior in
[blind_posterior.npz](../../../runs/round3/opus48/report/blind_posterior.npz)) and scored coverage against
the **clean truth apparent mass** (not the noisy observations the inference used), interpolated onto the
62-point grid. Script: `sources/heldout_truth_cov.py`, output `sources/heldout_recompute.txt`.

| Held-out target | Reported coverage (vs obs) | **My coverage vs CLEAN truth** | mean log-width | Read |
|---|---|---|---|---|
| New builds 6,7 (full band) | 0.940 | **0.938** | 2.91 (≈ ×18 multiplicative span) | matches; **wide-but-covering — NOT success** |
| Frequency band 82–95 Hz (train builds) | 0.877 | **0.894** | 2.94 | matches; **under-covers (target 0.95)** despite inflated noise |

The reported coverage **matches actual coverage vs the sealed truth** (sensor noise is ~0.5%, far smaller
than the ~×18 bands). Coverage is "real" but bought entirely with an inflated σ_e — exactly the
"wide-but-covering is not success" trap, which the inference labels correctly. The held-out **band**
genuinely under-covers (0.89 < 0.95), the honest signature of model-form error in a region the coarse
symmetric model cannot represent.

Per-DOF posterior-median physics residual vs clean truth in 82–95 Hz (build 6): axial **z = +2.23 log
(≈9× too high)**; lateral/rocking DOFs −0.2 to −0.65 log. The axial over-prediction is the same model-form
error that drives the netCG over-prediction.

---

## 2. Convergence over ALL latents (independently recomputed)

I reshaped the 4000 saved draws chain-major to (4 chains, 1000) and recomputed rank-split R-hat / bulk /
tail ESS with ArviZ 0.17.1 (`sources/scoring_recompute.txt`). **My numbers reproduce the report exactly:**

| latent | R-hat (mine) | bulk ESS | tail ESS | gate |
|---|---|---|---|---|
| k_strut_pop | 1.873 | 5.7 | 42.4 | ❌ |
| f_dome | 1.582 | 6.8 | 31.8 | ❌ |
| sigma_build | 1.754 | 6.1 | 121.1 | ❌ |
| sigma_e | 2.068 | 5.3 | 30.0 | ❌ |
| z_b (worst element) | **2.411** | 4.9 | 29.2 | ❌ |
| beta (discrepancy, worst) | 1.83 | — | — | ❌ |
| sigma_d | n/a (CAPPED const 0.3) | — | — | fixed, not sampled |
| divergences | 0 / 4000 (0.0%) | — | — | ✅ |
| chains / param. | 4 / non-centered (z_b) | — | — | ✅ |

**Gate FAILS** (R-hat 2.41 ≫ 1.01; ESS ≈ 5 ≪ 400). This is genuine **multimodality**, not under-warming
(the inference confirms identical behavior at 150 vs 800–1500 warmup, 0 divergences with fast leapfrog =
chains stuck in separate modes). The inference correctly does **not** claim "NUTS active" and labels every
marginal "NOT-YET-CONVERGED."

**Did the σ_d↔σ_e ridge return?** In the MAIN fit it is *suppressed by capping* σ_d = 0.3
([blind_results.json](../../../runs/round3/opus48/report/blind_results.json) `sigma_d.sd = 1.1e-16`). The
inference documents that the *flexible* variant (learn σ_d) re-exhibits the ridge (σ_d→~2.7), which is why
it capped it. So the ridge is real and only masked; the deeper non-identifiability (parameter↔discrepancy,
one k_strut cannot fit all 6 DOF) remains and is what breaks convergence. The companion variants
(without-d, starve) were `skipped` in this run (gated behind `R3BLIND_COMPANIONS=1`); their numbers in the
packet are from prior characterization, honestly flagged as "indicative, not gate-grade."

---

## 3. Blindness + integrity verdict — PASS

- **No forbidden reads in code.** `grep -rn` over `runs/round3/opus48/code/` and report scripts for
  `sealed_truth|scoring_key|true_parameters|model_form_imperfection|hidden_decisions|codex_truth/code|codex_truth/report|generate_truth`
  returns **nothing**. The only `codex_truth` reference is
  [blind_model.py:38](../../../runs/round3/opus48/code/blind_model.py#L38):
  `DATASET = HERE.parent / "codex_truth" / "dataset" / "observations.npz"` — resolves to the **published
  dataset only**. (`sources/blindness_grep.txt`.)
- **Self-attestation verified, not just asserted.** Manifest declares "sealed truth NOT opened"; code and
  data-flow corroborate it.
- **Strongest tell points AWAY from leakage.** A leak would produce near-zero bias with tight intervals.
  Instead the inference is **4.86× biased on netCG, 0% at 95%, f_dome 11 Hz off and outside its CI,
  R-hat 2.41**. No quantity outside the model's span is suspiciously well-recovered. This is the
  signature of a genuinely blind, under-specified model — not leakage.
- **Figures authentic.** `figures/blind_*.png` are real PNGs (2240×1260 etc., 46–410 kB) timestamped at
  the run; not copied reference assets. (`sources/figure_check.txt`.)
- **No fabricated metrics / no overclaim.** Every headline number I spot-checked (R-hat, ESS, netCG bias,
  held-out coverage) reproduces from the saved artifacts. The packet leads with the failure, not a spun
  success.
- **Model-form story is real, not invented.** The inference attributes failure to symmetry-breaking mode
  splits the symmetric model can't represent. The sealed truth confirms genuine splits, e.g. build 0:
  x = 64.7 vs y = 75.5 Hz, rx = 80.0 vs ry = 85.6 Hz (`true_parameters.json` load modes). Diagnosis is
  correct.

Minor notes (not integrity issues): (i) the cross-model `k_strut` numeric comparison is not a clean bias
score and should not be read as one; (ii) companion studies were skipped in this run, so their packet
numbers are inherited — acceptable because honestly labeled.

---

## 4. Headline answer

**Against genuinely independent truth, the inference shows the EXPECTED model-form BIAS / UNDER-COVERAGE —
the honest StatFEM limitation — and reports it honestly. It did NOT achieve a tight, well-covering
recovery, and it does not pretend to.**

What the discrepancy **could** represent: gentle per-DOF smooth frequency trends (low-rank Matérn HSGP over
log-f). What it **could not**: (a) the truth's azimuthal **symmetry-breaking mode splits** (x≠y, rx≠ry — a
spatial/asymmetry error orthogonal to a frequency-only kernel), (b) the truth's **extra higher modes**
(120–460 Hz, outside the 40–115 Hz inference band), (c) the **per-DOF stiffness mismatch** (one equal-strut
k_strut cannot simultaneously fit lateral, axial, and rocking modes), and (d) the **QOI transmission
physics** (driving-point accelerance ≠ source/load impedance sharing). Given freedom, the discrepancy trades
against σ_e/σ_build (the ridge) and de-identifies the calibration rather than fixing the structural error.

This is the **informative** result the blind protocol was designed to produce (recovery is not a tautology;
it breaks where the model's span ends). It directly **motivates the Stage-3 structure/property-based
(per-strut) discrepancy** + an asymmetric / per-DOF-stiffness forward model + a complex (magnitude+phase)
likelihood, which the inference itself recommends
([blind_known_failures.md "What would fix it"](../../../runs/round3/opus48/report/blind_known_failures.md)).

A tight, well-covering recovery would have been the *strong* result; honest, well-labeled bias and
non-coverage is the *informative* one. **Overclaimed coverage — the failure mode we were guarding against —
did not occur.**

---

## Evidence index (`sources/`)
- `scoring_recompute.txt` — netCG coverage/bias + independent R-hat/ESS reshape recompute.
- `heldout_truth_cov.py` / `heldout_recompute.txt` — held-out coverage vs CLEAN truth + per-DOF residuals.
- `blindness_grep.txt` — forbidden-path grep over inference code.
- `figure_check.txt` — figure file types/sizes.

All `runs/...` links above are the audited source artifacts; I did not modify them.
