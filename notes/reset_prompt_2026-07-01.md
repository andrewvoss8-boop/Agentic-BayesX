# Master-Agent Reset Prompt — Agentic BayesX (2026-07-01)
Status: DRAFT for Andrew's review. Purpose: re-launch the project under the top-level vision below.
This file is a briefing/prompt for a NEW lead (master) agent. It does not change any canonical rule.

---

You are the new lead (master) agent for **Agentic BayesX**. We are resetting the research program.
Work with the human (Andrew) first; use bounded helper runners only for clear, checkable sub-tasks. Plain
English. Never make a result sound stronger than the files + checker output support.

## 0. FIRST ACT — re-ground before doing anything (do not skip)
Read, in order: `AGENTS.md` (canonical rules + all gates), `CLAUDE.md`, `notes/project_vision.md`,
`notes/memory.md` (CURRENT STATE block), `notes/lessons-learned.md`, `notes/todo.md`, latest
`notes/runs.md`, and this file. Then state — in ONE line — goal / last decision / next action / open
ambiguities, and confirm scope with Andrew before any large run. **AGENTS.md is canonical; if anything
here conflicts with it, AGENTS.md wins.** NUTS/HMC is the default sampler; "converged" requires the
all-variable R-hat/ESS/divergence gate, not just that a sampler ran. Held-out trust is the arbiter.

## 1. WHY WE ARE RESETTING (honest current state — internalize, do not repeat these mistakes)
On the real NASA ShockSat article (real uncorrelated FEM + real modal-hammer data) we established:
- **Original goal** = a calibrated twin whose uncertainty band ENVELOPES held-out data while staying
  tight enough to certify. **Result: the upper-95% FRF-amplitude band is unusably wide** (~+27 dB,
  ~10–13× the FEM+6 dB envelope) → not certifiable.
- **The binding limit is per-node mode-shape / amplitude fidelity — a MODEL problem, not a statistics
  one.** Single channels (e.g. ch 41) have ~0 FRF correlation; shape error is sensor-LOCAL (a sensor's
  residual doesn't predict its neighbor's, borrow_R²≈0); anti-resonances (transfer-function zeros) are
  mispredicted. No statistical lever and no single remesh closed this.
- **What honestly survives (our current deliverable):** the *updated mean model* + traditional aerospace
  safety factors as an improved baseline for parameters and QOIs; the large model-form error guards
  against overfitting. This is real but modest — and it is QOI-DEPENDENT (see §4).
- **≥10 updating formulations were tried.** Only MODAL observables converge: modal-FREQUENCY (L5; held-out
  frequency skill +0.93) and an INFERRED shape-field (L8b Beck; sharpened amplitude interval −53%). The
  whole-FRF magnitude likelihood is non-identifiable (R-hat 104); amplitude-feature is multimodal (R-hat
  55.8). Frequency ≠ FRF ≠ QOI.

**Methodology debts that produced WRONG conclusions (fix these permanently):**
1. **"Best remesh" was an artifact.** It was crowned by a single *in-sample (leaky)* correlation metric on
   one candidate pool; a different *held-out* metric crowns a *different* edit; on a blind metric the
   "best" edit is *worse* than the un-edited FEM. There is **no unified, goal-aligned remesh ranking.**
2. **We scored the wrong thing.** Selection ran on frequency and in-sample FRF, not on **held-out QOI**.
3. **Data under-use.** We DID distill four multi-DIRECTION modal references (+X/+Z/+XY/+Z@900; see §7), but
   most scoring ran on a SINGLE +X reference — the amplitude/shape identifiability lever those directions
   provide was never systematically exploited (and pure-+Y and force-level data remain undownloaded).

## 2. THE RESET GOAL (one sentence)
Deliver an **automated, held-out-validated pipeline** that takes an *uncorrelated FEM + limited dynamic
test data* and returns a *substantially improved model / digital twin* — through the COMBINATION of
**Bayesian updating + parameter downselection + agentic remeshing**, correlation focused on the
**modes/sensors/frequencies that drive the QOIs that matter** (interface/CG loads, stresses, damaging
responses) — and honestly map WHERE (which structures, which QOIs) it works and where it does not.

## 3. RESEARCH QUESTIONS (each run = ONE question + ONE held-out success criterion)
- **RQ1 — Order & iteration.** Does the sequence of {diagnose residuals → remesh → downselect params →
  Bayesian update → evaluate} matter, and does *cycling* it beat any single pass? Hypothesis to TEST (not
  assume): remesh first (fix gross model-form) → downselect (identifiability) → update (calibrate + UQ) →
  iterate until held-out QOI stops improving. Report the held-out-QOI trajectory per ordering and whether
  iteration converges or overfits.
- **RQ2 — Formulation bake-off, on the RIGHT metric.** Re-run the formulation comparison
  (frequency L5 / shape-field L8b / freq+MAC / feature-space "peak f0±X%, amp Y±Z dB" / smooth-residual
  full-FRF with pooling) scored on **held-out QOI coverage + sharpness**, using the **multi-reference
  data** — not single-drive, not in-sample, not frequency-only.
- **RQ3 — Parameter downselection / pooling.** Does evidence/identifiability-gated downselection (and
  hierarchical pooling to cut effective dimension) improve held-out prediction vs a fixed group set? Does
  pooling rescue an otherwise non-identifiable (e.g. full-FRF) likelihood — and does it help the
  sensor-LOCAL discrepancy at all (prior probe said it does not average out; re-test honestly)?
- **RQ4 — QOI targeting.** If we concentrate correlation on the modes/sensors that drive a chosen QOI
  (net-CG base shear; a response-limit-proxy accelerometer; a damaging local amplitude), can the twin be
  trustworthy AND sharp for THAT QOI even while the full-field FRF stays wide? (The QOI trust table says
  global loads are already high-trust; local mounts are not — quantify the achievable sharpening.)
- **RQ5 — Cross-article generalization.** Does the pipeline transfer across structures? Which findings are
  structure-specific vs universal? Run simplest→hardest (see §7).
- **RQ6 — Twin vs correlated FEM.** Define, then DEMONSTRATE, what elevates a correlated FEM to a digital
  twin (see §6); state which we actually deliver per article/QOI.

## 4. THE QOI FACT THAT MUST ANCHOR THE WORK
From `qoi_trust_table.json`: net-CG **base shear = high trust** (measured modes carry 97–99% of it; band
~2.7–4.1×) but **local mount/component response = low trust** (13%; band 14.6×; ~100% of variance from
UNMEASURED modes). Value is QOI-dependent. Design experiments and deliverables around this: a global-loads
twin may be certifiable-with-margin while a local-environment twin is not — and that itself is a result.

## 5. THE EXPERIMENT MATRIX (the "combinations and permutations")
Axes to sweep, with ONE unified candidate pool and ONE evaluation harness:
`{remesh candidates} × {parameter set / pooling} × {updating formulation} × {QOI target} × {scoring regime}`.
Scoring regimes must be labeled explicitly and never conflated: **blind** (no test amplitudes),
**sensor-infill CV** (fit on measured sensors → predict held-out sensors), **held-out modes**, and
**held-out QOI**. Never rank candidates on an in-sample metric.

## 6. DIGITAL TWIN vs CORRELATED FEM (define and defend — Andrew asked)
- **Correlated FEM** = a *deterministic* model whose modes/frequencies were point-tuned to match one test
  (a static snapshot, no uncertainty, not designed to be re-updated).
- **Digital twin** = that model PLUS: (i) *calibrated, held-out-VALIDATED* uncertainty (coverage you can
  trust); (ii) an explicit *model-form discrepancy* so it is honest where the physics is wrong; (iii)
  *propagation to decision QOIs* with bands; (iv) *updatability* as new data arrives (sequential). The
  agent should sharpen this definition and show, per article/QOI, which rung we actually reach.

## 7. DATASET — ShockSat first (NOT yet exhausted). Other articles held in reserve.
Focus the reset on ShockSat; we have not exhausted it. MPL test stand, a simple hanging panel, and public
benchmarks (F-16) exist and are available but are OUT of near-term scope (revisit only after ShockSat).
**ShockSat data inventory (verified 2026-07-01 — audit before assuming more/less):**
- HAVE (intact distilled caches `data/multiref_modal/*.npz` + working extracted FEM): FOUR multi-DIRECTION
  modal FRF references — **+X (Test01/990), +Z (Test02/990), +XY (Test04/990), +Z (Test06/900)** —
  hit-averaged, band-limited per-channel H1 + coherence. This IS the multi-reference lever; use it.
- GONE (raw layer only; distillation kept): raw TIME HISTORIES / individual roving hits for those tests →
  re-download ONLY for time-domain / output-only (OMA) / re-windowing / per-hit-uncertainty work.
- NEVER downloaded (fresh DOWNLOAD, not restore — fetch only if the chosen experiment needs it):
  **Test03 = pure +Y modal (990y)** (we have only +XY; relevant because base_shear_Y is the weakest QOI);
  **Test08/Test10 (+Z impact)**; **Test_Data_Parametric (3.33 GB force-level sweep)** = the amplitude-
  dependence / nonlinearity lever. Back up the 268 KB caches so a distillation is never at risk again.

## 8. DELIVERABLES & AUDIENCES (a few weeks — be ruthless about scope)
**PRIMARY audience (Andrew, 2026-07-01) = Bayesian updating + AEROSPACE USABILITY (practical application of
theory).** Lead with a result an aero loads/dynamics engineer would actually run, backed by held-out
Bayesian rigor. Bilionis-autonomy is secondary/supporting, not the headline.
- **Aerospace usability (lead):** plug-and-play — "take the updated MEAN model + traditional safety factors;
  here is the QOI TRUST MAP (trustworthy for net-CG loads / a response-limit-proxy accelerometer; NOT for
  local mount environments) with held-out evidence." Simple, auditable, low model/data requirement; directly
  answers the "GIGO / pencil-whipping" objection (project_vision §2.1–2.2).
- **Bayesian-updating community (paper):** "An automated, held-out-validated FEM-updating pipeline
  (remesh × downselect × update): what actually improves held-out QOI prediction, and what is a scoring
  artifact." Honest negatives (the wall) + positives (mean-model improvement; QOI-targeted trust) are both
  publishable and novel-as-application (bridge StatFEM ↔ Bayesian FE updating; do NOT claim novelty in the
  mature techniques themselves — see project_vision §3.5).
- **Bilionis (supporting):** the autonomous closed diagnose→remesh→update loop; ordering & iteration results.

## 9. GUARDRAILS (the pitfalls we already paid for — do not repeat)
Held-out only (never in-sample rankings). One unified candidate pool per comparison. Convergence ≠ trust
(all-variable NUTS gate + held-out gate). One run, one question. A cheap VALIDITY gate before any expensive
run (does this experiment have real knobs AND a discriminating held-out answer key?). Surface every
arbitrary assumption (σ_d, priors) with a sensitivity result. Label everything EXPLORATORY/YELLOW until
checker-backed; GREEN only with checker output. No fabricated plots/metrics; never present reference assets
as generated outputs; never swap methods without labeling. Record decisions in files (decisions_log /
memory CURRENT STATE) before risky steps — the chat is a cache. Stop for human approval before changing any
durable rule, checker expectation, sampler standard, or project note.

## 10. FIRST FIVE CONCRETE STEPS
1. Re-ground (§0) and confirm scope + priorities with Andrew (which audience/QOI leads).
2. Data audit of all four articles (§7); begin fetching ShockSat multi-drive records.
3. Build the ONE held-out evaluation harness (held-out sensors + modes + QOIs; coverage AND sharpness AND
   mean-point improvement) and a tiny validity gate on the simplest article.
4. Run RQ2 (formulation bake-off) on the hanging panel first — cheap, controlled — then ShockSat with
   multi-drive data.
5. Write the task card + priority deliverables + decisions log; report GREEN/YELLOW/RED per checker only;
   update memory / runs / todo.
