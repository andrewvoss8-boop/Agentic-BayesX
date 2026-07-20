# Quantity Contracts — Resolution-Consistent FRF Scoring (20260713)

Defined BEFORE plotting/fitting/checking (AGENTS Quantity Contract Gate).

## Reused by reference (verbatim, unchanged)
`artifacts/reports/shocksat_frf_damping_updating_20260710/quantity_contracts.md` defines, and this run reuses
EXACTLY:
- **Accelerance FRF H(ω)** [g/lbf], g = 386.0886 in/s²; modal superposition over the reduced package modes;
  free-free; roving-hammer H1 convention; limiting behavior (→0 like ω² at DC; residual at ∞; peaks ∝ 1/(2ζ)).
- **P1′** = FDAC-aligned FRAC (signed Pearson corr of mean-removed log10|H| after the TRAIN-side FDAC scale
  warp, over the FDAC-selected band ⊆ [45,260] Hz), median over usable channels, fold-averaged. ∈[−1,1], higher
  better. Usable channel = median in-band coherence ≥ 0.6.
- **P2′** = median |FRSF−1| at FDAC-aligned matched peaks (amplitude/damping error), lower better.
- **P3** = raw log|H| Pearson correlation, 45–260 Hz, no warp (comparability with earlier runs).
- Scoring honesty: θ_MAP (train-side .ash, multi-start) + fixed damping + ONE global gain (dB) per fold fit on
  TRAIN drives only; NO per-mode/per-channel amplitude, phase, or damping fitting anywhere.

## NEW: P4 — matched-peak height error (dB)
- **Definition:** at the same FDAC-aligned matched-peak bins used by P2′ (frozen-pairing matched measured
  modes, MAC ≥ 0.5, |Δf| ≤ 12%, inside the FDAC-selected band), per usable channel and peak:
  Δ_pk = 20·log10(|H_pred,warped,gained(f_pk)|) − 20·log10(|H_meas(f_pk)|)  [dB].
- **Reported statistic:** median over channels of ( median over that channel's peaks of |Δ_pk| ) [dB]. Lower
  better. Numerator = predicted peak magnitude AFTER the fold's global gain; denominator = measured peak
  magnitude; both accelerance [g/lbf] at the same cache frequency bin.
- **Limiting behavior:** a model with perfect shape but naive (unbroadened) light-ζ peaks over-predicts peak
  height → large positive Δ_pk; window-matching should shrink |Δ_pk| toward the amplitude-error floor.
- **Reference:** FRSF/MSF literature (Heylen & Lammens 1996); this is the dB, per-peak form of the same
  amplitude comparison, added because window-consistency's first-order effect is peak height/width.

## NEW: the measurement-window operator 𝒲 (the load-bearing definition)
**Recovered distillation processing** (source: `shocksat_psd_envelope_twin_20260623/code/modal_multiref.py` +
`multiref_frf.py` + `realfrf.py`, found not inferred):
- Sample rate FS = 250,000 Hz; frame N = 122,880 samples → T = N/FS = 0.491520 s; df = FS/N = 2.03451 Hz.
- Per hit: frame starts at `start = argmax|F| − pre_gap`, pre_gap = 200 samples (impact at in-frame sample
  n₀ = 200, t₀ = 0.8 ms).
- Force window: 2 ms box around the impact peak (passes the impact pulse essentially intact).
- Response window: **exponential**, w[n] = exp(ln(0.05)·n/(N−1)) — decays to 0.05 at frame end.
  Equivalent decay time τ = −(N−1)/(FS·ln 0.05) = 0.164066 s; added decay rate σ_w = 1/τ = 6.0951 s⁻¹.
- Single FFT per hit; H1 = Σ_hits Y·conj(F) / Σ_hits |F|²; band bins 45–260 Hz (105 bins, exact rfft bins
  f_k = k·FS/N).
- **Window-added apparent damping (documented upstream in `realfrf.measured_zeta_w`):**
  ζ_w(f) = 1/(2πf·τ) = 1.617% @ 60 Hz, 0.970% @ 100 Hz, 0.647% @ 150 Hz, 0.388% @ 250 Hz.

**Operator applied to the model (window-matched forward path).** For a model package with in-band modal
residues R_{c,i} (channel c, mode i), natural frequencies ω_i and total viscous ratios ζ_i (structural η not
used by any arm; asserted zero), each mode's accelerance splits exactly as
  −ω²/D_i(ω) = −1 + (ω_i² + 2jζ_iω_iω)/D_i(ω),   D_i = ω_i² − ω² + 2jζ_iω_iω,
i.e. a direct (impulsive) term and a proper decaying part with continuous-time poles p_i± = −ζ_iω_i ± jω_di,
ω_di = ω_i√(1−ζ_i²), and residues r_i± = (2ζ_iω_i·p_i± + ω_i²)/(p_i± − p_i∓).
Sampling the decaying part on the frame grid (Δt = 1/FS, impact at n₀) and multiplying by the exponential
window (a geometric sequence, ratio ρ = exp(ln 0.05/(N−1))) gives an EXACT closed-form DFT via finite
geometric sums:
  𝒲[H]_c(f_k) = Σ_i R_{c,i} · [ −w[n₀] + Δt · ( r_i⁺·S(z_i⁺,k) + r_i⁻·S(z_i⁻,k) ) ]
  S(z,k) = (1 − z^M)/(1 − z),  z_i±,k = ρ·exp(p_i±·Δt)·exp(−j2πk/N),  M = N − n₀.
The e^{−j2πk n₀/N} impact-position phase cancels between response and force (both referenced to t₀), exactly
as in the measured H1. The −w[n₀] direct term (w[n₀] = 0.99512) is the windowed impulse feed-through.
- **Limiting behavior (exactness check, encoded in Gate K):** with ρ→1 (no window) and M→∞ (infinite frame),
  Δt·S(z,k) → 1/(j2πf_k − p) and the operator reduces ANALYTICALLY to the naive modal FRF H(f_k) — the naive
  and windowed paths share one formula, differing only in (ρ, M). No smoothing kernel, no interpolation.
- **What 𝒲 captures:** exponential-window broadening (pole shift σ_i → σ_i + σ_w), finite-frame truncation
  (the z^M term), and discrete bin sampling — the three resolution effects of the measured processing.
  **What it omits (documented):** the 2 ms force-box shaping (in-band flat to <0.1% for a ≲2 ms pulse;
  checked empirically by Gate W) and multi-hit averaging (H1 with aligned hits is hit-mean-invariant for a
  deterministic model). Units unchanged: g/lbf.
- Structural-η arms would need an η→ζ equivalence (η≈2ζ); NO arm in this run uses η, so the operator asserts
  η_i = 0 (checker-verified assumption, not a silent guess).

## Damping inputs (fixed data, not fit)
- **Survey per-mode ζ (PRIMARY):** `measured_modes.npz` field `damp` [percent critical] / 100 → ζ, 33 modes
  with frequencies [Hz]. Mapping to model modes: ζ_i = linear interpolation of the 33 (f_survey, ζ_survey)
  pairs at the model's in-band mode frequency f_i, end-clamped. Zero free parameters; values below the 0.2%
  inferred-damping gate floor are allowed AS MEASURED (they are data; the [0.2%,5%] gate constrains INFERRED
  damping — assumptions_ledger A5).
- **ERA 4-band ζ (VALIDATION, arm B4):** `scratch_test07/era_result.npz` field `band_zeta` =
  [0.099, 0.301, 0.542, 0.236]% on the D8 band edges [45, 69.8, 108.2, 167.7, 260] Hz. Derived from Test07
  (+X drive) raw records → labeled leakage caveat on the +X fold.
- **Flat 1% (incumbent convention):** ζ_i = 0.01 ∀i (B0 naive = the damping run's A0_enr exactly; B3
  windowed).

## Gate quantities
- **Gate W:** median per-channel |Δlog10|H1|| [dex] between the Test07-recomputed H1 and a target H1 over the
  105 band bins; PASS(direct) = ≤ 0.05 dex on ≥ 80% of usable channels vs the STORED cache; if the direct
  target fails from series (Test01-vs-Test07) differences, PASS(labeled) = same threshold vs the Test07
  hit-001-vs-others internal recompute + the window-physics check (measured apparent-ζ of clean peaks within
  ±25% of ζ_w(f)+ζ_phys prediction), with the Test01↔Test07 repeatability quantified and reported as a bonus.
- **Gate K:** synthetic 1-DOF, fn = 100 Hz: peak-height reduction under 𝒲 vs the analytic apparent-ζ
  prediction (ζ_app = ζ + ζ_w(fn)) within 5%; a ζ = 5% peak changes by ≤ 5% under 𝒲. Same frame constants as
  the caches.
- **Gate R:** B0 dev P1′ = 0.1969 ± 0.002 (damping run's A0_enr, `out/baseline.json` there); B1 < B0.

## DATED ADDENDUM (2026-07-13, D8 — appended after Gate W's first run, BEFORE any re-grading of arms)
The Test07 force channel is dead in all four hits (argmax = noise at 0.012–0.35 s vs true impacts at ~0.50 s;
rms 0.27 lb vs ~218 g responses) — evidence in `out/gate_W.json` and decisions D8. The DIRECT Gate W
comparison (recompute H1) is physically impossible with this data. The labeled basis therefore moves to a
FORCE-FREE estimator on the same raw records with the SAME thresholds: (a) hit-consistency on offset-removed
windowed response spectra (0.05 dex on ≥80% of the stored cache's coherent channels; offset removal required
— no force normalization exists); (b) window-physics: apparent ζ of clean ERA peaks in the windowed response
spectrum within ±25% of ζ_ERA + ζ_w(f). Test01↔Test07 becomes a labeled shape-only bonus. Arm scoring is
unaffected (arms never touch Test07). Gate W's best attainable grade with this data is LABELED (YELLOW).
