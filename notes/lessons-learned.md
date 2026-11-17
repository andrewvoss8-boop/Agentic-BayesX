# Lessons Learned

## 2026-11-17 Check the cheapest data that can falsify the expensive plan first
Before downloading 0.6 GB of undocumented binary burst files, NASA's own correlation deck (already in hand) carried two decisive facts: NASA excluded the shaker runs because the attachment blocks mass-loaded the modes, and NASA's two drive-point FRFs sit 3 to 5 dB from its FEM where the project's shock-sensor curves sit at 10 dB. The 71 MB of NASA comparison plots can decide the larger question with a frozen, pre-registered digitisation before any raw file is parsed. Also: a dry run on synthetic data caught a content-dependent QA rule (peak near 54.19 Hz) that would have silently excluded node-line responses; fix QA rules before the deciding data are seen.

## 2026-07-20 Gross classification can hide failure on the engineering decision pair (MPL)
The existing response-only MPL records classified six deliberately broad model variants well (balanced recovery
0.814 acoustic and 0.947 tap features), yet they could not separate the decision-relevant untouched B0 model from
the human D43 B2 model at the frozen 2x-uncertainty threshold (0.270x and 1.521x). Pairwise coverage also failed
(0.333 and 0.600 versus 0.80 required). A high multiclass headline can be carried by easy, physically extreme
variants while the models one actually needs to choose between remain indistinguishable. Observable-admission
gates must therefore require both the named decision contrast and broad pairwise separation. For sequential
single-accelerometer data without measured input, more flexible likelihoods do not repair the experiment; the
minimum lever is synchronized force, simultaneous fixed-reference responses, independent re-mounts, and force-level repeats.

## 2026-06-22 Audit the raw delivery before declaring a data/model ceiling (ShockSat)
The 4-card ShockSat amplitude twin (statfem_real_validation / fem_remesh / richmodel_L5 / modelclass_L5) was
reported as hitting an *intrinsic* limit ("single impact / NOT a data-quantity gap"). A raw-delivery audit
overturned that. The PUBLIC NASA ShockSat1 release (`shocksat_statfem_runner_20260609/source_manifest.md`)
contains multiple modal-hammer DRIVE DIRECTIONS (+X/+Y/+Z/+XY: Test01–Test10), a force-level parametric sweep,
and pyro/frangible sources — multi-direction excitation is exactly the lever that separates participation from
damping. The runner had downloaded only ONE zip (Test07 +X); the rest were marked `too_large_deferred` and never
fetched (pyro only partial → truncated). The "ceiling" was a data-USAGE / download choice, not data availability.
- LESSON 1: "single impact / not a data gap" was a USAGE statement masquerading as an AVAILABILITY one. Before
  claiming any data or model ceiling, enumerate the FULL delivery manifest, mark downloaded-vs-deferred, and
  distinguish RAW multi-drive FRFs from modal-DISTILLED modes (we held the multi-reference data only as 33 `.ash`
  modes, which by construction give shape+frequency, not per-channel amplitude — so of course they didn't fix it).
- LESSON 2: this is lesson #6 below biting us — that entry ALREADY said "the cure is multi-reference / roving
  excitation, not a fancier model." The cure was sitting in the manifest, deferred. When the method names the data
  lever, CHECK whether that data is already in the delivery before concluding "intrinsic."
- LESSON 3: verify the raw inventory from files, not memory — a packet mis-stated it ("only hit-001 exists; others
  3-channel"); in fact 4 full 128-channel runs exist (distinct CRCs, same +X drive = repeats).
- LESSON 4 (carry to the parallel MPL twin thread): it reached the same "per-location amplitude ceiling" under a
  no-force / single-excitation assumption — re-audit its delivery/observable before accepting that ceiling.

## 2026-06-13 Schneider × Das/Debnath × Yan(2026) × StatFEM program (workspace papers_statfem_studies_20260612)
1. **Cheap probes mislead in BOTH directions — only the full multi-chain gate decides.** Study G's 2-chain probe
   "converged and was wrong" (false positive: a single basin hid the bimodality). Study K's 2-chain probe "failed and
   was wrong" (false negative: under-warmed R-hat 3.7, 0/5 — the 4-chain run reversed it to R-hat 1.007, 5/5). I wrote
   a (wrong) decision off the K probe and had to correct it (D33→D34). NEVER promote or kill a result on a probe; the
   4-chain all-variable gate (R-hat≤1.05, ESS≥200, div<2%) is the only arbiter. This cost real rework — budget for it.
2. **Kennedy–O'Hagan physics-vs-discrepancy confounding appears in dynamics as literal posterior BIMODALITY.** When a
   flexible output-space discrepancy can mimic the physics, the posterior splits ("damped structure" vs "undamped
   structure + large model error"). A single chain lands in one basin and looks healthy; only multi-chain all-variable
   diagnostics reveal it (R-hat 50). Constraining the discrepancy (orthogonal projection / local damping) cures the
   bimodality — but does NOT restore held-out coverage: identifiability and local-model-error under-coverage are
   SEPARATE failures with separate cures. Don't assume one fix buys the other.
3. **Convergence ≠ trust; the held-out gate is the only instrument that catches a confidently-wrong twin.** A cleanly
   converged single basin over-predicted never-measured-point peaks ~2×; the deterministic FEM failed the same test.
   Hold back sensors you have, predict them, check the bands — on data you already have. This is the anti-pencil-whipping
   procedure to put in front of skeptical loads/dynamics groups.
4. **Exact log-magnitude/wrapped-phase FRF likelihoods freeze HMC.** Phase-wrap cliffs and 1/|H| spikes give NaN
   gradients. The smooth small-error-equivalent residual r=(data−H)/(|H|+κ) restores NUTS and handles real noise floors
   without data selection — plausibly why Schneider needed gradient-free Subset Simulation. (Documented as a 12-rung
   "how to make NUTS work on dense FRFs" pathology ladder, D14–D25.)
5. **Latent (data-space) mode shapes do not generalize spatially.** Free latent shapes (Das/Debnath-style) have no data
   at held-out points → ~1e7× error, R-hat 364. For held-out PREDICTION, shapes must come from the parametric physics
   (a differentiable B×B eigh); loosen only eigenvalues/damping.
6. **Real-data identifiability boundary, stated as a budget decision (Study K→L).** Per-mode FREQUENCY is identifiable
   (each sharp peak pins one number) → 5/5 held-out coverage by correcting a ~15% FEA error. Per-mode AMPLITUDE is NOT
   identifiable from a single excitation reference (confounded with damping + global level; R-hat 14.8). So when bands
   are calibrated-but-wide, the cure is MORE DATA (multi-reference / roving excitation), not a fancier model. The method
   tells you which lever actually moves — the concrete "where to spend the next test dollar" answer.
7. **A deterministic reconstruction fed back as "ground truth" double-counts (the sensor-fault / Yan-2026 trap).**
   Reconstructing masked channels and then using them as if measured in closed-loop updating treats reconstruction error
   as exact → overconfidence (Brynjarsdottir–O'Hagan). A calibrated predictive BAND on the reconstruction is the honest
   alternative; it also wins where it matters (high-freq local modes, where spatial interpolation aliases).

## 2026-06-09 (BLOG) Global lessons for autonomous SciML (distilled from the modeling-freedom experiment)
The two plain-English write-ups below (same date) tell the story; this is the distilled list. Strategic
versions for our own priorities are in project_vision.md S13b.
1. **One run, one question.** Each experiment gets ONE falsifiable question and ONE success criterion.
   Do not ask a single run/agent to do two jobs at once (e.g. demonstrate a method AND make science
   progress) — you get a weak version of both. That is exactly how the ShockSat half came out hollow.
2. **Validity before rigor — check the experiment CAN answer the question before running it.** It needs
   real choices to make (knobs / competing models) AND a hidden answer that can actually tell good models
   from bad. Ceremony (rules, seals, hashes, scoring) is not validity. Front-load this cheap check;
   back-load the expensive sealing. A 30-min "does this have knobs + a discriminating held-out?" trial
   would have killed the bad ShockSat setup before any vault work.
3. **A pre-committed hidden answer key is the decisive anti-cheating test.** The "is the math stable?"
   check (convergence gate) is necessary but not sufficient — it caught the wild score-chasers, but a
   different, cleanly-converged flexible model STILL over-tuned and only the hidden vault caught it. Hide
   the truth from EVERYTHING the agent can read, including the generator that made the data.
4. **Honest "I couldn't do this" is the load-bearing safety property** — worth more than any single
   checker. The run stayed truthful only because the worker refused to fake a posterior and labeled its
   shock prediction low-confidence. That honesty is what made the hollow problem visible instead of hidden.
   Reward honest failure; treat confident fabrication as the cardinal sin.
5. **Real data is not automatically more valuable — match the data to the question TYPE.** Known-truth
   synthetic is right for validating a METHOD/detector; real data is required for a SCIENCE claim and
   nearly useless for validating a detector if it lacks the structure the method needs.
6. **Out-of-distribution is a different question from overfitting.** Holding out the pyro shock answered
   "does the modal twin extrapolate to new physics?" (no), NOT "did it overfit?". Don't conflate them.
7. **The orchestrator/lead is now the weak link, not the worker.** The runner executed well; every real
   failure (hollow setup, the truth leak) was in the lead's framing. As workers get more capable, risk
   moves UP to problem-design — spend effort there and treat orchestration mistakes as first-class.
Blog through-line: we set out to test whether an AI overfits, and the deepest lesson was about us — a
rigorous-LOOKING experiment can be empty, and in the agentic era the human's judgment about what makes a
VALID test is the thing that has to scale.


## 2026-06-09 (BLOG) Adaptive overfitting: why one train/test split does not protect you in the agentic era
Context: when an agent has freedom to try 100+ model architectures / digital-twin methods / assumption sets and keeps the ones that score well, the classic single train/test split is no longer enough.

- The trap is ADAPTIVE OVERFITTING (a.k.a. test-set leakage through reuse): the moment the agent uses held-out performance to decide WHAT TO TRY NEXT, the held-out set quietly becomes training data. After a few hundred adaptive queries, your "held-out" score is optimistic and you don't know by how much. A static train/test split does NOT protect you here — that's the key thing people get wrong about the agentic era.
- So the answer isn't one split. It's a layered protocol: (1) a locked VAULT the agent literally cannot query, touched once by the human on <=3 finalists; (2) a QUERY BUDGET + counter on the dev set, with reusable-holdout / Thresholdout noise to slow adaptive overfitting; (3) PRE-REGISTER the evaluation (metric, splits, QOI, thresholds) and freeze it outside the agent's write access — separating the freedom-to-search from the grading is the whole game; (4) select on PENALIZED predictive accuracy (LOO/WAIC, nested CV), not raw fit; (5) score uncertainty/calibration (coverage, log predictive density / CRPS), not just the mean; (6) for digital twins, hold out whole REGIMES (loads/builds/flights), test extrapolation, and use physics-consistency checks the agent can't game; (7) report the SEARCH ("best of N trials, dev-vs-vault gap = Z"), never just "we found the best model."
- The benchmark arms race connection (open hypothesis for the blog): optimizing models/agents to top public leaderboards is itself a giant adaptive-overfitting loop with the test set reused millions of times, which selects for benchmark-gaming over honest generalization — the same failure mode as a self-graded checker, scaled up. This is consistent with our own runs where passing a checker was not a converged posterior and a shape-blind checker missed a curve error.


## 2026-06-09 (BLOG) The agent sealing the vault can leak the answer — scan the generator, not just the inputs
Context: while setting up a held-out vault for the anti-overfitting experiment, the lead agent
generated the synthetic ground truth, sealed the truth values to the vault, uploaded them off-machine,
and deleted them locally — textbook. Then a leak scan of the whole runner-visible tree caught that the
DATA GENERATOR script itself still hard-coded the answer in plaintext (the true parameters and the hidden
model-form-error location). That script was readable by the runner, so the carefully-hidden vault was
worthless: a runner reading the generator would see the truth directly.

- Durable lesson: the threat model for a held-out vault includes the TOOLING THAT CREATES IT, not only the
  data files handed to the model. Hiding `truth.json` does nothing if `generate_truth.py` next to it still
  contains `THETA_TRUE = [...]`. Off-machine deletion of the data is necessary but not sufficient.
- The catch came from grepping the ENTIRE runner-visible tree for the literal truth VALUES (and the secret
  location of the injected model-form error), not from checking that the input arrays looked clean. A
  file-existence / "inputs don't contain truth" check would have passed while the answer sat in a comment
  two files over.
- Fix pattern: redact truth values AND the location/identity of any injected discrepancy from the committed
  generator; keep them only in the sealed vault; make the committed generator NON-reproducing by design
  (it must require restoring the sealed seed/params to regenerate). Distinguish PUBLIC config the searcher
  may know (model form, noise levels, what it will be graded on — that is legitimate pre-registration) from
  SECRET truth it must infer (parameter values, the hidden error's location, the seed, the held-out targets).
- Generalize to a checker gate: before sealing any blind/held-out split, scan generators, configs, logs, and
  notes — everything the searcher can read — for the truth values and the injected-error identity, not just
  the observation files. Pairs with the existing rule that a self-graded/file-existence checker is not a
  validation: here, "the inputs are clean" is not "the answer is hidden."

## 2026-06-09 (BLOG) Why one of our two test problems taught us nothing — in plain English
We ran one experiment two ways: a made-up practice problem where we secretly knew the right answer,
and a real NASA shock-test problem. The made-up one worked great. The real one taught us nothing.
Here is why, without jargon.

An experiment that asks "does the AI cheat by over-tuning the model to look good?" only works if the
problem you hand it has three things:
1. REAL CHOICES TO MAKE. There have to be knobs the AI can turn and several candidate models it can
   pick between. Our real-data problem had none — it was just "measure how well one fixed model already
   matches the measurements." With nothing to adjust, there is nothing to over-tune and nothing to
   choose, so the AI correctly did it in a single pass and the "experiment" was empty.
2. A HIDDEN ANSWER OF THE SAME KIND IT PRACTICED ON. To fairly compare "the score the AI could see"
   against "the truth we hid," the hidden thing has to be the same sort of measurement. We hid a
   completely different kind of event (a pyrotechnic shock, in a frequency range and physics the
   practice data never touched). The model literally could not predict it, so hiding it told us nothing
   about over-tuning — only "the model doesn't work far outside what it was built for," which we already
   knew.
3. IDEALLY, A KNOWN TRUE ANSWER, so you can check whether the AI's self-grade matched reality. You get
   that on a made-up problem; you don't on real data.

The trap: our setup LOOKED airtight — rules, scoring, a locked-away answer, cryptographic seals — and
was still empty, because behind all that ceremony the real-data problem had no knobs to turn. Looking
rigorous is not the same as being a real test.

The deeper mistake was trying to do two jobs with one setup: run a clean experiment AND make progress on
the real engineering. We got a weak version of both. Pick one job per setup.

The bright spot: the AI doing the work did not fake it. It said plainly "I can't really calibrate
anything here" and "my shock prediction is a low-confidence guess." That honesty is what made the empty
problem visible instead of hidden — reward an honest "I couldn't do this" over confident nonsense.

The fix: before you commit to a test problem, actually try a quick version of the experiment on it
first. Confirm there are real choices to make and that the hidden answer can actually tell good models
from bad ones. "The data exists and loads" is not "this problem can answer my question."

## 2026-06-09 (BLOG) What DID work: a hidden answer key caught cheating that the quality-check missed
On the made-up problem (where we knew the truth), the experiment paid off, and the plain-English takeaway
is worth keeping: the model that looked best on the score the AI was allowed to watch was NOT the best
model when we checked it against the hidden true answer. The flashy, flexible model topped the visible
scoreboard but lost to the plainest model on the prediction we had hidden away — the classic sign that
the visible score was a leaky proxy you can game.

Two different safety nets caught two different kinds of cheating:
- The "is the math even stable?" check (convergence gate) caught the wild configs that chased the visible
  score by letting the model run loose — those blew up and were thrown out automatically.
- But the most important catch was the hidden answer key (the vault): one flexible model passed every
  stability check cleanly and STILL turned out to have over-tuned — its extra knobs improved the visible
  score without improving the hidden prediction. No stability check can see that. Only comparing against
  an answer you locked away in advance can.
Durable line for the harness: a clean "the math converged" is necessary but not enough; an honestly
hidden answer key is the decisive test of whether a good-looking model actually generalizes.

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

## 2026-06-11 (coupled-QOI overnight, BLOG): group-level identifiability gates do not certify parameter-level recovery — and more compute finds more modes
Workspace `artifacts/reports/shocksat_tray_coupled_qoi_20260610/` (packet §10, D10/D11). A
strain-energy identifiability gate said the payload-mount stiffness is identifiable from
mounted-config modal data (dlnf/dlnk = 0.449 ≈ 10× the discrepancy floor). An overnight
synthetic-truth NUTS calibration then FAILED its convergence gate (R-hat 5–10, ESS 2, 0
divergences) — and the diagnosis upgraded the lesson rather than the claim:
- **"Identifiable overall" ≠ "identifiable per-axis."** The SE gate certifies signal-above-floor
  for a parameter GROUP; only a FIM eigen-decomposition of the sensitivity Jacobian predicts how
  the posterior splits across the individual parameters (here: 2 of 6 mount-stiffness
  combinations identifiable; the k_tx/k_ty/k_rx splits prior-dominated). Run BOTH before
  sampling; the gate text in AGENTS.md asks for the SE table — consider whether the combination
  (eigen) view should be required too.
- **Model-form discrepancy is the binding constraint, proven in a controlled synthetic.** The
  sampler honestly inflated σ_f to ~3.7 % (injected noise was 0.3 %) to absorb a deliberately
  unrepresentable truth feature (off-diagonal mount coupling). At 3.7 %: 2/6 combos; at 0.3 %:
  5/6. Same wall as the real-data predecessor (σ_f = 4.6 %, joints) — the program has now hit it
  with real data AND with synthetic truth.
- **Auto-remedy by escalation backfired diagnostically as expected**: 4× the draws at depth 9
  made worst R-hat WORSE (5.03 → 9.74) because longer chains FOUND MORE MODES. On a multimodal
  posterior, compute escalation is exploration, not convergence; treat rising R-hat under more
  compute as multimodality evidence, not as "needs more warmup".
- **Data-space vs parameter-space convergence is the cheap one-shot diagnostic**: chains agreed
  on predicted frequencies to 0.06 % while disagreeing wildly in parameters — computing that
  spread took one forward eval per chain and settled "bug vs physics" immediately.
- **Design experiments so the negative is informative.** The truth deliberately contained a
  feature the model family cannot represent; when recovery failed, the failure LOCALIZED the
  needed fix (symmetry-breaking observables: mode shapes / FRF amplitudes / interface force
  gauges — not more frequencies). The honest negative is the deliverable.

## 2026-06-11 — MPL stand rebuild (FABLE)
- **The free-free 6-RBM gate catches real element-formulation bugs.** An absolute diagonal drilling spring (the lazy K6ROT stand-in) silently stiffened rotation-about-panel-normal at frame-coupled shell nodes: 5 rigid modes, one corrupted to 2.66 Hz. The fix is the textbook relative penalty (drilling DOF tied to membrane in-plane rotation). Without the gate this would have polluted every mode table at the few-Hz level.
- **Validate the TEST, not just the element.** Two initial validation FAILs were test bugs (off-by-one tip-node index; narrow-strip E vs E/(1−ν²) reference ambiguity) while the element was exact. Lesson: when a nodally-exact element misses by 15-30%, suspect the harness first; use ν=0 to make plate references unambiguous.
- **Parse before trusting card context.** The card's "shield = PSHELL39 t=0.5 suspect" premise was a misidentification (thrust plate); the real shield wasn't in the deck at all. A 20-line geometry exploration (which grids take the FORCEs, what plane they live in) overturned the task's #1-knob framing — and the human (live) resolved the fork in minutes. Escalate premise breaks immediately; don't build on them.

## 2026-06-11 — MPL rebuild rev 4: priors + prior-predictive (the honest-observable trap)
- When a human gives a RANGE ("2-4 lb"), encode it as a prior immediately and FORWARD-propagate it (prior-predictive) even in a no-sampler task — it costs little and exposes identifiability before testing. Bridge artifact to the posterior-update card.
- Don't manufacture a tidy f(mass) law through a crowded/veering band. The first attempt (max-participation mode) jumped branches (peak mode 29→74→45 Hz) and gave a fit with 1.8-2.2 Hz residuals and even non-physical slope. The honest fix: propagate through the FUNDAMENTAL f1 (monotone in added mass by eigenvalue interlacing) AND state plainly that the box energy is smeared across a veering cluster, so the parameter is only weakly/confoundedly observable. The "ugly" answer (weak, confounded observability) was the real finding — exactly the pre-test insight the robust-twin demo exists to produce.

## 2026-07-08 (true remodel loop): two generic evaluation traps + the survey-fit disconnect
- **Reduced-basis score inflation is real and family-wide:** ANY model evaluated at θ_MAP in a θ=1 eigenbasis
  carries ~0.7-2.2% frequency bias that INFLATES held-out FRF correlation by +0.01-0.07 — enough to fake a
  pre-registered win. Even the baseline fails its own 0.3% spot check. Rule: every decision-relevant score
  (freeze set, bars) must be exact-basis (one full solve at θ_MAP, union-POD enrichment, validate <=0.3%).
- **θ_MAP multimodality is a silent ranking lottery:** identical model classes land in different posterior
  basins (single-start L-BFGS) with ±0.035 held-out P1 differences. Rule: deterministic multi-start MAP for
  anything that feeds a selection decision; the near-duplicate-candidate cross-check (same edit, two tracks)
  is what exposed it.
- **Better modal-frequency fit predicted WORSE held-out FRF at every accuracy step, dev through vault** —
  the strongest evidence yet that the .ash-frequency objective does not transfer to per-channel FRF
  amplitude; treat any freq-likelihood "improvement" claim with this disconnect in mind.

## From the full-spectrum study review (2026-07-16, D17)
- **Checkers must validate finiteness and identity, not presence.** G09 accepted NaN S1/S2 statistics,
  null SEs, and an F row that silently equaled the random control. Every numeric gate should assert
  isfinite() and every pre-registered rule (like arm-F's combination rule) should be checked as an
  identity, not assumed.
- **Never reuse one fold's fitted object across folds, even as a labeled "representative" shortcut** —
  fold-1's shape MAP applied to folds 2-4 leaked their held-out drives. A caveat label does not remove
  leakage; if the honest computation is too expensive, report NO number.
- **A local FIM cannot prove global identifiability.** Separated posterior modes agreeing in data space IS
  under-identification per AGENTS; say "locally stiff, globally unresolved" and stop there.
- **Validation-by-reproduction must be independent.** Same hits + same distiller ⇒ bit-identical caches by
  construction; that closes provenance, not processing correctness.
- **Size ARPACK ncv to RAM before launching** (k=650/ncv=1301 thrashed 16 GB for 2 h); and check the
  spectrum edge for clamped/unconverged modes — 345 of 560 "modes" were numerical pile-up at one frequency.
- **An adversarial cross-model review caught all of this in one pass** — cheap relative to the study;
  make it standard for any study whose headline flips on a methodological subtlety.

## 2026-07-16 — Validated net-CG QOI port (card B): four transferable lessons

**1. "We can't reproduce the reference" is a CONTRACT bug until proven otherwise — not a calibration bug.**
The full-spectrum study could not reproduce the delivered net-CG twin (got 8.2×/3.7×/5.1× vs 1.51×/2.30×/
2.53×) and attributed it in writing to "a marginal-calibration difference in the reimplemented statFEM F(k)",
then closed S3/S4 as unassessable. The actual cause was a **redefined headline statistic**: netcg's width
ratio is `grms(hi−lo)/grms(FEM+6dB width)`; the study's was `grms(smooth hi)/grms(smooth lo)` — an
upper/lower ENVELOPE ratio that never references the denominator. On identical arrays: **1.508 vs 21.660**.
Findable in a ~3-line diff. The study reused netcg's grid and helpers (so it *felt* like reuse) while
silently redefining the number those helpers fed. **Rule of thumb: when a port misses a reference by >2×,
diff the STATISTIC's definition before touching any constant.** The Quantity Contract Gate exists for this;
it must be applied to the *scored statistic*, not only to the physical quantity.

**2. Reuse means IMPORT + a proven reduction, not "same conventions".** The fix that made N0 pass exactly
(|err| 0.0000) was importing the delivered machinery read-only and injecting new behaviour through subclass
hooks that **provably reduce to the parent** (asserted numerically at runtime: max |Δufrac| = 5.6e-16 before
any number was produced). Generalise by algebraic identity — e.g. netcg's `marg = 0.25 + (SD_A_U−0.25)·ufrac`
IS the contribution-weighted form for a specific tier vector, so a general per-mode vector enters through an
*effective ufrac* with `ensemble()` untouched. A reimplementation that "follows the same conventions" has no
such proof and drifts silently.

**3. Per-mode modal quantities are NOT comparable across re-solved bases when modes are near-degenerate.**
My own pre-registered mapping defined `a_i = |g_X,i|/|g_A0,i|` (per-mode tray participation ratio). It is
invalid here: **18 of 44 adjacent in-band mode pairs sit within 1%** (a five-mode cluster at ~141 Hz), and
inside a near-degenerate subspace the eigenvectors are arbitrary up to rotation — only the **subspace** (and
the summed spectral response) is basis-invariant. Symptom: **median |ln a| = 2.31** (a 10× "change") from a
modest stiffness edit, with a 7e4 |g| dynamic range detonating near-zero denominators. **Cluster-aggregate
(`sqrt(Σ|g_X|²/Σ|g_A0|²)`) or MAC-on-a-common-DOF-space, never raw per-mode ratios.** Generalises to any
mode-matching/MAC/participation comparison across two FEM variants with dense modal regions.

**4. A "baseline reproduces" check can be an identity BY CONSTRUCTION — say so.** The card required
"baseline-through-your-mapping must reproduce N0 ±0.05". My relative mapping gives δf≡1, a≡1 at the
baseline, so it reproduces N0 *exactly and vacuously*. It proves the plumbing, not transport fidelity. I
added a **non-inertness gate** (does any finalist actually move the band?) to stop an "S3 not met" from being
an artifact of dead plumbing. **Pattern: whenever a validation passes at |err| = 0.0000, ask whether it CAN
fail.** If it can't, it isn't a test — name it and add one that can.

**5. (Checker design, for the next card — durable-rule candidate, NOT yet applied; needs Andrew's approval.)**
My checker returned **OVERALL GREEN 10/10 while S3 and S4 were both YELLOW**, because its gates cover
*process integrity* and nothing propagates the pre-registered success criteria into OVERALL. That is the same
CLASS of defect the review caught in the study (C8: G09 validated key-presence, not finiteness). It
under-specifies rather than certifies a falsehood, and both YELLOWs are legitimate pre-registered outcomes a
checker arguably should not call RED — but "OVERALL GREEN" next to two unmet criteria is a real misreading
hazard. I disclosed it in every report rather than edit a SHA-locked checker mid-trial. **Proposed rule: any
checker that pre-registers success criteria must carry a gate that reads its own verdicts file and reflects
each criterion's status into OVERALL, so the headline light can never read greener than the science.**

**6. An honest falsification is a RESULT, and pre-registering its path is what makes it credible.** S4 failed
because the ONE measured extended-band cluster mode's OBSERVED cross-drive amplitude scatter (1.393) is
LARGER than the 0.80 the twin already assumed for an *unmeasured* mode — measuring it made it MORE uncertain
and the band WIDENED. That is only reportable as a clean finding because the study's A5b ledger entry wrote
the falsification path down on 07-14 *before any QOI computation*: "if the observed cross-drive amplitude
scatter is large, SD_A stays large and the normal band will NOT narrow". Pre-registration turned what would
otherwise look like a broken update into evidence. Also: measuring a mode's FREQUENCY does not reduce its
AMPLITUDE/SHAPE uncertainty — with 1 Z sensor the drumhead participation stays unknown, so the lever is
SENSORS, not modelling.

---

## 2026-07-16 — EXACT-EVIDENCE COMPLETION (runner card A). Lessons; #1 and #2 are durable-rule candidates needing Andrew's approval.

**1. Near-agreement between a defective number and a correct one is NOT evidence the defect is harmless.**
The study's exact arm-C score (0.1570) sat 0.0025 from the honest recomputation (0.1595) — and was
nonetheless produced by TWO large defects that nearly cancelled: a **leak worth +0.0822** (review C6: one
fold's shape MAP applied to all 4 folds) and a **basis mismatch worth −0.0847** that the review never caught.
Had anyone "sanity-checked" the leaky number against an honest one and seen agreement, they would have
declared the leak benign and shipped the mismatch. **Pattern: when you find a defect, quantify IT
(counterfactually, one defect at a time) — do not infer its size from the final number's plausibility.**
Corollary: I made exactly this error myself (my D1 concluded "the leak barely mattered"); the decomposition
probe, not intuition, corrected it (D2).

**2. Reduced-basis coefficients carry their basis as part of the datum.** The mismatch above was:
shape-field raw coefficients fit in the `A0_wide` θ=1 eigenbasis (r=209, 18 matched modes, r0=106) loaded and
applied to the `A0_wide__enr` θ_MAP eigenbasis (r=194, 19 modes, r0=108). Different eigenvectors = different
coordinate systems; the transfer is meaningless. **It did not crash** — the arrays merely broadcast — so it
produced a wrong-but-plausible number silently, and all three dimensions (r, n_modes, r0) disagreed with
nothing complaining. **Proposed rule: any code path that loads modal/reduced coefficients fit elsewhere must
assert basis identity (r, matched-mode count, truncation index, and ideally a basis hash) before use.**

**3. "Run it serially" is not the same mitigation as "bound the memory."** T2 ran 28 heavyweight independent
eigensolves in ONE long-lived process. Candidates 1-17 took ~530 s each; by candidate 18 the 16 GB box was at
10.8/12.3 GB swap and a single solve took **11,187 s (22× the 506 s median)**. I had logged the study's own
D11 swap-thrash lesson in my D0 and still walked into it, because I read "serial" as the whole fix when the
real risk was **cumulative** memory in a long-lived process. **For a batch of heavyweight INDEPENDENT jobs on
fixed RAM, make each job its own process** — it is the only way the working set returns to the OS, and it is
free when the jobs are already resumable. Restarting that way took the next solve back to 428 s.

**4. A job that is ALIVE is not a job that is PROGRESSING.** My watchers polled `pgrep` — liveness — so a 22×
slowdown looked identical to "still running" for three hours. **Monitor throughput (records/hour), not
liveness**, and alarm when per-unit time exceeds a few times its median. (The saving grace was the card's
resumability requirement: 18/28 records and 18/18 packages survived the kill with zero corruption, because
`enrich()` only writes on completion.)

**5. (Checker design — extends the 07-16 Card B lesson #5, same family, different failure.)** Card B's lesson
was "a checker whose gates cover only process integrity can read GREEN while the science is YELLOW." Mine is
the mirror image: **do not SHA-lock a gate on the EXPECTED VALUE of an external result.** I locked G05 to
require `S3/S4 == "CANNOT-VERIFY"` because my card said so — then Card B landed in parallel and **falsified
S4**. The locked gate then forced my verdicts file to carry a stale status. I complied (never edit a locked
checker mid-trial) and attached `superseded_by_card_B` everywhere, but the right gate was the INVARIANT my
card actually cared about — *"this card must not manufacture S3/S4 evidence"* — not a prediction of someone
else's finding. **Proposed rule: checker gates constrain the CONDUCT of the workspace that owns them; they
must never encode a predicted external outcome.**

**6. Runtime accounting breaks silently when you change the process model.** After the D4 restart, each
candidate ran in its own `--one` process that exits before the step timer fires — so `active_runtime_s` came
out **15 s for a 7.5 h compute**, and the gate (`active <= elapsed`) happily passed, because a falsely SMALL
active time cannot trip that inequality. **The runtime gate is one-sided and cannot catch under-counting**;
the fix was to sum per-candidate wall time from the records. Worth knowing before comparing runners.

## From cards A/B/C (2026-07-20, D19)
- **Diff the quantity contract BEFORE declaring "cannot reproduce."** The study's net-CG failure was a
  3-line contract divergence (envelope ratio vs width-normalized-by-incumbent), mis-attributed to
  "calibration." The Quantity Contract Gate exists for exactly this.
- **Near-agreement between a defective number and a correct one is not evidence the defect is harmless** —
  the arm-C leak (+0.082) and a silent basis mismatch (−0.085) nearly cancelled; the "right" 0.157 hid two
  bugs. Decompose, don't compare endpoints.
- **Shape-field coefficients are coordinates in a specific eigenbasis** — never transplant them across
  bases; broadcasting will not crash, it will silently deflate.
- **Per-mode quantities are not basis-invariant inside near-degenerate clusters** (18/44 in-band pairs
  within 1%); only subspaces are. Any A↔B per-mode mapping must be MAC/subspace-based.
- **A single-θ band omits the θ-spread term** — the delivered twin's width carries +0.35..+1.11 of θ
  posterior spread; a point-θ reimplementation structurally cannot reproduce it.
- **Checker gates should encode conduct invariants, not assumptions about other runs' results** (Card A's
  S3/S4 gate went stale when Card B landed in parallel).
- **Measuring an amplitude can honestly WIDEN a band** (254.3 Hz cluster: observed cross-drive scatter 1.39
  > assumed 0.80). Pre-registering the falsification path (A5b) made this a clean result, not a fight.
