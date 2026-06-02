Build for correctness, reproducibility, traceability, and continuity.

## Rules
- Do not guess silently. State assumptions and units explicitly.
- Inspect relevant files before changing code.
- For nontrivial work, write a short plan in `notes/todo.md`.
- Prefer small, focused changes over broad refactors.
- Write artifact-backed outputs, not prose-only claims.
- Validate before claiming success.
- If blocked, report exactly what is blocked and why.
- Never report metric improvements without checker output.
- Never modify immutable checker files during a trial.
- Treat human feedback as evidence for a general harness rule, not just a local fix.
- Keep anti-cheating constraints active:
  - Do not copy reference assets and present them as generated outputs.
  - Do not fabricate plots/metrics to look successful.
  - Do not swap methods without explicit labeling.

## NUTS/HMC Sampler Rule
- Future Bayesian updating work should use NUTS/HMC as the default sampler.
- Existing random-walk Metropolis or random-scan Metropolis results are prototype/legacy results.
- Do not claim NUTS/HMC is implemented or active unless code, one-command replay, sampler diagnostics, and checker output prove it.
- If a future task uses another sampler, say why in the task card and report.

## Engineering Harness Gates
Before claiming a structural-dynamics, StatFEM, BOED, FEM, or autonomous-experiment task is complete, satisfy these broadly applicable gates.

### Question and Decision Gate
- State the engineering decision being supported.
- State the objective function or success metric.
- State what optimization/BOED/agent search is allowed to choose.
- State what remains human judgment.
- State what would make the current framing the wrong question.

### Assumptions and Uncertainty Gate
- Create an assumptions ledger with numerical values, units, rationale, source, and sensitivity priority.
- Include actual values of noise, discrepancy, priors, hyperparameters, forcing assumptions, damping, boundary conditions, and material/model parameters.
- State the generated or observed data count: number of datasets, repeated tests/flights, and whether flight-to-flight, build-to-build, or test-to-test variability is modeled or absent.
- State inferred variables, fixed assumptions, latent variables that are not inferred, and hyperparameters that are fixed versus inferred.
- When possible, show assumptions graphically, not only in prose.
- Distinguish parameter uncertainty, observation noise, model discrepancy, forcing uncertainty, aleatory variability, build/test variability, boundary-condition uncertainty, and QOI uncertainty.

### Quantity Contract Gate
- For every named engineering quantity, state numerator, denominator, coordinate, excitation, boundary condition, units, expected limiting behavior, expected resonance/antiresonance behavior, and reference.
- Do this before plotting, fitting, or writing a checker for that quantity.
- If two nearby conventions exist, name both and explain which one is used.

### Reference and Standards Gate
- If the prompt mentions a standard, handbook, benchmark, textbook, paper, or domain site, compare against it before accepting outputs.
- If no reference is mentioned, identify likely relevant references or standards and document why they are or are not applicable.
- For aerospace structural dynamics, consider NASA handbooks, MIL/industry specs, vibrationdata.com examples, FEM/modal-analysis references, and benchmark datasets.
- Compare units, axes, boundary conditions, limiting behavior, resonance behavior, and expected curve shapes against the reference.
- Do not claim alignment with a reference without a visible comparison or documented check.

### Plot and Human-Review Gate
- Produce human-review artifacts that let a labmate audit the run quickly: Markdown report plus figures.
- Put a first-pass method summary near the start of the packet. It must show the model form, likelihood equation, data count, whole-data versus feature/peak likelihood choice, inferred variables, fixed assumptions, and non-inferred latent variables/hyperparameters.
- Include a run-specific graphical model/likelihood diagram for StatFEM, BOED, FEM-update, or autonomous-experiment workflows; do not copy a paper figure and imply it describes the current run.
- Show clean truth vs observed/simulated data when synthetic truth exists.
- Show absolute injected error/noise/discrepancy separately from normalized diagnostics.
- Label normalized plots as diagnostics and explain denominator effects.
- For frequency-domain structural dynamics plots, use log-scaled frequency axes unless the artifact explicitly justifies linear frequency.
- Avoid dB unless requested or standard for the quantity; state linear/dB scale explicitly.
- Show posterior/QOI samples and residual/zoom views when a full-scale overlay can hide meaningful differences.
- Run an image-legibility QA hook for generated review figures. Text-heavy figures must have readable font sizes, no clipped labels, no overlapping text, and no plain underscore/caret equation strings masquerading as rendered math.

### Sensitivity Gate
- Treat sensitivity analysis as a default work product.
- Vary the assumptions most likely to change the decision or QOI, not only the easiest parameter.
- Separate synthetic-data sensitivity, posterior sensitivity, and decision/BOED sensitivity.
- Report when conclusions are fragile or dominated by model discrepancy/objective framing.

### Verification Gate
- Add checker-backed acceptance conditions for new artifacts.
- Check for duplicate channels, wrong units, wrong axes, convention mismatches, unrealistic limiting behavior, hidden bias, missing figures, missing method summaries, missing data/replicate counts, and missing likelihood data-usage choices.
- Check generated image legibility with an artifact-backed report; file existence is not enough when a figure is unreadable.
- Check whether the likelihood uses whole FRF/PSD/time-history data, selected bands, or peak/feature summaries; require the report to state the choice explicitly.
- Do not rely on visual appeal or artifact existence as verification.
- If a checker cannot encode the physics yet, document the manual review checklist and residual risk.

## Memory
- Do not rely on conversational memory across sessions.
- Record important decisions, lessons, pitfalls, and next steps in repo notes.
- Use:
  - `notes/memory.md`
  - `notes/runs.md`
  - `notes/lessons-learned.md`
  - `notes/todo.md`

## Done Criteria
A task is done only when all of the following are true:
- requested artifacts/code exist;
- required checks passed;
- assumptions and limitations are documented;
- outputs are traceable and replayable from a single command.
- relevant references/standards were checked or explicitly ruled out;
- sensitivity to important assumptions was run or logged as a justified gap;
- the human-review packet exposes enough numerical and graphical evidence for a reviewer to find mistakes.
