# Todo

## Active
- [ ] Keep harness checkers immutable during trials.
- [ ] Finish 2DOF synthetic channels and NUTS/HMC posterior checks.
- [ ] Add MDOF reduced-order transfer-function prototype tests.
- [ ] Inspect `/Users/avoss/Downloads/check pages.pdf` for incorrect crop seams; record PDF page numbers, visible textbook page numbers, assumptions, and validation artifacts.

## 2026-06-02 Runner Experiment Infographic
- [x] Read the competitive runner task card and prompts.
- [x] Create a plain-English infographic describing the experiment each runner is asked to run.
- [x] Add a Markdown wrapper that displays the infographic from the repo.
- [x] Validate the SVG is well-formed.

## 2026-06-02 Artist Brief For Runner Experiment Infographic
- [x] Create a plain text artist brief describing the runner experiment.
- [x] Include visual story, required labels, uncertainty conventions, and cautions about what not to imply.
- [x] Verify the brief file exists and is readable.

## 2026-06-02 Claude Opus 4.8 Full Sequential Runner (isolated copy)
- [x] Read AGENTS/CLAUDE/runner role/task card/handoff/setup packet.
- [x] Install numpyro 0.19.0 + jax 0.4.30 + matplotlib in .venv_nuts (system Py3.9.6 had none).
- [x] Verify analytic JAX-able forward model reproduces dataset clean PSD (rel err ~1e-16).
- [x] Compute fixed flight-to-flight QOI log-scatter via MC (tray~0.201, iface~0.131).
- [x] Build hierarchical NumPyro NUTS model: struct params (k1,k2,z1,z2), sigma_build, sigma_sensor, 11x2 build effects (non-centered); flight-to-flight 3 dB fixed.
- [x] Full-curve likelihood (vibe PSD + 3 modal FRF log-mag + flight QOIs) and peak-feature likelihood (soft-argmax) variants.
- [x] Diagnostics (0 divergences, R-hat<=1.002, ESS>=942, tree depth<=8, step size logged), QOI 95/99% intervals, input spectra bands.
- [x] Figures (6), packet.md, manifest, checks.json (48/48 pass), contract files. 4 checker files verified unchanged. One-command replay verified.

## 2026-06-02 Codex GPT-5.5 Full Sequential Runner
- [x] Create a scoped runner output folder and one-command script for the full sequential vibe/modal/flight experiment.
- [x] Reuse the checked setup packet conventions: PSD-space dB, dome `m1`, tray `m2`, Matérn-3/2 forcing GP, fixed 3 dB flight-to-flight forcing variability.
- [x] Implement gradient-based HMC posterior inference with transparent backend handling because NumPyro/JAX/PyMC are absent under Python 3.9.6.
- [x] Compare full FRF/PSD likelihood with peak-feature likelihood, including posterior/QOI differences and feature assumptions.
- [x] Generate the required Markdown/JSON contract, figures, diagnostics, manifest, checks, and known-failure notes.
- [x] Run syntax checks, runner artifact checks, immutable checker hash verification, and record exact command outcomes.

## 2026-06-02 Sequential Vibe/Modal/Flight Research Setup
- [x] Create a separate sequential research packet so the existing fresh 2DOF run is not overwritten.
- [x] Document PSD-space dB conventions, forcing smoothline assumptions, and what is learned versus fixed.
- [x] Add a log-log smoothline PSD generator from the four-point test spec.
- [x] Add staged synthetic data schema for dome FEM, tray vibe, dome modal, coupled modal, first flight, and ten later build/flight updates.
- [x] Add build-to-build, flight-to-flight, and sensor-noise bookkeeping, with known 3 dB flight variability and learnable build/sensor variability.
- [x] Use a Matérn covariance for sampled flight forcing functions, not an RBF covariance.
- [x] Generate first-pass plots for spec/forcing, staged observations, build effects, and flight-by-flight QOI/interface summaries.
- [x] Add a NUTS/HMC backend choice note without claiming NUTS is active.
- [x] Add and run checker-backed acceptance for the new setup.

## 2026-06-02 Plain-English Multi-Agent Scaffold
- [x] Initialize Git with a minimal cache-focused `.gitignore`.
- [x] Sync `CLAUDE.md` with the stronger engineering gates in `AGENTS.md`.
- [x] Add plain agent workflow docs, role files, Claude agents, Codex prompts, and Cursor adapters.
- [x] Add a first-loop packet skeleton and manifest for the existing fresh 2DOF workflow.
- [x] Make NUTS/HMC the documented default for future Bayesian updating, while labeling current random-walk Metropolis outputs as prototype/legacy.
- [x] Add and run a scaffold checker for required files, manifest fields, roles, commands, sources, and open risks.
- [x] Run the fresh 2DOF workflow checks and immutable checker hash check.
- [x] Log run results and any lessons in repo notes.

## 2026-06-01 Fresh 2DOF StatFEM/FBS Rerun
- [x] Read `AGENTS.md`, `docs/harness/agentic-engineering-quality-gates.md`, and `docs/CODEX.md`.
- [x] Record independent question framing and implementation plan before inspecting prior artifacts.
- [x] Write quantity contracts and assumptions ledger before generating fresh plots/fits.
- [x] Implement a scoped reproducible rerun with synthetic data, posterior samples, QOI samples, sensitivity, reference comparison, and human-review packet.
- [x] Add checker-backed acceptance conditions for the fresh rerun artifacts without modifying immutable checker files.
- [x] Run one-command workflow and checker, then compare fresh outputs against prior run.
- [x] Log run details in `notes/runs.md` and lessons in `notes/lessons-learned.md`.

## 2026-06-01 Fresh 2DOF QOI/Noise/7004C Correction
- [x] Inspect the fresh-run implementation and artifact assumptions behind the line-on-line plots.
- [x] Write a short literature/reference review for higher aerospace noise/discrepancy assumptions, PSD QOI, and NASA-HDBK-7004C apparent mass values.
- [x] Change the flight-like QOI to `3 * GRMS` from the tray response PSD.
- [x] Increase synthetic observation/discrepancy assumptions and make noise visible locally, not only relative to channel median scale.
- [x] Add NASA-HDBK-7004C source/load apparent-mass benchmark plot and report/checker coverage.
- [x] Regenerate and validate the one-command fresh workflow.
- [x] Log updated run metrics and lessons.

## 2026-06-01 Fresh 2DOF Model-Error and Sensitivity Clarity
- [x] Identify the reference-check pass-bar figure as a checker visualization, not a useful engineering plot.
- [x] Replace the pass-bar figure with a value-based reference comparison artifact.
- [x] Remove arbitrary decision-threshold language from the sensitivity section.
- [x] Add explicit model-form frequency error of +/-15% and damping error of +/-25% into the synthetic truth/assumptions.
- [x] Regenerate and validate the one-command fresh workflow.
- [x] Log updated metrics and lessons.

## 2026-06-01 Fresh 2DOF Bayes-Rule and Replicate Triage
- [x] Add graphical Bayes-rule artifact showing prior, data/conditional likelihood, and posterior for natural frequencies and damping.
- [x] Add posterior sample/95% CI plots for dome/tray natural frequencies and damping ratios.
- [x] Add prior/posterior predictive spectra against observed data, including base-driven tray and coupled tray/flight response views.
- [x] Explicitly document generated dataset counts and the absence of flight-to-flight variability.
- [x] Document how StatFEM-style discrepancy/noise is used and what is not inferred.
- [x] Add checker-backed acceptance for new Bayes/replicate artifacts.
- [x] Regenerate, validate, and log lessons for Bilionis feedback.

## 2026-06-02 Fresh 2DOF Prior/Likelihood Methodology Clarity
- [x] Make prior variance assumptions explicit in the report and machine-readable summary.
- [x] State whether the likelihood uses whole FRFs/PSDs or peak summaries.
- [x] Explain "truth inside the parametric model family" in reviewer-facing language.
- [x] Document that inferring discrepancy fields/hyperparameters is desired future StatFEM work but not implemented here.
- [x] Add checker coverage for prior/likelihood methodology text.
- [x] Regenerate, validate, and log the update.

## 2026-06-02 StatFEM Method Graphic and Harness Rule Upgrade
- [x] Add a Girolami-inspired but run-specific graphical model/likelihood figure to the fresh packet.
- [x] Make the review summary explicitly list fixed assumptions, inferred variables, non-inferred variables, data count, and whole-FRF/peak-summary choice.
- [x] Add checker coverage that the new method graphic and method summary exist.
- [x] Update reusable harness gates and launch prompt so future runs expose these choices from the first packet.
- [x] Update local technical-work/project-harness skills with the same review-summary rule.
- [x] Regenerate, validate, and log the run and lessons.

## 2026-06-02 Figure Legibility Gate
- [x] Replace the method graphic with a report-scale legible version using new cache-busting filename.
- [x] Replace the stale green/reference checker graphic with a legible value-card/table figure using new cache-busting filename.
- [x] Add an image-generation legibility hook that records resolution, font size, clipping, and overlap checks.
- [x] Make the fresh checker require the image legibility report to pass.
- [x] Regenerate, visually inspect, validate, and log the fix.

## 2026-06-02 Smooth Priors and Peak-Feature Likelihood Comparison
- [x] Replace sampled/histogram prior curves with analytic smooth prior PDFs in Bayes parameter plots.
- [x] Add a peak/feature-only likelihood variant using resonance/notch/PSD peak frequencies and amplitudes.
- [x] Run a side-by-side posterior/QOI comparison against the full FRF/PSD likelihood.
- [x] Add figures, JSON summaries, report section, checker coverage, and image legibility QA.
- [x] Regenerate, validate, and log the result.

## 2026-06-02 Peak/Notch Feature Map Benchmark
- [x] Add a deterministic benchmark showing predicted feature locations versus structural natural frequencies.
- [x] Add feature-sensitivity diagnostics for uninformative or confounded peak/notch features.
- [x] Document that the feature likelihood compares observed features to predicted transfer-function features, not directly to true natural frequencies.
- [x] Add checker coverage, regenerate, validate, and log the result.

## 2026-06-02 Prior Visualization Triage
- [x] Replace remaining low-sample prior visual summaries with analytic-prior primary curves plus high-sample MC histogram diagnostics.
- [x] Increase prior predictive Monte Carlo samples enough that bands are visually stable.
- [x] Add checker/report language that analytic and MC prior views are both shown and labeled.
- [x] Update SciML harness docs and local skills with the broadly applicable prior-visualization rule.
- [x] Regenerate, validate, visually inspect, and log the result.

## 2026-06-02 Prior Predictive Band Smoothing
- [x] Smooth displayed prior/posterior predictive quantile bands over log-frequency while labeling them as smoothed MC summaries.
- [x] Increase prior predictive MC sample count and record smoothing/sample metadata in machine-readable artifacts.
- [x] Add checker/report/docs guidance distinguishing analytic priors from prior predictive envelopes.
- [x] Regenerate, validate, visually inspect, and log the result.

## 2026-05-27 Codex Review + Sampler Fix
- [x] Read `docs/CODEX.md`, design assumptions, source, tests, and prior notes.
- [x] Run the baseline pipeline and capture checker/test output.
- [x] Review code for errors, strange assumptions, and beginner-facing gaps.
- [x] Fix sampler behavior without modifying immutable checker files.
- [x] Re-run validation and document commands, metrics, assumptions, and limitations.

## Candidate Next Work
- [ ] Separate channel 2 and channel 3 forward models so interface modal and tray impact measurements are not duplicates.
- [ ] Add per-channel noise/discrepancy scaling and posterior predictive checks.
- [ ] Add NUTS/HMC sampler diagnostics instead of relying on acceptance rate alone.
- [ ] Make the MDOF prototype explicitly fixed-base and export matrix artifacts.
- [ ] Set a writable Matplotlib cache path in the pipeline.

## 2026-05-29 Aerospace Vibration Data Search
- [x] Search vibrationdata.com for flight/modal/vibe/FRF/matrix datasets or examples.
- [x] Search NASA, data repositories, and structural dynamics benchmarks for real aerospace vibration data.
- [x] Rank candidates by direct usability for primary/secondary structure FBS/STATFEM work.
- [x] Document links, data type, access path, fit to project, and limitations.

## 2026-05-29 Milestones 1-2: Synthetic Packet + Channel Fix
- [x] Add question-first review packet with assumptions, error taxonomy, checker status, diagnostics, figures, and human reflection prompts.
- [x] Make channel 2 primary-side coupled apparent mass and channel 3 tray-side impact apparent mass.
- [x] Add non-immutable checks for report completeness and channel distinctness.
- [x] Wire new checks and report generation into `scripts/run_pipeline.sh`.
- [x] Run full pipeline and log results.

## 2026-05-29 GP Error Exploration
- [x] Inspect current synthetic GP discrepancy and inference covariance implementation.
- [x] Generate a human-reviewable GP-over-frequency error exploration artifact.
- [x] Document what is already modeled and what is still simplified.

## 2026-06-01 Linear FRF Review Artifact
- [x] Add 5+ key 2DOF transfer functions in linear units with log-scaled frequency axis.
- [x] Include acceleration/force FRFs and apparent masses in synthetic mass units.
- [x] Add a checker-backed summary so the packet reports what was generated.
- [x] Update the human-review packet and docs with the new FRF artifact.

## 2026-06-01 NASA 7004C Apparent-Mass Convention Fix
- [x] Distinguish drive-point reciprocal inertance `F/a` from 7004C-style load apparent mass.
- [x] Add base/interface reaction force over base/interface acceleration apparent masses that peak at fixed-base resonances.
- [x] Update the key-FRF checker to catch apparent-mass curves with endpoint-only maxima.
- [x] Regenerate the packet and document the convention correction.

## 2026-06-01 Apparent-Mass Mistake Postmortem
- [x] Triage the root cause as an agentic workflow failure, not only a coding bug.
- [x] Create a lab-shareable postmortem for Dr. Bilionis and the group.
- [x] Update Codex project docs and prompts with convention-check guardrails.
- [x] Log the documentation change in project memory and runs.

## 2026-06-01 Source vs Load Apparent-Mass Correction
- [x] Review NASA-HDBK-7004C impedance-method source/load definitions.
- [x] Update key FRF artifact so source apparent mass has a notch and load apparent mass has a peak.
- [x] Update checker expectations for source minima versus load maxima.
- [x] Revise lab documentation to capture the second convention correction.

## 2026-06-01 Apparent-Mass Plot Reference Lines
- [x] Add fixed-mass horizontal references for `m1`, `m2`, and `m1 + m2`.
- [x] Add vertical references for uncoupled tray and dome natural frequencies.
- [x] Record the reference lines in the key-FRF JSON summary.
- [x] Regenerate and validate the review packet.

## 2026-06-01 Coupling + Error Evidence + Sensitivity
- [x] Tie the coupling parameters to the tray stiffness/damping (`k12 = k2`, `c12 = c2`) and stop treating them as independent inference variables.
- [x] Add checker coverage that the tied coupling assumption is present in generated artifacts.
- [x] Store realized synthetic GP discrepancy and iid noise components separately from clean/observed channels.
- [x] Add packet figures/tables with actual noise/discrepancy hyperparameter values and error-vs-truth plots by channel.
- [x] Add a first sensitivity-to-assumptions artifact and document why sensitivity should be a default workflow step.
- [x] Regenerate the full pipeline and log validation output.

## 2026-06-01 GP Samples + QOI Samples
- [x] Add packet figure with example GP discrepancy sample paths and the exact covariance definition.
- [x] Store or regenerate QOI posterior samples so the packet shows more than a mean/interval.
- [x] Add packet figure with example posterior tray-response/QOI samples.
- [x] Update packet checks, docs, and run notes; regenerate and validate.

## 2026-06-01 QOI Sample Plot Triage
- [x] Remove ambiguous "spectra shown" markers from the QOI histogram.
- [x] Add residual/zoom evidence so posterior response samples are not visually hidden by line-on-line overlays.
- [x] Report QOI bias and fraction of posterior samples above truth in the packet.
- [x] Regenerate packet and validate review-packet checks.

## 2026-06-01 Error Plot Communication Fix
- [x] Make clean truth versus observed synthetic data the primary channel error plot.
- [x] Add absolute injected GP/iid/total error magnitude by frequency.
- [x] Keep normalized error only as a clearly labeled secondary diagnostic.
- [x] Update packet checks/docs and validate regenerated artifacts.

## 2026-06-01 Log Frequency GP + Plot Scale Triage
- [x] Document why the earlier agent failed to propagate the requested log frequency axis to newly added plots.
- [x] Change channel/error/GP packet figures to log-scaled frequency axes.
- [x] Move the synthetic discrepancy GP and inference covariance from linear-Hz distance to natural-log-frequency distance.
- [x] Update docs, review checks, sensitivity artifact labels, and run the full pipeline.

## 2026-06-01 Broad Harness Guardrails for Fresh Rerun
- [x] Add broadly applicable engineering-review gates to `AGENTS.md`.
- [x] Add a reusable structural-dynamics/StatFEM harness guide that generalizes lessons beyond the 2DOF toy.
- [x] Update Codex launch prompts so new agents must use assumptions ledgers, reference/spec checks, human-review packets, and sensitivity analyses.
- [x] Add a fresh 2DOF rerun prompt that preserves the original goal but starts clean.
- [x] Document the change in project memory/runs/lessons.
