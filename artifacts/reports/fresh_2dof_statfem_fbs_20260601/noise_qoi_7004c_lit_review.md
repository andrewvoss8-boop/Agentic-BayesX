# Literature/Reference Review: Noise, PSD QOI, and 7004C Apparent Mass

Date: 2026-06-01

Purpose: correct the fresh 2DOF rerun after human review found the synthetic observations visually too clean, the QOI too dependent on one deterministic time trace, and the apparent-mass plots insufficiently tied to NASA-HDBK-7004C benchmark behavior.

## PSD QOI

NASA-STD-5002B describes random vibration excitation through interface acceleration PSDs and notes that random-vibration loads may be represented by RMS values multiplied by a factor such as 3, depending on the statistical distribution and enclosure/confidence level. This supports changing the QOI from one time-history peak to:

`QOI = 3 * sqrt(integral S_a(f) df)`

where `S_a(f)` is the tray acceleration response PSD in `g^2/Hz`. The result is reported in `g`.

Reference used:
- NASA-STD-5002B, Appendix C random vibration discussion: https://standards.nasa.gov/system/files/tmp/Final%20Approved%20NASA-STD-5002_REV%20B%20-%2003-10-2026.pdf

## Noise and Discrepancy Assumptions

The first fresh run used additive complex noise of 2.5% of channel median magnitude and GP discrepancy of 3.5% of channel median magnitude. That made observed and clean curves nearly indistinguishable on the review axes and is not a good stress test of the harness.

Reference signals from aerospace practice:
- NASA-STD-7001B uses random-vibration levels that envelope maximum expected flight level plus 3 dB for qualification/protoflight testing and lists a minimum workmanship random vibration spectrum with overall level `6.8 grms`.
- ECSS-E-ST-10-03C gives random-vibration PSD allowable tolerances of `-1 dB / +3 dB` from 20 Hz to 1000 Hz, `±3 dB` from 1000 Hz to 2000 Hz, and random overall `g r.m.s.` tolerance of `±10%`.
- NASA/NESC uncertainty-propagation guidance states that model uncertainty is unavoidable and that aerospace FEM errors are often model-form errors rather than only parameter errors.

Chosen updated assumptions:
- Complex FRF observation noise: `8%` of local magnitude, with a floor of `20%` of channel median magnitude.
- Complex FRF model discrepancy GP: `20%` of local magnitude, with the same local floor, correlated in natural log frequency.
- Flight response PSD observation scatter: lognormal iid `sigma_ln = 0.18`.
- Flight response PSD model discrepancy: log-frequency GP in log PSD with `sigma_ln = 0.35`.
- Explicit model-form frequency error in the synthetic truth: dome `-15%` and tray `+15%` relative to nominal natural frequency.
- Explicit model-form damping error in the synthetic truth: dome damping ratio `+25%` and tray damping ratio `-25%` relative to nominal damping.

These are still synthetic assumptions, not universal aerospace constants. They are intentionally more conservative and more visually reviewable than the first fresh run. The PSD discrepancy values are below a full one-sigma 3 dB PSD band (`ln(2) ~= 0.693`) but large enough to expose model-form error.

The `+/-15%` frequency and `+/-25%` damping choices are treated as a conservative weak-model stress case, not as standard pass/fail tolerances. NASA/NESC structural-dynamics UQ guidance supports separating model updating from uncertainty quantification and notes that model-form uncertainty cannot be represented completely by ordinary FEM input parameters. NASA/TM-20220010939 specifically describes hybrid parametric variation using fixed-interface modal-frequency variation layered with nonparametric matrix variation, and states that aerospace FEM errors are often model-form errors rather than clean parameter errors. A space-vehicle first-stage motor model-updating paper reports an initial maximum frequency error of about `15%` before updating, which makes the `15%` synthetic frequency shift a plausible stress-test magnitude for an unvalidated toy model. Damping is less reliably predicted and identified than frequency in modal work, so the `25%` damping shift is included as a human-review stress assumption and must not be interpreted as calibrated to this tank/tray analog.

References used:
- NASA-STD-7001B: https://standards.nasa.gov/sites/default/files/standards/NASA/B/0/nasa-std-7001b.pdf
- ECSS-E-ST-10-03C: https://s3vi.ndc.nasa.gov/ssri-kb/static/resources/ECSS-E-ST-10-03C.pdf
- NASA/NESC model uncertainty article: https://www.nasa.gov/centers-and-facilities/nesc/uncertainty-propagation-for-model-validation-using-a-hybrid-parametric-variation-method/
- NASA Engineering and Safety Center Technical Bulletin 22-04: https://ntrs.nasa.gov/citations/20220010362
- NASA/TM-20220010939, `Uncertainty Models for the Hybrid Parametric Variation Method of Uncertainty Quantification`: https://ntrs.nasa.gov/citations/20220010939
- Space vehicle first-stage motor model updating paper, abstracted frequency-error example: https://www.sciencedirect.com/science/article/abs/pii/S1270963815001911

## NASA-HDBK-7004C Apparent-Mass Benchmark

NASA-HDBK-7004C defines apparent mass for force-limited vibration in terms of interface reaction force over interface acceleration. It discusses measuring drive-point apparent mass as total reaction force divided by input acceleration, and Figure 9 gives benchmark behavior for a two-identical-oscillator impedance-method example.

Benchmark values used in the fresh plot:
- Figure 9 source apparent mass, normalized SDOF expression with `Q = 50`: `|1 - r^2 + i r/Q| / r^2`.
- Figure 9 load apparent mass, normalized SDOF expression with `Q = 50`: `|1 + i r/Q| / |1 - r^2 + i r/Q|`.
- At `r = 1`, the load apparent-mass peak is about `50.01` and the source apparent-mass notch is about `0.02`.
- At lower coupled-system resonance ratio `r = 0.62`, the load apparent mass is about `1.62`.

The fresh packet now plots these normalized 7004C benchmark curves alongside fresh-run source/load-style apparent-mass curves so the toy result can be compared against the standard shape and values without mislabeling reciprocal inertance.

Reference used:
- NASA-HDBK-7004C Force Limited Vibration Testing Handbook: https://experiorlabs.com/wp-content/uploads/2019/10/NASA-HDBK-7004C-Force-Limited-Vibration-Testing.pdf
