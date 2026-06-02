# Agentic BayesX Synthetic StatFEM Packet

Generated: 2026-06-01

## Scope: 2DOF, Not Two MDOFs

This packet is for the current synthetic **2DOF** workflow:

- `m1` is the primary dome analog.
- `m2` is the secondary tray analog.
- Coupling is tied to the tray fixed-base properties: `k12 = k2` and `c12 = c2`.

It is not yet the future workflow with **two separate MDOF/FEM structures** coupled through FBS. The repository does contain a small MDOF transfer-function prototype, but that is a separate sanity check and not the system being updated in this packet.

## Question Framing

Engineering question: which synthetic tests best inform the stiffness, damping, unknown forcing, and peak tray response of a primary dome plus secondary tray system?

Decision being supported: prepare a clear, auditable toy workflow before moving to F-16/Vibrationdata real-data pilots.

BOED stance: BOED can optimize a stated objective over a fixed menu of experiments, but it cannot decide whether the QOI, model class, or experiment family is the right one. Those remain human-in-the-loop decisions.

![question framing](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/question_framing.png>)

## Assumptions and Units

- Frequencies are in Hz.
- `m1 = 1.0` and `m2 = 0.6` are synthetic mass units.
- Stiffness and damping are SI-like only relative to those synthetic masses and Hz inputs.
- Coupling is not independently estimated in this version: `k12 = k2` and `c12 = c2`.
- Apparent masses use synthetic mass units.
- Tray flight QOI uses synthetic acceleration spectrum units.
- The unknown flight input is currently represented by two parameters, `force_amp` and `force_fc`.

![model schematic](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/model_schematic.png>)

## Experimental Setup and Workflow

The synthetic experiment is a sequence of virtual tests on the same 2DOF dome/tray system:

1. Dome-only modal test: estimate primary drive-point apparent mass before tray attachment.
2. Coupled primary-side apparent mass: assembled system response at the primary/interface coordinate.
3. Coupled tray impact test: assembled system response at the tray coordinate.
4. Tray standalone shaker-table test: tray base-to-tray acceleration transfer without the dome.
5. Flight-like response case: unknown primary forcing drives the coupled system, and the QOI is peak tray acceleration.

The agent workflow is: declare the question, generate clean 2DOF channels, add GP discrepancy and sensor noise, infer parameters/forcing/QOI, run checks, then package results for human review.

![experimental workflow](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/experimental_workflow.png>)

## Measurement Channels

| Item | Value |
|---|---|
| dome_drive_apparent_mass_modal | F1/a1: Uncoupled primary/dome drive-point apparent mass before tray attachment. |
| coupled_interface_apparent_mass_modal | F1/a1: Coupled system drive-point apparent mass at the primary-side interface coordinate m1. |
| coupled_tray_impact_apparent_mass_test | F2/a2: Coupled system drive-point apparent mass at the tray coordinate m2 during an impact/response test. |
| tray_standalone_accel_over_base | a_tray/a_base: Fixed-base tray-only acceleration transmissibility from shaker table base acceleration. |
| flight_tray_accel_from_unknown_m1_force | a2: Tray acceleration response to an unknown force spectrum applied to primary coordinate m1. |

The key Milestone 2 correction is that channel 2 and channel 3 now use different coordinates: channel 2 is primary-side `F1/a1`, while channel 3 is tray-side `F2/a2`.

## Key Transfer Functions (Linear Units)

The workflow now reports key 2DOF transfer functions as linear magnitudes, not dB. Acceleration/force FRFs use `a/F`. The apparent-mass panel distinguishes the NASA-HDBK-7004C source and load conventions: the source apparent mass has a resonance notch, while the load apparent mass has a fixed-base resonance peak. The plot uses a log-scaled frequency axis and mass units; the apparent-mass panel also uses a logarithmic magnitude axis to show both the source notch and load peaks.

![key 2DOF transfer functions in linear units](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/plots/key_2dof_transfer_functions_linear.png>)

Reference lines added to the apparent-mass panel:

| Item | Value |
|---|---|
| m1 primary/dome mass | 1 |
| m2 secondary/tray mass | 0.6 |
| m1 + m2 total mass | 1.6 |
| tray uncoupled fn | 75 Hz |
| dome uncoupled fn | 110 Hz |

| Item | Value |
|---|---|
| Dome-only a1/F1 | acceleration_over_force; units = accel/force; max magnitude = 33.34 at 110 Hz; min magnitude = 0.008333 at 10 Hz |
| Coupled a1/F1 | acceleration_over_force; units = accel/force; max magnitude = 13.09 at 135.4 Hz; min magnitude = 0.007314 at 10 Hz |
| Coupled a2/F1 | acceleration_over_force; units = accel/force; max magnitude = 14.67 at 92.49 Hz; min magnitude = 0.00369 at 10 Hz |
| Coupled a1/F2 | acceleration_over_force; units = accel/force; max magnitude = 14.67 at 92.49 Hz; min magnitude = 0.00369 at 10 Hz |
| Coupled a2/F2 | acceleration_over_force; units = accel/force; max magnitude = 30.11 at 92.49 Hz; min magnitude = 0.01681 at 10 Hz |
| Source dome apparent mass | source_apparent_mass; units = mass; max magnitude = 120 at 10 Hz; min magnitude = 0.03 at 110 Hz |
| Dome load apparent mass | load_apparent_mass; units = mass; max magnitude = 33.33 at 110 Hz; min magnitude = 0.5965 at 180 Hz |
| Tray load apparent mass | load_apparent_mass; units = mass; max magnitude = 14.91 at 74.79 Hz; min magnitude = 0.1266 at 180 Hz |
| Coupled primary support apparent mass | base_reaction_apparent_mass; units = mass; max magnitude = 22.6 at 92.04 Hz; min magnitude = 0.5027 at 120.6 Hz |
| Coupled tray support apparent mass | base_reaction_apparent_mass; units = mass; max magnitude = 12.93 at 92.49 Hz; min magnitude = 0.09352 at 147 Hz |
| Coupled total base apparent mass | base_reaction_apparent_mass; units = mass; max magnitude = 35.48 at 92.04 Hz; min magnitude = 0.7474 at 180 Hz |
| Standalone tray a2/abase | transmissibility; units = accel/accel; max magnitude = 24.86 at 74.79 Hz; min magnitude = 0.211 at 180 Hz |

Important convention fix: earlier versions of this plot collapsed source and load apparent mass. In NASA-HDBK-7004C, source and load apparent masses are both interface quantities, but the source and load constraints are different. The drive-point `F/a` terms below are retained for traceability as reciprocal inertance.

| Item | Value |
|---|---|
| Drive-point dome F1/a1 | reciprocal inertance; units = mass; minimum magnitude = 0.03 at 110 Hz |
| Drive-point primary-side F1/a1 | reciprocal inertance; units = mass; minimum magnitude = 0.07641 at 135.4 Hz |
| Drive-point tray-side F2/a2 | reciprocal inertance; units = mass; minimum magnitude = 0.03321 at 92.49 Hz |

## Error and Uncertainty Taxonomy

![error taxonomy](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/error_taxonomy.png>)

Actual error hyperparameters used in this run:

| Item | Value |
|---|---|
| GP type | zero-mean squared-exponential/RBF GP over natural log frequency |
| GP covariance | eta = ln(f); k(eta, eta') = sigma_d^2 exp(-0.5 ((eta - eta') / ell_d)^2) |
| GP draw structure | independent real and imaginary GP draws per channel with shared hyperparameters |
| iid real sigma | 0.02 |
| iid imaginary sigma | 0.02 |
| GP discrepancy scale | 0.03 |
| GP discrepancy coordinate | natural_log_frequency |
| GP discrepancy log-frequency corr length | 0.08 |
| posterior mean sigma_d | 0.3987 |
| posterior mean ell_d_logfreq | 0.01539 |
| posterior mean sigma_n | 0.2471 |

![error hyperparameters](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/error_hyperparameters.png>)

The discrepancy model is a zero-mean squared-exponential Gaussian process over natural log frequency, `eta = ln(f)`. This makes correlation depend on frequency ratio rather than an absolute Hz gap, which is a more natural first assumption for broad-band structural dynamics plots and modal features that are usually reviewed on logarithmic frequency axes. In this bootstrap, real and imaginary parts are drawn independently for each channel, all channels share the same `sigma_d` and `ell_d`, and the discrepancy is additive in raw complex channel units.

![GP discrepancy sample paths](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/gp_discrepancy_samples.png>)

Primary measurement view:

![clean truth vs observed synthetic data](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/channel_truth_vs_observed.png>)

Primary error-injection view:

![absolute injected synthetic error](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/channel_absolute_error.png>)

Secondary diagnostic: normalized error shows where the injected error is large relative to the clean signal. Peaks in this plot can be caused by small `|truth|` in the denominator, so it should not be read as evidence that the random error model is physically locked to resonances or antiresonances.

![relative error diagnostic](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/channel_error_vs_truth.png>)

Frequency-axis note: packet frequency-domain plots use log-scaled frequency axes. The prior packet revision missed this on newly-added channel/error plots; that was an agent workflow miss, not a physics choice.

Related workflow note: [log-frequency plot and GP coordinate postmortem](</Users/avoss/Downloads/bayesX/Agentic BayesX/docs/lab/log-frequency-plot-gp-postmortem.md>).

![parameter error summary](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/parameter_error_summary.png>)

## Sensitivity to Assumptions

This is a first-pass sensitivity artifact over synthetic error assumptions. It is not yet full posterior sensitivity, but it documents a miss in the prior packet: uncertainty categories were named without showing how conclusions move under different assumptions.

![sensitivity to error assumptions](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/sensitivity_assumptions/sensitivity_error_assumptions.png>)

| Item | Value |
|---|---|
| baseline | median rel error = 0.04407; max p95 rel error = 0.7849 |
| high_sensor_noise | median rel error = 0.07491; max p95 rel error = 1.048 |
| high_gp_discrepancy | median rel error = 0.1148; max p95 rel error = 1.915 |
| long_gp_correlation | median rel error = 0.05644; max p95 rel error = 0.5004 |
| low_noise_optimistic | median rel error = 0.01421; max p95 rel error = 0.2512 |

Full sensitivity note: [sensitivity assumptions](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/sensitivity_assumptions/sensitivity_assumptions.md>).

## Checker Status

| Item | Value |
|---|---|
| Canary harness | pass |
| Checker manifest mismatches before | [] |
| Checker manifest mismatches after | [] |
| Posterior recovery | True |
| Channel definitions | True |
| Tied coupling and saved errors | True |
| Key linear FRFs | True |
| Sensitivity artifact | True |
| MDOF transfer | True |

## Diagnostics

These diagnostics are for the 2DOF StatFEM workflow.

| Item | Value |
|---|---|
| MCMC acceptance rate | 0.2323 |
| Post-burn acceptance rate | 0.2033 |
| Ch2 vs Ch3 clean relative L2 | 0.567 |
| Key FRFs reported | 15 |
| Sensitivity scenarios | 5 |

![sampler diagnostics](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/sampler_diagnostics.png>)

## QOI Summary

| Item | Value |
|---|---|
| Synthetic truth | 1190 |
| Posterior mean | 1209 |
| Posterior mean bias | 18.29 (1.536%) |
| 95% interval | [1203, 1216] |
| Retained QOI samples | 240 |
| Fraction of retained samples above truth | 100% |

Concern to carry forward: the current retained QOI samples are all above the synthetic truth in this run. The full-scale response overlays look nearly identical, so the residual panel is included to make small but QOI-relevant differences visible.

![qoi uncertainty](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/qoi_uncertainty.png>)

![QOI posterior samples](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/figures/qoi_samples.png>)

## Existing Plot Artifacts

2DOF result plots:

- `artifacts/plots/nominal_2dof_frfs.png`
- `artifacts/plots/key_2dof_transfer_functions_linear.png`
- `artifacts/plots/synthetic_channels.png`
- `artifacts/plots/posterior_vs_truth.png`
- `artifacts/plots/posterior_channel_fit.png`
- `artifacts/plots/mcmc_traces.png`

2DOF machine-readable results:

- `artifacts/synthetic/twodof_dataset.json`
- `artifacts/inference/twodof_mcmc_result.json`
- `artifacts/reports/key_frf_summary.json`
- `artifacts/reports/sensitivity_assumptions/sensitivity_assumptions.json`
- `artifacts/tests/posterior_recovery_report.json`
- `artifacts/tests/channel_definitions_report.json`
- `artifacts/tests/tied_coupling_and_errors_report.json`
- `artifacts/tests/key_transfer_functions_report.json`
- `artifacts/tests/sensitivity_artifact_report.json`

Separate MDOF prototype result:

| Item | Value |
|---|---|
| MDOF transfer prototype | Separate check, not the system updated in this packet. |
| MDOF relative L2 error | 0.05142 |
| Future role | Supports later two-MDOF/FEM transfer-function workflow. |

- `artifacts/plots/mdof_frf_comparison.png`
- `artifacts/tests/mdof_transfer_report.json`

## What Changed in This Run

- Added a shareable Markdown + PNG review packet.
- Added explicit question framing and BOED boundary language.
- Defined STATFEM-style error and uncertainty terms in the packet.
- Added actual error hyperparameter values and plots of realized synthetic error versus clean truth.
- Added a first sensitivity-to-assumptions artifact for the synthetic error model.
- Tied coupling to tray properties with `k12 = k2` and `c12 = c2`.
- Switched the synthetic discrepancy GP and inference covariance from linear-Hz distance to natural-log-frequency distance.
- Set packet channel/error/GP frequency axes to log scale and documented the earlier miss.
- Corrected channel 2 and channel 3 so they are not duplicate clean forward models.
- Added a linear-unit key FRF artifact with acceleration/force and 7004C-style source/load apparent-mass curves.
- Added a channel-definition check and report-packet completeness check.

## Agentic Workflow Lesson

The first linear-unit FRF artifact mislabeled drive-point reciprocal inertance as apparent mass. The second version still blurred source and load apparent-mass constraints. Andrew caught the issue because the source and load curves in NASA-HDBK-7004C Figure 9 have different shapes: source apparent mass has a notch, while load apparent mass has a peak.

This has been documented as a workflow failure case for lab review: [apparent mass convention postmortem](</Users/avoss/Downloads/bayesX/Agentic BayesX/docs/lab/apparent-mass-convention-postmortem.md>).

Guardrail added: future structural-dynamics quantities should state numerator, denominator, coordinate, excitation, boundary condition, source/load constraint, units, expected limiting behavior, expected resonance behavior, and reference before a plot is accepted.

## Limitations

- This remains a synthetic toy model, not a validated aerospace structural dynamics model.
- Channel 2 uses the primary-side coordinate as a proxy for an interface apparent mass because the toy model has no explicit boundary/interface DOF.
- Measurement channels 1-3 still use drive-point `F/a` proxies; the key-FRF review plot now separately reports 7004C-style source and load apparent masses.
- Flight forcing remains parametric, not a nonparametric force spectrum.
- Per-channel discrepancy scaling and posterior predictive checks are still future work.
- BOED-lite experiment comparison is deferred to Milestone 3.

## Human Reflection

- What result surprised me?
- Which assumption feels most fragile?
- Is peak tray acceleration still the right QOI?
- What should be reframed before adding BOED or real data?
