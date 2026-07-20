# Assumptions Ledger — Resolution-Consistent FRF Scoring (20260713)

| id | assumption | value / units | rationale + source | sensitivity priority |
|---|---|---|---|---|
| A1 | Distillation frame/window recovered EXACTLY | N=122880 @ FS=250 kHz (T=0.49152 s, df=2.03451 Hz); exp response window end=0.05 (τ=0.16407 s, σ_w=6.095 1/s); force 2 ms box; pre_gap=200 | FOUND in source: `modal_multiref.py`→`multiref_frf.py`→`realfrf.py` (PROC dict + `measured_zeta_w`); cache metadata (N, df, used, impact_idx) agrees | LOW (verified by Gate W against raw data) |
| A2 | Survey per-mode damping interpretation | `measured_modes.npz['damp']` = PERCENT critical → ζ=damp/100; median 0.317% | Damping run D7 (carried); consistent with ERA (0.301%) + log-dec from raw decay | LOW (two independent confirmations) |
| A3 | Survey ζ → model modes by frequency interpolation | linear interp of 33 (f,ζ) pairs at model mode freqs, end-clamped; ZERO free params | The survey samples ζ(f) at measured modes; interpolation is the lowest-assumption map; alternative (nearest-mode) differs only at unmatched model modes | MED — sensitivity check: nearest-neighbor vs interp on B2 (reported in packet) |
| A4 | ERA 4-band ζ (B4 only) | [0.099, 0.301, 0.542, 0.236]% on edges [45,69.8,108.2,167.7,260] Hz | `era_result.npz` from Test07 hit-001 (+X drive) — LEAKAGE CAVEAT on +X fold (labeled per card) | MED (validation arm only) |
| A5 | Physical-damping honesty gate | ζ∈[0.2%,5%], η≤0.2 constrains INFERRED damping; measured survey values <0.2% allowed AS MEASURED | Card §3.2: they are data, not fit; gate exists to stop amplitude-fit-in-disguise, which cannot happen to fixed measured inputs | LOW |
| A6 | No structural η in any arm | η_i = 0 asserted | All 6 arms viscous-only per card table; window operator implemented viscous-only | LOW (checker asserts) |
| A7 | Force-box shaping omitted from 𝒲 | 2 ms box ≈ in-band flat (<0.1% to 260 Hz) | Half-sine ≲2 ms pulse: first spectral zero ≥ ~500 Hz; H1 divides out the pulse to first order; Gate W checks the whole operator empirically | LOW (Gate W covers) |
| A8 | Multi-hit averaging identity for the model | deterministic model ⇒ H1 over aligned identical hits = single-hit H | Hits are impact-ALIGNED to the same in-frame position (pre_gap); model has no hit-to-hit variability | LOW |
| A9 | θ = reused multi-start θ_MAP per package | A0_enr, c06_tb_xface_enr from the damping run (exact-basis, D19/D22 rules carried) | Card: "nothing inferred beyond reused θ_MAP" | LOW (fixed input) |
| A10 | One global gain/fold (train-side), no other amplitude freedom | mean log-offset over train drives [dB] | Damping run scorer convention, reused verbatim (Gate R enforces equality) | LOW |
| A11 | Usable channel rule | median in-band coherence ≥ 0.6 | Same rule as damping + remodel runs (comparability) | LOW |
| A12 | Vault second-read | +XY/Test04 graded ONCE here; SECOND program read overall | Card §3.1 honest label; zero-search arm set is the mitigation; known +0.22–0.30 location effect must not be read as a win | HIGH for interpretation (labeled everywhere) |
| A13 | Data counts | 5 drive caches (4 dev + 1 vault), 111 accel ch each, 105 band bins, 6 hits each; 33 survey modes; 1 raw drive (Test07 +X, 4 hits) | No flight/build variability data exist; test-to-test variability enters ONLY via Test01-vs-Test07 (Gate W bonus) | — |
| A14 | Uncertainty split | This run reports point metrics + fold spread ONLY; no posterior/aleatory claims (no sampler) | Card §0 | — |
| A15 | Test01(cache) vs Test07(raw) same drive point | node 990 +X face; modal vs impact hammer differ in tip/level | `modal_multiref.py` xyz (9.0,7.6,0.6) vs Test07 REFS (9.0,8.0,1.0) — nearby but not identical points; repeatability quantified in Gate W, NOT assumed away | HIGH for Gate W target choice (D3) |

Sensitivity plan (AGENTS Sensitivity Gate): (i) A3 interp-vs-nearest on B2 (the only modeling choice inside
the claim arm); (ii) Gate-W threshold sensitivity reported (0.05 vs 0.10 dex); (iii) S1 margin vs fold-SE
shown per fold (the decision-driving noise assumption). Grid/resolution: the analysis grid IS the study object
(2.03 Hz cache bins); the window operator is exact at those bins (no resampling error); finer-grid model
diagnostics use 0.1 Hz only in figures, labeled.
