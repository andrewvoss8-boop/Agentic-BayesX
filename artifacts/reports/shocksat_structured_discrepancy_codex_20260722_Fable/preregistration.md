# Preregistration — Task Card E `_Fable`

Frozen before the measured Stage-1 campaign and before any synthetic seed was scored.
Hashed into `CHECKER.sha256`; the checker verifies the hash is unchanged.

**Honest caveat, stated at the top:** a two-fold machinery smoke test read measured residuals before this
file was written. See decisions_log F8 and §9 below for the numbers that were seen, so a reviewer can check
nothing was retuned toward them.

---

## 1. Model (exact, no sampler in Stage 1)

```text
y(d,f,c) = q_meas - q_fem(theta_0)              raw residual, dimensionless log-ratio
y        = c_d + H(f,x,a) beta + u_d(f,x,a) + e
c_d      ~ Normal(c_bar, tau_c^2)               learned from TRAINING drives only
beta     ~ Normal(0, Lambda_beta)               zero-centred PRIOR; the fitted CONDITIONAL mean is not zero
u_d      ~ GP(0, K_fx)                          independent realisation per drive (rho = 0)
K_fx     = sigma_u^2 [ r K_f(df; l_f) (x) I_x + (1-r) I_f (x) K_x(dx; l_x) ]
e        ~ Normal(0, sigma_e^2) + per-channel excess nugget
```

Frozen: `l_f = 10 Hz`, `l_x = 2000 in`, `r = 0.82`, `zeta = 0.01`, `theta_0 = ` modal-posterior median.
`K_f` squared-exponential in linear frequency, `K_x` exponential in inches (byte-faithful to the frozen
in-project implementation; the deviation from Schneider's published forms is documented in
`question_framing.md` and tested by SENS-4).

## 2. Arms

| arm | training likelihood | held-out prediction | question isolated |
|---|---|---|---|
| E0 | zero mean, `K_TT + sigma_e^2 I` | force `K_*T = 0`; keep `K_**` as marginal uncertainty | current-style marginal discrepancy |
| E1 | **identical** to E0 | exact Gaussian conditional using `K_*T` | does zero-mean GP conditioning transfer? |
| E2 | `H beta + u`, same `K_TT` | universal kriging; `E[H_* beta]` and `E[u_*]` recovered separately | does a learned structured mean add value beyond E1? |
| E3 | as E2 with locally theta-orthogonal `H_perp` | same covariance and split | does theta protection preserve prediction while cutting confounding? |

E0 and E1 share the fitted training hyperparameters exactly (verification V3). E2/E3 reuse the E0/E1
covariance unchanged.

## 3. Hyperparameter estimation (training only, every fold)

1. `c_hat_d` = median training residual of drive `d`; `c_bar = mean(c_hat)`, `tau_c^2 = var(c_hat, ddof=1)`.
2. Per-channel variance profile `p_i` = mean squared centred training residual, normalised to mean 1.
3. `sigma_e^2 = s_nug * min_i p_i`; `nugget_i = s_nug * (p_i - min_i p_i)`.
4. `(sigma_u^2, s_nug)` by exact restricted maximum likelihood (Nelder-Mead, 2 parameters) on the training
   block, with `r`, `l_f`, `l_x` frozen.
5. A **held-out channel** gets `nugget = s_nug * (median_i p_i - min_i p_i)`. A channel-specific nugget is
   never transferred; that is the whole point.

No held-out response is used to choose knots, length scales, shrinkage, interval width or calibration.

## 4. Coefficient prior `Lambda_beta` (frozen)

Diagonal; main-effect blocks `(6 dB / 8.6859)^2 = 0.477`, interaction block `(3 dB / 8.6859)^2 = 0.119`.
Chosen as a weakly informative physical scale for a log-magnitude discrepancy; never tuned.

## 5. Splits (see `out/split_registry.json`, written before any fitting)

Drive (5 folds), spatial cluster (5), frequency core with a 10 Hz training guard (5), joint (5, Stage 1 only).

Structural consequences, stated in advance so they cannot be spun later:

- Under `rho = 0` and the card's `(x) I` kernel, `K_*T = 0` **exactly** in the drive family and in the joint
  family. Therefore **E1 == E0 by construction in those two families**, and only the structured mean can
  transfer there. This is a property of the frozen model, not a result.
- In the spatial family only the `(1-r) = 0.18` term carries cross-covariance, and with `l_x = 2000 in`
  it is essentially a common per-frequency-line offset.
- In the frequency family only the `r = 0.82` term carries cross-covariance, across a >= 10 Hz guard.

## 6. Scoring rules (frozen)

- Independent unit = drive / spatial cluster / contiguous band / joint pair. Dense frequency bins are **not**
  treated as independent replicates.
- Family-level statistic = the **median across the 5 folds of the per-fold median absolute error in dB**.
  Reduction = `stat(E1) - stat(arm)`.
- Coverage and width are averaged across the 5 folds.
- CRPS rule: the arm must have lower per-fold CRPS than E1 in at least 4 of the 5 folds.
- Uncertainty on 5 paired fold effects is reported as a percentile bootstrap over folds and is labelled
  **weak** unconditionally.

## 7. Synthetic gates (>= 20 deterministic seeds per case, real geometry, real splits)

| case | injected discrepancy mean |
|---|---|
| S0 null | `m = 0`; GP + observation noise only |
| S1 in-basis | dish-region **+3 dB** bump over 80–140 Hz plus a **-2 dB** low-frequency tilt |
| S2 out-of-basis | smooth continuous spatial gradient + an off-knot frequency feature |
| S3 confounded | a component aligned with the strongest theta sensitivity plus an orthogonal component |

Automatic acceptance, frozen:

- **S0 false-positive gate:** at most 1 of 20 seeds may make E3 cross the 2 dB / 20% rule versus E1.
- **S1 recovery gate:** E3 crosses the rule with acceptable coverage in >= 16 of 20 seeds; its learned-mean
  90% band covers the injected mean at >= 85% of held-out grid points aggregated by independent unit.
- **S2 robustness gate:** median E3-vs-E1 held-out error change across seeds is favourable, and at most 2 of
  20 seeds worsen median absolute error by more than 2 dB.
- **S3 confounding gate:** E3 reduces median absolute `delta_eta` bias by >= 50% relative to E2; every
  calibrated theta direction reaches >= 80% empirical 90% interval coverage across seeds; and the normalised
  orthogonality residual `||J^T W H_perp|| / (||J|| ||W H_perp||) <= 1e-8`.

If any synthetic gate is missed: STOP before measured fitting, write the failed thresholds and worst numbers
to `automatic_decision.json`, finish the artifacts, report. No approval request.

## 8. Preregistered sensitivities

| id | what varies | scope |
|---|---|---|
| SENS-1 | frequency-dependent damping `zeta(f) = 0.003 + zeta_w(f)` in the forward model | spatial + frequency families |
| SENS-2 | theta uncertainty **marginalised into the training covariance** (low-rank Woodbury) instead of propagated only at test points | frequency family |
| SENS-3 | `l_f`, `l_x`, `r` learned on training data inside physical bounds (`l_f` in [2, 60] Hz, `l_x` in [1, 200] in, `r` in [0.05, 0.95]) | spatial + frequency families |
| SENS-4 | Schneider's **published** additive form `r rho_f (x) 1 1^T + (1-r) 1 1^T (x) rho_z`, both exponential, dense algebra on a 3x-decimated frequency grid | spatial + frequency families |
| SENS-5 | frequency-grid decimation (every 2nd, every 3rd line) — discretisation-resolution sensitivity | spatial + frequency families |

A sensitivity may not change the headline verdict; it can only qualify it. If a sensitivity flips a sign,
the headline is downgraded to YELLOW with the flip reported.

## 9. Smoke-test numbers seen before this file was written (disclosure)

Measured, spatial cluster 0 and frequency core 0, median absolute error in dB:

| fold | E0 | E1 | E2 | E3 |
|---|---|---|---|---|
| spatial cluster 0 | 10.80 | 9.55 | 8.47 | 8.47 |
| frequency core 0 (47–87 Hz) | 15.75 | 15.49 | 12.32 | 12.31 |

Nothing was changed in response to these numbers. If the final measured table differs from these two rows by
more than numerical noise, the difference must be explainable by a documented change (e.g. the switch from a
finite-difference to an autodiff Jacobian, which affects E3 only).

## 10. Terminal-path rules

Evaluated in order; first match wins (card §"Automatic transition after Stage 1"):
`STOP_SYNTHETIC` -> `STOP_CONFOUNDED` -> `PROCEED_JOINT` -> `STOP_PARTIAL_MEAN` ->
`STOP_PROPAGATION_ONLY` -> `STOP_NEGATIVE`. Missing evidence resolves to the applicable conservative STOP.
`automatic_decision.json` is immutable once any Stage-2 output exists.
