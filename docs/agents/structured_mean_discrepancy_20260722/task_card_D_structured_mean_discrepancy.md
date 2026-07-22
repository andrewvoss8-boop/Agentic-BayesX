# Task Card D — StatFEM with a STRUCTURED (non-zero-mean) discrepancy m(f, x)

Status: **DRAFT — NOT APPROVED. Do not start.** Decisions **2 and 3 ANSWERED by Andrew 2026-07-22** (recorded at the bottom); decisions **1 (scope vs calendar)** and **4 (closure-brief correction)** are still OPEN. The card stays unapproved until they are answered, because decision 1 determines which arms exist.
Lead: Claude Code · Proposed workspace: `artifacts/reports/shocksat_structured_mean_discrepancy_20260723/`
Proposed compute budget: **HARD CAP 8 h active runtime.** Detached-launch gate (AGENTS.md Compute) applies to every sampler run.

## Task

Test whether a model-discrepancy term whose **mean** varies with frequency and sensor location — e.g. "the FEM is +3 dB low at the dish sensors between 80 and 140 Hz" — can do what the delivered ShockSat statFEM could not: **move the posterior predictive mean toward held-out measured FRFs**, and **narrow the prediction bands at equal coverage**.

## Why This Matters

The closure brief names exactly two failures and, in Andrew's comment C3, exactly one untested escape route:

- The posterior mean cannot move, because the only converged likelihood sees modal frequencies (no channel-specific amplitude/participation mechanism, 4 of 9 prior-whitened directions learned).
- The bands stay unusably wide (1.51× / 2.30× FEM+6 dB), because the delivered discrepancy was a **marginal variance** — it buys coverage only by being broad everywhere.
- A location- and frequency-structured **mean** discrepancy was never tested, so its failure is **not established**. The brief currently has to concede that as an open hole.

This card closes the hole with a measured answer — positive or negative. A negative answer with an effect size and a noise floor is a valid closure contribution.

## Controlling prior work — read BEFORE designing anything

### Literature position (checked 2026-07-22, lead)

| Source | Discrepancy mean | Structure | Verdict for this card |
|---|---|---|---|
| Febrianto, Butler, Girolami & Cirak 2022, *Digital twinning of self-sensing structures using statFEM* (`references/pdfs/digital-twinning-of-...pdf`) | **Zero-mean prior**, Eq. (11): `d ~ N(0, C_d)` | Squared-exponential in **space only**, Eq. (12); Eq. (24a) adds a per-time-instant load-magnitude scale `γ_k`. Quasi-static strain under a train pass — **no frequency dimension at all** | **Not done there.** Closest element is the `γ_k` amplitude scaling, which is a variance scale, not a mean |
| Schneider, Papaioannou & Straub 2022, MSSP 166:108407 (ref [11]) | **Zero-mean**, Eq. (18): `[w; θ] ~ N(0, ...)` on log-magnitude and phase | Correlated in **both space and frequency**, Eqs. (19)–(21): additive split `ρ = r·ρ_f(Δf) + (1−r)·ρ_z(Δz)` | Andrew's recollection is **correct**: frequency- and location-dependent, but zero mean and in the **covariance**, not the mean |
| Girolami et al. 2021 statFEM (`references/pdfs/statFEM.pdf`) | Zero-mean, stated explicitly | Spatial kernel | Zero mean |
| Latent-force misspecification paper (`references/pdfs/probabilistic digital twin ... latent force.pdf`) | Zero-mean GP latent forces | Temporal kernel | Zero mean |
| Kennedy & O'Hagan 2001 (ref [12]) | GP discrepancy **with a regression mean** `h(x)ᵀβ` | Generic input space | The canonical precedent for the mean form proposed here |
| Plumlee 2017 (`references/pdfs/Bayesian_calibration_of_inexact_computer_models_Plumlee_2017.pdf`) | Bias prior constrained **orthogonal to ∂(model)/∂θ** | — | The fix for the confounding this card will otherwise create |
| Brynjarsdottir & O'Hagan 2014 (ref [6]) | — | — | Why an unconstrained flexible discrepancy corrupts θ |

**Conclusion: a non-zero-mean discrepancy that is a function of BOTH frequency and location has not been done in either paper.** It is a genuine gap. It is also the gap where identifiability breaks, which is why it is not free.

### This project's own prior art (frozen artifacts — must be reproduced, not re-derived)

1. **A Schneider-style zero-mean freq×space discrepancy IS already implemented here**, contrary to the closure brief's line "Schneider-style surrogate … unimplemented" (see Open Decision 4). Code: `artifacts/reports/shocksat_modelclass_L5_20260619/code/schneider_faithful.py`. Results: `artifacts/reports/statfem_real_validation_20260617/out/tmcmc_faithful_M{0,1,2,3}_ident4_n8.json`, 8 observed channels × 173 band frequencies, 4 free stiffness groups, TMCMC ×4 runs.
   - **M0** (no discrepancy): converged, R̂ 1.0002, ESS 4716, gain c 5.916.
   - **M1** (iid marginal): R̂ 1.041, ESS 47 — **not converged**, σ_w 1.86.
   - **M2** (Schneider additive freq×space, zero mean): R̂ 2.577, ESS 0.71 — **badly non-converged**, σ_w ran to **12.37** against a prior centred at 1.726. This is the discrepancy-variance runaway.
   - **M3** (Plumlee-style orthogonal projection): R̂ 1.112, ESS 17 — **not converged**, σ_w 12.60, θ pinned near M0.
   All four are YELLOW-or-worse and must be restated that way.
2. **Location is a weak predictor of the residual.** `shocksat_modelclass_L5_20260619/out/spatial_reanalysis.json`, n=77: region-categorical R² = **0.036**; bolted-joint region mean |residual| 12.3 dB vs bulkhead 7.3, dish 9.0, impact 8.0, strut 7.5; Spearman |residual| vs distance-to-nearest-feature −0.094.
3. **The residual is dominated by a channel-specific nugget.** `out/discrepancy_diagnostic.json`, n=77: global gain c 6.350, median |residual| **6.596 dB**, p90 15.56 dB; the 8 a-priori-hard accelerometers average **17.452 dB** vs **6.535 dB** for the rest. Decisions log D13/D21 concluded a spatial-GP discrepancy would **not transfer** to unmeasured channels for this reason.

**Therefore the honest prior expectation is: the frequency part of `m` will transfer across channels better than the location part transfers across space.** The card must be designed to measure that split, not to prove a positive.

### A correction that must appear in the packet's method summary

A **zero-mean GP prior** on the discrepancy does **not** mean the discrepancy has zero **posterior** mean. In Febrianto/Girolami, `d ~ N(0, C_d)` is a prior; the posterior `d|y` is non-zero, and it is precisely what pulls the predicted true response onto the data at sensor locations and — through `C_d` — at nearby unsensored locations. ShockSat's mean did not move because the delivered discrepancy was a **marginal variance with no correlation carried to the prediction point**, not because zero-mean priors are incapable of moving a mean.

So this card tests **two separable things** and must keep them apart in every table and figure:

- **(a) Explicit structured mean** — a parameterized bias `m(f, x)` with its own prior (Kennedy–O'Hagan `h(x)ᵀβ` form).
- **(b) Correct propagation** — a zero-mean-prior GP discrepancy whose **posterior mean is actually propagated** to held-out channels/bands via the freq×space kernel (what Febrianto et al. do, and what ShockSat did not do).

If (b) alone closes most of the gap, **that is the finding**, and it is a finding about implementation, not about model form.

## Quantity contract (write to `quantity_contracts.md` before any fitting)

For drive `d`, channel `i` at location `x_i`, frequency line `f_s`:

```
y_{d,i,s} = log |H_meas(f_s, x_i; d)|                     [log of accelerance, g/lbf]
mu_{d,i,s}(theta) = log |H_FEM(f_s, x_i; theta, zeta)|    same units, reduced model
y = mu(theta) + c_d + m(f_s, x_i) + e ,   e ~ N(0, Sigma)
```

- `c_d` — per-drive scalar gain, **already in the existing model** (frozen medians 5.92–6.68). This is the current model's only non-zero mean: a constant. This card replaces "constant" with "a function of f and x".
- `m(f, x)` — the new structured mean, **sum-to-zero constrained** over the observed (f, x) grid so it cannot silently duplicate `c_d`. State the constraint and show it holds numerically.
- `Sigma` — start from the frozen M1 iid form (`sigma_meas² + sigma_w²`, `sigma_meas` = 0.15 frozen), then the frozen M2 Schneider additive form with `l_f` = 10 Hz, `l_z` = 2000 in, `r` = 0.82.
- Units: everything in natural log of g/lbf; report figures in dB (20·log10) and state the conversion once. Do not mix.

## Arms (pre-register in `preregistration.md`, hashed, BEFORE any fit output exists)

| Arm | Mean model | Purpose |
|---|---|---|
| D0 | none (M0) | frozen known-answer reproduction |
| D1 | none, iid marginal (M1) | frozen known-answer reproduction |
| D2 | none, Schneider zero-mean freq×space (M2) | frozen known-answer reproduction; the runaway baseline |
| D2b | as D2 but posterior discrepancy mean **propagated** to held-out points via the kernel | isolates item (b) above — the implementation fix |
| **D3** | `m(f) = Σ_k β_k b_k(f)`, B-spline in log f, 6–8 knots, shared across channels | frequency-only structured mean |
| **D4** | `m(x)` = 5 physical region effects (from `spatial_reanalysis.json`) + channel-level hierarchical effect | location-only structured mean |
| **D5** | `m(f,x) = Σ_{k,r} β_{k,r} b_k(f) a_r(x)` — region-specific frequency shapes | **headline arm**; directly encodes Andrew's C3 example |
| D6 | D5 with the Plumlee orthogonality constraint (project `m` off the span of `∂mu/∂theta`) | protects θ from being absorbed; reuse M3 machinery |

**Tractability rule (this is what makes the target samplable):** `m` is **linear in β** with a Gaussian prior, so β is **marginalized analytically**. NUTS then sees only θ (the 4 identified groups), `c_d`, and a handful of variance/length hyperparameters. This directly addresses the A4 diagnosis (~10 local maxima in the iid whole-FRF profile) rather than hoping a bigger sampler budget fixes it. β posteriors are recovered from the conditional Gaussian afterwards so `m(f,x)` can be plotted in dB — **that plot is the headline figure.**

Sampler statement (AGENTS.md): **NUTS/HMC** for all new arms, ≥4 chains, non-centered hierarchical parameterization, full convergence gate over **all** sampled variables. TMCMC appears only where it is needed to reproduce the frozen M0–M3 arms; label those as **legacy reproduction**, not as this card's method.

## Known-answer gates (all must pass before any new arm is interpreted)

1. Reproduce frozen M0/M1/M2/M3 headline values from the frozen configs: gain `c`, θ medians, σ_w, log-evidence, and the diagnostics above. Any mismatch ⇒ STOP and report.
2. Reproduce `discrepancy_diagnostic.json`: n=77, gain 6.350, median |res| 6.596 dB, hard 17.452 vs rest 6.535 dB.
3. Reproduce `spatial_reanalysis.json`: region-categorical R² 0.036, bolted-joint 12.3 dB.
4. **Synthetic recovery gate — mandatory, run BEFORE touching measured data, and it is pass/fail for the whole card.** On the frozen reduced model: pick θ\*, inject a known `m*(f,x)` (a +3 dB bump on the dish region over 80–140 Hz **plus** a −2 dB broadband low-frequency tilt), add noise at the frozen `sigma_meas`. Report (a) is θ\* recovered inside its CI, (b) is `m*` recovered inside its CI, (c) how much **θ bias** appears in D5 without the orthogonality constraint versus D6 with it, (d) posterior correlation between θ and the β coefficients. This is the Brynjarsdottir–O'Hagan confounding test. If θ is not recoverable on synthetic data, the measured-data arms are not interpretable and the card reports that as its result.

## Held-out evaluation — this is what decides the card

Splits, **pre-registered before fitting**, from the frozen `mc_cache.npz` / multiref caches:
- (i) **leave-channel-out** → does the location part of `m` transfer in space?
- (ii) **leave-band-out** → does the frequency part of `m` transfer across frequency?
- (iii) leave-drive-out (existing convention).
- (iv) joint channel×band cell hold-out (the hardest, and the one that matters for a twin).

Metrics at held-out points, against FEM+6 dB and against the frozen D1/D2 arms, reusing the Task Card A CRPS convention **and its documented sensitivity to the envelope convention**:
- median |error| in dB of the posterior predictive **median** — *does the mean move?*
- 90% interval width, and coverage.
- CRPS (continuous ranked probability score — a proper score generalizing absolute error to whole distributions; lower is better).

**Proposed pre-registered success bar (needs Andrew's sign-off — Open Decision 2):** a structured-mean arm "works" on held-out channels if it reduces median |dB error| by **≥ 2 dB** versus the parameter-only posterior **without losing coverage**, **or** narrows the 90% band by **≥ 20 %** at equal coverage. Anything smaller is reported as a negative result **with its effect size and the four-fold noise floor beside it** — never as a trend.

## Honesty clauses (non-negotiable)

- Fitting `m` on measured channels and showing a better fit **on those same channels** is **not** the deliverable and must never be reported as one.
- The project's own frozen diagnostics predict weak spatial transfer (R² 0.036, channel-specific nugget). Report the transfer test even when negative.
- Every non-converged arm is YELLOW at best, with worst-case R̂/ESS printed **on the figure** next to its intervals.
- Do not change split rules, arms, or the success bar after seeing any result. The preregistration file is hashed at FREEZE.

## Not Allowed

- Modifying, moving, or copying any frozen input; touching any predecessor workspace.
- New physics candidates, mesh/model-form search, or formulation calibration (that is a different thread).
- Presenting `m` fitted at a channel as a prediction *for that channel*.
- Editing `check.py` / `CHECKER.sha256` after the SHA-lock.

## Required workspace files (write at FREEZE, before science)

`priority_deliverables.md` · `question_framing.md` · `assumptions_ledger.md` (all priors, knots, lengths, units) · `quantity_contracts.md` · `preregistration.md` (hashed) · `decisions_log.md` · `source_manifest.json` (SHA-256 of every frozen input) · `code/` (all scripts as `.py`, figure scripts tufte-linted) · `check.py` + `CHECKER.sha256` with proven RED-on-empty · `run_all.sh` · `runtime.json`.

## Checker must verify (minimum)

1. All frozen-input hashes unchanged end-to-end.
2. Known-answer gates 1–3 reproduced before any new-arm output exists.
3. Synthetic recovery gate 4 present, with the θ-bias comparison D5 vs D6 and the θ–β posterior correlation.
4. `preregistration.md` hash recorded **before** the first fit output's mtime.
5. Per-arm convergence diagnostics for **all** sampled variables; per-chain draws retained.
6. Sum-to-zero constraint on `m` verified numerically.
7. Held-out tables carry the measured-vs-synthetic evidence labels (shear = measured; normal-Z = synthetic self-consistency, NOT validation).
8. Figures pass tufte lint + legibility QA; each names its source run and flags non-converged content.
9. `runtime.json` active total within the approved cap.

## Expected result status

Realistic expectation: **YELLOW overall.** D3 (frequency-only) is the most likely to converge and to transfer. D5 is the scientifically interesting arm and the most likely to hit the θ–`m` confounding wall; D6 is its guardrail. A clean, gated negative on spatial transfer is a publishable closure statement and is an acceptable outcome of this card.

## Open decisions for Andrew (card cannot start until answered)

1. **[OPEN] Scope vs calendar.** Less than a month remains. Full card ≈ 8 h compute plus write-up. A **feasibility-only** variant — synthetic recovery gate 4 plus arm D3 only, ~1 day — would let the brief say "we tested it, here is the measured bound" instead of "never tested." Which one?
2. **[ANSWERED 2026-07-22 — Andrew] Success bar = 2 dB / 20 %,** as pre-registered in the card text: a structured-mean arm "works" on held-out points if it cuts median |dB error| by ≥ 2 dB without losing coverage, **or** narrows the 90 % band by ≥ 20 % at equal coverage. The measured four-fold noise floor is *not* the bar; it is still reported **beside** every effect size so a sub-floor "win" cannot be read as real. This bar is frozen into `preregistration.md` at FREEZE and may not change after any result is seen.
3. **[ANSWERED 2026-07-22 — Andrew] D6 (Plumlee orthogonality) is IN SCOPE.** The θ-protection arm is built, not deferred, and the D5-vs-D6 θ-bias comparison stays a mandatory part of synthetic recovery gate 4.
4. **[ANSWERED 2026-07-22 — Andrew: DEFER] Closure-brief Schneider correction.** The brief says the Schneider-style correlated freq/space error model is "unimplemented" / "not a completed method here". `schneider_faithful.py` implemented exactly that model, and M2/M3 ran (non-converged, σ_w runaway to ~12.4); only the **rational surrogate** half is genuinely unimplemented. **Decision: do NOT rebuild the brief now — correct it once, together with this card's result, so the statement is made correctly a single time.** The defect and its accepted consequence are logged as F5 in `shocksat_closure_report_fable_20260722/decisions_log.md`; no delivered artifact was changed. **Card D therefore inherits a deliverable: its report must supply the corrected wording for the brief.** ⚠️ Reading of a one-letter reply "b" — Andrew to confirm or overrule.

### Human decisions recorded (do not delete; source of truth over chat)

| Date | Decision | Effect on the card |
|---|---|---|
| 2026-07-22 | Success bar = **2 dB median-|error| reduction OR 20 % band narrowing at equal coverage** (decision 2) | Pre-registered verbatim; noise floor reported alongside, not as the bar |
| 2026-07-22 | **D6 in scope** (decision 3) | Six arms D0–D6 stand as written; θ-bias D5-vs-D6 stays mandatory in gate 4 |
| 2026-07-22 | **Defer the closure-brief Schneider correction** (decision 4; reading of "b", to be confirmed) | Brief not rebuilt now; Card D's report must deliver the corrected wording. Defect logged as F5 in the fable workspace |
