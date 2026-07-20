# quantity_contracts — before plotting/fitting/checking (inherits + extends the proven netcg contracts)

## QOI-A: net-CG FORCE on the top tray (INHERITED VERBATIM from shocksat_netcg_method_selection_20260701/quantity_contracts.md)
- Numerator: net-CG force = mass-weighted acceleration integral of the tray (z >= 55 in), per frequency
  S_F(ω) = |G_qoi(ω)|² · S_input; G_qoi = modal sum with uniform-mass tray participation; per-drive variant
  includes φ_drive (drive-point participation). Convention: net interface FORCE (NASA-HDBK-7004C apparent-mass /
  base-reaction convention) — NOT net-CG acceleration (named alternative; ratios coincide).
- Components: tray-CG X, Y (SHEAR, in-plane) and Z (NORMAL, out-of-plane) — reported SEPARATELY, never blended.
- Excitation: 100%-known FLAT input PSD at each hammer drive point; all FIVE drives; input level cancels in all
  band-RATIO metrics. Units: force consistent with input; band metrics dimensionless RATIOS; freq Hz.
- Band: 45-260 Hz (data band). 1-octave geometric-mean smoothing before all band scores.
- Limiting behavior: ω→0 net force → input × tray mass; SHEAR peaks at measured global box modes (~114-197 Hz);
  NORMAL peaks at unmeasured drumhead plate modes (~234-258 Hz).
- Boundary condition: free-free survey basis; reduced model K(θ) = A_fix + Σ θ_g A_g (mass = I, mass-normalized).
  For M1 candidates: K_c(θ) = A_fix_c + Σ θ_p A_p_c in the candidate's OWN 80-mode mass-normalized basis
  (Rayleigh-Ritz from the candidate's full-order eigensolve for tier-3 arms).

## QOI-B: per-point FRF amplitude at held-out sensors (R1)
- Numerator: peak |accelerance| per held-out channel, g/lbf (|H| = a/F, accel g over force lbf), reconstructed
  from the arm's posterior (modes + shapes + F(k) discrepancy); denominator: measured single/multi-impact FRF
  peak at that channel. Coordinate: each channel's own structural axis. Excitation: the drive of that fold.
- Global gain: ONE scalar gain per (arm, fold) fit on OBSERVED channels only (mass-norm/units nuisance);
  NEVER per-mode or per-channel amplitude fitting in any score (metric-trap #1).
- Expected behavior: peaks at resonances of the in-band modes; interval must contain the measured peak ~95%.
- Reference: shapefield_lever.json bounds (σ 0.92-1.11 baseline, 0.86-0.88 Beck, 0.70 oracle ceiling).

## Mode pairing (metric-trap #2 contract)
- Candidate FEM modes are paired to the 33 .ash survey modes by ONE-TO-ONE optimal assignment (Hungarian
  algorithm on the full MAC matrix over shared measured DOFs, MAC ≥ 0.3 admissible), NOT greedy per-mode argmax.
- The pairing for scoring an arm is computed ONCE per (model, θ_ref) and FROZEN through that arm's scoring;
  re-pairing inside a score loop is forbidden. Pairing-stability (pairs changed at θ draws vs θ_ref) is reported.

## Evidence (tier-3 selector)
- log-evidence per model class on the SHAPE-INCLUSIVE observable: Y = {matched measured ω̂_r² (all in-band
  matched modes)} ∪ {matched MAC_r}; statFEM Eq-38 analytic screen at θ_MAP (type-II ML σ's) with a
  BIC hyperparameter adjustment, per stage1_evidence.py pattern, extended with the MAC block; prior width
  σ_prior swept {0.15, 0.25, 0.40} — ranking must be reported at all three (prior-robustness).
- Expected limiting behavior: a candidate that only re-fits frequencies cannot gain MAC-block evidence;
  complexity (extra params) must pay for itself (Occam).

## Spectral estimates (Discretization Resolution Gate)
- FRF caches: hit-averaged H1 with coherence, band-limited 45-260 Hz, native df from N=122880-200000 point FFTs
  (window/overlap documented in the source cache builders; averaging lives ACROSS impacts, not segments).
- QOI grid: 400-point linear grid on 45-260 Hz + 1-octave smoothing (proven netcg choice); QOI-driving peaks
  (ζ=0.01 → 3-dB width ~1-5 Hz) resolved by df ≈ 0.54 Hz on the grid; resolution sensitivity carried from the
  netcg study (documented there), spot-checked here on the winner.
