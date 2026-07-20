# Runner card — DELIBERATE FORMULATION/GEOMETRY CALIBRATION of the ShockSat twin
# (follow-up to the model-form pilot's HQ2 positive; the first earned "try to WIN" card of this arc)

**Paste-and-run: you are an autonomous runner agent. Execute end-to-end without stopping for approval. A
falsified pre-registered claim is a VALID outcome — including "the formulation lever is an unphysical fudge
and must not be delivered." Never fabricate; never claim beyond your checker's output.**

Date issued: 2026-07-20. Author: lead (Claude/Fable), dispatched by Andrew. Est. compute: ~1 day (a few
dozen serial k=200 eigensolves + one small-dimension NUTS attempt on the 16 GB Mac; everything detached +
resumable; BLAS pinned).

Workspace (create): `artifacts/reports/shocksat_formulation_calibration_<date>/`
READ-ONLY: `shocksat_modelform_pilot_20260716/` (the pilot — your starting evidence),
`shocksat_fullspec_exact_completion_20260716/`, `shocksat_netcg_validated_port_20260716/`,
`shocksat_full_spectrum_frf_20260714/` (+ its repair/review), `shocksat_true_remodel_loop_20260706/`,
all SHA-locked checkers, `AGENTS.md`, `CLAUDE.md`.

**VAULT RULE (Andrew's pre-registration choice, default as written): the +XY vault is NOT read.** It has
been read 3× by this program. If Andrew ticks the vault option before dispatch, exactly ONE post-freeze
read of +XY is permitted for the single delivered finalist, labeled "4th program read"; otherwise no vault
leg exists and you say so in the packet. Do not ask mid-run; the choice is fixed at dispatch.

---

## 0. Re-ground (mandatory, ~20 min)
`AGENTS.md` (every gate — especially Reference/Standards, Identifiability, Quantity Contract, Sampler/
Convergence), `docs/compute_protocol.md`, `notes/lessons-learned.md` (the D17/D19 entries are YOUR traps).
Then the pilot: `findings.md`, `packet.md`, `out/results_table.json`, `out/candidate_specs/mr2_elem5.json`,
`code/mfops.py` (the validated formulation/geometry operators + V-gates), `out/finalists.json`. Then the
exact-completion card's `out/verdicts_final.json` (the bars) and the study's `assumptions_ledger.md`.
Write D0 in your `decisions_log.md`. Verify your own tool's compaction behavior; filesystem = truth.

## 1. What the pilot found and what this card must decide

The pilot (HQ2, checker-verified) found that GENUINE model-form edits move held-out sub-200 FRF, and its
single best candidate ever is `mr2_elem5` — a **RANDOM draw**: bending-formulation stiffening on three
plate regions, `ops = [{formulation, pids [601, 401, 302], br_scale 1.2328, ts_t 5.0}]` (bend_ratio ×1.23,
transverse shear pushed toward the Kirchhoff limit on a rectangular plate, the cross-beam, and a bracket
plate). Exact-basis sub-200 **+0.1848** vs A1 +0.1137; the ONLY finalist robust to per-fold amplitude
refits (**+0.1954**); **zero added DOF/mass**, 0.8× solve time. Element-formulation as a CLASS beat A1 by
+0.0711 ± 0.0120 (best) and stayed positive on class means.

**But:** +0.1848 is a best-of-60 statistic (winner's curse), the parameter values are a lottery ticket, and
nobody knows WHY it works. This card answers, pre-registered:
- **F0 (physical-plausibility gate, decides delivery):** is there a defensible physical mechanism, or is
  the formulation knob an effective-stiffness fudge that happens to fit?
- **F1:** does a DELIBERATELY calibrated formulation/geometry model beat A1 on exact-basis held-out sub-200
  by **≥ +0.05 AND ≥ 2×paired-fold-SE** (the S1-class bar no arm has ever cleared)?
- **F2:** does deliberate calibration beat the lucky draw (calibrated model ≥ mr2_elem5's per-fold scores,
  paired)?
- **F3:** do the gains survive per-fold amplitude refits (the pilot's robustness convention)?
- **F4 (secondary):** what happens in 200–500 Hz (the band where amplitude-θ gains live; no bar, report)?
Falsification of any of F1–F3 is a valid outcome; F0=FAIL forces the "report, do not deliver" path.

## 2. F0 — physical plausibility FIRST (before any calibration; Reference/Standards Gate)

1. **What the knobs mean, from sources not vibes:** `bend_ratio` (12I/t³ bending-inertia ratio) and `ts_t`
   (transverse-shear thickness ratio) are NASTRAN PSHELL parameters; consult a shell-theory/NASTRAN
   reference (Kirchhoff vs Mindlin: ts→Kirchhoff means the model currently carries transverse-shear
   flexibility the edit removes; bend_ratio>1 means bending stiffer than the solid-homogeneous t³). Write
   the mechanism section in plain English with the equations.
2. **What the plates actually are:** read the inherited model's property values (`fem_model.npz` pshell
   dict: t, bend_ratio, ts_t per PID; `shocksat_statfem_runner_20260609/fem_inventory.md`; the ShockSat
   overview PDF). Determine what PIDs 601/401/302 physically are (plate, cross-beam, bracket) and whether
   their REAL construction (thickness steps, doublers, bonded/bolted lands, ribs) plausibly makes them
   bending-stiffer / shear-stiffer than the modeled uniform shell. OPTIONAL (only if needed and disk
   permits, one-zip protocol): re-download `FEM_and_CAD.zip` via the documented mediaex mechanism to check
   drawings; otherwise document unavailability.
3. **Discriminating checks (do at least two):** (a) does the SAME formulation edit applied to a
   physically-dissimilar control region help as much? (if yes → generic fudge, not physics); (b) is the
   implied stiffness change within the range the real construction supports (estimate, with numbers)?
   (c) does the edit move the specific mis-paired 150–180 Hz cluster / Y-box residuals the diagnosis
   attributes to these regions, or does it help diffusely?
4. **F0 verdict (pre-registered rule):** PLAUSIBLE-MECHANISM (deliverable as a model correction) /
   EFFECTIVE-PROXY (usable as a labeled calibration device, NOT a claimed physical correction) /
   UNPHYSICAL (report, do not deliver). Write it with evidence BEFORE the calibration results are known —
   the checker verifies F0's file predates the first calibration score.

## 3. Calibration design (deliberate, small-dimension, exact-basis only)

- **Parameters (≤ ~12):** per-region `br_scale` and `ts_t` for a SMALL pre-registered region set: the three
  pilot regions (601/401/302) + at most 3 more chosen by the F0 §2.3(c) diagnosis (regions whose residual
  signature the mechanism actually explains) + optionally ONE geometry warp parameter per the pilot's
  validated operator IF F0 implicates flatness. Priors with numbers in the ledger (e.g. br_scale LogNormal
  around 1, σ justified by the F0 construction estimate; ts_t bounded [1, 5]). No θ re-opening: the 9-group
  θ stays at the study θ_MAP convention unless a pre-registered ablation says otherwise (one ablation
  allowed: co-calibrate θ, labeled).
- **Objective/likelihood:** TRAIN-drive per-channel log|H1| (whole-band 45–400 Hz, one global gain per
  drive), the study's window-matched forward, survey ζ. LODO folds; per-fold calibration on 3 TRAIN drives
  only; NEVER reuse any fold's fitted object elsewhere (checker-audited fold provenance).
- **EXACT-BASIS RULE (absolute, the pilot's convention):** every reported score comes from a candidate
  basis solved at its own calibrated parameters (enrich-at-point, self-consistency recorded). NO θ=1/
  reduced screening numbers are ever reported as scores. Budget ~30–50 serial eigensolves; log each.
- **Sampler (AGENTS default, honestly attempted):** NUTS (NumPyro, 4 chains, float64) on the ≤12-dim
  formulation posterior for at least ONE fold — this small, physically-anchored space is the best-identified
  posterior this program has attempted; run the FULL convergence gate (all-variable R-hat/ESS/divergences).
  If it converges: report the posterior properly (first converged amplitude-trained posterior of the arc —
  say so) and use posterior-mean/MAP per fold for scoring. If multimodal again: YELLOW per the standard,
  worst-case diagnostics on every figure, fall back to deterministic multi-start MAP (≥5 starts, seeds
  recorded), and run the Identifiability Gate (strain-energy + FIM at the realized floor, with the D17
  lesson: local FIM ≠ global identification — say only what it supports).
- **Controls (pre-registered, scored identically):** (i) A1 baseline; (ii) `mr2_elem5` as-is (the lucky
  draw, per-fold refit convention); (iii) a random-parameter control: same region set, parameters drawn
  from the priors (seeded, n=6) — deliberate calibration must beat its own prior draws, else the "structure"
  is the prior, not the calibration.

## 4. Pre-registration + checker (BEFORE any science; hardened standard)
`priority_deliverables.md`; `question_framing.md` (F0–F4 verbatim + the F0 rule + vault choice as
dispatched); `quantity_contracts.md` (P1′ copied exactly from the study — DIFF your scorer's headline
statistic against the reused one before first use, the D19 contract lesson); `assumptions_ledger.md`
(priors with numbers, region set, ζ/window constants inherited). `check.py`: run on empty workspace (must
be RED), SHA-lock, never edit. Gates (conduct invariants only — never assumptions about results):
finiteness of every reported statistic; F0-before-first-score ordering; exact-basis-only (grep: no score
path touches a reduced/θ=1 evaluation); per-fold provenance (no cross-fold reuse); NUTS diagnostics
recorded for every attempted posterior (YELLOW propagation on non-convergence); control arms present;
eigensolve log; no vault reads (or exactly-one-post-freeze if the option was ticked); figures
scripted/tufte-linted/legibility-QA'd; runtime.json (active ≤ elapsed); checker self-SHA.
`REUSED_code.sha256` for everything imported read-only.

## 5. Deliverables
`packet.md` (method summary first: mechanism section, model form, likelihood, data counts, inferred vs
fixed; then the results table: {A1, mr2_elem5, calibrated, random-prior control} × {sub-200, 200–500} ×
{standard, per-fold-refit} with paired deltas ± SE); `findings.md` (F0–F4 verdicts, plain English, statuses
copied from the checker; an explicit DELIVERY RECOMMENDATION consistent with F0); `out/verdicts.json`;
≥5 figures (mechanism sketch of the formulation change; calibrated-vs-A1 FRF overlay on a held-out drive,
log-frequency axis; parameter posterior/MAP with priors overlaid and convergence status printed; results
table figure; control-region discriminating check); `decisions_log.md`; `run_all.sh`; `runtime.json`;
`checker_report.json`. Continuity: `notes/runs.md` entry + `docs/report/project_log.md` row (status copied
from YOUR checker; science verdicts stated separately, never conflated with the conduct GREEN — the Card-B
D7 convention).

## 6. Honest failure modes (expected; report, don't panic)
- **F0 = EFFECTIVE-PROXY or UNPHYSICAL** is a live possibility — the edit came from a random draw. Then the
  headline is "the best lever found is a fudge; here is what it proxies for" and delivery stays A1 + the
  statFEM twin. That is a useful result; write it with the same care as a win.
- **Winner's curse bites:** the calibrated model may land well below +0.185 (that was best-of-60). The F1
  bar compares calibrated-vs-A1 paired, not vs the lottery number.
- **NUTS may go multimodal even at 12 dims** → YELLOW, labeled MAP fallback, identifiability analysis;
  do not call it converged, do not burn GPU on it (compute protocol).
- **Calibration may overfit the train drives** — that is exactly what the per-fold refit convention (F3)
  and the random-prior control are for; if calibrated ≈ prior draws, say "the prior, not the data, is doing
  the work."
- One drive (+Z(990)) has fought every sub-200 gain in this program; expect a hostile fold and report
  per-fold numbers, not just means.
