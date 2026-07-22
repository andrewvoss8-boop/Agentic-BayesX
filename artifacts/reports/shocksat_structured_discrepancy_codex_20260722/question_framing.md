# Question and decision framing

## Decision

Should the final ShockSat statistical twin contain (1) a learned discrepancy mean that varies over frequency and sensor location, (2) only a correctly conditioned zero-prior-mean frequency×location Gaussian process (GP), or (3) neither?

## Objective and allowed choices

The primary objective is paired held-out median absolute force-referenced accelerance error in decibels (dB). Secondary objectives are continuous ranked probability score (CRPS; lower is better), 90% predictive coverage, and 90% interval width. Only E0–E3, the frozen basis, training-only covariance selection, and the preregistered folds may vary. The FEM mesh and model form are fixed.

## Human judgment

The runner determines whether a numerical gate was met. A human decides whether a positive but weak-five-fold result is useful enough for the final twin or thesis.

## Wrong-question trigger

The `(frequency, location, response axis)` discrepancy is the wrong abstraction if residual structure is dominated by drive×frequency forcing, undocumented orientation, or non-transferable channel nuggets. The measured study must quantify that variance before making a transfer claim.

## Literature ceiling verified before coding

Direct review of Febrianto et al. (2022), PDF pp. 7–9 and 18, shows a zero-mean spatial discrepancy prior for quasi-static strain; the nonsensor predictive mean in Eq. (28) is the conditioned FE-state mean, while new-location discrepancy enters covariance. Direct review of Schneider et al. (2022), PDF p. 5, shows zero-mean Gaussian log-magnitude/phase error and additive frequency×accelerometer-location correlation. The learned frequency×location mean tested here is absent from these two papers. No literature-wide novelty claim is allowed.
