# question_framing — Question/Decision Gate + PRE-REGISTERED arms and thresholds
(written and SHA-covered BEFORE any science ran; the checker `check.py` is locked against these)

## The engineering decision
Which single {model, shape-use} combo (+ statFEM F(k) output discrepancy, always on) becomes the DELIVERED
ShockSat net-CG twin per QOI — and does agentic remodeling (an agent generating/evaluating 100s of model-form
candidates, selected by shape-inclusive Bayesian evidence) earn a place in the workflow?

## Plain-English definitions (first use)
- **Likelihood**: the probability model scoring how well a candidate FEM explains the measured features.
- **Evidence (marginal likelihood)**: the average of the likelihood over the prior — rewards fit, penalizes
  complexity (Occam). Computed here per model class, on a likelihood that INCLUDES shape (freq+MAC).
- **MAC** (modal assurance criterion): squared cosine between two mode-shape vectors, 0-1 (1=same shape).
- **statFEM F(k)**: a frequency-correlated (1-octave-smooth) multiplicative output discrepancy field applied to
  the predicted spectrum, QOI-aware (wide where unmeasured modes drive the response). Proven in
  shocksat_netcg_method_selection_20260701.
- **CRPS** (continuous ranked probability score): a proper score for a predictive distribution vs a realized
  value (lower better); CRPS-skill = 1 − CRPS/CRPS_climatology (positive = beats climatology).
- **NUTS**: No-U-Turn Sampler (gradient-based Hamiltonian Monte Carlo), our default posterior sampler.
- **R-hat / ESS**: convergence diagnostics (R-hat→1 good; ESS = effective sample size).

## Pre-registered arms (ALL reported; no silent dropping)
| arm | model | shape use in likelihood | discrepancy |
|---|---|---|---|
| M0S0 | inherited 9-group FEM | none (L5 modal-frequency, Kiran Eq 25) — **baseline A (proven)** | statFEM F(k) |
| M0S1 | inherited | frequency + differentiable MAC on .ash-matched modes | statFEM F(k) |
| M0S2 | inherited | Beck mode-matching-free inferred shape FIELD (free shapes, Rayleigh + .ash MAC pull) | statFEM F(k) |
| M1S0 | best agent remodel (evidence-selected) | none (L5) | statFEM F(k) |
| M1S1 | best agent remodel | frequency + MAC | statFEM F(k) |
| M1S2 | best agent remodel | Beck shape field — **full composite D** | statFEM F(k) |
Reference bars (not arms): FEM+6dB incumbent; L5_freq_discrep; L5_theta_only (known-overconfident reference).

Prior nulls we must NOT hide: MAC-as-θ-constraint was ~NULL on single-impact data (modelclass_L5 §3a);
this run retests on multi-reference data at the QOI level. Null again = reportable finding.

## Pre-registered scoring resolutions and thresholds (grade against these; falsification accepted)
Held-out protocol: leave-one-DRIVE-out (5 folds: +X/Test01, +Z/Test02, +Y/Test03, +XY/Test04, +Z@900/Test06)
= primary answer key; held-out-SENSOR splits for R1 per-point metrics. Full in-band mode set 45-260 Hz always.

- **R1 per-point FRF amplitude at held-out sensors** (interval width, coverage, CRPS-skill).
  Pinned bounds (provenance): baseline FEM-shapes σ_QOI ≈ 0.92-1.11 & mean CRPS-skill −0.68
  (shapefield_lever.json, 3 seeds); Beck inferred-shapes prior result: mean CRPS-skill −0.25, σ 0.86-0.88,
  interval ~43% sharper (same file); shape-oracle ceiling σ ≈ 0.70 (bilionis_review/residual_map).
  GREEN for a shape arm: CRPS-skill better than its S0 counterpart AND coverage ≥ 0.90. YELLOW: documented miss.
- **R2 net-CG QOI bands** (shear X/Y + normal Z, 1-oct smoothed, 7004C force convention, netcg contracts).
  Coverage = HARD gate (energy-weighted, narrow exceedances tolerated per netcg convention: weighted_coverage
  ≥ 0.95 with energy_wtd_pos_dB_exceed ≤ 0.5 dB). Among covering arms, sharpest wins (sharpness =
  95%-band GRMS ratio vs FEM+6dB, LOWER = sharper). Baseline bars to beat (bakeoff_scorecard.json, statfem_Fk):
  shear_X 1.508, shear_Y 2.301, normal_Z 2.526. Held-out-drive context: proven statFEM F(k) covered 5/5 drives
  shear_X, 4/5 shear_Y (+Z@900 gap = drive-specific artifact per DD1).
- **R3 leave-modes-out overconfidence audit** on EVERY arm: hide top-K=3 QOI-driving measured modes; band
  widen ratio MUST be > 1.0 (reference: proven statfem_Fk widened 1.42 on shear_X; theta_only 1.00 = FAIL).
  An arm that fails R3 is DISQUALIFIED regardless of sharpness.
- **R4 evidence sanity**: any M1 delivered winner must beat M0 on shape-inclusive evidence AND on held-out R1
  or R2. Evidence-only wins reported but not delivered. Frequency-only evidence FORBIDDEN as selector
  (stage1_evidence precedent: freq-only evidence crowned inherited-FEM P=0.906 while blind to shape error).
- **Status**: GREEN threshold met / YELLOW documented honest miss / RED per Result Status Standard, with RED
  loudly labeled "pre-registered claim falsified" vs "pipeline failure" (plate_test_rehearsal lesson).
- **Winner's curse**: every "best" = best-of-N with N stated (candidate count per tier recorded).

## What the search may choose vs human judgment
- Agent/optimizer chooses: candidate model forms within the allowed families, screen ranking, evidence-based
  selection, per-arm hyperparameter retuning under the uniform retune policy (documented like parent D9).
- Human judgment (NOT optimized): the allowed remodel families and the geometry-rebuild prohibition (Card D
  verdict); the QOI definitions; acceptance thresholds above; the final delivery decision.

## What would make this the wrong question
- If the 45-260 Hz band or the 5-drive set is unrepresentative of the delivery environment (delivery band
  20-2000 Hz is wider; outside the data band the twin is prior-only — carried caveat).
- If per-point FRF amplitude (R1) and net-CG bands (R2) crown different combos with no coherent story — then
  "one delivered twin" needs a per-QOI split, which the card allows (single combo PER QOI).
- If the .ash survey shapes themselves carry the east-west error the shape likelihood is supposed to fix
  (survey = 76 nodes, 33 modes; treated as the shape truth source).
