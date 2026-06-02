# Review Request — Round 2 (Claude Opus 4.8 runner)

Reviewer: please audit in this order; each item points to the artifact that backs it.

## 1. The headline (P1) — interface response PSD vs spec GIF
- Open `figures/interface_response_psd_vs_spec.gif` (and the 11 `figures/gif_frames/frame_flight_*.png`).
- Confirm: it is the coupled **interface acceleration RESPONSE PSD** (g^2/Hz), NOT the forcing input;
  mean + 95% + 99% bands; overlaid on the original test spec (red dashed); log-frequency axis; legend.
- Engineering question (GEVS): does the spec ENVELOPE the flight interface environment? See the
  per-flight `frac_freqs_99hi_exceeds_spec` in `interface_psd_bands.json`.
- **CONFIRM THE INTERPRETATION:** I used per-flight realized-build frames (B) as primary and provided
  the sequential-assimilation view (A) as `figures/sequential_assimilation_qoi.png`. Tell me which you
  consider canonical for the GIF.

## 2. Convergence gate (P5) — is "NUTS active" earned?
- `nuts_diagnostics.json` / `nuts_diagnostics.md`: 4 chains, non-centered, R-hat/ESS over ALL latents
  including the raw `z_dome`/`z_tray`. Gate (Stan/Vehtari): rank-split-R-hat < 1.01; bulk AND tail ESS
  ≥ 400; divergences (0 ideal; <2% fail). Check the worst-case R-hat and min ESS rows.

## 3. Resolution (P4)
- `figures/resolution_sensitivity.png` + `resolution_metrics.json`: coarse global grid clips the
  62.3 Hz peak tip; mode-refined grid recovers it; the integrated 3·GRMS QOI shifts sub-percent vs a
  60k-point reference. Two separate consequences (peak ID vs decision QOI) are spelled out.

## 4. Supporting overlays (P2, P3)
- `figures/flight_forcing_overlay.png`: 11 discrete forcing draws vs original +6 dB forcing; −6 dB
  offset labeled as a PROJECT assumption (not a GEVS margin).
- `figures/flight_qoi_vs_vibe_reference.png`: flight tray 3·GRMS vs 43.9 g and 28.3 g references, log-y.

## 5. Trust checks
- `figures/posterior_recovery.png`: posterior vs synthetic truth (dome/tray f_n, ζ1, ζ2).
- `checks.json`: runner-local acceptance checks. `runtime.json`: active vs elapsed runtime.
- Immutable checkers: `shasum -a 256 -c harness/checkers/manifest.sha256` (all OK pre/post).

## Specific questions for the human
1. Which GIF interpretation (per-flight B vs sequential A) is canonical?
2. Is the log-magnitude modal likelihood acceptable, or do you want a full complex-FRF likelihood?
3. Is fixing σ_q (forcing scatter) and learning only σ_build acceptable given the scalar-3·GRMS
   confounding, or should later builds also carry full vibe/modal curves to identify σ_build?
