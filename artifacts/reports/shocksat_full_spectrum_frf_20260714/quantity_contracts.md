# quantity_contracts — Quantity Contract Gate (written BEFORE plotting/fitting/scoring; pre-registered)

## Q1: per-channel FRF amplitude score (the study's primary metric)
- **Quantity.** H1 accelerance FRF magnitude per channel: H(f) = accel response [g] / hammer force [lbf],
  H1 estimator (cross-spectrum / input auto-spectrum, averaged over hits). Model side: modal-superposition
  accelerance in g/lbf (G_IN_S2 conversion), free-free basis, mass-normalized modes.
- **Primary score P1′** (continuity with the resolution/damping runs, whose pinned bars are P1′ numbers):
  per-channel Pearson correlation of log10|H| between model and measurement over the scored band, after a
  TRAIN-side FDAC frequency alignment (one scalar frequency-scale warp ρ per fold, estimated on the train
  drives only) and coherence masking (channel used only if median in-band coherence ≥ 0.6). Median over
  channels per drive; mean over folds; fold SE = std(fold values)/√n_folds. Range [−1,1]; 1 = perfect shape.
- **Secondary P3:** the same correlation with NO alignment (raw log|H| corr). Reported alongside everywhere.
- **Per-band split:** the same P1′/P3 machinery restricted to sub-200 Hz / 200–500 Hz / 500 Hz–ceiling bins.
  The train-side warp/gain are fit ONCE on the whole certified band per fold, then scores are evaluated per
  band (no per-band re-fitting — that would hand each band a free alignment). If a band's FDAC ridge is
  degenerate (too few bins), that band reports P3 and the table cell is labeled.
- **GAIN CONVENTION (hard rule, checker-grepped):** ONE global gain (dB, train-side mean log offset) per
  fold per candidate. NO per-channel, per-mode, or per-band amplitude least-squares ANYWHERE in any
  selection score, likelihood ratio, or reported metric. Arm B's likelihood has one global gain per DRIVE
  (a train-drive nuisance parameter, inferred, shared across all channels of that drive) — same rule.
- **Damping convention (all arms except A0):** window-matched forward operator 𝒲 (below) + measured
  survey per-mode ζ (percent→ratio, frequency-interpolated); modes without a measured ζ (above the survey's
  257.6 Hz top) get the survey band median; ERA values are cross-check only. NO free per-mode damping
  fitting inside any selection score.
- **The window operator 𝒲** (reused verbatim from the resolution run, `wforward.py`, hashed): closed-form
  DFT of the sampled, exponentially-windowed (end=0.05), frame-truncated (N=122880 @ 250 kHz, pre-gap 200)
  modal impulse response. Adds apparent damping ζ_w(f)=1/(2πfτ), τ=0.1641 s. Naive limit is analytic.
- **Expected limiting behavior.** Accelerance → mass-line at high f between modes; peaks at resonances with
  apparent width set by ζ+ζ_w(f); antiresonances channel-dependent. At 2.03 Hz spacing, dense sub-260 Hz
  peaks merge (known); above 300 Hz modal density grows — correlation scores are expected to DROP per band.
- **Reference.** Pinned bars: A0 dev P1′ = 0.1969±0.002, A1 = 0.2371±0.005 (resolution run). Wall: ≈0.34
  deterministic-update median; ≈0.70 measured-shapes reference.
- **Two nearby conventions, named:** FRAC-style correlation of log-magnitudes (USED, this program's
  standard) vs FRF Similarity Metric on complex H (NOT used; phase not scored — H1 phase at 2 Hz with dense
  modes is unreliable). Alignment warp = train-side FDAC ridge (USED) vs no alignment (reported as P3).

## Q2: QOI-weighted sensor score
- Same per-channel P1′ values, weighted mean with per-sensor weights = net-CG SHEAR participation from
  `stage0_qoi_weights.json` (netcg run, read-only). Reported next to the unweighted median; per-sensor
  deltas for the 10 highest-weight sensors. Units: dimensionless correlation.

## Q3–Q4: net-CG shear (X,Y) and normal (Z) force bands — copied from the netcg workspace contract
- **Definition (numerator).** Net-CG force = Σ_i m_i a_i over the top-tray mass = the interface base
  reaction of the tray as a payload. Per frequency: S_F(ω) = |G_qoi(ω)|²·S_input with flat S_input (level
  cancels in all band-RATIO metrics). Modal form G_qoi(ω) = Σ_modes ω²·(Σ_{tray DOFs, axis a} m_i φ_i)/D_i(ω),
  D_i(ω)=ω_i²−ω²+2iζω_iω. Uniform-mass proxy over the tray region (nodes z ≥ 55 in; struts 45–55; box <45).
- **Denominator/reference.** 95%-band GRMS-force RATIO vs the FEM+6 dB incumbent envelope + interval width.
  Delivered-twin references to beat: shear 1.51× (X) / 2.30× (Y); normal 2.53×.
- **Coordinate/component.** Tray-CG translational X,Y (SHEAR) and Z (NORMAL), reported separately, never blended.
- **Excitation.** Flat input PSD at the hammer drive point; all five drives; held-out-drive answer key
  (`heldout_drive.py`, reused). **Boundary condition.** Free-free. **Units.** Force consistent with input
  (lbf); band metrics dimensionless ratios; frequencies Hz.
- **Expected behavior.** ω→0: net-CG force → input × tray mass (rigid-body check). SHEAR peaks at global
  box modes (~114–197 Hz); NORMAL peaks at drumhead plate modes (~234–254 Hz).
- **Convention named:** net interface FORCE (apparent-mass/base-reaction, NASA-HDBK-7004C) — USED; net-CG
  acceleration GRMS ratio coincides up to the cancelling tray mass.
- **Coverage (hard gate).** ≥ 0.95 on the held-out-drive answer keys for shear; normal validated against the
  plausible-truth ensemble + any data key from the extended band. Narrower-but-not-covering = DISQUALIFIED
  for delivery (still reported). Overconfidence audit: hide top-3 measured QOI-driving modes → band must
  widen (ratio > 1).

## Q5: wide-band cache overlap validation (per drive, HARD gate)
- Over 46.8–258.4 Hz: per-channel |H| Pearson correlation between new wide cache and existing cache ≥ 0.999
  AND median |Δlog10|H|| ≤ 0.01 (median over all channel×bin in the overlap). Same bins (2.03 Hz), same
  channels. Fail → diagnose (channel map, units, window); unexplained fail → drive excluded and reported.

## Q6: certified ceiling per drive
- The highest frequency where multi-hit, force-referenced coherence (H1 coherence over used hits) ≥ 0.6,
  taken as the top of the last contiguous run (median over channels) above the threshold starting from
  45 Hz. Target ≥ 1000 Hz per the Test07 response-side evidence (usable to ~2.4 kHz, repeatable ~2 kHz).
  Reported per drive; where FEM credibility (not data) binds is reported separately.

## Dated addendum 2026-07-14 (pre-arm-science; decisions D2): fold-SE convention for S1/S2
Raw per-fold P1′ scores scatter widely across drives (A1: 0.353/0.553/0.149/−0.107). For the S1/S2
comparison bars, "fold-SE" = the standard error of the PAIRED per-fold deltas (candidate fold score minus
reference fold score, std/√4) — the resolution run's S1 convention (its paired SE was 0.0263). The raw
fold SE of each arm's own scores is still reported in the arms×bands table as the score uncertainty.

## Q7: Arm-B likelihood (stated before fitting)
- Data: TRAIN drives' per-channel log10|H1| at cache bins over the certified band (whole-data likelihood,
  NOT peak features — choice stated per the Verification Gate).
- Model: log10|𝒲[H](θ)| + gain_d (one global per drive) + ε, ε ~ statFEM-style frequency-correlated
  Gaussian output error (squared-exponential kernel over log-frequency; magnitude σ_e and length-scale ℓ
  INFERRED; one σ_e shared across channels) + iid noise floor. θ: 9 group log-stiffness scalings,
  log-normal priors, σ=0.25 (inherited). Control: θ-only (no correlated term) = overconfidence control.
- Sampler: NUTS (NumPyro), 4 chains, float64; convergence gate per AGENTS.md over ALL variables.
