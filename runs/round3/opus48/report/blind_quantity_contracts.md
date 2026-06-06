# Quantity Contracts — BLIND round (vs Codex independent truth)

Each quantity defined BEFORE plotting/fitting. SI units. Frame: x,y transverse (tray plane); z axial
(dome→tray, +up); rotations RH about x,y,z. DOF order [x,y,z,rx,ry,rz] (from data_contract.md).

## Interface apparent mass (the observed/inferred channel)
- **Numerator:** interface force F(ω) [N or N·m]. **Denominator:** interface acceleration a(ω) [m/s² or
  rad/s²]. **Quantity:** diagonal complex apparent mass M_dd(ω) = F_d/a_d.
- **Units:** translational DOF (x,y,z) kg; rotational (rx,ry,rz) kg·m² (per data_contract).
- **Coordinate/BC:** single interface node; this is the COUPLED interface apparent mass (dome source +
  tray load in parallel at the shared node — apparent masses ADD in parallel).
- **Likelihood usage:** WHOLE-CURVE log|M_dd| over the adaptive grid (magnitude, log-space), per build per
  DOF. Magnitude-only (phase not fitted this run → damping fixed). Whole-curve, NOT peak-feature.
- **Expected limiting behavior:** ω→0 → rigid-body mass/inertia (the large measured asymptote ~520–760);
  resonances appear as apparent-mass MINIMA (driving-point), antiresonances as maxima; ω→∞ decays.
- **Reference:** experimental modal analysis / FBS apparent-mass conventions; data_contract.md schema.

## netCG (the QOI)
- **Numerator:** applied interface axial force F(ω) [N]. **Denominator:** axial interface apparent mass
  |M_zz(ω)| [kg] (driving-point accelerance a = F/M). **Definition:** a_cg(ω) = F(ω)/M_zz(ω) [m/s²];
  PSD_acg(f) = PSD_F(f) / (|M_zz(f)|² · g0²) [g²/Hz]; 3·GRMS_netCG = 3·√(∫ PSD_acg df) [g].
- **g0 = 9.80665 m/s²** (from data g0_m_per_s2). Load mass for reference = 170 kg (data load_mass_kg).
- **Excitation:** published flight forcing PSD (Matérn-3/2 in log10 f, mean −6 dB design envelope, 3 dB
  flight-to-flight), per data_contract.
- **Uncertainty propagated (FULL):** k_strut (epistemic) + build-to-build (aleatory) + flight-to-flight
  forcing (aleatory) + discrepancy d (with its uncertainty). Closes the D13 gap.
- **Known model-form bias:** driving-point mapping ≈ 2× the PUBLISHED 3·GRMS (truth's coupled transmission
  attenuates more); reported, not tuned away. See blind_known_failures §5.
- **Expected behavior:** netCG peaks at the coupled axial resonance (apparent-mass minimum, ~66/96 Hz in
  the data); large overall scalar margin vs a broadband spec can hide narrow-band exceedance.
- **Reference:** NASA-HDBK-7004 force-limited vibration framing; round-3 task-card netCG contract.

## Test spec envelope (for narrow-band exceedance)
- **Definition:** design-envelope forcing (published `design_force_psd_N2_per_Hz`, the +6 dB pre-data
  conservative envelope) driven through the predictive-MEDIAN accelerance, then peak-hold / broadband-
  enveloped: spec(f) = peakhold[ design_force(f) / (|M_zz,med(f)|² g0²) ].
- **Rationale:** a legitimate design-level spec that does NOT peek at the sealed truth; flights sit at −6 dB
  mean (¼ PSD) so they generally fall below it (large overall margin), but a high-side flight draw at a
  sharp resonance can locally exceed → the narrow-band-exceedance headline.
- **Verdict metric:** one-sided 99%-hi exceedance fraction = fraction of the band where the predicted
  99%-hi netCG PSD exceeds the spec; reported alongside the overall scalar margin.

## Frequency grid (discretization)
- **Adaptive grid from DATA peaks** (peak-pick build-averaged |M_dd| per DOF; true modes unknown blind) +
  coarse log baseline, FIXED during inference (D11/D15). Band 40–115 Hz (first mode cluster; holds the QOI
  energy at 66/96 Hz). Above ~115 Hz the coarse model has no predictive content (documented gap).
