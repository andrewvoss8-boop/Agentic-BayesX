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

## Convergence Gate
- "NUTS/HMC active" requires PASSING convergence diagnostics, not just that a sampler ran. Report R-hat and ESS over ALL sampled variables, including raw hierarchical latents, not only headline marginals.
- Default acceptance (state and justify any deviation): max R-hat <= 1.05 (prefer <= 1.01 where a primary source supports it), min ESS >= 200 for reported parameters (documented for nuisance latents), divergence fraction < 2%. Use >= 4 chains and a non-centered parameterization for hierarchical variance models unless justified.
- If convergence fails, do NOT report a clean "pass" or "NUTS active"; surface the worst-case R-hat/ESS next to any interval and label the intervals as not-yet-converged.

## Sampler Decision
- NUTS/HMC is the default. If the sampler library is unavailable, either install it in an isolated environment or use a clearly labeled alternative WITH a stated reason. Never present a non-NUTS sampler as NUTS. Honest labeling of a fallback is acceptable; misleading success framing is not.
- NUTS/HMC needs a differentiable forward model and likelihood; if features (e.g. peaks/argmax) are non-differentiable, document the smoothing/relaxation used and its effect.

## Engineering Harness Gates
Before claiming a structural-dynamics, StatFEM, BOED, FEM, or autonomous-experiment task is complete, satisfy these broadly applicable gates.

### Priority Deliverables and Clarification Gate
- At task start, restate the human/master's PRIORITY deliverables and acceptance criteria in your own words, and flag any ambiguous or underspecified ask.
- If a priority ask is ambiguous, ask for clarification BEFORE building. If you cannot ask mid-run, state the assumption prominently and, where cheap, produce both interpretations.
- Record a `priority_deliverables.md` listing each priority ask, its interpretation, and where it was delivered. A priority with no delivered artifact is a failure; an "assumed" interpretation without confirmation is a warning.
- The harness must NOT encode any specific problem's deliverables; those belong in the task card/runner prompt. The harness only ensures priorities are surfaced, clarified, and met.

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
- Plot analytic prior densities when available and, for SciML review packets, show a labeled high-sample MC prior histogram alongside them as a sampling diagnostic. Record the MC sample count/bins so jaggedness is not mistaken for prior structure.
- Distinguish prior densities from prior predictive envelopes. Predictive envelopes are finite-sample MC summaries of forward-model outputs; if quantile smoothing is used for readability, label it as display smoothing and record the sample count and smoothing parameter.
- When comparing whole-data likelihoods to peak/feature-summary likelihoods, show the side-by-side posterior and QOI consequences, including interval-width ratios and the feature/noise assumptions.
- For peak/notch feature likelihoods, benchmark observed features against predicted transfer-function features from the same forward model and report feature sensitivities; do not silently equate a peak or notch with a natural frequency.
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
- Check that feature-summary likelihood comparisons include the selected features, feature residual/noise assumptions, and posterior/QOI differences versus the whole-data likelihood.
- Check that peak/notch feature likelihoods include a feature-map or sensitivity benchmark that can expose falsely informative, redundant, or confounded features.
- Do not rely on visual appeal or artifact existence as verification.
- If a checker cannot encode the physics yet, document the manual review checklist and residual risk.

### Discretization Resolution Gate
- Treat the analysis grid/resolution (frequency, time, or mesh) as a first-class documented assumption: spacing, log/linear, and a rationale tying it to the features that drive the QOI.
- Show the QOI-driving features are adequately resolved, OR justify a coarser grid INCLUDING the runtime/accuracy tradeoff (finer is not free and may be intractable).
- Provide a resolution sensitivity result (refine near the QOI-driving features; report the QOI/posterior shift) or a justified intractability note with a bounded error estimate.
- The harness does not mandate a fixed points-per-feature number; specific targets belong in the task card.

### Runtime Accounting Gate
- Record `runtime.json` with `active_runtime_s` (sum of per-command execution time) and `elapsed_wallclock_s`. Cross-runner comparison uses `active_runtime_s` so human-approval wait does not distort it. `active_runtime_s <= elapsed_wallclock_s`.

## Memory
- Do not rely on conversational memory across sessions.
- Record important decisions, lessons, pitfalls, and next steps in repo notes.
- Use:
  - `notes/memory.md`
  - `notes/runs.md`
  - `notes/lessons-learned.md`
  - `notes/todo.md`

## Context and Compaction
- Treat the file system + git as the source of truth; the live chat is a cache that can be compacted or lost at any time.
- Any human clarification or non-obvious decision that changes an action MUST be written to a file before continuing: `decisions_log.md` in the runner workspace; the CURRENT STATE block at the top of `notes/memory.md` for the lead. Never leave it only in chat. (After a compaction, only the auto-loaded project rules file is re-injected; conversation-only instructions are otherwise lost.)
- At session start and after any compaction, run the re-grounding routine: re-read the task card, `priority_deliverables.md`, `decisions_log.md`/`notes/memory.md`, `notes/todo.md`, and the latest `notes/runs.md`; restate goal / last decision / next action / open ambiguities in one line before acting. If anything is missing or contradictory, ask the human before acting.
- Keep auto-loaded files short and high-signal (target < ~200 lines).
- If a long session is about to compact, prefer scoped compaction instructions that preserve the task card, human clarifications, open ambiguities, and sampler/convergence decisions. Prefer a fresh session re-grounded from files at phase boundaries over a heroic long session.
- Tool-specific compaction/memory mechanisms differ across Claude Code, Cursor, and Codex; verify each tool's behavior before relying on it.

## Done Criteria
A task is done only when all of the following are true:
- requested artifacts/code exist;
- required checks passed;
- assumptions and limitations are documented;
- outputs are traceable and replayable from a single command.
- relevant references/standards were checked or explicitly ruled out;
- sensitivity to important assumptions was run or logged as a justified gap;
- the human-review packet exposes enough numerical and graphical evidence for a reviewer to find mistakes.
