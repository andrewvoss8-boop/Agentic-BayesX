# Runner task card B — StatFEM evaluation: ShockSat held-out-QOI test (plain config, 5 bias combos)

You are a runner agent in **Agentic BayesX** (one of two parallel StatFEM-evaluation runners; you run
Experiment B only — the ShockSat held-out-QOI study; a sibling runner runs the simple consistency toy). Lead =
Claude Code; human = Andrew Voss; advisor whose objective this serves = Ilias Bilionis. Build for correctness,
reproducibility, traceability, continuity. Plain English; never make a result sound stronger than the files +
checker output support.

## 0. Re-grounding (do FIRST, before any code; re-do after any compaction)
Read, in order: `AGENTS.md` (every gate is binding); this card; `notes/memory.md` CURRENT STATE block; then
ground in the already-done work you build on:
- `artifacts/reports/shocksat_fem_modal_twin_20260609/` — the runnable Python ShockSat FEM (`scripts/fe_core.py`,
  reduced model `fem_model.npz` / `matrices/`, `groups.json` = the **9 stiffness groups**, mode shapes on 76
  accel nodes). `packet.md`: `K(θ)=A_fix+Σ_g θ_g A_g`; **θ_g=1.10–1.20 is exactly +10–20% E**; σ_f≈4.6%
  discrepancy floor; **only 4/9 groups identifiable**; held-out *frequency* predictions calibrated but
  withheld-mode posteriors multimodal = "predictive coverage robust / parameter recovery brittle" on real
  geometry (the very pattern this study probes).
- `artifacts/reports/shocksat_statfem_runner_20260609/` — `channel_map.csv` = 326 mapped sensors with FEM grids
  + coordinates; the launch-def principles you implement: *"output-space discrepancy — do NOT put discrepancy in
  the stiffness parameter space"* (the orthogonal lever), QOI = "shock response metric at a held-out channel",
  "hold out ≥1 channel". The StatFEM calibration was **deferred** — this card executes it, in controlled
  synthetic form so we have ground truth for the held-out QOIs.
- `artifacts/reports/confidently_wrong_modelform_20260616/` — today's study: naive (no discrepancy) is
  confidently wrong under model-form error; a learned discrepancy restores held-out coverage; the honest limit
  is coherent confounded bias (QOI holds, parameter missed). Reuse its structure and figure/checker patterns.
- `artifacts/reports/papers_statfem_studies_20260612/` — the Schneider complex-correlated discrepancy + the
  orthogonal cure are already coded here; **reuse and extend that code**, don't reinvent it.
- `.claude/skills/tufte-data-graphics/SKILL.md`.
Then create workspace `artifacts/reports/statfem_shocksat_eval_20260616/` and write `decisions_log.md` with one
line: goal / last decision / next action / open ambiguities.

## 1. The objective (Ilias, verbatim) — evaluate, do NOT defend or attack
> "Your objective should be to evaluate the StatFEM approach. It may not be possible to validate it because it
> may not be working. So, build, evaluate, identify its gaps, and suggest improvements should be your goal."

"StatFEM does not work (here)" is a permitted, valuable finding. Build the criterion; report whichever way the
numbers fall.

## 2. The concern under test (do NOT broaden)
Bilionis's "confidently wrong" charge (relayed via Andrew; HYPOTHESIS — no Bilionis paper found that names
StatFEM): a converged StatFEM posterior can be **confidently wrong** under model-form error, with no warning.
**The trust test = held-out-sensor QOI coverage:** calibrate on a few channels, predict QOIs at sensors you
never used, and check whether the truth lands in the band. Either verdict can be earned (StatFEM `d` may restore
coverage = robust, or fail = brittle); the direction is the science.

## 3. Plain-ShockSat constraint (Andrew, explicit — non-negotiable)
Use the **plain standalone ShockSat configuration ONLY** — the 9-group ShockSat FEM from
`shocksat_fem_modal_twin_20260609`. **Do NOT use the coupled ShockSat×tray model** from
`shocksat_tray_coupled_qoi_20260610`. No tray, no payload coupling. State this in the assumptions ledger.

## 4. Priority deliverables (each needs a delivered artifact; record in `priority_deliverables.md`)
1. The ShockSat held-out-QOI evaluation across **5 bias combos** × the discrepancy-structure arms, every NUTS
   arm gate-converged or labeled not-yet-converged.
2. **The held-out-QOI coverage result across the 5 combos** (the money result): per-arm coverage of held-out-
   sensor QOIs, reported as a **distribution over the 5 combos** (this retires the single-realization caveat).
3. θ recovery per group (identifiable vs not), tied to the strain-energy/FIM identifiability gate.
4. The discrepancy-structure comparison: naive vs StatFEM-iid vs Schneider vs orthogonal.
5. A StatFEM evaluation **scorecard** (claim → evidence → verdict → suggested improvement), folding in the prior
   ShockSat partial-identifiability and Schneider findings.
6. Immutable `check.py`, `run_all.sh`, `runtime.json`, tufte packet + slide deck for Ilias (gated on non-RED).

## 5. Testbed — plain ShockSat as a controlled truth generator (synthetic)
Reuse (COPY into the workspace; never edit originals) the reduced ShockSat FEM: `K(θ)=A_fix+Σ_g θ_g A_g` (9
groups), and the FEM mode shapes at the chosen sensor DOFs (map sensors→grids via `channel_map.csv`). Build the
**per-sensor modal-superposition FRF** `H_s(ω;θ,ζ)` over a documented frequency grid, assigning nominal modal
damping ζ (state value/source; e.g. a fixed 1–2% or from the measured modes). **Why synthetic FRF is valid here
(it was NOT for the real test data):** truth and inference share the FEM geometry, so the test-tap-vs-FEM
transfer-path objection does not apply — state this explicitly.

**Two layers of injected model-form error (the point of the study):**
- **Parametric bias:** set the *truth* θ_g to **+10–20% offsets** on chosen groups; the *inference* model starts
  at nominal θ=1 and infers θ (a recoverable-vs-unrecoverable error, given the 4/9 identifiability finding).
- **Schneider-style discrepancy** (reuse `papers_statfem_studies_20260612`): a **complex, correlated**
  multiplicative model-form error on the truth FRFs, correlated over **frequency AND space (across sensors)**,
  NOT representable by any θ scaling. Plus an **orthogonal variant** — the discrepancy projected orthogonal to
  the θ→FRF sensitivity span ("do not put discrepancy in the stiffness space").

## 6. The 5 bias combos (for solid coverage — the multi-realization upgrade)
Five distinct truth configurations spanning identifiable and unidentifiable groups. Defaults (document and may
refine): (1) **identifiable only** — top_box +15%, bottom_box −10%; (2) **unidentifiable only** — joints +20%,
contact +15%; (3) **mixed** — top_box +15%, joints +20%, plates −12%; (4) **large** — cross_beam +20%, joints
−18%; (5) **broad small** — ~±10% across several groups. Run **all arms on each combo** (same synthetic data per
combo). Report coverage as a distribution over the 5.

## 7. Observation + arms + QOI
- **Observe a FEW channels; hold out the rest.** Calibrate on a small sensor subset (e.g. 4–8 accel channels —
  document the choice; run a held-out-channel-choice sensitivity). **Predict QOIs at the held-out sensors.**
- **Arms (per combo, same data):** **M0 naive** (no discrepancy); **M1 StatFEM-iid** (additive iid output
  discrepancy `d`); **M2 StatFEM-Schneider** (complex correlated freq+spatial `d`); **M3 StatFEM-orthogonal**
  (Schneider `d` projected orthogonal to the θ-sensitivity span). NUTS, ≥4 chains, all-variable convergence gate
  (max R-hat ≤1.05, min ESS ≥200, div-frac <2%).
- **QOI at each held-out sensor:** (a) **peak FRF amplitude** in a documented band, and (b) a **band response
  metric** (GRMS-like). Per arm/combo record: held-out-sensor QOI coverage at nominal 95%; per-group θ posterior
  + truth-covered flag; learned discrepancy scale(s); convergence over ALL variables.

**Expectation to TEST, not assume:** naive confidently wrong on held-out QOIs as the injected error grows;
StatFEM `d` restores QOI coverage; θ recovered for identifiable groups, missed for unidentifiable ones; Schneider
beats iid where the error is structured; orthogonal avoids the over-absorption / parameter-bias (Plumlee
plug-in bias). Report whichever way it falls.

## 8. Identifiability gate (required — you infer θ + discrepancy)
Reuse the ShockSat **modal strain-energy** decomposition (`joint_strain_energy`) and the FIM eigen-view to state,
per group, whether it is identifiable from the chosen channels at the realized discrepancy floor, BEFORE any
"θ_g recovered / not" claim. Tie non-recovery to mechanism (sensitivity below the σ_d floor / θ↔discrepancy
confounding) + the pre-test lever (sensor placement / which band excites the group).

## 9. Sensitivity gate
Vary what is most likely to flip the verdict: discrepancy structure (already an arm), held-out-channel choice,
bias magnitude, damping value, frequency band. Report whether the robust/brittle verdict is stable across the 5
combos or fragile.

## 10. Discretization-resolution gate
Document the frequency grid and the modal-reduction basis; show the reduced FRF matches a fuller solve at the
QOI-driving peaks (reuse the modal twin's reduced-vs-full check pattern).

## 11. Verification gate — immutable `check.py` (write FIRST, then make it pass honestly)
GREEN requires ALL: every reported NUTS arm gate-converged or labeled not-yet-converged; **held-out-QOI coverage
reported with numbers for all arms across all 5 combos**; naive shown confidently wrong where the injected error
is large; StatFEM `d` coverage quantified; the iid/Schneider/orthogonal comparison reported; θ identifiable-vs-
not reported against the strain-energy gate; the reduced FRF validated against a fuller solve; the scorecard
present. YELLOW (documented, never "success"): synthetic surrogate error; any parameter-level miss; any
not-yet-converged arm; a combo-dependent (fragile) result. RED: undocumented non-convergence; a coverage claim
without numbers; a missing/fabricated figure; tufte_lint / image-QA / text-overlap failure; the coupled tray
model used; an original scaffold edited in place; reduced FRF not validated. Exit non-zero only on RED.

## 12. Plot & deck gate (apply the tufte skill; NO text-on-text)
Every figure → saved `.py` + `tufte_lint.py` + pixel image-QA + save-time text-overlap (bbox) auditor (JSON
each). Required: held-out-QOI coverage across combos by arm (the money figure); naive-vs-StatFEM held-out FRF
bands; θ recovery (identifiable vs not) by combo; the iid/Schneider/orthogonal comparison; a method/construction
schematic (where physics + discrepancy live). Log-frequency axes; linear magnitude unless dB justified;
provenance + not-yet-converged flags ON each figure. Deck (`slides/`, ~8–12, gated on non-RED checker):
objective (Ilias's words); plain-ShockSat testbed + injected error; the held-out-QOI money slide; θ recovery;
discrepancy structure; gaps; suggested improvements; verdict + scope. Every claim traces to a checker number.

## 13. Runtime & compute
`runtime.json` (`active_runtime_s`, `elapsed_wallclock_s`); pin `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`,
float64, `.venv_nuts`. Reuse the reduced 74-mode ShockSat basis (do NOT re-assemble the 67k-grid FEM). The 5
combos × 4 arms × 2 QOIs grid is large — make it **resumable** (skip finished cells) and **launch detached**
(`nohup … & disown`) with short until-loop monitoring if it exceeds the tool timeout.

## 14. Not allowed / anti-cheating
Do NOT edit the prior ShockSat/Schneider/today scaffolds or any immutable checker; COPY anything you reuse.
Do NOT use the coupled tray model (§3). Do NOT fabricate coverage numbers or figures; do NOT copy a prior
study's results as your own. Do NOT present an arm as failing if it merely didn't converge — converge it first
or label not-yet-converged. Do NOT pre-decide the verdict.

## 15. Done criteria
Artifacts exist; `check.py` passes (non-RED) via `bash run_all.sh`; assumptions + limits documented; every
figure tufte-linted + image-QA + overlap-audited; the deck's every claim traces to a checker number;
`decisions_log.md` complete; the StatFEM verdict + scorecard + gaps + suggested improvements written for Ilias;
the proposed `docs/report/project_log.md` row + `notes/*` updates SURFACED for the lead (status from the
checker), NOT self-applied.

## 16. References (local + arXiv)
Local: `references/pdfs/2020_Duffin_..._misspecified_models.txt`/`.pdf`, `statFEM.pdf`,
`digital-twinning-...-statistical-finite-element-method.pdf`, `KennedyOHagan_2002 (1).pdf`,
`Bayesian_calibration_of_inexact_computer_models_Plumlee_2017.pdf`; the ShockSat + Schneider workspaces above.
arXiv (verified): statFEM 1905.06391 (Girolami et al.); statFEM-misspecified PNAS (Duffin 2020); statFEM
misspecification 2307.05334; PIFT 2301.07609 (Alberts & Bilionis); IFT 2306.02150 (Hao & Bilionis).

## 17. Human stop points (lead handles; you SURFACE, do not self-apply)
Stop for human approval before changing any durable rule, checker expectation, sampler standard, or project
notes/vision. This study + its checker + deck are new artifacts and need no stop; the `project_log` row and any
`notes/memory.md` update do.

## Communication style
Reader is BEGINNER-TO-INTERMEDIATE in ML/statistics (define every ML/stats term, acronym, symbol with units on
first use; lead with intuition + a concrete example, then the precise detail) and ADVANCED in structural
dynamics / FEM (FRFs, modal analysis, mode shapes, damping used directly). Full rule in `AGENTS.md` / `CLAUDE.md`.
