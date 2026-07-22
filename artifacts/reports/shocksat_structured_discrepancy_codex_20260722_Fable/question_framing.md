# Question and decision framing — Task Card E `_Fable`

## The engineering decision being supported

Should the final ShockSat statistical twin include

(a) a **structured response-discrepancy mean** that varies with frequency and sensor location,
(b) a **conditioned zero-mean GP discrepancy only**, or
(c) **neither** (keep the current marginal-variance discrepancy)?

## Objective function / success metric

- **Primary:** paired change in held-out **median absolute FRF error, in dB**, scored at independent-unit
  level (drive, spatial cluster, contiguous band).
- **Secondary:** CRPS in dB (lower is better), 90% predictive coverage, 90% interval width in dB, and measured
  shear-load proxy metrics where the existing mapping is valid.
- **Success bar (frozen by the accepted project decision, not chosen here):** median held-out absolute-error
  reduction >= 2.0 dB with 90% coverage no worse by more than 0.02 absolute; **or** 90% interval width >= 20%
  narrower with coverage within 0.02 absolute of E1 and **no** test-set recalibration. Additionally, lower
  paired CRPS in at least 4 of 5 folds in the relevant split family.

## What the automatic search is allowed to choose

Nothing about the science. The only automated choices are:

- coefficient posteriors and GP conditionals, which are **exact analytic** Gaussian results, not searched;
- two covariance scale parameters (`sigma_u^2`, the nugget scale) fitted by restricted maximum likelihood
  **inside each training fold**;
- the terminal path (STOP_SYNTHETIC / STOP_CONFOUNDED / PROCEED_JOINT / STOP_PARTIAL_MEAN /
  STOP_PROPAGATION_ONLY / STOP_NEGATIVE), which is decided by the card's numerical rules in
  `out/automatic_decision.json`, not by agent preference.

Arms, splits, basis, success bar, gate thresholds and the interpretation hierarchy are all frozen inputs.

## What remains human judgment

Whether an artifact-backed positive effect is **useful enough to adopt** in the final twin or the thesis.
That judgment does not pause or change this run.

## What would make this the wrong question

The card's wrong-question triggers, checked and reported:

1. The residual depends primarily on unmodelled forcing, channel orientation, or **channel-specific nuggets**
   that cannot transfer from `(f, x)`.
2. The residual needs a **drive x frequency** term, i.e. the `(f, x)` framing is inadequate.
3. The held-out design has too few independent units to resolve the success bar. With five folds per family,
   uncertainty is labelled **weak** even when the threshold is crossed — this is a standing caveat here, not
   a contingency.

Frozen in-project prior evidence says trigger 1 is likely: region explains only `R^2 = 0.036` of the residual
variation and the channel nugget contrast is large (hard channels ~17.45 dB vs ~6.54 dB elsewhere).

## Literature claim ceiling — verified directly from the PDFs in this run

Verification was run by extracting the equations from the actual PDFs
(`code/` produced `out/literature_check_fable.json`), not from recollection.

### Febrianto, Butler, Girolami, Cirak (2022), *Digital twinning of self-sensing structures using statFEM*

- Eq. (11): the model-reality mismatch is `d ~ p(d) = N(0, C_d)` — **zero prior mean** (PDF p. 7).
- Eq. (12)/(4): `C_d` comes from a **squared-exponential kernel in spatial coordinates only**; there is no
  frequency input anywhere in the kernel (PDF pp. 6–8). The word "frequency" appears in the paper only as
  *sampling frequency*.
- Eq. (24a): `c_d(x, x', k) = (gamma_k sigma_d)^2 exp(-||x-x'||^2 / 2 l_d^2)` with
  `gamma_k = ||f_k|| / max_k ||f_k||` — a load-dependent **variance amplitude scale**, not a mean function.
  The setting is quasi-static bridge strain under a passing train; `k` is a load state, not a frequency.
- At non-sensor locations the published predictive mean moves through the **conditioned FE state**;
  `C_d` enters the predictive **covariance**.

**Conclusion:** a non-zero frequency x location discrepancy *mean* is not in this paper.

### Schneider, Papaioannou, Straub, Winter, Müller (2022), *Bayesian parameter updating in linear structural
dynamics with frequency transformed data using rational surrogate models* (MSSP 166:108407)

- Eq. (18): `[w; theta] ~ N([0; 0], diag(sigma_w^2 R_w, sigma_theta^2 R_theta))` with
  `w = log|epsilon|` — **zero mean in log-magnitude and phase** (PDF p. 5).
- Eqs. (19)–(21): `rho(dz, df) = r rho_f(df) + (1-r) rho_z(dz)`, with
  `rho_z(dz) = exp(-dz / l_co,z)` and `rho_f(df) = exp(-df / l_co,f)` — a frequency- and location-dependent
  **covariance**, not a structured mean. Posterior values (PDF p. 10): `l_co,z ~ 49.8 m`,
  `l_co,f ~ 10.1 Hz`, `r = 0.82` — exactly the frozen project values used here.
- Nuance that must travel with any "zero mean" claim: zero mean applies in the **transformed** space. The
  multiplicative error in the original amplitude space is lognormal, so its arithmetic mean need not be 1.

**Conclusion:** a structured non-zero mean is not in this paper either.

### Allowed conclusion

**The requested learned frequency x location discrepancy mean is absent from these two papers.**
No literature-wide novelty gap is claimed; that would need a systematic review this run did not do.

### Reference-gate finding: the frozen in-project kernel is NOT byte-faithful to Schneider

Comparing the frozen `schneider_faithful.py` (and the card's frozen kernel) against Schneider Eqs. (19)–(21)
turned up two deviations that this run reports rather than hides:

| item | Schneider Eqs. (19)–(21) | frozen in-project / card kernel |
|---|---|---|
| spatial correlation form | `exp(-dz / l_co,z)` (exponential) | `exp(-dz / l_x)` — **matches** |
| frequency correlation form | `exp(-df / l_co,f)` (exponential) | `exp(-0.5 (df / l_f)^2)` — **squared-exponential, differs** |
| additive structure | `r rho_f(df) + (1-r) rho_z(dz)`, i.e. `r K_f (x) 1 1^T + (1-r) 1 1^T (x) K_z` | `r K_f (x) I_x + (1-r) I_f (x) K_x` — **differs** |

The structural difference matters for exactly the question being asked. Under Schneider's published form,
two different sensors at the *same* frequency line have correlation `>= r = 0.82`, so a zero-mean GP would
transfer strongly to a held-out channel. Under the card's `(x) I` form the same pair correlates only
`~ (1-r) = 0.18`, and the frequency-correlated part carries no spatial transfer at all.

This run follows the **card's** frozen kernel for all primary arms (the card forbids model-form edits), and
adds **SENS-4**, a preregistered sensitivity that re-runs the spatial and frequency families with Schneider's
published additive form on a decimated frequency grid. If E1-vs-E0 flips under SENS-4, the honest headline
is that the propagation finding is kernel-form dependent.
