# Assumptions Ledger — Round 2 (Claude Opus 4.8 runner)

Units stated explicitly. dB are PSD/power-space: factor = 10^(dB/10); σ_ln = dB·ln10/10.

| # | Assumption | Value | Units | Source | Inferred? | Sensitivity priority |
|---|---|---|---|---|---|---|
| 1 | Dome/source mass m1 | 1.0 | kg | fresh_2dof Constants | fixed | low |
| 2 | Tray/load mass m2 | 0.6 | kg | fresh_2dof Constants | fixed | low |
| 3 | Dome nominal f_n (prior center) | 110.0 | Hz | fresh_2dof | prior center | med |
| 4 | Tray nominal f_n (prior center) | 75.0 | Hz | fresh_2dof | prior center | med |
| 5 | Dome stiffness k1 | inferred, prior log(k1/k1_nom)~N(0,0.18) | N/m | dataset prior_model_summary | INFERRED | high |
| 6 | Tray stiffness k2 | inferred, prior log(k2/k2_nom)~N(0,0.18) | N/m | dataset prior_model_summary | INFERRED | high |
| 7 | Dome damping ζ1 | inferred, prior log ζ1~N(ln 0.018,0.35) | — | dataset prior | INFERRED | high |
| 8 | Tray damping ζ2 | inferred, prior log ζ2~N(ln 0.026,0.35) | — | dataset prior | INFERRED | high |
| 9 | Sensor-noise scale σ_sensor (ln-PSD) | inferred, HalfNormal(0.30); truth 0.173 (0.75 dB) | ln-PSD | round-1 setup (to-be-learned) | INFERRED | high |
| 10 | Build-to-build scale σ_build (dome,tray) | inferred, HalfNormal(0.50); truth 0.345 (1.5 dB) | ln-PSD | round-1 setup (to-be-learned) | INFERRED | high |
| 11 | Per-build dome/tray effects (×11 each) | non-centered: effect = σ_build·z, z~N(0,1) | ln-PSD | hierarchical model | INFERRED (raw z reported) | high |
| 12 | Flight-to-flight forcing variability | 3.0 (σ), Matérn-3/2, ell=0.08 in ln-freq | dB PSD / — | round-1 setup (KNOWN) | FIXED (not learned) | high |
| 13 | Flight forcing mean offset | −6.0 | dB PSD | round-1 setup (PROJECT assumption) | fixed | high |
| 14 | Original forcing PSD shape | flat (broadband), 0.0201 N^2/Hz | N^2/Hz | dataset | fixed | med |
| 15 | Smoothline test spec | log-log interp of (20,.01)(100,.1)(750,.1)(2000,.001) | Hz, g^2/Hz | human plan | fixed | high |
| 16 | g0 | 9.80665 | m/s^2 | standard | fixed | low |
| 17 | Modal likelihood form | whole-curve **log-magnitude** of FRF (phase dropped) | — | this run (deviation, documented) | — | med |
| 18 | Vibe likelihood form | whole-curve log-PSD, Normal(·, σ_sensor) | — | this run | — | med |
| 19 | Flight 3·GRMS likelihood | LogNormal w/ FIXED forcing+sensor σ_q (forcing integrated out via MC) | — | this run (approx, documented) | — | high |
| 20 | Prior truncation | DROPPED (plain Normal in log space) for smoother NUTS gradients | — | this run (deviation vs round-1) | — | low |
| 21 | Analysis grid (global) | 260 log pts 20–2000 Hz (shared dataset grid) | Hz | dataset | fixed | high |
| 22 | Analysis grid (refined) | global + 41-pt linear clusters near 62.3/86.25/93.5/129.5 Hz | Hz | this run | fixed | high |

## Data / replicate counts
- 1 first-build vibe-test PSD (260 freqs), 3 first-build modal FRFs (180 freqs each: dome-only,
  coupled-interface, coupled-tray), 11 flights each with a scalar tray 3·GRMS and interface 3·GRMS.
- build_id == flight_id (each flight is its own build). Only build 0 has full vibe+modal curves;
  builds 1–10 are constrained only by their scalar flight 3·GRMS (weak) + the hierarchical σ_build.
- This is ONE synthetic realization (one dataset). Flight-to-flight forcing variability IS modeled
  (fixed 3 dB GP); build-to-build IS modeled (learned σ_build); no test-to-test repeat of the vibe
  test or modal test is available (single first-build measurement each).

## Uncertainty taxonomy in this run
- **Parameter uncertainty:** structural k1,k2,ζ1,ζ2 (posterior). Drives resonance-region band width.
- **Observation noise:** σ_sensor (learned), per-frequency iid in log space.
- **Build/test variability (aleatory, learned):** σ_build dome/tray → per-build effects.
- **Forcing uncertainty (aleatory, KNOWN/fixed):** 3 dB Matérn GP → dominant broadband band width in P1.
- **Model discrepancy:** NOT separately inferred this run (the forward model family contains the truth,
  by construction of the synthetic dataset). Documented limitation.
- **QOI uncertainty:** propagated to tray/interface 3·GRMS and the per-flight interface response PSD.

## Notable deviations (flagged)
- Modal likelihood uses log-MAGNITUDE only (drops phase). Justification: the build/sensor effects are
  real PSD-space magnitude scalings; magnitude carries the identifying information for k,ζ and the
  build effects. Risk: slightly less information than a full complex likelihood; acceptable for this
  scope and documented.
- Flight 3·GRMS likelihood integrates the KNOWN forcing GP out analytically as a LogNormal with a
  fixed σ_q (precomputed by 4000-sample Monte Carlo at truth params). This confounds build-to-build
  and forcing scatter in the scalar; σ_build is therefore weakly identified — reported honestly with
  its wide posterior.
- Prior truncation dropped for NUTS smoothness; the informative Normal priors keep draws in-range.
