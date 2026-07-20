# assumptions_ledger.md — Confidently-Wrong Model-Form-Error experiment

One synthetic realization per (δ, arm, class) unless stated. No test-to-test / flight-to-flight variability is
modeled (single realization = a documented YELLOW scope flag). Float64 everywhere.

| ID | Assumption | Value + units | Rationale / source | Inferred? | Sensitivity priority |
|----|-----------|---------------|--------------------|-----------|----------------------|
| A1 | Forward model | modal-ROM FRF `core.frf_np` (Eqs 4,11,12), mass-normalized modes, 4 channels, fixed Φ | Yan et al. (2026) updating parameterization; reused unchanged from prior-art scaffold | model form (fixed) | — |
| A2 | Modes (main sweep) | 3 well-resolved modes f=[18,95,280] Hz, ζ=[0.020,0.015,0.020], Φ 4×3 (first 3 cols of `core.default_modes`), Binput=[1,0.6,0.3,0.2] | every mode appears in every channel ⇒ observed channels inform masked ones. **3 modes (not the scaffold's 4): the 720 Hz HF mode is intrinsically bimodal/weakly identified from 2 observed channels even at δ=0 (decisions_log D9) — that HF under-identification is a separate phenomenon, isolated in E-LIMIT.** Per-mode α(3) AND β(3) both inferred. | fixed | low |
| A3 | Modes (E-LIMIT) | `core.local_mode_modes`: mode 4 f=760 Hz is LOCAL to masked Ch3/Ch4 (Φ row3/4 ≈0.9, row1/2 ≈0.05) | makes the peak-shift↔stiffness confound bite the failed-sensor parameter | fixed | — |
| A4 | Frequency grid | `core.freq_grid` 160 log-spaced lines, 5–1000 Hz (geomspace) | matches paper [5,1000] Hz; log spacing resolves low + high modes; resolution shown in discretization note | fixed | medium |
| A5 | Truth | `core.make_truth`: truth = (best modal fit at α_true,β_true,γ_true) × `correlated_logfield` discrepancy | the correlated log-field is NOT representable by modal α/β/γ scalings ⇒ GENUINE model-form error | — | — |
| A6 | **Injected error scale δ (the sweep)** | δ = high-freq discrepancy std ∈ {0.0,0.05,0.10,0.20,0.35,0.50}; low-freq std = δ/6; corr length 0.25 in log-f | δ=0 = no-error CONTROL; growth low→high freq mirrors real twins worsening at HF | — | **HIGHEST** |
| A7 | Truth modal params (main) | α_true=[0.95,0.95,0.95] (3 modes), β_true=1, γ_true=GAMMA0=0.02 | mild uniform softening; keeps the story about discrepancy not parameter extremes | recovered as θ | — |
| A8 | Measurement noise | σ_meas = 0.05 (log-amplitude), σ_phase = 0.05 | paper-scale measurement noise; the ONLY noise the naive arm (A1) admits | fixed | medium |
| A9 | Observed / held-out | Observed = Ch1,Ch2 (fit); Held-out = Ch3,Ch4 (masked, predicted, scored post-hoc) | the paper's A3 sensor fault; held-out = the trust test | — | medium (varied in sensitivity) |
| A10 | Inferred variables | per-mode α (4), per-mode β (4), γ (1), σ_d (1, A2/A3 only) | the updating parameterization + the discrepancy scale | inferred | — |
| A11 | Priors | log α ~ Normal(0,0.15)/mode; log β ~ Normal(0,0.5)/mode; log γ ~ Normal(ln 0.02,0.2); σ_d ~ HalfNormal(0.3) | scaffold priors; stated, not silently changed | fixed | low |
| A12 | A1 naive arm | σ_d ≡ 0; likelihood = iid Normal(log\|H\|, σ_meas) on observed channels only | Bilionis's "no mechanism for model error" arm; must still CONVERGE | — | — |
| A13 | A2 disc-aware iid | learns σ_d; obs likelihood Normal(log\|H\|, sqrt(σ_meas²+σ_d²)) iid over frequency | output-side iid discrepancy | inferred σ_d | — |
| A14 | A3 disc-aware correlated | learns σ_d + Schneider-style correlated discrepancy: cov = σ_d²·K_corr(0.25) + σ_meas²·I via eig-form | smooth correlated discrepancy structure matching the injected field class | inferred σ_d, corr fixed | — |
| A15 | Convergence gate | ≥4 chains, exp-reparam (non-centered), max R-hat ≤1.05, min ESS ≥200 ALL vars, div-frac <2% | AGENTS.md gate; "NUTS active" requires PASSING diagnostics | — | — |
| A16 | NUTS settings | warmup 1000, samples 1000, 4 chains, target_accept 0.92 (0.95 dense), init_to_median; A3 dense mass | tuned in prior art for the correlated likelihood | — | — |
| A17 | E-LIMIT bias | +15% coherent peak-frequency shift on masked virtual target (`reconstruct_virtual` bias_peakshift=0.15) | E4's coherent bias = peak shift ≡ stiffness scaling | — | — |
| A18 | Missing-mode class (sensitivity) | TRUTH = 3 modes (280 Hz scaled by severity∈{0,0.5,1.0}); FIT model drops the 280 Hz mode (keeps 18/95 Hz); severity = 280 Hz participation scale | second error CLASS = structural hidden DOF, à la Phase-1 | — | medium |
| A19 | QOI | held-out masked-channel peak log-amplitude (max \|H\| over 10–900 Hz band), `core.peak_qoi` | the paper's main-peak dB metric, on held-out channels | — | — |
| A20 | σ_d interpretation | σ_d is an EFFECTIVE band-average output-side discrepancy std; it tracks ≈ the band-average of the injected std (which grows δ/6→δ low→high freq), not the peak HF std δ. Reported as trend/level, not literal equality. | the injected field is heteroscedastic; σ_d is homoscedastic | — | — |

## Uncertainty taxonomy (kept distinct, per AGENTS.md)
- **Parameter uncertainty:** posterior on α,β,γ (Fig C).
- **Observation noise:** σ_meas = 0.05 (aleatory, fixed, known).
- **Model discrepancy:** σ_d (learned, A2/A3) — the quantity that should track δ (Fig B). δ=injected truth.
- **QOI uncertainty:** held-out peak-amplitude posterior predictive interval (coverage in Fig A / D).
- Forcing uncertainty / build-to-build / flight-to-flight: NOT modeled here (single realization; YELLOW flag).

## Absolute vs normalized
Injected error δ is an ABSOLUTE log-amplitude std (shown directly in Fig B against learned σ_d). Coverage
fractions are NORMALIZED diagnostics (fraction of held-out lines / QOIs covered at nominal 95%).
