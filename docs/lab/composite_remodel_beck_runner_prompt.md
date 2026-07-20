# Runner prompt — COMPOSITE BAKE-OFF: agentic remodeling × shape-in-likelihood (MAC) × Beck shape-field × orthogonal discrepancy

Approved by Andrew 2026-07-02. Self-contained: a FRESH agent executes autonomously through all stages.
FIRST re-ground: read `AGENTS.md` (follow EVERY gate), this card, then skim the source workspaces in §6.
Audience/communication per AGENTS.md. Do not stop for approval except where this card says STOP.

## 1. Question and decision (one paragraph)
Can the combination of (a) agent-generated model-form candidates selected by Bayesian EVIDENCE on a
SHAPE-INCLUSIVE likelihood, (b) shape information in the likelihood (frequency+MAC), and (c) the Beck
mode-matching-free inferred shape FIELD — each carried with the proven statFEM F(k) orthogonal output
discrepancy — beat the proven non-Beck baseline on HELD-OUT data? Decision supported: which model+shape+
discrepancy combo becomes the delivered ShockSat twin, and whether agentic remodeling earns a place in the
workflow. Andrew's principle: **LIMITED DATA, NEVER LIMITED MODES** — always use the full in-band mode set
(45–260 Hz) and all 5 drives; never prune modes to make a method look good.

## 2. The matrix (pre-register ALL arms before running any)
Axes: MODEL {M0 inherited FEM, M1 best agent remodel(s)} × SHAPE-USE {S0 frequency-only likelihood (L5,
Kiran Eq 25 — the proven baseline), S1 frequency+MAC likelihood (NEW REQUIRED AXIS — Andrew), S2 Beck
inferred shape field} × DISCREPANCY {statFEM F(k) always ON}. Core arms: M0S0 (baseline A), M0S1, M0S2,
M1S0, M1S1, M1S2 (full composite D). Report the full matrix; no silent arm-dropping. Prior context you
must not ignore: shape-MAC-as-θ-constraint was ~NULL on SINGLE-impact data (modelclass_L5 §3a) — this run
retests it on MULTI-REFERENCE data and at the QOI level; if it is null again, that is a reportable finding,
not a reason to hide the arm. Beck (L8b) previously sharpened held-out amplitude ~43% (CRPS −0.68→−0.25).

## 3. Agentic remodeling track (feeds M1)
- CANDIDATE FAMILY (allowed): local interface/joint compliance parameterizations incl. new DOFs; per-region
  thickness/offset fields; connectivity variants; weld/contact representations; mass-distribution variants.
  FORBIDDEN: from-scratch geometry rebuild (Card D verdict). Seed from the diagnosis (bolted joint, steel
  bottom corner, 150–210 Hz cluster, bulkhead interfaces — `shocksat_fem_remesh_20260618/region_diagnosis.md`)
  PLUS a random-exploration tranche. Target: O(100+) candidates.
- TWO-TIER SCREEN (compute default, Andrew-approved): cheap reduced/perturbation screen on all → full
  eigensolves (80 modes) on the top ~30 → NUTS + EVIDENCE on the top ~10.
- SELECTION: Bayesian evidence (Occam-penalized model-class selection) computed on a likelihood that
  INCLUDES SHAPE INFORMATION (frequency+MAC at minimum). Frequency-only evidence is FORBIDDEN as the
  selector — it is blind to the shape (east–west) error and will re-crown frequency-fitters
  (stage1_evidence precedent: inherited FEM P=0.906 on freq-only). Report prior-robustness of the ranking.
- METRIC TRAPS (encode in the checker; both burned us before): (i) NO per-mode amplitude/phase fitting in
  any score (the "+0.083" artifact); (ii) re-pairing-robust mode matching (fixed cross-orthogonality
  pairing, not greedy MAC — the "+0.010" churn artifact).

## 4. Scoring (pre-registered; checker SHA-locked BEFORE science; falsification accepted)
Held-out protocol: leave-one-DRIVE-out (5 folds) as the primary answer key + held-out-SENSOR splits for
per-point metrics. Two resolutions, both required:
- R1 per-point FRF amplitude at held-out sensors: interval width, coverage, CRPS-skill (grade against the
  known bounds: shape-oracle σ 0.70 ceiling; Beck prior −0.25 CRPS; baseline σ ~0.92).
- R2 net-CG QOI bands (shear X/Y + normal Z, 1-oct smoothed, 7004C force convention, netcg contracts):
  coverage = HARD gate (energy-weighted, tolerated narrow exceedances); among covering arms sharpest wins.
  Baseline bars to beat: statFEM F(k) 1.51×/2.30× shear (held-out-drive 5/5, 4/5), 2.53× normal.
- R3 leave-modes-out overconfidence audit on every arm (widen ratio must be > 1; an arm that fails is
  DISQUALIFIED regardless of sharpness).
- R4 evidence sanity: any M1 winner must beat M0 on EVIDENCE (shape-inclusive) *and* on held-out R1 or R2 —
  evidence-only wins are reported but not delivered.
- Status encoding: GREEN threshold met / YELLOW documented honest miss / RED per Result Status Standard.
  LABEL LOUDLY whether any RED is "pre-registered claim falsified" vs "pipeline failure" (lesson:
  plate_test_rehearsal_20260701).
- Winner's curse: every "best" is reported as best-of-N with N stated.

## 5. Convergence, compute, integrity (non-negotiable)
NUTS default (numpyro, 4 chains, x64), all-variable R-hat ≤1.05 / ESS ≥200 / div <2%; uniform retune policy
allowed (document like parent D9). MAC terms in the likelihood need a differentiable form — document the
smoothing/relaxation used (AGENTS Sampler Decision). Eigenvector gradients near the 246–258 Hz cluster are
degenerate — if S1/S2 need shape derivatives, freeze bases or use subspace-projected forms and DOCUMENT
(parent A9 precedent). Detached resumable launches (`nohup … & disown`), per-(arm,fold) outputs, threads
pinned. Checker SHA-locked before science; never modified during the trial. Tufte-linted saved plotting
scripts; every figure states run/dataset + convergence status. Truth-vs-observed plots for any synthetic
element. Assumptions ledger with values/units/sensitivity; quantity contracts before plotting/checking.

## 6. Sources (reuse, do not rebuild)
- `artifacts/reports/shocksat_netcg_method_selection_20260701/` — statFEM F(k), QOI forward (netcg_qoi.py),
  1-oct scoring, held-out-drive machinery, theta_post_L5.npz, quantity contracts. (§10 erratum context.)
- `artifacts/reports/shocksat_modelclass_L5_20260619/` — Beck/L8b shape-field code + numbers; MAC-likelihood
  (L6/L10) prior nulls; evidence machinery (stage1_evidence).
- `artifacts/reports/shocksat_fem_remesh_20260618/` — fem_model.npz, groups.json, region_diagnosis.md,
  Card D boundary + metric-trap history (correlation_contribution.md).
- `artifacts/reports/shocksat_psd_envelope_twin_20260623/code/` — realfrf.py, modal_feature.py (L5 NUTS),
  shape_borrow_diag.py (.ash survey shapes for MAC), 4-drive data caches (+Y cache in netcg data/).
- `notes/memory.md` CURRENT STATE (2026-07-02 redirect entry) for the human decisions behind this card.

## 7. Deliverables & done criteria
Own workspace `artifacts/reports/shocksat_composite_bakeoff_<date>/` ONLY (no durable-rule / checker /
other-workspace edits). Gate files first (priority_deliverables, question_framing w/ pre-registered
thresholds, quantity_contracts, assumptions_ledger, decisions_log), then locked check.py, then science.
Deliver: full-matrix scorecard, evidence table (prior-robust), the delivered-twin recommendation (single
{model, shape-use} combo per QOI with caveats), packet.md + findings.md (numbers never stronger than
checker), figures (matrix money-figure comparing all arms vs baseline bars + oracle ceiling), runtime.json,
runs.md entry + project_log row copied from the checker, decisions_log for every non-obvious choice.
STOP for the human only if: a durable rule seems wrong, data appears corrupted, or compute exceeds the
two-tier plan. Falsified or null arms are findings — report them with the same care as wins.
