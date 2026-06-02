Build for correctness, reproducibility, traceability, and continuity.

Claude Code is the lead agent for the first multi-agent proof of concept. Work with the human first, then use helper agents only for clear, bounded tasks. Use plain English. Do not make a result sound stronger than the files and checker output support.

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

## Engineering Checks
Before claiming a structural-dynamics, StatFEM, BOED, FEM, or autonomous-experiment task is complete, satisfy these checks.

### Priority Deliverables and Clarification
- At task start, restate the human/master's PRIORITY deliverables and acceptance criteria in your own words, and flag any ambiguous or underspecified ask.
- If a priority ask is ambiguous, ask for clarification BEFORE building. If you cannot ask mid-run, state the assumption prominently and, where cheap, produce both interpretations.
- Record a `priority_deliverables.md` listing each priority ask, its interpretation, and where it was delivered. A priority with no delivered artifact is a failure; an "assumed" interpretation without confirmation is a warning.
- The harness must NOT encode any specific problem's deliverables; those belong in the task card/runner prompt. The harness only ensures priorities are surfaced, clarified, and met.

### Question and Decision
- State the engineering decision being supported.
- State the objective function or success metric.
- State what optimization, experiment selection, or agent search is allowed to choose.
- State what remains human judgment.
- State what would make the current framing the wrong question.

### Assumptions and Uncertainty
- Create an assumptions ledger with numerical values, units, rationale, source, and sensitivity priority.
- Include actual values of noise, discrepancy, priors, hyperparameters, forcing assumptions, damping, boundary conditions, and material/model parameters.
- State the generated or observed data count: number of datasets, repeated tests/flights, and whether flight-to-flight, build-to-build, or test-to-test variability is modeled or absent.
- State inferred variables, fixed assumptions, latent variables that are not inferred, and hyperparameters that are fixed versus inferred.
- Distinguish parameter uncertainty, observation noise, model discrepancy, forcing uncertainty, aleatory variability, build/test variability, boundary-condition uncertainty, and QOI uncertainty.

### Quantity Contracts
- For every named engineering quantity, state numerator, denominator, coordinate, excitation, boundary condition, units, expected limiting behavior, expected resonance/antiresonance behavior, and reference.
- Do this before plotting, fitting, or writing a checker for that quantity.
- If two nearby conventions exist, name both and explain which one is used.

### References and Standards
- If the prompt mentions a standard, handbook, benchmark, textbook, paper, or domain site, compare against it before accepting outputs.
- If no reference is mentioned, identify likely relevant references or standards and document why they are or are not applicable.
- For aerospace structural dynamics, consider NASA handbooks, MIL/industry specs, vibrationdata.com examples, FEM/modal-analysis references, and benchmark datasets.
- Do not claim alignment with a reference without a visible comparison or documented check.

### Plots and Human Review
- Produce human-review artifacts that let a labmate audit the run quickly: Markdown report plus figures.
- Put a first-pass method summary near the start of the packet. It must show the model form, likelihood equation, data count, whole-data versus feature/peak likelihood choice, inferred variables, fixed assumptions, and non-inferred latent variables/hyperparameters.
- Include a run-specific graphical model/likelihood diagram for StatFEM, BOED, FEM-update, or autonomous-experiment workflows; do not copy a paper figure and imply it describes the current run.
- Show clean truth vs observed/simulated data when synthetic truth exists.
- Show absolute injected error/noise/discrepancy separately from normalized diagnostics.
- Label normalized plots as diagnostics and explain denominator effects.
- For frequency-domain structural dynamics plots, use log-scaled frequency axes unless the artifact explicitly justifies linear frequency.
- Avoid dB unless requested or standard for the quantity; state linear/dB scale explicitly.
- Show posterior/QOI samples and residual/zoom views when a full-scale overlay can hide meaningful differences.

### Sensitivity
- Treat sensitivity analysis as a default work product.
- Vary the assumptions most likely to change the decision or QOI, not only the easiest parameter.
- Separate synthetic-data sensitivity, posterior sensitivity, and decision/BOED sensitivity.
- Report when conclusions are fragile or dominated by model discrepancy/objective framing.

### Verification
- Add checker-backed acceptance conditions for new artifacts.
- Check for duplicate channels, wrong units, wrong axes, convention mismatches, unrealistic limiting behavior, hidden bias, missing figures, missing method summaries, missing data/replicate counts, and missing likelihood data-usage choices.
- Check whether the likelihood uses whole FRF/PSD/time-history data, selected bands, or peak/feature summaries; require the report to state the choice explicitly.
- Do not rely on visual appeal or artifact existence as verification.
- If a checker cannot encode the physics yet, document the manual review checklist and residual risk.

### Discretization Resolution
- Treat the analysis grid/resolution (frequency, time, or mesh) as a first-class documented assumption: spacing, log/linear, and a rationale tying it to the features that drive the QOI.
- Show the QOI-driving features are adequately resolved, OR justify a coarser grid INCLUDING the runtime/accuracy tradeoff (finer is not free and may be intractable).
- Provide a resolution sensitivity result (refine near the QOI-driving features; report the QOI/posterior shift) or a justified intractability note with a bounded error estimate.
- The harness does not mandate a fixed points-per-feature number; specific targets belong in the task card.

### Runtime Accounting
- Record `runtime.json` with `active_runtime_s` (sum of per-command execution time) and `elapsed_wallclock_s`. Cross-runner comparison uses `active_runtime_s` so human-approval wait does not distort it. `active_runtime_s <= elapsed_wallclock_s`.

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
- outputs are traceable and replayable from a single command;
- relevant references/standards were checked or explicitly ruled out;
- sensitivity to important assumptions was run or logged as a justified gap;
- the human-review packet exposes enough numerical and graphical evidence for a reviewer to find mistakes.
