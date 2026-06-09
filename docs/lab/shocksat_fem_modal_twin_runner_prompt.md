# Runner Prompt — ShockSat Full Parametric FEM Modal Twin (Bayesian, NUTS, held-out)

Date: 2026-06-09 · Lead: Claude Code (Opus) · Runner: ONE expert agent (Opus or Codex),
single session. This is a **real build and a deliberate pressure test of our current
state of knowledge and abilities.** An honest "it failed here, for this reason, with
this evidence" is SUCCESS. A polished result that hides a shortcut is FAILURE.

Read first (do not skip): project-root `CLAUDE.md` and `AGENTS.md` (all gates),
`docs/agents/how_to_run.md` (runner isolation + compute), `docs/compute_protocol.md`,
and the prior science findings you are building on:
`artifacts/reports/shocksat_opus_20260609/` — especially `statfem_v1_heldout.md`,
`opus_normalization_findings.md`, `opus_point_reconcile.json`. The normalization finding
is upstream truth: **SOL111 FRF vs Test07 taps are different transfer paths → a magnitude
FRF likelihood is invalid. The observation layer is MODAL correlation (frequencies +
mode shapes / MAC).**

---

## 1. Mission (one paragraph)
Build a **full parametric finite-element modal twin** of the NASA/NESC ShockSat free-free
structure from the provided NASTRAN model, with a small set of **per-part-group stiffness
parameters** as the inferred variables. Calibrate them with **Bayesian updating (NUTS/HMC
default)** against the **measured** free-free modal data (frequencies + mode shapes on the
1101–7105 grids). Then deliver the thing the project has been driving toward: a
**side-by-side of held-out modal quantities of interest (QOIs) — posterior median + 95%
credible interval — versus their measured actual values**, with full convergence
diagnostics and honest coverage reporting. This is the first real-hardware, real-FEM
Bayesian validation in the project; treat it as a pressure test, not a demo.

## 2. Why this matters (the decision being supported)
Everything before this was synthetic-truth or a deterministic/reduced (TAM) correlation.
This run answers: *can our pipeline take a real industrial FEM + real test data and produce
a calibrated, convergence-gated, honestly-uncertain modal twin whose held-out predictions
are trustworthy?* The objective metric is **held-out predictive accuracy AND calibration
(coverage of 95% CIs)** on modes not used in calibration — not in-sample fit. What stays
human judgment: which part groups are physically meaningful, which modes to trust, and
whether the twin is fit for any downstream load/QOI use.

## 3. Workspace isolation & inputs (hard constraints)
- Create and work ONLY in a fresh workspace `artifacts/reports/shocksat_fem_modal_twin_<YYYYMMDD>/`.
  Assert your CWD at start; **refuse to run if CWD is the master repo root.** You may
  auto-run inside your own workspace; never auto-run in the master repo.
- **Read-only inputs** (verify each file's SHA256 at start and again at end; record both):
  - NASA model + correlation: `artifacts/reports/shocksat_statfem_runner_20260609/extracted/FEM/`
    (the full `ShockSat_*.blk` bulk-data includes, `FEM_20211021/…`, and
    `Correlation/Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/` with `Modes.pch`,
    `TAM.pch`, `TDM_FF*`, plus `ShockSat_TAM_101521.dat`, `Final_Summary_Documentation_101521_rev1.pptx`).
  - Instrumentation/grids: `artifacts/reports/shocksat_statfem_runner_20260609/channel_map.csv`
    and the parsed grid coordinates in `artifacts/reports/shocksat_opus_20260609/opus_point_reconcile.json`.
- Do **not** modify any sibling workspace. Copy what you need into your own `inputs/`.
- Pin and record the environment (see §12). Reproduce any immutable checker hashes you rely on.

## 4. TASK 0 — verify the measured modes BEFORE modeling (do this first; it gates everything)
The prior runner labeled `FINAL_FF/TAM_FF/Modes.pch` as the *measured test* modes, but
`Modes.dat` is a NASTRAN `SOL SEMODES` (FEM) deck and several MAC values are **exactly
1.000** — the signature of a FEM-vs-FEM (reduction-fidelity) comparison, not test-vs-FEM.
**Resolve this unambiguously:**
- Identify which file holds the genuinely **measured** free-free test modes (candidate:
  the Test Display Model `TDM_FF*`) vs the **analysis** modes (`Modes.pch` from SOL SEMODES),
  vs the reduced TAM (`TAM.pch` DMIG KAAX/MAAX/MUG1T).
- Cross-check the candidate measured frequencies against NASA's published test frequencies
  (in `Final_Summary_Documentation_101521_rev1.pptx` and/or the modal test logs).
- Write `measured_modes_provenance.md` stating exactly which file = measured, which = FEM,
  with evidence. **If you cannot establish a genuinely measured mode set, STOP and report
  that** — do not calibrate against FEM-as-if-test (that would be circular and is a failure mode).

## 5. The build (your engineering freedom, with required properties)
Build a **full parametric FEM** whose stiffness is a function of per-part-group scales
`theta_g` (g = a small, physically-motivated set of part groups — e.g., boxes, brackets,
cross-beam, plates, joint connections; justify your grouping from the `.blk` property/part
structure). Required properties:
1. **Real assembly:** assemble global stiffness `K(theta) = K0 + Σ_g (theta_g − 1)·K_g` and
   mass `M` from the actual model (elements, materials, properties, joints). You may:
   (a) parse the NASTRAN `.blk` deck and assemble in Python/JAX yourself, or
   (b) use CalculiX (`ccx`, available in repo; see `runs/fem_phase1/`) or another solver to
   export per-group `K_g`, `M`, then assemble. State and justify your choice and its error.
2. **NUTS-feasible forward model:** the full DOF count is large (~67k nodes). Use a
   **parametric model-order reduction** (e.g., project onto the nominal low-mode basis or a
   Craig–Bampton basis) so `modes(theta) = eigh(K_r(theta), M_r)` is small and
   **differentiable** (JAX `eigh`). **Report the reduction error** vs a full sparse
   eigensolve at nominal `theta` (this is a Discretization-Resolution deliverable).
3. **Handle the known numerical hazards explicitly (name each in the report):**
   - Free-free → **6 rigid-body modes ≈ 0**: project them out / constrain so they don't
     pollute the elastic-mode likelihood or the eigensolve gradient.
   - **Degenerate / near-degenerate pairs** (symmetry): `eigh` gradients are ill-conditioned
     for repeated eigenvalues — use a subspace/eigenvalue-sum or smoothing approach and
     document it.
   - **Mode pairing (test↔analysis) via MAC is non-differentiable (argmax):** fix the pairing
     per-iteration or use a documented smoothed assignment; per the NUTS rule, document any
     smoothing/relaxation of non-differentiable features and its effect.
4. **Validate the forward model** before inference: at nominal `theta`, your reduced
   parametric modes must reproduce NASA's analysis modes (and, post-Task-0, sit reasonably
   near the measured modes) — show this.

## 6. Inference (sampler + convergence — non-negotiable)
- **NUTS/HMC is the default** (NumPyro). ≥4 chains, non-centered parameterization for any
  hierarchical variance, `jax_enable_x64` forced and verified.
- Likelihood = measured vs predicted modal **frequencies and mode-shape components / MAC**
  on the common 1101–7105 grids. State the noise model (frequency error sd, shape error sd)
  in the assumptions ledger with units and rationale.
- **Convergence gate (HARD; from CLAUDE.md):** report R-hat and ESS over **ALL** sampled
  variables incl. raw latents; accept only max R-hat ≤ 1.05 (prefer ≤ 1.01), min ESS ≥ 200,
  divergence fraction < 2%. If it fails, **do not report a clean pass** — surface the
  worst-case R-hat/ESS next to any interval and label intervals not-yet-converged.

## 7. Held-out protocol + the required deliverable (do not stop until this exists)
- **Discipline:** calibrate on held-in modes ONLY; **lock the model/predictions, then reveal
  held-out actuals.** Record the lock (hash your predictions) before grading.
- **Held-out designs (do at least the first two):**
  1. **Leave-one-mode-out** cross-validation across the elastic modes (each held-out mode
     predicted with a 95% CI vs its measured frequency + MAC).
  2. **Frequency-band extrapolation:** calibrate on the lower modes (e.g., ≤ ~120 Hz),
     hold out the higher band (e.g., 120–300 Hz); predict those modes with CIs vs actual.
  3. (Stretch, clearly labeled OOD) the **pyro NSD** regime as an out-of-distribution check —
     directional unless a defensible pyro QOI is defined; do NOT fabricate a magnitude.
- **THE DELIVERABLE (required):** a **side-by-side figure + table of held-out QOIs:
  posterior median + 95% CI vs measured actual**, with explicit coverage (covers / misses)
  and error %. QOIs = held-out modal frequencies (Hz) and, if defined, a receptance/QOI with
  a full quantity contract. Report coverage honestly even if the CIs miss (miscoverage is a
  finding, not a failure to hide).

## 8. Reference / standards checks (compare before accepting)
- NASA's own correlation in `Final_Summary_Documentation_101521_rev1.pptx` and the TAM/TDM
  files — your nominal-FEM modes and your test set must be consistent with NASA's reported
  frequencies/MAC; show the comparison.
- `runs/fem_phase1/` (the project's prior CalculiX/JAX/TensorMesh modal builds) for assembly
  cross-checks and the integrity/independence lessons.
- Free-free physics: 6 rigid-body modes ≈ 0; symmetry/degenerate-pair sanity.

## 9. Quantity contracts, assumptions, sensitivity, plots (apply the standard gates)
- **Quantity contracts** for every named quantity (modal frequency, MAC, any receptance QOI):
  numerator/denominator/coordinate/excitation/BC/units/expected limiting + resonance behavior.
- **Assumptions ledger** with numerical values + units + source + sensitivity priority:
  materials, densities, BCs (free-free), joint stiffness, part grouping, noise sd's, prior
  widths, reduction basis size, mode count.
- **Sensitivity** (default work product): vary the assumptions most likely to change the
  held-out QOI — part-grouping choice, reduction basis size, noise sd, prior width, held-in
  band. Separate forward-model sensitivity from posterior/held-out sensitivity.
- **Plots:** before writing/editing ANY figure, read+apply `.claude/skills/tufte-data-graphics/SKILL.md`
  and run `scripts/tufte_lint.py` on each plotting `.py` (write plotting code to saved `.py`,
  not heredocs). Log-frequency axes for frequency-domain plots; show truth/measured vs
  predicted; show residual/zoom; label CIs; report all-variable convergence.

## 10. FEMAP cross-check handoff (human will run later)
Andrew can run modes in **FEMAP** as an independent cross-check. Produce a clean NASTRAN
normal-modes deck (or reuse/annotate the provided one) at (a) nominal `theta` and (b)
posterior-mean `theta`, under `femap_handoff/`, with a short `femap_instructions.md`
(what to solve, expected frequency table, where to drop the `.f06`/CSV back). Your modal
predictions must be reproducible by an independent FEMAP solve at the same `theta`.

## 11. Verification / checker
Write an executable `check.py` + `checker_report.json` with artifact-backed gates, at least:
- inputs' SHA256 unchanged; measured-mode provenance resolved (Task 0);
- forward model reproduces nominal analysis modes within a stated tolerance; reduction error
  reported; rigid-body modes ≈ 0;
- convergence gate values present for ALL sampled variables and meeting thresholds (or
  explicitly labeled fail);
- held-out QOI table present with median, 95% CI, actual, coverage; lock-before-reveal
  evidence present;
- no NUTS/posterior claim without diagnostics; no FRF magnitude likelihood (modal only).
One-command replay: `bash run_all.sh` runs build → inference → held-out → figures → checker.

## 12. Compute & environment
CPU + High-RAM is the default (the reduced eigensolve + NUTS is small). Use Colab A100 +
float64 ONLY if the full assembly/eigensolve is the measured wall AND the work is
parallel-shaped — and only after the method is validated; justify in the report. Pin:
jax 0.4.30, numpyro 0.15.3, numpy 1.26.4, scipy 1.10.1; force `jax_enable_x64` and verify.
Record `runtime.json` with `active_runtime_s` and `elapsed_wallclock_s`.

## 13. Deliverables (your workspace)
`priority_deliverables.md` (restate the PRIORITY asks in your words; flag ambiguities up
front), `question_framing.md`, `assumptions_ledger.md`, `quantity_contracts.md`,
`measured_modes_provenance.md` (Task 0), `decisions_log.md` (every non-obvious decision —
file-based, not chat), the build/inference/figure scripts (saved `.py`), `packet.md`
(method summary near the top: model form, likelihood equation, data counts, inferred vs
fixed vs non-inferred variables, whole-data-vs-feature likelihood choice, a run-specific
graphical-model/likelihood diagram — NOT a copied paper figure), the held-out QOI
figure+table, convergence diagnostics, sensitivity results, `femap_handoff/`, `check.py` +
`checker_report.json`, `run_all.sh`, `runtime.json`, `files_changed.md`, `manifest.json`,
`next_prompt.md`.

## 14. Communication style
Reader is BEGINNER-TO-INTERMEDIATE in ML/stats (define every ML/stat term, acronym, symbol
with units on first use; lead with intuition + a concrete example) and ADVANCED in
structural dynamics (use FRF/modal/FEM/damping terms directly). (Full rule in CLAUDE.md.)

## 15. Honesty / anti-cheating / what failure looks like
- No fabricated metrics or plots; no copied reference asset presented as generated output;
  no silent method swap; no "converged" without diagnostics; no FRF magnitude likelihood.
- If the parametric FEM is not identifiable from the modal data, if the reduction is too lossy,
  if convergence fails, or if the held-out CIs systematically miss — **report it plainly with
  evidence.** That is a valid, valuable pressure-test result. State exactly what is blocked and why.
- Do not change durable rules, checker expectations, sampler standards, or project notes — that
  is the LEAD's job after human review. Surface recommendations in `next_prompt.md`.

## 16. Done criteria
Done only when: requested artifacts/scripts exist; `bash run_all.sh` reproduces them and the
checker passes (or honestly reports a labeled failure); Task-0 provenance is resolved; the
held-out QOI side-by-side (median + 95% CI vs actual, with coverage) exists; convergence is
reported over all variables; references/standards were checked; sensitivity was run; the
FEMAP handoff deck exists; and the packet exposes enough numerical + graphical evidence for a
labmate (and a FEMAP re-solve) to find mistakes.
