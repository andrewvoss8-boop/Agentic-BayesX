# Assumptions ledger

| ID | Value / assumption | Units | Rationale / source | Sensitivity priority |
|---|---|---:|---|---|
| A1 | Analysis band 45–260; primary grid 2.5 Hz | Hz | Frozen ShockSat band; 2.5 Hz gives four points per 10 Hz covariance length and resolves broad transfer structure, not individual razor-sharp peaks | High; repeat at 1.25 Hz near scored cores |
| A2 | `H_ref = 1 g/lbf` | g/lbf | Makes the natural logarithm dimensionless | Fixed |
| A3 | Modal parameter prior is the retained 4,000-draw converged full-data posterior; 32 hash-spaced draws used in modular prediction | dimensionless stiffness multipliers | `shocksat_fem_modal_twin_20260609/nuts_full_samples.npz`; max R-hat 1.0224, min ESS 232, 0 divergences | Medium; 64-draw check |
| A4 | Damping ratio `zeta = 0.01` plus inherited measurement window | dimensionless | Frozen real-FRF forward model | High; documented gap, not re-inferred here |
| A5 | Observation/spectral-estimation scale `sigma_e = 0.15` | natural-log ratio | Frozen Schneider implementation; one processed impact per selected drive file, so independent repeats are absent from this layer | High |
| A6 | GP kernel `l_f=10`, `l_x=2000`, `r=0.82` | Hz, in, dimensionless | Frozen primary Schneider-style values | High; training-only bounded grid sensitivity |
| A7 | GP amplitude candidates `{0.30,0.60,1.00,1.50}` selected by training marginal likelihood | natural-log ratio | Avoids outer-test tuning while permitting the realized discrepancy scale to differ by fold | High |
| A8 | Coefficient prior scale `tau_beta=0.35` on RMS-normalized constrained columns | natural-log ratio | About 3.0 dB per standardized basis direction; fixed before responses | High; `{0.20,0.50}` sensitivity if measured stage runs |
| A9 | Frequency basis: six cubic B-spline degrees of freedom in log frequency | dimensionless basis | Task card | Fixed |
| A10 | Location basis: five nearest-physical-region indicators plus five Gaussian radial functions; deterministic coordinate-only k-medoids | dimensionless basis | Task card | Fixed |
| A11 | Rank tolerance `1e-10` relative to largest singular value; pseudoinverse tolerance `1e-10` | dimensionless | Frozen before fitting | Medium |
| A12 | Primary selected response set: 15 mapped channels, one X/Y/Z channel per frozen physical region where available, chosen nearest each region centroid without residuals; spatial folds are then coordinate-only k-medoids | — | Keeps all five mean regions and all three response axes in the exact-Gaussian study while staying inside the Stage-1 cap | High; selection limits generality |
| A16 | The `+XY (990)` drive is represented by an equal-amplitude normalized X+Y drive row at its frozen impact coordinate | — | The source cache labels a combined XY excitation, while the reduced forward exposes Cartesian drive rows | High; forcing-direction approximation |
| A13 | Drive gain `c_d` is fitted from retained data in spatial/band folds; for leave-drive-out it uses the training-drive empirical Normal prior predictive | natural-log ratio | Card quantity contract | High |
| A14 | Shared mean and GP act on `(f,x,a)` across drives; a measured drive×frequency variance dominance is a wrong-question finding | natural-log ratio | Card | High |
| A15 | Synthetic seeds 0–19; GP/noise draws use NumPy PCG64 and stored seeds | — | Deterministic replay | Fixed |

## Uncertainty bookkeeping

Inferred in Stage 1: fold-specific drive gains, GP amplitude selected from a frozen training-only grid, conditional mean coefficients, and the conditioned residual GP. Fixed: kernel primary lengths/split, observation scale, damping, basis rules, and FEM model form. Modular parameter uncertainty comes from retained modal-posterior draws and is not updated by response data. Not inferred: build-to-build variability, response-axis misorientation, channel identity effects, forcing spectra beyond one scalar drive gain, and repeat-to-repeat impact variability. Those omissions bound the claim.
