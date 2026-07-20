# References reviewed / applied — MPL twin iteration

The method references are APPLIED (not just cited). Where each is used below.

## Girolami, Cockayne, Duncan, Oden, Tempone (2021) — "The statistical finite element method (statFEM)"
- Model: y = ρ P u(θ) + d + e (scaled FE solution + discrepancy GP d + obs noise e). APPLIED as the
  observation model for log|T|: predicted log|T| = forward(θ) + d(log f) + e, d a GP over log-frequency.
- 3-level Bayes / marginal likelihood p(Y|M) and Bayes factors (Eq 38, 52–53). APPLIED in `stage1_evidence.py`
  pattern for the cheap Stage-1 model-class ranking on the frequency observable.
- §4.1.5 model/mesh selection by marginal likelihood: "simpler can win." Carried as the honest-negative bar.
- Predictive density Eq 57 — held-out predictive on the held-out location.

## Kiran et al. (2025) review — Bayesian FE model updating
- Likelihood forms: modal (Eq 24–26) → used for the Stage-1 frequency screen; FRF (Eq 18–23) → the whole-curve
  log|T| likelihood (peak-weighted); no-mode-matching / eigen-residual (Eq 29–32) → a candidate likelihood that
  avoids fragile mode pairing.
- Evidence Eq 43–45 → BIC-adjusted Stage-1 evidence (only type-II-ML'd hyperparameters penalized).
- Hierarchical (test-to-test) — noted; limited applicability here (single build/field), flagged.

## Schneider et al. (2022) — correlated (spatial+frequency) discrepancy
- Source of the frequency-correlated / region-structured discrepancy candidate likelihood (Kiran Eq 18–23,
  statFEM Eq 31). To be tried as a model-class lever (iid vs freq-correlated vs physical-region).
- Prior lesson (L5/Card A): pure-Kronecker + fixed lengths + NUTS on a whole-FRF magnitude under real model-form
  error is multimodal; escalate to TMCMC and consider modal-feature/transmissibility likelihoods. Carried.

## Project priors carried (lessons-learned)
- L5 ShockSat: per-channel single-impact AMPLITUDE is near-irreducible for any global model (σ_QOI≈1 across
  damping+freq+shape); modal FREQUENCY is where the twin has real skill. The transmissibility observable here is
  designed to be more identifiable than single-impact amplitude (input cancels; cross-location ratio), but the
  honest-negative possibility (data can't distinguish forms) is pre-registered.
- Re-pairing-robust metrics, lead with held-out QOI (not in-sample MAC), scope claims to exactly what's tested.

## Reuse (byte-identical)
- `score.py` (L5, SHA c62c564…) — proper scores (interval/Winkler, CRPS, log-density, PIT, z, coverage/width;
  peak-weighted whole-FRF score; wideband_demo proving wide bands don't win). Problem-agnostic ⇒ reused as-is.
