# Independent review of Task Card D

Date: 2026-07-22  
Reviewer: Codex  
Scope: supplied attachment `pasted-text.txt`, the original nine-page closure brief, the two named papers, and frozen in-project evidence. No science was executed and no predecessor artifact was modified.

## Bottom line

**Overall review status: RED as a dispatch artifact; GREEN as a research direction.**

The card asks the right scientific question and contains unusually good controls: held-out transfer rather than fitted-channel improvement, a synthetic confounding gate, an orthogonality arm, immutable preregistration, convergence checks, and a valid negative-result path. But four issues must be corrected before its results can support the intended claim:

1. It attributes GP-discrepancy posterior-mean propagation to Febrianto et al.; their published nonsensor predictive equation moves the mean through the conditioned FE state and adds the discrepancy at the prediction location as covariance.
2. It calls a zero-centered Gaussian coefficient vector, analytically marginalized from the likelihood, an “explicit non-zero mean.” Marginally this is a low-rank covariance term unless the conditional mean function and recovered coefficient posterior are kept explicit.
3. It takes the logarithm of a dimensional accelerance. The log must be of a ratio to a stated reference unit.
4. The held-out and orthogonality rules are not specified tightly enough to prevent correlated-band leakage, test-set interval recalibration, or θ–discrepancy aliasing.

The supplied attachment also labels itself **DRAFT — NOT APPROVED. Do not start** and leaves four human decisions open. A run from that exact attachment violates its own start gate. The later repository copy records decisions 2 and 3, but this review did not modify either copy or the separate run.

## Literature answer to the user's prompt

### Febrianto et al., *Digital twinning of self-sensing structures using statFEM*

The proposed non-zero discrepancy mean depending on both frequency and location was **not done in this paper**.

- The mismatch is explicitly `d ~ N(0, C_d)` in Eq. (11): zero prior mean. [`references/pdfs/digital-twinning-of-self-sensing-structures-using-the-statistical-finite-element-method.pdf`, PDF p. 7]
- Its kernel is squared-exponential in spatial coordinates `x` and `x'` in Eq. (12). There is no frequency input. [PDF p. 8]
- The setting is quasi-static bridge strain under a passing train. The index `k` in Eq. (24) is time/load state, and `gamma_k` scales the discrepancy covariance amplitude with load magnitude; it is not a mean function. [PDF p. 9]
- The FE posterior mean changes through conditioning, Eq. (21). At nonsensor locations the published predictive mean is `rho P_hat u_bar_|y`, while `C_d_hat` enters the predictive covariance in Eq. (28). [PDF pp. 9, 18]

Therefore Card D's `D2b` arm is a legitimate new GP-conditioning experiment, but “what Febrianto et al. do” is not a defensible description of that arm. A precise statement is: **Febrianto et al. use zero-mean, space-only model discrepancy and data-conditioned FE states; they do not use a non-zero frequency×location discrepancy mean, and their nonsensor equation does not show a kriged discrepancy-mean term.**

### Schneider et al., *Bayesian parameter updating in linear structural dynamics...*

Andrew's recollection is correct with one transformation-space qualifier.

- Schneider models `w = log|epsilon|` and phase `theta` jointly as a Gaussian with zero vector mean in Eq. (18). [`references/pdfs/Bayesian parameter updating in linear structural dynamics with frequency transformed data using rational surrogate models.pdf`, PDF p. 5]
- Eqs. (19)–(25) give an additive correlation structure in frequency separation and accelerometer-location separation. This is frequency- and location-dependent **covariance**, not a structured mean. [PDF p. 5]
- “Zero mean” applies to log-magnitude and phase error. The multiplicative error in the original amplitude space is lognormal, so its arithmetic mean need not equal one. That nuance should travel with any zero-mean claim.

The defensible novelty statement is narrow: **the requested non-zero frequency×location mean is absent from the two papers examined.** Calling it a literature-wide “genuine gap” requires a broader systematic search than the prompt requested.

## Closure-brief finding

The original brief is visually clean across all nine rendered pages: no clipping, overlap, broken tables, or unreadable figures were found. Its technical inventory, however, says the “Schneider-style surrogate” is unimplemented on page 5 and again calls it future work on page 7. The repository contains a Schneider covariance implementation and stored M2/M3 runs. The brief therefore conflates two components:

- implemented: additive frequency×space error covariance in log-FRF magnitude, with non-converged M2/M3 results;
- unimplemented: Schneider's rational FRF surrogate and a validated full method matching the paper end to end.

Recommended correction for a future brief revision:

> A Schneider-style additive frequency×space covariance was implemented for log-FRF magnitude, but its M2/M3 TMCMC runs did not converge and the discrepancy scale ran to about 12.4. Schneider's rational FRF surrogate and a validated end-to-end reproduction were not implemented.

## Gate-by-gate review of Card D

| Gate | Status | Review |
|---|---|---|
| Question and decision | GREEN | It asks whether a structured response discrepancy can move the held-out predictive center and sharpen intervals. A negative bound is accepted. |
| Literature: two named papers | YELLOW | The main yes/no conclusions are right. The Febrianto propagation attribution and literature-wide novelty claim are too strong. |
| In-project prior art | GREEN | The stored M0–M3 diagnostics, spatial `R² = 0.036`, and hard-channel nugget contrast agree with the frozen JSON artifacts. |
| Mean-versus-covariance contract | RED | With `beta ~ N(0, Lambda)` and beta analytically marginalized, `H Lambda H^T` is a covariance contribution. The card must define `delta = H beta + u`, retain `E[H beta | training]` as the learned mean contribution, and compare it with `E[u_* | training]`. |
| Quantity contract | RED | `log |H|` of a quantity carrying `g/lbf` units is undefined physically. Use `log(|H| / H_ref)`, with `H_ref = 1 g/lbf`, or use dB directly. |
| Isolation of mechanisms | YELLOW | D2b, D3–D6 change several ingredients at once. A paired design should keep the training covariance fixed and toggle prediction cross-covariance first, then add the mean basis under that same covariance. |
| Location dependence | YELLOW | Region effects are a coarse categorical location model. A channel random effect cannot transfer to an unseen channel; its held-out posterior mean is zero. Continuous coordinates, response axis, and region must be contracted explicitly. |
| Centering constraints | YELLOW | A single grand sum-to-zero condition does not stop aliasing with per-drive gain or main effects. Center within each training fold/drive and impose zero frequency and location margins on the interaction basis. |
| Held-out bands | RED | “Leave-band-out” has no block widths or guard bands. With a 10 Hz correlation length, adjacent bins leak nearly the same residual realization. Contiguous blocks and training exclusion guards must be frozen. |
| Equal-coverage width | RED | “At equal coverage” is undefined and could cause test-label recalibration. No interval rescaling may use outer-test responses; freeze a coverage tolerance or use a nested calibration subset. |
| Synthetic recovery | YELLOW | One injected signal aligned with the proposed basis is too easy. Add a null false-positive case, an in-basis case, an out-of-basis smooth case, and a θ-aligned confounding case over multiple seeds. |
| Orthogonality | YELLOW | “Reuse M3 machinery” is insufficient. The stored M3 uses an unweighted Euclidean projection at one reference θ. The card must state the inner product, reference θ, training design, and how local orthogonality drift is checked over the posterior. |
| Modal identifiability | YELLOW | Synthetic θ coverage and θ–beta correlation are useful, but the repository rules also require modal strain-energy fractions and the eigenstructure of `J^T Sigma^-1 J` at the realized discrepancy floor before per-parameter claims. |
| Legacy known answers | YELLOW | Re-running non-converged stochastic M1–M3 chains is a poor deterministic gate. Hash and parse their frozen summaries; verify selected likelihood values deterministically. Do not require stochastic diagnostics to reproduce exactly. |
| Arm count and compute | RED | The table has eight arms (`D0`, `D1`, `D2`, `D2b`, `D3`, `D4`, `D5`, `D6`), not “six.” Eight arms × several holdout families × ≥4 NUTS chains is not credibly bounded by eight active hours without a measured smoke benchmark. |
| Sampler honesty | GREEN | It correctly reserves “NUTS/HMC active” for converged new work and labels TMCMC legacy. |
| Checker and immutability | GREEN | Hashes, RED-on-empty, retained per-chain draws, plot QA, and frozen preregistration are strong. |

## Why the alternative card is staged

The existing whole-FRF likelihood is multimodal, while the scientific uncertainty is more basic: can a learned discrepancy transfer to a held-out frequency/location at all? The cheapest honest order is:

1. Hold the converged modal-parameter posterior fixed and run exact Gaussian conditioning on residuals.
2. With identical training covariance, compare no cross-point conditioning against zero-mean GP conditioning.
3. Add a learned structured mean under the same covariance and recover its conditional posterior contribution.
4. Only if the structured mean adds held-out value beyond GP conditioning, attempt a joint NUTS θ update.

That sequence produces an interpretable implementation finding even if joint response-level sampling remains non-converged.

## Review status

**RED until the four red conceptual/design issues above are fixed.** The independent runner card in this directory incorporates those fixes and is autonomously dispatch-ready: after dispatch, immutable numerical gates choose synthetic stop, Stage 1 closure, or joint Stage 2 without a human approval pause. It has not been dispatched by this review task.
