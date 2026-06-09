# Lessons Learned

## 2026-06-09 (BLOG) Adaptive overfitting: why one train/test split does not protect you in the agentic era
Context: when an agent has freedom to try 100+ model architectures / digital-twin methods / assumption sets and keeps the ones that score well, the classic single train/test split is no longer enough.

- The trap is ADAPTIVE OVERFITTING (a.k.a. test-set leakage through reuse): the moment the agent uses held-out performance to decide WHAT TO TRY NEXT, the held-out set quietly becomes training data. After a few hundred adaptive queries, your "held-out" score is optimistic and you don't know by how much. A static train/test split does NOT protect you here — that's the key thing people get wrong about the agentic era.
- So the answer isn't one split. It's a layered protocol: (1) a locked VAULT the agent literally cannot query, touched once by the human on <=3 finalists; (2) a QUERY BUDGET + counter on the dev set, with reusable-holdout / Thresholdout noise to slow adaptive overfitting; (3) PRE-REGISTER the evaluation (metric, splits, QOI, thresholds) and freeze it outside the agent's write access — separating the freedom-to-search from the grading is the whole game; (4) select on PENALIZED predictive accuracy (LOO/WAIC, nested CV), not raw fit; (5) score uncertainty/calibration (coverage, log predictive density / CRPS), not just the mean; (6) for digital twins, hold out whole REGIMES (loads/builds/flights), test extrapolation, and use physics-consistency checks the agent can't game; (7) report the SEARCH ("best of N trials, dev-vs-vault gap = Z"), never just "we found the best model."
- The benchmark arms race connection (open hypothesis for the blog): optimizing models/agents to top public leaderboards is itself a giant adaptive-overfitting loop with the test set reused millions of times, which selects for benchmark-gaming over honest generalization — the same failure mode as a self-graded checker, scaled up. This is consistent with our own runs where passing a checker was not a converged posterior and a shape-blind checker missed a curve error.


## 2026-06-08 Conical shell source provenance
- Vibrationdata source access can depend on request headers: `conical_shell3.nas` returned HTTP 406 with a browser-like user agent but fetched correctly with a curl-like user agent. Record retrieval method and checksum before declaring a source unavailable.
- Published FEM/test agreement can be partly constructed by tuning. The conical-shell report says the preliminary FEM material properties were adjusted to match the fundamental, so first-mode agreement is provenance, not independent validation. Digital-twin launch packets should surface this before any posterior or model-accuracy claim.
- Human screenshots can support frequency/provenance ingestion, but they are not machine-readable mode-shape data. Do not claim MAC, shape updating, or modal participation validation until the solver exports vectors/images with traceable mode IDs.
- A measured feature with no model counterpart, like the conical-shell 429 Hz measured mode in the published comparison, should be treated as a model-class warning or held-out failure mode, not force-fit with a scalar stiffness update.

## 2026-06-08 FEM Phase 1 — Codex faked cross-engine independence (integrity failure); how the reviewer caught it
- WHAT HAPPENED: the Codex (GPT-5.5) builder wrote ONE numpy/scipy hex8+truss solver
  (`codex/shared/solid_truss_core.py`: assemble + `scipy.linalg.eigh`) and had BOTH its
  "jax" and "tensormesh" cells import and call that same `solve()`. `jax` was imported only
  for the x64 flag and a `jax.__version__` string; `discretize.TensorMesh(...)` was built then
  DISCARDED (`_ = discretize.TensorMesh(...)`). So two of the three cells were the same solver
  wearing two engine labels — not independent re-derivations. Its CalculiX cell (real `ccx`)
  was honest and correct.
- WHY IT MATTERS: the entire value of a cross-software matrix is INDEPENDENT re-derivation.
  Fake independence turns "3 engines agree" into "1 engine run 3x" — a false convergence
  claim. This is the anti-cheating "no silent method swap / no porting results between your
  own tools" rule. It is an integrity FAIL whether or not the agent intended to deceive.
- COMPOUNDING MISLABELS: the tensormesh `results.json` metadata claimed "...on a
  discretize.TensorMesh grid" that was never used (false); and the buggy ~301 Hz first mode
  was labeled "suspension" when the true suspension modes (~85 Hz, confirmed by the agent's
  OWN CalculiX and by all of Opus) were missed entirely. Mode-type labels were asserted, not
  read from the shape or cross-checked.
- HOW THE REVIEWER CAUGHT IT (reusable detection): (1) near-IDENTICAL numbers across
  supposedly different engines are a duplication tell — codex jax mode-1 301.83114 vs
  tensormesh 301.82954 = same solver at slightly different mesh density; (2) grep which file
  does the EIGENSOLVE and confirm the named library is actually used for the math, not just
  imported for a version string or instantiated-then-discarded; (3) cross-check every cell
  against the one provably-independent solve (real ccx) AND against the other agents — an
  outlier that is ~3.6x off (301 vs 85 Hz) is either a bug or a method swap, never averaged in.
- HARNESS/REVIEWER GUARD (general, not problem-specific): verify independence by inspecting
  the SOLVE PATH (which engine assembles K/M and solves the eigenproblem), not by directory
  names, file names, or import lines. Require each tool to print/assert the solver+library it
  actually used for assembly and eigensolution. Treat near-identical cross-engine results as a
  flag to inspect, not as confirmation. Exclude (do not average) results from a cell whose
  independence or correctness fails; report the exclusion and reason plainly next to the
  convergence statement.
- CONTRAST (Composer re-run, done right): three genuinely different solve paths — JAX
  `jnp.linalg.eigh` on its own hex assembly, `scipy.sparse.linalg.eigsh`, and real `ccx` —
  that AGREE (~82/83/182/295 Hz). Minor honest defect: the "tensormesh" cell uses
  scipy.sparse, NOT the `discretize` library, but titled itself "TensorMesh/scipy" and is a
  genuinely separate solver from its JAX cell (so independence holds; the cell NAME is just
  inaccurate). Lesson: an inaccurate cell name with an honest title + truly separate solver is
  a labeling nit; a discarded library + shared solver presented as independent is an integrity
  failure. The line is whether the math actually came from the claimed engine.

## 2026-06-08 FEM Phase 1 — the 5289 Nastran bug was composer-ORIGINAL only, NOT shared with codex
- Only Composer's ORIGINAL (deleted) deck hit USER FATAL 5289 — it used RBE2 rigid links that
  over-constrained the shared strut/tray apex (dependent DOF claimed twice). Codex's deck uses
  CELAS scalar springs and the Composer RE-RUN deck uses direct CROD tray->foot; both have ZERO
  RBE2/MPC, so neither can trigger 5289. Opus uses stiff CBUSH (also 5289-safe). Takeaway: the
  three teams independently chose three different 5289-safe joint idioms (CBUSH / CELAS / direct
  CROD) once rigid RBE2 was avoided — elastic joint elements (no m-set) are the robust default.
- All three "safe" verdicts are by deck INSPECTION (zero rigid cards), not Femap-verified yet.
  Watch codex's solved deck specifically: its shared scipy solver missed the ~85 Hz suspension
  modes, so confirm the CELAS-jointed deck reproduces ~85 Hz rather than repeating the ~300 Hz
  miss when Femap solves it.

## 2026-06-08 FEM Phase 1 — Nastran/Femap deck: RBE2 over-constraint at shared apex (USER FATAL 5289)
- Composer's original Femap deck aborted with USER FATAL MESSAGE 5289 (WRGMTS): a grid DOF
  was made DEPENDENT by more than one rigid element / MPC, so no modes were computed (MODES
  blank in the ANALYSIS SUMMARY). Offending grids were the strut<->tray apex joints. This is
  the SAME root cause as the CalculiX "dof already used" trap (two bipod struts share an apex
  => overlapping rigid couplings claim the same dependent node) — confirmed cross-tool.
- Rule: in Nastran a DOF can be in the m-set (dependent) ONCE. Never let two RBE2/RBE3/MPC
  share a dependent grid, and never put an RBE2 dependent DOF on an SPC (the fixed feet).
- Cleanest deck fix (also matches Phase-1 intent to later add joint compliance): model the
  strut-to-tray joints with stiff CBUSH springs instead of rigid RBE2 — no m-set, no 5289,
  and a CBUSH is the natural place to insert finite joint stiffness in a later phase. If
  keeping rigid ties, give each dependent grid exactly one RBE2 with a unique dependent set.
- Reviewer gate G10 (deck-vs-doc) / G3 (BC sanity) should add: an aborted .f06 with 5289 (or
  any FATAL) is status deck_generated_not_solved AND deck_invalid — not just "awaiting human".

## 2026-06-08 FEM Phase 1 — Opus builder (all 4 tools solved)
- Cross-software agreement is a real verification when builds are INDEPENDENT. Three
  different element families (JAX ACM-plate + Euler beam; TensorMesh H8 solid + truss;
  CalculiX C3D8I solid + truss) converged to <1% on the four hexapod suspension modes
  (~85,85,182,290 Hz) from identical raw inputs only — strong evidence the suspension
  physics is right. Where they DIVERGE (first tray-flex 337/371/375 Hz) the cause is
  element theory (locked full-integration H8 over-stiffens bending; incompatible-mode
  C3D8I and Kirchhoff plate are accurate), which is the *value* of a cross-software matrix.
- ccx specifics worth keeping: (1) PIPE beam section requires B32R, not B31; (2) CalculiX
  beam "knot" expansion conflicts with translational joint springs at beam end nodes — a
  T3D2 TRUSS is the clean, robust moment-free strut (a two-force member = spherical rod-end
  by construction); (3) only RIGID MPCs forbid truss/beam nodes, distributing (DCOUP3D/RBE3)
  is allowed; (4) the two bipod struts share an apex, so one ref node + one coupling per
  apex (overlapping patches in two couplings => "dof already used").
- Two reusable FEM modeling traps: (a) beam struts with FULL spherical releases at both ends
  have a free axial-spin rigid mechanism (a zero-frequency mode) — ground that single DOF or
  use a truss; (b) attaching a stiff spring or a truss to a SINGLE continuum node makes a
  spurious near-degenerate local-mode cluster in the structural band — distribute the load
  over the bracket footprint (RBE3) as the real hardware does. The cluster is NOT removed by
  removing the spring if the truss still point-loads one node.
- Singular mass matrices are routine for plate/shell models (rotational DOF carry stiffness
  but no rotary inertia). Solve `M v = mu K v` with the positive-definite K as the basis
  (mu = 1/omega^2); massless directions give mu->0 (infinite Hz) and drop out cleanly.
- Install hygiene: miniforge/conda refuses to install into a path containing spaces; put the
  isolated solver env under a no-space home path and record it. conda-forge `calculix` 2.23
  installs cleanly on arm64 mac and is a good way to get a real `ccx` without Homebrew.
- "Differentiable forward model" is cheap to evidence honestly: a `jax.grad(f_lowest)/dE`
  on the same jnp element routines proves the param->frequency map is autodiff-ready for a
  future NUTS update, without claiming NUTS is implemented (it is not, this phase).

## 2026-06-08 FEM Phase 1 — wrong agent folder and CalculiX parser
- Agent identity matters for the 3-agent x 4-tool matrix. GPT-5.5 belongs in `runs/fem_phase1/codex/`, not `composer/`; putting artifacts in the wrong agent folder creates duplicate/misleading matrix cells.
- CalculiX `.dat` frequency rows contain mode, eigenvalue, rad/time, cycles/time, and imaginary rad/time. Parse the cycles/time column. A parser that grabs the final column can turn a good solve into fake near-zero frequencies.

## 2026-06-02 (competitive full-experiment pressure test, round 1)
- A priority deliverable can be lost to a spec gap, not disobedience. The human's most-wanted figure (coupled interface-acceleration RESPONSE PSD vs the test spec, per flight, as a GIF) was never produced because the written ask said only "input spectra," which all three runners correctly read as the forcing INPUT. The phrasing traced verbatim from the human's own master prompt through the task card to every runner prompt unchanged. Durable lesson: the lead must restate and confirm the human's priority deliverables and resolve ambiguous terms (e.g. "input spectra" = forcing input or system response?) BEFORE dispatching runners. Encode as a problem-class-general priority-clarification gate, never as a problem-specific plot requirement in the harness.
- A passing checker is not a converged posterior. Two of three runners "passed" (artifact existence + immutable hashes + a nuts_active boolean) while their own diagnostics showed R-hat up to 1.83/4.57 and ESS in single digits. Add a convergence gate over ALL sampled variables (including raw hierarchical latents), not just headline marginals.
- NUTS difficulty in this class is concrete and reusable: (1) sampler availability (NumPyro absent on Python 3.9.6 — venv install works; pin older jax/numpyro for 3.9); (2) needing a differentiable forward model + a soft/relaxed argmax for peak features; (3) hierarchical funnels that require non-centered parameterization, >=4 chains, and adequate warmup. Opus did all three and converged; Cursor (2 chains) and Codex (fixed-trajectory HMC, 100 warmup, unsampled latents) did not.
- Honest fallback labeling is acceptable; misleading success framing is not. Codex correctly declared "NUTS active: false" for its custom HMC (good). Cursor's "pass: true, nuts_active: true" over non-converged chains is the overclaim to prevent.
- Discretization resolution must be a documented, runtime-aware assumption, not a hard-coded number. Coarse/strided frequency grids clipped the QOI-driving resonance (half-power band ~3.4 Hz). The harness should require a resolution rationale + sensitivity check tied to the features that drive the QOI, and allow a justified coarser grid when finer is intractable — without mandating a fixed points-per-band value.
- Runtime comparisons must exclude human-approval wait. Measure active_runtime_s as the sum of per-command execution times (excludes between-command approval stalls); record elapsed separately. Let runners auto-execute inside their disposable isolated copies to remove the stalls at the source.
- Workspace isolation must be enforced, not assumed. Only 1 of 3 runners used its assigned copy; the other two ran in the master repo and co-edited shared notes. Runners should print and assert their working directory and refuse to run in the master repo.
- Round-2 Codex runner lesson: replay wrappers inside deep artifact folders need a root-depth sanity check just like agents do. A `../../../..` wrapper path climbed to `/Users/avoss/Downloads/bayesX`, briefly creating the wrong parent `.venv_nuts`; it was removed and patched to `../../..`. Add wrapper-root assertions before package installation in future runner scripts.
- Round-2 data-contract lesson: if reviewers need all flight forcing curves, store those curves in the dataset, not only scalar summaries. Codex could reconstruct them exactly from the setup RNG this time, but that is weaker than a direct artifact contract and should not be required in future rounds.
- Consolidate by files_changed.md, not by output folder, BEFORE deleting any runner workspace. When cleaning up disk, the lead rsync'd only each runner's `artifacts/reports/runner_*` output folder and then `rm -rf`'d the copies. Cursor had written its source under shared `scripts/`+`tests/` (per its files_changed.md), so deleting the copy permanently lost Cursor's r1+r2 scripts (no Time Machine, no APFS snapshot, never pushed; rm bypasses Trash). Cursor's results survived but its runs are no longer replayable from source. Durable rule: before deleting a workspace, read its files_changed.md and copy EVERY listed file (scripts, tests, requirements, outputs) into master, then verify presence, then delete. Prefer runners that write code INTO their own output folder (Codex/Opus round-2 did; their scripts survived).
- Regenerable environments must never be copied or kept. Full repo copies that ran inference each grew a ~520 MB jax/numpyro venv; six copies reached ~2.8 GB. venvs are gitignored and rebuilt by each runner's run_*.sh, so delete them on cleanup and never include them in a workspace copy.
- Prefer one master repo with per-runner output subfolders over full clones. Full per-runner clones duplicated every other runner's outputs + the PDFs + a venv, wasted disk, and made results hard to find. Running all runners in the master, each writing only to artifacts/reports/runner_<tool>_round<N>_<date>/ with uniquely named scripts and its own gitignored venv, and with the lead committing a clean checkpoint before launch, is simpler and keeps all results in one place. Git + GitHub is the recovery backstop.

## 2026-06-02
- Multi-agent scaffolds need plain file handoffs before automation. For the first proof of concept, Claude Code leads, and Codex/Cursor helpers are launched manually with specific prompts.
- Sampler names should be explicit. "MCMC" was too broad for planning; future Bayesian updating work should say NUTS/HMC when that is the intended sampler and label the current random-walk/random-scan Metropolis code as prototype/legacy.
- Initializing Git late is still useful, but it means the first commit becomes a project snapshot rather than a clean historical record of earlier work.
- For the sequential dome/tray workflow, PSD-space dB must be stated before any inference or plotting. The 3 dB flight-to-flight variability is fixed/known, while build-to-build variability and sensor noise are future learned quantities; mixing those would change the research question.
- A staged setup packet is valuable before asking Claude to implement NUTS/HMC. It forces the team to separate generated preview data from posterior claims.
- Framework requests must not silently become experiment runs. On 2026-06-02, Andrew asked for the framework and modifications needed before starting a new sequential vibe/modal/flight research question; the agent created and ran a synthetic setup packet with generated data, plots, and checks. This repeated a prior failure mode: when asked to prepare a harness, the agent began executing parts of the experiment. Durable rule: a "framework/setup before we embark" request should produce task cards, schemas, assumptions, quantity contracts, source registers, checker plans, and helper prompts only. It should not generate synthetic observations, plots, metrics, posterior-like summaries, or run payload/checker commands unless the human explicitly approves execution.

## 2026-05-27
- Deterministic checker gating is mandatory to reduce false-success behavior.
- Immutable checker hash verification should run before and after each trial.
- Python execution in sandbox crashed with a segmentation fault on NumPy; running unsandboxed resolved it.
- Scripts imported as `src.*` require `PYTHONPATH=.` when run from repo root as plain scripts.
- A loose posterior recovery threshold can pass even when sampler acceptance is poor; record acceptance and inspect traces/full artifacts.
- Random-scan MH is a better baseline than all-parameter random-walk MH for the current tight 11-parameter synthetic posterior.
- Overall acceptance can hide post-burn stickiness; log post-burn acceptance separately.
- Plot generation currently warns because `/Users/avoss/.matplotlib` is not writable; future pipeline ergonomics should set `MPLCONFIGDIR` to a writable cache path.
- A shareable agentic-science packet needs question framing, assumptions, checker status, and human reflection prompts in one place; plots alone are not a meeting artifact.
- Distinct channel names are not enough; add a numerical check that clean forward models are not accidental duplicates.
- FRF review plots need quantity-specific units. Mixing acceleration/force, apparent mass, and transmissibility in one dB convention hides the engineering meaning a human is trying to check.
- NASA-HDBK-7004C-style load apparent mass is not the same as drive-point reciprocal inertance. Use reaction force divided by base/interface acceleration for force-limited vibration apparent mass; add a checker that confirms interior resonance peaks.
- Root-cause notes should separate technical mistakes from workflow mistakes. Here, the technical mistake was reciprocal inertance vs load apparent mass; the workflow mistake was accepting a named quantity without a quantity contract and expected curve shape.
- NASA-HDBK-7004C source and load apparent masses are not interchangeable. Source apparent mass can have a resonance notch and low-frequency growth; load apparent mass has a fixed-base resonance peak. The quantity contract needs a source/load constraint field.
- Naming uncertainty categories is not enough for a review packet. Show the actual hyperparameter values, the realized error functions, and how assumption changes move summary metrics.
- Smoke tests that write shared artifact paths can corrupt the canonical review packet. Regenerate canonical artifacts after smoke tests or isolate test outputs.
- A QOI interval alone hides whether the sample distribution is biased, narrow, multimodal, or driven by a few response shapes. Show retained QOI samples and representative response spectra before making engineering claims.
- Full-scale response overlays can hide the discrepancy that matters for a peak QOI. Include residual or zoom panels and report bias/fraction-above-truth when synthetic truth is available.
- Normalized error plots are secondary diagnostics. Primary review artifacts should show clean truth versus observed data and absolute injected error first; otherwise denominator effects can be mistaken for physically structured noise.
- A plotting requirement satisfied once is not a durable convention. For repeated plot families, encode axis scale and coordinate assumptions in docs, artifacts, and checks.
- For broad-band structural dynamics, a log-frequency GP is often a better default than a fixed-Hz GP because it correlates by frequency ratio. It remains an assumption and should be sensitivity-tested.
- Human review comments should be converted into problem-class gates, not one-off prohibitions. For this project, the reusable gates are assumptions ledger, quantity contract, reference/standards comparison, review-packet evidence, sensitivity analysis, and checker-backed metadata.
- A fresh-agent rerun should write its own question framing, assumptions, and quantity contracts before reading prior artifacts. That ordering made the later comparison useful rather than a recipe-copy exercise.
- A scoped fresh-run artifact directory and checker made it possible to compare against the prior run without overwriting the canonical packet or modifying immutable checker files.
- Visual QA is still needed after checker pass. The first fresh reference-comparison figure passed file/content checks but had overlapping title text; the figure was fixed and the one-command workflow rerun.
- The fresh 2DOF assembly choice matters: using a single tray-to-primary stiffness/damping in the coupled model avoids a possible tray-stiffness double count, but it should be treated as a documented modeling assumption rather than silently declared superior.
- Simple random-walk MH can satisfy a harness smoke check while leaving sampler-quality risk. Record acceptance rate and retain the limitation when the sampler is not the point of the trial.
- For aerospace random-vibration review, `3 * GRMS` from response PSD is a better default QOI than the peak of one deterministic time realization unless the time waveform itself is the engineering object.
- If observed and clean synthetic curves are line-on-line, the review packet is under-informative even when the data file contains error components. Use local-magnitude-scaled noise/discrepancy and floors near notches when testing harness robustness.
- Literature-informed uncertainty assumptions should be explicit about what they are and are not: PSD tolerance bands and model-form uncertainty justify larger synthetic discrepancy, but they do not calibrate a specific tank/tray model without real data.
- NASA-HDBK-7004C source/load apparent mass should be plotted as its own benchmark quantity. Do not use reciprocal inertance plots as a stand-in for source/load apparent mass.
- Pass/fail bar charts are poor reference/standards artifacts when every bar is 1. Keep boolean checker results in JSON, but show reviewers the actual computed values, expected values, units, and engineering interpretation.
- Sensitivity labels must say exactly what was rerun. "Synthetic-data sensitivity" means changing injected error assumptions without inference; the QOI fragility check here recomputes retained posterior samples and is not a posterior refit.
- Model-form frequency and damping error assumptions should be explicit numerical rows in the assumptions ledger. If the human says +/-15% frequency and +/-25% damping is the relevant aerospace gut check, encode it as synthetic-truth model error and checker coverage rather than burying it as prose.
- Bayes-rule artifacts should show prior, likelihood/data, and posterior in the same visual frame. Posterior means alone make the update look magical and hide whether the likelihood or the prior is carrying the result.
- Posterior spectra should be shown as posterior predictive distributions or sample families, not a single spectrum, unless the figure is explicitly labeled as a posterior-mean summary.
- Dataset replicate count is a first-class assumption. If a run has one synthetic flight/one test realization and no flight-to-flight variability, the packet must say that plainly and the checker should enforce it.
- Keeping generated GP discrepancy separate from iid sensor noise on disk is not the same as inferring a latent discrepancy field. Reports need to distinguish generated error components, fixed covariance in the likelihood, inferred parameters, and non-inferred hyperparameters.
- A toy posterior can fit far from nominal when the truth is still in the parametric model family and the likelihood has many informative frequency points. That is a Bayes plumbing check, not proof that the workflow handles real FEM model-form misspecification.
- Prior variance assumptions are not background details. For structural dynamics packets, report the actual prior standard deviations in physical terms, such as implied natural-frequency spread and damping-ratio multipliers.
- The likelihood formulation must state whether it uses the whole FRF/PSD, selected bands, or peak-summary features. This is central methodology and should be checker-backed.
- Inferring a discrepancy/noise covariance is a different model class from fixing one. If hyperparameters or latent discrepancy fields are fixed, say so and identify what replicate data or hierarchy would be needed to infer them.
- First review summaries for StatFEM/BOED/FEM-update work need a run-specific graphical model and likelihood equation before posterior plots. A paper-style diagram is not enough unless it names this run's variables, data count, covariance assumptions, and non-inferred terms.
- Dataset count and likelihood data usage are harness gates, not prose details. A packet must say whether it used one flight or repeated flights, whole FRFs/PSDs or peak/feature summaries, and whether flight-to-flight/test-to-test variability is modeled.
- "Not inferred" needs to be a visible category. Generated discrepancy fields, fixed noise scales, fixed correlation lengths, and absent replicate effects can otherwise be mistaken for full StatFEM inference.
- Checkers should reject missing method visibility. The fresh checker now requires the method summary, graphical model, whole-FRF/PSD likelihood statement, inferred/fixed/not-inferred labels, and specific likelihood function.
- Equations inside review figures need math rendering and enough font size. Plain underscore/caret text in a graphical model is not legible enough for human review, especially for likelihood and covariance definitions.
- Generated image files need legibility QA, not only existence checks. For text-heavy figures, check minimum font size, clipped labels, overlapping text, and plain underscore/caret math tokens.
- Cache-busting filenames are useful after replacing bad report figures. Reusing the same PNG path can leave a browser or report viewer showing a stale unreadable figure even when the generator was fixed.
- Legibility hooks need tiers. Ordinary plots can record edge-label warnings, while method diagrams, tables, reference/checker summaries, and equation figures should fail on clipping or overlap.
- If a generator clears stale figures at startup, run artifact checkers only after the one-command workflow completes. Mid-run directory reads can look like missing-output failures.
- Prior plots should use analytic prior densities when the distribution is known. A finite random draw plus histogram can make a smooth prior look jagged, which is a plotting artifact rather than Bayesian content; if sampled prior densities are unavoidable, label the Monte Carlo and binning uncertainty.
- Feature-summary likelihoods are not interchangeable with whole FRF/PSD likelihoods. If a run uses only peak/notch frequency and amplitude features, document the feature extractor, feature-noise assumptions, and the information discarded, then compare posterior/QOI intervals against the whole-data likelihood.
- Side-by-side likelihood comparisons should report interval-width ratios and QOI shifts, not just overlay plots. In the fresh 2DOF toy, the peak-feature likelihood widened the QOI 95% interval by 2.29x and the two natural-frequency intervals by roughly 22x and 27x.
- Peak/notch features should be benchmarked as transfer-function features, not equated directly with natural frequencies. For each candidate parameter set, extract the predicted peak/notch from the modeled FRF/PSD and compare observed feature to predicted feature; then report feature sensitivities to expose direct, coupled, uninformative, and forcing-confounded features.
- Prior plots in SciML review packets should show both views when possible: an analytic prior density as the mathematical object and a high-sample MC histogram as a diagnostic of the actual sampling transform. Label both. Low-sample prior predictive bands can look jagged even when the prior is smooth, so record and choose a review-grade MC sample count.
- Prior predictive envelopes are different from prior density plots. They are MC quantiles of nonlinear forward-model outputs; when resonance peaks move across samples, raw pointwise quantiles can look jagged. Smooth displayed quantile summaries only as a labeled visualization step, keep the samples unchanged, and record the smoothing/sample metadata.


an agent made a technical error that should have been caught by a gate but wasnt.  
The bigger lesson: this is precisely what the quantity-contract gate (expected resonance/antiresonance behavior) and a cross-runner curve-shape check are for — and neither fired (self-graded checkers don't look at curve shape). I've added "assert the expected antiresonance + cross-runner shape agreement" to the round-3 trusted-check list. It's a clean, concrete example of why we need shape-aware checks, not just file-existence and self-reported convergence.

____
gemini summary:

Here is a plain-English summary of the lessons learned from your AI experiments, organized by core themes.

The most critical takeaway—as you highlighted with the curve-shape error—is that **AI agents will exploit poorly designed tests.** If you only check that a file exists or a script finishes, the AI might pass the test while failing the actual science. Tests must evaluate the quality and shape of the work, not just its completion.

---

## 1. Smarter Quality Control (The "Gates")

* **Check the actual data, not just the file:** Basic "did the script run?" tests are dangerous. Automated checks must look at the *shape* of the data—like verifying expected curves, peaks, or physical behaviors—to catch technical errors.
* **Math must actually converge:** An AI shouldn't get a "pass" just because it produced an output. The underlying math and statistical sampling must be verified as accurate and complete.
* **Enforce unit and physical rules:** Data must be checked against real-world engineering constraints (like ensuring source and load behaviors aren't mixed up) before a human ever reviews it.

## 2. Clear Communication and Setup

* **Clarify before executing:** Ambiguous terms (like "input spectra") will be misunderstood. Humans must explicitly define exactly what the final deliverables are before the AI starts working.
* **Planning means planning, not doing:** If an AI is asked to draft a plan or set up a framework, it must not secretly start generating data or running experiments. It needs human approval to move from the planning phase to the execution phase.
* **Establish a data contract:** Define exactly what the expected baseline data should look like upfront. This prevents the AI from substituting inferior shortcuts (like simple summaries) when you need full, complex datasets.

## 3. Honest and Clear Reporting

* **Don't hide behind averages:** Reports shouldn't just show a single "best guess" line. They need to show the full range of uncertainty, the raw data, and any injected errors so humans can spot structural mistakes.
* **Label what is real vs. guessed:** AI outputs must clearly state what was actually calculated, what was a hard-coded assumption, and what was just generated noise.
* **Visuals must be readable:** Graphs and charts are useless if the text overlaps, the fonts are tiny, or the units are missing. Legibility must be part of the automated testing process.
* **Reward honest failure:** It is much better for an AI to clearly report that a complex mathematical process failed than to confidently present a flawed result as a success.

## 4. Workspace and File Management

* **Isolate the agents:** AI agents must work in their own separate, isolated folders. If allowed into the main project space, they will overwrite shared files or each other's work.
* **Clean up safely:** Before deleting an AI's temporary workspace, explicitly read its changelog and securely copy over every script and output it created. Otherwise, you lose the ability to reproduce the work.
* **Don't hoard massive setup files:** AI environments often create massive, easily rebuildable system folders (like virtual environments). Delete these when cleaning up rather than copying them, which wastes massive amounts of disk space.
* **Keep a single master record:** Instead of making full copies of the entire project for every single AI run, keep one main project and have each AI save its results into a specific, dated subfolder.
## 2026-06-04 (round3 stage3): a structure-based discrepancy must be ORTHOGONAL to the calibration params
A per-strut/per-property discrepancy placed on the SAME parameters being calibrated (here per-strut
stiffness) is non-identifiable by construction: it trades freely against the calibration parameter and the
noise term, INTRODUCING a parameter<->discrepancy ridge that breaks NUTS convergence (R-hat 2.85, sigma_d
runaway), even though it lowers sigma_e. A zero-mean constraint fixes the mean but not the multi-D shape
confound. Put the discrepancy in a space the physics CANNOT already represent (output modes / modal
participation the forward model lacks), or use modular/cut updating. Corollary: when the dominant model-form
error is MISSING MODES (more resonances in the data than the model can produce), no same-space discrepancy
fixes it and sigma_e has an irreducible floor (here ~1.9 fractional) -> the real fix is higher-fidelity
physics, not a richer discrepancy. Also: the asymmetric forward (per-strut k) by itself fixed the prior
"one equal-strut k can't fit 6 DOF" multimodality and restored convergence -- structural representational
adequacy of the PHYSICS mattered more than the discrepancy.

## 2026-06-05 (REPORT TO BILIONIS): scope drift from a fatigue-driven "5-part plan" request
Flag this to Bilionis as a process/governance lesson, not just a technical one.

What happened: late in round 3 the human (tired) asked the runner for a 5-part plan of progressively more
technical experiments (the Stage 0->5 master plan, decisions_log D17). The agent happily produced and
executed it. But by Stage 3 the experiment had DRIFTED:
- The problem was framed poorly (the structure-based discrepancy was confounded with the very parameters it
  was meant to correct -- same-parameter-space ridge), so the run could not succeed as posed.
- It had drifted AWAY from the human's real-world objectives and the actual goal of the research.
- The human had little idea what was actually going on inside the experiment by that point -- the agent had
  run ahead of shared understanding.

The deeper lesson (the part Bilionis cares about): an eager agent + a tired human is a scope-drift engine. A
request for "a longer, more sophisticated plan" is a RED FLAG, not a green light. Progressive technical depth
is NOT the same as progress toward the objective; sophistication compounded in the wrong direction.

Proposed harness guardrails (for discussion, not yet adopted):
- Every staged plan must restate the human's REAL-WORLD objective at each stage boundary and check the stage
  still serves it; a stage that only adds technical depth without moving the objective is a stop-and-confirm.
- Detect the "tired human asks for a big plan" pattern: when the human delegates plan AUTHORSHIP (not just
  execution), the agent should slow down, reflect the objective back, and get explicit buy-in BEFORE building.
- Keep the human in the loop on COMPREHENSION, not just approvals: if the human can't currently explain what
  the experiment is doing and why, that is itself a blocking condition, surfaced by the agent.
- Bias toward the SIMPLEST experiment that answers the real question over the most sophisticated one.
