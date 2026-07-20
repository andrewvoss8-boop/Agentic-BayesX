# Quantity contracts — plate-test rehearsal

Inherits the netcg contracts (`shocksat_netcg_method_selection_20260701/quantity_contracts.md`);
restated here with the rehearsal-specific quantities.

## 1. Tray net-CG NORMAL-Z force spectrum |G_qoi(f)| (the QOI)
- Numerator: net (mass-weighted, uniform-mass proxy) Z-force integral over the tray region
  (z >= 55 in) = |sum_i g_i * w^2 / D_i(w)|, g_i = tray-region modal participation on Z,
  D_i = w_i^2 - w^2 + 2j*zeta*w_i*w, zeta = 0.01.
- Denominator/input: flat unit input PSD at the drive — all reported metrics are RATIOS so the
  input level cancels (7004C net-CG force convention; NOT net-CG acceleration — both named in the
  netcg contract, we use FORCE).
- Grid: 45-260 Hz, 400 linear points, 1-octave geometric-mean smoothing for all scored metrics.
- Units: arbitrary (ratio metrics); frequency Hz, log axis on plots.
- Limiting behavior: mass-line at low f, resonance peaks at drumhead modes 234-258 Hz.

## 2. 95% band factor (headline number)
- Numerator: 97.5th percentile of 1-oct-smoothed band GRMS over the delivery ensemble.
- Denominator: 2.5th percentile of the same. (Identical to `pretest_design.py::band_factor` so the
  analytic curve and the rehearsed number are directly comparable.)
- Dimensionless (x). Reference values: current 5.4x, promised 3.5x @ 12 sensors, floor 2.8x.

## 3. Energy-weighted 1-octave coverage (calibration metric)
- Fraction of 1-oct-smoothed frequency bins where the true spectrum lies inside the delivered
  [2.5, 97.5]% band, weighted by the truth's energy (peaks dominate) — identical to
  `netcg_qoi.coverage_vs_truth` with the single per-seed truth. Dimensionless [0,1];
  calibrated 95% band -> ~0.95.

## 4. Simulated plate observation y_{s,i}
- Numerator: true modal Z-displacement of drumhead mode i at sensor location x_s (mass-normalized
  reduced-model field units), + additive Gaussian noise sigma_y = 10% of the plate-field RMS of
  that mode (hammer-test realism ~0.85 coherence; assumption A7).
- Coordinate: plate nodes z >= 55 in, Z axis only. Excitation context: +Y drive (mode
  identifiability from the drive is NOT re-modeled here; frequencies of drumhead modes are
  treated as measured by the new test with the measured-tier 1% sigma — assumption A6).
- Two nearby conventions: mode SHAPE sample (ours) vs operating-deflection-shape sample (not ours
  — would fold participation; named and excluded).

## 5. Per-target-mode log-amplitude posterior sd (pooling-checkability metric)
- sd over the posterior of ln(g_i^post / g_i^model(theta)) for each target drumhead mode i.
- Dimensionless (log-amplitude). Prior value 0.80 (tier-2); "checkable" threshold 0.40 (S6).
