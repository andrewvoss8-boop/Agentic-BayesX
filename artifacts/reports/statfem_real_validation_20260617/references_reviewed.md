# References reviewed (Reference/Standards Gate) — FRF-likelihood multimodality

Two papers Andrew supplied 2026-06-17, reviewed for how they handle the FRF-likelihood problem we hit
(NUTS non-convergence / multimodality / σ_d runaway on the real ShockSat FRF). Both are directly on-point;
the second is the SOURCE of our "Schneider discrepancy."

## Paper A — Kiran, Das, Bansal (2025), *A state-of-the-art review of Bayesian FE model updating*, Prob. Eng. Mech. 80:103761
Key passages that NAME our exact findings:
- **§3.2 + Fig 1 (after Ching & Chen / Beck–Katafygiotis):** three identifiability regimes by the topology of
  the likelihood in parameter space — (a) UN-identifiable = a 1-D manifold (continuum) of equally-good θ;
  (b) LOCALLY identifiable = samples cluster at a FINITE number of DISTINCT locations (= MULTIMODAL);
  (c) GLOBALLY identifiable = a single cluster. **Our R-hat≈104 / ESS 2 / 0 div is textbook case (b): local
  identifiability** (several output-equivalent θ basins), a named phenomenon, NOT a bug.
- **§3.4.2 (sampling), verbatim:** "the model updating problem... will typically face convergence problems due
  to an over-parameterized identification model or data with incomplete information. Furthermore, the likelihood
  function has singularities (i.e. nonsensical maximas), and depending on initial values, the sampling run may
  converge to the neighborhood of a local maximum. **For example, a local maximum around which a run may get
  trapped involves variance parameters approaching extreme values, such as zero or infinity.**" → **This is our
  σ_d → 9.8 runaway, named as a known likelihood singularity.**
- **§3.4 / §4:** the dominant samplers in FE-updating are TMCMC (transitional MCMC), Gibbs, SuS, evolutionary/
  population MCMC — i.e. MULTIMODAL-CAPABLE / tempered samplers — *because* of (b)/(c). NUTS-MCMC is listed once
  (ref [133]) but is rare. Gradient HMC/NUTS is NOT the field-standard tool here; tempering/sequential samplers are.
- **§4.2:** multiple FRF likelihoods exist: RMS (Eq 13), Gaussian-on-difference (Eq 14 ≈ ours but on magnitude),
  complex circular-Gaussian additive (Eq 18/20, Γ covariance), and the Yan ratio-distribution (Eq 21–23, because
  Ĥ=Ŷ/F̂ is a RATIO of two noisy transforms). Schneider [184] = the complex MULTIPLICATIVE log-error (ours).
- **§4.3:** modal-domain likelihoods (mode-matching Eq 24–26; mode-matching-free eigen-equation Eq 27–42) are the
  most common on REAL structures and are computationally easier / better-behaved than whole-FRF.
- **§5 (model class selection):** Bayesian evidence = automatic Ockham's razor; "excessively diffuse priors...
  enforce a strong preference towards simpler models." Grounds our parameter-count study in evidence.

## Paper B — Schneider, Papaioannou, Straub, Winter, Müller (2022), MSSP 166:108407 — the SOURCE of our discrepancy
This is the paper our M2/M3 "Schneider discrepancy" is patterned on. Critical method details we did NOT replicate:
- **Sampler: BUS + Subset Simulation (SuS), NOT NUTS.** Stated reason (§1): "Laplace approximations are inaccurate
  in problems with small numbers of measurements and are DIFFICULT TO OBTAIN IN MULTIMODAL (non-uniquely
  identifiable) problems," and SuS handles "peaky" likelihoods. They used a multimodal-capable sampler BY DESIGN.
- **Discrepancy correlation is ADDITIVE, not pure-Kronecker:** ρ(Δz,Δf)=r·ρ_f(Δf)+(1−r)·ρ_z(Δz),
  R = r(R_ff⊗I) + (1−r)(I⊗R_zz) (Eq 19–25). The additive split RETAINS correlation when one distance is large
  (ours, np.kron(C_f,C_z), decays to ~0 if EITHER is large). **Our covariance is a simplified/over-decaying form.**
- **They LEARN 5 error hyperparameters** (σ_w, σ_θ, l_co,z, l_co,f, r); we FIX the lengths and learn only σ_d.
  Their posterior: σ_w≈σ_θ≈0.31, l_co,z≈50 m (≫ plate → near-fully spatially correlated), l_co,f≈10 Hz, r≈0.82.
- **Clean-data discipline:** restricted to 25–160 Hz, and KEPT ONLY 5 of 18 channels with coherence≈1 across the
  band (5 measurement repetitions gave real coherence); dropped poor-coherence points entirely.
- **Parsimonious, well-conditioned parameters:** 3 global moduli (Ex,Ey,Gxy) + ζ, identified to CoV 0.3–0.9% —
  NOT 9 group stiffnesses. Solid model has Ex–Ey ρ=−0.74 (a near-degenerate ridge); SHELL (homogenized, fewer
  effective params) has HIGHER evidence (574.3 vs 569.8) → they used evidence to prefer the better-identified
  parameterization (the parameter-count lesson).
- **The damping/peak-amplitude problem is THEIRS TOO (Fig 6, §5.4), verbatim:** "the eigenfrequencies of the
  response are recovered quite well, whereas the amplitudes are not well predicted around the eigenfrequencies...
  We would have to increase the damping ratio to explain the amplitude for some eigenfrequencies, whereas the
  damping ratio would have to be decreased to obtain the measured amplitude at the other eigenfrequencies. This
  cannot be achieved by a single damping ratio. Thus... the applied damping model is too limited." → **Identical
  to our finding.** Their σ_w≈0.31 (NOT a runaway) ABSORBS this misfit; result = ~90% coverage (611/680 inside
  95%), with the ~10% misses CONCENTRATED AT EIGENFREQUENCIES. So the realistic best case is "calibrated with
  eigenfrequency-localized misses," NOT perfection — and they were honest about it.

## How this updates our diagnosis + plan (feeds decisions_log D8)
1. Our NUTS non-convergence is the EXPECTED, named behavior (local identifiability); σ_d→9.8 is the named
   "variance→∞" likelihood singularity. NUTS is an honest DIAGNOSTIC of these, but the WRONG sampler to validate
   the method — the source paper and the field use TMCMC/SuS (multimodal/tempered) precisely for this.
2. We did NOT implement Schneider faithfully: we used pure-Kronecker (over-decaying) covariance with FIXED
   lengths + NUTS, vs their additive correlation + LEARNED hyperparameters + SuS + coherent-band/channel
   selection + parsimonious params. Part of our "negative" is likely our SIMPLIFICATION, not the method.
3. The damping-limited peak-amplitude misfit is FUNDAMENTAL and corroborated; the realistic target is calibrated
   coverage with eigenfrequency-localized misses (~90%), absorbed by the discrepancy — not a perfect fit.
4. The orthogonal projection (M3) becomes the SHARP scientific question: it removes the θ-span from the
   discrepancy, but the dominant misfit (peak frequency/amplitude) LIVES near the θ-span → M3 may STARVE the
   discrepancy where M2 (plain Schneider) lets it absorb the misfit. Test M2-vs-M3 directly.
