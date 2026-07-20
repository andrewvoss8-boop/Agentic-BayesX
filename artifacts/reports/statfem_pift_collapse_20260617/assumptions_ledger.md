# assumptions_ledger.md — Card B (PIFT collapse / orthogonal-Schneider cure)

All values are explicit, with units, rationale, source, and sensitivity priority. Inherited from the synthetic
companion `statfem_shocksat_eval_20260616` (COPY-reused core) unless noted.

## Model / forward
| symbol | value | units | rationale / source | sensitivity |
|---|---|---|---|---|
| testbed | plain ShockSat, 9 groups, reduced 74-mode basis | — | card §3 (no coupled tray); reduced_blocks.npz SHA be9af90e… (modal twin) | fixed |
| K_red(θ) | A_fix + Σ_g θ_g A_g | — | linear-in-θ group-stiffness multipliers | fixed |
| ζ (modal damping) | 0.02 (2% critical), all modes, hysteretic η=2ζ | — | installed-config representative; free-free .ash is artificially light (D5 companion) | medium |
| band | 45–260 Hz | Hz | spans the calibration-mode region (<222 Hz), 74-mode basis 54.6–321.7 Hz | low |
| QOI | held-out PEAK & band-GRMS accelerance | (in/s²)/lbf (synthetic) | decision-relevant interface response | — |

## Discrepancy / noise (the genuine model-form error)
| symbol | value | units | rationale | sensitivity |
|---|---|---|---|---|
| σ_meas | 0.05 | log-mag | iid measurement noise floor | medium |
| Schneider log-amp std | 0.03 → 0.12 (rises with f) | log-mag | injected correlated model-form error, NOT representable by θ | HIGH |
| ℓ_f (corr length) | 0.30 | log-Hz | freq correlation length (squared-exp) — sets the freq N_eff ceiling | HIGH |
| ℓ_z (corr length) | 12.0 | in | sensor-space correlation length (exponential) — sets the space N_eff ceiling | HIGH |
| phase frac | 0.5 | — | complex-discrepancy phase relative to amplitude | low |

## Priors / inference
| symbol | value | rationale |
|---|---|---|
| θ prior | LogNormal(0, 0.25) per group (9) | ~±28% 1σ stiffness multiplier |
| σ_d prior | HalfNormal(0.3) | weakly-informative discrepancy scale (M1/M2/M3) |
| NUTS | 4 chains, dense mass, target_accept 0.9, max_tree_depth 6, 1000 warmup + 1000 samples | companion D12 (depth-6 sweet spot for the stiff FRF posterior) |
| convergence gate | max R-hat ≤1.05, min ESS ≥200, div-frac <2%, ALL variables | AGENTS.md |

## The controlled truth (synthetic leg)
- ONE truth: combo "mixed" — top_box ×1.15, joints ×1.20, plates ×0.88 (identifiable + unidentifiable θ bias)
  × ONE fixed Schneider correlated-complex field (seed 20260617) + fixed measurement noise.
- The known model-form error = the Schneider field (not representable by any θ) + the unidentifiable joint bias.

## The observation-density ladder N (the collapse axis = the PIFT "collocation points")
- master fine grid NMAX = 640 log-spaced points; each cell uses an EXACT decimated subset (densification of the
  SAME truth). primary axis N_freq ∈ {20,40,80,160,320}; secondary N_sensor ∈ {3,6,12,18}; N = N_freq·N_sensor.
- held-out evaluation set FIXED across the sensor ladder; drive DOF fixed.

## Data count / variability (Assumptions & Uncertainty Gate)
- Synthetic leg: ONE truth realization (one Schneider field, one noise draw); no flight/build/test variability.
- Real leg (P3): single-impact matched-path FRF (no hit-to-hit averaging) — 1-hit SNR, coherence-weighted; YELLOW.

## Inferred vs fixed
- INFERRED: θ (9 group multipliers), σ_d (M1/M2/M3). FIXED: ζ, σ_meas, Schneider correlation lengths ℓ_f/ℓ_z
  (inference uses the injected lengths — favorable to the correlated arm; a mismatch arm is a sensitivity item).
- NOT inferred: the realized Schneider discrepancy field itself (only its scale σ_d); the held-out discrepancy
  is KRIGED (M2/M3) from observed residuals, not sampled as latent.

## EARLY FINDING (logged 2026-06-17, will be reported per-N)
- Low observation density (N=120, N_freq=20) is UNDER-IDENTIFIED: 4-chain R-hat ≈ 8–24, ESS ≈ 2 (multimodal
  θ↔discrepancy). These low-N cells are LABELED not-yet-converged (YELLOW); the headline collapse curve is read
  over the CONVERGED higher-N regime (the companion converged at N=960). The low-N non-convergence is itself the
  "broad / not-yet-collapsed" end of the story, reported, not hidden.
