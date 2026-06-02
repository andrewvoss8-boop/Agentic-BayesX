# Assumptions Ledger

| Assumption | Value | Units | Source | Rationale | Sensitivity |
|---|---|---|---|---|---|
| PSD-space dB convention | factor = 10 ** (dB / 10) | dimensionless PSD multiplier | setup packet | All dB values are power/PSD quantities. | High |
| Smoothline PSD points | [(20,0.01),(100,0.1),(750,0.1),(2000,0.001)] | Hz, g^2/Hz | human task card | Original test spec for envelope comparison. | High |
| Flight forcing mean offset | -6.0 | dB PSD | project setup assumption | Mean flight forcing is below original force PSD; not a GEVS margin. | High |
| Flight forcing variability | 3.0 | dB PSD sigma | setup/task card | Known Matern forcing variability, fixed in inference. | High |
| Forcing covariance | Matern-3/2 ell=0.08 | natural log frequency | setup/task card | Flight forcing curves are correlated over log frequency. | High |
| Build-to-build scale prior | HalfNormal(0.5) on natural-log PSD sigma | ln PSD | round-2 model | Learn build variability with non-centered raw build effects. | High |
| Sensor scale prior | HalfNormal(0.3) on natural-log PSD sigma | ln PSD | round-2 model | Learn observation scatter for full PSD/modal curves. | High |
| Flight QOI observation noise | 0.08 | natural log 3*GRMS | round-2 model assumption | Scalar flight observations need residual noise beyond sampled forcing latent. | Medium |
| Structural stiffness prior | log(k/k_nom) ~ Normal(0,0.18^2), truncated [0.55,1.65] | dimensionless | setup prior summary | Prior centers from fresh 2DOF setup. | High |
| Damping prior | log(zeta/zeta_nom) ~ Normal(0,0.35^2), truncated [0.004,0.09] | dimensionless | setup prior summary | Positive damping with broad uncertainty. | High |
| Likelihood data usage | whole stored tray PSD and modal log-magnitude curves; scalar flight 3*GRMS observations | mixed | round-2 model | No full flight PSD observations are stored in sequential_dataset.json. | High |
| Response evaluation grid | stored 260 point grid plus mode-local refinement | Hz | round-2 resolution gate | Resolve tray/dome modes without inventing a new coarse truth. | High |
