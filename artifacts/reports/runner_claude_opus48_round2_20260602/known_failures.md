# Known Failures, Limitations & Residual Risk — Round 2

## Process honesty
- **Accidental double-run early on.** A smoke run was left running in its slow 11-fit sequential step
  while I launched the first full run; the two contended for CPU/XLA devices and looked hung. I killed
  both and used a single clean full run for all reported artifacts. The first (uncontended) full run
  produced converged diagnostics with **1 divergence** in 8000 draws; I then raised
  `target_accept_prob` 0.95→0.99 and re-ran for a cleaner result. The REPORTED numbers come from the
  final run only (`smoke_mode=false` in `nuts_diagnostics.json`).

## Modeling limitations (do not over-read the result)
- **Modal likelihood uses log-MAGNITUDE only** (phase dropped). Carries the identifying info for k,ζ
  and the magnitude build effects, but is less informative than a full complex likelihood.
- **Flight 3·GRMS likelihood integrates the KNOWN forcing GP out as a LogNormal** with a FIXED σ_q
  (precomputed by 4000-sample MC at truth). This CONFOUNDS build-to-build scatter with forcing scatter
  in the scalar, so **σ_build is only weakly identified** — its posterior stays wide. The per-build
  effects for builds 1–10 are therefore close to prior (only build 0 has rich vibe+modal data).
  Consequence: the per-flight GIF frames for flights 1–10 differ mostly through the (uncertain) build
  effect and the known forcing GP, not through strong per-flight learning. This is honest and expected.
- **No separate model-discrepancy term.** The synthetic truth lies inside the parametric forward-model
  family (by construction of the round-1 dataset), so there is no model-form error to infer here. A
  real test article would need a StatFEM discrepancy term; not in scope this round.
- **Tray f_n posterior is slightly biased low** (truth 86.25 Hz sits near the upper tail). Likely from
  the log-magnitude modal likelihood + build/transmissibility partial confounding. Documented, not hidden.
- **Single synthetic realization.** One dataset; flight-to-flight forcing variability is modeled (fixed
  3 dB GP) and build-to-build is modeled (learned), but there is no replicate vibe/modal test.

## Interpretation risk (flagged, not resolved by me)
- The headline GIF uses interpretation **(B) per-flight realized build** as primary; interpretation
  **(A) sequential assimilation** is provided as a secondary figure. The human should confirm which is
  canonical. The secondary (A) figure shows the structural QOI posterior is essentially STABLE across
  cumulative flights — i.e. the flight scalars add little structural information beyond build-0 data —
  which is itself a finding worth the human's attention.

## What a reviewer should still check by eye (checker cannot encode physics)
- That every figure has a legend (the checker verifies file existence/size, not legend pixels).
- That the interface response PSD stays under the spec envelope across frequency in every frame
  (the 99%-exceeds-spec fraction is recorded per flight in `interface_psd_bands.json`).
- That the resolution figure’s coarse-grid curve visibly clips the 62.3 Hz peak tip while the QOI is
  unchanged (the engineering point of P4).
