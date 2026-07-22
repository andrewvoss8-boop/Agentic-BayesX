# Task Card E — staged StatFEM test of a learned frequency×location discrepancy mean

Status: **AUTONOMOUSLY DISPATCH-READY — NO HUMAN APPROVAL PAUSE**  
Authored: 2026-07-22  
Proposed isolated workspace: `artifacts/reports/shocksat_structured_discrepancy_codex_20260722/`  
No file in Task Card D's directory or proposed workspace may be changed.  
Compute: Stage 1 active-runtime cap 2 h; Stage 2 additional cap 6 h only when the automatic transition gate passes. Total active-runtime hard cap 8 h. Long jobs must be detached and resumable.

Once dispatched, execute from INIT through the applicable terminal state without requesting human approval. Checker-backed gates—not agent preference—choose whether to stop after synthetic work, close after Stage 1, or continue into joint Stage 2.

## Priority deliverable

Determine whether a **learned discrepancy mean whose conditional expectation varies with frequency and sensor location** adds transferable held-out value beyond:

1. the converged modal-parameter posterior plus per-drive gain; and
2. a zero-prior-mean frequency×location Gaussian process (GP) whose posterior is correctly conditioned at held-out points.

Do not conflate those two mechanisms. If GP conditioning alone moves the held-out center, report an implementation finding. If the learned mean adds value beyond GP conditioning, report a mean-model finding. If neither transfers, report a bounded negative result.

This is a runner prompt, not authority to revise the closure brief. Deliver proposed corrected wording in a separate Markdown file.

## Engineering decision

- Decision supported: whether the final ShockSat statistical twin should include a structured response-discrepancy mean, a conditioned zero-mean GP discrepancy only, or neither.
- Primary success metric: paired change in held-out median absolute FRF error in dB.
- Secondary metrics: continuous ranked probability score (CRPS; lower is better), 90% predictive coverage, 90% interval width, and measured shear-load proxy metrics where the existing mapping is valid.
- Allowed choices: the frozen arms and hyperparameter rules below; no model-form/mesh edits.
- Human judgment after completion: whether an artifact-backed positive effect is useful enough to adopt in the final twin or thesis. This judgment does not pause or change the runner's execution path.
- Wrong-question trigger: the residual depends primarily on unmodeled forcing, channel orientation, or channel-specific nuggets that cannot transfer from `(f, x)`; or the held-out design has too few independent units to resolve the success bar.

## Literature claim ceiling

Verify directly before coding:

- Febrianto et al. 2022: zero-mean discrepancy prior, spatial covariance only, quasi-static strain; nonsensor mean changes through the conditioned FE state, not an explicit frequency×location mean.
- Schneider et al. 2022: zero-mean Gaussian error in log-magnitude/phase with additive frequency×accelerometer-location correlation; transformed-space zero mean, not a structured mean.

Allowed conclusion: **the requested learned frequency×location mean is absent from these two papers.** Do not claim a literature-wide novelty gap without a broader review.

## Immutable source gate

Before writing fit output:

1. Create `source_manifest.json` with SHA-256, size, and role for every source file.
2. Hash the preregistration, split registry, mean-basis registry, quantity contract, and checker.
3. Prove the checker returns RED on an empty output directory.
4. Parse the frozen M0–M3 summaries and deterministically recompute at least three stored likelihood values or covariance eigenvalues. Do **not** rerun legacy non-converged TMCMC merely to reproduce stochastic R-hat/ESS.
5. Inventory actual data counts by drive, channel, response axis, location, region, frequency line, repeat/impact, and measured-versus-synthetic status. Stop if the card's required coordinates or response labels are missing.

## Quantity contract

Write `quantity_contracts.md` before fitting. For drive `d`, response channel `i`, frequency `f_s`, and reference accelerance `H_ref = 1 g/lbf`:

```text
q_meas(d,i,s)  = ln(|H1_meas(d,i,f_s)| / H_ref)                 [dimensionless]
q_fem(d,i,s;θ) = ln(|H1_fem(d,i,f_s;θ,ζ)| / H_ref)              [dimensionless]
r(d,i,s;θ)     = q_meas - q_fem - c_d                           [dimensionless]
r              = m(f_s,x_i,a_i) + u(f_s,x_i,a_i) + e
e              ~ Normal(0, σ_e²)
```

- `H1`: force-referenced accelerance magnitude, response acceleration divided by impact force.
- `x_i`: sensor coordinates in inches in the frozen ShockSat frame; state axes and origin.
- `a_i`: response-axis label. It is a categorical input, not a coordinate.
- `c_d`: per-drive scalar log-gain with `c_d ~ Normal(c_bar, tau_c²)`. Learn or condition `c_bar` and `tau_c` from training drives only. In leave-drive-out prediction, integrate over the held-out drive's prior-predictive `c_d`; never estimate it from that drive's response. In channel/band folds, infer `c_d` from the retained training portion of the same drive.
- `m = H beta`: learned structured conditional mean; `E[delta | beta] = H beta`, generally nonzero.
- `u`: zero-prior-mean residual GP with frequency×location covariance.
- `e`: observation/spectral-estimation error. State whether repeats exist and where independent realizations live.
- The structured mean and residual-GP hyperparameters are shared across drives; only `c_d` is drive specific. If the residual requires a drive×frequency term, the current `(f,x)` framing is inadequate and triggers the wrong-question stop.
- Report dB using `20/log(10) * q`. Never write “log of g/lbf.”
- State frequency range, line spacing, window, frame length, overlap, detrending, averaging axis, coherence treatment, and why the retained grid resolves QOI-driving features.

## Statistical model and the mean/covariance distinction

Use

```text
delta(f,x,a) = H(f,x,a) beta + u(f,x,a)
beta ~ Normal(0, Lambda_beta)
u ~ GP(0, K_fx)
```

The zero-centered prior on `beta` does not make the fitted conditional mean zero. But if `beta` is integrated out, its marginal contribution is `H Lambda_beta H^T`, a low-rank covariance. Therefore every report must show separately:

- `E[H_* beta | training]`: learned structured-mean contribution;
- `E[u_* | training]`: conditioned zero-mean-GP contribution;
- their posterior covariance and sum.

Beta may be marginalized for computation only if its conditional posterior is recovered exactly for prediction and plotting.

## Mean basis frozen from design information only

Construct basis functions before reading response residuals:

1. Frequency main effect: cubic B-splines in `log f`, with six degrees of freedom and boundary knots at the frozen analysis-band endpoints. Interior knots are equally spaced in `log f`. Save knots numerically.
2. Location main effect: five physical-region indicators plus five Gaussian radial basis functions. Choose radial-basis centers by deterministic k-medoids on standardized sensor coordinates using coordinates only; set spatial scale to the median nonzero center distance. Save centers and scale.
3. Response-axis main effect: frozen one-hot labels when more than one measured response axis is included.
4. Frequency×location interaction: tensor product of the frequency basis with the location basis. Do not interact with channel identity.
5. Channel-specific variation belongs in a nugget/heteroscedastic variance term. A random effect for a held-out channel has zero predictive mean and may not be credited as spatial transfer.

Within every training fold impose weighted ANOVA constraints:

- each main-effect block has weighted mean zero, separately within drive;
- the interaction has zero frequency margin and zero location margin;
- rank-deficient columns are removed by a deterministic tolerance frozen before fitting.

Record the maximum numerical constraint residual. A single grand sum-to-zero constraint is insufficient.

## Shared residual covariance

Start with the frozen Schneider-style additive kernel:

```text
K_fx = σ_u² [ r K_f(Δf; l_f) ⊗ I_x + (1-r) I_f ⊗ K_x(Δx; l_x) ]
```

Use the frozen project values (`l_f = 10 Hz`, `l_x = 2000 in`, `r = 0.82`) for the primary known-answer comparison. Add one preregistered sensitivity using physically bounded length scales learned on training data only. Do not use held-out responses to choose them.

## Arms — Stage 1 modular feasibility

Use retained draws from the converged modal-frequency posterior. Stage 1 is a **modular StatFEM prediction study**, not a jointly updated response posterior.

| Arm | Training likelihood | Held-out prediction | Question isolated |
|---|---|---|---|
| E0 | zero mean, `K_TT + σ_e²I` | force `K_*T = 0`; retain `K_**` as marginal uncertainty | Current-style marginal discrepancy: no residual transfer |
| E1 | identical to E0 | use `K_*T` in the exact Gaussian conditional | Does zero-mean GP conditioning transfer? |
| E2 | `H beta + u`, same `K_TT` | universal-kriging conditional; recover beta and `u_*` separately | Does a learned structured mean add value beyond E1? |
| E3 | as E2 with locally θ-orthogonal `H_perp` | same covariance and split | Does θ protection preserve prediction while reducing confounding? |

E0 and E1 must share exactly the same fitted training hyperparameters; only the train-to-test cross-covariance differs. E2 and E3 must use the same residual covariance as E1. This is the primary causal comparison.

Compute exact Gaussian conditionals and analytic coefficient posteriors. Do not invoke NUTS in Stage 1.

## Orthogonality contract

At the modal-posterior median `theta_0`, compute the response Jacobian `J = ∂q_fem/∂log(theta)` on each training grid and use the realized covariance metric `W = Sigma_train^-1`:

```text
P_perp = I - J (J^T W J)^+ J^T W
H_perp = P_perp H
```

- Use only the training grid and frozen `theta_0`.
- Record pseudoinverse tolerance and `||J^T W H_perp||`.
- This is local orthogonality, not a full reproduction of Plumlee's continuous-domain prior.
- If Stage 2 runs, evaluate orthogonality drift across posterior θ draws.

## Synthetic gates before measured fitting

Run at least 20 deterministic seeds for each case on the frozen reduced model and the actual split geometry:

1. S0 null: `m = 0`, GP + observation noise only. Controls false discovery and spurious 2 dB “wins.”
2. S1 in-basis: dish-region +3 dB bump over 80–140 Hz plus -2 dB low-frequency tilt.
3. S2 out-of-basis: a smooth continuous spatial gradient and off-knot frequency feature. Score predictive recovery, not exact beta recovery.
4. S3 confounded: a discrepancy component aligned with the strongest θ sensitivity plus an orthogonal component.

Required outputs:

- held-out mean-error, CRPS, coverage, and width by case;
- false-positive rate for E2/E3 versus E1 under S0;
- θ bias/coverage for E2 versus E3 in S3;
- posterior canonical correlations between θ sensitivity directions and mean-basis directions;
- coefficient coverage only for S1, where the injected function lies in the basis.

For S3, use the local linear-Gaussian response model `r = J delta_eta + H beta + u + e`, with `delta_eta = delta log(theta)` and its Gaussian prior taken from the modal posterior. Compute the joint `delta_eta, beta` posterior analytically; do not introduce a sampler merely for this gate.

Automatic synthetic acceptance, all frozen before measured fitting:

- S0 false-positive gate: no more than 1 of 20 seeds may make E3 cross the 2 dB/20% success rule versus E1.
- S1 recovery gate: E3 must cross the success rule with acceptable coverage in at least 16 of 20 seeds; its learned-mean 90% band must cover the injected mean at at least 85% of held-out grid points when aggregated by independent holdout unit.
- S2 robustness gate: the median E3-versus-E1 held-out error change across seeds must be favorable, and no more than 2 of 20 seeds may worsen median absolute error by more than 2 dB.
- S3 confounding gate: E3 must reduce median absolute `delta_eta` bias by at least 50% relative to E2, every calibrated θ direction must achieve at least 80% empirical 90% interval coverage across seeds, and the normalized orthogonality residual `||J^T W H_perp|| / (||J|| ||W H_perp||)` must be ≤1e-8.

If any synthetic gate is missed, STOP before measured fitting, write the failed thresholds and worst numbers to `automatic_decision.json`, finish the packet/checker/runtime artifacts, and report the result. No approval request is permitted.

## Held-out registry

Freeze split membership from design data before residuals are inspected.

1. Drive transfer: existing five leave-one-drive-out folds.
2. Spatial transfer: five spatial clusters made by deterministic k-medoids on coordinates; hold out one entire cluster at a time. Preserve axis/region balance where possible and document impossible strata.
3. Frequency transfer: five contiguous core bands spanning the analysis range. Exclude a 10 Hz guard on both sides of the held-out core from training. Score only the core.
4. Joint transfer: five preregistered spatial-cluster×frequency-core pairs selected by a hash-derived permutation; Stage 1 only. Stage 2 uses the drive, spatial, and frequency split families and may not expand the joint-transfer budget.

All covariance/mean hyperparameters are fixed a priori or fit inside each training fold. No outer-test response may tune knots, length scales, shrinkage, interval width, or calibration.

## Metrics and success rule

Score independent units at the drive, spatial-cluster, or contiguous-band level; do not treat dense frequency bins as independent replicates.

Primary E2/E3 versus E1 success bar, frozen from the accepted project decision:

- median held-out absolute-error reduction ≥2.0 dB with 90% coverage no worse by more than 0.02 absolute; **or**
- 90% interval width ≥20% narrower while held-out coverage is within 0.02 absolute of E1, with no test-set recalibration.

Also require lower paired CRPS in at least four of five folds in the relevant split family. Report paired fold effects, the worst fold, and a cluster/bootstrap interval using independent units. With only five folds, label uncertainty as weak even when the threshold is crossed.

Interpretation hierarchy:

- E1 beats E0, E2 does not beat E1: propagation/conditioning finding, not structured-mean support.
- E2 beats E1 and E3 preserves the gain with lower confounding: structured-mean support.
- E2 beats E1 but E3 loses it: improvement is entangled with FEM-parameter directions; YELLOW at best.
- No arm crosses the bar: negative transfer bound, still a valid result.

## Modal identifiability gate

Before any per-parameter claim:

1. Reproduce modal strain-energy fractions for all calibration modes and parameter groups.
2. Recompute the eigen-decomposition of `J^T Sigma^-1 J` at the **realized Stage 1 discrepancy floor**.
3. State how many parameter combinations clear prior precision and which raw parameters mix in strong/weak directions.
4. For a low-sensitivity parameter, use a finite perturbation to distinguish “in load path but below the discrepancy floor” from “out of load path.”

Do not turn non-converged/multimodal parameter posteriors into sampler-only diagnoses.

## Automatic transition after Stage 1

Always write `stage1_checkpoint.md` and machine-readable `automatic_decision.json`; do not stop merely to request review. The decision file must contain every threshold, observed value, pass/fail result, active runtime, projected Stage 2 runtime, and chosen terminal path.

Evaluate these rules in order and choose the first matching path:

1. **STOP_SYNTHETIC:** any synthetic gate failed. Do not fit measured data.
2. **STOP_CONFOUNDED:** E2 succeeds on measured data but E3 does not retain at least 80% of E2's median error reduction, or the frozen S3 bias/coverage rule is not satisfied. Close YELLOW at best; do not run joint updating.
3. **PROCEED_JOINT:** all synthetic gates passed; E3 versus E1 crosses the success rule in both spatial and frequency transfer; E3 has lower CRPS in at least four of five folds in both families; E3 retains at least 80% of E2's median error reduction; no gate is RED; Stage 1 active runtime is ≤2 h; and the measured Stage 2 projection fits inside the remaining 6 h.
4. **STOP_PARTIAL_MEAN:** E3 versus E1 crosses the success rule in exactly one of the spatial or frequency transfer families. Close with the component-specific finding; do not claim support for a joint frequency×location mean and do not run joint updating.
5. **STOP_PROPAGATION_ONLY:** E1 versus E0 succeeds in at least one primary transfer family, but none of the preceding rules matched. Close with an implementation/GP-conditioning finding; do not claim support for a frequency×location mean.
6. **STOP_NEGATIVE:** none of the preceding rules matched. Close with a negative structured-mean transfer bound and report any sub-threshold effects.

Missing evidence resolves to the applicable conservative STOP path. `automatic_decision.json` is immutable once any Stage 2 output exists.

## Stage 2 — automatic conditional joint Bayesian update

Run immediately and without approval only on `PROCEED_JOINT`.

- Joint arms: J1 = E1 mechanism and J3 = E3. E2 remains the Stage 1 confounding diagnostic; do not spend the joint budget on an unprotected J2 arm.
- Infer only the four previously supported stiffness groups unless the new realized-floor FIM supports more.
- Use the modal posterior as the response-stage prior and label the sequential/modular use of data.
- Use whole log-magnitude data, not peaks/features. Keep the forward model differentiable.
- NUTS/HMC, ≥4 chains, non-centered hierarchy where applicable.
- Convergence: max rank-normalized R-hat ≤1.05, min ESS ≥200 for reported parameters, divergences <2%; report every raw latent/hyperparameter.
- Retain per-chain draws. Non-converged intervals are YELLOW, labeled not trustworthy on every figure.
- Detached, resumable launches; pin BLAS threads for small dense operations.

If joint sampling remains multimodal/non-converged, do not erase the Stage 1 modular finding and do not call Stage 2 “NUTS active.” Report that joint θ–discrepancy learning was not established, complete all artifacts, and terminate without asking for a rerun or budget extension.

## Required artifacts

At FREEZE:

`priority_deliverables.md`, `question_framing.md`, `assumptions_ledger.md`, `quantity_contracts.md`, `data_inventory.json`, `split_registry.json`, `mean_basis_registry.json`, `preregistration.md`, `decisions_log.md`, `source_manifest.json`, `check.py`, `CHECKER.sha256`, `run_all.sh`, `runtime.json`.

At completion:

`packet.md`, `stage1_checkpoint.md`, `automatic_decision.json`, `closure_brief_correction.md`, `out/checker_report.json`, numeric tables, retained draws/conditionals, and figures generated by saved `.py` scripts.

The packet's first page must show the model equation, data counts, whole-curve likelihood choice, inferred/fixed/not-inferred quantities, split families, and the distinction among `E[H beta|train]`, `E[u_*|train]`, and parameter uncertainty.

## Figure requirements

Before plotting numeric data, read `.claude/skills/tufte-data-graphics/SKILL.md`; save scripts and run `tufte_lint.py`.

Minimum figures:

1. run-specific graphical model separating θ, structured mean, residual GP, and observation noise;
2. synthetic truth/data/recovery for S0–S3;
3. held-out FRF small multiples on log frequency, with mean and GP contributions separately visible;
4. paired fold effects for error, CRPS, coverage, and width;
5. θ–mean-basis sensitivity/FIM view and orthogonality residuals;
6. analytic beta priors plus labeled high-sample Monte Carlo sampling check.

Every figure names its run and split and prints invalidity/convergence status in its caption or on the figure.

## Checker minimum

The immutable checker must verify:

1. source and preregistration hashes unchanged;
2. RED-on-empty proof predates outputs;
3. dimensional log-ratio contract and dB conversion;
4. E0/E1 identical training fit with only `K_*T` toggled;
5. recovered mean and GP posterior contributions are stored separately;
6. basis centering and interaction-margin residuals;
7. contiguous band guards and no outer-test tuning;
8. S0–S3 gates and ≥20 seeds each;
9. modal strain energy plus realized-floor FIM before per-parameter claims;
10. immutable automatic decision with all numerical transition criteria, written before any Stage 2 output mtime;
11. all NUTS variables in convergence diagnostics if Stage 2 runs;
12. plot lint, legibility QA, evidence labels, and runtime accounting;
13. no predecessor workspace or frozen input changed;
14. overall status rule: any RED → RED; else any YELLOW → YELLOW; else GREEN.

## Expected honest outcome

Most likely: E1 improves some frequency-held-out predictions; E2 adds little spatial transfer because region explains only about 3.6% of the frozen residual variation and channel nuggets dominate. That expectation is not a target. A clean negative with a 2 dB/20% bound is a complete scientific result.

## Stop conditions

Stop and report RED/YELLOW as appropriate if:

- source hashes differ or data identities cannot be reconciled;
- coordinates/axes needed for location transfer are missing;
- the synthetic null produces frequent false “success”;
- test responses influence basis, hyperparameters, or interval calibration;
- active runtime reaches the stage cap;
- a requested claim would exceed the evidence status.

Every stop is a terminal scientific outcome for this dispatch. Finish the checker, packet, runtime, continuity logs, and closure-brief correction wording; never convert a stop condition into a human approval request.
