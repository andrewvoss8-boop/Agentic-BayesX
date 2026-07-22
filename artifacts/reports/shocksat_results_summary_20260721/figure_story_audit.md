# Figure story audit — ShockSat advisor-summary revision

Date: 2026-07-21

## Narrative spine

The report should let Bilionis answer one question: **Is the next useful research contribution another
parameter-updating method, or a model-form / experiment-design contribution?** The evidence supports the
latter. Two kinds of visual evidence are needed: the delivered direction-dependent load bands and the FRF
shape mismatch. Exact method comparisons, gate outcomes, and caveats are lookup tasks and therefore belong
in tables.

## Figure-by-figure decision

| Current item | Current stories competing for attention | Fit with advisor narrative | Revision decision |
|---|---|---|---|
| Figure 1: load bands + six-method width/coverage bars + leave-modes-out bars | Delivered bands; method bake-off; coverage; humility; convergence; held-out-drive validation | Central, but overloaded and the caption incorrectly reads the upper panels as direct held-out net-CG measurements. The source code shows a plausible-truth ensemble; direct net-CG force was not measured. | Retain only three direction panels: delivered 95% band plus the plausible-truth median. Put band ratios, coverage checks, held-out-drive evidence, and the unvalidated normal direction in a table. Correct the provenance language. |
| Figure 2: trust bars + modal participation + observability list + amplitude sensitivity | Which QOIs are measured; which modes drive them; which frequencies were observed; sensitivity to an unmeasured-amplitude prior | Important evidence, but four distinct stories. | Replace with the same direction table: measured-mode share 96% / 94% / 45%, validation status, and implication. Keep the sensitivity details in the source packet. |
| Figure 3: 12-channel FRF grid | Peak alignment; shape mismatch; variation across channels; per-channel correlations; modeling convention | Central and inherently visual. The figure itself is good; 12 panels plus a long caption make it harder than necessary. | Rebuild as four deterministic, non-cherry-picked channels at fixed quantiles of updated agreement. Retain measured/original/updated curves, log frequency and log magnitude, one legend, and a two-sentence caption. Put the aggregate 0.269 to 0.338 and 70% result in text/table. |
| Figure 4: damping/shape/random leaderboard with held-back-drive overlay | Damping result; shape result; random baseline; development-vs-vault comparison; noise threshold | Exact comparison, not a shape/trend the reader needs to inspect. The held-back series creates a second story. | Replace with a four-row method table. Include baseline 0.1969, damping 0.1931, best shape 0.2337, random 0.2389, threshold, YELLOW claim status, and the non-converged damping posterior caveat. |
| Figure 5: 151-candidate histogram + proxy/full scatter | Funnel attrition; proxy-score distribution; proxy reliability; winning candidate | Secondary process detail. | Replace with one sentence (151 to 29 to 10 to 1) and a model-selection result table. |
| Figure 6: evidence across 11 model classes and three prior widths | Evidence ranking; prior robustness; candidate identity; held-out failure stated only in caption | Exact comparison with project-local labels. | Replace with a two-row table: evidence result (+54.02 log-evidence over baseline; robust top) versus held-out result (no earned improvement). Explicitly distinguish evidence on observed data from predictive skill. |
| Figure 7: six-row forest plot | Four model-form families; property control; agent vs random; four folds; thresholds | The conclusion matters, but the plot requires decoding a local score, hidden-drive folds, and selection rules. | Replace with a compact table of mean held-out gains and standard errors. Put agent minus random first; then the four genuine model-form classes. |
| Figure 8: local FIM eigenvalues | Local curvature; prior precision; nine parameter combinations; multimodality and sampler failure asserted outside the plotted data | Risks telling a stronger story than the graphic supports. All nine local directions clear the prior, but the source explicitly warns that resonance-bin crossings inflate curvature; every reported NUTS posterior is non-converged (worst R-hat 360.6, ESS about 2). | Replace with a caveat table: local FIM result, physical interpretation, sampler result, and permissible claim. No posterior interval or per-parameter identifiability claim. |
| Figure 9: MPL observed/predicted feature raster | Five held-out families; five model classes; many feature misses; valve path; next dataset | Not ShockSat evidence and too dense for a future-work paragraph. | Remove from the main packet. Mention MPL in one scoped sentence as an existing-data-only, YELLOW boundary case; point to its own packet if Bilionis wants it. |

## Main-text visual budget

1. **Figure 1 — Load bands are direction-dependent because observation coverage is direction-dependent.**
2. **Figure 2 — Frequency/damping updates align peaks but leave the channel-by-channel FRF shape mismatch.**

Everything else is a table, short finding, or appendix pointer.

## Deliberate Tufte deviations

- Figure 1 keeps a three-panel small-multiple layout because the engineering decision depends on comparing
  three load directions; it does not overlay the directions because their magnitudes and modal content differ.
- Figure 2 keeps a small legend because the same three curve roles repeat in four panels and direct endpoint
  labels would collide with dense FRFs.
- Both figures retain log frequency axes and physical/source units. Figure 1 retains the source study's
  arbitrary load scaling because the source quantity is a uniform-mass proxy; this is stated in the caption.
