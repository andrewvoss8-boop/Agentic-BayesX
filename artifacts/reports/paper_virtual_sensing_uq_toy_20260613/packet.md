# Packet — virtual-sensing-target credibility toy (paper review + 4 experiments)

2026-06-13. Workspace `artifacts/reports/paper_virtual_sensing_uq_toy_20260613/`.
**One-command replay:** `bash run_all.sh`  ·  **Checker:** `python3 check.py`  ·  **Status:** OVERALL **YELLOW** (41 GREEN / 2 YELLOW / 0 RED — the 2 yellows are deliberate honest-scope flags).

Paper reviewed: Yan, Zhang, Zhou, Sun, Wang, Liu, *Physics-Informed Digital Twin for Spacecraft
Structures under Sensor Faults: Virtual Sensing via a Frequency Attention U-Net and Closed-Loop
Model Updating*, **Aerospace Science and Technology (2026)**, doi:10.1016/j.ast.2026.112794.

---

## 1. Paper review and applicability verdict — HIGH

The paper builds a closed-loop digital twin for a scaled reconfigurable spacecraft (3 joint
configurations A1/A2/A3, excitations 10 Hz & 800 Hz, 4 sensor channels). Three stages: (i) a
**reduced-order FEM (ROM)** FRF baseline; (ii) a **Frequency Attention U-Net (FAU)** that reconstructs
*masked* (failed) sensor channels in the frequency domain — a Fourier Neural Operator learns the global
spectral residual, a gated Transformer decides how much physics-correction to trust per channel; (iii)
**closed-loop updating**: the FAU reconstruction is treated as a "virtual ground truth" and a
*deterministic* constrained nonlinear least-squares fit (`lsqnonlin`, box constraints) updates modal
stiffness scaling α, damping scaling β, and input coupling γ. Headlines: 800 Hz peak-error cut ~76.7 dB;
masked-channel error held to 8–10 dB (vs interpolation up to 48 dB); α drops 0.93→0.89 and γ 2.38%→2.22%
across A1→A3, read as joint softening.

**Why it maps onto our project (HIGH).** Same domain (spacecraft high-frequency Sim-to-Real gap from joint
micro-slip), same updating parameterization as our per-mode frequency/damping calibration, same
under-observability theme, and the paper's own caveat that α/β/γ are "effective ROM-level indicators, not
microscopic joint measurements" is exactly our Brynjarsdottir–O'Hagan honest-scope finding. **The gap we
fill:** the paper updates *deterministically* against a *black-box reconstruction treated as exact*, and
explicitly defers uncertainty quantification ("adaptively weight the credibility of reconstructed virtual
targets") to **Future Work #3**. That deferred UQ *is* our project. This toy implements it and stress-tests it.

---

## 2. Method summary (read first)

- **Forward model:** the paper's modal-ROM FRF (Eqs. 4,11,12), mass-normalized modes, diagonal reduced
  matrices ⇒ `H_c(ω;θ) = γ Σ_i Φ_{c,i}(Φᵀ B)_i / (α_i² ω_i² + jω β_i²(2 ζ_i ω_i) − ω²)`. Four channels
  coupled through a fixed mode-shape matrix Φ, so observed channels physically inform masked ones.
- **Likelihood:** Gaussian on **log-amplitude** FRF (the paper's dB metric, Eq. 21), over the whole
  [5,1000] Hz curve (160 lines). Inferred variables: per-mode α (4), per-mode β (4) or global, γ, and a
  model-discrepancy scale σ_d. Fixed: mode shapes Φ, mode count, noise floors, box constraints.
- **Sensor fault:** Ch3/Ch4 masked (the paper's A3). Observed = Ch1/Ch2 (measured); masked = a **virtual
  ground truth**.
- **The virtual ground truth is a LABELED surrogate**, not the FAU network: true masked FRF + a controlled
  reconstruction error calibrated to the paper's ~8–10 dB masked-channel residual (and, in E4, a coherent
  peak-shift like their ~10.8% pure-FAU shift). We test the *updating stage + its deferred UQ*, not the net.
- **Two updaters on the same target:** (A) deterministic constrained least-squares = the paper's FAU-Up
  (point estimate, virtual target trusted fully); (B) **discrepancy-aware NUTS** = Future-Work #3 (masked
  channels down-weighted by a credibility noise; σ_d learned). NUTS, 4 chains, gate: R-hat≤1.05, ESS≥200,
  div<2%.
- **Trust test:** the TRUE masked-channel FRF and its main-peak amplitude QOI, used post-hoc (paper protocol).
- **Data count:** one synthetic realization per configuration; no test-to-test / flight-to-flight variability.

---

## 3. Experiments and results (all NUTS converged)

### E1 — discriminating: deterministic point vs discrepancy-aware band
Same imperfect virtual target (realized peak error ~4.4 dB) into both updaters.
- NUTS converged: R-hat **1.000**, ESS **3313**, 0 divergences. Learned σ_d ≈ **0.34–0.38** (≈ the injected
  discrepancy floor).
- Deterministic main-peak QOI error: Ch3 **2.8 dB**, Ch4 **10.5 dB**; its tight (measurement-noise) interval
  **misses both** masked channels — **0/2** covered.
- Discrepancy-aware Bayes **covers both** masked-channel QOIs (**2/2**) and **100%** of high-frequency
  held-out lines.
- **Takeaway:** the deterministic point is sometimes ~right, sometimes ~10 dB wrong, with no warning; the
  Bayesian band is honest in both cases. UQ buys *calibrated coverage*, not a smaller point error.
- Figures: `figures/exp1_masked_prediction.png`, `figures/exp1_qoi_coverage.png`.

### E2 — baselines + reconstruction-error sweep (reproduces the paper ranking)
Deterministic Meas-Up (discard+physics, **6.3 dB floor**), Interp-Up (spatial interpolation, **2.7 dB**),
FAU-Up (trust surrogate), plus the Bayesian update, vs reconstruction error 1.3→12.2 dB (all 5 levels
converged, R-hat ≤1.003).
- FAU-Up error tracks reconstruction error in the plausible range (0.7→4.7 dB), then **peels off** —
  observed-channel + box constraints partly *reject* a grossly-wrong surrogate. Trusting a poor
  reconstruction is **worse than discarding the channel** once it crosses the physics floor.
- Bayesian masked-channel coverage **2/2 maintained across all levels**, at the cost of wider intervals.
- Figure: `figures/exp2_baselines_sweep.png`.

### E3 — configuration trend + identifiability (the paper's joint-softening claim, with our FIM gate)
Monotonic joint softening A1→A2→A3; the high-frequency local mode lives at the **failed sensors**.
- Aggregate mean-α trend recovered: medians **0.952 / 0.899 / 0.854** (truth 0.945/0.905/0.860),
  **monotonic with separated 95% intervals** ⇒ the softening trend is identifiable.
- The failed-sensor local-mode α posterior is **5.7×** wider than the observed modes (its damping is the
  FIM's weakest direction) ⇒ **aggregate trend identifiable, the local mode's per-mode stiffness is not**.
  Confirms the paper's "effective ROM-level indicator" caveat and ties identifiability to *which sensor failed*.
- Figures: `figures/exp3_softening_trend.png`, `figures/exp3_identifiability.png`.

### E4 — coherent reconstruction bias (stress test; the deepest result)
A **+15% coherent peak-frequency shift** on the masked reconstruction (like the paper's pure-FAU shift).
Four updates, all converged (R-hat ≤1.001, ESS ≥3497).
- **Unbiased correlated control** recovers α₄ = **[0.833, 0.879]** (covers truth 0.85, says *softening*) ⇒
  the discrepancy-aware method itself is sound.
- **Deterministic** drives α₄ to the box floor **0.50**; **iid** Bayes → α₄ **[0.984, 1.068]**; **correlated**
  Bayes → α₄ **[0.951, 1.019]** — **all three biased variants miss the true α₄ and flip to apparent
  *hardening* (wrong physical sign)**.
- Yet the **amplitude QOI stays covered** by both Bayesian variants ⇒ **QOI coverage ≠ parameter recovery**.
- **Takeaway:** a coherent reconstruction bias is *confounded* with the failed-sensor mode's stiffness
  (a peak shift ≡ a stiffness scaling), and that sensor is the only evidence. UQ — even a correlated
  (Schneider-style) discrepancy — does **not** rescue the parameter; the fix is to **break the degeneracy**
  (keep/restore a sensor that sees the local mode, or a bias-aware credibility model), not more flexible
  discrepancy. This is the project's physics-vs-discrepancy confounding, surfaced on the paper's own workflow.
- Figure: `figures/exp4_biased_reconstruction.png`.

---

## 4. Honest status (green / yellow / red)

- **GREEN:** all four NUTS experiments cleared the convergence gate; E1 shows UQ covers where the
  deterministic point misses; E2 reproduces the baseline ranking and Bayesian coverage robustness; E3
  recovers the softening trend and locates the identifiability limit; E4 validates the method on an
  unbiased control and exposes the coherent-bias confounding with QOI-vs-parameter separation.
- **YELLOW (2 deliberate scope flags, never reported as success):**
  1. The virtual ground truth is a **labeled surrogate** calibrated to the paper's residual, **not the FAU
     network**; we test the updating stage + deferred UQ, not the reconstruction network.
  2. **One synthetic realization** per config, no test/flight variability; α/β/γ are **effective ROM-level
     indicators**, not microscopic joint measurements (the paper's own caveat).
- **RED:** none.

## 5. Runtime
`runtime.json`: active ≈ sum of the four experiments' NUTS+generation time (~85 s); see file for wall-clock.

## 6. Figures
`exp1_masked_prediction.png`, `exp1_qoi_coverage.png`, `exp2_baselines_sweep.png`,
`exp3_softening_trend.png`, `exp3_identifiability.png`, `exp4_biased_reconstruction.png`.
Image-legibility proxy: `image_qa_exp{1..4}.json` (all pass).

## 7. Proposed durable updates (await Andrew — NOT yet applied)
- `notes/runs.md`: add a row for this thread with the checker status copied verbatim.
- `docs/report/project_log.md`: add a thread row (paper-review + method-extension toy; status YELLOW 41/2/0).
- `notes/todo.md`: add the follow-ups below.
- Candidate follow-ons: (a) a bias-aware credibility model (calibrate σ_virtual / a bias term from
  observed-channel residuals or repeated reconstructions); (b) sensor-placement / pre-test design that keeps
  a channel on each local mode (the E4 lever); (c) swap the surrogate for a real reconstruction if the
  paper's data or a comparable dataset becomes available.
