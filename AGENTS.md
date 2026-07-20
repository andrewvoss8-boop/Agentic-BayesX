Build for correctness, reproducibility, traceability, and continuity.

## Communication Style
- Two audience levels (chat, reports, packets): BEGINNER-TO-INTERMEDIATE in ML/statistics (~1 yr, not expert); ADVANCED in structural dynamics (FRFs, modal analysis, FEM, damping, mode shapes, apparent mass used directly).
- For ML/stats/sampling terms: plain English; define each term/acronym/symbol (with units) on first use; don't assume the reader recalls an earlier symbol. Structural-dynamics terms need no basic gloss.
- Lead with intuition + a concrete example on the ML/stats side, then the precise detail; don't hide the simple idea behind formalism.

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

## Result Status Standard (green / yellow / red)
Report every gate AND the overall result on a three-tier light, not binary pass/fail:
- GREEN: the acceptance threshold is met; the result is trustworthy as stated.
- YELLOW: the threshold is NOT met, but the miss is understood, documented, and non-fatal — the result is usable ONLY with the stated caveat (e.g. a non-converged posterior whose held-out coverage is still informative). Yellow MUST carry its caveat and worst-case numbers; yellow is NEVER reported as success, "passing", or "green".
- RED: blocking — a missing/fabricated artifact, broken pipeline, integrity violation (e.g. inputs changed), an undocumented gate miss, or a claim stronger than the evidence. Red must be fixed or the result withdrawn.
- Overall = RED if any gate is red; else YELLOW if any gate is yellow; else GREEN. A checker / one-command replay exits non-zero ONLY on RED, so documented yellow findings do not abort replay — but the report and the human-review packet must surface every yellow prominently.
This three-tier scheme does NOT relax any gate: a non-converged sampler is YELLOW at best (a documented not-yet-converged finding) and may never be called "NUTS active" / converged / green. Yellow is an honesty tier, not a softened pass.

## NUTS/HMC Sampler Rule
- Future Bayesian updating work should use NUTS/HMC as the default sampler.
- Existing random-walk Metropolis or random-scan Metropolis results are prototype/legacy results.
- Do not claim NUTS/HMC is implemented or active unless code, one-command replay, sampler diagnostics, and checker output prove it.
- If a future task uses another sampler, say why in the task card and report.

## Convergence Gate
- "NUTS/HMC active" requires PASSING convergence diagnostics, not just that a sampler ran. Report R-hat and ESS over ALL sampled variables, including raw hierarchical latents, not only headline marginals.
- Default acceptance (state and justify any deviation): max R-hat <= 1.05 (prefer <= 1.01 where a primary source supports it), min ESS >= 200 for reported parameters (documented for nuisance latents), divergence fraction < 2%. Use >= 4 chains and a non-centered parameterization for hierarchical variance models unless justified.
- If convergence fails, do NOT report a clean "pass" or "NUTS active"; surface the worst-case R-hat/ESS next to any interval and label the intervals as not-yet-converged. On the Result Status Standard this is YELLOW at best (a documented finding), never green.

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
- Before writing or editing ANY figure of numeric data (FRF/PSD/time-history, posterior/QOI, sensitivity, diagnostics, report figures), read and apply the `tufte-data-graphics` skill at `.claude/skills/tufte-data-graphics/SKILL.md`, and run its `scripts/tufte_lint.py` on the plotting script. Write plotting code to a saved `.py` (not an inline heredoc) so it is lintable, traceable, and replayable. State any deliberate deviation from the checklist and why.
- Produce human-review artifacts that let a labmate audit the run quickly: Markdown report plus figures.
- Every figure of numeric data must state which run/dataset it came from and flag any invalidity (e.g. non-converged intervals, failed gate, stale/preliminary data) ON the figure or its caption, not only in prose — unless obviously unnecessary (e.g. a pure schematic/graphical-model diagram). For non-converged posteriors, print the worst-case R-hat/ESS on the figure next to the intervals and label them not-trustworthy.
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

### Modal / Eigenproblem Identifiability Gate
Applies to ANY task that infers element/group/material/joint parameters from modal data (eigenfrequencies, mode shapes, MAC) or uses an eigenproblem-based forward model, and to any claim that a parameter is or is not identifiable from such data.
- Compute and report the parameter->mode sensitivity that physically links each inferred parameter to the modes: the modal strain-energy fraction each calibration mode stores in each parameter group, `f_{i,g} = (phi_i^T K_g phi_i) / lambda_i` (= 2*SE/lambda for mass-normalized modes), normalized to sum to 1 over groups; report which modes drive which parameters and each parameter's typical and peak sensitivity. (For shape/MAC observations, report the analogous eigenvector sensitivity.) Do this BEFORE concluding identifiable vs not.
- For any PER-PARAMETER identifiability claim (e.g. "parameter X is/is not identifiable", as distinct from a group/aggregate claim), ALSO report the eigen-decomposition of the sensitivity Fisher information `J^T Σ^-1 J` (J = parameter->observable sensitivity Jacobian, Σ = noise+discrepancy covariance) evaluated at the REALIZED discrepancy floor (not just the measurement-noise floor): state how many parameter COMBINATIONS clear the prior precision and which raw parameters each strong/weak combination mixes. A group can store ample strain energy (be identifiable in aggregate) while its individual parameters are NOT separable — the strain-energy table certifies signal-above-floor for a group; only the FIM/eigen view (or an equivalent profile-likelihood / posterior-correlation analysis) certifies that the individual parameters separate. Run BOTH before any per-parameter identifiable/not claim; a converged-or-not sampler that goes multimodal in parameter space while agreeing in data space is the same finding and must be reported as under-identification, not a sampler bug.
- When a parameter is poorly identified, state the CAUSE with evidence and distinguish: (a) low sensitivity but IN the load path (near-rigid, or signal below the noise / model-discrepancy floor) — confirm with a finite parameter perturbation that DOES move the eigenvalues/QOI; vs (b) genuinely OUT of the load path (~zero strain energy AND a finite perturbation moves ~nothing). Never assert a parameter is "irrelevant" / "out of the load path" without BOTH the strain-energy decomposition and the finite-perturbation check.
- Compare each parameter's modal sensitivity to the inferred discrepancy/noise level: a parameter whose sensitivity sits below that floor is unidentifiable due to discrepancy/noise, not absence — say so, and give the pre-test lever (which modes/bands carry its signal, or how much discrepancy reduction would resolve it).
- This ties identifiability claims to physical mechanism and to pre-test design (cf. Fisher-information/sensitivity analyses); it is method-agnostic (applies whether or not a sampler is run).

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
- For any spectral estimate (FFT, PSD, FRF, coherence, SRS), state how window, frame length, overlap, detrending, averaging axis, and frequency-vector range/spacing affect the result, and name where the averaged independent realizations actually live (e.g., across impacts, not segments of one transient).
- If a derived quantity looks wrong (low coherence/SNR, misplaced peaks, violated limiting/resonance behavior), first rule out a poorly defined frequency vector or a window/averaging choice mismatched to the signal class before blaming the data.

### Runtime Accounting Gate
- Record `runtime.json` with `active_runtime_s` (sum of per-command execution time) and `elapsed_wallclock_s`. Cross-runner comparison uses `active_runtime_s` so human-approval wait does not distort it. `active_runtime_s <= elapsed_wallclock_s`.

## Compute
- For where to run multi-hour NUTS / TMCMC / FEM jobs (CPU+High-RAM now; Colab A100+float64 only when the method is validated AND the work is parallel-shaped; H100 reserve) and the non-negotiables for any remote/GPU run, follow `docs/compute_protocol.md`. Do NOT use T4/L4/TPU for the posterior/eigen math (float64).
- Detached-launch gate: any compute job expected to exceed the agent tool's command timeout (e.g. NUTS/TMCMC, full-order eigensolves, sensitivity sweeps) MUST be launched detached (`nohup … > logs/x.log 2>&1 & disown`) and monitored with short chained until-loops or a background watcher; never rely on the foreground tool to keep a long job alive. The tool's timeout has killed long jobs and wasted hours. Make jobs resumable (write partial results, skip finished work on relaunch) so a killed/relaunched run does not start over. Pin BLAS threads (`OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`) for small dense eigh/posterior math where multi-thread BLAS thrashes.

## Memory
- Do not rely on conversational memory across sessions.
- Record important decisions, lessons, pitfalls, and next steps in repo notes.
- Use:
  - `notes/memory.md`
  - `notes/runs.md`
  - `notes/lessons-learned.md`
  - `notes/todo.md`
  - `docs/report/project_log.md` (central reporting hub: indexed, status-tagged log of every work thread for end-of-summer reporting; update the relevant row when a thread is created/advances/closes — see `docs/report/README.md`)

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
- outputs are traceable and replayable from a single command;
- relevant references/standards were checked or explicitly ruled out;
- sensitivity to important assumptions was run or logged as a justified gap;
- the human-review packet exposes enough numerical and graphical evidence for a reviewer to find mistakes;
- if the task creates, materially advances, or closes a work thread, its row in `docs/report/project_log.md` is updated with the status copied straight from the study checker (never stronger than checker output).
