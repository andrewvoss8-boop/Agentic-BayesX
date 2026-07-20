# DRAFT — PIFT → StatFEM/FRF analogy mapping (SURFACE item S1; awaiting Andrew sign-off)

Status: DRAFT for human review (card §11 says SURFACE, do not self-decide). The verbatim quote below is taken
from the **card text**; it MUST be checked against the PIFT PDF (arXiv:2301.07609) before it goes in the packet
(the PDF is not yet in `references/` — blocker B1).

Define-on-first-use (reader is beginner-to-intermediate in ML/stats):
- **Posterior** = the updated probability distribution over unknowns after seeing data. "Width" = how uncertain.
- **Collapse** = the posterior width shrinks toward zero (a point mass) — the model becomes (over)confident.
- **Fisher information** = how much the data tells you about a parameter; for *independent* observations it adds
  up, so total information ∝ N (number of points). More information → tighter posterior.
- **σ_meas** = measurement-noise standard deviation (units = the residual's units, here log-magnitude of the
  FRF). **σ_d** = the standard deviation scale of the *model-form discrepancy* (how wrong the FEM is, beyond
  noise). **θ** = the 9 group stiffness multipliers we calibrate (dimensionless, nominal 1.0).
- **Effective sample size N_eff** = the number of *independent* observations the likelihood effectively has.
  For correlated data N_eff < N: points within one correlation length carry redundant information.

## 1. The PIFT result (Alberts & Bilionis 2023, arXiv:2301.07609) — to be quoted verbatim from the PDF
PIFT (Physics-Informed Information Field Theory) puts a prior on an unknown *field* and enforces the governing
PDE through a "fictitious" residual likelihood whose precision (inverse of a **fictitious residual variance**) is
a learned nuisance parameter. The result the card asks us to map:

> as the number of collocation points **N→∞**, the posterior uncertainty over the **fictitious residual
> variance** → 0 and "**the field posterior … collapses to a single function irrespective of [that variance] …
> a collapsing field posterior is undesirable in cases of model-form uncertainty or in ill-posed problems.**"

Intuition: each collocation point adds independent information about the residual, so information ∝ N; as you
add points everywhere, both the field and the residual-variance posterior tighten without bound.

## 2. The mapping to OUR StatFEM/FRF setting
| PIFT concept | Our StatFEM/FRF analogue | Units |
|---|---|---|
| collocation points (where the PDE residual is evaluated) | **observation points the likelihood conditions on**: frequency samples of the FRF × observed sensors (modal route: # modes × # sensors) | count N = N_freq · N_sensor |
| the latent field being inferred | the FEM forward model output `log|H(ω;θ)|` PLUS the additive discrepancy field | log-magnitude |
| fictitious residual variance (PDE-residual precision⁻¹) | our **likelihood variance** = σ_meas² (real noise floor) + σ_d² (model-form discrepancy scale) | (log-mag)² |
| collapsing field posterior as N→∞ | iid/naive arms: σ_d→0 and identified-θ width→0 as N grows, **even though the FEM has genuine model-form error** | — |

The danger (the same "confidently wrong," now reached by *adding data*): with an **iid** likelihood (each point
independent), Fisher information ∝ N, so as N grows the posterior over θ AND over the discrepancy variance σ_d
tightens without bound — and the held-out predictive coverage DEGRADES (over-tight + biased).

## 3. Where the analogy HOLDS
- Both have a residual likelihood whose precision is a learned nuisance, and a field/parameter posterior that
  conditions on N points.
- In both, an **independent-across-points** residual model makes Fisher info ∝ N, driving the variance-posterior
  to a point mass and the field/θ posterior to (over)confidence.
- The conceptual **cure is the same**: impose correlation among residual points → caps the effective sample
  size → the variance posterior plateaus instead of collapsing.

## 4. Where the analogy BREAKS / differs (the honest caveats — these are the science, not boilerplate)
1. **Mechanism vs role.** PIFT's "data" are collocation points enforcing a *known* PDE residual on an unknown
   field; our points are *measurement* observations conditioning a likelihood on a fixed parametric FEM (θ ∈ R⁹)
   plus a discrepancy field. So "collocation ↔ observation" is an analogy of the *count that drives Fisher
   information*, NOT an identity of mechanism. We must say this plainly.
2. **N→∞ by densification, not domain growth.** Our band is physically fixed (≈45–260 Hz); we approach large N
   by *densifying* the frequency grid (and adding sensors), which oversamples a smooth, resonance-dominated,
   spatially-correlated response. The correlated arm's plateau is *because* densification within a correlation
   length adds redundant, not independent, information — exactly the finite-N_eff effect.
3. **θ is low-dimensional and partly UN-identifiable.** Only ~4/9 groups carry appreciable modal strain energy.
   The collapse danger is sharpest for the *identified* θ directions and for σ_d; unidentified θ directions stay
   prior-dominated for all N (a *different* failure — under-identification, not collapse). Report both, don't
   conflate.
4. **Our variance has physical meaning.** PIFT's fictitious variance is a pure modeling device; our σ_meas is a
   real measurement-noise floor and σ_d is the genuine model-form discrepancy scale. So "σ_d→0" is a falsifiable
   *claim that the FEM is right*, and held-out coverage is the falsifier.

## 5. Hypothesis to TEST (report either way; card §2)
The **orthogonal-Schneider** correlated discrepancy (correlated over log-frequency AND sensor space, projected
off the θ→observable sensitivity span) has a **finite effective sample size** N_eff, capped by its correlation
lengths. So its σ_d-uncertainty and held-out score should **PLATEAU** once N exceeds the correlation scale,
while iid/naive **COLLAPSE**. If so, the correlated discrepancy is a concrete **cure** for the PIFT collapse in
the StatFEM/FRF setting. Crossover N* ≈ where added points start falling within one correlation length.
