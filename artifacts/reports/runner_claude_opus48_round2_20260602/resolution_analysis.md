# Resolution Analysis (P4)

## Grid choice and rationale
- **Global grid (consumed, not regenerated):** the shared `sequential_dataset.json` grid — 260
  log-spaced points, 20–2000 Hz. min Δ(ln f) ≈ 0.01778, i.e. at 62 Hz Δf ≈ 1.10 Hz.
- **QOI-driving resonances** (verified numerically against the forward model):
  - Coupled interface/tray response: **62.3 Hz** (half-power Δf ≈ 1.82 Hz, ζ_eff≈0.015) and
    **129.5 Hz** (Δf ≈ 7.85 Hz). These — NOT the uncoupled 86.25/93.5 Hz — drive the coupled
    interface response PSD and the flight 3·GRMS.
  - Standalone tray-vibe transmissibility peak: **86.25 Hz** (Δf ≈ 3.37 Hz) — drives the vibe 3·GRMS.
  - Dome-only modal peak: **93.5 Hz**.
- **Why the global grid is marginal:** at the narrowest mode (62.3 Hz) the global grid puts only
  ≈ 1.82/1.10 ≈ **1.7 points inside the half-power band** → the peak TIP falls between grid points and
  is visually clipped (this matches the round-1 reviewer note about a clipped tray peak).
- **Mode-local refinement (this run):** the analysis grid for QOI integration and the headline PSD
  bands = global grid ∪ 41-point LINEAR clusters spanning ±3·Δf around each of 62.3/86.25/93.5/129.5
  Hz. This clusters extra points where curvature is highest (near f_n), which is more efficient than
  uniformly increasing the global point count. No source-backed fixed "lines per band" number is
  invented; density is a documented assumption and resolution is PROVEN by the sensitivity check below.

## Sensitivity check (coarse global vs mode-refined vs 60k-pt reference)
Numbers are written by the pipeline to `resolution_metrics.json` (figure: `figures/resolution_sensitivity.png`).
Two findings, kept separate because they have different engineering consequences:

1. **Peak TIP (visualization / modal identification):** on the coarse global grid the 62.3 Hz peak
   height is under-resolved (clipped) by `peak62_coarse_clip_frac`; the mode-refined grid removes the
   clip (`peak62_refined_clip_frac` ≈ 0). Consequence: any peak/modal-feature reading off the coarse
   grid would under-report the resonance amplitude — relevant if a future likelihood uses peak features.

2. **Integrated 3·GRMS QOI (decision quantity):** the tray and interface 3·GRMS shift by
   `*_coarse_err_vs_ref` (coarse) and `*_refined_err_vs_ref` (refined) relative to the 60k-point
   reference. Both are SMALL (sub-percent) because the narrow 62 Hz peak carries little of the total
   integrated energy. Consequence: the 3·GRMS decision QOI is **robust** to grid choice; the headline
   envelope conclusion is not sensitive to the clip.

## Runtime/accuracy tradeoff
- Refining globally to 60k points is accurate but ~230× more forward-model evaluations per likelihood
  call — intractable inside NUTS (thousands of gradient evaluations). Mode-local refinement (+164
  points, ~1.6× cost) recovers the peak tip and matches the reference 3·GRMS to sub-percent, so it is
  the chosen analysis grid. The NUTS likelihood for the modal/vibe curves still uses the dataset's
  native grids (the observations live on those grids); only the QOI integrals and the headline PSD
  bands use the refined grid.

## Residual risk
- The "observed" flight 3·GRMS values in the dataset were integrated on the coarse 260-pt grid by the
  round-1 generator, so they carry the same sub-percent grid bias; this is far below the fixed
  forcing+sensor log-scatter σ_q used in the flight likelihood, so it does not bias the posterior
  meaningfully. Documented rather than corrected.
