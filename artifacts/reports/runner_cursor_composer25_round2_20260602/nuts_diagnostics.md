# NUTS diagnostics — Cursor Composer 2.5 round 2

Sampler: NumPyro NUTS, 4 chains, warmup 1000, samples 1000.

## Convergence gate (source-backed)

- max rank-normalized split R-hat < 1.01
- bulk ESS and tail ESS >= 400 (= 100 x chains)
- divergences: 0 ideal; >2% post-warmup is fail

## Full likelihood

- converged_all_variables: **True**
- max_r_hat: 1.0028201622552135
- min_bulk_ess: 901.4619299057999
- min_tail_ess: 945.6197875376464
- divergences: 0 (0.0)

## Peak-feature likelihood

- max_r_hat: 1.0027049644228427
- min_bulk_ess: 1471.0928618664182

Do **not** treat headline intervals as final engineering evidence unless `converged_all_variables` is true.
