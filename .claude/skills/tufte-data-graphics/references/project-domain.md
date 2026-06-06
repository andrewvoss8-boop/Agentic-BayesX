# Applying Tufte to Agentic BayesX figures

How the Tufte checklist combines with the existing CLAUDE.md / AGENTS.md figure
gates for this project's structural-dynamics + Bayesian-updating work. Tufte
adds *design* discipline; it does not replace the project's *honesty* and
*physics* gates — apply both.

## Where the project already encodes Tufte-aligned rules (keep enforcing)
From CLAUDE.md "Plots and Human Review" and "Verification":
- **Log-scaled frequency axes** for frequency-domain plots unless justified → Tufte "honest, documented scales".
- **Avoid dB unless requested/standard; state linear/dB explicitly** → graphical-integrity labeling.
- **Clean truth vs observed/simulated** overlay when synthetic truth exists → Tufte principle 1 (comparisons).
- **Absolute injected error/noise/discrepancy shown separately** from normalized diagnostics; label normalized plots as diagnostics and explain the denominator → integrity / "data variation not design variation".
- **Residual and zoom views** when a full-scale overlay hides differences → show the comparison that matters.
- **Posterior/QOI samples** shown, not just point estimates → show data variation (spread), not a bare mean.
- **Run-specific graphical model/likelihood diagram**, not a copied paper figure → documentation + integrity (don't imply a borrowed figure describes this run).
- **Method summary near the start** with model form, likelihood, data/replicate counts → Tufte documentation principle.

## Quantity contract first (Tufte principle 6: content counts most)
Before plotting any named quantity (FRF, apparent mass M(f), netCG, PSD, QOI),
state numerator / denominator / coordinate / excitation / BC / units / expected
limiting + resonance/antiresonance behavior (the project's Quantity Contract).
A beautiful plot of an undefined or wrong quantity is a failure. Put the contract
in the caption.

## Figure-type playbook
- **FRF / apparent-mass curves:** log frequency x-axis; linear magnitude in physical units unless dB is justified; mark resonances/antiresonances with light annotations in place (not a crowded legend); overlay horizontal mass-asymptote references (e.g. m1, m2, m1+m2) and vertical uncoupled-frequency references as thin guide lines; truth vs posterior median + band; residual panel.
- **Response PSD (flight/vibe):** log-log; show the spec/smoothline as a reference line for "compared with what?"; band (e.g. 95%/99%) as a layered, muted fill below the curves; state whether the band exceeds the spec in the caption with the numeric ratio.
- **Posterior parameter plots:** show prior vs posterior (comparison); show the truth marker when synthetic; use small multiples across parameters with shared structure; report 95% CI numerically in the caption; never imply precision the sampler didn't earn.
- **Convergence diagnostics (NUTS/HMC):** report R-hat and ESS over ALL sampled variables incl. raw hierarchical latents (Convergence Gate). Per-parameter **sparklines** (trace / running ESS) in a table read well. Do not color a failing R-hat green; surface the worst case next to any interval and label not-yet-converged intervals as such.
- **Sensitivity:** small multiples varying the assumption that moves the decision/QOI; keep shared scales so the reader compares magnitudes honestly; separate synthetic-data vs posterior vs decision sensitivity.
- **Small multiples across flights/builds/cases:** shared x/y limits; one shared axis-label set; vary exactly one variable per grid.

## Honest-labeling interaction with the sampler rules
- If a figure shows random-walk / random-scan Metropolis output, label it **prototype/legacy** (project sampler rule), in the caption, not just internally.
- Do not present a non-NUTS sampler's diagnostics styled to look like a passing NUTS run. Design polish must never upgrade a result's apparent strength (this is the anti-cheating + "don't make results sound stronger than files support" rule, in visual form).

## Synthetic vs measured provenance (documentation)
Every figure with synthetic truth must say so in the caption, with the data count
(datasets / repeated tests / flights) and whether build-to-build / flight-to-flight
variability is modeled. Show clean truth vs observed when truth exists.

## What Tufte does NOT override
- The physics quantity contracts, units, and limiting-behavior checks.
- The Convergence Gate acceptance thresholds.
- The anti-cheating constraints (no fabricated/borrowed-as-generated figures).
If a Tufte design choice ever conflicts with honesty or physics, honesty/physics win.
