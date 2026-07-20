# Follow-up E1 — a SECOND error class (localized stiffness defect) to press into the method differences

**Why this run.** The main study's model-form error (a Winkler foundation) was *θ-like* across the drive
band, so all three constructions absorbed it into a biased θ and looked the same — the only differences
were M-lik's fictitious-σ_r drift and a modest held-out-coverage gap. To press into the DIFFERENCES, this
follow-up uses a model-form error that is **NOT θ-like**: a localized stiffness defect
`EA(x)=θ_true·(1 − depth·1[0.4≤x≤0.6])` (a soft patch in the middle of the rod). This is exactly the
spatially-structured discrepancy that statFEM's additive spatial GP term is *designed* to absorb, but that
physics-in-likelihood (M-lik) and physics-in-prior (M-ift) have no dedicated term for.

**Setup.** Truth = a high-resolution variable-EA FE reference solve (n_el=512), **not analytic** (the
defect breaks the analytic sine solution); validated to match the analytic uniform response at depth=0
(rel diff 2.6e-6). The three inference models are UNCHANGED (uniform-EA, defect omitted = the model-form
error). Finest discretization, n=8 replicates, NUTS 4-chain. **All 12 cells converged** (worst R-hat 1.007).
Code: `code/followup.py`, `code/followup_run.py`, `code/fig_followup.py`. Figure:
`figures/figF_followup_defect_class.png`. Data: `followup/defect_summary.json`.

## Results (defect depth 0 → 0.5)

| depth | M-lik θ / cov | M-statfem θ / cov / σ_d | M-ift θ / cov |
|------:|:-------------:|:----------------------:|:-------------:|
| 0.00  | 1.150 / 1.00  | 1.151 / 1.00 / 0.0007  | 1.151 / 1.00  |
| 0.15  | 1.108 / 1.00  | 1.112 / 1.00 / 0.0031  | 1.109 / 1.00  |
| 0.30  | 1.053 / **0.71** | 1.062 / **1.00** / 0.0103 | 1.046 / **1.00** |
| 0.50  | 0.946 / **0.33** | 0.962 / **1.00** / 0.0762 | 0.993 / **1.00** |

(θ_true = 1.15; depth=0 is the no-error control — all three recover θ.)

## What it shows (the sharpened method differences)
1. **θ recovery fails for all three** under the spatial defect too (θ biased down to ~0.95–0.99 as the
   patch softens) — the model omits the defect, so no construction recovers θ_true. M-ift is marginally
   least biased at depth 0.5 (0.993). *Parameter non-recovery under model-form error is the shared limit,
   robust to the error class.*
2. **Held-out PREDICTION is where the methods split — sharply.** Physics-in-likelihood (M-lik) with a
   FIXED residual noise σ_r **cannot recalibrate**: its 95% held-out coverage **collapses 1.00 → 0.33**.
   Both methods that LEARN their model-error term keep prediction calibrated: M-statfem (learned additive
   discrepancy) and M-ift (learned prior weight β) hold coverage at **1.00** across all depths. This
   amplifies the main-study gap (foundation: M-lik 0.71 vs M-ift 0.86 vs M-statfem 1.00).
3. **statFEM's discrepancy actually CATCHES this error.** Its learned σ_d **grows ~100×** (0.0007 → 0.076)
   with the defect depth — whereas for the θ-like Winkler foundation σ_d stayed flat at ≈0.004 and did NOT
   flag the error. So statFEM's additive *spatial* discrepancy is informative for *spatially-structured*
   model error but blind to a θ-like one (which θ silently absorbs). The discrepancy's diagnostic value is
   error-class dependent.

## Verdict refinement (for Ilias)
The mechanism Bilionis warns about — a *fixed, un-calibrated* residual treatment in the LIKELIHOOD — is the
real culprit, and its damage is broader than θ drift: under a non-θ-like model error, physics-in-likelihood
is **confidently wrong on PREDICTION** (coverage 0.33), because its fixed σ_r cannot widen the predictive
bands. The two constructions that LEARN their model-error term — statFEM's discrepancy σ_d and IFT's
prior temperature β — both stay predictively honest (coverage 1.00), even though neither recovers θ. So:
**learn the model-error weight from data** (whether in the prior, à la IFT, or as an additive discrepancy,
à la statFEM); a fixed residual noise in the likelihood is the brittle choice. None of the three recovers
the parameter under model-form error — that needs breaking the discrepancy↔parameter confounding (richer
observables / constrained discrepancy), the open improvement carried from the main study.

## Scope / honesty
One synthetic realization per cell; defect truth is a high-res reference solve (surrogate, not measured);
θ-only inference models (the corrected-model 2-parameter decomposition, E2, is the natural next probe).
This follow-up does not modify the main study's immutable `check.py`; the main checker still passes
(YELLOW 60/3/0) with `figF` present (image-QA + text-overlap audited).
