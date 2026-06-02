# Fresh 2DOF StatFEM/FBS Human-Review Packet

Date: 2026-06-01

One-command replay: `bash scripts/run_fresh_2dof_statfem_fbs.sh`.

## Question Framing

Engineering decision: decide whether the secondary tray analog has acceptable random-vibration response under a flight-like forcing case after updating a fixed-base 2DOF model with synthetic evidence.

Objective/QOI: estimate the posterior distribution of `3 * GRMS` from the tray acceleration response PSD, reported in `g`. The run is successful only if the review packet, sensitivity, references, and checker pass are artifact-backed.

BOED/optimization could choose future measurement class, frequency grid, drive level, sensor set, and forcing basis. Human judgment still chooses the risk threshold, whether this toy model is relevant, and whether apparent-mass-like conventions match real hardware.

Wrong-question trigger: channel convention mismatch, non-distinct Ch2/Ch3 channels, residuals dominated by arbitrary discrepancy/forcing assumptions, or failure to reproduce expected resonance/antiresonance behavior.

![workflow_diagram.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/workflow_diagram.png>)

## Method Summary

This first-pass review summary is intentionally redundant with later sections. These choices control how every plot should be interpreted and should be visible before a reviewer reaches posterior fits.

![statfem_likelihood_graphical_model_legible.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/statfem_likelihood_graphical_model_legible.png>)

| Item | Current run choice |
|---|---|
| Inferred variables | `theta = {k1, k2, zeta1, zeta2, force_amp, force_fc}` |
| Fixed assumptions | `m1=1 kg`, `m2=0.6 kg`, fixed base, one 2DOF coupling convention, frequency grids, QOI definition, and fixed noise/discrepancy hyperparameters |
| Data count | one synthetic dataset: `1` realization per FRF/transfer channel, `1` flight-like response PSD, and `1` secondary time-history realization |
| Flight-to-flight variability | Not modeled; there are no repeated flights or repeated tests in this trial |
| Whole FRF/PSD likelihood | Yes. Ch1-Ch4 use all complex FRF/transfer values at 120 log-spaced frequencies; Ch5 uses all 181 log response-PSD points |
| Peak-only likelihood | No. Peak and notch locations are reference checks and plot diagnostics only |
| Not inferred variables/hyperparameters | Realized discrepancy fields, sensor-noise scales, discrepancy scales, correlation lengths, flight-to-flight effects, and replicate random effects are fixed/not inferred in this toy |
| Posterior spectra | Posterior predictive spectra are distributions over retained samples; a single posterior-mean spectrum is only a visual summary |

Specific likelihood function: for FRF channel `i`, `y_i(f_j) = H_i(f_j; theta) + d_i(f_j) + e_i(f_j)`, with real and imaginary residual vectors evaluated against `K_discrepancy_i + diag(sigma_sensor_i^2)`. For the flight-like response, `log S_obs(f_j) = log S_a2(f_j; theta) + d_psd(f_j) + e_psd(f_j)`, evaluated against `K_discrepancy_psd + sigma_sensor_psd^2 I`. This is a whole-curve likelihood, not a peak-summary likelihood.

## Assumptions Ledger

Key numerical values: `m1=1.000 kg`, `m2=0.600 kg`, nominal tray `75 Hz`, nominal dome `110 Hz`, true tray `86.250 Hz`, true dome `93.500 Hz`, model-form frequency errors `dome -15%` and `tray +15%`, damping errors `dome +25%` and `tray -25%`, complex FRF observation noise `0.080` times local magnitude with a `0.200` median floor, complex FRF GP discrepancy `0.200` times local magnitude, response PSD log-noise sigma `0.180`, response PSD log-discrepancy sigma `0.350`.

Full ledgers: `assumptions_ledger.md`, `assumptions_ledger.json`, and `noise_qoi_7004c_lit_review.md`.

![assumptions_graphical.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/assumptions_graphical.png>)

## Quantity Contracts

Quantity contracts were written before fitting or plotting in `quantity_contracts.md`. The apparent-mass-like channels Ch1-Ch3 are explicitly reciprocal inertance `F/a`, not NASA-HDBK-7004C load apparent mass. Ch4 is standalone tray absolute acceleration transmissibility `a_tray/a_base`. Ch5 QOI is `3 * GRMS` of the tray acceleration response PSD.

Frequency-domain plots use linear magnitudes and log-scaled frequency axes. Frequency-axis metadata is recorded in `manifest.json`.

![model_schematic.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/model_schematic.png>)

## Measurement Channels

| Channel | Numerator | Denominator | Boundary/excitation | Units |
|---|---|---|---|---|
| Ch1 dome-only | `F1` | `a1` | fixed base, tray absent, force on m1 | kg |
| Ch2 coupled primary | `F1` | `a1` | fixed base, tray attached, force on m1 | kg |
| Ch3 coupled tray | `F2` | `a2` | fixed base, tray attached, force on m2 | kg |
| Ch4 standalone tray | `a_tray` | `a_base` | fixed-base shaker-table tray-only test | dimensionless |
| Ch5 flight-like | tray acceleration PSD response | force PSD on m1 | unknown force PSD on m1; QOI `3 * GRMS` | g |

## Synthetic Data and Error Evidence

Clean truth vs observed synthetic data is shown separately from absolute injected GP discrepancy, iid sensor noise, and total error. The updated observation/discrepancy assumptions are intentionally larger and local-magnitude-scaled so the curves are not visually line-on-line. The normalized error plot is only a diagnostic because the denominator can amplify notches.

Dataset count: this run generates one synthetic dataset: `1` realization for each FRF/transfer channel, `1` flight-like response PSD realization, and `1` secondary time-history realization; flight-to-flight variability is not modeled. Repeated-flight scatter is a missing capability, not a hidden feature.

The time-domain flight trace is retained only as a secondary synthetic realization for intuition and plotting. The fitted flight-like likelihood and the QOI are PSD-domain quantities, so the time trace is not the acceptance metric.

![channel_truth_vs_observed.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/channel_truth_vs_observed.png>)

![channel_absolute_error.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/channel_absolute_error.png>)

![channel_normalized_error_diagnostic.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/channel_normalized_error_diagnostic.png>)

![flight_truth_vs_observed.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/flight_truth_vs_observed.png>)

## GP Discrepancy

Covariance definition for FRF discrepancy: `k(f, f') = sigma_d(f) sigma_d(f') exp(-0.5 ((ln f - ln f') / ell_d)^2)`. Real and imaginary parts are independent GP draws for this toy run. Response PSD discrepancy is modeled in log PSD with the same log-frequency idea.

StatFEM-style noise/discrepancy model: generated model discrepancy and sensor noise are kept separate in `fresh_2dof_dataset.json` (`gp_discrepancy`, `iid_sensor_noise`, and `total_error`). The likelihood then uses the sum of discrepancy covariance and sensor-noise covariance. It does not infer a realized discrepancy field or its hyperparameters; those are fixed assumptions in this trial.

![gp_discrepancy_samples.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/gp_discrepancy_samples.png>)

## Bayes Rule Update

Central methodology: the prior has explicit variance assumptions and the likelihood uses the whole frequency-domain data, not only resonance peak locations or magnitudes.

Prior variance assumptions: stiffness uses `log(k/k_nom) ~ Normal(0, 0.18^2)`, so natural frequency has implied `sigma_log(f/f_nom)=0.09` because `f` is proportional to `sqrt(k)`. The untruncated 95% natural-frequency factor is approximately `[0.838, 1.193]`, centered at 110 Hz for the dome and 75 Hz for the tray. Damping uses `log(zeta/zeta_nom) ~ Normal(0, 0.35^2)`, giving an untruncated 95% damping multiplier of approximately `[0.504, 1.986]`, centered at zeta1=0.018 and zeta2=0.026.

Likelihood formulation: Ch1-Ch4 use all complex FRF/transfer values at 120 log-spaced frequencies. For each channel, residuals are `observed complex FRF - model complex FRF`; real and imaginary residual vectors are evaluated independently with covariance `K_discrepancy + diag(sensor_noise^2)`. The flight-like response uses all 181 log response-PSD frequency points with covariance `sigma_log_discrepancy^2 R_logfreq + sigma_log_sensor^2 I`. Peak and notch locations are used only for reference checks and plots, not as likelihood summary statistics.

Method status: realized discrepancy fields and noise/discrepancy hyperparameters are not inferred in this toy. We would like to infer them in the longer-term StatFEM version, but that needs a hierarchical discrepancy/noise model and preferably repeated tests/flights so structural parameters, sensor noise, flight-to-flight variability, and model discrepancy are not hopelessly confounded. Current desired next step: Infer discrepancy fields and/or hyperparameters in a hierarchical StatFEM model, preferably with replicate data so sensor noise, flight-to-flight variability, and model discrepancy are identifiable.

Plain-language model-family caveat: the synthetic data were generated by the same 2DOF equations used in fitting, just with shifted stiffness, damping, and forcing parameters. That means the posterior can fit by moving those parameters. A real FEM may be wrong in ways that no parameter shift can represent, such as missing modes, nonlinear joints, slosh, preload, or incorrect boundary conditions.

Bayes rule in action: the parameter plot shows analytic prior density, a high-sample MC prior histogram diagnostic (`n=80,000`), a one-dimensional conditional likelihood slice, and posterior density for the two natural frequencies and two damping ratios. The likelihood slices hold all other transformed variables at the retained posterior sample with largest log posterior; they are visual diagnostics, not full marginal likelihoods.

Prior visualization policy: the smooth blue curve is the analytic prior density and is the primary prior representation. The light-blue MC prior histogram is shown only as a sampling diagnostic and is labeled separately so histogram roughness is not mistaken for mathematical prior structure. Posterior curves are kernel-density estimates from retained samples.

Likelihood diagnostic: log likelihood at the prior center is `-8.4e+03`, at synthetic truth `167`, and at the retained posterior mode `173`.

![bayes_parameter_update.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/bayes_parameter_update.png>)

| Parameter | Prior median | Posterior median | Posterior 95% CI | Synthetic truth | Units |
|---|---:|---:|---:|---:|---|
| Dome natural frequency | 109.98 | 93.472 | [93.199, 93.795] | 93.5 | Hz |
| Tray natural frequency | 74.97 | 86.253 | [86.042, 86.398] | 86.25 | Hz |
| Dome damping ratio | 0.018028 | 0.021987 | [0.019116, 0.025913] | 0.0225 | ratio |
| Tray damping ratio | 0.026009 | 0.02177 | [0.020177, 0.023802] | 0.0195 | ratio |

Posterior interval diagnostic: synthetic truth falls outside the displayed 95% CI for Tray damping ratio. This is a warning, not a pass.

![parameter_posterior_samples.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/parameter_posterior_samples.png>)

Prior predictive versus data: the base-driven standalone tray transfer, coupled tray drive-point channel, flight-like tray response PSD, and latent force PSD are shown with prior and posterior predictive bands. These are not analytic prior densities; they are smoothed MC predictive summaries. The prior predictive bands use `4000` prior draws, and plotted pointwise quantile summaries are smoothed over frequency with Gaussian sigma `1.8` grid points so resonance-ordering wiggles are not mistaken for prior structure. The force PSD is latent in this toy; the observed flight-like data are the tray response PSD, not a direct force measurement.

![prior_predictive_vs_data.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/prior_predictive_vs_data.png>)

## Whole FRF vs Peak-Feature Likelihood Comparison

This side-by-side comparison asks what changes if the likelihood uses only selected peak/notch frequency and magnitude features instead of the whole complex FRFs and whole response PSD. The peak-feature likelihood uses one dominant feature from each frequency channel plus the response-PSD peak. It treats feature residuals as independent with broad log-frequency and log-amplitude uncertainty. This is a deliberately lossy comparison artifact, not a recommended replacement for the whole-curve StatFEM likelihood.

QOI comparison: full FRF/PSD likelihood mean `12.12 g`, 95% interval `[9.8823, 14.283] g`; peak-feature likelihood mean `10.316 g`, 95% interval `[6.8628, 16.945] g`. Peak-feature QOI 95% width divided by full-curve width is `2.29`.

Feature likelihood assumptions and observed feature values are stored in `peak_feature_likelihood_summary.json`.

![full_vs_peak_feature_likelihood_comparison.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/full_vs_peak_feature_likelihood_comparison.png>)

## Peak/Notch Feature Mapping Benchmark

A peak or notch is not assumed to equal a natural frequency. The feature likelihood compares an observed transfer-function feature with the predicted transfer-function feature from each candidate parameter set. It is therefore benchmarked against `feature(theta)`, not directly compared with the true natural frequency.

In a clean one-DOF-like channel, the feature can sit very near the natural frequency but still depends on the exact quantity, damping, and boundary condition. In coupled channels, notches and response-PSD peaks are mixed features: they can depend on dome frequency, tray frequency, damping, and forcing assumptions at the same time.

| Feature | Clean predicted feature | Observed feature | Frequency z-score | Interpretation |
|---|---:|---:|---:|---|
| Ch1 dome notch | 93.576 Hz | 98.107 Hz | 0.79 | direct structural feature |
| Ch2 primary notch | 129.683 Hz | 129.134 Hz | -0.07 | coupled structural feature |
| Ch3 tray notch | 62.177 Hz | 60.315 Hz | -0.51 | coupled structural feature |
| Ch4 tray peak | 86.341 Hz | 86.416 Hz | 0.01 | direct structural feature |
| Ch5 PSD peak | 62.378 Hz | 62.398 Hz | 0.01 | forcing/response-shape confounded feature |

The sensitivity matrix below reports log-log slopes of each selected feature with respect to the inferred variables at the synthetic truth. Ch1 and Ch4 are close to direct structural features. Ch2 and Ch3 mix dome and tray frequency information. Ch5 is a response/forcing feature, so its amplitude is strongly confounded with the assumed force spectrum.

![peak_feature_mapping_benchmark.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/peak_feature_mapping_benchmark.png>)

![peak_feature_sensitivity_matrix.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/peak_feature_sensitivity_matrix.png>)

## Posterior Fit and Diagnostics

Sampler: single-coordinate random-walk Metropolis-Hastings; steps `3800`, burn `1000`, thin `5`, retained samples `560`, acceptance rate `0.499`.

The older posterior-fit plot uses a posterior-mean prediction as a summary line. The posterior predictive figure below shows the distribution across retained samples; that is the correct object to inspect when asking how much spectral uncertainty remains.

![posterior_fit_and_residuals.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/posterior_fit_and_residuals.png>)

![posterior_predictive_spectra.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/posterior_predictive_spectra.png>)

Why the fit can move far from nominal: the synthetic truth is inside the same parametric model family used by the likelihood, and the priors are broad enough that the many FRF/PSD frequency points dominate the nominal prior center. This is useful for checking Bayes-rule plumbing, but it is optimistic compared with a real FEM/model-form misspecification problem.

![sampler_diagnostics.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/sampler_diagnostics.png>)

## QOI Summary

QOI posterior samples: definition `3 * GRMS of tray acceleration response PSD`, mean `12.1201 g`, 5-95% interval `[10.2192, 13.9448] g`, truth `10.8949 g`, mean bias `1.22515 g`, fraction above truth `0.861`.

![qoi_samples.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/qoi_samples.png>)

## Sensitivity to Assumptions

Sensitivity meaning: the synthetic-data error sensitivity asks how large the injected measurement/model-error terms become if the assumed noise or discrepancy scale changes. It does not rerun inference. The QOI sensitivity keeps the retained posterior samples fixed and re-computes `3 * GRMS` under damping and forcing-band variants. It is a quick fragility check, not a full posterior refit for every scenario.

No pass/fail decision threshold is asserted in this synthetic run; a real threshold is a human engineering decision.

![sensitivity_qoi.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/sensitivity_qoi.png>)

![sensitivity_synthetic_error.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/sensitivity_synthetic_error.png>)

## Reference and Standards Comparison

NASA-HDBK-7004C comparison: the packet now includes NASA-HDBK-7004C Figure 9 normalized source/load apparent-mass benchmark values and fresh source/load-style apparent-mass curves. Ch1-Ch3 remain reciprocal inertance and are labeled separately.

The previous green pass/fail bar chart was only a checker scoreboard. It has been replaced by a value table so a reviewer can see the actual computed numbers, the reference expectations, and the engineering meaning.

vibrationdata.com comparison: used as a classical SDOF/2DOF sanity-check family for transmissibility, resonance location, rolloff, and distinct drive-point behavior.

Reference metrics: Ch4 low-frequency median `1.029`, Ch4 high-frequency median `0.2307`, Ch4 peak `86.903 Hz` vs tray truth `86.250 Hz`, Ch1 notch `93.515 Hz` vs dome truth `93.500 Hz`, Ch2/Ch3 relative L2 `0.6739`, NASA-HDBK-7004C Figure 9 load `M(0.62)=1.624`, load `M(1)=50.010`, source `M(1)=0.0200`.

![reference_standards_comparison_cards.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/reference_standards_comparison_cards.png>)

![nasa_7004c_apparent_mass_benchmark.png](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/fresh_2dof_statfem_fbs_20260601/figures/nasa_7004c_apparent_mass_benchmark.png>)

## Checker Status

Fresh checker status: **PASS**.

Image legibility QA: **PASS**. Strict text-heavy figures checked: `figures/statfem_likelihood_graphical_model_legible.png, figures/reference_standards_comparison_cards.png`. Full details are in `image_legibility_report.json`.

| Acceptance condition | Result |
|---|---:|
| required_files_exist | True |
| required_report_snippets_present | True |
| numerical_assumptions_present | True |
| model_error_assumptions_present | True |
| reference_comparison_present | True |
| reference_value_metrics_present | True |
| sensitivity_artifact_present | True |
| no_arbitrary_sensitivity_threshold_language | True |
| channel_2_and_3_not_duplicates | True |
| frequency_axis_metadata_log | True |
| qoi_sample_summary_exists | True |
| bayes_parameter_update_artifact_present | True |
| posterior_parameter_95_ci_exists | True |
| simulation_replicate_count_reported | True |
| statfem_noise_model_documented | True |
| prior_likelihood_methodology_documented | True |
| method_summary_documented | True |
| peak_feature_likelihood_comparison_present | True |
| peak_feature_mapping_benchmark_present | True |
| image_legibility_report_pass | True |
| checker_status_and_limitations_included | True |

Checker-backed acceptance conditions include required report/figures, numerical assumptions, reference comparison, sensitivity artifact, Ch2/Ch3 non-duplication, frequency-axis metadata, QOI samples, checker status, and limitations.

## Fresh-Agent Comparison

This comparison was generated after fresh outputs were written.

**Matched:** same nominal 75 Hz tray and 110 Hz dome problem class; synthetic observation noise plus model-form discrepancy; log-scaled frequency-domain review plots; separate Ch2 and Ch3 drive/response definitions; posterior QOI samples, sampler diagnostics, sensitivity, and checker-backed packet; NASA-HDBK-7004C used to prevent apparent-mass convention overclaiming.

**Differed:** fresh coupled assembly uses one tray-to-primary stiffness/damping and no direct tray-to-base spring in the coupled model; updated flight-like measurement uses a response PSD likelihood and 3*GRMS QOI rather than a deterministic time-history peak; updated noise/discrepancy is larger, local-magnitude scaled, and visibly separates observed from clean curves; synthetic truth now includes explicit model-form shifts of -15%/+15% in natural frequency and +25%/-25% in damping ratio; fresh checker and artifacts are scoped under a separate rerun directory.

**Improvements:** question framing, assumptions, and contracts were written before fresh plots/fits; absolute injected GP, iid, and total errors are stored for every channel; the report includes explicit NASA-HDBK-7004C Figure 9 source/load apparent-mass benchmark values; reference comparison is now a value table instead of a pass/fail bar chart.

**Unresolved:** synthetic-only toy with no physical hardware data; simple random-walk MH rather than NUTS/HMC or formal convergence diagnostics; sensitivity does not refit the posterior for every noise/discrepancy scenario; the larger discrepancy assumptions are literature-informed but not calibrated to a specific tank/tray test article.

**Gates that prevented mistakes:** Question gate prevented optimizing a QOI before stating the engineering decision; Quantity-contract gate forced separation between reciprocal inertance and 7004C source/load apparent mass; Plot gate forced log frequency axes and linear magnitude units; Verification gate forced a duplicate-channel numerical check and report-content checker.

## Limitations

- Synthetic-only data; no real tank, tray, dome, shaker, or flight data are used.
- Only one synthetic realization is generated per measurement class; flight-to-flight variability and repeated-test variability are not modeled.
- The two-DOF model is linear, fixed-base, and low order; no slosh, nonlinear joints, preload, build variability, or FEM modal reduction is represented.
- The larger GP/log-PSD discrepancy assumptions are literature-informed but not calibrated to a real tank/tray dataset.
- Random-walk MH is auditable but not a production-grade sampler; convergence is not proven by trace plots.
- Sensitivity is first-pass and does not refit the posterior for all error-model scenarios.
- Reference/standards checks are shape, convention, and benchmark-value checks, not qualification or NASA compliance evidence.

## Human Reflection Prompts

- Is `3 * GRMS` tray acceleration the right QOI, or should stress, relative displacement, fatigue damage, or interface force be used?
- Would a real apparent-mass test use the same numerator/denominator and source/load boundary conditions?
- How many repeated flights/tests are needed before flight-to-flight variability can be separated from sensor noise and model discrepancy?
- Which uncertainty source should be reduced before an autonomous experiment loop is trusted?
- What threshold would make the flight-like QOI a decision rather than a plot?
