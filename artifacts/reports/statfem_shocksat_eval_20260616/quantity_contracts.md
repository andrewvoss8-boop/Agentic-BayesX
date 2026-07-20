# quantity_contracts.md — StatFEM ShockSat held-out-QOI evaluation

For every named engineering quantity: numerator, denominator, coordinate, excitation, boundary condition, units,
expected limiting/resonance behavior, reference. Pinned BEFORE plotting/fitting/checking (AGENTS.md Quantity
Contract Gate).

## Q1 — Per-sensor accelerance FRF `H_s(ω)`
- **Numerator:** acceleration response a_s at sensor DOF s (translational x/y/z at an accelerometer node).
- **Denominator:** applied point force F_d at the drive DOF d.
- **Coordinate:** s and d are translational DOFs in the FEM global frame (in inches; X,Y lateral, Z long axis).
- **Excitation:** single point force at d (drive-point + transfer accelerances).
- **Boundary condition:** FREE-FREE (the ShockSat modal article; 6 rigid-body modes excluded from the basis, so
  the FRF is the elastic accelerance — no rigid-body 1/(−ω²m) growth at low f because RBMs are removed; the band
  starts at 45 Hz < first elastic mode 54.6 Hz).
- **Units:** accelerance |H| in (in/s²)/lbf (synthetic units; the study reports coverage and ratios, not a
  certified absolute load).
- **Expected resonance behavior:** peaks at the elastic natural frequencies ω_k = √λ_k(θ); peak sharpness set by
  ζ (half-power bandwidth ≈ 2ζf_k). Drive-point accelerance (s = d) is positive-real-part with antiresonances
  between modes; transfer accelerances (s ≠ d) show sign changes per mode-shape products Φ_s,kΦ_d,k.
- **Expected limiting behavior:** as ω→ band-low (well below first elastic mode) |H|→ small (stiffness-line,
  elastic-only); as ω→ band-high, modal sum of the in-band modes plus residual of higher modes (truncation
  checked in the discretization gate).
- **Reference:** standard modal-superposition receptance × (−ω²) for accelerance; modal twin reduced model
  (`reduced_blocks.npz`).

## Q2 — QOI (a): held-out-sensor peak accelerance
- **Definition:** `QOI_peak,s = max_{f∈[45,260]Hz} |H_s(f)|`, linear magnitude.
- **Why:** a shock/vibration "worst single-frequency response" proxy at an un-instrumented location.
- **Coverage contract:** truth peak (from the truth FRF) inside the 95% posterior-predictive interval of the
  predicted peak at the held-out sensor. Reported per arm/combo and aggregated over the 5 combos.
- **Differentiability note:** max over a fixed grid is non-differentiable, but the QOI is computed in
  POST-PROCESSING from posterior-predictive FRF draws, NOT inside the NUTS likelihood, so no smoothing is needed
  (the likelihood is on the whole log-magnitude FRF over observed channels — see Q4).

## Q3 — QOI (b): held-out-sensor band response metric (GRMS-like)
- **Definition:** `QOI_band,s = √( Σ_f |H_s(f)|² · S_FF · Δf )` over [45,260] Hz, with flat input PSD S_FF = 1
  (synthetic), Δf = trapezoidal frequency weights on the log grid.
- **Numerator/denominator:** response-acceleration RMS per unit flat force PSD (energy-integrated accelerance).
- **Why:** a broadband random-vibration response-energy proxy (GRMS = root-mean-square g, here in synthetic
  units), complementary to the single-peak QOI — tests whether the *integrated* band is covered, not just the
  worst peak.
- **Coverage contract:** as Q2, on the band metric.

## Q4 — Calibration likelihood quantity
- **Quantity used:** whole log-magnitude FRF `log|H_s(f)|` on the OBSERVED sensor DOFs over the full 160-point
  band (NOT peak/feature summaries) — the whole-data likelihood choice, stated explicitly (AGENTS.md likelihood
  data-usage gate).
- **Noise/discrepancy:** observed-channel residual `r_s(f) = log|H_meas,s(f)| − log|H_model,s(f;θ)|` modeled as
  M0 iid N(0, σ_meas²); M1 iid N(0, σ_meas²+σ_d²); M2 N(0, σ_meas²I + σ_d² C_schneider) with C correlated over
  freq AND space; M3 same with C replaced by the θ-orthogonal-projected P_⊥ C P_⊥.

## Q5 — Coverage (the trust metric)
- **Numerator:** count of held-out QOI truth values inside their 95% predictive interval.
- **Denominator:** total held-out QOI values (held-out sensors × {peak, band}).
- **Expected behavior if calibrated:** ≈0.95. "Confidently wrong" = a tight interval with coverage ≪0.95.
- **Reference:** standard posterior-predictive coverage / calibration check (Kennedy–O'Hagan, Plumlee).

## Q6 — Learned discrepancy scale σ_d (model-form-error thermometer)
- **Quantity:** posterior median of σ_d (log-magnitude units), per arm/combo.
- **Expected behavior:** ≈0 with no injected discrepancy; rises with injected error magnitude. M0 fixes it at 0
  by construction (the naive arm has NO mechanism to say "my physics may be wrong").

## Q7 — θ recovery
- **Quantity:** per-group θ_g posterior (median + 95% CI) vs θ_truth,g; covered flag; informed-vs-prior flag.
- **Expected behavior:** identifiable groups (bottom_box, top_box, plates, cross_beam) recoverable when their
  bias is in-path and above the σ_d floor; unidentifiable groups (joints, contact, welds, brackets) stay at
  prior / multimodal (the modal twin's 4/9 finding). Tied to the strain-energy/FIM gate BEFORE any claim.
