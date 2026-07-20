# Unified modal statFEM (UMS) — statFEM × Das/Debnath × Schneider in one generative model
2026-06-12 · Study G method note · plain-English definitions on first use (project communication rule)

## 0. One paragraph
UMS is a Bayesian digital-twin method for dense frequency-response (FRF) test data. A parametric FEM
provides the physics; **latent complex modes** (Das/Debnath) carry the structure's actual eigenvalues,
damping, and shapes without ever running an eigensolver or pairing modes inside the sampler; a soft
**eigen-residual** ties those latent modes back to the FEM with an inferred looseness τ (the statFEM
"the model may be wrong" lever, expressed in modal space); a **correlated multiplicative complex
discrepancy** (Schneider) absorbs what the modal model + FEM cannot represent, with its size and
correlation lengths learned from data; and the **trust gate is held-out QOI coverage** (statFEM
backbone), not parameter recovery.

## 1. The generative model (top to bottom)
Symbols: θ = FEM parameters; λ_m = complex eigenvalue of mode m; ψ_m = complex mode shape; B = Ritz
basis size; κ = noise-floor scale; σ, ℓ = discrepancy scale/correlation hyperparameters.

1. **FEM layer (physics):** K(θ) = Σ_g s_g K_g + s_susp K_susp (stiffness groups + suspension),
   C(θ) = a₀M + a₁K(θ) (Rayleigh damping), M fixed. Priors: lognormal around nominal.
2. **Latent-mode layer (Das/Debnath T-D1/T-D2):** for m = 1..Nm
   - f_m = Σ_{k≤m} δ_k with δ_k ~ LogNormal(log nominal gap, 0.25) — *ordered frequencies by
     construction (no label switching, degenerate-pair safe)*;
   - ζ_m ~ LogNormal(log 0.01, 0.7) — per-mode damping, NOT forced to follow Rayleigh;
   - λ_m = −ζ_m ω_m + i ω_m √(1−ζ_m²);
   - shape coefficients c_m ∈ ℂ^B in a FIXED Ritz basis Φ₀ (the nominal FEM's mass-orthonormal
     modes, eigh computed once OFFLINE) with prior c_m ~ N(e_m, 0.3) + i N(0, 0.1) — centered on
     "this latent mode looks like nominal mode m", deviations = mixing with neighbours;
   - **eigen-residual** (the glue): r_m = (λ_m² I + λ_m C̃(θ) + K̃(θ)) c_m / (|λ_m|²‖c_m‖)
     with K̃, C̃ the B×B projections (precomputed per group, so the residual costs O(B²), no
     N-dimensional operation, no eigensolve, no mode matching);
     Re r_m, Im r_m ~ N(0, τ²), τ = 0.004 + LogNormal — **τ is the statFEM lever**: τ→0 locks the
     modes to the (possibly wrong) FEM; τ free lets data move them; the posterior of τ is an
     interpretable "how wrong is my FEM's eigenstructure" diagnostic.
3. **FRF synthesis (no eigensolve):** H(ω) = Σ_m [ψ_mψ_m^T/a_m/(iω−λ_m) + c.c.], a_m = ψ_m^T(2λ_mM+C)ψ_m
   — the standard complex-mode residue form; scale-invariant in ψ; accelerance = −ω²H. Modes above the
   latent set are TRUNCATED (their effect lands in the discrepancy; documented).
4. **Discrepancy + observation layer (Schneider T-S1/T-S2, HMC-compatible form):**
   scaled complex residual r(ω, p) = (data − H_pred)/(|H_pred| + κ) with κ = inferred noise floor;
   Re r and Im r are zero-mean Gaussian fields with covariance σ² (R_f ⊗ R_z): exponential kernels in
   frequency (length ℓ_f, Hz) and space (length ℓ_z, m over the true sensor coordinates), all four
   hyperparameters inferred. For |H|≫κ this is Schneider's multiplicative error to first order
   (Re r ≈ log-magnitude error, Im r ≈ phase error); for |H|≲κ it degrades gracefully to an additive
   floor — one field covers both regimes.
5. **Trust gates (statFEM backbone):** all-variable NUTS convergence AND held-out QOI coverage at
   never-measured locations (response-limit-proxy peak + band-RMS).

## 2. What each source contributes (and what is ours)
| Layer | Source | Contribution |
|---|---|---|
| Output-space discrepancy, held-out trust gate, "calibrated prediction ≠ parameter recovery" | statFEM backbone (project) | the frame everything plugs into |
| Latent complex modes, eigen-residual, no mode matching, damping ID | Das & Debnath 2020 | the differentiable, degenerate-safe physics glue |
| Correlated multiplicative complex FRF error, inferred space×frequency correlation | Schneider et al. 2022 | the dense-data discrepancy structure |
| Ritz-projected eigen-residual (O(B²)); ordered-increment frequencies; separable OU kernel with O(n) innovations whitening; floor-scaled smooth complex residual | this work (engineering glue) | what makes the combination actually run under NUTS |

## 3. Documented deviations from the papers (and why)
- **Separable (R_f ⊗ R_z) instead of Schneider's additive split** — the named alternative in his Eq. 19;
  enables exact O(n) likelihood via AR(1)/OU innovations (self-tested vs dense MVN to 1e-13).
- **Smooth scaled-complex-residual instead of exact log-magnitude/wrapped-phase** — the exact form has
  gradient cliffs (phase wrap at every resonance crossing; 1/|H| spikes at antiresonance zeros) that
  defeat gradient-based samplers. *Finding: this is plausibly why Schneider used gradient-free
  BUS-Subset-Simulation; porting his error model to NUTS/HMC requires the smooth small-error-equivalent
  form.* Verified empirically here: exact form = sampler frozen, 67–100% divergences; smooth form =
  moves, divergences <10% (probe).
- **τ floor (0.004)** — the FEM eigenstructure is never exactly right; bounds the eigen-residual needle.
- **Peak-picked initialization of latent frequencies** (init only, priors unchanged) — dense-FRF
  posteriors are needle-sharp in the resonance positions; starting misaligned by several half-bandwidths
  is a cliff. A practitioner does the same thing (peak table) before any updating.

## 3b. The sampler-pathology ladder (what it actually took — each rung evidence-backed in logs/)
| Rung | Symptom | Diagnosis | Cure | Evidence |
|---|---|---|---|---|
| 1 | NUTS frozen, 100% div | log/wrapped-phase gradient cliffs | smooth residual r=(data−H)/(|H|+κ) | probe_medium vs probe2 |
| 2 | chains scatter across basins (R-hat 236) | default initial step ~1 throws early-warmup trajectories over needle ridges | initial step 5e-4, adapts up | run-1 vs probe3 (div 56%→2%) |
| 3 | R-hat 73 with healthy chains | per-mode complex-scale GAUGE valley (residue invariant to c→αc) | pin shape normalization: m-th comp ≡ 1+0i (standard modal practice, as in Das/Debnath) | probe3 vs probe4 |
| 4 | both chains agree on a WRONG ζ pattern (modes smeared to ~6–7%) | mode-level physics-vs-discrepancy trade-off (KOH confounding in the modal layer) | practitioner damping prior ζ∈[0.4,2]% — engineering knowledge, not truth-tuning | probe4 vs probe5 |
| 5 | R-hat 176, ESS=1 on named coords (in-band shape imaginaries; s_susp) | posterior CONDITIONING: needle freqs force tiny steps; flat/uninformed directions freeze; s_susp uninformed by the band | fix s_susp at nominal (documented unidentifiable); tighten out-of-band shape priors; warmup 1500 | probe6 → final run |

This ladder is itself a result: it is the concrete cost of running gradient-based, fully-Bayesian inference
on dense FRF data with a unified physics+discrepancy model — and each cure is standard practice made
explicit (smooth residuals, scaled initialization, gauge fixing, engineering priors, identifiability-aware
parameter fixing).

## 3c. The architecture lesson (the load-bearing finding of Study G)
Two ways to place the mode SHAPES, and they are NOT interchangeable for held-out SPATIAL prediction:
- **Free latent shapes (Das/Debnath, "UMS-full"):** each mode's shape is a sampled vector. Excellent for
  updating at MEASURED DOF (no mode pairing, recovers damping) — but the held-out points have NO data, so
  their shape values are unconstrained → held-out QOI is garbage (we measured ~1e7× error) and the sampler
  is multimodal (R-hat 364). **Das/Debnath's latent shapes do not generalize to unmeasured locations.**
- **Physics-bound shapes (the PRODUCTION method, "UMS-FEM"):** the shapes are the eigenvectors of the
  parametric reduced stiffness K̃(θ) (a cheap, differentiable B×B `eigh`). They generalize spatially because
  they come from the PHYSICS; θ (quadrant group stiffnesses) calibrates them; per-mode damping ζ_m stays
  latent (the Das/Debnath contribution that the eigensolve does not give you); the Schneider field absorbs
  the rest. ~22 parameters instead of 481.
This is exactly the StatFEM principle stated in the modal domain: **calibrate the physics (it generalizes),
add a discrepancy (it does not pretend to); do not give the discrepancy/shape so much freedom that it stops
generalizing.** Study G's headline reports UMS-FEM; UMS-full is kept as the documented over-parameterization
negative (`out/ums_summary_FULL_ambition.json`, R-hat 364, QOI 0/10).

## 4. Honest limitations
- The symmetric complex-Gaussian residual loses Schneider's directional "kidney" error geometry
  (magnitude/phase asymmetry) in the large-error tail.
- Shape deviations are restricted to span(Φ₀) (Ritz truncation, B modes) — standard CMS-style truncation.
- The discrepancy field conditioning treats observed residuals at floor-dominated lines as exact.
- One synthetic dataset/realization in Study G; no test-to-test variability yet.
