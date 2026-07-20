# Question & decision framing — MPL twin iteration

## Engineering decision being supported
Which FEM MODEL CLASS (mesh/elements + modeling approach + damping model + likelihood form + parameters)
gives the most trustworthy MPL-stand digital twin — i.e. predicts the response at a *held-out* accel
location (frequencies + full transmissibility spectrum + band energy) with calibrated, ideally sharp
uncertainty — and does enriching the model form measurably help vs the simplest sufficient class?

## Objective / success metric
Per leave-one-location-out split, on the held-out location:
1. **CRPS-skill vs climatology** = `1 − CRPS_twin/CRPS_clim` (>0 ⇒ twin carries location information beyond
   guessing the observed-channel population). HEADLINE.
2. **Interval/Winkler score + coverage** (proper score rewards calibration AND sharpness; coverage = trust gate).
3. **Band-GRMS error** on the gain-free transmissibility \|T\| (un-blurrable: a dimensionless ratio).
Ranked across the 5 splits (mean ± spread) AND by Bayesian evidence (Stage-1 logZ + Bayes factors +
posterior model probability, prior-sensitivity-flagged); Stage-2 TMCMC confirms the top 1–2.

## What the search/optimization is allowed to choose
- The model class: mesh density / element order, element type, modeling approach (orthotropic panel, real
  stiffener pattern, calibrated 6-DOF joints, ruler-in-FEM for the coupled config), damping model
  (Rayleigh/Caughey vs hysteretic η vs localized non-proportional), likelihood form (whole-curve Gaussian on
  log\|T\| vs frequency-/region-correlated discrepancy vs no-mode-matching eigen-residual vs shape-field),
  discrepancy structure (iid vs frequency-correlated vs physical-region), parameter vector + priors.
- The posterior over the chosen class's parameters (via NUTS, convergence-gated; TMCMC for evidence/multimodal).

## What remains human judgment
- Whether to REPLACE the inherited fable FEM (surfaced to Andrew, never self-applied).
- Durable-rule / checker-expectation / sampler-standard changes (surfaced).
- Acceptance of the node-mapping / load-shape assumptions flagged ANDREW-CONFIRM in the ledger.
- Whether an evidence-positive-but-held-out-neutral result warrants further data (multi-reference, force gauge).

## What would make this the WRONG question
- If the held-out QOI is dominated by a quantity the no-force observable cannot legitimately access (absolute g,
  calibrated apparent mass) — then no model class can win and the framing is mis-scoped. Mitigation: the QOI is
  the gain-free transmissibility + frequencies + band-GRMS only.
- If the single-sensor, single-axis, fixed-acoustic-field data cannot distinguish the candidate model forms at
  all (the L5 ShockSat finding: per-channel single-impact amplitude is near-irreducible for any global model).
  Then the honest result is YELLOW: simplest sufficient class wins; state the data that would resolve it.
- If the load-shape nuisance (unknown acoustic spatial distribution) is so dominant that the transmissibility
  is uninformative about the structure — checked by the discrepancy floor vs the cross-location signal.
