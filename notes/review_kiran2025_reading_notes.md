# Reading notes — Kiran et al. (2025), "Review of Bayesian FE model updating techniques for structural systems"
*Probabilistic Engineering Mechanics 80, 103761. Organized from Andrew's highlights + questions, 2026-06-06.*

Notation used throughout (ML/stats symbols defined; structural-dynamics terms assumed):
- `D` = observed data; `θ` = model parameters being updated (e.g., element stiffness, material params).
- `p(D|θ)` = likelihood (how probable the data are for a given θ); `p(θ)` = prior; `p(θ|D)` = posterior.
- `Ŷ(ω)` = measured response spectrum; `U(ω,θ)` = model response; `Ĥ(ω)` = measured FRF; `H(ω,θ)` = model FRF; `F̂(ω)` = measured input/force spectrum.
- `Γ` = error covariance matrix (the "weight"); `(·)^H` = conjugate transpose; `(·)^{-1}` = inverse.
- `n_o` = number of observed DOF (outputs); `n_ω` = number of frequency lines; `σ²` = scalar prediction-error variance; `tr(·)` = trace.

---

## A. Likelihood formulations (Section 4.2 FRF, and the error-PDF logic)

### A1. The "simple" complex Gaussian FRF likelihood — Eqs. 18 & 20
- **Eq. 18** (response data): `ln p(D|θ) = -½ Σ_k [Ŷ(ω_k) − U(ω_k,θ)]^H Γ^{-1} [Ŷ(ω_k) − U(ω_k,θ)]`.
- **Eq. 19–20** (Fathi et al.): additive error `Ĥ(ω) − H(ω,θ) = e`, with `e` a circular complex Gaussian. Then `ln p(D|θ) = -½ Σ_k [Ĥ−H]^H Γ^{-1} [Ĥ−H]`.
- **Plain meaning:** this is **weighted least squares in complex form**. Take the difference between measured and modeled FRF, square it (via `[·]^H Γ^{-1} [·]`, the Mahalanobis/quadratic form), weight by the inverse error covariance `Γ^{-1}`, sum over frequencies. Frequencies assumed independent (so the band likelihood is a product → sum of logs).
- **Key limitation stated in the paper:** the circular-complex-Gaussian assumption is valid **only if the forcing is deterministic**. This is the "measure of difference" family.

### A2. The "proper for random input" likelihood — Eqs. 21–23 (Yan et al. [183]) — *the eqs you had no idea about*
The whole point: an FRF is a **ratio** `Ĥ = Ŷ/F̂` of two noisy spectra (output ÷ input). The ratio of two complex Gaussians is **not** Gaussian — it has heavier (polynomial) tails. So instead of pretending the residual is Gaussian (Eq. 20), Yan et al. use the correct distribution.
- **Eq. 21 — the FRF ratio distribution.** For the augmented vector `H_ω = [1, H(ω)^T]^T` (the leading `1` handles the ratio normalization),
  `p(h_ω) = n_o! / (π^{n_o} |det Σ_ω|) · (h_ω^H Σ_ω^{-1} h_ω)^{-(n_o+1)}`,
  where `Σ_ω = blockdiag(E(S_Fω), E(S_Yω))` collects the **expected force and response spectral densities**. The `(quadratic form)^{-(n_o+1)}` shape is the heavy-tailed signature of a ratio (multivariate Cauchy/t-like), vs. the `exp(-½ quadratic)` of a Gaussian.
- **Eq. 22** = the band log-likelihood = sum over frequencies of `ln` of Eq. 21 (product over independent frequency lines).
- **Eq. 23 — the cheap vectorized closed form** (so you don't re-evaluate the full likelihood naively):
  `ln p(D|θ) = -Σ_k ( n_o ln σ² + ln[1 + tr(G_H)/σ²] + (n_o+1) ln[1 + (1/σ²) Ĥ^H {I/σ² + tr(G_H)}^{-1} G_H Ĥ] )`,
  with `σ²` = prediction-error variance and `G_H = H(ω;θ)·H(ω;θ)^H` = rank-1 outer product of the model FRF vector (so `tr(G_H) = Σ|H_i|²` = squared magnitude of the predicted FRF).
- **Plain meaning:** the three terms are (1) a normalization `n_o ln σ²`, (2) a forcing/response-uncertainty penalty `ln[1 + tr(G_H)/σ²]`, (3) the actual data-vs-model misfit `(n_o+1) ln[...Ĥ...G_H...Ĥ...]`. The `ln[1+...]` structure (instead of a bare quadratic) is what encodes the heavy-tailed ratio distribution.
- **Why it matters to us:** Eqs. 21–23 are the **right likelihood when the input is random/uncertain** — directly adjacent to our unknown-stochastic-forcing / OMA novelty direction (research_backlog). Caveat: Yan still **measures** the input (`Ĥ=Ŷ/F̂`), so it's input–output, not output-only. True unknown forcing (OMA / input-state / force-ID) needs to go a step further (spectral-density/transmissibility or a forcing model).

### A3. Where the likelihood comes from in general — Simoen et al.
- The likelihood is built from the **probabilistic models of measurement + modeling error**. Simoen: the likelihood is the **convolution** of the measurement-error PDF and the modeling-error PDF. If both are **additive**, they combine into one **"model prediction error"** and the likelihood is the PDF of that.
- **Stated caveat (important):** the additive-error assumption **breaks down when modeling error is large** — adjusting θ only partly compensates, so a fundamentally wrong model can't be rescued by parameter tweaks. (This is exactly our round-3 *missing-modes* finding: `sigma_e` had an irreducible floor because the coarse model can't represent the truth's higher modes.)

### A4. "Weighted Gaussian distribution" — your question
A Gaussian likelihood where each residual is **weighted by the inverse covariance** (`Γ^{-1}` in Eqs. 18/20, `1/σ²` in Eq. 23). The weight = **precision** (1/variance):
- Measurements you trust more (small variance) get more weight; noisy ones get less.
- Off-diagonal terms encode **correlation** between channels/frequencies (so correlated points aren't double-counted).
- It's the probabilistic version of **weighted least squares**: maximizing a weighted Gaussian log-likelihood = minimizing `Σ wᵢ·residualᵢ²`. A flat/identity weight (`Γ=I`) = ordinary least squares = treats every point as equally trustworthy and independent.

---

## B. Samplers / solution methods (Section 3.4.2 + tables)
- **MLE / asymptotic approximation** (Beck–Katafygiotis): point estimate + Gaussian (Laplace) approx around it. Cheap; misses non-Gaussian/multimodal posteriors.
- **Gibbs sampling** — good with conjugate priors (closed-form conditionals).
- **HMC / TMCMC / hybrid HMC+TMCMC** (Cheung & Beck, Beck): gradient-based + tempered; TMCMC also gives **evidence**.
- **S²HMC (Separable Shadow Hybrid Monte Carlo)** (Boulkaibet [121]) — your highlight: an HMC variant that samples using a *separable shadow Hamiltonian* (a slightly modified energy that the leapfrog integrator conserves more exactly), giving **higher acceptance at larger step sizes without extra tuning parameters**. Niche refinement of HMC; NUTS's auto-tuning addresses the same pain differently. (We discussed this in the sampler-choice thread — S²HMC not justified for us over NUTS.)
- **Adaptive BUS-SuS** (Schneider, Betz et al.): reframe posterior sampling as a structural-reliability rare-event problem; subset simulation climbs there in stages; "adaptive" auto-estimates the BUS constant `c`. Gives **evidence** too. Gradient-free → good for surrogate/non-differentiable models. (Full write-up in the earlier sampler thread.)
- **Nested sampling** (Ping et al.) — evidence-focused sampler.
- **Kalman filter / EKF / UKF** (Cheung & Beck [145], Yuen & Mu, Ramancha) — your "Kalman filter for BU??": yes — recursive/**sequential** Bayesian estimation. Treat parameters (and/or state) as things to update each time step; EKF linearizes, UKF uses sigma-points for nonlinearity. Natural fit for **real-time / online digital-twin** updating; joint state–parameter estimation. Conceptually the time-domain, sequential cousin of batch MCMC.
- **MABC + BFGS** (Sun & Betti) — your highlight: a *deterministic/optimization* hybrid, not Bayesian sampling. Modified Artificial Bee Colony (a population/swarm global search) hands off to BFGS (a gradient quasi-Newton local optimizer) — global-then-local optimization for high-dim updating. Finds a point estimate, not a posterior.

---

## C. Identifiability & likelihood singularities (your "does MY likelihood have singularities?")
- **Beck–Katafygiotis identifiability classes** (from the set of MLEs):
  - **Globally identifiable** = a single optimal θ.
  - **Locally identifiable** = a finite number of optima.
  - **Unidentifiable** = a **continuum** of optima (a ridge/manifold of equally-good solutions).
- **Observed DOF matter:** the number and spatial distribution of measured DOF sets the identifiability pattern (too few sensors → unidentifiable).
- **The paper's singularity passage:** high-dim / over-parameterized models + incomplete data → convergence problems; the likelihood can have **singularities (nonsensical maxima)** where **variance parameters run to 0 or ∞**, and runs get trapped near local maxima depending on initialization.
- **Answer to your question — YES, ours did, in round 3:**
  - The `sigma_d ↔ sigma_e` **ridge** = the **unidentifiable continuum** class (the discrepancy size and noise size trade off; data only constrain their sum).
  - `sigma_d → 1.33` (≈6.6 prior SDs out, implying ~14× strut-to-strut stiffness spread) = the **variance-parameter-runs-to-extreme** singularity, live.
  - Symmetric-strut **multimodality** = the local-maxima-by-initialization case.
  - Honest nuance: part of ours was *also* **missing-modes model-form error** (A3), which is a different failure than a likelihood singularity and no sampler/discrepancy fixes it.

---

## D. Priors (Section 3.1)
- **Maximum entropy (Jaynes)** = pick the least-committal prior consistent with what you know (e.g., known mean/variance → Gaussian; only a range → uniform). Avoids smuggling in unjustified information.
- **Conjugate priors** = prior chosen so the posterior has the **same functional form** (e.g., Gaussian-Gaussian, Gamma-Gaussian-precision). Makes Gibbs sampling clean. Convenience, not necessity.
- **Uniform prior → MLE.** A flat prior makes the posterior ∝ likelihood, so the MAP (posterior mode) = the MLE. Common in Bayesian *modal* updating.

---

## E. Model error taxonomy (Section 1.1)
- **Model parameter errors** — wrong parameter values (the thing updating fixes).
- **Model form / structure errors** — wrong *equations*: plate modeled as a beam, distributed mass as lumped, wrong BCs, wrong mesh connectivity, wrong geometry, nonlinear-as-linear, wrong constitutive law. **Cannot be fixed by tuning parameters** — this is the discrepancy/model-form term (KOH/statFEM territory) and the source of our missing-modes floor.
- **Numerical errors** — discretization, round-off, convergence.
- **Measurement errors** — systematic + random; *also* introduced by assuming linear/time-invariant behavior during modal extraction.

---

## F. Data domains & noted gaps
- Likelihood-by-domain: **4.1 time**, **4.2 frequency/FRF**, **4.3 modal** (mode-matching vs no-mode-matching).
- **Complex modal data / non-classical damping gap:** most modal-data BU uses *real* modes (assumes proportional/classical damping), but real structures rarely meet that → **complex modes** (complex mode shapes + damping ratios). Few BU works handle complex modal data. Paper flags variational Bayes / ML-in-Bayes as opportunities.
- **"Output-only time-history BU of FE models not yet researched"** — your statFEM question: statFEM uses observation data but is **state/response reconstruction with an explicit discrepancy**, not output-only *parameter* updating of an FE model from raw time histories. The output-only *modal* route is **OMA (operational modal analysis)**. So statFEM is adjacent but not the example the paper means; the genuine output-only-time-history-BU gap overlaps our unknown-forcing direction.
- **RMS formulations (4.2):** likelihoods/objectives built on root-mean-square response levels rather than full spectra — lossy summary, but robust. (Relevant to our QOI-weighted-likelihood idea: RMS is a flat summary; consequential errors can hide in it.)
- **Substructure coupling / Component Mode Synthesis** (Jensen et al. [159]): use CMS model reduction inside BU so each posterior evaluation is cheap — directly relevant to our tractability problem (see G).

---

## G. Tractability — your "recompute modes every posterior point? linearize the FEM?"
**Yes — that's the core cost.** Every posterior sample/likelihood evaluation needs model FRFs/modes, i.e. a fresh **eigen-solve / linear solve** of the (parameter-dependent) FE system. For a fine mesh and thousands of samples that's the bottleneck. The paper also flags a *second* modal-data issue: needing to assign **weighting factors** between frequencies and mode-shape terms **without solid mathematical basis** (the ratio/covariance likelihoods in A2 partly remove this by deriving the weights).

Standard ways to make it tractable (maps to our "FEM-run-count" core problem):
- **Surrogate models** — replace the expensive FE FRF with a fast approximation: polynomial chaos expansion (PCE), Gaussian-process emulators, neural nets, and **rational-function surrogates** (Schneider — natural for FRFs since an FRF *is* rational in frequency, poles = resonances).
- **Reduced-order models (ROM) / modal truncation** — keep only the modes in/near the band of interest.
- **Component Mode Synthesis / substructuring** (Jensen) — reduce per-component, couple at interfaces; recompute only what changed.
- **Eigenvalue/eigenvector derivatives (Nelson's method) / perturbation** — update modes cheaply from derivatives instead of a full re-solve; also supplies **gradients** for HMC/NUTS.
- **Linearization / affine stiffness parameterization** (Niu) — `K(θ) = K_0 + Σ θ_i K_i` makes assembly and derivatives cheap.
- **Differentiable FEM + autodiff** — our route: keep the forward model differentiable so NUTS gets exact gradients (Stage-4 feasibility hinges on this staying affordable; ROM/modal-truncation are the levers).

---

## H. Damage detection levels (SHM, Section 6) — your highlight
Rytter's hierarchy: **L1** existence (is there damage?), **L2** location, **L3** severity/quantification, **L4** remaining service life / prognosis. Bayesian methods naturally target L1–L3 with uncertainty; L4 needs a damage-evolution/prognostic model.

## I. Non-probabilistic — "what is the fuzzy?"
**Fuzzy (interval) approach:** when you lack enough information to justify a probability distribution, represent parameter uncertainty as **interval bounds with membership/confidence values** (fuzzy sets) instead of a PDF. Mostly used for **epistemic** uncertainty (lack of knowledge), not aleatory (inherent randomness). Effective but doesn't give a posterior; it's a different UQ philosophy from Bayesian.

## J. Benchmarks worth knowing
- **NASA Multidisciplinary UQ Challenge** — community benchmark for UQ methods (aleatory/epistemic separation, model updating, reliability). Good external yardstick if we want a recognized validation case.
- **IASC-ASCE SHM benchmark**, ten-storey shear buildings, RC beams/columns — recurring lab/numerical cases in the review's tables.

## K. MAP vs MLE (recap — full answer in the first chat of this thread)
- **MLE** = argmax `p(D|θ)` — best fit to data, **ignores the prior**.
- **MAP** = argmax `p(D|θ)·p(θ)` — best fit **plus** prior (= regularization). MAP with a **uniform prior = MLE** (ties to D above).
- Both are **point estimates** (modes), not the full posterior; neither gives uncertainty by itself. Full Bayes (MCMC/NUTS) characterizes the whole posterior.

---

## Connections to our project (why this review matters for us)
1. **Identifiability classes (C) = our core problem #1.** Beck–Katafygiotis "unidentifiable = continuum of solutions" is exactly the round-3 ridge. The review gives us the vocabulary to *name* what failed.
2. **Ratio-distribution likelihood (A2) ≈ our unknown-forcing novelty.** Eqs. 21–23 handle random input; our OMA/input-state/force-ID direction lives one step beyond (no measured input at all). Worth citing Yan et al. as prior art when we scope the forcing novelty.
3. **Additive-error breakdown (A3) = our missing-modes floor.** The review explicitly says additive prediction error fails when model-form error is large — independent confirmation of the round-3 `sigma_e` floor diagnosis.
4. **Tractability menu (G) = our FEM-run-count problem.** ROM / CMS / surrogates / eigen-derivatives are the levers for keeping Stage-4 higher-fidelity FEM NUTS-feasible.
5. **The review under-covers explicit discrepancy / statFEM** (only lumped prediction error; KOH cited once). Our discrepancy-kernel + unknown-forcing + load-QOI combination sits in that gap — a positioning argument for novelty.
6. **QOI-weighted likelihood idea** is reinforced by the RMS/weighting-factor discussion (F, G): flat weights miss consequential errors; deriving/uncertainty-weighting beats ad-hoc weighting factors.

## Open follow-ups to decide
- Pull the exact Yan et al. [183] paper if we want to *use* the ratio-distribution likelihood (random forcing) — it may be closer prior art to our novelty than expected.
- Decide whether NASA UQ Challenge or a real public dataset (research_backlog priority 2) is the validation case.
- Map our differentiable-FEM tractability plan onto the review's ROM/CMS/eigen-derivative options for Stage 4.
