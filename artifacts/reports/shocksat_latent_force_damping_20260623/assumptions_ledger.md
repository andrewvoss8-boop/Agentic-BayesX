# Assumptions ledger (AGENTS Assumptions & Uncertainty Gate)

| Quantity | Value / setting | Units | Rationale / source | Sensitivity priority |
|---|---|---|---|---|
| Sampling rate fs (raw) | 250,000 | Hz | confirmed by probe_mat.py; TestLog | low (verified) |
| Decimation factor / fs_dec | 100 / 2,500 | — / Hz | Nyquist 1.25 kHz » 260 Hz band; zero-phase FIR preserves decay envelope | med (decay distortion) |
| Pre-trigger / impact sample | ≈125,009 (≈500 ms) | sample / ms | argmax\|F\|; D2; probe_mat.py (250,001-sample, 1 s records) | low (verified) |
| Ring-down window | 6 ms skip → fit to k·noise-floor; ≈500 ms available | ms | skip impulsive transient + force-window; fit clean decay | med |
| Band-pass | 4th-order Butterworth, zero-phase, half-width = min(½·neighbour-gap, 7 Hz), ≥3 Hz | Hz | isolate the mode; flag close-mode contamination | HIGH (cluster modes) |
| Accel units | g (per-channel cal already applied) | g | D2 / TestLog xlsx; samples in engineering units | low (verified) |
| Force units | lbf (Dytran 5850B, Recorder116) | lbf | D2 / TestLog; peak 416–805 lbf (modal hammer) | low |
| BAD_DAQ excluded | {29,30,31,101} | — | TestLog-flagged (60 Hz / install fault); realfrf.BAD_DAQ | low |
| Decay-fit acceptance gate | R² > 0.90 (0.92 for NUTS/L2), SNR > 8–12, cycles > 10–15 | — | reject noise-dominated / contaminated traces | med |
| ζ prior (Layer 1 NUTS) | LogUniform(0.05%, 6%) | — | IDENTICAL bounds to D22 → like-for-like "resolved" criterion | low |
| NUTS settings | 4 chains, 600 warmup + 600 samples, target_accept 0.9, vectorized, float64 | — | AGENTS sampler/convergence gate; non-centered hierarchical ζ | med |
| Convergence gate | R-hat ≤ 1.05, ESS ≥ 200, divergence fraction < 2% over ALL sampled vars | — | AGENTS convergence gate | HIGH |
| FEM/L5 nominal structural ζ | 1.0% | % crit | realfrf.ZETA_NOM | HIGH (direction of L3 lever) |
| Exponential-window ζ_w(f) | from PROC.exp_end=0.05, N=122,880 | % crit | baked into the windowed FRF; added to both FEM & twin | med |
| Measured ζ (this run) | ~0.33–0.76% (median ~0.45%) | % crit | Layer-1 NUTS; cross-checked by log-dec + .ash 0.25–0.44% | — (result) |
| Latent-force process noise q_g | q_g_rel·var(a), swept {1e-2,1e-1,1e0} | — | empirical (NOT a posterior); velocity-projection ζ stable across sweep | HIGH (L2 caveat) |
| Twin amplitude-discrepancy σ | 1.604 (log) → 97.5% band ≈ +27 dB PSD | log | inherited probe_seed00 (per-node FEM shape error, misalignment-free) | HIGH (L3 binding limit) |
| Train/test split (L3) | leave-sensors-out, 90% training, seed 0 | — | inherited probe; validity probe first | med |
| S_F0 (flat input PSD) | 1.0 | lbf²/Hz | inherited Q1; cancels in every twin/FEM ratio | low |

## Data count / variability
- 4 references (drive direction × location): Test01 +X@990, Test02 +Z@990, Test04 +XY@990, Test06 +Z@900.
- 6 roving hits each (24 ring-down records); each test = a small roving cluster (OK for global modal ζ; per-hit for
  amplitude/shape). 111 good accel channels each. Test-to-test = the 4 references; hit-to-hit captured by pooling.
- 16 union modal peaks (45–260 Hz). Damping ζ is treated as a GLOBAL modal property (pooled across references/channels);
  between-channel ζ heterogeneity is modeled (non-centered hierarchical s_between) and reported.

## Uncertainty types distinguished
- Parameter uncertainty: ζ posterior (NUTS), per-trace bootstrap CI (Layer 1).
- Between-channel/amplitude heterogeneity: hierarchical s_between (Layer 1), early/late-ζ ratio (Layer 2).
- Observation/measurement noise: per-channel pre-impact band-passed floor (SNR gate); smoother R.
- Model discrepancy: per-node FEM shape error σ≈1.6 (inherited) — the binding limit on the Layer-3 QOI, NOT damping.
- Forcing: hammer impulse (known); latent MFE force g(t) = the estimated model-form forcing residual.
