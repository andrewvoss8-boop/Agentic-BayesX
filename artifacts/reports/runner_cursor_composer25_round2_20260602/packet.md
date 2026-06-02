# Human-Review Packet — Round 2 Sequential Vibe → Modal → Flight

Runner: **Cursor Composer 2.5** (isolated copy `Agentic_BayesX_runner_cursor_composer25_r2`). Date: 2026-06-02.

## Round-2 priority deliverables (see `priority_deliverables.md`)

| Artifact | Path |
|---|---|
| Interface response PSD vs smoothline (GIF, 11 flights) | `figures/07_interface_response_psd_vs_spec_evolution.gif` |
| Final interface PSD vs spec | `figures/10_interface_response_psd_vs_spec_final.png` |
| Flight forcing draws vs original +6 dB | `figures/08_forcing_overlay_discrete_flights.png` |
| Tray 3*GRMS vs vibe refs (43.9 / 28.3 g) | `figures/09_tray_3grms_vs_vibe_test_refs.png` |
| Resolution sensitivity | `resolution_sensitivity.json`, `figures/11_resolution_peak_zoom.png` |

**Quantity contract (interface acceleration response PSD):** numerator = interface (dof0) acceleration squared spectral density; denominator = Hz bandwidth; units g^2/Hz; excitation = flight force at m1; coupled dome/tray; compared to smoothline vibe qualification spec as envelope reference.

**Convergence (full likelihood, all sampled sites incl. `dome_build_raw` / `tray_build_raw`):** max rank-normalized split R-hat = 1.0028; min bulk ESS = 901; min tail ESS = 946; divergences = 0. `nuts_active` / `converged_all_variables` = true only when these pass (see `nuts_diagnostics.json`).

Replay: `bash scripts/run_runner_cursor_composer25_round2.sh`

---

# Baseline method summary (inherited from Opus 4.8 implementation)

Runner baseline: **Claude Code Opus 4.8** NUTS code path. Date: 2026-06-02.
Sampler: **NUTS/HMC (NumPyro 0.19.0 / JAX 0.4.30)** — real run, not Metropolis.
One-command replay: `bash scripts/run_runner_claude_opus48.sh`.

> A checker pass is NOT proof of physical correctness. Read the quantity contracts,
> `known_failures.md`, and `review_request.md` alongside this packet.

---

## 1. First-pass method & likelihood summary

**Engineering decision supported.** After a tray vibe test, dome + coupled modal tests, and a
sequence of flights, how confident can we be in the tray random-vibration environment
(tray 3*GRMS) for a *future* build/flight, and how much do build-to-build and sensor-noise
scales matter? Success metric: calibrated tray 3*GRMS QOI intervals (95% / 99%) plus recovered
natural frequencies, damping, and learned variability scales.

**Model form (2DOF, dome=`m1`=1.0 kg, tray=`m2`=0.6 kg).**
`Z(ω) = K + iωC − ω²M`, `K = [[k1+k2,−k2],[−k2,k2]]`, `C = [[c1+c2,−c2],[−c2,c2]]`,
`c1 = 2ζ1√(k1 m1)`, `c2 = 2ζ2√(k2 m2)`. Accel/force `H(ω) = −ω² Z⁻¹`. This is the same
assembly used to generate the setup data (forward model reproduces the dataset clean PSD to
relative error ~6.5e-16).

**Likelihood (full / whole-curve model), all in PSD-space dB `factor=10^(dB/10)`:**

- Tray vibe PSD (260 bins):
  `log P_vibe(f) ~ Normal( log|T(k2,ζ2)|² + log S_smooth(f) + b_tray[0], σ_sensor )`
  where `T` is the standalone tray transmissibility and `b_tray[0]` is build-0 tray effect.
- Dome-only modal (180 pts):
  `log|F/a|_dome ~ Normal( log|recip(k1,ζ1)| + 0.5 b_dome[0], 0.5 σ_sensor )`.
- Coupled interface & tray modal (180 pts each):
  `log|F/a| ~ Normal( log|ch(k1,k2,ζ1,ζ2)| + 0.5 b_{dome/tray}[0], 0.5 σ_sensor )`.
  (The generator scales complex FRF *magnitude* by `exp(0.5·effect)` with no phase noise, so the
  likelihood is on log-magnitude.)
- Flights (11 flights, scalar 3*GRMS each — the only flight data stored):
  `log(3GRMS_tray[f]) ~ Normal( log(3·√∫|H21(θ)/g|² S_meanF df) + 0.5 b_tray[build(f)], σ_qoi,tray )`
  and the interface analogue with `b_dome` and `H11`. `σ_qoi` is the **fixed** flight-to-flight
  scatter (tray 0.197 / iface 0.150 ln-units) from the known 3 dB Matérn-3/2 forcing GP.

**Peak-feature (lossy) model.** Same priors and flight terms, but the test-stage curves are
replaced by peak/notch features: vibe-PSD peak + three modal notches, each as
`Normal` on log-frequency (σ=0.06) and log-amplitude (σ=0.30). Soft (temperature, β=45) argmax
makes the feature differentiable for NUTS; observed features use a hard quadratic-refined extremum.

**Data count.** vibe 260 pts; modal 180 pts × 3 channels; 11 flights × 2 scalar QOIs; 11 builds.
No test-to-test replicates. Build-to-build modeled (scale learned); flight-to-flight modeled but
**fixed** at 3 dB.

**Inferred:** `k1,k2,ζ1,ζ2` (→ dome/tray fn, damping), `σ_build`, `σ_sensor`, and 22 per-build
log-PSD effects (non-centered). **Fixed/not inferred:** 3 dB flight-to-flight, Matérn-3/2 forcing
covariance (ell=0.08), −6 dB mean force offset, masses, smoothline input, `force_amp/force_fc`
(unused here). **Latent not inferred:** per-flight realized forcing PSD (integrated out via fixed
σ_qoi). See `assumptions_ledger.md`.

**Graphical model (run-specific).**
```
 priors: u_k1 u_k2 u_z1 u_z2        sigma_build_ln      sigma_sensor_ln
            |   |    |    |              |                    |
        (k1,k2,zeta1,zeta2)        b_dome[0..10] ~N(0,sigma_build)  (per-build, non-centered)
            |                          b_tray[0..10]                |
            |                            |  |                       |
   +--------+----------+--------+        |  |          +------------+-----------+
   |        |          |        |        |  |          |            |           |
 vibe    dome       coupled  coupled   build0      vibe/modal    flight        (modal amp
 PSD     modal      iface    tray      anchors      sensor sd     QOI sd        sd = 0.5*sensor)
 (260)   (180)      (180)    (180)                                 |
   \________\__________\________\____ log-curve likelihood        flights f=0..10:
                                                                  log(3GRMS_tray) ~ N(., sigma_qoi,tray FIXED 3dB)
                                                                  log(3GRMS_iface)~ N(., sigma_qoi,iface FIXED 3dB)
```

---

## 2. NUTS/HMC diagnostics (both models)

| | Full FRF/PSD | Peak feature |
|---|---:|---:|
| Divergences | 0 | 0 |
| Max R-hat | 1.0024 | 1.0019 |
| Min ESS | 942 | 1495 |
| Final step size | 0.0521 | 0.0367 |
| Max tree depth (cap 10) | 7 | 8 |
| Mean accept prob | 0.949 | 0.892 |

4 chains × (1000 warmup + 1000 draws). Full details in `nuts_diagnostics.md` / `.json`.

---

## 3. Posterior results (full vs peak) vs generating truth

| Quantity | Truth | Full mean [95%] | Peak mean [95%] |
|---|---:|---|---|
| dome fn [Hz] | 93.50 | 93.55 [93.40, 93.71] | 97.53 [90.25, 105.50] |
| tray fn [Hz] | 86.25 | 86.14 [86.01, 86.28] | 83.56 [77.60, 89.94] |
| dome ζ | 0.0225 | 0.0224 [0.021, 0.024] | 0.020 [0.013, 0.028] |
| tray ζ | 0.0195 | 0.0197 [0.019, 0.021] | 0.020 [0.014, 0.026] |
| σ_build [dB] | 1.50 | 1.75 [0.97, 2.71] | 1.80 [0.94, 2.85] |
| σ_sensor [dB] | 0.75 | 0.74 [0.71, 0.78] | 1.05 [0.04, 2.99] ← ≈prior, **not identified** |

**Headline.** The full whole-curve likelihood recovers all structural parameters tightly and on
truth, and learns the sensor-noise scale (0.74 dB vs 0.75 truth) and build scale. The peak-feature
likelihood is much broader and biased, and **cannot identify the sensor-noise scale** — the
information lives in per-frequency residual scatter that features discard. (Figure
`02_posterior_full_vs_peak.png`.)

---

## 4. QOI intervals (tray 3*GRMS = 3*RMS in g, after flights)

| QOI | 95% interval [g] | 99% interval [g] |
|---|---|---|
| Structural posterior (mean force), **full** | [1.011, 1.052] | [1.004, 1.060] |
| Structural posterior (mean force), **peak** | ~5.8× wider than full | — |
| Future build+flight predictive, **full** | [0.592, 1.815] | [0.490, 2.232] |
| Future build+flight predictive, **peak** | [0.552, 1.776] | [0.463, 2.142] |
| Setup prior-predictive (first build only) | [0.651, 1.460] | [0.613, 1.670] |

- **Interval-width ratio (peak / full), structural QOI: 5.77.** Predictive ratio ≈ 1.0 because the
  predictive is dominated by the shared new-build + fixed-forcing scatter, which masks the
  structural-likelihood difference. Both reported honestly (Figure `04_qoi_intervals.png`).
- The future predictive is *wider* than the setup prior-predictive because it adds a NEW build
  draw from the learned `σ_build`; the setup used only the known first-build effect. This is a
  definitional difference, **not** a regression (see `known_failures.md` item 8).
- Median predictive tray 3*GRMS ≈ 1.03 g matches the observed flight mean (1.07 g).

**95% / 99% flight input force spectra** (Figure `03_input_spectra_95_99.png`): the fixed 3 dB
Matérn-3/2 forcing band about the known −6 dB mean force PSD, `mean·exp(±z·0.691)` with z=1.96 /
2.576. These bands are fixed/known (forcing not learned), shown in N²/Hz on log–log axes.

---

## 5. Figures

| File | Content |
|---|---|
| `figures/01_truth_vs_observed.png` | Clean truth vs observed: tray vibe PSD, dome & coupled modal FRFs (log–log), flight QOI sequence. |
| `figures/02_posterior_full_vs_peak.png` | Posterior histograms (full vs peak) vs truth for 6 quantities. |
| `figures/03_input_spectra_95_99.png` | 95% / 99% flight input force spectra (fixed 3 dB Matérn band). |
| `figures/04_qoi_intervals.png` | Tray 3*GRMS QOI: predictive vs structural posterior; 95/99% interval comparison full vs peak. |
| `figures/05_build_effect_recovery.png` | Per-build dome/tray log-PSD effect posteriors vs generating truth. |
| `figures/06_feature_map.png` | Peak/notch feature locations used by the lossy feature likelihood. |

---

## 6. Quantity contracts (frequency-domain, log axes)

- **Tray vibe PSD** — accel²/Hz [g²/Hz] at tray `m2`; base smoothline excitation; standalone tray.
  Peaks near tray resonance; rolls off per spec at band edges.
- **Reciprocal inertance |F/a|** [kg] — force/accel at the named coordinate; modal impact; **notch**
  (minimum) near resonance (driving-point inertance peaks → its reciprocal dips). Limits → static
  mass at low ω.
- **Flight input force PSD** [N²/Hz] at `m1`; latent Matérn-3/2 flight forcing; coupled config.
- **Tray 3*GRMS** [g] — `3·√(∫ PSD df)` of tray accel; increases with response energy; sensitive to
  damping and forcing. `3*RMS` (g) ≡ `3*GRMS` here.

Full contracts: `assumptions_ledger.md` and the setup packet's `quantity_contracts.md`.

---

## 7. Honesty notes
- Synthetic data was generated by the same parametric model used for inference (no model-form
  error), so full-likelihood recovery is unrealistically clean. Real-hardware discrepancy would
  widen these intervals. See `known_failures.md` for all shortcuts and the soft-argmax / scalar
  flight-QOI / log-magnitude approximations.
