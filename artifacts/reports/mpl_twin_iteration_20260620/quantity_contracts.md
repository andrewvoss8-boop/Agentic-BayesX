# Quantity contracts — MPL twin iteration

For every named engineering quantity: numerator, denominator, coordinate, excitation, boundary condition,
units, limiting behavior, resonance/antiresonance behavior, reference. Written BEFORE plotting/fitting/checking.

## Q1 — Measured output/output transmissibility |T_a(f)|  (the OBSERVABLE)
- **Definition:** `|T_a(f)| = sqrt( PSD_a(f) / PSD_ref(f) )`, ref = SHIELD MIDDLE (always-trained reference).
- **Numerator:** auto-power spectral density (PSD) of out-of-plane acceleration at accel location *a*, m²/s⁴/Hz.
- **Denominator:** auto-PSD of OOP acceleration at the shield reference, same units.
- **Coordinate:** single axis = OUT-OF-PLANE of the shield (shield is a y–z panel at x≈61.5; OOP = +X). Andrew A5: every test, every setup.
- **Excitation:** diffuse acoustic field from a speaker held FIXED in position/volume across ALL acoustic runs (Andrew A7). Sequential single-sensor placements share the same acoustic input ⇒ the cross-file ratio is legitimate.
- **Boundary condition:** stand feet fixed (nominal SPC); uncoupled config (no ruler) for the 5 LOLO splits.
- **Units:** DIMENSIONLESS (ratio of like quantities). GAIN-FREE: same sensor (MMF KS78C, 100 mV/g) moved between placements; the common acoustic input level and sensor calibration cancel in the ratio. This is what keeps GRMS un-blurrable (D-A) — no per-channel gain can hide in a ratio.
- **Limiting behavior:** f→0: rigid-body ⇒ |T|→ ratio of rigid participations (≈1 if both move together). Far above the band: rolls off / dominated by local modes; out of scope (band ≤ ~260 Hz, QOI-driving).
- **Resonance behavior:** near the i-th resonance one mode dominates both sums ⇒ |T_a|→|φ_{a,i}/φ_{ref,i}| (the modal amplitude ratio; the unknown load participation γ_i CANCELS). Antiresonance of a appears as a deep valley (weighted DOWN by the peak-weighting). A peak in |T_a| occurs where mode i has large φ_a but small φ_ref.
- **Reference:** Girolami statFEM 2021 (y=ρPu+d+e); Kiran 2025 review FRF likelihood (Eq 18–23). Transmissibility as a force-free observable: standard OMA practice.

## Q2 — Predicted (FEM) transmissibility
- `T_a(ω) = |Σ_i φ_{a,i} γ_i / D_i(ω)| / |Σ_i φ_{ref,i} γ_i / D_i(ω)|`, with `D_i(ω) = λ_i − ω² + 2 i ζ_i √λ_i ω`.
- `φ_{a,i}` = OOP (X-DOF) component of mass-normalized mode i at FEM node for location *a*; `λ_i=(2πf_i)²`.
- `γ_i = φ_i^T f` = modal participation of the ASSUMED acoustic load shape `f` (default: uniform OOP pressure on shield exposed area). NUISANCE: the unknown true spatial load only enters off-resonance; absorbed by the spectral discrepancy GP over log-frequency. The input spectrum g(ω) CANCELS in the ratio (only the spatial shape `f` matters).
- `ζ_i` = modal damping ratio (the damping-model lever): default uniform; alternatives Rayleigh/Caughey, hysteretic η, localized non-proportional.
- Units dimensionless; same limiting/resonance behavior as Q1 (by construction).

## Q3 — Band-GRMS error (3rd headline score, un-blurrable)
- `GRMS_band(|T|) = sqrt( ∫_band |T(f)|² df )` over the QOI band (≤ ~260 Hz). Dimensionless (it is the RMS of a ratio, NOT an acceleration GRMS in g).
- **Error metric:** `grms_rel_err = GRMS_pred/GRMS_truth − 1` (from `score.frf_score`). Computed on the gain-free |T|; if any spectrum ever needs a units/centering gain it is ONE global gain fit on TRAINING/observed channels only and applied byte-identically to twin, climatology, baseline (NEVER re-fit per held-out channel). check.py gates one documented convention.
- Reference: GRMS is the standard vibration-energy roll-up; here on a dimensionless ratio so it cannot be laundered by a per-channel gain.

## Q4 — Natural frequencies (Stage-1 evidence SCREEN ONLY, per D-B)
- FEM eigenfrequency f_i (Hz) ↔ measured tap/acoustic peak frequency at the accel location, matched by proximity and GATED by OOP modal amplitude at that node (a peak only counts if the mode is "alive" at the sensor: |φ_node,i| above a fraction of its max). Used for cheap Stage-1 analytic statFEM evidence ranking; NEVER the scored held-out QOI (that is the full |T| spectrum).

## Q5 — Modal damping ζ (observable AND lever, D-F)
- Extracted from tap ring-downs (log-decrement) / acoustic half-power where resolvable. Reported with resolvability honesty (df, window broadening). ShockSat caveat: half-power can be under-resolved.

## Q6 — Climatology baseline
- Predicts the held-out location's |T(f)| (and GRMS) from the POPULATION of observed-location |T| curves (no location-specific info) — a no-skill CALIBRATED bar (value_eval.py pattern). The deterministic FEM point is a strawman reported as context, NOT the bar.
