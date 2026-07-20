# Validating a StatFEM digital twin on the REAL ShockSat — human-review packet (Card A)

Runner: Claude Code. Human: Andrew Voss. Advisor objective (Ilias Bilionis): *evaluate the StatFEM approach —
build it, evaluate it, identify its gaps, and suggest improvements.* Status from the study checker: **see
`checker_report.json`** (do not read claims here as stronger than that file). Every number below traces to a JSON
in `out/` or a figure in `figures/`.

> Plain-language note (ML/stats terms defined on first use; structural-dynamics terms used directly).
> **StatFEM** = "statistical finite-element method": calibrate a finite-element (FE) model's uncertain parameters
> against measured data *and* add a statistical **discrepancy** term that absorbs the part the model structurally
> cannot capture (model-form error), so predictions come with honest uncertainty bands.

---

## 1. Method summary (read this first)

**Test article / data count.** Plain 9-group ShockSat primary structure (no coupled tray). Observable = the
**REAL measured frequency-response function (FRF)** |H₁(ω)| in g/lbf from **one** impact-hammer hit (hit-001),
reprocessed as a single-impact FRF (2 ms force window + exponential response window, N=200000, Δf≈1.25 Hz),
band 45–260 Hz (173 frequency points). Drive = the FEM node nearest the physical impact point (node 22951, +X).
hit-001 (Test07_ImpactHammer_990X_001) is logged **"Good Data"** in the test log. **84** accelerometer channels
map to kept FEM nodes AFTER excluding the sensors the instrumentation/test log flags as bad (D20/D21): **ch101**
("bad at installation … all tests") and **ch29–31** ("60 Hz noise … all tests", inside our band). **Data-
availability caveat (YELLOW): 1 hit, 1 impact location** — only the observed/held-out channel **split** can be
randomized (impact-location and hit axes collapse to one each; labeled reduction).

**Model form.** FEM matched-path accelerance H(ω;θ) = −ω² Σ_k (φ_s,k φ_d,k)/((1+iη)λ_k − ω²) [g/lbf], where
θ = 9 group stiffness multipliers, λ_k = ω_k² and φ_k = mode shapes from eig(K(θ)), η = 2ζ loss factor. A single
global **units-gain** nuisance c reconciles a ×~100 mass-normalization constant (g/slinch).

**Two likelihood choices (the central comparison).** "Likelihood" = how we score model-vs-data; the choice turns
out to decide everything.
- **Whole-FRF magnitude** (every |H(ω)| point): residual R = log|H_meas| − (log|H_FEM(θ)| + c), with a Gaussian
  discrepancy. Arms: M0 none, M1 iid, **M2 Schneider** (correlated over frequency×space), **M3 orthogonal-Schneider**
  (M2 projected off the θ→FRF sensitivity span — the method nominally "under validation").
- **Modal peak-frequency feature** (L5): match FEM eigenvalues ω_k²(θ) to the measured peak frequencies extracted
  from the same FRF (Kiran et al. 2025, §4.3 — the FE-updating field's standard for real structures).

**Inferred vs fixed.** Inferred: θ (or a 4-group identifiable subset), the discrepancy scale σ_w, the gain c,
modal-frequency error σ. Fixed (with sensitivity noted): ζ=0.01 (+ exponential-window damping), correlation
lengths/split at Schneider's posterior values, σ_meas=0.15. θ has **no ground truth on real data** → the
parameter study is scored on **held-out-sensor QOI** + Fisher-information identifiability, not θ-recovery.

**Sampler.** NUTS (gradient MCMC) as the default + multimodality **detector**; when it fires (the named
"local-identifiability" signature), escalate to **TMCMC** (tempered sequential MC, multimodal-capable, also
returns model **evidence**). Documented deviation from the NUTS-only default, per the field standard (Schneider
used BUS+Subset-Simulation). All convergence is reported on every variable (R̂, ESS, divergences).

---

## 2. The headline verdict

**Meaningful StatFEM on the real ShockSat is achievable — but only through the modal-feature likelihood; the
whole-FRF-magnitude likelihood is a documented dead end on a coarse FEM.**

1. **Whole-FRF magnitude fails, robustly and for a understood reason.** NUTS R̂ 104, TMCMC R̂ 129, and even a
   *faithful* additive-correlation Schneider M2 with an informative prior gives R̂ 2.58 (n=4000×4); σ_w runs away
   to ~12–15. **Simulation A** explains it quantitatively (§4): this likelihood converges only when the FEM aligns
   peaks within **~1%**, and our coarse FEM is off by several %. The held-out-sensor QOI from these arms is
   uselessly wide (interval score ~1e17 — "100% covered" only by being absurd; `fig_method_comparison`).
2. **Modal-feature works.** L5 converges (R̂ 1.002, ESS 2388, 0 divergences), predicts held-out modal frequencies
   6/6, and its held-out-**sensor** QOI is **calibrated**: across **25** random channel splits, peak-|H| coverage
   median 0.88 [0.75–0.99], z-score std ≈ 0.75 (≈1 = calibrated), L5 converged on 100% of splits
   (`fig_mc_distributions`).
3. **The honest ceiling is the model+data, not the Bayesian method.** The working twin is calibrated but **wide**
   (≈×2.7 on peak amplitude). **Simulation B** shows per-mode damping does *not* sharpen it. **Correction (D20):**
   the ceiling is NOT mainly "wrong FEM mode shapes" — the proper modal-survey (`.ash`) shapes have **MAC ≈ 0.73**
   with the FEM under correct (MAC-based) matching (clean low modes 0.88–0.98), so the shapes are *decent*. The
   ≈×2.7 ceiling is a **combination**: residual shape error (MAC 0.5–0.7 on several dense modes) + frequency
   misalignment near sharp resonances + dense-mode superposition + damping. Two concrete, actionable causes
   surfaced: (a) the mode shapes extractable from the **single-impact FRF** are unusable (operating-deflection
   shapes, MAC≈0.04, because 24 in-band modes superpose); (b) **frequency-based mode matching mis-pairs the dense
   modes** (mode crossings) — MAC-based matching is required. **The sharpening lever that WORKS (D22):** putting
   shapes in the likelihood to constrain θ does *not* sharpen (L6/L10 — θ can't move the shapes), but **inferring
   the mode-shape *field* directly** (Beck mode-matching-free on the `.ash` survey shapes: Rayleigh quotient + an
   orthogonal-MAC term) **converges (R̂ 1.004, 0 divergences) and sharpens** the held-out amplitude (interval
   671→545 at fixed mode count) while staying calibrated (coverage 0.97). Other levers: a finer mesh; measured
   per-mode damping. Not damping alone, not a cleverer sampler.

**Engineering consequence.** For a conservative apparent-mass / vibration-environment twin that should *widen
honestly when the model is wrong* rather than report a confident wrong number, the modal-feature twin is
**fit-for-purpose**. For sharp point prediction of peak responses, the coarse FEM is the binding constraint.

---

## 3. Whole-FRF arms under TMCMC (Q-A, Q-B) — `fig_arms_comparison`

Faithful additive Schneider, n=4000×4, 4 identifiable groups, real data (`out/tmcmc_faithful_*.json`):

| arm | R̂ | ESS | log-evidence | σ_w | reading |
|---|---|---|---|---|---|
| M0 no-disc | 1.000 | 4716 | −105485 | — | converges but catastrophic fit |
| M1 iid | 1.041 | 47 | −2859 | 1.86 | informative prior holds (no 9.8 runaway) |
| **M2 Schneider** | 2.577 | 1 | **−2717.5 ±1.0** | 12.4 | best fit; θ multimodal |
| **M3 orthogonal** | 1.112 | 17 | **−2822.1 ±0.4** | 12.6 | **starved** (−105 logZ vs M2) |

- **Q-A:** faithfulness (additive correlation + informative prior) *stabilizes the evidence* (±1.0 vs the
  unfaithful ±739) and improves fit, but does **not** converge θ — the sharp peak-misalignment residual lives in
  the null space of any smooth discrepancy.
- **Q-B:** the **orthogonal projection starves the discrepancy** — M3 is ~105 log-evidence below M2 (Bayes factor
  e¹⁰⁵), because the dominant misfit lives in exactly the θ-span M3 removes. It *helps sampling* (R̂ 1.11 vs 2.58)
  but *hurts fit*. Not a blanket indictment (orthogonalization's purpose is θ de-biasing) — a concrete gap for a
  coarse FEM.

---

## 4. Simulation A — when does whole-FRF work? — `fig_fem_error_sweep`

SYNTHETIC controlled study (`out/fem_error_sweep.json`): truth = FEM(θ=1) with a per-mode frequency perturbation
(1+δ·ξ)², ξ=±1 (same mode shapes ⇒ pure peak-misalignment of magnitude δ). Faithful M2, TMCMC n=2000×4.

| δ | 0% | 1% | 2% | 5% | 10% | 20% |
|---|---|---|---|---|---|---|
| R̂ | 1.000 | 1.000 | 1.057 | 2.04 | 4.31 | 1.14 |
| σ_w | 0.03 | 0.44 | 3.76 | 3.19 | 3.26 | 4.39 |
| converged | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

**Convergence boundary δ\* = 1%.** δ=0 reproduces the synthetic-study convergence (σ_w≈0); σ_w jumps 0.44→3.76
across the boundary. **Pre-test design number: align FEM peaks to ~1% (≈0.5–2.6 Hz here) or the whole-FRF
magnitude likelihood is unusable.** Real ShockSat misalignment ≫1% ⇒ the real-data negative is FEM coarseness,
not method failure.

---

## 5. Simulation B — does per-mode damping sharpen? — (honest negative)

`out/modal_amp_feature.json`: extend L5 with peak **amplitudes** and a per-mode loss factor η_r. Result: R̂ 55.8,
ESS 2, **174 divergences** (does not converge); σ_a≈3.17; per-mode η barely moves; held-out coverage 0.34.
**Verdict: per-mode damping does not rescue the wide bands.** Follow-on mode-shape work (L6 freq+MAC, L8 Beck
mode-matching-free) added MAC/shape terms; key findings (D20): (i) the **MAC scalar likelihood is numerically
clean** (L6: 2 divergences) — Sim B's 174 divergences were the per-component amplitude form, not MAC; (ii) on the
single-impact FRF the **shape data itself is unusable** (operating-deflection MAC≈0.04), so L6 was null for *data*
reasons; (iii) the **modal-survey `.ash` shapes are usable** (MAC≈0.73 with MAC-matching) — the viable path is a
shape likelihood on `.ash` + MAC-based matching, the subject of the next run.

---

## 6. Held-out-sensor QOI of the working twin — `fig_scoring_suite`, `fig_heldout_frf`, `fig_mc_distributions`

L5 modal-calibrated twin → predict UNSEEN channels' peak-|H| and band-GRMS [g/lbf] (`out/heldout_qoi_L5.json`,
`out/mc_summary.json`). Without an amplitude discrepancy the twin is **overconfident** (coverage 0.12, z-std 14 —
frequency calibration ≠ magnitude calibration); with a marginal QOI-discrepancy estimated on observed sensors it
is **calibrated** (coverage 0.91, z-std≈1) and every proper score improves (informative, not band-padding). The
**wide-band-doesn't-win** guard holds at the QOI level (`out/wideband_demo.json`: a wider band gains coverage
0.96→1.00 but its interval score *worsens* 0.92→7.90). `fig_heldout_frf` shows the twin placing the resonances
(frequencies) while mis-predicting peak amplitudes — the model-form gap, visualized on a held-out channel.

---

## 7. Identifiability & parameter count — `fig_error_participation`, `out/paramcount.json`

Modal/Eigenproblem Identifiability Gate (`out/identifiability.json`): strain-energy decomposition + Fisher-
information eigen-view at the realized discrepancy floor (σ_d0=1.73) + finite-perturbation check. **4 of 9 groups**
clear the floor (bottom_box, cross_beam, plates, top_box, peak strain-energy >30%). The parameter-count study
(`paramcount.json`) compares the 4-group FIM-downselect against all-9 by **TMCMC evidence** (Schneider's Ockham
argument that a parsimonious, better-identified parameterization wins).

---

## 8. Honest limitations (YELLOW)

- **1 hit, 1 impact** → only the channel split is randomized; no multi-average coherence (a single-hit quality
  weight is used, labeled). The ≥25-config Monte-Carlo is over **splits only**.
- The whole-FRF arms are **non-converged** (reported, never called "converged"); they appear only as the diagnostic
  + the QOI-uselessness demonstration.
- ζ fixed at 0.01 (sweep deferred); mode matching by nearest-frequency (MAC refinement deferred); the held-out QOI
  discrepancy is a **marginal** transfer (spatial kriging deferred — with σ_w≈15 on the whole-FRF arms it would not
  rescue them).
- **Node mapping is NOT the cause of the held-out misses (quantified, `out/mapping_sensitivity.json`).** The
  observation operator snaps each sensor to the nearest kept FEM node (impact 0.11 in; response median 0.15 in, max
  0.75 in). Re-predicting the 8 worst-mapped channels with shape-function interpolation instead of the snap shifts
  the predicted peak by a **median 0.8%** (max 13%), versus the measured mismatch of **0.1×–4.7×** — so the misses
  are genuine model-form, not the mapping. Reduction fidelity is exact (reduced-vs-inherited eigenfreqs 3e-10,
  observation rows 1e-15); the held-out-FRF figures overlay the as-received θ=1 FEM with +3/+6 dB PSD margins
  (×1.41 / ×2.0 amplitude). *Caveat correction (D21):* an earlier "1000× mode-shape error" example used **ch101**,
  which the test log flags **bad at installation (all tests)** — so that channel is now EXCLUDED (bad data, not
  model error); the figures use a representative channel instead.
- **The consistent held-out failures are PHYSICALLY interpretable (instrumentation/TestLog review, D21).** Across
  25 splits, ~7 channels miss the band nearly always (clean raw data — no clipping/saturation, sensor ranges
  100/10/5 kg appropriate, dynamic range uncorrelated with pass/fail). Mapping them to the instrumentation list:
  **every one is on the +X (impact/source) face and at a structural interface** — bulkheads (ch40,69), a bolted
  joint (ch52), the strut base (ch92), the dish (ch98), the source face (ch4,27). So the residual ceiling is
  **joint/interface model-form + near-field dynamics on the impact face** — the classic hard part of StatFEM — not
  a sampler, mapping, or data defect. Improvement levers: model the bolted-joint/bulkhead interfaces (stiffness +
  damping) and the near-drive local dynamics; or accept calibrated-but-wide there and flag those channels.
- Simulations A and B are **synthetic/exploratory** controlled studies (labeled), used to explain and bound the
  real-data result, not to make a real-data claim.

## 9. Assumptions, parameters, and choices ledger — everything that could move the result

Every non-obvious assumption, fixed parameter, and modeling/processing choice, with its value, why, and **Impact**
(HIGH = could change the *verdict*; MED = shifts numbers materially; LOW = minor). "Source" = where it's set.
This is the honest "what we baked in" list; the ones marked HIGH are where a reviewer should push.

### A. Observable & signal processing
| Choice / parameter | Value | Rationale / source | Impact |
|---|---|---|---|
| Observable = matched-path **single-impact FRF** \|H₁\| (not Welch, not SOL111) | force window 2 ms + exp response window, N=200000, Δf≈1.25 Hz | prior Welch coherence was a processing artifact (D1); SOL111 is mismatched-path (forbidden) | **HIGH** — defines the whole problem |
| Analysis band | **45–260 Hz** (173 lines) | resonance-rich, above rigid modes, single-hit SNR ok | **HIGH** — sets which modes drive everything; excludes a 117/118/125 Hz dense cluster |
| Frequency resolution | Δf≈1.25 Hz (~1–2 pts/peak at ζ≈0.5–1.5%) | native FFT bin; peaks under-resolved | MED — under-resolved peaks widen the magnitude residual |
| Single hit (1 of 4 raw) | hit-001 only | only 1 raw hit on disk; no multi-average coherence | **HIGH** — no real coherence; the MC has only the split axis |
| Single-hit **quality weight** | w=[S/(S+25th-pct floor)]·[\|F\|²/(\|F\|²+5·force-floor)] | coherence substitute (D5) | MED — re-weights the magnitude likelihood |
| Exponential-window added damping ζ_w | ≈0.25–1% (60–240 Hz) | window end-value 0.05, N=200000 | MED — inflates effective damping; folded into ζ |
| **Global units-gain** c (g/lbf scale) | fit per draw, prior N(5.6, 1.5); ≈×100–500 | reduced-basis mass-norm/g constant (D4) | MED — a level nuisance; biases the peak QOI (+0.7 log) |
| Sensor → **nearest kept FEM node** snap | impact 0.11 in; response median 0.15, max 0.75 in | tap grids aren't real FEM nodes | LOW–MED — quantified ≤1% on QOI (mapping_sensitivity.json) |
| **Bad-channel exclusion** | ch101 (install), ch29–31 (60 Hz) | instrumentation/TestLog (D21) | LOW — aggregate ≈ unchanged |
| Dynamic-range eligibility | DR ≥ 30× | meaningful QOI only | LOW |
| Quadrature mode shapes from FRF | Im[H] at peaks (L6/L8) | found UNUSABLE (MAC≈0.04, dense modes) | (rejected — informs L10) |
| Mode shapes for L10 | `.ash` EMA survey (33 modes, 76 nodes) | proper modal test; MAC≈0.73 | **HIGH** for the shape-likelihood arm |

### B. FEM & model form
| Choice | Value | Rationale / source | Impact |
|---|---|---|---|
| Test article | **plain 9-group ShockSat**, no coupled tray | inherited, NASA-correlated FEM | **HIGH** |
| Reduced model | 74-dim, **mass M = I**, K(θ)=A_fix+Σθ_gA_g | affine; reduced-vs-full eigenfreq 3e-10 | LOW (reduction exact) — HIGH that it's COARSE (the ×2.7 ceiling) |
| **Damping** | single constant ζ=0.01 (η=0.02), all modes | "single ζ too limited" (Schneider §5.4) | **HIGH** — drives peak amplitude; per-mode ζ didn't help (Sim B) |
| Damping model | proportional/classical (real modes) | standard; real structure may be non-classical | MED |
| Calibrated groups | 4 identifiable [bottom_box, cross_beam, plates, top_box] of 9 | strain-energy/FIM gate | MED — param-count study |
| Modes in the model | matched in-band only | truncation | MED — missing modes raise the floor |

### C. Priors
| Prior | Value | Rationale | Impact |
|---|---|---|---|
| θ (stiffness mult.) | LogNormal(0, **0.25**), centered θ=1, **independent** across groups | nominal FEM, no injected error (D-real) | MED — width/indep. assumption |
| σ_d / σ_w (discrepancy) | HalfNormal(0.3) → ran away; **faithful = LogNormal(log 1.726, 0.6)** | informative at FIM floor kills the ∞-singularity (D10) | **HIGH** — the prior choice decides the variance runaway |
| Schneider lengths/split | **fixed** l_f=10 Hz, l_z=2000 in, r=0.82 | Schneider posterior (not learned) | MED — learning them is deferred |
| σ_meas (iid floor) | **0.15** (log) | measurement+window+map floor (assumed) | MED |
| modal-freq error σ_w2 | HalfNormal(0.15) | weakly informative | LOW |
| MAC error σ_mac | HalfNormal(0.3) | weakly informative | LOW |
| gain c | Normal(5.6, 1.5) | empirical offset | LOW |

### D. Likelihood
| Choice | Value | Rationale | Impact |
|---|---|---|---|
| **Whole-FRF magnitude vs modal-feature** | both tested | the central fork | **HIGH** — *the* verdict driver |
| Magnitude in **log\|H\|** | yes | compresses peaks | MED |
| Modal likelihood | eigenvalue match (Kiran §4.3) | well-behaved | **HIGH** (the working path) |
| **Mode matching** | nearest-frequency ≤12% → **MAC-matching (L10)** | freq mis-pairs dense modes (D20) | **HIGH** — wrong matching kills the shape term |
| Consensus mode extraction | histogram-of-peaks, ≥4 ch, prom 0.06, bin 1.5 Hz, tol 2.5 Hz | robustness | MED |
| Held-out QOI | **peak \|H\|** + band-GRMS | engineering quantity | **HIGH** — different QOI → different story |
| Held-out discrepancy | **marginal** QOI-level logN(0,σ_QOI), σ_QOI from observed | avoids per-bin max-inflation; spatial kriging deferred | **HIGH** — sets the band width/calibration |
| Peak-weighting / quality-weighting | power=2 / quality w | "missing a peak ≫ a valley" | MED |
| Orthogonal projection (M3) | off θ→FRF Jacobian span | the method under validation | **HIGH** (Q-B: it starves the discrepancy) |
| Additive vs Kronecker covariance | additive (faithful Schneider) | retains correlation | MED |

### E. Sampler & convergence
| Choice | Value | Impact |
|---|---|---|
| Sampler protocol | NUTS detector → TMCMC if multimodal | MED (honest labeling; TMCMC for evidence) |
| NUTS | 4 chains, target 0.9, dense mass, tree depth 6–10, 1000+1000 | MED |
| TMCMC | n=1500–4000, ≥4 independent runs, n_mcmc 8, target CoV 1 | MED |
| **Convergence gate** | R̂≤1.05, ESS≥200, div<2% | **HIGH** — defines "converged" / the YELLOW |
| Predictive draws | 300–400 | LOW |
| eigh differentiability | eigVALUES clean; eigVECTORS pathological (Sim B 174 div) | **HIGH** for shape/amplitude likelihoods |

### F. Validation & scoring
| Choice | Value | Impact |
|---|---|---|
| Train/test axis | **channel split only** (1 impact, 1 hit) | **HIGH** — labeled reduction; no impact/hit generalization tested |
| MC | ≥25 random splits, obs_frac 0.6 | MED |
| Headline metric | proper scores (interval/CRPS/logpd); coverage secondary | **HIGH** — coverage alone is fooled (fig_method_comparison) |
| Interval level | 95% (α=0.05) | LOW |
| Param-count winner | by TMCMC evidence + FIM (tie-break) | MED |
| dB margins shown | +3/+6 dB **PSD** = ×1.41/×2.0 amplitude | LOW (display) |

### G. Controlled synthetic studies (Sim A/B) — clearly labeled synthetic
| Choice | Value | Impact |
|---|---|---|
| Sim A perturbation | per-mode (1+δξ)², ξ=±1 fixed seed; δ∈{0,1,2,5,10,20}% | **HIGH** for the δ\*≈1% boundary (frequency-only error, same shapes) |
| Sim B per-mode ζ prior | LogNormal(log 0.02, 0.7) | MED |

### H. Numerical / environment
| Choice | Value | Impact |
|---|---|---|
| Precision / threads | float64, OMP=1, .venv_nuts (numpyro/jax x64) | LOW (correctness guard) |
| Eigenvalue clip | 1e-9 | LOW |
| Reduced basis | V_keep 80-dim → T transform (recon 1e-14) | LOW |

**The handful that most likely move the *verdict*:** the observable+band (A), the whole-FRF-vs-modal likelihood (D), the single constant damping (B), the discrepancy prior that controls the variance runaway (C), the held-out QOI + marginal-discrepancy choice (D), the channel-split-only validation (F), and the δ-perturbation design of Sim A (G). Everything else mainly shifts numbers, not the conclusion.

## 10. Reproduce

`bash run_all.sh` regenerates figures + QA + the checker from cached `out/` artifacts (the heavy TMCMC/NUTS steps
are listed there, each resumable). Convergence thresholds, gate logic, and status: `check.py` (immutable) →
`checker_report.json`. Runtime: `runtime.json`.
