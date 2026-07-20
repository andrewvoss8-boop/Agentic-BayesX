# PIFT → StatFEM/FRF analogy mapping (FINAL — Andrew signed off via "go", 2026-06-17; card §11 SURFACE item)

Verbatim PIFT quotes verified against `references/pdfs/2301.07609v5.pdf`; see `references_and_quotes.md`.

Define-on-first-use (reader is beginner-to-intermediate in ML/stats):
- **Posterior** = the updated probability distribution over the unknowns after seeing data; its "width" = how
  uncertain we still are. **Collapse** = width shrinks toward zero (a point mass) → (over)confidence.
- **Fisher information J** = how much one observation tells you about a parameter. For *independent*
  observations information adds, so total information = N·J for N points, and the posterior variance of an
  identified parameter scales like **1/(N·J) → 0** as N grows. (This is literally PIFT's `(nJ(θ0))⁻¹`.)
- **σ_meas** = measurement-noise standard deviation (units: log-magnitude of the FRF). **σ_d** = the standard
  deviation scale of the model-form discrepancy (how wrong the FEM is beyond noise). **θ** = the 9 group
  stiffness multipliers we calibrate (dimensionless, nominal 1.0).
- **Effective sample size N_eff** = the number of *independent* observations the likelihood effectively has.
  For correlated data N_eff < N: points within one correlation length carry redundant information.

## 1. The PIFT result we are testing for (Alberts & Bilionis 2023, arXiv:2301.07609, p17/p25)
> "if σr is kept fixed while the number of collocation points n goes to infinity, then the 'posterior
> distribution of [the field parameters] θ … approaches normality with mean θ0 and variance (nJ(θ0))−1'" …
> "the field posterior in B-PINNs collapses to a single function irrespective of the value of σr as n →∞." …
> "a collapsing field posterior is undesirable in cases of model-form uncertainty or in ill-posed problems."

The mechanism is explicit in the formula: posterior variance = (n·J(θ0))⁻¹, so it → 0 as n → ∞, regardless of
the residual scale σr. Adding collocation points buys unbounded confidence.

## 2. The mapping to OUR StatFEM/FRF setting
| PIFT concept | Our StatFEM/FRF analogue | Units / count |
|---|---|---|
| collocation points n (where the PDE residual is evaluated) | **observation points the likelihood conditions on**: FRF frequency samples × observed sensors (modal route: # modes × # sensors) | N = N_freq · N_sensor |
| the latent field being inferred | FEM output `log|H(ω;θ)|` + the additive discrepancy field | log-magnitude |
| residual scale σr (fictitious, fixed) | our likelihood scale: σ_meas (real noise floor) + σ_d (model-form discrepancy scale) | (log-mag) |
| posterior variance (nJ(θ0))⁻¹ → 0 | iid/naive arms: identified-θ width and σ_d *uncertainty* → 0 as N grows, **though the FEM is genuinely wrong** | — |

The danger (the same "confidently wrong," now reached by *adding data*): with an **iid** likelihood (each point
independent → Fisher info ∝ N), as N grows the posterior over θ AND over the discrepancy variance σ_d tightens
without bound, while the held-out predictive coverage DEGRADES (over-tight + biased).

## 3. Where the analogy HOLDS
- Both have a residual likelihood whose scale is a (fictitious or learned) nuisance, and a field/parameter
  posterior conditioned on N points.
- In both, an **independent-across-points** residual model gives total Fisher info = N·J → posterior variance
  1/(N·J) → 0 (PIFT's exact formula), driving the variance-posterior to a point mass.
- The conceptual **cure is the same**: impose correlation among residual points → caps the effective sample
  size → the variance posterior plateaus instead of collapsing.

## 4. Where the analogy BREAKS / differs (honest caveats — these ARE the science)
1. **Mechanism vs role.** PIFT's "data" are collocation points enforcing a *known* PDE residual on an unknown
   field; ours are *measurement* observations conditioning a likelihood on a fixed parametric FEM (θ∈R⁹) plus a
   discrepancy field. "collocation ↔ observation" is an analogy of the *count that drives Fisher information*,
   NOT an identity of mechanism. State this plainly.
2. **N→∞ by densification, not domain growth.** Our band is physically fixed (≈45–260 Hz); we reach large N by
   *densifying* the frequency grid (and adding sensors), oversampling a smooth, resonance-dominated, spatially
   correlated response. The correlated arm's plateau is *because* densification within a correlation length adds
   redundant, not independent, information — the finite-N_eff effect.
3. **θ is low-dimensional and partly UN-identifiable** (~4/9 groups carry appreciable modal strain energy). The
   collapse danger is sharpest for the *identified* θ directions and for σ_d; unidentified θ directions stay
   prior-dominated for all N (a *different* failure — under-identification, not collapse). Report both.
4. **Our variance is physically real.** PIFT's σr is a pure modeling device; our σ_meas is a real measurement
   floor and σ_d is the genuine model-form discrepancy scale. So "σ_d-uncertainty→0" is a falsifiable *claim
   that the FEM error is pinned down*, and held-out coverage is the falsifier.

## 5. Hypothesis to TEST (report either way; card §2)
The **orthogonal-Schneider** correlated discrepancy (correlated over log-frequency AND sensor space, projected
off the θ→observable sensitivity span) has a **finite effective sample size** N_eff, capped by its correlation
lengths. So its σ_d-uncertainty and held-out score should **PLATEAU** once N exceeds the correlation scale,
while iid/naive **COLLAPSE** (σ_d-uncertainty & identified-θ width → 0, held-out score degrades). If so, the
correlated discrepancy is a concrete **cure** for the PIFT collapse in the StatFEM/FRF setting. Crossover
N* ≈ where added points start falling within one correlation length. **This is a hypothesis; the N-ladder +
ESS accounting decide it with numbers, not assertion.**
