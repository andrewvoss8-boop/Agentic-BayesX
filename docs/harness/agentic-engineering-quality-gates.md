# Agentic Engineering Quality Gates

Purpose: make the lessons from the 2DOF StatFEM/FBS toy run broadly applicable to future structural dynamics, FEM, BOED, and autonomous experiment workflows.

These gates are not "do not repeat Andrew's last complaint." They are reusable checks for a class of engineering problems where a technically plausible artifact can still be wrong because the objective, convention, reference, uncertainty model, or review surface was underspecified.

## 1. Question-First Gate

Every run should begin with a short question-framing artifact.

Required fields:

| Field | Required content |
|---|---|
| Engineering decision | What decision would this analysis support? |
| Objective/QOI | What quantity or decision metric is being optimized, estimated, or reduced in uncertainty? |
| Decision variables | What can BOED, optimization, or the agent choose? |
| Fixed assumptions | What is not being optimized or questioned in this run? |
| Human judgment | What remains a human framing decision? |
| Wrong-question trigger | What observation would imply the current framing is not useful? |

Why: BOED and agentic search can optimize inside a frame. They do not automatically choose the right frame.

## 2. Assumptions Ledger Gate

Every technical run should include a machine-readable and human-readable assumptions ledger.

Required columns:

| Column | Meaning |
|---|---|
| Assumption | Short name |
| Value | Numerical value or categorical choice |
| Units | Physical/statistical units |
| Source | User prompt, standard, code default, paper, hand estimate, or synthetic choice |
| Rationale | Why this is reasonable for the current run |
| Sensitivity priority | High, medium, low |
| Where used | Model, inference, plotting, checker, QOI, BOED |

Minimum assumptions to expose in structural dynamics workflows:

- masses, stiffnesses, damping, natural frequencies;
- boundary conditions and coupling assumptions;
- excitation/forcing assumptions;
- observation noise values;
- model discrepancy type, scale, correlation coordinate, and correlation length;
- priors, posterior parameterization, and sampler choice;
- inference target list: inferred variables, fixed assumptions, latent variables that are not inferred, and hyperparameters that are fixed versus inferred;
- data count and variability structure: number of datasets, repeated tests/flights, build/test/flight variability modeled, and variability explicitly absent;
- likelihood data usage: whole FRF/PSD/time-history curves, selected bands, or peak/feature summaries;
- QOI definition and frequency/time grid;
- units and scaling choices;
- plot axes and magnitude conventions.

Graphical expectation: if an assumption has a shape over frequency, time, space, or mode number, show it as a plot.

Sampler default: future Bayesian updating workflows should use NUTS/HMC unless the task card documents a checked reason to use another sampler. Existing random-walk/random-scan Metropolis outputs are prototype/legacy and must be labeled that way.

## 2a. Method Summary and Likelihood Gate

Every probabilistic structural-dynamics review packet should include a first-pass method summary before detailed results.

Required fields:

| Field | Required content |
|---|---|
| Graphical model | Run-specific diagram of variables, data, forward model, noise/discrepancy, likelihood, and outputs |
| Model equation | Forward model and data-generation equation in the notation used by the run |
| Likelihood equation | Residual definition, covariance/noise/discrepancy form, and whether residuals are real, complex, log-space, time-domain, or frequency-domain |
| Data count | Number of datasets, repeated tests/flights, synthetic realizations, and whether flight-to-flight/build-to-build/test-to-test variability is modeled |
| Inferred variables | Structural, damping, forcing, discrepancy, noise, or hyperparameters inferred from data |
| Fixed assumptions | Values and conventions held fixed during inference |
| Not inferred | Latent fields, discrepancy realizations, noise scales, hyperparameters, replicate effects, or variability terms that are generated or assumed but not inferred |
| Data usage | Whole FRF/PSD/time-history likelihood, selected bands, or peak/feature-summary likelihood |
| QOI propagation | Whether QOI samples come from posterior samples, posterior predictive samples, a mean model, or a deterministic plug-in value |
| Prior visualization | Analytic prior density plus labeled high-sample MC prior histogram when available; MC sample count/bins recorded |
| Prior predictive visualization | MC sample count, raw-versus-smoothed quantile status, and smoothing parameter if display smoothing is used |
| Likelihood comparisons | If whole-data and peak/feature likelihoods are compared, selected features, feature uncertainty assumptions, and interval/QOI changes |
| Feature-map benchmark | For peak/notch features, predicted feature location/amplitude versus structural parameters and feature sensitivity/confounding diagnostics |

Why: plots of posterior fit can look persuasive while hiding the central methodological choices. A reviewer should not have to infer from code whether the workflow used the whole FRF, only a peak location, one flight, many flights, fixed discrepancy, or inferred discrepancy.

## 3. Quantity Contract Gate

Before generating a plot, checker, or inference likelihood for a named engineering quantity, write its quantity contract.

Required fields:

| Field | Question |
|---|---|
| Quantity name | What exact convention is meant? |
| Numerator | What is in the numerator? |
| Denominator | What is in the denominator? |
| Coordinate(s) | Which physical/model coordinates are used? |
| Excitation | What is the input or forcing condition? |
| Boundary condition | What is fixed, free, coupled, source-side, load-side, or base-driven? |
| Units | What are the units? |
| Frequency/time axis | Linear, log, frequency ratio, time, mode index? |
| Expected low/high limit | What limiting behavior should appear? |
| Expected resonance behavior | Peak, notch, phase roll, antiresonance, asymptote? |
| Reference | Standard, handbook, benchmark, or derivation |
| Checker | How will the workflow catch a wrong convention? |

Why: many structural dynamics words have nearby meanings: apparent mass, inertance, mobility, impedance, transmissibility, drive point, transfer, source, load, fixed base, free-free, interface.

## 4. Reference and Standards Gate

The agent must actively connect outputs to external domain references.

If the prompt names a reference:

- locate/read the relevant section or local note;
- identify what comparison the reference enables;
- document whether the current model matches the reference's boundary conditions and units;
- add a plot, table, or checker that compares expected behavior.

If the prompt does not name a reference:

- identify likely standards, handbooks, textbooks, benchmark datasets, or trusted examples;
- document which were used and which were rejected as not applicable;
- never imply that a reference applies without checking boundary conditions.

For aerospace structural dynamics, likely references include:

- NASA-HDBK-7004C for force-limited vibration and apparent mass/source-load conventions;
- vibrationdata.com examples for SDOF/2DOF/MDOF vibration checks and aerospace response examples;
- modal test/GVT benchmark datasets such as F-16 GVT data when relevant;
- FEM/modal analysis textbooks or solver documentation for matrix, mode, and FRF conventions;
- applicable MIL/NASA/industry vibration or acoustic test standards when the task resembles qualification testing.

## 5. Plot and Review Packet Gate

A human-review packet should be a first-class artifact, not an afterthought.

Minimum packet contents:

- question framing;
- first-pass method summary and graphical model/likelihood diagram;
- assumptions ledger with actual values;
- model schematic or workflow diagram;
- quantity contracts for important plots;
- clean truth vs observed/simulated data when synthetic truth exists;
- absolute injected noise/discrepancy/error;
- normalized error only as a secondary diagnostic with denominator warning;
- posterior fit and residuals;
- sampler/convergence diagnostics;
- posterior/QOI samples, not only means and intervals;
- sensitivity study;
- reference/standard comparison;
- checker status and limitations;
- human reflection prompts.
- image-legibility QA report for generated PNGs, with strict checks for text-heavy method, table, checker, and standards figures.

Plot defaults for frequency-domain structural dynamics:

- log frequency x-axis unless a linear-Hz axis is explicitly justified;
- linear magnitude unless dB is requested or standard for the quantity;
- mass/reference lines when they aid interpretation;
- vertical natural-frequency or mode markers when relevant;
- residual/zoom panels when overlays hide important differences.
- Text-heavy figures should use report-scale typography, rendered equations, and cache-busting filenames after major redesigns. A checker should reject clipped labels, overlapping text, and plain underscore/caret equation strings in review figures.

## 6. Sensitivity Gate

Sensitivity analysis is required unless explicitly scoped out.

At minimum:

- vary noise/discrepancy assumptions;
- vary key structural assumptions that influence the QOI;
- vary boundary-condition or convention assumptions when those are fragile;
- report whether the decision/QOI ranking changes.

Use clear labels:

- synthetic-data sensitivity: how generated observations change;
- posterior sensitivity: how inferred parameters/QOI change;
- decision sensitivity: how experiment/test/design recommendations change.

Do not claim BOED usefulness unless objective, simulator, uncertainty model, decision variable, and sensitivity to assumptions are all stated.

## 7. Anti-Cheating and Traceability Gate

The agent must leave enough trace for a human to audit the work.

Required:

- one command to reproduce the main outputs;
- artifact manifest with paths and key metadata;
- checker outputs on disk;
- notes entry with commands and metrics;
- checker-backed method visibility: report existence of method summary, graphical model, likelihood equation, data count, whole-data versus peak/feature likelihood choice, and inferred/fixed/not-inferred variables;
- checker-backed figure legibility: generated image QA should record resolution, font-size floor, clipped text, overlap checks, and plain-text math checks for text-heavy figures;
- checker-backed prior/likelihood comparison metadata: analytic prior density and high-sample MC prior histogram should both be shown/labeled when available, prior predictive MC sample count should be recorded, and feature-summary likelihood comparisons should report selected features, feature uncertainty assumptions, and posterior/QOI interval-width changes;
- checker-backed prior predictive display metadata: predictive envelopes should declare sample count and whether pointwise quantiles are raw or smoothed for visualization;
- checker-backed feature-map diagnostics: peak/notch likelihoods should compare observed features to predicted transfer-function features and report sensitivities that expose redundant, direct, coupled, and forcing-confounded features;
- no unstated method swaps;
- no tuning only to pass a checker;
- failed or concerning findings reported as findings, not hidden as limitations.

## 8. Rerun/Fresh-Agent Gate

When rerunning a workflow in a fresh agent:

- provide the original goal and constraints;
- provide these quality gates;
- do not provide the final code path as a recipe to copy;
- ask for independent implementation or replication;
- compare outputs against the prior run only after the new run has produced its own artifacts;
- document where the fresh agent converged, diverged, or found new issues.

This preserves the experiment: we are testing the agentic workflow, not only trying to regenerate a known plot.
