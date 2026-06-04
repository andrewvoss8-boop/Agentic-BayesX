# Research directions & proposals (Claude Code Opus 4.8 runner)

These are flagged for human/master review. Per workspace isolation + the CLAUDE.md rule ("stop for human
approval before changing durable rules, checker expectations, sampler standards, or project notes"), I
have NOT written to harness/ or notes/. The reference implementations live in this workspace; the
harness/skill/hook changes below are PROPOSALS awaiting your approval and placement.

## A. Adaptive frequency grid — propose as a standard hook/skill for this problem class
Reference implementation: `code/adaptive_freq.py` (`adaptive_frequency_grid`, `points_in_halfpower_bands`).
Demo: `report/figures/adaptive_freq_demo.png`, `report/adaptive_freq_summary.json`.

Principle (no hardcoded frequencies): we have an FEM, so we KNOW the modes from the eigensolve. Build a
coarse log-spaced (octave-like) baseline over the full band, then add DENSE mode-local clusters within a
few half-power bandwidths (~zeta*fn) of each solved mode. Derived from the solved modes + damping; nothing
hardcoded.

HONEST result (demo, matched 229 points, light damping zeta=0.015):
- PEAK fidelity: peak-height error 0.7% (adaptive) vs 7.2% (uniform-log), max 3.0% vs 15.5% -> ~11x
  better. min points in a half-power band: 4 (adaptive) vs 1 (uniform) -> uniform CLIPS peaks.
- Integrated 3*GRMS: grid-robust either way (0.7% vs 0.15%); a matched-N adaptive grid can even be
  slightly WORSE on the integral if its log baseline is starved.
- RULE: use adaptive refinement for PEAK-SENSITIVE outputs (peak height, modal ID, narrow-band
  exceedance, "no clipped peaks", FRF display); keep an ADEQUATE log baseline for broadband integrals.
  Best practice = adequate log baseline AND mode-local refinement.

PROPOSED hook (for approval): whenever an FRF/PSD frequency vector is generated for a model whose modes
are known, default to `adaptive_frequency_grid(modes, zetas, fmin, fmax)` rather than a hand-picked grid,
and emit `points_in_halfpower_bands` as a resolution check. This operationalizes the CLAUDE.md
"Discretization Resolution" gate (resolve QOI-driving features; no hard-coded lines-per-band).

## B. Model-form-error correlation over ELEMENT FEATURE SPACE (novel; prioritize)
Human idea (strong): the discrepancy's correlation should not be purely spatial. Model-form error arises
from MODELING ASSUMPTIONS, which cluster by element TYPE and PROPERTY — so the discrepancy should be
correlated by "which assumption is wrong," i.e. over an element FEATURE space:
- elements sharing a PROPERTY id -> high correlation (same idealization error);
- elements of the same TYPE (spring / beam / shell / solid) -> moderate correlation (shared element-tech
  error, e.g. all Euler-Bernoulli beams share the same shear-neglect error; all linear joint springs
  share the linear-joint error);
- elements far apart in BOTH type and property -> low correlation.

This generalizes statFEM's spatial GP (Girolami: kernel "is a modelling choice based on what is
understood about the structure") to a kernel on element ATTRIBUTES. Proposed kernel form:
  k(e_i, e_j) = sigma^2 * [ a * 1(prop_i = prop_j) + b * 1(type_i = type_j)
                            + c * exp(-(log k_i - log k_j)^2 / (2 l_k^2)) ] * spatial_factor(x_i, x_j)
i.e. categorical (Hamming-like) terms on property/type + a continuous term on element stiffness magnitude
+ an optional spatial-proximity factor. The discrepancy then perturbs ELEMENT properties (parameter-space
error), propagated through the FEM — the physically faithful version of the spatial error we already
inject in the truth.

Why it's promising: model-form error genuinely clusters by element technology/property, not by raw (x,y,z)
distance; this is a more honest and more generalizable discrepancy prior than a spatial GP, and is novel
relative to the spatial-field statFEM literature.

CAVEAT the human already flagged: basing correlation on MODAL PARTICIPATION puts us back in the
frequency/modal domain (participation ~ which modes the element drives) -> defer that variant; start with
property/type (+ stiffness magnitude), which is genuinely parameter-space.

Status: design only; prioritized for a future run. Would slot in as a parameter-space discrepancy on the
6-strut stiffnesses first (struts share type "spring" -> correlated; differing stiffness -> partial
correlation), then generalize to mixed element types.

## C. How build-to-build and flight-to-flight map onto base StatFEM (y = rho*P*u + d + e)
- Build-to-build: HIERARCHICAL extension of the parameter prior — the structural parameter (k) becomes a
  population, k_b ~ p(k | theta_pop); we learn theta_pop (mean) and sigma_build (scatter). A fleet/
  multi-unit StatFEM (the paper allows hierarchical hyperparameters; the population layer is the
  extension). Epistemic about the population mean (shrinks with builds) + aleatory scatter (irreducible).
- Flight-to-flight: the RANDOM SOURCE term f in statFEM's stochastic forward problem — environment/load
  variability, aleatory input, propagated to the QOI. Not a structural unknown.
- Discrepancy d and noise e remain separate from both. So: structure variability -> (hierarchical)
  parameter prior; load variability -> forcing GP; model-form error -> d; measurement -> e.

## D. Open gap to close (from the QOI discussion)
The netCG / interface-PSD QOI predictions currently propagate only k_j (epistemic) + aleatory
(build + forcing); they do NOT yet propagate the learned discrepancy d into the QOI. A complete StatFEM
twin should predict each QOI from corrected apparent mass = BU(k_j) + d (with d's uncertainty), including
honest band-growth OUTSIDE the measured band (d reverting to prior). Flagged to implement.
</content>
