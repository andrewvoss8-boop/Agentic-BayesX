# Task card — ShockSat × tray coupled QOI: method & coupling comparison

You are a FRESH Claude Code agent continuing the Agentic BayesX program. This is a
new phase; the predecessor (a validated ShockSat modal twin) is DONE. Work in a
NEW workspace. Do the work yourself end-to-end; use detached compute for long jobs.

## RE-GROUND FIRST (do not skip)
1. `AGENTS.md` — ALL gates. Pay special attention to the ones added this week:
   Result Status Standard (green/yellow/red), Modal/Eigenproblem Identifiability
   Gate, the figure-provenance/invalidity rule, the detached-launch gate, the
   NUTS/HMC + convergence gates, quantity-contract and reference/standards gates.
2. Predecessor workspace `artifacts/reports/shocksat_fem_modal_twin_20260609/`:
   read `packet.md`, `decisions_log.md` (D1–D38 — D38 is YOUR scope), `theta_full.json`
   (the converged ShockSat posterior), `joint_strain_energy.json`, `reduction_report.json`.
3. `notes/memory.md` (CURRENT STATE + the "NEXT DIRECTION" block) and `notes/runs.md`.
4. Tray (secondary) FEM: `artifacts/reports/fim_identifiability_opus_20260609/`
   (`arrays_fim.npz`, `code/`, `quantity_contracts.md`, `packet.md`).
Restate goal / last decision / next action / open ambiguities in one line before acting.

## THE ENGINEERING QUESTION
A payload tray (secondary) is mounted to ShockSat (primary). For predicting the
**net CG interface load** the tray transmits, how much does the **analysis method**
(time-history vs SRS vs PSD) and the **coupling assumption** (uncoupled fixed-base
vs coupled) change the answer — and how much of the answer is controlled by the
**unidentified mount stiffness**? Quantify the uncoupled→coupled gap (this is the
apparent-mass / force-limiting effect, NASA-HDBK-7004C — the program's novelty thread).

## QOI (write the quantity contract BEFORE any number/plot — gate)
- QOI = **net CG interface load resultant on the secondary, 3 directions (Fx, Fy, Fz)**
  under base excitation at the mount. **Single-point 6-DOF condensation is sufficient**
  (net translational force is bounce-mode dominated). Report peak |F| and the SRS/PSD
  summary per direction.
- Apparent-mass convention traps are real here — state numerator/denominator,
  source-vs-load apparent mass, base-drive BC, units, expected limiting/notch
  behavior, reference. SEE the predecessor program's apparent-mass postmortem
  (`docs/lab/apparent-mass-convention-postmortem.md`) and NASA-HDBK-7004C Fig 9.

## SCOPE — locked by D38 (do NOT re-expand without asking)
Experiment matrix:
- **Coupling:** (a) UNCOUPLED — tray fixed-base (cantilever) modes driven by the base
  input; (b) COUPLED — tray tied to the ShockSat ROM via a single condensed interface
  point. Use Craig-Bampton (transient) and/or LM-FBS (frequency-domain, natural for
  apparent mass). The **uncoupled→coupled gap = force-limiting / apparent-mass**.
- **Method:** (1) TIME-HISTORY (reference/truth-of-method); (2) MODAL-SRS — fixed-base
  modes as independent SDOFs, scaled by **participation factor (MMF)**, combined by
  **SRSS**, **sweep Q**; (3) PSD/Miles — clearly-labeled enveloping arm only (SRS→PSD
  conversion knobs = explicit assumptions; per-mode Miles, RSS, ×3σ).
- **Mount = uncertain 6-DOF CBUSH** at the condensed point. It is a JOINT → treat its
  stiffness as an uncertain parameter (likely unconstrained). HYPOTHESIS TO TEST: the
  QOI uncertainty is **mount-stiffness-dominated** (the predecessor's under-identification
  finding propagating into the QOI). Apply the Modal Identifiability Gate to the coupled
  interface modes.
- **Base input:** in the LINEAR-VALID regime (a specified moderate random/transient, or
  the low-frequency band of the measured strut-base motion). Propagate the ShockSat
  posterior (`theta_full.json`) + a prior on the mount CBUSH.
- DROPPED for this QOI: the distributed multi-mount arm (only matters for moments/
  per-mount loads — not net CG force).
- **SHOCK ground-truth case: DEFAULT SKIP.** Linear FEM does not predict pyro
  near-field shock; shock was never the StatFEM objective; the coupled tray QOI is
  hypothetical regardless. Do NOT polish it. If you have a specific reason, run only a
  small, explicitly-caveated "does the linear twin track low-freq and break at high-freq
  as expected" probe — bounded, labeled, not a deliverable.

## HONESTY / LABELING (non-negotiable)
- The **coupled tray QOI is HYPOTHETICAL** — no tray was ever mounted to ShockSat. Label
  it a methods demonstration; make NO hardware-validation claim. The tray placement,
  mount location, and mount stiffness are INVENTED assumptions (ledger them).
- The ShockSat primary IS validated (predecessor, modal regime); the tray FEM comes from
  the FIM workspace. Reconcile units (tray SI vs ShockSat in/lbf/s) and coordinates.
- Every figure states its run/dataset and flags invalidity (figure-provenance gate).
- Status on green/yellow/red; non-converged samplers yellow at best.

## DELIVERABLES
- `priority_deliverables.md`, `question_framing.md`, `quantity_contracts.md`,
  `assumptions_ledger.md` (mount stiffness, damping, placement, Q, SRS→PSD knobs as
  H-priority items).
- Method comparison: how much modal-SRS and PSD/Miles over/under-predict the net-CG-load
  QOI vs the time-history reference, with conservatism quantified, under model + mount
  uncertainty.
- **Uncoupled→coupled gap** = the apparent-mass / force-limiting quantification (tie to
  7004C; show the notch/over-test).
- **Mount-stiffness sensitivity**: is the QOI mount-dominated? (Modal Identifiability Gate.)
- Figures (tufte-linted, run/invalidity-labeled), `check.py` (green/yellow/red),
  `run_all.sh` one-command replay, `runtime.json`, `manifest.json`, `files_changed.md`,
  `decisions_log.md`, and a `packet.md` with the method summary + graphical model AT TOP.
- Workspace: create `artifacts/reports/shocksat_tray_coupled_qoi_<YYYYMMDD>/`.

## ENV / TOOLS
- Reuse the ShockSat 74-mode ROM (predecessor `matrices/` + `reduced_blocks.npz`) and
  `theta_full.json`. Tray from `arrays_fim.npz`.
- If sampling: pinned `../../../.venv_nuts/bin/python` (jax 0.4.30 / numpyro 0.15.3),
  `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`, detached for long jobs.
- References to check: NASA-HDBK-7004C (force limiting / apparent mass), Miles' equation
  assumptions, SRS mode-combination rules (SRSS/NRL/ABSSUM), Craig-Bampton/LM-FBS.

## FIRST STEPS
1. Re-ground (above), restate goal in one line.
2. Write `quantity_contracts.md` for the net-CG-load QOI + apparent mass (get sign-off
   from the human if anything is ambiguous — apparent-mass conventions have burned us).
3. Stand up the uncoupled tray fixed-base path + the base input, get one QOI number out
   end-to-end (time-history), THEN add SRS, PSD, and the coupled path.
Honest negative results are successes here. Do not over-claim; the value is the
method/coupling comparison and the mount-dominance finding, not a polished prediction.
