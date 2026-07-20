# Assumptions ledger

| ID | Value | Units | Rationale/source | Sensitivity priority |
|---|---:|---|---|---|
| A1 | 45-260 | Hz | Inherited ShockSat PSD-envelope analysis band. | high |
| A2 | 1.0 | lbf^2/Hz | Flat force PSD `S_F0`, identical for all methods. | low for ratios |
| A3 | 0.01 | fraction critical | Nominal modal damping used in the state filter. | high |
| A4 | 2000 | Hz | Downsampled filter rate after anti-alias resampling from 250 kHz; Nyquist exceeds the 260 Hz QOI band. | medium |
| A5 | 122880 | samples at 250 kHz | Inherited modal-hammer ringdown window, about 0.49 s and df about 2.03 Hz. | high |
| A6 | 0.08 | dimensionless | Observation-noise scale: per-channel noise sigma = 8% of training-channel RMS plus floor. Fixed validity-probe hyperparameter, not inferred. | high |
| A7 | 0.08 | dimensionless | Modal residual/process-noise scale relative to modal force participation and median hammer peak. Fixed validity-probe hyperparameter, not inferred. | high |
| A8 | 2 | stiffness groups | Maximum number of stiffness groups freed in the stiffness-updated variant. Selected by observed-mode sensitivity/FIM. | medium |
| A9 | seed 0, 90% training | sensors | First validity probe split inherited from the PSD-envelope thread. | high |
| A10 | 2% | energy fraction | Clean exceedance threshold for held-out measured PSD above the sequential envelope. | high |

Uncertainty separation:

- Parameter uncertainty: small-subset stiffness uncertainty is sampled by NUTS for mode-frequency calibration, but only the posterior median is used in the filter dynamics in this pilot.
- Observation noise: fixed per-channel acceleration noise scale, not inferred.
- Model discrepancy: low-dimensional modal process noise plus training-only multiplicative FRF residual band.
- Forcing uncertainty: measured hammer force is treated as known; no forcing GP posterior is claimed.
- Build/test variability: not modeled; this is one modal-hammer campaign with 6 hits per reference.
- QOI uncertainty: the 97.5% envelope comes from the empirical held-out predictive residual band, not a full hierarchical posterior.

