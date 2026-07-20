# Runner task card A — StatFEM evaluation: the physics-in-likelihood *consistency* toy

You are a runner agent in **Agentic BayesX** (one of two parallel StatFEM-evaluation runners; you run
Experiment A only — the simple consistency toy; a sibling runner runs the ShockSat held-out-QOI study). Lead =
Claude Code; human = Andrew Voss; advisor whose objective this serves = Ilias Bilionis. Build for correctness,
reproducibility, traceability, continuity. Plain English; never make a result sound stronger than the files +
checker output support.

## 0. Re-grounding (do FIRST, before any code; re-do after any compaction)
Read, in order: `AGENTS.md` (every gate is binding); this card; `notes/memory.md` CURRENT STATE block;
`artifacts/reports/confidently_wrong_modelform_20260616/` (today's confidently-wrong study — same harness style,
reuse its scaffolding patterns: copied NUTS module, immutable checker written first, tufte figures + image-QA +
text-overlap auditor); `.claude/skills/tufte-data-graphics/SKILL.md`. Then create workspace
`artifacts/reports/statfem_consistency_toy_20260616/` and write `decisions_log.md` with one line:
goal / last decision / next action / open ambiguities.

## 1. The objective (Ilias, verbatim) — evaluate, do NOT defend or attack
> "Your objective should be to evaluate the StatFEM approach. It may not be possible to validate it because it
> may not be working. So, build, evaluate, identify its gaps, and suggest improvements should be your goal."

"StatFEM does not work (here)" is a permitted, valuable finding. Build the criterion, then report whichever way
the numbers fall. Do not pre-decide.

## 2. The single concern under test (do NOT broaden)
Bilionis's charge (relayed via Andrew; treat as a HYPOTHESIS — no Bilionis paper found that names StatFEM):
methods that encode **physics through the likelihood** (residual-as-fictitious-data) give posteriors that
**depend on the discretization** (collocation count `N_c`, residual noise `σ_r`, mesh `h`) and do **not converge
to the truth as you refine** — i.e. they are **"inconsistent and incorrect."** His cure (IFT/PIFT, arXiv:
2301.07609, 2306.02150) puts physics in the **prior** with a learned inverse-temperature **β**, "independent of
any such discretization."
**The decisive, testable question:** as you refine the discretization, does each construction's posterior
**converge to the truth** AND stay **invariant** to knobs that carry no real information, or does it **drift**?
(*consistency* = posterior concentrates on the true value as data/refinement grows; *discretization-invariance*
= the answer doesn't change when you turn a purely-numerical knob.)

## 3. Testbed — keep it minimal and in-domain (structural dynamics)
A **simple 1-D structural-dynamics system** with an analytic truth and one uncertain parameter — e.g. a
fixed-free **axial rod** (or Euler–Bernoulli beam) eigenproblem, `−(EA u')' = ω² ρA u`, inferring a scalar
stiffness scale `θ` (θ=1 nominal; truth offset for the misspecified case). Observables = a few natural
frequencies and/or the drive-point FRF, with measurement noise. Discretization knobs: number of FE elements
(mesh `h`), number of retained modes, collocation count `N_c`, residual noise `σ_r`. **Controllable model-form
error ε:** the truth has a feature the inference model omits (e.g. a small distributed support spring, or
spatially varying `EA`, or a local stiffness loss); ε=0 is the no-error control where consistency MUST hold for
a correct method.

## 4. The three constructions (same data; the construction differences ARE the experiment)
- **M-lik — physics-in-likelihood (the indicted form):** condition on the governing-equation **residual ≈ 0**
  at `N_c` points with residual noise `σ_r` (a *fictitious* likelihood), plus the data likelihood on the
  measured frequencies/FRF; infer the discretized field + `θ`. **`N_c`, `σ_r` are the knobs to sweep.**
- **M-statfem — StatFEM:** the FE model gives the prediction; data = FE prediction + **additive zero-mean
  discrepancy `d`** (the model-misspecification term, assumed covariance) + noise; infer `θ` + `d`'s
  hyperparameters. **The StatFEM discretization is the FE mesh = the number of FE basis functions `h`,
  refined jointly with the number of measurement points `n`** (this is the canonical "discretization" in
  statFEM — NOT collocation count). Note StatFEM's physics lives in the FE *prior* (the stiffness/operator
  defines the prior), not a residual likelihood.
- **M-ift — physics-in-prior / IFT-style:** a field prior weighting the residual by a **learned β**; data
  likelihood; infer field + `θ` + `β`. Knob: discretization.
State for each, in the Method Summary: where the physics lives (prior vs likelihood), what plays the
model-error role (`d`, `σ_r`, or `β`), and the likelihood/posterior equations.

## 5. The consistency experiment (the centerpiece)
With the **correct model (ε=0)** and under **model-form error (ε>0)**, for each construction refine the knobs
and record the posterior over `θ` and the held-out field/frequency band:
- M-lik: sweep `N_c` and `σ_r` (the irrelevant knobs) → **hypothesis: the θ posterior drifts / fails to
  concentrate on θ_true (inconsistency).**
- M-statfem / M-ift: sweep mesh `h → finer` and data `n → larger` → **hypothesis: M-ift converges to θ_true and
  is invariant to the numerical discretization. For M-statfem there is published convergence theory** (Papandreou
  2111.07691: the discretized statFEM posterior converges to the *ideal/continuum* statFEM posterior at the
  **FE mesh rate** O(h^p); Karvonen 2201.07543: posterior-mean L²-error has polynomial rates in `n` and the #
  basis functions, with the smoothness possibly misspecified). **So benchmark M-statfem's mesh-refinement
  against that predicted convergence** — a clean convergence is the theory-backed expected result and would
  *rebut* a naive "statFEM is mesh-inconsistent" claim; reserve genuine "inconsistency" findings for the
  collocation arm (M-lik) whose `N_c`/`σ_r` have no continuum limit. Report which way each falls, with numbers.
Decisive metrics: (C1) does the θ posterior **concentrate on θ_true** as data grows? (C2) **discretization
sensitivity** = spread of the posterior mean across the knob (report a number); (C3) held-out field/frequency
coverage at nominal 95%. The **money figure** = posterior(θ) mean ± 95% CI vs the refinement knob, per
construction, with the θ_true line — this adjudicates Ilias's charge.

## 6. Gates (all binding; AGENTS.md)
- **Solver-validation FIRST:** the forward solver must converge to the **analytic truth** under refinement, so
  any posterior drift is the *method*, not under-resolution. Show this before any consistency claim.
- **Sampler:** NUTS (NumPyro, `.venv_nuts`), ≥4 chains, all-variable convergence gate (max R-hat ≤1.05, min ESS
  ≥200, div-frac <2%) or labeled not-yet-converged (YELLOW). If a construction needs SVI (e.g. IFT), say why and
  report its diagnostics.
- **Identifiability:** report the θ→observable sensitivity; if θ is weakly identified at a given ε, say so.
- **Discretization-resolution gate is CENTRAL** — the discretization is the independent variable; document it.
- **Immutable `check.py` (write FIRST):** GREEN requires the solver-convergence check; every reported arm
  gate-converged or labeled; the **consistency criterion reported with numbers for all three constructions**
  (concentration on θ_true + a discretization-sensitivity number, whichever direction); held-out coverage
  reported; the verdict stated for each construction. YELLOW: synthetic surrogate error; any not-yet-converged
  arm; a fragile/realization-dependent result. RED: undocumented non-convergence; a consistency claim without
  numbers; a missing/fabricated figure; tufte_lint / image-QA / text-overlap failure; solver not validated
  against analytic truth; original scaffold edited in place. Exit non-zero only on RED.
- **Plots/deck:** every figure → saved `.py` + `tufte_lint.py` + pixel image-QA + save-time text-overlap (bbox)
  auditor (JSON each). Required: the consistency money figure (θ vs knob by construction); held-out coverage;
  a construction schematic (physics in prior vs likelihood). Log-frequency axes where frequency is plotted;
  provenance + not-yet-converged flags ON each figure. Short deck (`slides/`, ~6–8, gated on non-RED checker):
  the charge; the three constructions; the consistency verdict; gaps + suggested improvements; scope.
- **Runtime:** `runtime.json` (`active_runtime_s`, `elapsed_wallclock_s`); pin `OMP_NUM_THREADS=1
  VECLIB_MAXIMUM_THREADS=1`, float64. A 1-D rod/beam is a tiny tridiagonal/banded solve — runs fast; if the
  knob×ε×construction grid is large, make it resumable.
- **Reference/standards:** cite statFEM 1905.06391 (Girolami et al.); **the statFEM convergence theory you MUST
  benchmark against — Papandreou, Cockayne, Girolami, Duncan 2111.07691 "Theoretical Guarantees for StatFEM"
  (Wasserstein-2 convergence to the ideal posterior at the FE mesh rate) and Karvonen, Cirak, Girolami
  2201.07543 "Error analysis for a statFEM" (L² posterior-mean rates in n and # basis functions, smoothness
  possibly misspecified)**; PIFT 2301.07609, IFT 2306.02150. Note that probabilistic *solvers* (Chkrebtii
  1306.2365 / Conrad 1506.04592 / Cockayne 1702.03673) quantify **discretization** error and Conrad explicitly
  distinguishes it from "model error induced by missing physical or inadequate descriptors" — keep the strands
  separate. The honest framing: "inconsistent" (mesh) has theory *for* statFEM; the live failure is "incorrect"
  under model-form error (the discrepancy/identifiability issue), which is the sibling ShockSat study, not this one.

## 7. Not allowed / anti-cheating
Do NOT edit prior scaffolds or any immutable checker; COPY anything you reuse. Do NOT copy the PIFT repo's
results as your own (reimplement minimally; cite github.com/PredictiveScienceLab/pift-paper-2023). Do NOT
present a construction as failing if it merely didn't converge — converge it first or label not-yet-converged.
Do NOT pre-decide the verdict.

## 8. Done criteria
Artifacts exist; `check.py` passes (non-RED) via `bash run_all.sh`; assumptions + limits documented; every
figure tufte-linted + image-QA + overlap-audited; the deck's every claim traces to a checker number;
`decisions_log.md` complete; the per-construction consistency verdict + gaps + suggested improvements written
for Ilias; the proposed `docs/report/project_log.md` row + `notes/*` updates SURFACED for the lead (status from
the checker), NOT self-applied.

## 9. Human stop points (lead handles; you SURFACE, do not self-apply)
Stop for human approval before changing any durable rule, checker expectation, sampler standard, or project
notes/vision. This study + its checker + deck are new artifacts and need no stop; the `project_log` row and any
`notes/memory.md` update do.

## Communication style
Reader is BEGINNER-TO-INTERMEDIATE in ML/statistics (define every ML/stats term, acronym, symbol with units on
first use; lead with intuition + a concrete example, then the precise detail) and ADVANCED in structural
dynamics / numerical methods (FRFs, modal analysis, FEM, eigenproblems used directly). Full rule in
`AGENTS.md` / `CLAUDE.md`.
