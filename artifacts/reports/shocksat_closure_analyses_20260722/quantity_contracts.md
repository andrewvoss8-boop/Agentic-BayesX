# Quantity contracts — Task Card A closure analyses

All conventions fixed at FREEZE, before any science. Frozen-source line references cite the predecessor
code that DEFINES each inherited quantity; those files are hashed in `source_manifest.json`.

## C1 — Prior-whitened posterior variance ratio (A1)
- Coordinates: t = log θ, θ = the 9 dimensionless part-group stiffness multipliers (median 1). Draws:
  `nuts_full_samples.npz` field `theta` (4000×9, pooled over 4 converged chains).
- Prior: t ~ N(0, 0.25²) i.i.d. (frozen twin ledger A8; `run_nuts.py` NSIG=0.25). Whitening = divide each
  log-draw component by 0.25 (prior covariance is 0.25²·I, so no rotation is needed).
- Quantity: eigenvalues λ_k and eigenvectors v_k of Cov(t/0.25) over the 4000 draws (denominator N−1).
  λ_k = posterior variance / prior variance along direction v_k (dimensionless). λ≈1 ⇒ prior-like
  (data added nothing along v_k); λ≪1 ⇒ data contracted that combination. Limiting behavior: with no
  data all λ→1; with perfect data on m independent frequency combinations, m eigenvalues → σ_f-limited
  small values.
- CI: block bootstrap over the draw sequence (block length stated in the ledger with an autocorrelation
  rationale), ≥1000 resamples, percentile 2.5/97.5 on sorted eigenvalues.
- Known answer (Andrew, read-only calc): sorted contracted ≈ 0.019, 0.029, 0.259, 0.355; five prior-like
  0.872–1.166. Gate: point estimates within our bootstrap CI of these values.

## C2 — σ_f (A2)
- σ_f = standard deviation of the log-frequency residual, log f_pred − log f_meas, per paired mode
  (natural log; dimensionless; ×100 ≈ % frequency error). Likelihood (frozen twin `run_nuts.py`):
  log f_meas,m ~ Normal(log f_pred,m(θ), σ_f), m = 18 paired calibration modes, frequencies in Hz.
  No MAC term (use_mac=False, matching the stored full run).
- Reported: posterior median and central 95% CI of σ_f per prior variant; θ medians for the reference.
- Convergence per AGENTS gate over ALL sampled variables; ≥4 chains; per-chain draws retained.
- Prior predictive check: fraction of the 18 measured log-frequencies inside the prior predictive central
  95% per mode. Posterior predictive check: PIT (probability integral transform: the posterior-predictive
  CDF evaluated at each measured value; calibrated ⇒ ~uniform on [0,1]) per mode for the reference run.

## C3 — Coverage, band width, and CRPS (A3)
Inherited (must reproduce, definitions in `netcg_qoi.py` of the frozen bake-off):
- QOI = tray-region net-CG force spectrum |S_F|(f) per axis (shear_X, shear_Y, normal_Z) on
  FGRID = 400 linear points, 45–260 Hz, ζ=0.01, reduced 74-mode model; model-internal force units
  (relative comparisons only; the global gain is a fitted nuisance so absolute units cancel).
- weighted_coverage (`netcg_qoi.coverage_vs_truth`): 1-octave-smoothed band [lo,hi] vs 1-octave-smoothed
  truth curves; pointwise ensemble coverage averaged with energy weights w(f) ∝ median-truth(f)²
  (QOI-driving peaks dominate). Calibrated 95% band ⇒ ≈0.95.
- Band-width statistic (`bakeoff.band_ratio`): GRMS(hi−lo) of the method band / GRMS(hi−lo) of the
  FEM+6 dB band; FEM+6 dB band = nominal spectrum ×/÷ 10^(6/20) (i.e. ±6 dB about the θ-map nominal).
- Truth for the scorecard = epistemic truth ensemble (n=200, seed 7; measured modes: 1% freq / 0.35 amp
  lognormal sd; unmeasured: 6% / 0.80) — SYNTHETIC self-consistency, NOT validation. Measured evidence =
  per-drive shear answer key (LSQ modal participation to that drive's measured 111-channel H1,
  `heldout_drive.py`), one global gain per drive.
- Known answers to reproduce: FEM+6 dB weighted coverage 0.865/0.706/0.738 (shear_X/shear_Y/normal_Z),
  statFEM_Fk shear_Y 2.301× / cov 0.982; heldout summary per `heldout_drive.json`.
New (this study):
- CRPS(F, y) = ∫ (F(x) − 1{x≥y})² dx for predictive CDF F and realized truth y. Ensemble form (fair /
  unbiased sample CRPS): CRPS = mean|X−y| − (1/(2n(n−1)))ΣΣ|X_i−X_j|, X = method's predictive samples of
  the 1-octave-smoothed spectrum at a frequency bin. Lower is better; units = force units of the QOI.
- Aggregation: energy-weighted mean over FGRID with the SAME w(f) as weighted_coverage, then averaged over
  truth realizations (synthetic axis) or reported per drive (measured shear axes).
- FEM+6 dB is an envelope, not a distribution. Primary scoring convention: Uniform in log10-force between
  band edges (log-uniform). Sensitivity conventions reported alongside: (a) Uniform in linear force
  between edges; (b) Gaussian in log10-force with the ±6 dB band as central 95%. The conclusion must be
  stated under all three or flagged as convention-dependent.
- Delivered statFEM band and parameter-only propagation are scored from their predictive ensembles
  directly (same n per method, stated in the output JSON).

## C4 — Profile likelihood (A4)
- Likelihood: the iid log-magnitude whole-FRF likelihood of the source study (`arm_b_nuts.py`
  --theta-only): y_{d,ch}(f) = log10|H1_meas| vs log10|H1_model(θ)| + gain_d, residual iid
  Normal(0, σ_n); θ_g = exp(t_g), t_g ~ N(0, 0.25); gain_d ~ N(0,1) dex; σ_n ~ HalfNormal(0.2).
  Exact form re-documented from the frozen source in the output JSON before computing.
- Profile: L_p(θ_g) = max over nuisances (all drive gains, σ_n; other θ fixed at 1) of the log-likelihood
  ×(also recorded: log-posterior variant with the priors added). Grid ≥41 points spanning the prior 95%
  range of θ_g, i.e. exp(±1.96·0.25) ≈ [0.612, 1.633], log-spaced.
- Two profiled parameters = the two stiffness groups with the largest whole-FRF sensitivity
  ‖∂ log10|H|/∂ log θ_g‖ (energy-weighted RMS over the likelihood band at θ=1); choice rule stated in
  the output.
- Inner optimizer convergence (success flag, final gradient norm / iteration count) recorded at every
  grid point. Multimodality claim = number of local maxima along the profile after smoothing-free
  inspection, cross-annotated with the separated NUTS chain means from the retained per-chain draws.

## C5 — Phase diagnostic (A5)
- Circular variance CV = 1 − |mean(exp(iΔφ))| over channels, Δφ = measured-vs-model phase residual at
  matched modes; CV≈1 ⇒ incoherent, CV≈0 ⇒ coherent. Dimensionless. Found artifact value: 0.8536.
- Deliverable is provenance (workspace, file, SHA-256) — no recomputation.
