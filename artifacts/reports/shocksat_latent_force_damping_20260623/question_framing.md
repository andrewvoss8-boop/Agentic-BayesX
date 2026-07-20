# Question framing (AGENTS Question & Decision Gate)

## Engineering decision being supported
Whether the clean modal-hammer **ring-downs** (time domain) unlock per-mode **damping ζ** and residual model-form
information that the single windowed FRF (D22, frequency domain) could not — and whether that information buys a
**less-conservative-yet-defensible** PSD-envelope qualification level (the live ShockSat PSD-envelope twin program).

## Objective / success metric (three layers)
- **L1 (headline):** number of union modes whose damping ζ is RESOLVED from the ring-down (posterior CI < half the
  prior log-width, interior, with a passed resolvability table), vs D22's 0/9 from the windowed FRF.
- **L2:** the fraction of the latent model-form-error (MFE) force explained by a viscous **damping** correction
  (parsimonious "FEM has the wrong ζ") vs a genuine non-viscous/nonlinear **residual** (missing physics).
- **L3 (hard bar):** held-out 97.5%-percentile PSD-envelope **GRMS ratio** twin/(FEM+6 dB) < 1 while still enveloping
  the held-out measured PSD (energy-weighted exceedance, Q-E). Reused byte-identical from the live program.

## What the analysis is allowed to choose
- The decay-estimation method (band-pass width, fit window, smoother process noise) and the NUTS/smoother
  hyperparameters — all documented, with robustness sweeps where they could bias the answer.
- Which modes/channels/hits enter each fit (gated by SNR, coherence-at-peak, R² of the decay fit, cycles of decay).

## What remains human judgment
- Whether to adopt the measured ζ into the live FEM/CLA forward (this run shows it does NOT win the
  less-conservative-envelope metric — a measured-ζ twin is MORE conservative because the FEM is over-damped).
- Whether the per-node FEM shape error (the binding limit) is worth an agentic FEM-correlation effort (out of scope).
- Any change to the inherited QOI contract, the sampler standard, or the project notes (surfaced, not self-applied).

## What would make this the WRONG question
- If the ring-downs were too short/noisy to resolve even the heaviest mode (they are not: 40–120 cycles of decay,
  SNR 4–25, ζ resolved for 14/16 modes) — then the time-domain claim would collapse to D22 (a YELLOW pre-test floor).
- If a realistic ζ change did NOT move the envelope QOI (it does, ~1/ζ — finite-perturbation gate passed), then ζ
  would not be a lever at all and L3 would be moot. It IS a lever in absolute terms; it simply CANCELS in the
  contract's twin/FEM win ratio and points the wrong way (FEM over-damped), so it does not win the live metric.
- If the latent force absorbed everything and made ζ/model-form attribution uninterpretable (the prompt's stop
  condition): partly true for the raw variance split (q_g/close-mode-beating contaminated) — so we lean on the
  q_g-robust velocity-projection ζ and the log-decrement cross-check (corr 0.82) for the L2 conclusion, and flag the
  variance-split caveat rather than over-claiming.
