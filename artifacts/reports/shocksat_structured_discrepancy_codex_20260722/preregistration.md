# Preregistration — frozen before fit output

## Arms

- E0: train with the same zero-mean GP covariance as E1; set train-to-test cross-covariance to zero at prediction, retaining marginal test uncertainty.
- E1: exact zero-mean GP conditional.
- E2: exact Bayesian universal kriging with `H beta + u`; recover mean and GP contributions separately.
- E3: E2 with the mean basis locally orthogonalized to the four supported stiffness-sensitivity directions under the realized training covariance metric.

E0 and E1 use byte-identical training-fit records. E2/E3 reuse E1's selected residual covariance. Stage 1 uses exact Gaussian algebra and no sampler.

## Frozen folds

Five leave-one-drive-out folds; five coordinate-only spatial-cluster folds; five contiguous frequency cores over 45–260 Hz with a 10 Hz training guard; and five hash-permuted spatial×frequency pairs. Dense frequency points are never treated as independent replicates. Fold effects are the inferential units.

## Synthetic cases and gates

Seeds 0–19 on the actual selected sensor/frequency geometry:

- S0: zero mean, GP plus observation noise.
- S1: dish-region +3 dB over 80–140 Hz plus a -2 dB low-frequency tilt, lying in the intended design span to numerical projection error.
- S2: smooth continuous spatial gradient plus an off-knot frequency feature; score prediction, not coefficient recovery.
- S3: discrepancy aligned with the strongest theta sensitivity plus an orthogonal component; joint linear-Gaussian posterior for `delta log(theta), beta`.

Gates are copied verbatim from Card E: at most 1/20 false E3 successes under S0; at least 16/20 S1 E3 successes and at least 85% held-out-grid aggregate 90% learned-mean coverage; favorable median S2 error change with at most 2/20 seeds worse by more than 2 dB; S3 E3 reduces median absolute theta bias by at least 50% relative to E2, every calibrated direction has at least 80% empirical 90% coverage, and normalized orthogonality residual is at most `1e-8`.

## Measured metrics and success

E2/E3 succeeds versus E1 when either median held-out absolute-error reduction is at least 2.0 dB with 90% coverage no worse by more than 0.02, or interval width is at least 20% narrower with coverage within 0.02, without test recalibration. It must also lower paired CRPS in at least four of five folds in the split family. Report the worst fold and a cluster/bootstrap interval over folds; five-fold uncertainty is weak.

## Automatic transition

The ordered paths are `STOP_SYNTHETIC`, `STOP_CONFOUNDED`, `PROCEED_JOINT`, `STOP_PARTIAL_MEAN`, `STOP_PROPAGATION_ONLY`, and `STOP_NEGATIVE`. Missing evidence chooses the conservative stop. `automatic_decision.json` is immutable once Stage 2 output exists.
