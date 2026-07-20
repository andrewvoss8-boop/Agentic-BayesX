# Quantity Contracts — ShockSat TRUE Agentic Remodeling Loop (20260706)

For every named quantity: numerator, denominator, coordinate, excitation, boundary condition, units, limiting
behavior, resonance/antiresonance behavior, reference. Written before plotting/fitting/checking any quantity.

## Q1. Per-channel FRF magnitude, log|H| (the P1/P2 observable)
- **Symbol / units:** H_c(f) = accelerance FRF at accelerometer channel c. Numerator = acceleration response
  (g, where 1 g = 9.80665 m/s^2, from PCB 350B01 accels, mV/g calibration in channel_map.csv). Denominator =
  input force at the hammer impact DOF (lbf; PCB force hammer). So |H| has units g/lbf. We score **log10|H|**
  (dimensionless after the log), per-channel Pearson correlation vs measured over 45-260 Hz.
- **Coordinate:** each channel is one translational DOF (X/Y/Z) at a grid node (channel_map.csv `structural_axis`,
  `fem_grid`); 228 observed translational DOFs (obs_dofs.npy) at 76 instrumented nodes.
- **Excitation:** single-point impact hammer at the drive location for that test (drive set: +X/990x, +Z/990z,
  +Y/990y, +XY/990xy [reserved vault], +Z@900z). Distilled per-channel H1 estimator (force->response), band-limited,
  hit-averaged (n_hits in the caches; e.g. +X used 6 hits), with coherence stored alongside.
- **Boundary condition:** free-free suspension (soft bungee), consistent with the modal survey; FEM prediction
  uses the elastic mode superposition (rigid-body modes excluded) with modal damping ζ (assumptions_ledger).
- **Forward model:** H_c(f) = g_gain * Σ_i [ φ_{i,c} φ_{i,drive} / (ω_i^2 - ω^2 + 2 j ζ_i ω_i ω) ] * (unit input),
  θ moving ω_i and (for shape-changing edits) φ_i; ONE global real gain g_gain per fold fit on train; NO per-mode
  or per-channel amplitude/phase fitting anywhere in selection (the LSQ trap, forbidden by card §4.3).
- **Limiting behavior:** below the first elastic mode, |H| -> stiffness-line (flat/rising accelerance toward the
  rigid-body region); at each resonance ω_i a peak of height set by 1/(2 ζ_i) and modal participation; between
  modes, antiresonances (notches) where contributions cancel. Log axis in frequency for all FRF plots.
- **Reference:** distilled measured H1 caches (netcg/psd_envelope `m_*.npz`), NASA ShockSat modal survey (.ash,
  33 modes), Card D correlation_contribution.md (per-channel corr baseline ~0.27-0.38).

## Q2. P1 — fold-averaged median per-channel log|H| correlation
- **Definition:** for a held-out drive, corr_c = Pearson(log10|H^pred_c|, log10|H^meas_c|) over the 45-260 Hz
  frequency samples; P1(fold) = median over channels c with usable coherence; P1 = mean over the leave-one-drive-out
  folds. Reported WITH per-fold values and the standard error over folds (SE = sd/sqrt(n_folds)).
- **Units:** dimensionless (correlation in [-1, 1]). **Reportability rule:** never a single-fold number; a claimed
  margin must be fold-averaged AND exceed 2x SE (noise-floor rule).

## Q3. P2 — matched-peak log-amplitude RMSE (dB)
- **Definition:** at measured peaks matched to model peaks by the frozen Hungarian pairing (pairing.py convention),
  RMSE of (20*log10|H^pred| - 20*log10|H^meas|) in dB, over matched peaks on the held-out drive. Same fit rules
  (θ_MAP + one global gain, no per-mode amplitude fit). Lower is better.
- **Matched-peak definition:** a measured spectral peak is "matched" iff the frozen pairing assigns it a model mode
  with |Δf|/f <= 0.12 and MAC >= 0.5 (pairing.py `calib_ok`); unmatched peaks are excluded from P2 and their count
  reported (an edit that loses matches is penalized via the count, not by silently dropping them).

## Q4. Net-CG force QOI (Q leg, finalists only; netcg conventions)
- **Quantities:** net-CG base SHEAR (in-plane, X and Y components) and NORMAL (out-of-plane Z) force on the top
  tray/plate, 95% predictive band, from response = |H|^2 * S_F with a flat known input PSD S_F at the impact DOF.
  Numerator = summed nodal inertial force over the tray (lbf); coordinate = CG of the top tray; excitation = flat
  input PSD at the hammer DOF; BC = free-free. Bands built with statFEM output discrepancy F(k) (netcg packet).
- **Coverage / sharpness contract:** coverage = weighted fraction of the held-out band enveloped, hard gate >=0.95
  with <=0.5 dB energy-weighted exceedance (narrow exceedances tolerated if enveloping elsewhere); sharpness =
  band-width ratio vs FEM+6dB, compared to the proven bars 1.508 (shear_X) / 2.301 (shear_Y) / 2.526 (normal).
- **Reference:** netcg_method_selection packet.md (statFEM F(k), held-out-drive answer key, leave-modes-out).

## Q5. Modal quantities used only for TRAIN-side diagnosis + screening (NO-sampler)
- **Matched frequency error** Δf_i = f_model_i / f_meas_i - 1 (signed, %), per frozen pairing.
- **Region MAC** = Modal Assurance Criterion between model and measured mode shapes on the .ash 76-node grid,
  MAC = |φ_m^T φ_t|^2 / ((φ_m^T φ_m)(φ_t^T φ_t)); reported per region and per mode. Used to rank screen candidates
  (train proxy) and to build diagnosis maps; NEVER used as a selection score on dev.
- **Modal strain-energy fraction** f_{i,g} = (φ_i^T K_g φ_i)/λ_i (= 2*SE/λ for mass-normalized modes), normalized
  over groups — the identifiability quantity (AGENTS Modal/Eigenproblem Identifiability Gate).
