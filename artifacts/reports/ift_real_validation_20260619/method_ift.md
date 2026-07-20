# method_ift.md — the faithful IFT twin (physics-in-prior, learned trust β) on real ShockSat

Plain-English intent first, then the precise math, then every adaptation and the honest deviation.

## 0. One-paragraph intuition (for the ML/stats-intermediate reader)
A digital twin needs a way to say **how much it trusts its own physics model**. Information Field Theory (IFT)
and its Physics-Informed-Field-Theory (PIFT) variant do this by putting the **physics equation into the prior**
over the response field, weighted by a single number **β ("beta") — an inverse temperature**. Think of β as a
thermostat for trust: high β = "I strongly believe the FEM equation, keep my predictions tight"; low β = "I
distrust the model here, widen my predictions." Crucially β is **learned from data**, so the twin reports a
calibrated level of self-distrust — a *model-form-error thermometer*. We contrast this against our StatFEM twin,
which instead puts the trust knob in the **likelihood** (a discrepancy term with its own free variance σ_d). The
whole study asks: on the **same real data, same FEM, same held-out test, same proper scores**, does it matter
**where** the trust lives — in the prior (IFT) or the likelihood (StatFEM)?

Terms (units): "field" = the structure's complex frequency response at every reduced coordinate; "prior" = the
belief before seeing data; "likelihood" = how data is explained given parameters; "marginalize" = integrate a
nuisance variable out analytically; β = inverse-temperature [dimensionful trust weight]; σ_meas = measurement
log-noise std [log-|H| units]; θ_g = stiffness multiplier on FEM group g [dimensionless]; c = global units-gain
[natural-log |H| units]; |H| = accelerance magnitude [g/lbf].

## 1. The shared, reused ingredients (apples-to-apples — NOT reimplemented)
- **Data:** the real single-impact accelerance |H₁(ω)| of hit-001 (band 45–260 Hz, native df≈1.25 Hz, ~172
  lines), bad channels excluded (ch101, ch29–31), DR-eligible mapped channels (peak/floor ≥ 30×). Reused from
  `measured_frf_cache.npz` (byte-identical, manifest_sha256.txt).
- **Forward model:** the reduced dynamic-stiffness accelerance `realfrf.fem_logmag` / `jax_fem_logmag_factory`
  (74-dim, mass = I, K(θ)=A_fix+Σ_g θ_g A_g, hysteretic loss η = 2ζ, ζ = 0.01, /386.0886 → g/lbf). Reused
  byte-identical.
- **Held-out protocol:** the channel split is the SAME RNG as `heldout_qoi.py`
  (`np.random.default_rng(seed).permutation(elig)`, obs_frac 0.6, DR_MIN 30) → IFT/L5/M2 share byte-identical
  splits per seed. ≥25 seeds.
- **QOI:** peak accelerance |H| and band-GRMS = √∫|H|² df, both in g/lbf, at held-out sensors (`core.qoi_peak`,
  `core.qoi_band`).
- **Scorer:** `score.py` interval/Winkler + CRPS + log-predictive-density (HEADLINE), coverage + z-std
  (SECONDARY). Reused byte-identical.

## 2. The IFT construction (faithful to the papers; adapted to structural dynamics)
**Field.** u(ω) ∈ ℂ⁷⁴ = the reduced complex response at drive frequency ω.

**Physics residual / operator.** R(u;θ,ω) = A(θ,ω)u − f, with dynamic stiffness
A(θ,ω) = (1+iη)K(θ) − ω²I (hysteretic damping, mass = I), and f = unit point force at the drive DOF (the same
impact node as the StatFEM run).

**Physics-informed PRIOR over the field** (the papers' central move; PIFT's ∝ exp(−β∫R²) and Hao–Bilionis's
"physics-informed prior measure on the function space of system responses"):

  π(u | θ, β) ∝ exp( −(β/2)‖A(θ,ω)u − f‖² − (τ₀/2)‖u‖² )

= a complex Gaussian CN(μ_u, Σ_u) with **precision** Λ = β·AᴴA + τ₀I and **mean** μ_u = Λ⁻¹(β·Aᴴf). As τ₀→0,
μ_u → A⁻¹f = the deterministic FEM response. **β = learned inverse-temperature = trust in the physics.** The
hysteretic damping makes AᴴA strictly positive-definite (see §3), so β·AᴴA is invertible without τ₀; τ₀ = 1e-12
is a numerical jitter only, NOT the regularizer.

**Measurement likelihood (SAME observable as StatFEM whole-FRF M2).** The observed-channel accelerance
H_j(ω) = −ω²·obs_V[s_j,:]·u = w_jᴴu is a **linear** functional of the field, so H_j is a scalar complex Gaussian
H_j ~ CN(m_j, v_j). The measurement is log|H_j| with iid log-noise floor σ_meas = 0.15. Held-out channels are
NEVER in the likelihood.

## 3. Closed-form moments via the forward-model eigendecomposition (no extra solve)
Diagonalize K(θ) = QΛQᵀ (real symmetric — the eigh already inside the forward). Then
A = Q·diag((1+iη)λ_k − ω²)·Qᵀ and AᴴA = Q·diag(D_k)·Qᵀ with

  D_k(ω) = (λ_k − ω²)² + (ηλ_k)²  = |g_k|²,   g_k = (1+iη)λ_k − ω².

With p_j = obs_V[s_j]·Q (channel j modal participation) and u_d = drive_row·Q (drive participation):

  **mean**  m_j(ω) = ω²·|Σ_k p_{j,k} u_{d,k} / g_k|   (= deterministic FEM accelerance |H_j^FEM(θ)|)
  **field variance**  v_j(ω) = ω⁴·Σ_k p_{j,k}² / (β·D_k(ω) + τ₀)

Both are smooth and differentiable in θ (through λ, Q) and β — NUTS-ready, with the eigh OUTSIDE any unstable
gradient path (degenerate-cluster contributions cancel in the sum, the StatFEM D10 trick). Because D_k ≥ (ηλ_k)²
> 0, v_j is finite for all ω; it grows near a resonance ω²≈λ_k (small D_k) — physically the FRF is most uncertain
at resonances, exactly the behavior IFT should show.

## 4. The honest deviation: log-magnitude moment approximation (Andrew's directive, D0)
log|H_j| with H_j ~ CN(m_j, v_j) is **log-Rician**, NOT Gaussian — so the field does **not** marginalize out in
closed form for this observable (the DRAFT's "exact marginalization" claim was wrong; corrected per D0). We
marginalize the field by **matching the first two moments** (delta-method / high-SNR propagation of a complex
Gaussian through log|·|):

  E[log|H_j|]  ≈ log|m_j| = log|H_j^FEM(θ)|
  Var[log|H_j|] ≈ v_j / (2|m_j|²)

giving the headline likelihood

  **log|H_j^meas|(ω) ~ N( log|H_j^FEM(θ)| + c ,  σ_meas² + v_j(ω;θ,β)/(2|H_j^FEM(θ)|²) )**.

This is **exactly a log|H| likelihood — the SAME observable as StatFEM M2** — but its per-bin variance is
**physics-derived** and controlled by the **single learned trust scalar β**, instead of M2's free σ_d² × fixed
freq×space Kronecker correlation. Limits: β→∞ ⇒ the field variance vanishes ⇒ a plain log|H| likelihood with
only σ_meas (full trust in physics); β→0 ⇒ variance blows up ⇒ graceful widening (no trust).

**Where the approximation is exact vs weak (carried as YELLOW everywhere):** exact in the high-SNR limit
K_j = |m_j|²/v_j ≫ 1; biased in deep antiresonances (low SNR), where v_j/(2|m_j|²) is already large so the
likelihood near-ignores those bins — the error sits where the term is downweighted, which is self-consistent.
The data is DR-eligible (median peak/floor ≈147×) so the informative peaks are high-SNR. We report
per-(channel,freq) SNR and flag low-SNR bins. A refinement (exact log-Rician moments via Rice/Bessel series) is
available but unnecessary for the headline; it is labeled, not hidden.

## 5. Held-out prediction (apples-to-apples with L5; avoids the peak-inflation pitfall)
The IFT posterior over (θ, β, c) predicts a held-out channel's |H| curve as exp(log|H^FEM(θ)| + c) with a
per-bin field+measurement log-std √(σ_meas² + v_j/(2|m_j|²)). The QOI widening is the **physics-derived field
uncertainty** applied as a QOI-level log-normal multiplier — peak: the field std **at the peak frequency**; band:
the **energy-weighted** field std over the band. This mirrors L5's marginal QOI-discrepancy STRUCTURE (so the two
arms are directly comparable) while avoiding the documented "white per-bin noise then max() inflates the peak"
pitfall (`heldout_qoi.py`). The difference is the source of the widening: **L5 estimates σ_QOI from
observed-channel scatter; IFT derives it from the physics operator and the learned trust β.**

## 6. Priors and nuisances
- **β prior (the headline new knob, D2):** β is dimensionful, so we center it on the forward model with NO data:
  β* solves median_{j,ω}[ v_j(θ=1,β)/(2|m_j(θ=1)|²) ] = σ_meas² (computed from `realfrf` at nominal θ=1 — a pure
  forward-model scaling constant). Default prior **log β ~ Normal(log β*, 2.0)** (≈1.7 decades each way; matches
  the consistency-toy log-sd). Swept ×{0.33, 3} and center-shifted in the sensitivity gate.
- **θ prior:** LogNormal(0, 0.25) on the 9 groups (StatFEM). The fair comparison calibrates only the **4
  FIM/strain-energy-identifiable groups** (bottom_box, top_box, plates, cross_beam); others fixed at 1.0. Full-9
  is a sensitivity.
- **Global units-gain c:** Normal(c₀, 1.5), c₀ = quality-weighted median of log|H_meas| − log|H_FEM| on observed
  channels (the ~×100–500 mass-norm/g constant, StatFEM D4). Refit per draw on observed channels for a fair
  held-out level (as L5 does).
- **τ₀ = 1e-12** numerical jitter; **σ_meas = 0.15** inherited; **ζ = 0.01** inherited (η = 2ζ).

## 7. Inference + convergence
NUTS (numpyro, x64, 4 chains, dense mass, target-accept 0.9, tree depth 8), all-variable convergence gate
including β (R̂ ≤ 1.05, ESS ≥ 200, divergence fraction < 2%). If a β-resonance multimodality fires (β·AᴴA
near-singular at resonances), escalate to TMCMC (reuse the byte-identical `tmcmc.py`) and report evidence — the
same documented NUTS→TMCMC protocol as the StatFEM run (D9/D10). A non-converged arm is never presented as
converged (D3): it is flagged and excluded from the headline median.

## 8. Faithfulness statement and citations
- Hao, Z. & Bilionis, I. (2024). *Information Field Theory ...* arXiv:2306.02150 — physics-informed prior measure
  on the function space of system responses; learned inverse-temperature.
- Alberts, A. & Bilionis, I. (2023). *Physics-Informed Information Field Theory ...* arXiv:2301.07609 — PIFT
  ∝ exp(−β∫R²), β as inverse temperature.
The papers use SGLD/VI because their fields are NONLINEAR. Here the field is LINEAR given (θ,β), so the field
*statistics* are closed-form (mean/variance above); the ONLY approximation is the log-Rician→Gaussian moment
match on the magnitude observable (§4), which we label everywhere. This is a faithful, tractable adaptation —
not a copied implementation. No results, code, or assets are copied from any IFT/PIFT/StatFEM repository.
