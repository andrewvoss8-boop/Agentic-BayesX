# assumptions_ledger.md — IFT real-validation study

Two layers: (A) INHERITED from the StatFEM run `statfem_real_validation_20260617` (cited, NOT silently changed),
and (B) IFT-SPECIFIC, with value + rationale + sensitivity priority. "Sensitivity priority": HIGH = most likely
to change the verdict (swept in §11), MED = checked, LOW = fixed/documented.

## A. INHERITED (cite the StatFEM ledger; do not change any value)
| ID | Assumption | Value | Source / rationale | Sens. |
|----|------------|-------|--------------------|-------|
| A1 | Analysis band | 45–260 Hz, native df≈1.25 Hz (~172 lines) | StatFEM A4 / real measured grid | MED (§11 sub-band) |
| A2 | Observable | log\|H\| accelerance magnitude (g/lbf) | StatFEM whole-FRF; SAME as M2 (apples-to-apples) | LOW (the point) |
| A3 | Damping | ζ = 0.01 (hysteretic η = 2ζ) | StatFEM D10 | MED |
| A4 | Measurement floor | σ_meas = 0.15 (iid log) | StatFEM `real_arms.SIGMA_MEAS` | HIGH (§11) |
| A5 | θ prior | LogNormal(0, 0.25), 9 groups | StatFEM | MED |
| A6 | Identifiable subset | 4 groups: bottom_box, top_box, plates, cross_beam | StatFEM FIM/strain-energy gate (4-of-9) | MED |
| A7 | Global units-gain | c ~ Normal(c₀, 1.5); c₀ = quality-wt median offset (obs only) | StatFEM D4 (~×100–500 mass-norm/g) | LOW |
| A8 | Bad channels | exclude ch101, ch29–31 | TestLog (install / 60 Hz) | LOW |
| A9 | Validation axis | channel split ONLY (1 impact, 1 hit) | StatFEM D2 — labeled reduction (YELLOW) | LOW (caveat) |
| A10 | Single-hit quality weight | S(f)/(S(f)+N₀) (1-hit coherence substitute) | StatFEM D5 (YELLOW) | LOW (caveat) |
| A11 | QOI | peak \|H\| + band-GRMS [g/lbf], held-out sensors | StatFEM card | LOW |
| A12 | Forward / reduced model | 74-dim, M=I, K(θ)=A_fix+Σθ_gA_g | StatFEM `realfrf`/`core` (byte-identical) | LOW |

## B. IFT-SPECIFIC (value + rationale + sensitivity)
| ID | Assumption | Value | Rationale | Sens. |
|----|------------|-------|-----------|-------|
| B1 | Field | reduced complex response u ∈ ℂ⁷⁴ per drive frequency | the PIFT "field"; matches the forward basis | LOW |
| B2 | Physics residual / operator | R = A(θ,ω)u − f, A=(1+iη)K(θ)−ω²I, f = unit force @ drive DOF | faithful PIFT residual; same drive as StatFEM | LOW |
| B3 | Physics-informed prior | π(u\|θ,β) ∝ exp(−(β/2)‖Au−f‖²−(τ₀/2)‖u‖²) = CN(μ_u,Σ_u), μ_u→A⁻¹f | the papers' central move (physics in prior) | LOW |
| B4 | **β prior (headline knob)** | log β ~ Normal(log β*, 2.0); β* set s.t. median field-var = σ_meas² at θ=1 (NO data) | β dimensionful → center on forward; sd matches consistency toy | **HIGH (§11: sd ×0.33/×3, center shift)** |
| B5 | **Marginalization** | log-magnitude **moment approximation** (E≈log\|m\|, Var≈v/(2\|m\|²)) of the log-Rician | linear field → closed-form moments; log\|·\| nonlinear → moment-match (D0, Andrew). Exact at high SNR; weak in deep antiresonances (downweighted there) | **HIGH (the honest deviation; reported per-bin SNR)** |
| B6 | Resonance regularization | hysteretic (ηλ_k)² > 0 floors D_k; τ₀ = 1e-12 numerical jitter only | the damping (physics) is the regularizer, not an ad-hoc ridge | MED |
| B7 | Held-out QOI widening | physics-derived field std as a QOI-level log-normal (peak: at peak freq; band: energy-wt) | mirrors L5 QOI-disc STRUCTURE; avoids white-per-bin-max() peak inflation | MED |
| B8 | Sampler | NUTS 4 chains dense mass depth 8, x64; TMCMC escalation if multimodal | AGENTS.md default + StatFEM D9/D10 protocol | MED |
| B9 | Predictive draws | n_draws = 300 subsampled from the posterior | matches L5 (`heldout_qoi` 400 / `mc_heldout` 300) | LOW |

## Uncertainty taxonomy (which knob carries which uncertainty)
- **Parameter uncertainty:** θ posterior (4 identifiable groups).
- **Model-form / field uncertainty:** β-controlled field variance v_j/(2\|m_j\|²) — the IFT analog of StatFEM's
  σ_d discrepancy. This is the headline contrast: IFT derives it from the physics operator; StatFEM (M2) fits a
  free σ_d² × Kronecker discrepancy; L5 estimates a marginal σ_QOI from observed-channel scatter.
- **Observation noise:** σ_meas (iid log floor) + the 1-hit quality weight.
- **Aleatory / build-to-build / flight-to-flight:** NOT modeled (single hit, single impact — A9/A10 YELLOW).
- **Discretization:** reduced-basis dimension + frequency-grid density — the IFT invariance sub-test (§8) varies
  these and reports the θ/QOI spread vs the StatFEM whole-FRF arm.

## Data count (explicit)
1 structure, 1 impact location, 1 hit (hit-001), ~80 DR-eligible mapped channels split obs/held-out per seed,
≥25 seeds. NO repeated tests/flights; build/test variability NOT modeled (labeled reduction, A9).
