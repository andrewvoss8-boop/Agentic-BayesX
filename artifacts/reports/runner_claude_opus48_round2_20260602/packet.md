# Human-Review Packet — Round 2 (Claude Code Opus 4.8 runner)

Sequential vibe → modal → flight Bayesian update for a dome(m1)+tray(m2) system. This packet leads
with the method summary, then the headline deliverable, then evidence and limitations. Every figure
has a legend; FRF/PSD axes are log-frequency.

---

## 0. First-pass method summary (read this first)

- **Decision supported:** does the existing random-vibration TEST SPEC envelope the in-flight coupled
  **interface acceleration** environment, across frequency and across flights? (GEVS/GSFC-STD-7000:
  the spec must envelope the flight environment; scalar 3·GRMS is a summary only.)
- **Forward model:** coupled 2DOF, M=diag(1.0, 0.6) kg; K=[[k1+k2,−k2],[−k2,k2]];
  C=[[c1+c2,−c2],[−c2,c2]], ci=2ζi√(ki·mi). Accel/force H=−ω²Z⁻¹, Z=K+iωC−ω²M. Verified to reproduce
  the shared dataset clean curves to rel err 0.0. Implemented differentiably in JAX (`scripts/r2_forward.py`).
- **Likelihood (whole-curve, NOT peak-summary):**
  - tray vibe PSD (build 0, 260 freqs): log S_obs ~ Normal( log(|T(k2,ζ2)|²·smoothline) + build_tray[0], σ_sensor ).
  - 3 modal FRFs (build 0, 180 freqs each): log|FRF_obs| ~ Normal( log|FRF_model| + 0.5·build, 0.5·σ_sensor )
    — log-MAGNITUDE (phase dropped; documented deviation).
  - 11 flight tray & interface 3·GRMS (scalars): log(3·GRMS_obs) ~ Normal( log(3·√∫|H/g0|²·S̄_force df)
    + 0.5·build + bias, σ_q ), with σ_q the FIXED forcing-induced log-scatter (3 dB Matérn GP integrated
    out by 4000-sample MC: σ_q tray 0.197, interface 0.127).
- **Data count:** 1 vibe PSD curve + 3 modal FRF curves (build 0 only) + 11 flights × 2 scalar 3·GRMS.
  build_id == flight_id (each flight is its own build); only build 0 has rich curves. One synthetic
  realization. Flight-to-flight forcing variability IS modeled (fixed 3 dB GP); build-to-build IS
  modeled (learned σ_build); no replicate vibe/modal test.
- **Inferred (NUTS):** k1, k2, ζ1, ζ2; σ_sensor; σ_build_dome, σ_build_tray; 11×2 non-centered build
  effects (raw z reported). **Fixed (not learned):** masses, flight-to-flight 3 dB forcing GP
  (Matérn-3/2, ell=0.08), −6 dB flight forcing offset (PROJECT assumption), smoothline spec, g0.
  **Not inferred:** model discrepancy (truth is inside the model family by construction).
- **Sampler:** NumPyro NUTS, 4 chains, 1500 warmup + 2000 draws/chain, non-centered, target_accept 0.99.

```
graphical model (this run):
  priors: log k1,k2 ~ N(0,.18);  log ζ1,ζ2 ~ N(ln·,.35);  σ_sensor,σ_build ~ HalfNormal
  hierarchy: build_dome[b]=σ_build_dome·z_dome[b];  build_tray[b]=σ_build_tray·z_tray[b];  z~N(0,1)
  data:  vibe PSD(build0) ← k2,ζ2,build_tray[0],σ_sensor
         modal FRFs(build0) ← k1,k2,ζ1,ζ2,build[0],σ_sensor
         flight 3GRMS[f]  ← k,ζ,build[f]  (+ FIXED forcing σ_q, FIXED sensor)
  QOI / prediction: interface response PSD[f](ω)=|H00/g0|²·S̄_force·e^{build_dome[f]}·e^{GP_forcing(ω)}
```

---

## 1. HEADLINE (P1): per-flight coupled interface acceleration RESPONSE PSD vs test spec

`figures/interface_response_psd_vs_spec.gif` (11 frames, one per flight; PNGs in `figures/gif_frames/`).

- Quantity = coupled **interface acceleration RESPONSE PSD** (g²/Hz) — the response at the dome/source
  interface DOF under flight forcing — NOT the forcing input. Contract in `quantity_contracts_round2.md`.
- Each frame: posterior-predictive **mean + 95% + 99%** bands vs the original test spec (smoothline),
  log-frequency axis, legend. Peaks at the COUPLED modes ≈ 62.3 and 129.5 Hz (verified) with an
  antiresonance ~90 Hz.
- **Envelope finding (the engineering answer):** the spec envelopes the flight interface response in
  10 of 11 flights at the 99% level. For **flight 3** (the high-energy build) the 99% upper band
  narrowly **exceeds the spec at ~1.2% of frequencies** near the lower coupled mode — a narrow-band
  exceedance that the scalar 3·GRMS summary would hide. Per-flight numbers: `interface_psd_bands.json`.
- **Interpretation flag (needs human confirm):** frames use interpretation (B) per-flight realized
  build as primary; the sequential-assimilation view (A) is `figures/sequential_assimilation_qoi.png`
  and shows the structural QOI posterior is essentially stable across cumulative flights (the weak
  flight scalars add little structural information beyond the rich build-0 data).

## 2. Forcing overlay (P2)
`figures/flight_forcing_overlay.png` — 11 discrete flight forcing draws (Matérn-3/2, 3 dB) vs the
original forcing PSD (+6 dB above the flight mean) and the flight mean. The −6 dB offset is labeled a
PROJECT assumption, explicitly NOT the GEVS +3 dB qualification margin and NOT a "+6 dB/oct" slope.

## 3. QOI vs vibe reference (P3)
`figures/flight_qoi_vs_vibe_reference.png` — flight tray 3·GRMS per flight vs first-build vibe-test
3·GRMS = 43.9 g and smoothline 3·GRMS = 28.3 g, log-y. The large qual-vs-flight gap is expected and
annotated. 3·GRMS = 3σ ≈ 99.73% peak estimate (not a hard max). This scalar is a SUMMARY; the P1
PSD-envelope is the primary check.

## 4. Resolution (P4)
`figures/resolution_sensitivity.png` + `resolution_metrics.json`.
- Global grid puts only **1.64 points** inside the 62.3 Hz half-power band (Δf≈1.82 Hz) → it **clips
  the peak tip by 2.3%**. Mode-local refinement (+164 points; 424 total) reduces the clip to 0.02%.
- Integrated **3·GRMS QOI is robust**: error vs a 60k-point reference is +0.03% (coarse) / +0.006%
  (refined) for interface, +0.22% / +0.02% for tray. So the decision QOI is grid-insensitive while
  peak/modal IDENTIFICATION on the coarse grid would under-report the resonance amplitude.

## 5. Convergence (P5) — NUTS active is EARNED
`nuts_diagnostics.md` / `.json`. Over ALL 29 sampled scalar quantities (incl every raw z latent):
worst rank-split-R-hat **1.0025**, min bulk-ESS **2393**, min tail-ESS **3174**, **0 divergences**.
Gate (Stan/Vehtari): R-hat<1.01, bulk&tail ESS≥400, divergences 0-ideal/<2%-fail → **PASS**.

## 6. Trust checks
- `figures/posterior_recovery.png`: posterior vs synthetic truth — dome f_n, ζ1, ζ2 recovered on
  target; tray f_n slightly biased low (truth in upper tail), documented in `known_failures.md`.
- `checks.json` (runner-local acceptance), `runtime.json` (active 1268 s vs elapsed 2900 s),
  immutable checkers verified unchanged pre/post.

## 7. Limitations
See `known_failures.md`: log-magnitude modal likelihood, fixed-σ_q flight likelihood confounds
build/forcing scatter (σ_build weakly identified), no separate discrepancy term, one realization,
early accidental double-run (discarded). One-command replay: `bash scripts/run_runner_claude_opus48_round2.sh`.
