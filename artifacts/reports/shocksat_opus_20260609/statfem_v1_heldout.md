# StatFEM v1 — Held-Out QOI Validation (predicted with CI vs actual)

Date: 2026-06-09 · Build: `scripts/opus_statfem_v1_heldout.py` · Replay: `bash run_all.sh`
Figure: [figures/v1_heldout_qoi_sidebyside.png](figures/v1_heldout_qoi_sidebyside.png) ·
Table: `v1_heldout_qoi_table.csv` · Summary: `v1_heldout_qoi_summary.json`

## What this is
The held-out validation the project asked to *see*: held-out quantities of interest (QOIs)
predicted by the StatFEM v1 twin **with 95% confidence intervals**, placed side by side with
their **actual** values.

## Provenance and honesty (read this first)
This was **not re-fit to the held-out truth**. It assembles two integrity-pinned sources:
- **Predictions + posterior CIs** come from the modal-correlation StatFEM v1 (NUTS, 4 stiffness-
  group scales, convergence-gated) built by the modeling-freedom runner and **locked in
  `finalists.json` before any vault access**. The script re-verifies its SHA256 against the
  committed pin `finalists.sha256` (**match confirmed**) and refuses to run otherwise.
- **Actuals** come from the **sealed synthetic-tray vault truth** (truth-known substrate → a true
  held-out QOI exists) and the **graded real ShockSat pyro** regime.

So the temporal commitment (predict → lock → then reveal truth) was already enforced by the
experiment protocol; this is the legitimate grading view, not hindsight tuning.

- **Model:** free-free modal-correlation twin; observation layer = modal frequencies + mode-shape
  components on the consistent 1101–7105 grids (the normalization finding ruled out a magnitude
  FRF likelihood). Sampler: **NUTS**, ≥4 chains, non-centered; all three finalists pass the
  convergence gate (max R-hat ≤ 1.016, min ESS ≥ 370, 0 divergences).
- **QOI definition:** peak |H_{out,in}(ω)| (receptance) over 10–600 Hz, units m/N, modal damping
  ζ = 0.02. Two paths: `QOI_ref` (in-regime, out 11 ← in 0) and `QOI_heldout` (out-of-distribution
  forcing path, out 5 ← in 8). `θ_true = [1.15, 0.88, 1.06, 0.80]`.

## Result — synthetic tray (truth known), 95% CI vs actual

| finalist | QOI | predicted | 95% CI | actual | err % | CI covers? |
|---|---|--:|---|--:|--:|:--:|
| F1 (freq+shape) | ref (in-regime) | 8.23e-6 | [7.06e-6, 9.40e-6] | 9.13e-6 | −9.8 | **yes** |
| F2 (freq) | ref (in-regime) | 8.32e-6 | [7.10e-6, 9.54e-6] | 9.13e-6 | −8.9 | **yes** |
| F3 (none) | ref (in-regime) | 8.11e-6 | [7.68e-6, 8.55e-6] | 9.13e-6 | −11.1 | no |
| F1 (freq+shape) | **held-out (OOD)** | 4.60e-5 | [4.00e-5, 5.19e-5] | 3.25e-5 | **+41.6** | **no** |
| F2 (freq) | **held-out (OOD)** | 4.68e-5 | [4.02e-5, 5.33e-5] | 3.25e-5 | **+44.0** | **no** |
| F3 (none) | **held-out (OOD)** | 4.55e-5 | [4.34e-5, 4.76e-5] | 3.25e-5 | **+40.1** | **no** |

**Headline:** in-regime, the twin is mildly low (~9–11%) and the better-calibrated finalists (F1,
F2) cover truth; **out of regime, all three finalists over-predict the held-out QOI by ~40–44%
and NO 95% CI covers the sealed actual.** A converged, gate-passing twin is **confidently wrong**
outside its calibrated regime. Note F3's *narrow* in-regime CI misses truth → narrow ≠ accurate.

This is the project's central cautionary result, now shown with numbers: **the convergence gate
certifies sampling, not generalization; only the held-out set exposes the OOD miscoverage.**

## Result — real ShockSat held-out (pyro NSD): directional only
Figure: [figures/v1_shocksat_pyro_directional.png](figures/v1_shocksat_pyro_directional.png).
The real held-out regime is the pyro shock. Only a *direction* was committed (no magnitude QOI),
so there is no CI-vs-number here — and we do not fabricate one. The graded pyro data show **99.9%
of acceleration energy lies above the twin's ~152 Hz validated band** (median peak-PSD ~3.8 kHz,
95%-energy ~82 kHz). The twin therefore *cannot* resolve the pyro regime → committed direction
(under-resolve / under-predict) **confirmed**. This is the honest OOD extrapolation limit of a
modal twin and motivates the unknown-forcing / high-frequency work as the real novelty axis.

## Caveats
- The synthetic OOD overfit is *small in magnitude* (mode shapes pin θ strongly); the ~40% OOD
  floor is dominated by a shared missing-joint model-form bias (the QOI does not propagate the
  discrepancy δ), so read the cross-finalist differences as a *ranking* signal.
- Real-data held-out (pyro) is directional, not a calibrated magnitude prediction.
- This is v1: 4 stiffness groups, modal-only observation layer, single build (no build-to-build
  scatter). Next steps belong in a task card.
