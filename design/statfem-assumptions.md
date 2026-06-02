# StatFEM/FBS Assumptions (2DOF bootstrap)

## System
- 2DOF fixed-base model.
- `m1` = primary (tank dome analog), nominal natural frequency 110 Hz.
- `m2` = secondary (tray analog), nominal natural frequency 75 Hz.
- Coupled through tray fixed-base properties (`k12 = k2`, `c12 = c2`) rather than separate independent coupling variables.

## Measurement channels
1. Dome drive-point apparent mass (uncoupled modal representation).
2. Coupled primary-side interface apparent mass, approximated as assembled-system drive-point `F1/a1` at `m1`.
3. Coupled tray apparent mass, approximated as assembled-system drive-point `F2/a2` at `m2` for an impact/response analog.
4. Standalone tray accel/accel transfer from base excitation.
5. Flight extension: unknown forcing spectrum on `m1` and tray peak-response QOI.

## Review transfer functions
- Acceleration/force FRFs use `a/F = -omega^2 x/F` and are reported as linear magnitude, not dB.
- Plotted apparent masses distinguish NASA-HDBK-7004C source and load conventions. Source apparent mass looks back into the source/mounting structure and has a resonance notch; load apparent mass is the load-side interface reaction over input/interface acceleration and has a fixed-base resonance peak.
- Drive-point `F/a` at a moving response coordinate is reciprocal inertance. It is retained in the JSON summary for traceability.
- Current key FRFs for review:
  - dome-only `a1/F1`;
  - coupled `a1/F1`, `a2/F1`, `a1/F2`, `a2/F2`;
  - standalone dome source apparent mass;
  - standalone dome load-style base-reaction apparent mass;
  - standalone tray load apparent mass `Fbase2/abase`;
  - coupled primary support, tray support, and total base apparent mass;
  - standalone tray `a2/abase`.
- The key-FRF plot uses a log-scaled frequency axis over the synthetic dataset frequency range and shows fixed-mass reference lines for `m1`, `m2`, and `m1 + m2`, plus vertical reference lines at the uncoupled dome and tray natural frequencies.

## Noise and discrepancy
- Observation noise: additive complex Gaussian with independent real/imag parts.
- Model discrepancy: additive zero-mean Gaussian process over natural log frequency with a squared-exponential/RBF kernel. Let `eta = ln(f)`;
  `k(eta, eta') = sigma_d^2 exp(-0.5 ((eta - eta') / ell_d)^2)`.
- Rationale: broad-band structural dynamics plots are usually reviewed on logarithmic frequency axes, and modal feature width is often better treated as a fractional-frequency phenomenon than as a fixed-Hz phenomenon. This is a modeling assumption, not a proven physical law.
- In the current bootstrap, real and imaginary discrepancy components are independent GP draws for each channel. Channels share the same `sigma_d` and `ell_d`; this is transparent but probably too blunt for real FRFs with different units and magnitudes.
- Shared discrepancy hyperparameters in bootstrap:
  - `sigma_d` (scale),
  - `ell_d` in natural-log-frequency units (correlation length).
- Parameter uncertainty: posterior uncertainty on `k1`, `k2`, `c1`, and `c2`; `k12` and `c12` are tied to `k2` and `c2`.
- Forcing uncertainty: posterior uncertainty on the two-parameter flight input model (`force_amp`, `force_fc`).
- QOI uncertainty: posterior uncertainty in peak tray acceleration during the flight forcing scenario.
- QOI samples are computed by evaluating the tray acceleration spectrum for each retained posterior parameter sample and taking the peak over the frequency grid.

## Question framing
- Engineering decision: decide which measurements make the tray flight-response estimate more credible.
- Candidate objective: reduce uncertainty in stiffness, damping, forcing, and peak tray acceleration QOI.
- BOED boundary: BOED can optimize over a stated experiment menu and objective, but cannot decide whether the QOI, simulator, or experiment class is the right one.
- Human judgment remains responsible for reframing the question, rejecting bad objectives, and choosing when synthetic results are informative enough to justify real-data work.

## Inference
- Full MCMC via random-scan Metropolis-Hastings in log-parameter space.
- One positive parameter is proposed per step by default (`proposal_block_size = 1`) to avoid very low acceptance in the tightly identified synthetic posterior.
- Proposal scale is adapted during burn-in toward a target acceptance rate, then held fixed for retained samples.
- Positive parameters represented in log space.
- Priors: Gaussian in log space around engineering nominals.
- Status: this sampler is a prototype/legacy baseline. Future Bayesian updating work should use NUTS/HMC as the default unless a task card gives a checked reason to use another sampler.

## Sensitivity posture
- Sensitivity to assumptions should be treated as a default work product, not an optional afterthought.
- Current first-pass sensitivity varies synthetic iid noise and GP discrepancy hyperparameters and reports error against clean truth.
- Required next step: propagate assumption changes through posterior summaries and QOI uncertainty, then report whether engineering recommendations change.

## Plotting posture
- Frequency-domain packet plots should use log-scaled frequency axes unless a plot is explicitly checking uniform linear-Hz behavior.
- Linear-frequency plots in earlier packet revisions were an agent workflow miss: the log-axis requirement was implemented for the key FRF plot but not propagated to newly-added channel/error plots.

## Validity bounds
- This is a synthetic benchmark to validate harness discipline and posterior mechanics.
- Not yet calibrated against physical test hardware.
- Apparent-mass and FRF definitions are simplified to maintain a transparent baseline.
- The toy model has no explicit boundary/interface coordinate, so channel 2 uses the primary-side coordinate as a proxy for interface apparent mass.
