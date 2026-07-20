# quantity_contracts.md — Card B

For every named quantity: numerator/denominator, coordinate, excitation, BC, units, limiting & resonance
behavior, reference. Done BEFORE plotting/fitting/checking.

## Q1 — Accelerance FRF H_s(ω;θ)  [the observable the likelihood uses]
- numerator: acceleration response at sensor DOF s; denominator: point force at the fixed drive DOF d.
- coordinate: per-sensor translational DOF (node-major, axis-minor); excitation: single point force at d.
- BC: free-free reduced 74-mode model (modal twin). units: (in/s²)/lbf (synthetic, uncalibrated scale).
- limiting: |H|→0 as ω→0 (acceleration of a force-driven structure vanishes at DC for this form); resonance:
  sharp peaks at the in-band modes (54.6–321.7 Hz), peak height ∝ 1/(2ζ). reference: textbook modal
  accelerance; hysteretic η=2ζ matches viscous peak amplitude (companion D10).
- likelihood uses the **whole log|H|** over all observed channels at all N_freq band points (NO peak/feature
  selection). log compresses resonance peaks; residual R = log|H_meas_obs| − log|H_model_obs(θ)|.

## Q2 — Held-out PEAK QOI  (primary scored quantity)
- = max over the band of |H_s| at a HELD-OUT sensor (not in the likelihood). units: same as Q1.
- decision-relevant peak interface response. grid note: at coarse N_freq the max can miss the exact peak →
  slight under-resolution; truth and prediction use the SAME per-cell grid so the per-cell score is consistent.

## Q3 — Held-out band-GRMS QOI  (secondary)
- = sqrt(∫_band |H_s|² df) (flat unit input). units: (in/s²)/lbf·√Hz. GRMS-like.
- grid note: RISES as the grid resolves sharp peaks (discretization.json: ~8% over N_freq 80→640) — a
  resolution effect, NOT a posterior effect; reported with that caveat; we lead with σ_d/θ widths.

## Q4 — σ_d posterior width  (PRIMARY collapse metric)
- = 97.5–2.5 percentile width of the posterior over σ_d (the discrepancy scale; M1/M2/M3; M0 fixed 0). units:
  log-mag. expected: SHRINKS with N for iid (Fisher info ∝ N → PIFT collapse); PLATEAUS for correlated.

## Q5 — Identified-θ width  (PRIMARY collapse metric)
- = mean 97.5–2.5 percentile width over the 4 identifiable groups (bottom_box/top_box/plates/cross_beam).
  dimensionless (multiplier). expected: → 0 like (N·J)⁻¹ for iid; plateaus for correlated.

## Q6 — Sharpness-aware held-out score  (interval score / CRPS / PIT, in dB)
- interval score IS_0.05 = (u−l) + (2/α)(l−y)1{y<l} + (2/α)(y−u)1{y>u} on the PEAK QOI in dB; CRPS empirical;
  PIT KS-distance from uniform. lower IS/CRPS = better. PENALISES width → not foolable by band inflation.

## Q7 — Effective sample size N_eff  (the WHY)
- iid: N_eff = N. correlated: N_eff_fisher = 2(σ_meas²+s)²·½Σ[Lam/(σ_meas²+s·Lam)]² and participation ratio
  PR = (ΣLam)²/ΣLam². expected: iid grows ∝N; correlated saturates near (band/ℓ_f)·(extent/ℓ_z).
