# Codex task: FRESH 2DOF STATFEM/FBS RERUN

You are in `Agentic BayesX`. Read these first:

- `AGENTS.md`
- `docs/harness/agentic-engineering-quality-gates.md`
- `docs/CODEX.md`

Do not start by copying the previous implementation path. Treat this as a fresh agentic trial of the same problem class. You may inspect existing repo artifacts after you have written your own question framing and plan.

## Original Goal To Re-Run

Start a harness-first agentic workflow for aerospace structural dynamics.

Build a simple synthetic fixed-base 2DOF StatFEM/FBS example:

- `m1` is a primary tank dome analog.
- `m2` is a secondary tray analog.
- Nominal tray natural frequency: 75 Hz.
- Nominal dome natural frequency: 110 Hz.
- Use synthetic data with observation noise and model-form discrepancy.
- Estimate/update stiffnesses, damping properties, forcing parameters, and the QOI of peak tray response during a flight-like forcing case.

Synthetic measurement classes:

1. Dome-only drive-point/modal apparent-mass-like measurement.
2. Coupled primary/interface apparent-mass-like measurement.
3. Coupled tray impact/response apparent-mass-like measurement.
4. Standalone fixed-base tray shaker-table acceleration transfer.
5. Flight-like response with unknown forcing on `m1` and tray peak response as QOI.

Longer-term context:

- Build toward MDOF/FEM transfer functions from simple FEMs and modal reduction.
- Eventually support agent-controlled autonomous experiments.
- The meta-goal is the agentic harness: correctness, reproducibility, traceability, anti-cheating, standards comparison, sensitivity, and human-review artifacts.

## Required Broad Gates

Before implementation, create a question-framing artifact that states:

- engineering decision being supported;
- objective/QOI;
- uncertainty sources;
- what BOED/optimization could choose;
- what remains human judgment;
- what would make this the wrong question.

Before plotting or fitting any named structural-dynamics quantity, write quantity contracts:

- numerator;
- denominator;
- coordinate;
- excitation;
- boundary condition;
- units;
- expected limiting behavior;
- expected resonance/antiresonance behavior;
- reference.

Before accepting outputs, identify relevant references or standards. Because NASA-HDBK-7004C and vibrationdata.com are known useful references for this problem class, compare against them unless you document why they do not apply.

## Required Artifacts

Produce a human-review packet in Markdown with PNG figures. It must include:

- question framing;
- first-pass method summary and run-specific graphical model/likelihood diagram;
- explicit inferred variables, fixed assumptions, non-inferred variables/hyperparameters, generated/observed dataset count, and whether flight-to-flight variability is modeled;
- explicit likelihood formulation, including whether it uses whole FRFs/PSDs/time histories, selected bands, or peak/feature summaries;
- assumptions ledger with actual numerical values, units, sources, and rationale;
- graphical assumptions where possible;
- model schematic and workflow diagram;
- measurement channel definitions;
- clean truth vs observed synthetic data;
- absolute injected noise/discrepancy/error;
- normalized error only as a clearly labeled diagnostic;
- GP/discrepancy sample paths and covariance definition;
- posterior fit and residual/zoom plots;
- sampler diagnostics;
- posterior/QOI samples, not only mean and interval;
- sensitivity to assumptions;
- reference/standards comparison;
- checker status;
- image-legibility QA report for generated PNGs, especially method, checker/status, table, and standards figures;
- limitations and human reflection prompts.

Frequency-domain plots should use log-scaled frequency axes unless you explicitly justify linear frequency. Magnitude scale should be linear unless dB is requested or standard for the quantity.

## Sensitivity Requirement

Run at least a first-pass sensitivity study. Prefer assumptions that could change the engineering conclusion:

- observation noise;
- model discrepancy scale/correlation;
- damping;
- boundary/coupling assumptions;
- forcing model assumptions;
- QOI definition.

Label clearly whether the sensitivity is synthetic-data sensitivity, posterior sensitivity, or decision/BOED sensitivity.

## Validation Requirement

Add checker-backed acceptance conditions for new artifacts. At minimum, check:

- required report exists;
- required figures exist;
- image-legibility report exists and passes for text-heavy figures;
- method summary and graphical model/likelihood figure exist;
- data count and flight-to-flight variability assumption are stated;
- likelihood data usage is stated as whole-data, selected-band, or peak/feature summary;
- inferred/fixed/not-inferred variables and hyperparameters are stated;
- numerical assumptions are present;
- reference/standards comparison is present;
- sensitivity artifact is present;
- channel 2 and channel 3 are not accidental duplicates;
- frequency-domain plot metadata states log x-axis or documented exception;
- QOI sample summary exists;
- checker status and limitations are included.

Do not claim improvement or correctness without checker output.

## Fresh-Agent Comparison

Only after producing your own artifacts, compare against the prior run:

- what matched;
- what differed;
- which differences are improvements;
- which differences are unresolved;
- which broad harness gates prevented mistakes.

Log the run in `notes/runs.md` and any lessons in `notes/lessons-learned.md`.
