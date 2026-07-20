# ShockSat time-domain latent-force damping / residual diagnostic — human-review packet

**Workspace:** `artifacts/reports/shocksat_latent_force_damping_20260623/`
**Replay:** `bash run_all.sh` (writes `runtime.json`; checker exits non-zero only on RED)
**Overall result:** **YELLOW** — a GREEN methodological headline (Layer 1) plus a documented HONEST NEGATIVE
on the engineering value bar (Layer 3). `check.py` = 8 green / 3 yellow / 0 red, exit 0.

---

## 0. The one hypothesis under test (plain English)
Damping (ζ, the fraction of critical damping for a mode) is the rate at which a rung structure's vibration fades.
A prior study (**D22**) tried to read ζ off a single **windowed FRF** (a frequency-domain transfer function) and got
**0 of 9 modes** — because a light mode's frequency-domain "half-power" width Δf = 2·ζ·f is *narrower than one FFT
frequency bin* (sub-bin), so the peak is described by less than one sample and the width can't be fit.

But damping is fundamentally a **time-domain decay rate**: a clean modal-hammer **ring-down** (the ~0.5 s of free
vibration after the hammer hit) contains *many cycles* of measurable decay even when the mode is sub-bin in an FFT.
**Hypothesis:** on the clean ring-downs (Test01/02/04/06), a time-domain estimate resolves per-mode ζ (and residual
model-form structure) that the windowed FRF could not — and we ask whether that buys a less-conservative-yet-defensible
PSD-envelope qualification level for the live ShockSat twin program.

## 1. Method summary (first-pass)
| Layer | Question | Model / likelihood | Inferred | Fixed | Sampler |
|---|---|---|---|---|---|
| L1 | Does the ring-down resolve ζ? | per-mode band-pass + analytic-signal (Hilbert) log-decrement; **+ hierarchical exp-decay-envelope** model: env_i(t)=A_i·exp(−ζ_i·2πf·t)+c_i+noise, ζ_i=ζ_pop·exp(s·z_i) | ζ_pop, s (heterogeneity), per-trace A_i,c_i,σ_i | f0 (measured peak), prior ζ~LogUniform[0.05%,6%] | **NUTS** (ζ nonlinear), 4 chains |
| L2 | Damping correction vs genuine residual MFE? | per-mode modal SDOF + random-walk latent force g(t); decompose by projecting g on velocity | states q,v,g (smoothed) | ζ_nom=1%, noise levels (empirical) | **RTS Kalman SMOOTHER** (linear-Gaussian FILTER, *not* NUTS) |
| L3 | Does measured-ζ lower the held-out envelope GRMS vs FEM+6 dB? | inherited PSD-envelope twin, byte-identical; response PSD=\|H\|²·S_F flat; 97.5% predictive envelope | (reuses calibrated θ; swaps ζ) | per-node FEM shapes φ; σ=1.60 | reuses converged NUTS calib |

Data: 4 references (drive dir×loc), 6 roving hits each, 111 good accel channels, 16 union modal peaks 45–260 Hz;
accel in g, force in lbf (Dytran 5850B, 416–805 lbf); fs=250 kHz, impact pre-triggered ≈500 ms, ring-down ≈500 ms,
decimated to 2.5 kHz for analysis. Whole-time-history (decay) likelihood, NOT a peak/feature summary.

## 2. Headline (Layer 1) — GREEN: the time domain RESOLVES ζ where D22 could not
- **D22 reproduced: 0/9 identified** (frequency-domain windowed FRF) — integrity baseline (`out/d22_reproduction.json`).
- **Time-domain decay: 14/16 union modes RESOLVED** (`out/layer1_damping.json`), each with a passed resolvability
  table (40–120 cycles of decay, 15–35 dB decay, SNR 10–27).
- **NUTS posterior over ζ: 14/16 converged** (`out/layer1_nuts.json`): worst R-hat 1.020, min ESS 250, 0 divergences,
  CI < 0.16× the prior log-width (the same prior bounds as D22). ζ ≈ **0.33–0.76% (median ~0.45%)**, consistent with
  the independent NASA `.ash` modal ζ (0.25–0.44%). See **fig2_zeta_headline.png**.
- **Why it works (discretization gate):** half-power Δf=2·ζ·f is SUB-BIN vs the df=2.03 Hz FFT bin for the light modes
  (e.g. ζ=0.4% @ 138 Hz ⇒ Δf≈1.1 Hz < 2.03 Hz), yet the same mode rings for ~45–120 cycles in time. See
  **fig1_ringdown.png**. The time-domain decay also measures the TRUE structural ζ directly, free of the
  exponential-window artifact that contaminates the frequency-domain estimate.
- **Honest nuance (fig3_counts.png):** a frequency-domain width fit on the *clean* data reaches 7/16 (clean multi-hit
  data helps even in frequency: 0→7); the time domain adds the light/sub-bin and clustered modes (7→14). So **two real
  levers** — clean data AND the time domain; the time domain's specific gain is the sub-bin modes.

## 3. Layer 2 — the model-form error is mostly *wrong damping*, not missing physics (caveated)
A GP/random-walk **latent-force** model (the Kashyap & Nayek mechanism) adds one latent modal MFE force per mode to a
nominal SDOF and estimates it with an **RTS Kalman smoother** — an exact **linear-Gaussian filter**, explicitly **NOT
NUTS** and not a posterior over physical parameters (sampler-labeling gate). Projecting the latent force on velocity:
- recovers ζ_true that **cross-checks** the independent log-decrement per trace (corr ~0.82) and the Layer-1 NUTS;
- the recovered ζ_true (~0.4–0.6%) < FEM nominal 1% ⇒ the latent MFE force is dominantly a **viscous damping
  correction** ("the FEM has the wrong ζ", the parsimonious explanation);
- the non-viscous residual shows **no amplitude dependence** (residual-vs-q² corr ~0.03) and **near-exponential decay**
  (early/late-decay ζ ratio ~1.08) → little evidence of strong missing nonlinear physics. See **fig4_layer2.png**.
- **CAVEAT (YELLOW):** the raw latent-force *variance split* (damping vs residual fraction) is contaminated by smoother
  process noise and by close-mode beating in clusters, and a per-mode *free-decay* latent force is weakly identified for
  that split — so the headline is the q_g-robust velocity-projection ζ and the cross-check, not the variance fraction.

## 4. Layer 3 — HONEST NEGATIVE: damping does NOT win the less-conservative-envelope metric
The runner prompt's bridge assumed the FEM is *under-damped* (so its peaks/envelope are over-conservative and measured
ζ would lower them). On this structure that direction is **sign-flipped**, and the win metric is a ratio:
- **Finite-perturbation (fig5_layer3 left):** envelope GRMS scales ~1/ζ — ζ IS a strong **absolute** lever (passes the
  gate) — **but** the twin/FEM+6 dB win RATIO is **invariant to ζ** (spread = 1.0000) because the inherited contract
  uses the **same damping for FEM and twin**: ζ is common-mode and **cancels** (mirrors D8's "channel-common →
  gain-absorbed"). And the as-built FEM ζ=1% is **heavier** than the measured ~0.4% ⇒ the FEM is **over-damped**, so a
  measured-ζ correction *raises* the twin's peaks and GRMS (MORE conservative).
- **Held-out value (90% split, `out/layer3_value_seed00.json`, NUTS calib converged):** combined-correlated median
  GRMS ratio twin/(FEM+6 dB): A(nominal)=12.4, B(measured-ζ, identical η)=11.0 ≈ A (ζ cancels), C(measured-ζ twin vs
  as-built nominal FEM+6 dB)=14.3 ≥ A (over-damped → worse). **All framings = 0% GRMS win.**
- **Why (fig5_layer3 right):** the twin's honest 97.5% predictive band must be ~**+27 dB** to cover a held-out sensor —
  set by the **per-node FEM mode-shape error** (σ≈1.6), exactly the D7 finding. Damping is not the binding limit.
- **Held-out PSD examples (fig6_heldout_psd_examples.png):** in the style of the live program's
  `heldout_psd_examples.png` — 3 held-out sensors (FEM over-/near-/under-predicts), columns = unsmoothed (data, FEM,
  measured-ζ twin median + 2.5–97.5% band) and smoothed (data, FEM smoothed, twin 97.5% smoothed for NOMINAL-ζ vs
  MEASURED-ζ). It makes the damping effect visible: the measured (lighter) ζ RAISES the posterior FRF peaks, so the
  measured-ζ twin envelope sits ABOVE the nominal-ζ one — a measured-ζ correction makes the envelope MORE conservative,
  not less. The twin's covering band remains far above FEM and data (shape-error-driven, not damping).

## 5. Gates (status)
- Damping-resolvability gate: PASS — per-mode τ, T_fit, cycles, SNR, Δf vs df in `out/layer1_damping.json`; sub-bin
  shown; finite-perturbation included (ζ moves the QOI, ~1/ζ).
- Discretization gate: documented — fs 250 kHz→2.5 kHz, pre-trigger ≈500 ms, ring-down window, band-pass, df=2.03 Hz
  bin vs sub-bin Δf; time-domain claim never mixed with a frequency-domain df.
- Sampler labeling / convergence gate: PASS — ζ posterior = NUTS (R-hat≤1.020/ESS≥250/0div over all sampled vars,
  non-centered hierarchical); Layer 2 = labeled FILTER; no empirical-Bayes mislabeled as posterior.
- Leakage gate: held-out sensors do not enter decay fitting, calibration, scaler/σ fitting, or display tuning (L3
  reuses the inherited leave-sensors-out probe).
- History-dependence / nonlinearity gate: residual-vs-q² and early/late-ζ reported (both near linear).
- Plot gate: all figures from a saved `.py` (`code/make_figures.py`), tufte-linted (advisory flags reviewed:
  dual-axis labeled + meaningful, dB stated explicitly, linear-frequency justified on the narrow band), image-QA'd.
- Verification gate: `check.py` (SHA-locked, self-sha printed) FAILS RED on unsupported "resolved"/"win" claims,
  non-converged resolved modes, mislabeled sampler, broken byte-identical reuse, or missing artifacts.

## 6. Files
- Analysis: `code/{cache_builder,decay_core,layer1_damping,layer1_nuts,freq_control,finite_perturbation,layer2_gplfm,layer3_value,make_figures}.py`
- Outputs: `out/*.json`, `out/layer3_curves.npz`, `data/ringdown/*.npz` (time-domain caches, self-contained for replay)
- Figures: `figures/fig1..fig5*.png`
- Governance: `priority_deliverables.md`, `question_framing.md`, `quantity_contracts.md`, `assumptions_ledger.md`,
  `decisions_log.md`, `REUSED_code.sha256`, `check.py`, `run_all.sh`, `runtime.json`

## 7. For Andrew (surfaced, NOT self-applied)
1. **The prompt's "under-damped FEM" bridge is sign-flipped here:** the FEM nominal ζ=1% is heavier than the measured
   ~0.4%. A measured-ζ correction makes the twin more accurate AND more conservative; it does not win the
   less-conservative-envelope metric. Damping cancels in the contract's win ratio (like D8).
2. **A genuinely useful by-product:** we now have a measured, NUTS-resolved per-mode ζ (~0.45%, time-domain, free of
   the window artifact) for 14 modes — usable to *correct* the FEM/CLA damping (it currently uses 1%, ~2× too heavy),
   which would fix the FEM+6 dB *under-coverage* (D7's 34% exceedance) at the cost of a higher, more honest level.
3. **The binding lever remains per-node FEM shape fidelity** (σ≈1.6, +27 dB), not damping — consistent with §7.1 and D7.
4. Disk: raw modal `.mat` (5.6 GB, psd_envelope ws) and root zips (3.9 GB) left in place (re-downloadable); deletion
   surfaced for your call. project_log/runs.md rows and any QOI/standard implications await your review.
