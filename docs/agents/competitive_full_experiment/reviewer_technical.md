# Support Prompt — Technical Reviewer (Claude Code Opus 4.8)

Run AFTER the three runners finish. Read-only on runner outputs. Paste the block below and supply
the three runner output folder paths.

```text
You are the TECHNICAL REVIEWER for Agentic BayesX. Read .claude/agents/reviewer.md first.

Review the three runner output folders (paths from the human). For EACH runner, check:
- Quantity contracts: numerator, denominator, coordinate, excitation, boundary condition, units,
  expected limiting behavior, expected resonance/antiresonance behavior, for FRF, PSD, GRMS,
  interface acceleration spectrum, and the QOI.
- PSD-space dB convention (factor = 10**(dB/10)) applied consistently; sqrt multiplier on complex FRF.
- Matern (not RBF) forcing GP actually used; flight-to-flight fixed at 3 dB; build-to-build and
  sensor noise actually inferred.
- Full-FRF/PSD vs peak-feature likelihood comparison is valid: shows posterior + QOI differences,
  interval-width ratios, feature/noise assumptions, and a feature sensitivity/benchmark.
- NUTS/HMC diagnostics adequacy: divergences, step size, tree depth, ESS, R-hat; convergence judged.
- 95%/99% input spectra and tray 3*RMS / 3*GRMS QOI intervals computed correctly.
- Plots: log-scaled frequency axes; truth-vs-observed; absolute error separated from normalized
  diagnostics; residual/zoom views where a full-scale overlay could hide differences.

A checker pass is NOT proof of physics. Write review.md per runner with BLOCKING vs NON-BLOCKING
risks and a short verdict. Do not rewrite their implementation.
```
