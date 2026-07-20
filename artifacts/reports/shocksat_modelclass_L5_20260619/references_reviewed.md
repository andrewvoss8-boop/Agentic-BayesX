# references_reviewed.md — Card F (model-class selection by Bayesian evidence)

Reference/Standards Gate. The two method papers for this card are on disk and were reviewed in the parent
threads (Card A `statfem_real_validation_20260617/references_reviewed.md`, Card D
`shocksat_fem_remesh_20260618/references_reviewed.md`); equation numbers carried from those notes. PDFs present:
`references/pdfs/statFEM.pdf` (Girolami et al. 2021), `references/pdfs/review of Bayesian finite element model
updating techniques for structural systems copy.pdf` (Kiran et al. 2025),
`references/pdfs/2007-transitional-markov-chain-monte-carlo-method-...` (Ching–Chen 2007, TMCMC origin).
Schneider 2022 (MSSP 166:108407) and Das–Debnath 2020 (MSSP 136:106524) reviewed in Card D.

## Primary — Girolami, Febrianto, Yin, Cirak 2021, "The statistical finite element method", CMAME 375:113533
- **§3.4 (model selection / posterior over models):** Bayesian evidence ranks competing statFEM models;
  `p(M_j|Y) ∝ p(Y|M_j) p(M_j)` and the Bayes factor `BF_{12}=p(Y|M_1)/p(Y|M_2)` (Eq 52–53).
- **§4.1.5 (mesh / model selection demonstration):** the marginal likelihood selects among mesh resolutions /
  model forms and **can prefer the simpler model even when a richer one fits the data better** — the canonical
  precedent that "the richer form does not earn its complexity" is a legitimate, Ockham-correct WIN.
- **Eq 38 (analytic Gaussian evidence):** `p(Y|M_j) = N(ρ P ū, C_d + C_e + ρ² P C_u P^T)` — closed-form when
  the observation is a linear-Gaussian functional of the field; used for the Stage-1 fixed-θ screen. For our
  modal-feature observable: mean = FEM modal-frequency (or peak-amplitude) vector at θ_MAP; covariance =
  model-prediction variance (C_u) + discrepancy (C_d) + extraction/measurement noise (C_e); the model class
  sets the *structure* of these terms.
- USE: Stage-1 analytic evidence + Bayes factors + posterior model probabilities; the §4.1.5 "simpler can win"
  result as the honest baseline expectation.

## Primary — Kiran, Das, Bansal 2025, "State-of-the-art review of Bayesian FE model updating", Prob. Eng. Mech. 80:103761
- **§5 (Bayesian model class selection):** evidence `p(D|M_j)=∫p(D|θ,M_j)p(θ|M_j)dθ` (Eq 43) = automatic
  Ockham's razor `log p(D|M_j) = E_post[log p(D|θ,M_j)] − KL(post‖prior)` (Eq 44) = (avg log-likelihood) −
  (information gain / complexity). Laplace/asymptotic evidence (Eq 45) valid ONLY when globally identifiable.
- **Evidence pitfalls (the gate we honor):** "excessively diffuse priors enforce a strong preference towards
  simpler models" → informative priors + a prior-width sweep; large raw datasets overwhelm the prior and bias
  toward complex models → **use modal-feature statistics as the data** (Kiran [72,222]) = our L5 observable.
  ARD suggested for data-driven prior choice on added local parameters.
- **§3.2 identifiability (Beck–Katafygiotis):** un- / locally- / globally-identifiable. Our multimodality
  (Card A R̂≈104, ESS 2, 0 div) = textbook *local* identifiability → sampling evidence (TMCMC/SuS), not Laplace.
- **§4.3 modal-domain likelihoods** are better-behaved than whole-FRF on real structures (why L5 converges).
- USE: §5 evidence framing + pitfalls (informative prior, modal-feature data); §3.2 to justify TMCMC over Laplace.

## Supporting — Ching & Chen 2007 (TMCMC), incl. model-class selection & model averaging
- TMCMC returns the **log-evidence** as a by-product of the tempering ladder (used by `tmcmc.py`). The original
  paper explicitly covers Bayesian model-class SELECTION and model AVERAGING — direct precedent for ranking M0–M5.
- USE: Stage-2 flexible-θ evidence; report cross-run logZ stability (an unstable logZ is unusable — Card A D10).

## Supporting — Schneider et al. 2022, MSSP 166:108407 (the source of our "Schneider discrepancy", M4)
- Additive space×freq correlation `R = r(R_ff⊗I) + (1−r)(I⊗R_zz)` (Eq 19–25), BUS+SuS sampler (multimodal by
  design), learned hyperparameters (σ_w, σ_θ, l_co,z, l_co,f, r), model evidence reported.
- USE: M4 correlated-discrepancy class via `schneider_faithful.py`. NOTE his single-η damping hit the SAME
  peak-amplitude ceiling we see (absorbed into σ_w≈0.31) — corroborates the D3 confound on amplitude.

## Supporting — Das & Debnath 2020, MSSP 136:106524 (the damping-update form, M2/M3)
- Bayesian (MAP) FE updating with incomplete COMPLEX modal data; updates mass+stiffness+DAMPING
  (Rayleigh α0,α1 + non-classical viscous C = C0 + Σ θ_g C_g); mode-matching-free; complex eigenvalue
  λ = −ζω + iω√(1−ζ²); quadratic eig (λ²M+λC+K)Ψ=0.
- USE: M2 (Rayleigh) and M3 (localized non-proportional C on identifiable shell groups) parameter forms.
  Damping priors informative from Card D measured ζ = 0.06–1.8% (`out/cardD_inputs/damping_gate.json`).

## How each is used in Card F
- Evidence/Bayes-factor/Ockham math → statFEM §3.4/§4.1.5 + Kiran §5 (D1).
- "Use modal features as the data" → Kiran pitfall (b) → our L5 observable (D3).
- TMCMC for evidence under local identifiability → Kiran §3.2 + Ching–Chen 2007.
- M2/M3 damping forms → Das–Debnath; M4 discrepancy → Schneider; both corroborate the amplitude confound (D3).
