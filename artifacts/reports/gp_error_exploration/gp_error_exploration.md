# GP Error Exploration

This artifact makes the current frequency-domain model discrepancy visible.

## Short Answer

Yes, Agentic BayesX already generates additive model error with a zero-mean Gaussian process over frequency. The current synthetic generator draws independent real and imaginary GP discrepancy functions for each channel, then adds independent sensor noise.

The inference likelihood also uses a squared-exponential frequency covariance, plus iid noise variance, to marginalize residual error.

## Current Settings

| Term | Value |
|---|---|
| GP scale `discrepancy_scale` | 0.03 |
| GP correlation length `discrepancy_corr_hz` | 8.0 Hz |
| iid real noise `sigma_re` | 0.02 |
| iid imaginary noise `sigma_im` | 0.02 |

## Figures

![GP covariance](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/gp_error_exploration/gp_frequency_covariance.png>)

![GP samples](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/gp_error_exploration/gp_error_samples.png>)

![Ch2 components](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/gp_error_exploration/gp_error_components_ch2.png>)

## Important Limitations

- The main dataset currently stores only clean and observed channels. It does not store the realized GP discrepancy separately from iid sensor noise.
- Real and imaginary parts are modeled as independent GPs. That is simple and transparent, but it is not a full complex-valued GP.
- All channels share the same discrepancy scale and correlation length. This is unlikely to be adequate for real FRFs with different units and magnitudes.
- The GP discrepancy is additive in raw channel units. A per-channel or relative-error model is probably more defensible later.
- Inference marginalizes discrepancy through the covariance instead of estimating latent discrepancy curves.
