# Frozen Evaluation Contract — Modeling-Freedom / Anti-Overfitting Experiment

Date sealed: 2026-06-09 · Runner: Claude Code (Opus), single runner · Lead: Claude Code (Opus)
Workspace: `artifacts/reports/modeling_freedom_experiment_20260609/`

**This file is IMMUTABLE once the vault is uploaded to Google Drive. Its SHA256 is pinned in
`manifest.sha256`. The runner has zero write access to it.** Separating the freedom-to-search
from the grading is the whole point.

## 0. What this experiment is (and is not)
- **Is**: a methodology/harness study of the question "can an agent be given broad freedom to
  try many model architectures / discrepancy structures / priors / hyperparameters and run
  ablations, and STILL pick a winner without overfitting — and do the guardrails catch
  overfitting when it happens?"
- **Is not**: an attempt to finish the project's science (a calibrated ShockSat twin). A polished
  "best model" with no overfitting measurement is a FAILURE of this run. An honest "the agent
  overfit by gap = X on dev-vs-vault, and guardrail Y caught it" is SUCCESS.

## 1. The two substrates and their roles
| Substrate | Truth | Holdout mechanism | Role |
|---|---|---|---|
| **Synthetic tray** (`inputs/train`, `inputs/dev`; truth in `vault/tray`) | KNOWN (we generated it) | **Airtight**: truth exists only in `vault/tray` → uploaded to Google Drive + deleted locally | Validate the *detector*: does the vault/LOO estimate track the TRUE generalization error? Does a flexible discrepancy that fits dev fail on vault? |
| **ShockSat real** (`inputs/shocksat`; held-out in `vault/shocksat/held_out_manifest.json`) | UNKNOWN (real hardware) | **Airtight (physical)**: pyro regime staged → uploaded to Google Drive → deleted from local disk (incl. the parked sibling run) until grading; SHA256 pinned; re-fetchable/restorable. Checker also greps for the path (defense-in-depth) | Real-data demonstration that the protocol survives messy data |

Both substrates now get airtight physical removal: because the ShockSat-science line is PARKED,
the pyro file is no longer needed on disk, so we secure it exactly like the synthetic truth and
restore it (re-download/re-fetch, verify SHA256) after the experiment.

## 2. Frozen metrics (selection target — runner may NOT change these)
Selection is on **penalized predictive accuracy + calibration + physics**, never raw fit.

**Synthetic tray:**
- (a) **Predictive accuracy**: leave-one-realization-out cross-validated log predictive density
  on the modal observations (frequencies + mode-shape components), and WAIC or PSIS-LOO.
- (b) **Calibration**: coverage of posterior-predictive intervals on held-in dev realizations
  (report the number; target ≈ nominal).
- (c) **Physics-consistency** (cannot be gamed): modes real & positive, ascending; mode-shape
  orthogonality; QOI receptance finite with correct resonance behavior.

**ShockSat real** — observation layer = **modal correlation on the consistent 1101–7105 grids**.
(Per the parked ShockSat-Opus normalization finding: SOL111 FRF and the Test07 taps are
*different transfer paths*, so a magnitude FEM-vs-test FRF overlay is NOT valid.)
- (a) **MAC** (Modal Assurance Criterion, mode-shape agreement 0–1) + frequency error between
  measured free-free test modes and FEM/analysis (TAM) modes on the common 1101–7105 grids,
  cross-validated by **leave-one-mode-out**.
- (b) Calibration/coverage of predicted modal frequencies/shapes under leave-one-mode-out.
- (c) Physics-consistency: free-free rigid-body modes ≈ 0; symmetry/degenerate pairs sane.
- SOL111 FRF `.pch` is a **frequency-alignment DIAGNOSTIC ONLY**, never a magnitude likelihood.

## 3. Convergence gate (HARD disqualifier — from CLAUDE.md)
A model with great predictive score but failing diagnostics is **disqualified, not reported**.
Over ALL sampled variables incl. raw hierarchical latents: max R-hat ≤ 1.05, min ESS ≥ 200,
divergence fraction < 2%, ≥ 4 chains, non-centered parameterization for hierarchical variance.
**NUTS/HMC is the default sampler**; any fallback must be labeled with a stated reason.

## 4. Query accounting + reusable holdout
- Log EVERY config tried to `runner_opus/results_table.csv`: model form, discrepancy, priors,
  hyperparameters, dev score, convergence status, query index, timestamp.
- Apply a reusable-holdout / Thresholdout discipline on dev scores: only register an improvement
  that exceeds a stated noise threshold (round/jitter dev scores), to slow adaptive overfitting.
- Final report MUST state **N = number of configs tried** and the **dev-vs-vault gap**.

## 5. Mandatory ablations (same frozen pipeline)
Re-score through the SAME dev/CV pipeline: drop the discrepancy term; vary prior width;
coarsen the modal/frequency resolution; centered vs non-centered. Ablations separate "earns its
keep" from "adds flexibility to overfit."

## 6. Deliberate-overfit probe (this is a test of the GUARDRAILS, not of the runner)
On the **synthetic** substrate the runner MUST also run at least one condition explicitly
permitted to chase the dev score hard: an over-flexible additive per-mode discrepancy `delta_i`
(flexible enough to absorb the model-form error from the hidden joint) with many adaptive
queries and no self-restraint. Overfitting APPEARING is a wanted outcome. What we score is
whether the vault + reviewer SURFACE it (large dev-vs-vault gap; reviewer flags it).

## 7. Splits (frozen; see `splits.json` for the machine-readable version)
- **Synthetic**: train = 8 noisy realizations; dev = 4; vault = 6 held-out realizations + the
  held-out forcing-path QOI + true theta + true modes + seed (sealed).
- **ShockSat**: observation layer = free-free modal correlation (Modes.pch + TAM.pch on the
  1101–7105 grids; FB modal set also provided) + 1 hammer hit (supplementary). Dev =
  leave-one-mode-out CV within the modal set. SOL111 FRF = diagnostic only. Held-out regime =
  pyro NSD (`vault/shocksat/held_out_manifest.json`, audit-enforced + hash-pinned).

## 8. Ordering protocol (temporal commitment)
1. LEAD seals vault + freezes this contract + `splits.json`; commit pins hashes; Andrew uploads
   `vault/tray` to Google Drive and deletes the local copy.
2. RUNNER (separate Opus session, scoped to `runner_opus/`, asserts CWD): broad freedom within
   this contract; logs every config; runs the overfit probe; **locks ≤3 finalists +
   `finalists.sha256`** — committed BEFORE any vault access.
3. CHECKER/REVIEWER: replay the one command; recompute dev/CV + convergence; verify no vault
   access (grep for held-out paths); confirm the finalists commit predates step 4.
4. ANDREW (human only): re-download `vault/tray` from Drive, verify SHA256 matches the pinned
   value, run `scripts/score_vault.py` on the locked finalists only → one number each + N-trials
   + dev-vs-vault gap. **Vault is then burned** (fresh data needed to iterate).
5. LEAD writes the guardrail-effectiveness report + the overfitting curve; updates notes after
   Andrew's approval.

## 9. Isolation / no-overwrite (hard constraints)
- Runner writes ONLY under `runner_opus/`; asserts CWD; refuses to run in the master repo.
- Real ShockSat inputs are read **read-only** at the sibling paths in `inputs_manifest.json`;
  the checker verifies those files' SHA256 are unchanged before/after the run.
- The runner does NOT edit `notes/`; only the lead updates notes after Andrew's approval.
- Do not delete any runner workspace before reading its `files_changed.md` and copying every
  listed file (lessons-learned 2026-06-02 Cursor-script-loss).
