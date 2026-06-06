# Assumptions Ledger — BLIND round (vs Codex independent truth)

All values are MY engineering choices for a coarse NOMINAL design model. The truth's values are SEALED; I
did not read them. "Inferred" = learned this run; "Fixed" = held constant; "Read-from-data" = set from an
observable asymptote (allowed). Sensitivity priority H/M/L.

| # | Quantity | Value / prior | Units | Status | Rationale / source | Sens |
|---|----------|---------------|-------|--------|--------------------|------|
| 1 | Load mass (tray) M_TRAY | 170 | kg | Fixed | data_contract load_mass_kg=170 | M |
| 2 | Tray radius of gyration | 0.60 | m | Fixed | geometry estimate (isogrid tray) | L |
| 3 | Rigid base mass/inertia M_base6 | x520,y524,z(238+dome),rx747,ry747,rz576 | kg / kg·m² | Read-from-data | low-f apparent-mass asymptote (build-avg) = rigid-body mass; standard | M |
| 4 | Dome resonant mass m_dome | 0.45×(z asymptote − tray) ≈ 195 | kg | Fixed | nominal cap-mass participation fraction | M |
| 5 | Strut axial stiffness k_strut | prior N(log k0, 0.40), k0=1.82e7 | N/m | **Inferred** | nominal calibrated so axial mount mode = 86.25 Hz | H |
| 6 | Dome bounce frequency f_dome | prior TN(93.5, 6, [70,115]) | Hz | Inferred / Fixed(variant) | nominal design 93.5 Hz | H |
| 7 | Build-to-build k scatter sigma_build | HalfNormal(0.05) or fixed 0.05 | – (log) | Inferred / Fixed(variant) | task: ±5% @3σ on fn → ~3–5% on k | H |
| 8 | Sensor noise sigma_e | HalfNormal(0.12) | – (log) | **Inferred** | ~1 dB nominal; INFLATES to ~0.6–0.85 (model-form leak) | H |
| 9 | Discrepancy magnitude sigma_d | fixed 0.3 (main) / HalfNormal(0.25) (flexible variant) | – (log) | Fixed / Inferred(variant) | capped to break the ridge (D19); flexible variant exhibits it | H |
| 10 | Discrepancy length-scale ell_d | 0.45 | norm-log-f | Fixed | informative (D19) — joint learning de-identifies | M |
| 11 | Discrepancy rank (HSGP) | 3 per DOF | – | Fixed | low-rank: smooth-trend only (keeps physics identified) | M |
| 12 | Structural loss eta | 0.04 | – | Fixed | finite FRF peaks; magnitude-only → not identifiable | M |
| 13 | Forcing model | Matérn-3/2 log10 f, −6 dB mean, 3 dB f2f, ℓ=0.28 | – | Known (published) | data_contract forcing_model_json (shared design) | M |
| 14 | g0 | 9.80665 | m/s² | Known (published) | data g0_m_per_s2 | L |
| 15 | Inference band | 40–115 | Hz | Fixed | first mode cluster; holds QOI energy (66/96 Hz) | H |
| 16 | Held-out builds | 2 of 8 | – | Choice | held-out calibration (whole builds) | – |
| 17 | Held-out freq band | 82–95 | Hz | Choice | held-out calibration (whole band, inside cluster) | – |

## Data counts (from observations.npz)
- 8 builds × 6 DOF × 4040 frequencies (5–600 Hz) complex apparent mass (sensor noise applied).
- 11 flights forcing PSD + design-envelope PSD.
- Response PSD 8 builds × 11 flights × 4040; netCG 3·GRMS 8×11.
- Build-to-build variation present (~19% std of log|AM|, concentrated near resonances).

## Uncertainty taxonomy (this run)
- **Parameter (epistemic):** k_strut, f_dome — reducible; here NON-IDENTIFIED (multimodal) → wide/biased.
- **Aleatory:** build-to-build (sigma_build) + flight-to-flight forcing (published model) — irreducible.
- **Model discrepancy d:** smooth per-DOF frequency GP — CANNOT represent the spatial/asymmetry + higher-
  mode error (the core limitation).
- **Observation noise sigma_e:** inflated (absorbs model-form residual; not pure sensor noise).
- **NOT modeled:** asymmetry/mode-splitting, lateral dome dynamics, >115 Hz modes, phase/damping, QOI
  transfer beyond driving-point.
