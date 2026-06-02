# Known Failures And Risks

- NumPyro NUTS was not achieved because NumPyro/JAX are not installed under Python 3.9.6. I used a labeled custom PyTorch HMC backend instead. This is not a random-walk sampler, but it is also not NUTS.
- Tree depth is not applicable to fixed-trajectory HMC; the diagnostics file records fixed leapfrog steps instead.
- Sampler diagnostics are not perfect. Recorded divergences: full = 3, peak-feature = 0. R-hat and ESS should be inspected in `nuts_diagnostics.json` before trusting intervals as final engineering evidence.
- Modal FRF inference uses log magnitudes only. Complex phase and real/imag residual structure are generated but not used in the HMC likelihood.
- Individual build effects and forcing GP paths are not sampled as HMC latent variables. The runner learns their scales and uses posterior predictive draws for QOI intervals.
- The model is a 2DOF synthetic pressure test. It is not a validated rocket hardware analysis.
- Checker-backed artifact existence and consistency do not prove physical correctness.
